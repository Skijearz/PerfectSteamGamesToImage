document.getElementById('steamForm').addEventListener('submit', function(event) {
    event.preventDefault();  // Prevent the default form submission
    var loader = document.getElementById('loader');
    var submitButton = document.getElementById('submitButton');
    var errorMessage = document.getElementById('errorMessage');
    
    // Add loading class to body
    document.body.classList.add('loading');
    errorMessage.style.display = 'none';

    var formData = new FormData(this);

    fetch('/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json().then(data => ({ status: response.status, body: data })))
    .then(data => {
        if (data.status === 200) {
            var token = data.body.token;
            var link = document.createElement('a');
            link.href = `/download/${token}`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } else {
            errorMessage.textContent = `Error: ${data.body.error}`;
            errorMessage.style.display = 'block';
        }
        // Remove loading class from body
        document.body.classList.remove('loading');
    })
    .catch(error => {
        console.error('Error:', error);
        errorMessage.textContent = 'An unexpected error occurred.';
        errorMessage.style.display = 'block';
        // Remove loading class from body
        document.body.classList.remove('loading');
    });
});
