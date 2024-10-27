game_rooms = []

game = {
    'room_id' : 'None',
    'current_turn' : 'None',
    'player_1' : 'None',
    'palyer_2' : 'None',
    'private' : 'None',
    'board_state' : [None] * 9
    }

board = [
    [' ',' ',' '],
    [' ',' ',' '],
    [' ',' ',' ']
]

def check_win(board):

    #check each row

    for row in board:
        if row[0] == row[1] == row[2] and row[0] != ' ':
            return row[0]
        
    #check each column

    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] and board[0][col] != ' ':
            return board[0][col]
        
    # check diagonal

    if board[0][0] == board[1][1] == board[2][2] and board[0][0] != ' ':
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] != ' ':
        return board[0][2]
    
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

winner = check_win(board)
if winner:
    print(f"The winner is {winner}!")
elif check_tie(board):
    print("The game is a tie!")
else:
    print("No winner or tie yet.")

    