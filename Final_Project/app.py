from flask import session, Flask, render_template, request, redirect, url_for
from flask_session import Session
from flask_socketio import SocketIO, emit, join_room, leave_room
import sqlite3
import bcrypt
from functools import wraps
import chess
from uuid import uuid5, uuid4
import random
import time

app = Flask(__name__)

socketio = SocketIO(app)

rooms_boards = {}
room_colors = {}
board = chess.Board()

games = {}

tictactoe_rooms = []
# after closing website session deletes set to True if you want permament session.
app.config["SESSION_PERMANENT"] = True
# Save session in filesystem insted of browser
app.config["SESSION_TYPE"] = "filesystem"
# Initilise session
Session(app)

def login_required(f):

    # ez kell hogy brijuk ugy hogy @login_required

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # if no session
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
        
    return decorated_function


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    #Landing page after login

    #Temporary simulate loged in user:
    # nem birod  jinjaba be rakni mert ha nem letezik a session["user_id"] akkor hibat fog ki adni iffel meg kell csinalni

    # valahogy igy
    if session.get("user_id") is None:
        return render_template("index.html")
    else:
        return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # TODO
    if session.get("user_id") is not None:
        # if we are logged in then prompt to logout
        return redirect("/")
    else:
        if request.method == "GET":
            # base case
            return render_template("login.html")
        # else if POST.
        else:
            username = request.form.get("username")
            password = request.form.get("password")

            if not username or not password:
                return render_template("login.html", placeholder="Missing password or username")
            
            password = password.encode("utf-8")

            db = sqlite3.connect("users.db")
            cursor = db.cursor()

            try:

                # began transaction
                db.execute("BEGIN TRANSACTION")

                cursor.execute("SELECT uuid, hash FROM users WHERE username = ?", (username,))
                user = cursor.fetchone()
                
                if user and bcrypt.checkpw(password=password, hashed_password=user[1]):
                    session["user_id"] = user[0]
                    session["username"] = username
                    return redirect("/")

                else:
                    return render_template("login.html", placeholder="Invalid password and/or username")
                
            except sqlite3.Error as e:
                print(f"DB error: {e}")
                return render_template("login.html", placeholder="Something went wrong")
            finally:
                cursor.close()
                db.close()



@app.route("/register", methods=["GET", "POST"])
def register():
    # TODO
    if session.get("user_id") is not None:
        # if we are logged in then go to index
        return redirect("/")
    
    else:
        if request.method == "GET":
            # base case
            return render_template("register.html")
        # else if POST.
        else:

            username = request.form.get("username")
            password = request.form.get("password")
            password2 = request.form.get("password2")

            if not username or not password or not password2:
                return render_template("register.html", placeholder="Missing password or username")

            elif password != password2:
                return render_template("register.html", placeholder="Passwords must match")
            
            elif len(password) < 8:
                return render_template("register.html", placeholder="Passwords must be atleast 8 characters")
            
            password2 = password.encode("utf-8")
            phash = bcrypt.hashpw(password=password2, salt=bcrypt.gensalt())

            db = sqlite3.connect("users.db")
            cursor = db.cursor()

            try:
                
                # begain transaction
                db.execute("BEGIN TRANSACTION")

                cursor.execute("INSERT INTO users (uuid, hash, username) VALUES(?, ?, ?)", (str(uuid4()), phash, username))

                db.commit()

                cursor.execute("SELECT uuid FROM users WHERE username = ?", (username,))
                uuid = cursor.fetchone()

                session["user_id"] = uuid[0]
                session["username"] = username

                return redirect("/")
            except ValueError:
                return render_template("register.html", placeholder="Username taken")
            
            except sqlite3.Error as e:
                # rollback if error
                db.rollback()
                print(f"Database error: {e}")
                return render_template("register.html", placeholder="Username taken")
            
            finally:
                cursor.close()
                db.close()

