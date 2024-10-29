const socket = io();

// Get references to HTML elements
const board = document.getElementById('board');
const cells = document.querySelectorAll('[data-cell]');
const turnDisplay = document.getElementById('turn');
const winningMessage = document.querySelector('.winning-message');
const winningText = document.getElementById('winning-text');
const restartButton = document.getElementById('restart-button');

// Set the current player
let currentPlayer = 'X';
const roomId = document.getElementById('room-info').dataset.roomId;

// Event listeners for cell clicks
cells.forEach(cell => {
    cell.addEventListener('click', () => handleCellClick(cell));
});

// Handle cell click
function handleCellClick(cell) {
    const cellIndex = Array.from(cells).indexOf(cell);
    const row = Math.floor(cellIndex / 3);
    const col = cellIndex % 3;

    // Emit move to the server
    socket.emit('move', { room_id: roomId, H: col, V: row });
}

// Listen for board updates from the server
socket.on('board_update', data => {
    const { board, current_turn } = data;
    updateBoard(board);
    currentPlayer = current_turn;
    turnDisplay.innerText = `Current turn: ${currentPlayer}`;
});

// Update the board UI
function updateBoard(board) {
    board.forEach((row, rowIndex) => {
        row.forEach((cell, colIndex) => {
            const cellElement = cells[rowIndex * 3 + colIndex];
            cellElement.classList.remove('x', 'circle');
            if (cell === 'X') {
                cellElement.classList.add('x');
            } else if (cell === 'O') {
                cellElement.classList.add('circle');
            }
        });
    });
}

// Listen for game over event
socket.on('game_over', data => {
    const winner = data.winner;
    if (winner) {
        winningText.innerText = `The winner is ${winner}!`;
    } else {
        winningText.innerText = "It's a tie!";
    }
    winningMessage.classList.add('show');
});

// Restart the game
restartButton.addEventListener('click', () => {
    winningMessage.classList.remove('show');
    resetBoard();
});

// Reset the board for a new game
function resetBoard() {
    cells.forEach(cell => {
        cell.classList.remove('x', 'circle');
    });
    currentPlayer = 'X'; // Reset to player X
    turnDisplay.innerText = `Current turn: ${currentPlayer}`;
    
    // Optionally, emit a reset event to the server or reset the game state on the server
    socket.emit('reset_game', { room_id: roomId });
}