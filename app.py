from flask import Flask, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# Load API key from environment
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("ERROR: GEMINI_API_KEY is not set. Please add it to your environment variables.")

genai.configure(api_key=API_KEY)

# Preferred model selection (fixed match logic)
PREFERRED_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-pro-exp",
    "gemini-1.5-flash",
    "gemini-1.5-pro"
]

# Fetch available models once at startup
MODEL_NAME = None
print("Fetching available models...")

try:
    available_models = [model.name for model in genai.list_models()]
    print(f"Available models: {available_models}")

    # Find the first matching preferred model
    for preferred in PREFERRED_MODELS:
        MODEL_NAME = next((m for m in available_models if m.startswith(f"models/{preferred}")), None)
        if MODEL_NAME:
            break

    if not MODEL_NAME:
        raise ValueError("No suitable models found. Please check your API key permissions.")

    print(f"✅ Using model: {MODEL_NAME}")

except Exception as e:
    print(f"❌ Error fetching models: {e}")
    MODEL_NAME = None  # Avoid crashing, but server won't respond properly.

@app.route("/", methods=["GET"])
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gemini Chat App</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            h1 { color: #333; }
            #chat-container { display: flex; flex-direction: column; height: 400px; }
            #chat-box { flex-grow: 1; border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; overflow-y: auto; }
            #message-input { width: 80%; padding: 8px; }
            button { padding: 8px 16px; background-color: #4CAF50; color: white; border: none; cursor: pointer; }
        </style>
    </head>
    <body>
        <h1>Gemini AI Chat</h1>
        <div id="chat-container">
            <div id="chat-box"></div>
            <div>
                <input type="text" id="message-input" placeholder="Type your message...">
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>

        <script>
            function sendMessage() {
                const messageInput = document.getElementById('message-input');
                const message = messageInput.value.trim();
                if (!message) return;

                const chatBox = document.getElementById('chat-box');
                chatBox.innerHTML += `<p><strong>You:</strong> ${message}</p>`;
                messageInput.value = '';

                fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                })
                .then(response => response.json())
                .then(data => {
                    chatBox.innerHTML += `<p><strong>AI:</strong> ${data.response || "No response"}</p>`;
                    chatBox.scrollTop = chatBox.scrollHeight;
                })
                .catch(error => {
                    console.error('Error:', error);
                    chatBox.innerHTML += `<p><strong>Error:</strong> Failed to get response</p>`;
                });
            }

            document.getElementById('message-input').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') sendMessage();
            });
        </script>
    </body>
    </html>
    """

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    print(f"📩 Received message: {user_message}")

    if not MODEL_NAME:
        return jsonify({"response": "❌ ERROR: No valid AI model available. Please check API settings."}), 500

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(user_message)

        # Extract response text properly
        response_text = None

        if hasattr(response, "text") and response.text:
            response_text = response.text
        elif hasattr(response, "parts") and response.parts:
            response_text = ''.join(part.text for part in response.parts if hasattr(part, 'text'))
        elif hasattr(response, "candidates") and response.candidates:
            candidates = response.candidates
            if candidates and hasattr(candidates[0], 'content'):
                content = candidates[0].content
                if hasattr(content, 'parts') and content.parts:
                    response_text = ''.join(str(part.text) for part in content.parts)

        if not response_text:
            response_text = "⚠️ Could not parse response."

        return jsonify({"response": response_text})

    except Exception as e:
        print(f"❌ Error generating response: {e}")
        return jsonify({"response": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