@app.route("/logout")
@login_required
def logout():

    global tictacrooms

    for i in range(len(tictactoe_rooms) - 1, -1, -1):  # Iterate in reverse to avoid skipping elements
        if tictactoe_rooms[i]["user_id"] == session["user_id"]:
            del tictactoe_rooms[i]

    session.clear()
    return redirect("/login")

@app.route("/tictacrooms", methods=["GET", "POST"])
@login_required
def tictacrooms():

    global tictactoe_rooms, games

    if request.method == "POST" and request.form.get("create"):

        for room in tictactoe_rooms:
            if room["user_id"] == session["user_id"]:
                return redirect(f"/tictactoe?room={room['room_id']}")
        
        room_id = random.randint(10000, 99999)
        while room_id in games:  # Ensure the room_id is unique
            room_id = random.randint(10000, 99999)

        new_room = {
                "room_id" : room_id,
                "user_id" : session["user_id"],
                "username" : session["username"],
                "players" : 1
                }
        tictactoe_rooms.append(new_room)

        games[room_id] = {
            "players" : [session["user_id"]],
            "board" : [None] *9,
            "current_turn" : session["user_id"]
        }


        print(f"Room created: {new_room}")  # Debugging statement
        print(f"Current games: {games}")  # Debugging statement

        return redirect(f"/tictactoe?room={room_id}")

    return render_template("tictacrooms.html", rooms=tictactoe_rooms)

@app.route("/tictactoe", methods=["GET", "POST"])
@login_required
def tictactoe():
    global games
    

    room_id_str = request.args.get("room")

    print(f"Accessing room: {room_id_str}")  # Debugging statement

    try:
        room_id = int(room_id_str)  # Convert to integer
    except ValueError:
        print("Invalid room ID format!")  # Debugging statement
        return "Room not found!", 404


    if room_id not in games:
        print("Room not found!")
        return "Room not found!", 404
    
    room_info = games[room_id]
    return render_template("tictactoe.html", room=room_info)

@socketio.on('join_game')
def on_join(data):
    room_id = data['room']
    player_id = session['user_id']  # Get the current player's ID
    game = games.get(room_id)

    if game and len(game['players']) < 2:
        if player_id not in game['players']:
            game['players'].append(player_id)
            join_room(room_id)
            emit('message', f'Player {player_id} has joined room {room_id}', to=room_id)
            if len(game['players']) == 2:
                emit('message', 'Game is ready to start!', to=room_id)
        else:
            emit('message', 'You are already in this room!', to=player_id)
    else:
        emit('message', 'Room is full or does not exist', to=player_id)  # Prevent more than 2 players

@socketio.on('cell_click')
def handle_cell_click(data):
    room_id = data['roomId']
    cell_index = data['cell']
    current_class = data['currentClass']
    player_id = session['user_id']  # Get the current player's ID

    game = games.get(room_id)

    # Ensure the move is from the current player
    if game:
        if player_id == game['current_turn'] and game['board'][cell_index] is None:
            # Update the board state
            game['board'][cell_index] = current_class
            
            # Swap turns
            next_player = game['players'][1] if game['current_turn'] == game['players'][0] else game['players'][0]
            game['current_turn'] = next_player
            
            # Broadcast the move to the room
            emit('update_board', {'cell': cell_index, 'currentClass': current_class}, to=room_id)
        else:
            emit('message', 'Not your turn or invalid move!', to=player_id)
    else:
        emit('message', 'Game not found!', to=player_id)

@socketio.on('restart_game')
def restart_game(data):
    room_id = data['room']
    game = games.get(room_id)
    if game:
        game['board'] = [None] * 9  # Reset the board
        game['current_turn'] = game['players'][0]  # Set turn to the first player
        emit('reset_board', to=room_id)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)




