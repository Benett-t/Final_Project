const cells = document.querySelectorAll('.cell');
const winningMessageElement = document.querySelector('.winning-message');
const winningMessageTextElement = document.querySelector('.winning-message-text');
const restartButton = document.querySelector('.restart-button');

let currentClass = 'x'; // Start with 'X'
let gameActive = true; // Game status
let socket = io(); // Initialize Socket.IO client
let roomId = null; // Initialize roomId
let playerId = null; // Store player ID

// Join the game room via server-side logic
socket.on('connect', () => {
    const userId = sessionStorage.getItem('userId');
    if (userId) {
        socket.emit('request_room', { userId: userId });
    } else {
        console.error('User ID not found in session storage');
    }
});

// Listen for the server response with the room ID
socket.on('room_assigned', (data) => {
    roomId = data.room; // Get assigned room ID
    console.log(`Joined room: ${roomId}`);
    // Now that we have the roomId, join the game
    socket.emit('join_game', { room: roomId });
});

// Listen for messages from the server
socket.on('message', (data) => {
    console.log(data.msg);
    if (data.msg.includes('wins')) {
        winningMessageTextElement.textContent = data.msg;
        winningMessageElement.classList.add('show');
        gameActive = false; // End the game
    } else if (data.msg.includes('draw')) {
        winningMessageTextElement.textContent = data.msg;
        winningMessageElement.classList.add('show');
        gameActive = false; // End the game
    }
});

// Listen for board updates
socket.on('update_board', (data) => {
    const cell = cells[data.cell];
    placeMark(cell, data.currentClass);
    // Update currentClass to switch turn for local player
    currentClass = data.currentClass === 'x' ? 'circle' : 'x';
});

// Listen for game reset requests
socket.on('reset_board', () => {
    resetBoard();
});

// Add event listeners to all cells
cells.forEach((cell, index) => {
    cell.addEventListener('click', () => handleCellClick(index));
});

// Handle click events on cells
function handleCellClick(cellIndex) {
    const cell = cells[cellIndex];

    // Prevent click if game is not active or cell already has a mark
    if (!gameActive || cell.classList.contains('x') || cell.classList.contains('circle')) {
        return;
    }

    // Check if it's the current player's turn
    if (currentClass === 'x' && playerId === 'player1' || currentClass === 'circle' && playerId === 'player2') {
        // Place the mark visually
        placeMark(cell, currentClass);

        // Send the cell click event to the server
        socket.emit('cell_click', {
            roomId: roomId,
            cell: cellIndex,
            currentClass: currentClass,
        });
    } else {
        alert('It\'s not your turn!');
    }
}

// Function to visually place the mark
function placeMark(cell, currentClass) {
    cell.classList.add(currentClass); // Add class for 'x' or 'circle'
}

// Reset the board
function resetBoard() {
    cells.forEach(cell => {
        cell.classList.remove('x', 'circle'); // Clear marks
    });
    winningMessageElement.classList.remove('show'); // Hide the winning message
    currentClass = 'x'; // Reset to 'X'
    gameActive = true; // Set game status to active
}

// Add event listener for the restart button
restartButton.addEventListener('click', () => {
    resetBoard();
    socket.emit('restart_game', { room: roomId }); // Notify server to restart the game
});
