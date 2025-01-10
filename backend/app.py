from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
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
        # Save the uploaded audio file temporarily
        with NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(file.file.read())
            temp_file_path = temp_file.name

        # Use OpenAI Whisper API for transcription
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

        # Use GPT-3 API to generate a response based on the transcribed text
        gpt_response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=user_query,
            max_tokens=150
        )
        ai_response_text = gpt_response["choices"][0]["text"].strip()

        # Return the AI's response as JSON
        return JSONResponse(
            content={
                "responseText": ai_response_text,
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
