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
                    console.log("Received data:", data);
                    if (data && data.response) {
                        chatBox.innerHTML += `<p><strong>AI:</strong> ${data.response}</p>`;
                    } else {
                        chatBox.innerHTML += `<p><strong>AI:</strong> No response received</p>`;
                        console.error('Empty response:', data);
                    }
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
    print(f"Received message: {user_message}")

    try:
        # Print API key status (not the key itself, just if it exists)
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return jsonify({"response": "ERROR: GEMINI_API_KEY is not set. Please add it to your Secrets."}), 500
        
        print(f"API key present: {bool(api_key)}")
        print(f"API key length: {len(api_key)}")
        
        # Use API key from environment
        genai.configure(api_key=api_key)
        
        # List available models to check what's available
        print("Fetching available models...")
        try:
            models = genai.list_models()
            if not models:
                return jsonify({"response": "No models available. Your API key may be invalid or have insufficient permissions."}), 500
                
            print("Available models:")
            for model in models:
                print(f"- {model.name}")
                # Print more details about capabilities
                if hasattr(model, 'supported_generation_methods'):
                    print(f"  Supported methods: {model.supported_generation_methods}")
                    
            # Get only models that support text generation
            text_models = [m for m in models if hasattr(m, 'supported_generation_methods') and 
                          'generateContent' in m.supported_generation_methods]
            
            if not text_models:
                return jsonify({"response": "No models supporting text generation found. Please check your API key permissions."}), 500
                
            print(f"Found {len(text_models)} models supporting text generation")
            
            # Try to use these models in order of preference
            gemini_models = [
                "gemini-1.5-flash",
                "gemini-1.5-pro",
                "gemini-1.0-pro",
                "gemini-pro"
            ]
            
            # Use the full model name from the API (models/name)
            model_name = None
            
            # First try the preferred models in order
            for preferred in gemini_models:
                for m in models:
                    if preferred in m.name.lower():
                        model_name = m.name
                        print(f"Using preferred model: {model_name}")
                        break
                if model_name:
                    break
                    
            # If no preferred model found, try any model that supports generateContent
            if not model_name and text_models:
                model_name = text_models[0].name
                print(f"Using first available text model: {model_name}")
                
            if not model_name:
                return jsonify({"response": "No suitable models available. Please check your API key."}), 500
                
            print(f"Final model selection: {model_name}")
            
            # Use the model without the "models/" prefix if it has one
            model_id = model_name.split('/')[-1] if '/' in model_name else model_name
            print(f"Using model ID: {model_id}")
            
            model = genai.GenerativeModel(model_id)
            response = model.generate_content(user_message)
            
        except Exception as model_error:
            print(f"Error listing models: {str(model_error)}")
            return jsonify({"response": f"Error listing models: {str(model_error)}. Please check your API key."}), 500
        
        print(f"Response type: {type(response)}")
        print(f"Response dir: {dir(response)}")
        
        # More detailed handling of response structure
        response_text = None
        
        if hasattr(response, 'text'):
            print("Using response.text")
            response_text = response.text
        elif hasattr(response, 'parts') and response.parts:
            print("Using response.parts")
            response_text = ''.join(part.text for part in response.parts)
        elif hasattr(response, 'candidates') and response.candidates:
            print("Using response.candidates")
            candidates = response.candidates
            if candidates and hasattr(candidates[0], 'content'):
                content = candidates[0].content
                if hasattr(content, 'parts') and content.parts:
                    response_text = ''.join(str(part.text) for part in content.parts)
        
        if response_text is None:
            print(f"Fallback to string representation: {str(response)}")
            response_text = f"Could not parse response: {str(response)}"
            
        print(f"Final response text: {response_text}")
        return jsonify({"response": response_text})

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error: {str(e)}")
        print(f"Details: {error_details}")
        return jsonify({"response": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
