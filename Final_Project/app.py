from flask import session, Flask, render_template, request, redirect, url_for, flash
from flask_session import Session
from flask_socketio import SocketIO, emit, join_room, leave_room
import sqlite3
import bcrypt
from functools import wraps
import chess
from uuid import uuid4
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
        if tictactoe_rooms[i]["user_id"] == session.get("user_id"):
            del tictactoe_rooms[i]

    session.clear()
    return redirect("/login")

@app.route("/tictacrooms", methods=["GET", "POST"])
@login_required
def tictacrooms():
    global tictactoe_rooms, games

    if request.method == "POST":
        # Handle room creation
        if request.form.get("create"):
            # Check if the user already has a room
            existing_room = next((room for room in tictactoe_rooms if room["user_id"] == session.get("user_id")), None)
            if existing_room:
                return redirect(f"/tictactoe?room={existing_room['room_id']}")  # Redirect to existing room

            # Generate a unique room ID
            room_id = random.randint(10000, 99999)
            while room_id in games:  # Ensure the room_id is unique
                room_id = random.randint(10000, 99999)

            # Create a new room
            new_room = {
                "room_id": room_id,
                "user_id": session.get("user_id"),
                "username": session.get("username"),
                "players": 1  # Starting with one player
            }
            tictactoe_rooms.append(new_room)

            # Initialize the game state
            games[room_id] = {
                "players": [session.get("user_id")],  # Add the creator as the first player
                "board": [None] * 9,
                "current_turn": session.get("user_id")
            }

            print(f"Room created: {new_room}")  # Debugging statement
            print(f"Current games: {games}")  # Debugging statement

            return redirect(f"/tictactoe?room={room_id}")  # Redirect to the new game room

        # Handle joining a room
        elif request.form.get("join"):
            room_id = request.form.get("room_id")  # Get the room ID from the form
            if not room_id:  # Check if room_id is not present
                flash('Room ID is required', 'error')  # Flash message if room ID is not provided
                return redirect('/tictacrooms')

            try:
                room_id = int(room_id)  # Convert room_id to an integer
            except ValueError:
                flash('Invalid room ID', 'error')  # Flash message if room ID is invalid
                return redirect('/tictacrooms')

            # Find the room in tictactoe_rooms by the room_id
            room = next((r for r in tictactoe_rooms if r["room_id"] == room_id), None)

            print(f"Attempting to join room: {room_id}")  # Debugging statement
            print(f"Current players in room: {games.get(room_id, {}).get('players', [])}")  # Debugging statement

            # Check if the room exists
            if room:
                # Check if the game exists and if there's space for a new player
                if room_id in games:
                    if len(games[room_id]["players"]) < 2:
                        # Add user to the players list
                        games[room_id]["players"].append(session.get("user_id"))  
                        return redirect(f"/tictactoe?room={room_id}")  # Redirect to the game room
                    else:
                        flash('Room is full', 'error')  # Flash message if the room is full
                else:
                    flash('Game does not exist', 'error')  # Flash message if the game does not exist
            else:
                flash('Room does not exist', 'error')  # Flash message if room does not exist
            
            return redirect('/tictacrooms')  # Redirect back to the rooms list if any checks fail

    # Render the rooms page
    return render_template("tictacrooms.html", rooms=tictactoe_rooms)

@app.route("/tictactoe", methods=["GET", "POST"])
@login_required
def tictactoe():
    room_id_str = request.args.get("room")
    try:
        room_id = int(room_id_str)
    except (ValueError, TypeError):
        return "Room not found!", 404  # Return 404 if room ID is invalid

    if room_id not in games:
        return "Room not found!", 404  # Return 404 if room ID does not exist

    room_info = games[room_id]
    return render_template("tictactoe.html", room=room_info)  # Render game page

@socketio.on('join_game')
def on_join(data):
    room_id = data['room']
    player_id = session['user_id']
    game = games.get(room_id)

    # Ensure the game exists and there is space for players
    if game and len(game['players']) < 2:
        if player_id not in game['players']:
            game['players'].append(player_id)
            join_room(room_id)  # Add user to room
            socketio.emit('message', {'msg': f'Player {player_id} has joined room {room_id}'}, to=room_id)
            if len(game['players']) == 2:
                socketio.emit('message', {'msg': 'Game is ready to start!'}, to=room_id)
        else:
            socketio.emit('message', {'msg': 'You are already in this room!'}, room=request.sid)
    else:
        socketio.emit('message', {'msg': 'Room is full or does not exist'}, room=request.sid)

@socketio.on('cell_click')
def handle_cell_click(data):
    room_id = data['roomId']
    cell_index = data['cell']
    current_class = data['currentClass']
    player_id = session['user_id']  # Get current player ID
    game = games.get(room_id)

    # Debug: Log current turn and player trying to play
    print(f"Current turn: {game['current_turn']}, Player trying to play: {player_id}")

    if game:
        if player_id == game['current_turn'] and game['board'][cell_index] is None:
            game['board'][cell_index] = current_class  # Update the board with the current player's move

            # Check for win or draw
            if check_winner(game['board'], current_class):
                emit('message', {'msg': f'Player {current_class} wins!'}, to=room_id)
                emit('reset_board', to=room_id)  # Reset the board for the next game
                return
            elif all(cell is not None for cell in game['board']):  # Check for draw
                emit('message', {'msg': 'It\'s a draw!'}, to=room_id)
                emit('reset_board', to=room_id)  # Reset the board for the next game
                return

            # Update the turn to the next player
            next_player_index = (game['players'].index(player_id) + 1) % 2
            game['current_turn'] = game['players'][next_player_index]  # Switch turn to the next player
            
            # Send updated game state
            emit('update_board', {'cell': cell_index, 'currentClass': current_class}, to=room_id)
        else:
            emit('message', {'msg': 'Not your turn or invalid move!'}, room=request.sid)
    else:
        emit('message', {'msg': 'Game not found!'}, room=request.sid)



