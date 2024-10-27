const socket = io.connect();

socket.on('turn', function(data) {
    // Update the page with the current turn
    document.getElementById("turn").innerText = "Current turn: " + data.turn;
    console.log("Received turn data:", data);
});

function sendMove(H, V) {
    socket.emit('move', { H: H, V: V });
}