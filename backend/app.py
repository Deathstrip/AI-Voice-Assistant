from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import openai
import os
from tempfile import NamedTemporaryFile

# Initialize FastAPI app
app = FastAPI()

# Set your OpenAI API key
openai.api_key = "YOUR_OPENAI_API_KEY"

@app.post("/process-audio/")
async def process_audio(file: UploadFile = File(...)):
    # Save the uploaded file
    with NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        temp_file.write(file.file.read())
        temp_file_path = temp_file.name

    # Convert audio to text using OpenAI Whisper API
    with open(temp_file_path, "rb") as audio_file:
        transcription = openai.Audio.transcribe("whisper-1", audio_file)
    text_query = transcription.get("text", "")

    # Generate AI response using GPT
    gpt_response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=text_query,
        max_tokens=150
    )
    ai_text_response = gpt_response["choices"][0]["text"].strip()

    # Convert GPT response to audio using OpenAI TTS (mock example)
    tts_response = openai.Audio.create_tts(
        text=ai_text_response,
        voice="Joanna"  # Replace with preferred voice
    )

    # Save the audio response to a file
    audio_output_path = temp_file_path.replace(".wav", "_response.mp3")
    with open(audio_output_path, "wb") as audio_file:
        audio_file.write(tts_response["audio"])

    # Return the audio file to the frontend
    return FileResponse(audio_output_path, media_type="audio/mpeg")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
