// API URL of your backend
const API_URL = "https://ai-voice-assistant-as7w.onrender.com/";

// Handle file upload and send to backend
async function handleFileUpload(event) {
    event.preventDefault();
    
    // Get the file from the input
    const fileInput = document.getElementById("audioFile");
    const file = fileInput.files[0];

    if (!file) {
        alert("Please upload a file!");
        return;
    }

    // Create a FormData object
    const formData = new FormData();
    formData.append("file", file);

    // Display loading message
    const resultDiv = document.getElementById("result");
    resultDiv.innerText = "Processing your audio...";

    try {
        // Send the file to the backend
        const response = await fetch(API_URL, {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.statusText}`);
        }

        // Parse the response
        const result = await response.json();

        // Display the AI's response
        if (result.responseText) {
            resultDiv.innerText = `AI Response: ${result.responseText}`;
        } else if (result.error) {
            resultDiv.innerText = `Error: ${result.error}`;
        } else {
            resultDiv.innerText = "Unexpected response from the server.";
        }
    } catch (error) {
        console.error("Error:", error);
        resultDiv.innerText = `Error: ${error.message}`;
    }
}

// Attach event listener to the form
document.getElementById("audioForm").addEventListener("submit", handleFileUpload);
