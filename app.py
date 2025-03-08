from flask import Flask, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# Set API key for Gemini AI
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")

    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(user_message)

        return jsonify({"response": response.text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
