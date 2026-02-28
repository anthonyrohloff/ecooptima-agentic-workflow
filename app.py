import ecooptima
from flask import (
    Flask,
    request,
    render_template,
    url_for,
    jsonify,
    send_from_directory,
    session,
)
import asyncio
import os
from pathlib import Path
from uuid import uuid4

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "ecooptima-dev-secret")


conversation_store: dict[str, dict] = {}


def _get_session_state() -> dict:
    session_id = session.get("session_id")
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
def home():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/community")
def community():
    return render_template("community.html")


@app.route("/academic")
def academic():
    return render_template("academic.html")


@app.route("/consumer")
def consumer():
    return render_template("consumer.html")


@app.route("/government")
def government():
    return render_template("government.html")


@app.route("/response", methods=["POST"])
def workFlowRoute():
    user_text = request.form.get("userInput", "")
    mode = request.form.get("mode", "analyze").strip().lower()
    workflow = request.form.get("workflow", "community").strip().lower()

    if mode not in {"analyze", "followup"}:
        mode = "analyze"

    if workflow not in {"community", "consumer"}:
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
def reset_conversation():
    session_id = session.get("session_id")
    if session_id and session_id in conversation_store:
        conversation_store[session_id] = {
            "chat_history": [],
            "last_pipeline_output": "",
        }
    return jsonify({"status": "ok", "message": "Conversation context cleared."})


@app.route("/response_log/<path:filename>")
def response_log_file(filename: str):
    return send_from_directory("response_log", filename)


if __name__ == "__main__":
    app.run(debug=True)