@app.route("/chessboard/<roomid>")
@login_required
def chessboard(roomid):
    global room_colors
    global rooms_boards
    user_id = session.get("user_id")

    if roomid not in rooms_boards:
        rooms_boards[roomid] = chess.Board()

    board_fen = rooms_boards[roomid].fen()

    if roomid not in room_colors:
        room_colors[roomid] = {'white': None, 'black': None}
    
    color = room_colors[roomid]


    if color['white'] == user_id:
        currentplayer = 'white'
        return render_template("chess.html", board_fen=board_fen, currentplayer=currentplayer, roomid=roomid)
    
    elif color['black'] == user_id:
        currentplayer = 'black'
        return render_template("chess.html", board_fen=board_fen, currentplayer=currentplayer, roomid=roomid)
    
    elif color['white'] is None:
        color['white'] = user_id
        currentplayer = 'white'
        return render_template("chess.html", board_fen=board_fen, currentplayer=currentplayer, roomid=roomid)
    
    elif color['black'] is None:
        color['black'] = user_id
        currentplayer = 'black'
        return render_template("chess.html", board_fen=board_fen, currentplayer=currentplayer, roomid=roomid)
    else:
        return "Room full", 403 # Prevent more than 2 players


# if we recive join
@socketio.on('join')
def on_join(data):
    username = session.get("user_id")
    room = data['room']  # room id will be passed from the client
    join_room(room)
    print(room)
    socketio.emit('message', {'msg': f'{username} has entered the room {room}.'}, room=room)

# if we leave
@socketio.on('leave')
def on_leave(data):
    username = session.get("user_id")
    room = data['room']  # room id will be passed from the client
    leave_room(room)
    socketio.emit('message', {'msg': f'{username} has left the room {room}.'}, room=room)

