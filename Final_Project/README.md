# Duo play arena
#### Video Demo: <URL>
#### Description:

This Project was created by Benett Palinkas and Mate Palinkas.
GitHub username for Benett: *Benett-t*
edX username for Benett: *b-palinkas*

GitHub username for Mate: *MateP777*
edX username for Mate: * *

#### Overview:
Duo Play Arena is a web-based multiplayer platform where users can play Chess and Tic Tac Toe against each other in real-time. Built using Flask and Socket.IO, this application enables seamless online gaming with user management and game statistics.

## Chess:
Our Chess implementation stays true to the classic rules of the game, and allows players to make all standard moves such as castling, en passant, and pawn promotion. The Chess game is designed for multiplayer using Socket.IO for real-time interaction between players. The frontend of the Chess game is made from scratch allowing precise control over the user interface allowing us to enable dragging and square for moving the pieces. The game ends either by checkmate, stalemate, draw or forfeit. If the opponent left the room a 60 second timer begins counting down till the opponent returns or it reaches zero when it reaches zero the opponent is forced to forfeit. A draw offer can be sent anytime in the game if the opponent accepts the draw the game ends in a tie. The outcome of the game is recorded by the updatewin function this function interacts with the database and changes the values based on the outcome. Furthermore the game has several sound effects allowing for a more immersed user experience. Overall, we have successfully brought the rich, competitive world of Chess to the web.

## Tic Tac Toe:

### List of files with descriptions:
- app.py contains the Flask web app with user management, game stats and the games itself
- README.md - This readme file
- requirements.txt - Contains all python libraries used for the app
- tictactoe.py - Test application for testing the tictactoe game logic
- users.db - Contains the user data with hashed passwords and statistics for the games in separate tables
- /static
    - /static/images contain the png files for the chess
    - /static/sounds contain the sounds for the games
    - chess.js - contain the javascript frontend for the chess game with
    - tictactoe.js - javascript for the frontend (tictactoe)
    - style.css - main style of the website
- /templates
    - All of the html for the website