import chess

board = chess.Board()


def movepiece(move):
    move = chess.Move.from_uci(move)
    board.push(move)

def undomove():
    board.pop()

def show_moves(piece):
    # TODO 
    pass


