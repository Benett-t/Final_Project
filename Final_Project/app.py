from flask import session, Flask, render_template, request, redirect
from flask_session import Session
import sqlite3
from hashlib import md5

app = Flask(__name__)

# TODO make database named users.db
db = sqlite3.connect("users.db")

# after closing website session deletes set to True if you want permament session.
app.config["SESSION_PERMANENT"] = False
# Save session in filesystem insted of browser
app.config["SESSION_TYPE"] = "filesystem"
# Initilise session
Session(app)