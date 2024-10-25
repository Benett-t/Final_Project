document.addEventListener("DOMContentLoaded", () => {
  const cells = document.querySelectorAll("[data-cell]");
  const winningMessageElement = document.getElementById("winningMessage");
  const winningMessageTextElement = document.getElementById("winningMessageText");
  const restartButton = document.getElementById("restartButton");
  const roomId = "1"; // Replace with your room ID logic
  let currentClass = "X"; // Assume player X starts
  let gameActive = true;

  // Socket.io connection
  const socket = io();
  socket.on('connect', () => {
      console.log('Connected to server');
  });

  // Handle cell click
  cells.forEach(cell => {
      cell.addEventListener("click", handleCellClick);
  });

  function handleCellClick(e) {
      const cell = e.target;
      const cellIndex = Array.from(cells).indexOf(cell);

      console.log("Cell clicked:", cellIndex); // Debug log for cell click

      // Prevent click if game is not active or cell already filled
      if (!gameActive || cell.classList.contains("X") || cell.classList.contains("O")) {
          console.log("Cell is already occupied or game is not active."); // Debug log
          return;
      }

      // Emit the move to the server
      socket.emit('cell_click', {
          roomId: roomId,
          cell: cellIndex,
          currentClass: currentClass,
      });

      // Place the mark locally
      placeMark(cell, currentClass);
      
      // Check for winning message locally
      if (checkWinCondition(currentClass)) {
          gameActive = false;
          winningMessageTextElement.textContent = `Player ${currentClass} wins!`;
          winningMessageElement.classList.add("show");
          return;
      }

      // Switch turn to the next player
      switchTurn();
  }

  function placeMark(cell, currentClass) {
      cell.classList.add(currentClass);
  }

  socket.on('update_board', data => {
      const { cell, currentClass } = data;
      const cellToUpdate = cells[cell];
      placeMark(cellToUpdate, currentClass);
      if (checkWinCondition(currentClass)) {
          gameActive = false;
          winningMessageTextElement.textContent = `Player ${currentClass} wins!`;
          winningMessageElement.classList.add("show");
      } else {
          switchTurn(); // Switch turn after update
      }
  });

  function checkWinCondition(player) {
      const winPatterns = [
          [0, 1, 2], [3, 4, 5], [6, 7, 8], // Rows
          [0, 3, 6], [1, 4, 7], [2, 5, 8], // Columns
          [0, 4, 8], [2, 4, 6],             // Diagonals
      ];
      return winPatterns.some(pattern => {
          return pattern.every(index => {
              return cells[index].classList.contains(player);
          });
      });
  }

  // Handle game restart
  restartButton.addEventListener("click", () => {
      socket.emit('restart_game', { room: roomId });
  });

  // Reset board from the server
  socket.on('reset_board', () => {
      cells.forEach(cell => {
          cell.classList.remove("X", "O"); // Clear cells
      });
      currentClass = "X"; // Reset to player X
      gameActive = true;
      winningMessageElement.classList.remove("show"); // Hide winning message
  });

  function switchTurn() {
      currentClass = currentClass === "X" ? "O" : "X"; // Switch between X and O
  }
});