@socketio.on('move_piece')
@login_required
def handle_move(data):
    if not data or 'move' not in data or 'room' not in data:
        emit('move_response', {'success': False, 'error': 'Invalid request, move data missing'})
        return
    
    move = data['move']
    room = data['room']

    if room not in rooms_boards:
        emit('move_response', {"success": False, "error": "Room does not exist"})
    board = rooms_boards[room]

    try:    
        board_fen = board.fen()
        chess_move = chess.Move.from_uci(move)
        piece = board.piece_at(chess_move.from_square)

        # Prepare the base response with the move
        response_data = {"move": move}  # Include the move in all response

        if str(piece) == 'K' and chess_move.from_square == 4 and chess_move.to_square == 6 and board.has_kingside_castling_rights(chess.WHITE):
            board.push(chess_move)
            if board.is_check():
                print("sending OO")
                response_data.update({"success": True, "checkb": True, "OO": True})
            else:
                response_data.update({"success": True, "board_fen": board_fen, 'OO': True})
            emit('move_response', response_data, room=room)
            socketio.emit('update_board', response_data, room=room)
            return

        elif str(piece) == 'K' and chess_move.from_square == 4 and chess_move.to_square == 2 and board.has_queenside_castling_rights(chess.WHITE):
            board.push(chess_move)
            if board.is_check():
                response_data.update({"success": True, "checkb": True, "OOO": True})
            else:
                response_data.update({"success": True, "board_fen": board_fen, 'OOO': True})
            emit('move_response', response_data, room=room)
            socketio.emit('update_board', response_data, room=room)
            return

        elif str(piece) == 'k' and chess_move.from_square == 60 and chess_move.to_square == 62 and board.has_kingside_castling_rights(chess.BLACK):
            board.push(chess_move)
            if board.is_check():
                response_data.update({"success": True, "checkw": True, "oo": True})
            else:
                response_data.update({"success": True, "board_fen": board_fen, 'oo': True})
                

            emit('move_response', response_data, room=room)
            socketio.emit('update_board', response_data, room=room)
            return


        elif str(piece) == 'k' and chess_move.from_square == 60 and chess_move.to_square == 58 and board.has_queenside_castling_rights(chess.BLACK):
            board.push(chess_move)
            if board.is_check():
                response_data.update({"success": True, "checkw": True, "ooo": True})

            else:
                response_data.update({"success": True, "board_fen": board_fen, 'ooo': True})

            emit('move_response', response_data, room=room)
            socketio.emit('update_board', response_data, room=room)



        elif str(piece) == 'P' and chess.square_rank(chess_move.from_square) == 6:
            chess_move = chess.Move.from_uci(move + 'q')
            board.push(chess_move)
            if board.is_checkmate():
                response_data.update({"success": True, "board_fen": board_fen, "is_checkmate": True, "white": True})
                board.reset()
                emit('move_response', response_data, room=room)
                socketio.emit('update_board', response_data, room=room)

                return
            if board.is_check():
                print("in P promotion check")
                response_data.update({"success": True, "bcheck": True, "wpromotion": True})
                socketio.emit('update_board', response_data, room=room)
                return
            
            elif board.is_stalemate():
                board.reset()
                response_data.update({"success": True, "stalemate": True})
                emit('move_response', response_data, room=room)
                socketio.emit('update_board', response_data, room=room)
                return
            response_data.update({"success": True, "board_fen": board_fen, "is_checkmate": False, "wpromotion": True})
            emit('move_response', response_data, room=room)
            socketio.emit('update_board', response_data, room=room)


        elif str(piece) == 'p' and chess.square_rank(chess_move.from_square) == 1:
            chess_move = chess.Move.from_uci(move + 'q')
            board.push(chess_move)
            if board.is_checkmate():
                response_data.update({"success": True, "board_fen": board_fen, "is_checkmate": True, "black": True})
                board.reset()
                emit('move_response', response_data, room=room)
                socketio.emit('update_board', response_data, room=room)
                return
            
            if board.is_check():
                print("in P promotion check")
                response_data.update({"success": True, "wcheck": True, "bpromotion": True})
                socketio.emit('update_board', response_data, room=room)
                return
            elif board.is_stalemate():
                board.reset()
                response_data.update({"success": True, "stalemate": True})
                emit('move_response', response_data, room=room)
                socketio.emit('update_board', response_data, room=room)

                return
            response_data.update({"success": True, "board_fen": board_fen, "is_checkmate": False, "bpromotion": True})
            emit('move_response', response_data, room=room)
            socketio.emit('update_board', response_data, room=room)


        elif chess_move in board.legal_moves:
            board.push(chess_move)

            if board.is_stalemate():
                board.reset()
                response_data.update({"success": True, "stalemate": True})
                emit('move_response', response_data, room=room)
                socketio.emit('update_board', response_data, room=room)
                return

            elif board.is_checkmate():
                if board.outcome().winner == chess.WHITE:
                    response_data.update({"success": True, "board_fen": board_fen, "is_checkmate": True, "white": True})

                else:
                    response_data.update({"success": True, "board_fen": board_fen, "is_checkmate": True, "black": True})

                board.reset()
                emit('move_response', response_data, room=room)
                socketio.emit('update_board', response_data, room=room)
                return

            elif board.is_check() and board.turn == chess.WHITE:
                response_data.update({"success": True, "wcheck": True})
                socketio.emit('update_board', response_data, room=room)

            elif board.is_check() and board.turn == chess.BLACK:
                response_data.update({"success": True, "bcheck": True})
                socketio.emit('update_board', response_data, room=room)


            response_data.update({"success": True, "board_fen": board_fen, "is_checkmate": False})

            socketio.emit('update_board', response_data, room=room)

            emit('move_response', response_data, room=room)
        else:
            emit('move_response', {"success": False, "error": "Invalid move"}, room=room)
    except Exception as e:
        emit('move_response', {"success": False, "error": str(e)}, room=room)

@app.route("/chess", methods=["POST", "GET"])
@login_required
def croom():
    global room_colors
    if request.method == "GET":
        return render_template("searchchess.html")
    else:
        room = str(uuid4())
        color = request.form.get('color')
        if room and color:
            user_id = session.get("user_id")

            if room not in room_colors:
                room_colors[room] = {'white': None, 'black': None}

            if room_colors[room][color] is None:
                room_colors[room][color] = user_id
                return redirect(url_for('chessboard', roomid=room))
            
            return redirect(url_for('chessboard', roomid=room))
        elif room:
            return redirect(url_for('chessboard', roomid=room))
        else:
            return render_template("searchchess.html")
