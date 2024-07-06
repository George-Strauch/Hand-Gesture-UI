import os.path
from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
from src.hand_watcher import Runner

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
    hand = Runner()
    while True:
        count += 1
        state = hand.process_frame(count)
        # print(state)
        socketio.emit('server_response', state)

@socketio.on('connect')
def test_connect():
    return
    # emit('server_response', {'data': 'Connected'})

if __name__ == '__main__':
    threading.Thread(target=background_thread).start()
    socketio.run(app, allow_unsafe_werkzeug=True)
