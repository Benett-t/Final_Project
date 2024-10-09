from flask import session, Flask, render_template, request, redirect
from flask_session import Session
import sqlite3
from hashlib import md5
from functools import wraps
import chess

board = chess.Board()

app = Flask(__name__)

# TODO make database named users.db
db = sqlite3.connect("users.db")

# after closing website session deletes set to True if you want permament session.
app.config["SESSION_PERMANENT"] = False
# Save session in filesystem insted of browser
app.config["SESSION_TYPE"] = "filesystem"
# Initilise session
Session(app)

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def index():
    #Landing page after login

    return render_template("index.html")

def login_required(f):

    # ez kell hogy brijuk ugy hogy @login_required
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # if no session
        if session.get("user_id") is None:
            return redirect("/login")
    return decorated_function

@app.route("/login", methods=["GET", "POST"])
def login():
    # TODO
    if session.get("user_id") is not None:
        # if we are logged in then prompt to logout
        return render_template("logout.html")
    else:
        if request.method == "GET":
            # base case
            return render_template("login.html")
        # else if POST.
        else:
            pass
            # TODO first have to make login.html
