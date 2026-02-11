import ecooptima
from flask import Flask, request, render_template, url_for, jsonify, send_from_directory
import asyncio
import os
from pathlib import Path

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/community")
def community():
    return render_template("community.html")

@app.route("/response", methods=["POST"])
def workFlowRoute():
    user_text = request.form.get("userInput", "")
    result = asyncio.run(ecooptima.main(user_text))

    if hasattr(result, "model_dump"):  # Pydantic v2
        result = result.model_dump()
    elif hasattr(result, "dict"):  # Pydantic v1 fallback
        result = result.dict()

    img_urls = []
    folder_env = os.environ.get("ECOOPTIMA_LOG_DIR")
    if folder_env:
        folder = Path(folder_env)
        if folder.exists():
            for p in sorted(folder.iterdir()):
                if p.suffix.lower() == ".png":
                    img_urls.append(
                        url_for("response_log_file", filename=p.name))

    return jsonify({"result": result, "img_urls": img_urls})


@app.route("/response_log/<path:filename>")
def response_log_file(filename: str):
    return send_from_directory("response_log", filename)


if __name__ == "__main__":
    app.run(debug=True)
