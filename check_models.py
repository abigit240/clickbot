import google.generativeai as genai

# Replace with your actual API key
import os
my_secret = os.environ['GEMINI_KEY']

genai.configure(api_key=my_secret)

print("Fetching available models...")
for model in genai.list_models():
    print(model.name)
