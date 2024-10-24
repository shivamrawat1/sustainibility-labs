document.addEventListener('DOMContentLoaded', () => {
    const imageFilename = document.getElementById('imageCanvas').getAttribute('data-filename');
    const canvas = new fabric.Canvas('imageCanvas');

    // Load the image onto the canvas
    fabric.Image.fromURL('/static/uploads/' + imageFilename, function (img) {
        img.set({ selectable: false });
        canvas.setWidth(img.width);
        canvas.setHeight(img.height);
        canvas.add(img);
        canvas.sendToBack(img);
    });

    // Enable drawing mode for mask creation
    canvas.isDrawingMode = true;
    canvas.freeDrawingBrush.color = 'rgba(255, 255, 255, 1)';
    canvas.freeDrawingBrush.width = 20;

    // When the user submits the form, get the mask data
    const form = document.getElementById('promptForm');
    form.addEventListener('submit', function (event) {
        event.preventDefault();

        // Create a mask canvas
        const maskCanvas = document.createElement('canvas');
        maskCanvas.width = canvas.width;
        maskCanvas.height = canvas.height;
        const maskCtx = maskCanvas.getContext('2d');

        // Fill the mask canvas with black
        maskCtx.fillStyle = 'black';
        maskCtx.fillRect(0, 0, maskCanvas.width, maskCanvas.height);

        // Draw the user's drawing onto the mask canvas in white
        const drawingCanvas = new fabric.Canvas(null, {
            width: canvas.width,
            height: canvas.height
        });

        // Copy the user's drawing paths
        canvas.getObjects('path').forEach(function (path) {
            drawingCanvas.add(path.clone());
        });

        // Render the drawing onto the mask canvas
        drawingCanvas.renderAll();
        const drawingDataURL = drawingCanvas.toDataURL('image/png');

        // Load the drawing data onto the mask canvas
        const img = new Image();
        img.onload = function () {
            maskCtx.drawImage(img, 0, 0);
            // Get the data URL of the mask
            const maskDataURL = maskCanvas.toDataURL('image/png');
            document.getElementById('maskData').value = maskDataURL;

            // Submit the form after mask data is set
            form.submit();
        };
        img.src = drawingDataURL;
    });
});
