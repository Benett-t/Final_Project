const cells = document.querySelectorAll('td');

// Store the callback function for event removal
function handleMouseEnter() {
    // Store the original text to restore later
    this.setAttribute('data-original-text', this.innerHTML);
    // Set the content to 'X' on hover
    this.innerHTML = 'X';
}

function handleMouseLeave() {
    // Restore the original content
    this.innerHTML = this.getAttribute('data-original-text');
}

cells.forEach(cell => {
    // Add hover effect for 'X'
    cell.addEventListener('mouseenter', handleMouseEnter);
    cell.addEventListener('mouseleave', handleMouseLeave);

    cell.addEventListener('click', function() {
        if (this.innerHTML === '') {  // Only set 'X' if the cell is empty
            this.innerHTML = 'X';
            // After the cell is clicked, remove the hover event listeners
            this.removeEventListener('mouseenter', handleMouseEnter);
            this.removeEventListener('mouseleave', handleMouseLeave);
        }
    });
});

// pseudo code for js

// turn based logic X, O

// track player turn

// check state of the board to determine if there is a winner

