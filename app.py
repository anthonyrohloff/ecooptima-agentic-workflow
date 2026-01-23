import ecooptima
from flask import Flask, request, render_template_string
from ecooptima import main
import asyncio

app = Flask(__name__)


@app.route("/")
def home():
    return open("index.html").read()


@app.route("/response", methods=["POST"])
def workFlowRoute():
    user_text = request.form["userInput"]
    result = asyncio.run(ecooptima.main(user_text))
    return result


if __name__ == "__main__":
    app.run(debug=True)
