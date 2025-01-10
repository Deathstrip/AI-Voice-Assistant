// Select DOM elements
const micButton = document.getElementById('mic-button');
const queryText = document.getElementById('query-text');
const responseText = document.getElementById('response-text');
const aiAudio = document.getElementById('ai-audio');

let isListening = false;

// Function to toggle microphone listening
micButton.addEventListener('click', () => {
  if (!isListening) {
    startListening();
  } else {
    stopListening();
  }
});

function startListening() {
  micButton.textContent = '🛑 Stop Listening';
  micButton.classList.add('button-primary-active'); // Add active state styling
  isListening = true;

  // Use Web Speech API for speech-to-text
  const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
  recognition.lang = 'en-US';
  recognition.start();

  // When speech is detected
  recognition.onresult = async (event) => {
    const userQuery = event.results[0][0].transcript;
    queryText.textContent = userQuery;

    // Show "processing" state
    responseText.textContent = 'Processing...';

    // Send the query to the backend
    try {
      const response = await fetch('https://your-backend-url.onrender.com/process-audio/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: userQuery }),
      });

      const data = await response.json();

      // Update response text and play audio
      responseText.textContent = data.responseText;
      aiAudio.src = data.audioUrl;
      aiAudio.style.display = 'block';
      aiAudio.play();
    } catch (error) {
      responseText.textContent = 'Error: Unable to process your request.';
      console.error('Error communicating with backend:', error);
    }
  };

  // When recognition ends or is stopped
  recognition.onend = () => {
    stopListening();
  };

  recognition.onerror = (err) => {
    responseText.textContent = 'Error: Speech recognition failed.';
    console.error('Speech recognition error:', err);
    stopListening();
  };
}

function stopListening() {
  micButton.textContent = '🎤 Start Listening';
  micButton.classList.remove('button-primary-active');
  isListening = false;
}
