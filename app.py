import ecooptima
from flask import (
    Flask,
    request,
    render_template,
    url_for,
    jsonify,
    send_from_directory,
    session,
    redirect,
    g
)
import os
import asyncio
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4
from auth import get_auth0_client
from dotenv import load_dotenv
from functools import wraps
from auth0_server_python.auth_types import StartInteractiveLoginOptions, LogoutOptions

load_dotenv()

app = Flask(__name__)

conversation_store: dict[str, dict] = {}
app.secret_key = os.getenv('AUTH0_SECRET')

# Configure session for Auth0
app.config.update(
    SESSION_COOKIE_SECURE=False,  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

@app.before_request
def store_request_response():
    """Make request/response available for Auth0 SDK"""
    g.store_options = {"request": request}


async def _get_current_user():
    return await get_auth0_client().get_user(g.store_options)


def _run_async(awaitable):
    return asyncio.run(awaitable)


def _default_logout_return_to() -> str:
    configured = os.getenv("AUTH0_LOGOUT_RETURN_TO")
    if configured:
        return configured

    redirect_uri = os.getenv("AUTH0_REDIRECT_URI")
    if redirect_uri:
        parts = urlsplit(redirect_uri)
        return urlunsplit((parts.scheme, parts.netloc, url_for("login"), "", ""))

    return url_for("login", _external=True)


def login_required_page(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        user = _run_async(_get_current_user())
        if not user:
            return redirect(url_for("login", next=request.path))
        g.user = user
        return view_func(*args, **kwargs)

    return wrapped_view


def login_required_api(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        user = _run_async(_get_current_user())
        if not user:
            return jsonify({"error": "unauthorized"}), 401
        g.user = user
        return view_func(*args, **kwargs)

    return wrapped_view

@app.route('/login')
def login():
    """Render the local login page."""
    user = _run_async(_get_current_user())
    if user:
        return redirect(url_for("home"))
    return render_template("login.html")


@app.route('/auth/start')
def auth_start():
    """Redirect to Auth0 Universal Login."""
    next_path = request.args.get("next")
    login_options = StartInteractiveLoginOptions(
        app_state={"next": next_path} if next_path else None
    )
    authorization_url = _run_async(
        get_auth0_client().start_interactive_login(login_options, g.store_options)
    )
    return redirect(authorization_url)

@app.route('/callback')
def callback():
    """Handle Auth0 callback after login"""
    try:
        result = _run_async(
            get_auth0_client().complete_interactive_login(
                str(request.url), g.store_options
            )
        )
        next_path = (result.get("app_state") or {}).get("next")
        if next_path and next_path.startswith("/") and not next_path.startswith("//"):
            return redirect(next_path)
        return redirect(url_for('home'))
    except Exception as e:
        return f"Authentication error: {str(e)}", 400

@app.route('/profile')
@login_required_page
def profile():
    """Protected route - shows user profile"""
    return render_template('profile.html', user=g.user)

@app.route('/logout')
def logout():
    """Logout and redirect to Auth0 logout"""
    logout_url = _run_async(
        get_auth0_client().logout(
            LogoutOptions(return_to=_default_logout_return_to()),
            g.store_options,
        )
    )
    return redirect(logout_url)



def _get_session_state() -> dict:
    user = g.get("user") or {}
    session_id = user.get("sub") or session.get("session_id")
    if not session_id:
        session_id = str(uuid4())
        session["session_id"] = session_id
    if session_id not in conversation_store:
        conversation_store[session_id] = {
            "chat_history": [],
            "last_pipeline_output": "",
        }
    return conversation_store[session_id]


@app.route("/")
@login_required_page
def home():
    return render_template("index.html", user=g.user)


@app.route("/about")
def about():
    return render_template("about.html", user=_run_async(_get_current_user()))


@app.route("/academic")
@login_required_page
def academic():
    return render_template("academic.html", user=g.user)


@app.route("/business")
@login_required_page
def business():
    return render_template("business.html", user=g.user)


@app.route("/community")
@login_required_page
def community():
    return render_template("community.html", user=g.user)


@app.route("/consumer")
@login_required_page
def consumer():
    return render_template("consumer.html", user=g.user)


@app.route("/government")
@login_required_page
def government():
    return render_template("government.html", user=g.user)


@app.route("/response", methods=["POST"])
@login_required_api
def workFlowRoute():
    user_text = request.form.get("userInput", "")
    mode = request.form.get("mode", "analyze").strip().lower()
    workflow = request.form.get("workflow", "community").strip().lower()

    if mode not in {"analyze", "followup"}:
        mode = "analyze"

    if workflow not in {"community", "consumer", "academic", "business", "government"}:
        workflow = "community"

    session_state = _get_session_state()
    result = asyncio.run(
        ecooptima.main(
            user_text, mode=mode, workflow=workflow, session_state=session_state
        )
    )
    img_urls = []
    folder_env = os.environ.get("ECOOPTIMA_LOG_DIR")
    if folder_env and mode == "analyze":
        folder = Path(folder_env)
        if folder.exists():
            for p in sorted(folder.iterdir()):
                if p.suffix.lower() == ".png":
                    relative_path = p.relative_to("response_log")
                    img_urls.append(
                        url_for("response_log_file", filename=relative_path.as_posix())
                    )

    return jsonify({"result": result, "img_urls": img_urls})


@app.route("/reset", methods=["POST"])
@login_required_api
def reset_conversation():
    user = g.get("user") or {}
    session_id = user.get("sub") or session.get("session_id")
    if session_id and session_id in conversation_store:
        conversation_store[session_id] = {
            "chat_history": [],
            "last_pipeline_output": "",
        }
    return jsonify({"status": "ok", "message": "Conversation context cleared."})


@app.route("/response_log/<path:filename>")
@login_required_page
def response_log_file(filename: str):
    return send_from_directory("response_log", filename)


port = int(os.environ.get("PORT", 10000))

if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=port)  # DEPLOYMENT FOR ONLINE HOST --- DO NOT COMMENT OUT DURING COMMITS
    app.run(debug=True)               # DEPLOYMENT FOR LOCAL HOST --- THIS MUST BE LEFT COMMNETED OUT DURING COMMITS
