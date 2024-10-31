from flask import session, Flask, render_template, request, redirect, url_for
from flask_session import Session
from flask_socketio import SocketIO, emit, join_room, leave_room
import sqlite3
import bcrypt
from functools import wraps
import chess
from uuid import uuid4
import random

app = Flask(__name__)

socketio = SocketIO(app)

rooms_boards = {}
room_colors = {}
board = chess.Board()

tictac_game = {
        'room_id' : 'None',
        'current_turn' : 'None',
        'player_1' : 'None',
        'palyer_2' : 'None',
        'private' : 'None',
        'board_state' : [[None]*3]*3
        }

tictactoe_games = {}

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
    if session["username"] == None:
        return redirect("/login")
    else:
        username = session["username"]
    db = sqlite3.connect("users.db")
    cursor = db.cursor()
    try:
        cursor.execute("SELECT wins, loss FROM chess WHERE username = ?", (username,))
        chesst = cursor.fetchone()

        cursor.execute("SELECT wins, loss FROM tictactoe WHERE username = ?", (username,))
        tictactoet = cursor.fetchone()
        
    except ValueError:
        return ValueError, 302
    except sqlite3.Error as e:
        return e, 302
    finally:
        cursor.close()
        db.close()

    if chesst == None:
        return redirect("/login")
    if tictactoet == None:
        return redirect("/login")
    chess_wins = chesst[0]       
    chess_losses = chesst[1]     
    tictac_wins = tictactoet[0]      
    tictac_losses = tictactoet[1]     
    return render_template("index.html", chess_wins=chess_wins, chess_losses=chess_losses, tictac_wins=tictac_wins, tictac_losses=tictac_losses, username=username)

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
                
                db.execute("BEGIN TRANSACTION")
                cursor.execute("INSERT INTO chess (username, wins, loss) VALUES(?, 0, 0)", (username,))
                cursor.execute("INSERT INTO tictactoe (username, wins, loss) VALUES(?, 0, 0)", (username,))
                db.commit()

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

    session.clear()
    return redirect("/login")

@app.route("/tictacrooms", methods=["GET", "POST"])
@login_required
def tictacrooms():
    global tictactoe_games

    if request.method == 'POST' and request.form.get("create"):

        #to esnure unique ID
        room_id = random.randint(10000, 99999)
        while room_id in tictactoe_games:
            room_id = random.randint(10000, 99999)

        username = session.get("username")

        tictactoe_games[room_id] = {
            'room_id' : room_id,
            'current_turn' : 'X',
            'player_1' : username,
            'player_2' : 'None',
            'private' : 'False',
            'board_state' : [
                                [' ',' ',' '],
                                [' ',' ',' '],
                                [' ',' ',' ']
                            ]
        }

        return redirect(url_for('tictactoe', room=room_id))

    elif request.method == 'POST' and request.form.get("join"):

        username = session.get("username")

        room_id = int(request.form.get("room_id"))

        tictactoe_games[room_id]['player_2'] = username

        return redirect(url_for('tictactoe', room=room_id))


    return render_template("tictacrooms.html", tictactoe_games=tictactoe_games)

@app.route("/tictactoe/<room>")
@login_required
def tictactoe(room):

#Original game without SpcketIO TODO: SocketIO implementation
    global tictactoe_games

    if int(room) not in tictactoe_games:
        return "Room not found.", 404
    
    return render_template("tictactoe.html", room=room)

@socketio.on('join_room')
@login_required
def handle_join_room(room_id):
    # Check if room_id is actually a string or integer, not a dictionary
    if isinstance(room_id, dict):
        room_id = room_id.get('room_id')  # Extract the actual room ID if wrapped in a dictionary
    
    # Join the room and emit the current game state to the client
    join_room(str(room_id))  # Ensure room_id is a string for consistency with SocketIO
    print(f"User joined room {room_id}")

    # Retrieve the game state and emit it to the client
    game = tictactoe_games.get(int(room_id))
    if game:
        emit('board_update', {'board': game['board_state'], 'current_turn': game['current_turn']}, room=str(room_id))
    else:
        print(f"Room {room_id} does not exist.")

