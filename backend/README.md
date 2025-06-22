# Facty Backend

## How to run

1. Install dependencies (in this folder):

    pip install -r requirements.txt

2. Make sure your `.env` file is present in this folder and contains your Hugging Face API token:

    HF_API_TOKEN=your_hf_token_here

3. Start the FastAPI server:

    uvicorn app_V4:app --reload

The API will be available at http://127.0.0.1:8000

## Endpoints
- POST `/chat` — main chat endpoint for the frontend.
