from flask import Flask, render_template

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/')
def index():
    return render_template("index.html")


if __name__ == '__main__':
    app.run(debug=True, port=8000)
    # For some reason the browser says refused to connect. 
    # Gemini AI said to change the port from 5000 to 8000 for Mac.
    # This change works.

