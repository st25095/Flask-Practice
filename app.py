import json

from flask import Flask, render_template

app = Flask(__name__)
app.secret_key = 'your_secret_key'


@app.route('/')
def index():
    flowers = load_data()
    return render_template("index.html", flowers=flowers)

def load_data():
    with open('data/flowers.json') as file:
        flowers = json.load(file)
    return flowers

if __name__ == '__main__':
    app.run(debug=True, port=8000)
    # For some reason the browser says refused to connect. 
    # Gemini AI said to change the port from 5000 to 8000 for Mac.
    # This change works.