@socketio.on('restart_game')
def restart_game(data):
    room_id = data['room']
    game = games.get(room_id)
    if game:
        game['board'] = [None] * 9  # Reset the board
        game['current_turn'] = game['players'][0]  # Reset to the first player
        socketio.emit('reset_board', to=room_id)  # Notify clients to reset their boards


def check_winner(board, player):
    # Define winning combinations
    winning_combinations = [
        [0, 1, 2],  # Top row
        [3, 4, 5],  # Middle row
        [6, 7, 8],  # Bottom row
        [0, 3, 6],  # Left column
        [1, 4, 7],  # Middle column
        [2, 5, 8],  # Right column
        [0, 4, 8],  # Diagonal
        [2, 4, 6],  # Diagonal
    ]
    
    # Check if any winning combination is satisfied
    for combo in winning_combinations:
        if all(board[i] == player for i in combo):
            return True
    return False

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)



@app.route("/chessboard/<roomid>")
@login_required
def chessboard(roomid):
    global room_colors
    global rooms_boards
    username = session.get("username")

    if roomid not in rooms_boards:
        rooms_boards[roomid] = chess.Board()

    board_fen = rooms_boards[roomid].fen()

    if roomid not in room_colors:
        room_colors[roomid] = {'white': None, 'black': None, 'visibility': 'public', 'room_id': roomid}
    
    color = room_colors[roomid]


    if color['white'] == username:
        currentplayer = 'white'
        return render_template("chess.html", board_fen=board_fen, currentplayer=currentplayer, roomid=roomid)
    
    elif color['black'] == username:
        currentplayer = 'black'
        return render_template("chess.html", board_fen=board_fen, currentplayer=currentplayer, roomid=roomid)
    
    elif color['white'] is None:
        color['white'] = username
        currentplayer = 'white'
        return render_template("chess.html", board_fen=board_fen, currentplayer=currentplayer, roomid=roomid)
    
    elif color['black'] is None:
        color['black'] = username
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

        if str(piece) == 'K' and chess_move.from_square == 4 and chess_move.to_square in (6,7) and board.has_kingside_castling_rights(chess.WHITE):
            board.push(chess_move)
            if board.is_check():
                print("sending OO")
                response_data.update({"success": True, "checkb": True, "OO": True})
            else:
                response_data.update({"success": True, "board_fen": board_fen, 'OO': True})
            emit('move_response', response_data, room=room)
            socketio.emit('update_board', response_data, room=room)
            return

        elif str(piece) == 'K' and chess_move.from_square == 4 and chess_move.to_square in (2,1,0) and board.has_queenside_castling_rights(chess.WHITE):
            board.push(chess_move)
            if board.is_check():
                response_data.update({"success": True, "checkb": True, "OOO": True})
            else:
                response_data.update({"success": True, "board_fen": board_fen, 'OOO': True})
            emit('move_response', response_data, room=room)
            socketio.emit('update_board', response_data, room=room)
            return

        elif str(piece) == 'k' and chess_move.from_square == 60 and chess_move.to_square in (62,63) and board.has_kingside_castling_rights(chess.BLACK):
            board.push(chess_move)
            if board.is_check():
                response_data.update({"success": True, "checkw": True, "oo": True})
            else:
                response_data.update({"success": True, "board_fen": board_fen, 'oo': True})
                

            emit('move_response', response_data, room=room)
            socketio.emit('update_board', response_data, room=room)
            return


        elif str(piece) == 'k' and chess_move.from_square == 60 and chess_move.to_square in (58,57,56) and board.has_queenside_castling_rights(chess.BLACK):
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
                socketio.emit('update_board', response_data, room=room)
                emit('move_response', response_data, room=room)
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
        public_rooms = []
        for room_id, room_info in room_colors.items():  # room_id is the key, room_info is the dict
            if room_info['visibility'] == "public":
                # Check if both white and black are not filled
                if room_info['white'] is None or room_info['black'] is None:
                    username = room_info['white'] or room_info['black']  # Find the player who joined
                    if username:
                        color = "white" if room_info['white'] == username else "black"  # Determine the color
                        public_rooms.append({
                            "room_id": room_id, 
                            "username": username,
                            "color": color  # Add color information
                        })
        
        return render_template("searchchess.html", rooms=public_rooms)
    else:
        room = str(uuid4())
        color = request.form.get('color')
        visibility = str(request.form.get('visibility'))
        if room and color:
            username = session.get("username")

            if room not in room_colors:
                room_colors[room] = {'white': None, 'black': None, 'visibility': visibility, 'room_id': room}

            if room_colors[room][color] is None:
                room_colors[room][color] = username
                return redirect(url_for('chessboard', roomid=room))
            
            return redirect(url_for('chessboard', roomid=room))
        elif room:
            return redirect(url_for('chessboard', roomid=room))
        else:
            return render_template("searchchess.html")
