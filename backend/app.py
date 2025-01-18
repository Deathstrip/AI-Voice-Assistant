from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import openai
import os
from tempfile import NamedTemporaryFile
from io import BytesIO
import base64
from gtts import gTTS

# Initialize FastAPI app
app = FastAPI()

# CORS Middleware to allow requests from your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ai-voice-assistant-rawaf-global.onrender.com"],  # Allow requests from your frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Set OpenAI API Key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.post("/")
async def process_audio(audio_base64: str):
    try:
        # Decode the base64 audio data
        audio_data = base64.b64decode(audio_base64)

        # Save the audio data as a temporary WAV file
        with NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(audio_data)
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
        gpt_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Use "gpt-4" if needed
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_query}
            ],
            max_tokens=150
        )
        ai_response_text = gpt_response['choices'][0]['message']['content'].strip()

        # Convert text to speech using gTTS
        tts = gTTS(text=ai_response_text, lang="en")
        audio_io = BytesIO()
        tts.write_to_fp(audio_io)
        audio_io.seek(0)

        # Encode the generated audio as base64
        audio_base64 = base64.b64encode(audio_io.read()).decode("utf-8")

        # Return AI text response and audio as base64
        return JSONResponse(
            content={
                "responseText": ai_response_text,
                "audioBase64": audio_base64
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
