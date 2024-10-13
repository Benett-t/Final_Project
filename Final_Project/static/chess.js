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
            if (row === 7) {
                const collabel = document.createElement('div');
                collabel.textContent = String.fromCharCode(97 + col);
                collabel.classList.add('row-label')

                if (col % 2 == 0) {
                    collabel.classList.add('label-white');
                }

                else {
                    collabel.classList.add('label-black');
                }

                square.appendChild(collabel);
            }

            if (col === 0) {
                const rowlabel = document.createElement('div');
                rowlabel.textContent = 8 - row;
                rowlabel.classList.add('col-label');

                if (row % 2 == 0) {
                    rowlabel.classList.add('label-black');
                }

                else {
                    rowlabel.classList.add('label-white');
                }

                square.appendChild(rowlabel);
            }

            if (isNaN(piece)) {
                // If the character is not a number, it's a piece
                const img = document.createElement('img');
                img.src = `/static/images/chess/${pieceImages[piece]}.png`;
                img.alt = piece;
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
                    
                    if (row === 7) {
                        const collabel = document.createElement('div');
                        collabel.textContent = String.fromCharCode(97 + col);
                        collabel.classList.add('row-label');
                        
                        if (col % 2 == 0) {
                            collabel.classList.add('label-white');
                        }
                        else {
                            collabel.classList.add('label-black');
                        }
                        emptySquare.appendChild(collabel);
                    }
        
                    if (col === 0) {
                        const rowlabel = document.createElement('div');
                        rowlabel.textContent = 8 - row;
                        rowlabel.classList.add('col-label');

                        if (row % 2 == 0) {
                            rowlabel.classList.add('label-black');
                        }
                        else {
                            rowlabel.classList.add('label-white');
                        }
                        emptySquare.appendChild(rowlabel);
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
            updateBoard(move, response.is_checkmate, response.white, response.black, response.wpromotion, response.bpromotion);
            if (response.OO == true) {
                updateBoard('h1f1');
            }
            else if (response.OOO == true) {
                updateBoard('a1d1');
            }
            else if (response.oo == true) {
                updateBoard('h8f8');
            }
            else if (response.ooo == true) {
                updateBoard('a8d8');
            }
        },
        error: function(response) {
            square.classList.remove('selected')
        }
    });
}

function updateBoard(move, is_checkmate, white, black, wpromotion, bpromotion) {
    const fromSquare = move.slice(0, 2);
    const toSquare = move.slice(2);
    var piece = boardState[fromSquare];
    const toElement = document.querySelector(`[data-square='${toSquare}']`);
    const fromElement = document.querySelector(`[data-square='${fromSquare}']`);


    if (wpromotion == true) {
        piece = 'Q'
    }
    else if (bpromotion == true) {
        piece = 'q'
    }

    if (toElement && fromElement) {
        // Get positions of the source and target squares for animation
        const fromRect = fromElement.getBoundingClientRect();
        const toRect = toElement.getBoundingClientRect();

        const img = fromElement.querySelector('img');

        if (img) {
            // Calculate the translation for animation
            const deltaX = toRect.left - fromRect.left;
            const deltaY = toRect.top - fromRect.top;

            // Apply the transform to animate the piece
            img.style.transform = `translate(${deltaX}px, ${deltaY}px)`;

            // Once the transition is over, move the piece to the new square
            setTimeout(() => { 
                console.log(piece)
                const fromrowlabel = fromElement.querySelector('.col-label')
                const fromcollablel = fromElement.querySelector('.row-label')

                const torowlabel = toElement.querySelector('.col-label')
                const tocollablel = toElement.querySelector('.row-label')

                toElement.innerHTML = `<img src="/static/images/chess/${pieceImages[piece]}.png" alt="${piece}" class="piece-img">`;
                fromElement.innerHTML = ''; // Clear the from square
                img.style.transform = ''; // Reset the transform
    
                if (fromcollablel) {
                    fromElement.appendChild(fromcollablel);
                } 
                if (fromrowlabel) {
                    fromElement.appendChild(fromrowlabel);
                }
                if (torowlabel) {
                    toElement.appendChild(torowlabel);
                }
                if (tocollablel) {
                    toElement.appendChild(tocollablel);
                }

                // Update the board state
                boardState[toSquare] = piece;
                delete boardState[fromSquare];

                if (is_checkmate == true) {
                    if (white == true) {
                        alert("WHITE WON!");
                    } else if (black == true) {
                        alert("BLACK WON!");
                    }
                }
            }, 500); // Match the duration of the CSS transition
        }
    }
}


// Initial board render
$(document).ready(function() {
    renderBoard(boardFen);  // boardFen will be passed from the server-side
});
