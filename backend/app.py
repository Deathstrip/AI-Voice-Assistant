from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import openai
import os
import pandas as pd
from io import BytesIO
from tempfile import NamedTemporaryFile
import base64
from gtts import gTTS

# Initialize FastAPI app
app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ai-voice-assistant-rawaf-global.onrender.com"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set OpenAI API Key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

# Define model for incoming request
class AudioRequest(BaseModel):
    audio_base64: str

# Define function to search for a response in the Excel file
def search_excel(query):
    try:
        file_path = "data.xlsx"  # Path to your Excel file
        if not os.path.exists(file_path):
            return None

        # Load the Excel file
        df = pd.read_excel(file_path)

        # Search for the query in the Excel data (case-insensitive)
        for _, row in df.iterrows():
            if query.lower() in str(row['Query']).lower():
                return row['Response']  # Return the matched response

        return None
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None

@app.post("/")
async def process_audio(request: AudioRequest):
    try:
        audio_base64 = request.audio_base64

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

        # Search for a response in the Excel file
        excel_response = search_excel(user_query)

        if excel_response:
            # Use the response from the Excel file
            ai_response_text = excel_response
        else:
            # Use GPT API to generate a response if no match is found in Excel
            gpt_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are Rawaf, a helpful customer service AI assistant for Rawaf Global."},
                    {"role": "user", "content": user_query}
                ],
                max_tokens=500,  # Allow longer responses
                temperature=0.7  # Adjust creativity if needed
            )
            ai_response_text = gpt_response['choices'][0]['message']['content'].strip()

        # Convert the final response to speech using gTTS
        tts_lang = "ar" if any(char in "ءاآإأبجدهوزحطكلمنسعفصقكلمهةىي" for char in ai_response_text) else "en"
        tts = gTTS(text=ai_response_text, lang=tts_lang)
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