@socketio.on('move')
@login_required
def tictac_move(data):

    def check_win(board):

        #check each row

        for row in board:
            if row[0] == row[1] == row[2] and row[0] != ' ':
                return True
            
        #check each column

        for col in range(3):
            if board[0][col] == board[1][col] == board[2][col] and board[0][col] != ' ':
                return True
            
        # check diagonal

        if board[0][0] == board[1][1] == board[2][2] and board[0][0] != ' ':
            return True
        if board[0][2] == board[1][1] == board[2][0] and board[0][2] != ' ':
            return True
        
        return None

    def check_tie(board):
        # Check if there's a winner
        if check_win(board) is not None:
            return False
        
        # Check if all cells are filled
        for row in board:
            if ' ' in row: 
                return False
            
        return True

    room_id = int(data['room_id'])
    H = data['H']
    V = data['V']

    if room_id in tictactoe_games:
        game = tictactoe_games[room_id]
        board = game['board_state']
        current_turn = game['current_turn']

        if board[V][H] == ' ':
            # Update board with the player's move
            board[V][H] = current_turn
            game['current_turn'] = 'O' if current_turn == 'X' else 'X'  # Switch turns

            # Emit the updated board and turn to all clients in the room
            socketio.emit('board_update', {'board': board, 'current_turn': game['current_turn']}, room=str(room_id))
            print(f"Board update emitted to room {room_id} with turn {game['current_turn']} and board:")
            print(board)  # Debug print to confirm board state

            # Check for a win or tie
            if check_win(board):
                socketio.emit('game_over', {'winner': current_turn}, room=str(room_id))
            elif check_tie(board):
                socketio.emit('game_over', {'winner': None}, room=str(room_id))
        else:
            socketio.emit('invalid_move', {'message': 'Invalid move! Cell already taken.'}, room=request.sid)

    print(tictactoe_games[room_id])  # Print entire game state for debugging



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
                updatewin(room_colors[room]["white"], room_colors[room]["black"], "chess")
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
                updatewin(room_colors[room]["black"], room_colors[room]["white"], "chess")
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
                    updatewin(room_colors[room]["white"], room_colors[room]["black"], "chess")                  
                    response_data.update({"success": True, "board_fen": board_fen, "is_checkmate": True, "white": True})
                else:
                    updatewin(room_colors[room]["black"], room_colors[room]["white"], "chess")
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

def updatewin(winner:str, loser:str, game:str):
    # winner and loser = username of the person.
    if winner == None:
        return "bug", 402
    elif loser == None:
        return "bug", 402
    
    if game == "chess":
        db = sqlite3.connect("users.db")
        cursor = db.cursor()

        try:
            db.execute("BEGIN TRANSACTION")
            cursor.execute("UPDATE chess SET wins = wins + 1 WHERE username = ?", (winner,))
            cursor.execute("UPDATE chess SET loss = loss + 1 WHERE username = ?", (loser,))
            db.commit()
        except ValueError:     
            return ValueError, 401
        except sqlite3.Error as e:
            # rollback if error
            db.rollback()
            return e, 401
        finally:
            cursor.close()
            db.close()

    elif game == "tictactoe":
        db = sqlite3.connect("users.db")
        cursor = db.cursor()

        try:
            db.execute("BEGIN TRANSACTION")
            cursor.execute("UPDATE tictactoe SET wins = wins + 1 WHERE username = ?", (winner,))
            cursor.execute("UPDATE tictactoe SET loss = loss + 1 WHERE username = ?", (loser,))
            db.commit()
        except ValueError:     
            return ValueError, 401
        except sqlite3.Error as e:
            # rollback if error
            db.rollback()
            return e, 401
        finally:
            cursor.close()
            db.close()  
    else:
        return "if you see this something went horribly", 402
