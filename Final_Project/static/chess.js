const pieceImages = {
    'r': 'b_rook', 'n': 'b_knight', 'b': 'b_bishop', 'q': 'b_queen', 'k': 'b_king', 'p': 'b_pawn',
    'R': 'w_rook', 'N': 'w_knight', 'B': 'w_bishop', 'Q': 'w_queen', 'K': 'w_king', 'P': 'w_pawn'
};

const boardElement = document.getElementById('chessboard');
let selectedSquare = null;
let selectedPiece = null;
let selectedSquareData = null;
let boardState = {}; // keep track of pos
let draggedPiece = null;
let sourceSquare = null;

// Render the board based on the FEN string
function renderBoard(fen) {
    boardElement.innerHTML = '';
    boardState = {};

    // Split the FEN string into ranks
    const ranks = fen.split(' ')[0].split('/');

    // Loop through each rank
    for (let row = 0; row < 8; row++) {
        let col = 0; // Reset column index for each row
        const rank = ranks[row];
        console.log("Processing rank:", rank); // Debugging line

        // Loop through each character in the rank
        for (let i = 0; i < rank.length; i++) {
            const piece = rank[i];
            const square = document.createElement('div');
            square.classList.add('square');

            // Determine square color
            if ((row + col) % 2 === 0) {
                square.classList.add('white');
            } else {
                square.classList.add('black');
            }

            if (isNaN(piece)) {
                // If the character is not a number, it's a piece
                const img = document.createElement('img');
                img.src = `/static/images/chess/${pieceImages[piece]}.png`;
                img.alt = piece;
                img.draggable = true;
                img.classList.add('piece-img');
                square.appendChild(img);
                col++; // Increment for pieces
            } else {
                // If the character is a number, it indicates empty squares
                const emptySquares = parseInt(piece);
                for (let j = 0; j < emptySquares; j++) {
                    // Create empty squares based on the number
                    const emptySquare = document.createElement('div');
                    emptySquare.classList.add("square")
                    if ((row % 2 === 0 && col % 2 === 0) || (row % 2 === 1 && col % 2 === 1)) {
                        emptySquare.classList.add("white")
                    }
                    else {
                        emptySquare.classList.add("black")
                    }
                    
                    emptySquare.addEventListener('click', () => handleSquareClick(emptySquare));
                    boardElement.appendChild(emptySquare); // Add empty square
                    col++; // Increment column for each empty square
                    emptySquare.dataset.square = String.fromCharCode(97 + col - 1) + (8 - row); // e.g., 'e2'
                }
                continue; // Skip to the next character
            }
            
            square.dataset.square = String.fromCharCode(96 + col) + (8 - row); // e.g., 'e2'
            square.addEventListener('click', () => handleSquareClick(square));

            boardElement.appendChild(square);
            if (isNaN(piece)) {
                boardState[square.dataset.square] = piece;
            }

        }
    }
}

// Handle square click for moving pieces
function handleSquareClick(square) {
    const squareData = square.dataset.square
    const piece = square.dataset.piece;
    const img = square.querySelector('img')

    if (selectedSquare) {
        selectedSquare.classList.remove('selected')
        const move = selectedSquare.dataset.square + squareData;
        submitMove(move, selectedSquare);
        selectedSquare = null;
        selectedPiece = null;
    } else {
        if (img) {
            selectedSquare = square;
            selectedPiece = piece;
            square.classList.add('selected')
        }
    }
}

// Send the move to the server
function submitMove(move, square) {
    $.ajax({
        url: "/move_piece",
        method: "POST",
        contentType: "application/json",
        data: JSON.stringify({ move: move }),
        success: function(response) {
            updateBoard(move, response.is_checkmate, response.white, response.black);
        },
        error: function(response) {
            square.classList.remove('selected')
        }
    });
}

function updateBoard(move, is_checkmate, white, black) {
    const fromSquare = move.slice(0, 2)
    const toSquare = move.slice(2)
    const piece = boardState[fromSquare]
    const toElement = document.querySelector(`[data-square='${toSquare}']`)
    const fromElement = document.querySelector(`[data-square='${fromSquare}']`)

    if (toElement && fromElement) {
        toElement.innerHTML = `<img src="/static/images/chess/${pieceImages[piece]}.png" alt="${piece}" class="piece-img">`;
        fromElement.innerHTML = ''; // Clear the from square

        boardState[toSquare] = piece; // Update the new position
        delete boardState[fromSquare]; // Remove the piece from the old position
        if (is_checkmate == true) {
            console.log(white)
            console.log(black)
            if (white == true) {
                alert("WHITE WON!")
            }
            else if (black == true) {
                alert("BLACK WON!")
            }
        }
    }

} 
// Initial board render
$(document).ready(function() {
    renderBoard(boardFen);  // boardFen will be passed from the server-side
});
