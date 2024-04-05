from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
from openai import OpenAI

app = Flask(__name__)
CORS(app)  # This is necessary to handle CORS if your Flutter app and this backend are on different domains.

OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions'
API_KEY = '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'  # Replace with your OpenAI API key

@app.route('/generate-response', methods=['POST'])
def ask():
    data = request.json
    print(data)
    user_message = data.get('prompt')
    messages_list = data.get('messages', [])  # Extract messages from the request, default to empty list if not present
    print(messages_list)
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
    }

    # Adjusted for the Chat API
    payload = {
        
        "model": "gpt-3.5-turbo",  # You can adjust the model if needed
        "messages": messages_list,
        
        "max_tokens": 150,  # For example, limit the response to 150 tokens
        "temperature": .5,
        
    
    }
  

    
    client = OpenAI(api_key="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")

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
       
        
        messages=messages_list
        ,
        
        max_tokens=150
    )

    print(response.choices[0].message.content)

  

    # response = requests.post(OPENAI_API_URL, headers=headers, data=json.dumps(payload))
 
  
    return jsonify({'data': response.choices[0].message.content.strip()})


if __name__ == '__main__':
    app.run(debug=True, port=3000)

