from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
import openai
import os
from tempfile import NamedTemporaryFile

# Initialize FastAPI app
app = FastAPI()

# Set OpenAI API Key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.post("/process-audio/")
async def process_audio(file: UploadFile = File(...)):
    try:
        # Save uploaded audio file temporarily
        with NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(file.file.read())
            temp_file_path = temp_file.name

        # Use Whisper API for Speech-to-Text
        with open(temp_file_path, "rb") as audio_file:
            response = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file
            )
        user_query = response.get("text", "")

        if not user_query:
            return JSONResponse(
                status_code=400, content={"error": "Could not transcribe audio."}
            )

        # Use GPT API to generate a response
        gpt_response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=user_query,
            max_tokens=150
        )
        ai_response_text = gpt_response["choices"][0]["text"].strip()

        # Use OpenAI TTS to generate audio from the response
        tts_response = openai.Audio.create_tts(
            text=ai_response_text,
            voice="Joanna"  # Replace with the preferred voice
        )

        # Save TTS output audio temporarily
        audio_output_path = temp_file_path.replace(".wav", "_response.mp3")
        with open(audio_output_path, "wb") as audio_file:
            audio_file.write(tts_response["audio"])

        # Return AI text and TTS audio file URL
        return JSONResponse(
            content={
                "responseText": ai_response_text,
                "audioUrl": f"/get-audio/{os.path.basename(audio_output_path)}"
            }
        )

    except openai.OpenAIError as e:
        return JSONResponse(
            status_code=500, content={"error": f"OpenAI API Error: {str(e)}"}
        )

    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": f"Internal Server Error: {str(e)}"}
        )


@app.get("/get-audio/{filename}")
async def get_audio(filename: str):
    audio_path = f"/tmp/{filename}"  # Adjust this based on where temp files are saved
    if os.path.exists(audio_path):
        return FileResponse(audio_path, media_type="audio/mpeg")
    return JSONResponse(status_code=404, content={"error": "Audio file not found."})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
