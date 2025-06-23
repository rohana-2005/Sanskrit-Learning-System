from flask import Flask, render_template, jsonify, send_file
from flask_cors import CORS
import json
import random

app = Flask(__name__)
CORS(app)  # Enable CORS

# Load sentences data
with open('sentences.json', 'r', encoding='utf-8') as f:
    sentences = json.load(f)

@app.route('/')
def serve_game():
    return send_file('sent_game.html')

@app.route('/get_random_sentence')
def get_random_sentence():
    sentence = random.choice(sentences)
    return jsonify({
        'sentence': sentence['sentence'],
        'subject': sentence['subject'],  # Send full object
        'object': sentence['object'],    # Send full object  
        'verb': sentence['verb'],        # Send full object
        'hint': {
            'subject': {
                'gender': sentence['subject']['gender'] if sentence['subject'] else None,
                'number': sentence['subject']['number'] if sentence['subject'] else None
            } if sentence['subject'] else None,
            'object': {
                'gender': sentence['object']['gender'] if sentence['object'] else None,
                'number': sentence['object']['number'] if sentence['object'] else None
            } if sentence['object'] else None,
            'verb': {
                'person': sentence['verb']['person'],
                'number': sentence['verb']['number'],
                'class': sentence['verb']['class'],
                'meaning': sentence['verb']['meaning']
            }
        }
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)