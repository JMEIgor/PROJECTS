from flask import Flask, request, render_template, jsonify
import requests
import os


app = Flask(__name__)

# Substitua 'YOUR_API_KEY' pela sua chave de API do OpenAI
API_KEY = os.getenv("OPENAI_API_KEY")
API_URL = 'https://api.openai.com/v1/chat/completions'

def call_chatgpt_api(prompt):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}'
    }
    data = {
        'model': 'gpt-4',  # Usando o modelo GPT-4
        'messages': [
            {'role': 'system', 'content': 'You are ChatGPT, a large language model.'},
            {'role': 'user', 'content': prompt}
        ]
    }
    response = requests.post(API_URL, headers=headers, json=data)
    response_json = response.json()
    return response_json

@app.route('/', methods=['GET', 'POST'])
def index():
    response = None
    if request.method == 'POST':
        user_prompt = request.form['prompt']
        api_response = call_chatgpt_api(user_prompt)
        response = api_response['choices'][0]['message']['content']
    return render_template('index.html', response=response)

if __name__ == '__main__':
    app.run(debug=True)
