// API URL of your backend
const API_URL = "https://ai-voice-assistant-as7w.onrender.com";

// Handle microphone recording and send to backend
let recorder, audioChunks;
let isRecording = false;

// Toggle recording
async function toggleRecording() {
    const micButton = document.getElementById("micButton");
    const micIcon = document.getElementById("micIcon");
    const micStatus = document.getElementById("micStatus");

    if (isRecording) {
        // Stop recording
        micButton.classList.remove("active");
        micIcon.classList.remove("fa-microphone-slash");
        micIcon.classList.add("fa-microphone");
        micStatus.textContent = "Click to start speaking";

        isRecording = false;
        stopRecording();
    } else {
        // Start recording
        micButton.classList.add("active");
        micButton.classList.remove("idle");
        micIcon.classList.remove("fa-microphone");
        micIcon.classList.add("fa-microphone-slash");
        micStatus.textContent = "Listening...";

        isRecording = true;
        startRecording();
    }
}

// Start recording audio
async function startRecording() {
    const resultDiv = document.getElementById("result");
    resultDiv.innerText = "Listening...";

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    recorder = mediaRecorder;

    audioChunks = [];
    recorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
    };

    recorder.start();
}

// Stop recording and send the audio to the backend
async function stopRecording() {
    const resultDiv = document.getElementById("result");
    resultDiv.innerText = "Processing audio...";

    recorder.stop();
    recorder.onstop = async () => {
        // Combine audio chunks into a single Blob
        const audioBlob = new Blob(audioChunks, { type: "audio/wav" });

        // Convert audio Blob to base64
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = async () => {
            const base64Audio = reader.result.split(",")[1]; // Remove metadata

            try {
                // Send the base64 audio to the backend
                const response = await fetch(API_URL, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ audio_base64: base64Audio }),
                });

                if (!response.ok) {
                    throw new Error(`Server error: ${response.statusText}`);
                }

                // Parse the response
                const result = await response.json();

                // Display the AI's text response
                if (result.responseText) {
                    resultDiv.innerText = `AI Response: ${result.responseText}`;
                }

                // Play the AI's audio response if available
                if (result.audioBase64) {
                    const audioData = atob(result.audioBase64);
                    const audioBlob = new Blob([new Uint8Array(audioData.split("").map((char) => char.charCodeAt(0)))], { type: "audio/mpeg" });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    const audio = new Audio(audioUrl);
                    audio.play();
                } else {
                    resultDiv.innerText += "\n(Audio response unavailable)";
                }
            } catch (error) {
                console.error("Error:", error);
                resultDiv.innerText = `Error: ${error.message}`;
            }
        };
    };
}
