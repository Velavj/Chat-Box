from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, send
from datetime import datetime
import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

rooms = {}

def generate_unique_code(length=4):
    while True:
        code = ''.join(random.choices(string.ascii_uppercase, k=length))
        if code not in rooms:
            break
    return code

@app.route('/', methods=['GET', 'POST'])
def home():
    session.clear()
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        join = request.form.get('join', False)
        create = request.form.get('create', False)

        if not name:
            return render_template('home.html', error="Please enter a name.")

        if join and not code:
            return render_template('home.html', error="Please enter a room code.", name=name)

        room = code
        if create:
            room = generate_unique_code()
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template('home.html', error="Room does not exist.", name=name)

        session['room'] = room
        session['name'] = name
        return redirect(url_for('room'))

    return render_template('home.html')

@app.route('/room')
def room():
    room = session.get('room')
    name = session.get('name')
    if room is None or name is None or room not in rooms:
        return redirect(url_for('home'))
    return render_template('room.html', code=room, messages=rooms[room]["messages"])

@socketio.on('message')
def message(data):
    room = session.get('room')
    name = session.get('name')
    if room not in rooms:
        return
    content = {
        "name": name,
        "message": data["data"],
        "timestamp": datetime.now().strftime("%H:%M")
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)

@socketio.on('connect')
def connect():
    room = session.get('room')
    name = session.get('name')
    if not room or not name or room not in rooms:
        return
    join_room(room)
    send({"name": name, "message": "has entered the room."}, to=room)
    rooms[room]["members"] += 1

@socketio.on('disconnect')
def disconnect():
    room = session.get('room')
    name = session.get('name')
    leave_room(room)
    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    send({"name": name, "message": "has left the room."}, to=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)