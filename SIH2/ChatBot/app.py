from flask import Flask, request, jsonify
from flask_cors import CORS
from backend_logic import process_user_query

app = Flask(__name__)

CORS(app)  
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400

    user_message = data['message']
    selected_float = data.get('selected_float') 

    print(f"Received message: '{user_message}', Selected float: '{selected_float}'")

    response_text = process_user_query(user_message, selected_float=selected_float)

    return jsonify({'response': response_text})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)