from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import os

app = Flask(__name__)

# Set API key for Gemini AI
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

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
                
                // Display user message
                const chatBox = document.getElementById('chat-box');
                chatBox.innerHTML += `<p><strong>You:</strong> ${message}</p>`;
                messageInput.value = '';
                
                // Send to server
                fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                })
                .then(response => response.json())
                .then(data => {
                    chatBox.innerHTML += `<p><strong>AI:</strong> ${data.response}</p>`;
                    chatBox.scrollTop = chatBox.scrollHeight;
                })
                .catch(error => {
                    console.error('Error:', error);
                    chatBox.innerHTML += `<p><strong>Error:</strong> Failed to get response</p>`;
                });
            }
            
            // Allow Enter key to send message
            document.getElementById('message-input').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        </script>
    </body>
    </html>
    """

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")

    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(user_message)
        
        # Handle the response properly - response structure may vary based on API version
        if hasattr(response, 'text'):
            # For newer versions of the Gemini API
            return jsonify({"response": response.text})
        elif hasattr(response, 'parts'):
            # Alternative response structure
            return jsonify({"response": ''.join(part.text for part in response.parts)})
        else:
            # Fallback for other response structures
            return jsonify({"response": str(response)})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"response": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
