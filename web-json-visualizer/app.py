from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    """Serves the main page of the application."""
    return render_template('index.html')

if __name__ == '__main__':
    # Note: debug=True is for development only.
    app.run(debug=True, port=5001)