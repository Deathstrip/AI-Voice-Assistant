from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import openai
import os
import requests
import json
import pandas as pd
from tempfile import NamedTemporaryFile
import base64
from io import BytesIO

# Initialize FastAPI app
app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set OpenAI API Key and Google Cloud API Key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")
google_tts_api_key = os.getenv("GOOGLE_TTS_API_KEY")

# Define model for incoming audio request
class AudioRequest(BaseModel):
    audio_base64: str

# Path to the Excel file
EXCEL_FILE_PATH = "data.xlsx"

# Function to search for a response in the Excel file
def search_excel(query):
    try:
        if not os.path.exists(EXCEL_FILE_PATH):
            return None

        # Load the Excel file
        df = pd.read_excel(EXCEL_FILE_PATH)

        # Search for the query in the Excel data (case-insensitive)
        for _, row in df.iterrows():
            if query.lower() in str(row["Query"]).lower():
                return row["Response"]  # Return the matched response

        return None
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None

# Function to convert text to speech using Google Cloud TTS
def text_to_speech_google(text):
    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={google_tts_api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "input": {"text": text},
        "voice": {"languageCode": "en-US", "ssmlGender": "FEMALE"},
        "audioConfig": {"audioEncoding": "MP3"}
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        audio_content = response.json().get("audioContent")
        return audio_content
    else:
        print("Error in TTS API:", response.json())
        return None

@app.post("/")
async def process_audio(request: AudioRequest):
    try:
        # Decode the base64 audio data
        audio_data = base64.b64decode(request.audio_base64)

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
        user_query = response.get("text", "").strip()

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
                    {"role": "system", "content": "You are Rawaf, a helpful customer service AI assistant for Rawaf Global. Always respond in English."},
                    {"role": "user", "content": user_query}
                ],
                max_tokens=500,
                temperature=0.7
            )
            ai_response_text = gpt_response['choices'][0]['message']['content'].strip()

        # Convert the final response to speech using Google TTS
        audio_base64 = text_to_speech_google(ai_response_text)

        if not audio_base64:
            return JSONResponse(
                status_code=500, content={"error": "Text-to-Speech conversion failed."}
            )

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
