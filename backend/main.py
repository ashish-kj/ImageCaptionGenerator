from fastapi import FastAPI, UploadFile, File, HTTPException
import requests
import base64
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LLaVA Image Captioning API")

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llava" # Make model name configurable if needed

@app.post("/caption/", summary="Generate caption for an uploaded image")
async def caption_image(file: UploadFile = File(..., description="Image file to caption")):
    """
    Receives an image file, sends it to the Ollama LLaVA model,
    and returns the generated caption.
    """
    logger.info(f"Received file: {file.filename}, content type: {file.content_type}")
    if not file.content_type.startswith("image/"):
        logger.warning(f"Invalid file type uploaded: {file.content_type}")
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")

    try:
        image_bytes = await file.read()
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        logger.info("Image successfully read and encoded.")

        payload = {
            "model": MODEL_NAME,
            "prompt": "Describe this image concisely.", # Slightly modified prompt
            "images": [image_base64],
            "stream": False
        }

        logger.info(f"Sending request to Ollama API: {OLLAMA_API_URL}")
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=60) # Add timeout
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        result = response.json()
        caption = result.get("response", "").strip()
        logger.info(f"Received caption from Ollama: '{caption}'")

        if not caption:
            logger.warning("Ollama returned an empty caption.")
            # Return a specific message instead of raising 500
            return {"caption": "Model could not generate a caption for this image."}

        return {"caption": caption}

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error with Ollama API: {e}")
        raise HTTPException(status_code=503, detail=f"Could not connect to Ollama service at {OLLAMA_API_URL}")
    except requests.exceptions.Timeout:
        logger.error("Request to Ollama API timed out.")
        raise HTTPException(status_code=504, detail="Request to Ollama timed out.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error communicating with Ollama API: {e}")
        # Provide more context if available from the response
        error_detail = f"Error communicating with Ollama: {e}"
        if e.response is not None:
             try:
                 ollama_error = e.response.json().get('error', '')
                 if ollama_error:
                     error_detail = f"Ollama error: {ollama_error}"
             except ValueError: # If response is not JSON
                 error_detail = f"Ollama error: {e.response.text}"

        raise HTTPException(status_code=502, detail=error_detail)
    except Exception as e:
        logger.error(f"An unexpected error occurred during caption generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

# Optional: Add a root endpoint for health check or info
@app.get("/", summary="API Status")
async def read_root():
    """Check if the API is running."""
    return {"message": "LLaVA Image Captioning API is running."} 