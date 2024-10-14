from flask import session, Flask, render_template, request, redirect, jsonify
from flask_session import Session
import sqlite3
import bcrypt
from functools import wraps
import chess
from uuid import uuid5, uuid4

app = Flask(__name__)

board = chess.Board()
# after closing website session deletes set to True if you want permament session.
app.config["SESSION_PERMANENT"] = False
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

@app.route("/tictactoe")
@login_required
def tictactoe():

    return render_template("tictactoe.html")

@app.route("/chessboard")
@login_required
def chessboard():
    # get board state
    board_fen = board.fen()
    return render_template("chess.html", board_fen=board_fen)

@app.route("/move_piece", methods=["POST"])
@login_required
def move_piece():
    data = request.get_json()

    if not data or 'move' not in data:
        return jsonify({'error': 'Invalid request, move data missing'}), 400
    
    move = data['move']

    
    try:
        board_fen = board.fen()
        chess_move = chess.Move.from_uci(move)
        piece = board.piece_at(chess_move.from_square)
        print(piece)
        print (chess_move.from_square)

        if str(piece) == 'K' and chess_move.from_square == 4 and chess_move.to_square == 6 and board.has_kingside_castling_rights(chess.WHITE) == True:
            board.push(chess_move)
            print("trying to castle short side")
            if board.is_check() == True:
                return jsonify({"success": True, "checkb": True, "OO": True})
            return jsonify({"success": True, "board_fen": board_fen, 'OO': True})
        
        elif str(piece) == 'K' and chess_move.from_square == 4 and chess_move.to_square == 2 and board.has_queenside_castling_rights(chess.WHITE) == True:
            board.push(chess_move)
            print("trying to castle short side")
            if board.is_check() == True:
                return jsonify({"success": True, "checkb": True, "OOO": True})
            
            return jsonify({"success": True, "board_fen": board_fen, 'OOO': True})
        
        elif str(piece) == 'k' and chess_move.from_square == 60 and chess_move.to_square == 62 and board.has_kingside_castling_rights(chess.BLACK) == True:
            board.push(chess_move)
            print("trying to castle short side")
            if board.is_check() == True:
                return jsonify({"success": True, "checkw": True, "oo": True})
            return jsonify({"success": True, "board_fen": board_fen, 'oo': True})

        elif str(piece) == 'k' and chess_move.from_square == 60 and chess_move.to_square == 58 and board.has_queenside_castling_rights(chess.BLACK) == True:
            board.push(chess_move)
            print("trying to castle short side")
            if board.is_check() == True:
                return jsonify({"success": True, "checkw": True, "ooo": True})
            return jsonify({"success": True, "board_fen": board_fen, 'ooo': True})


        elif str(piece) == 'P' and chess.square_rank(chess_move.from_square) == 6:
            chess_move = chess.Move.from_uci(move + 'q')
            board.push(chess_move)

            if board.is_checkmate() == True:
                if board.outcome().winner == chess.WHITE:
                    board.reset()
                    return jsonify({"success": True, "board_fen": board_fen, "is_checkmate": True, "white": True})
                else:
                    board.reset()
                    return jsonify({"success": True, "board_fen": board_fen, "is_checkmate": True, "black": True})
                
            if board.is_check() == True:
                return jsonify({"success": True, "checkb": True, "wpromotion": True})
            elif board.is_stalemate() == True:
                board.reset()
                return jsonify({"success": True, "stalemate": True})
            
            return jsonify({"success": True, "board_fen": board_fen, "is_checkmate" : False, "wpromotion": True})
        
        elif str(piece) == 'p' and chess.square_rank(chess_move.from_square) == 1:
            chess_move = chess.Move.from_uci(move + 'q')
            board.push(chess_move)
            if board.is_checkmate() == True:
                if board.outcome().winner == chess.WHITE:
                    board.reset()
                    return jsonify({"success": True, "board_fen": board_fen, "is_checkmate": True, "white": True})
                else:
                    board.reset()
                    return jsonify({"success": True, "board_fen": board_fen, "is_checkmate": True, "black": True})
            if board.is_check() == True:
                return jsonify({"success": True, "checkw": True, "bpromotion": True})
            if board.is_checkmate() == True:
                if board.outcome().winner == chess.WHITE:
                    board.reset()
                    return jsonify({"success": True, "board_fen": board_fen, "is_checkmate": True, "white": True})
                else:
                    board.reset()
                    return jsonify({"success": True, "board_fen": board_fen, "is_checkmate": True, "black": True})
            elif board.is_stalemate() == True:
                board.reset()
                return jsonify({"success": True, "stalemate": True})
                
            return jsonify({"success": True, "board_fen": board_fen, "is_checkmate" : False, "bpromotion": True})
            
        elif chess_move in board.legal_moves:
            board.push(chess_move)

            if board.is_stalemate() == True:
                board.reset()
                return jsonify({"success": True, "stalemate": True})
            
            elif board.is_checkmate() == True:
                if board.outcome().winner == chess.WHITE:
                    board.reset()
                    return jsonify({"success": True, "board_fen": board_fen, "is_checkmate": True, "white": True})
                else:
                    board.reset()
                    return jsonify({"success": True, "board_fen": board_fen, "is_checkmate": True, "black": True})
                
            elif board.is_check() == True and board.turn == chess.WHITE:
                return jsonify({"success": True, "wcheck": True})
            elif board.is_check() == True and board.turn == chess.BLACK:
                return jsonify({"success": True, "bcheck": True})
                

            return jsonify({"success": True, "board_fen": board_fen, "is_checkmate" : False})
        else:
            return jsonify({"success": False, "error": "Invalid move"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400