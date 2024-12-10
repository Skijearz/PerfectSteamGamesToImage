from __future__ import annotations

import os
import secrets

from dotenv import load_dotenv
from flask import (
    Flask,
    Response,
    jsonify,
    render_template,
    request,
    send_file,
)
from waitress import serve

import perfect_games_to_image

load_dotenv()

app = Flask(__name__)


user_tokens = {}

@app.route("/", methods=["GET", "POST"])
def home() ->  Response |tuple[Response, int] | str:
    if request.method == "POST":
        steam_id = request.form.get("steamid")
        if not steam_id:
            return jsonify({"error": "SteamID is required"}), 400
        token = generate_token()
        pig = perfect_games_to_image.PerfectGamesToImage(steam_id)
        if pig.run_from_non_async():
            user_tokens[token] = pig.steam_id
            return jsonify({"token": token})
        return jsonify({"error": "Something went wrong, try again"}),400
    return render_template("index.html")

@app.route("/download/<token>")
def download_file(token:str) ->  Response |tuple[Response, int]:
    if token in user_tokens:
        steamid = user_tokens[token]
        filename = f"{steamid}.zip"
        file_path = os.path.join("output", filename)
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
        return send_file(file_path, as_attachment=True, download_name=filename)
    return jsonify({"error": "Invalid or expired token"}), 403 # Forbidden if token is not found or invalid

def generate_token() -> str:
    return secrets.token_hex(16)

if __name__ == "__main__":
    serve(app,host="0.0.0.0", port=9898)
