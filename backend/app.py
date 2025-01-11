from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import openai
import os
import base64
from io import BytesIO
from tempfile import NamedTemporaryFile
from gtts import gTTS

# Initialize FastAPI app
app = FastAPI()

# Set OpenAI API Key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.post("/process-audio/")
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
