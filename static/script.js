document.addEventListener('DOMContentLoaded', function() {
    const elements = document.querySelectorAll('.animate');

    elements.forEach(element => {
        element.classList.add('animated');
    });

    // Canvas animation (optional, hidden)
    const canvas = document.getElementById('myCanvas');
    const ctx = canvas.getContext('2d');

    let x = canvas.width / 2;
    let y = canvas.height - 30;
    let dx = 2;
    let dy = -2;
    let img = new Image();
    img.src = '/static/initial_image.png';  // Initial image path

    function drawImage() {
        ctx.drawImage(img, x, y, 50, 50);  // Adjust width and height as needed
    }

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        drawImage();

        if (x + dx > canvas.width - 50 || x + dx < 0) {
            dx = -dx;
        }
        if (y + dy > canvas.height - 50 || y + dy < 0) {
            dy = -dy;
        }

        x += dx;
        y += dy;
    }

    img.onload = function() {
        setInterval(draw, 10);
    };
});
