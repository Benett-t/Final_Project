const PLAYER_X_CLASS = 'x';
const PLAYER_O_CLASS = 'circle';
const WINNING_COMBINATIONS = [
  [0, 1, 2], [3, 4, 5], [6, 7, 8],
  [0, 3, 6], [1, 4, 7], [2, 5, 8],
  [0, 4, 8], [2, 4, 6]
];

const cellElements = document.querySelectorAll('[data-cell]');
const boardElement = document.getElementById('board');
const winningMessageElement = document.getElementById('winningMessage');
const restartButton = document.getElementById('restartButton');
const winningMessageTextElement = document.getElementById('winningMessageText');
let isPlayer_O_Turn = false; // Track if it's player O's turn
let gameActive = true; // Prevent further moves after game ends

const socket = io();
const roomId = document.getElementById('room-info').dataset.roomId;

// Start the game and set up the board
startGame();

// Event listener for the restart button
restartButton.addEventListener('click', () => {
  socket.emit('restart_game', { room: roomId });
  startGame();
});

// Function to start the game
function startGame() {
  isPlayer_O_Turn = false; // Reset to Player X's turn
  gameActive = true; // Allow moves again
  cellElements.forEach(cell => {
    cell.classList.remove(PLAYER_X_CLASS);
    cell.classList.remove(PLAYER_O_CLASS);
    cell.removeEventListener('click', handleCellClick); // Remove any existing event listeners
    cell.addEventListener('click', handleCellClick, { once: true }); // Add click listener
  });
  setBoardHoverClass(); // Set the hover class for the board
  winningMessageElement.classList.remove('show'); // Hide the winning message
}

// Function to handle cell clicks
function handleCellClick(e) {
  if (!gameActive) return; // Ignore clicks if the game is over
  const cell = e.target;
  const currentClass = isPlayer_O_Turn ? PLAYER_O_CLASS : PLAYER_X_CLASS; // Determine the current player class
  const cellIndex = [...cellElements].indexOf(cell); // Get the index of the clicked cell

  // Emit the cell click event to the server
  socket.emit('cell_click', { cell: cellIndex, currentClass, roomId });
}

// Function to place a mark in the clicked cell
function placeMark(cell, currentClass) {
  cell.classList.add(currentClass); // Add the current class to the cell
  cell.removeEventListener('click', handleCellClick); // Remove click event after placing a mark
}

// Function to swap player turns
function swapTurns() {
  isPlayer_O_Turn = !isPlayer_O_Turn; // Toggle the turn between players
}

// Function to set the hover class on the board
function setBoardHoverClass() {
  boardElement.classList.remove(PLAYER_X_CLASS, PLAYER_O_CLASS); // Remove existing hover classes
  boardElement.classList.add(isPlayer_O_Turn ? PLAYER_O_CLASS : PLAYER_X_CLASS); // Add the current hover class
}

// Function to end the game
function endGame(draw) {
  gameActive = false; // Prevent further moves
  if (draw) {
    winningMessageTextElement.innerText = "It's a draw!";
  } else {
    winningMessageTextElement.innerText = `Player with ${isPlayer_O_Turn ? "O's" : "X's"} wins!`;
  }
  winningMessageElement.classList.add('show'); // Show the winning message
}

// Function to check for a draw
function isDraw() {
  return [...cellElements].every(cell => {
    return cell.classList.contains(PLAYER_X_CLASS) || cell.classList.contains(PLAYER_O_CLASS);
  });
}

// Function to check for a win
function checkWin(currentClass) {
  return WINNING_COMBINATIONS.some(combination => {
    return combination.every(index => {
      return cellElements[index].classList.contains(currentClass);
    });
  });
}

// Listen for updates from the server about the board state
socket.on('update_board', ({ cell, currentClass }) => {
  placeMark(cellElements[cell], currentClass); // Place the mark in the correct cell
  if (checkWin(currentClass)) {
    endGame(false); // End the game if there's a win
  } else if (isDraw()) {
    endGame(true); // End the game if it's a draw
  } else {
    swapTurns(); // Swap turns if the game continues
    setBoardHoverClass(); // Update hover class
  }
});

// Listen for the reset board event
socket.on('reset_board', () => {
  startGame(); // Restart the game
});

// Handle connection errors
socket.on('connect_error', () => {
  console.error('Connection error with the server');
  alert('Unable to connect to the game server. Please refresh the page.');
});

// Handle successful connection
socket.on('connect', () => {
  console.log('Connected to the server');
});

// Listen for the 'joined_room' event to automatically set up the game
socket.on('joined_room', () => {
  startGame(); // Start the game when a player joins a room
});
