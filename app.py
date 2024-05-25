# app.py
import os.path

from flask import Flask, render_template
from flask_socketio import SocketIO
import time
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

@app.route('/')
def index():
    print(os.listdir("."))
    print(os.path.exists("templates/index.html"))
    return render_template('index.html')

def background_thread():
    """Example of how to send server-generated events to clients."""
    count = 0
    while True:
        time.sleep(1)
        count += 1
        socketio.emit('server_response', {'data': f'Count {count}'})

@socketio.on('connect')
def test_connect():
    return
    # emit('server_response', {'data': 'Connected'})

if __name__ == '__main__':
    threading.Thread(target=background_thread).start()
    socketio.run(app, allow_unsafe_werkzeug=True)
