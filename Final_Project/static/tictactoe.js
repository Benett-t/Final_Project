const cells = document.querySelectorAll('.cell');
const winningMessageElement = document.querySelector('.winning-message');
const winningMessageTextElement = document.querySelector('.winning-message-text');
const restartButton = document.querySelector('.restart-button');

let currentClass = 'x'; // Start with 'X'
let gameActive = true; // Game status
let socket = io(); // Initialize Socket.IO client
let roomId = prompt("Enter room ID:"); // Ask the user to enter a room ID
let playerId = null; // Store player ID

// Join the game room
socket.emit('join_game', { room: roomId });

// Listen for messages from the server
socket.on('message', (data) => {
    console.log(data.msg);
    if (data.msg.includes('wins')) {
        winningMessageTextElement.textContent = data.msg;
        winningMessageElement.classList.add('show');
        gameActive = false; // End the game
    }
});

// Listen for board updates
socket.on('update_board', (data) => {
    const cell = cells[data.cell];
    placeMark(cell, data.currentClass);
    currentClass = currentClass === 'x' ? 'circle' : 'x'; // Switch turn
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

    // Place the mark visually
    placeMark(cell, currentClass);

    // Send the cell click event to the server
    socket.emit('cell_click', {
        roomId: roomId,
        cell: cellIndex,
        currentClass: currentClass,
    });

    // Check for win condition
    if (checkWinCondition(currentClass)) {
        gameActive = false;
        winningMessageTextElement.textContent = `Player ${currentClass.toUpperCase()} wins!`;
        winningMessageElement.classList.add('show');
        return;
    }

    // Switch turn
    currentClass = currentClass === 'x' ? 'circle' : 'x';
}

// Function to visually place the mark
function placeMark(cell, currentClass) {
    cell.classList.add(currentClass); // Add class for 'x' or 'circle'
}

// Check win condition
function checkWinCondition(currentClass) {
    const winningCombinations = [
        [0, 1, 2], // Top row
        [3, 4, 5], // Middle row
        [6, 7, 8], // Bottom row
        [0, 3, 6], // Left column
        [1, 4, 7], // Middle column
        [2, 5, 8], // Right column
        [0, 4, 8], // Diagonal
        [2, 4, 6], // Diagonal
    ];

    return winningCombinations.some(combination => {
        return combination.every(index => {
            return cells[index].classList.contains(currentClass);
        });
    });
}

// Reset the board
function reset
