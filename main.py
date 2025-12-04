from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return {"message": "Python API is running on Render!"}

@app.route("/scan")
def scan():
    url = request.args.get("url")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    # Example only — replace with real logic later
    return jsonify({
        "url": url,
        "status": "safe",
        "info": "This is demo result"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
