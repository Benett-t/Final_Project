// Establish connection to the server using Socket.IO
const socket = io.connect();

// Get the room ID from the HTML data attribute
const roomId = document.getElementById('room-info').dataset.roomId;

// Join the room
socket.emit('join_room', { room_id: roomId });

// Listen for board updates from the server
socket.on('board_update', (data) => {
    console.log("Board update received:", data);  // Debug log to track incoming board updates
    updateBoard(data.board, data.current_turn);   // Update board UI with latest data
});

// Listen for game over events
socket.on('game_over', (data) => {
    console.log("Game over event received:", data);  // Debug log for game over events
    const winningText = document.getElementById('winning-text');
    if (data.winner) {
        winningText.textContent = `Winner: ${data.winner}`;
    } else {
        winningText.textContent = "It's a tie!";
    }
    document.querySelector('.winning-message').classList.add('show');
});

// Listen for invalid move events
socket.on('invalid_move', (data) => {
    console.log("Invalid move:", data.message);  // Log invalid move message
    alert(data.message);  // Show an alert for invalid moves
});

// Function to update the board UI based on the server's board data
function updateBoard(board, currentTurn) {
    // Update each cell with the current board state
    board.forEach((row, rowIndex) => {
        row.forEach((cellValue, colIndex) => {
            const cell = document.querySelector(`.cell[data-row="${rowIndex}"][data-col="${colIndex}"]`);
            if (cell) cell.textContent = cellValue;  // Set the cell's content to 'X', 'O', or ' '
        });
    });
    // Update the turn display
    document.getElementById('turn').textContent = `Current turn: ${currentTurn}`;
}

// Handle cell clicks and send move to the server
document.querySelectorAll('.cell').forEach((cell, index) => {
    // Set row and column data attributes for each cell
    const row = Math.floor(index / 3);
    const col = index % 3;
    cell.setAttribute("data-row", row);
    cell.setAttribute("data-col", col);

    cell.addEventListener('click', () => {
        console.log(`Move made at row ${row}, column ${col}`);  // Debug log for move
        socket.emit('move', { room_id: roomId, V: row, H: col });
    });
});

// Restart the game when the restart button is clicked
document.getElementById('restart-button').addEventListener('click', () => {
    console.log("Restart game clicked");  // Debug log for restart
    socket.emit('restart_game', { room_id: roomId });  // Emit a restart request to the server
    document.querySelector('.winning-message').classList.remove('show');  // Hide the winning message
});
