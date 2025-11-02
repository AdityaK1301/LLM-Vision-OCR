# LLM-Vision-OCR
Vision OCR is a small prototype that extracts text from images using the Groq chat/completion API and exposes two main interfaces:

- A Flask-based HTTP API (`api.py`) for server-side OCR and downloadable Excel export.
- A Streamlit web UI (`app.py`) for upload-and-download in the browser.

This README describes the project's purpose, how to run each component, configuration, API endpoints, and known limitations / suggestions.

---

## Table of contents

- Project overview
- Files of interest
- Requirements
- Configuration
- Running locally
  - Run the Flask API
  - Run the Streamlit app
- API usage examples
  - /ocr
  - /download
  - /health
- Streamlit app usage
- Output format
- Security & privacy notes
- Known issues & suggested improvements
- License

---

## Project overview

This project sends an image (base64) to the Groq chat/completions endpoint with a prompt to extract the text exactly as it appears, parses the returned text into line-by-line rows, and stores that result both as JSON and as an Excel file (in memory) for later download.

- `api.py` exposes HTTP endpoints to trigger OCR against an image file path on the server and to download the last generated Excel file.
- `app.py` is a Streamlit web app that allows a user to upload an image, calls the Groq chat/completions API, and offers the result as an Excel download directly to the browser.

---

## Files of interest

- `api.py` — Flask application.
  - Endpoints:
    - GET `/ocr?image=<filename>` — run OCR on a server-side image file (expects a file present in the current working folder).
    - GET `/download` — returns the last generated `.xlsx` (from the last OCR call) as an attachment.
    - GET `/health` — basic health check.
  - When an OCR run completes, the server keeps the extracted text in-memory:
    - `flask_app.last_json_data` — list of objects representing lines (for JSON responses).
    - `flask_app.last_excel` — BytesIO with Excel bytes for download.

- `app.py` — Streamlit application for client-side use.
  - Uploads an image in the browser and uses the Groq client to create the same chat/completion request.
  - Returns an Excel file for browser download.

- `image.txt` — contains a base64-encoded image (example). Not required to run the apps but present in the repository.

---

## Requirements

Python 3.9+ (recommended). The project uses:

- Flask
- Streamlit
- pandas
- groq (Groq client)
- openpyxl (for Excel generation with pandas) — pandas uses it to write .xlsx

Install with pip:


```
pip install flask streamlit pandas openpyxl groq
```

Note: the `groq` client is required and must be installed from the proper package source (pip registry or internal). Confirm package name and availability for your environment.

---

## Configuration

- The Groq API key is used by both `api.py` and `app.py`.

To read the key:

```python
from dotenv import load_dotenv
import os

load_dotenv()
groq_api_key = os.environ("GROQ")
```

The key is kept in the .env file as:
```
GROQ="gsk......"
```

---

## Running locally

1. Create and activate a virtual environment (optional but recommended):

```
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
.venv\Scripts\activate      # Windows
```

2. Install dependencies:

```
pip install flask streamlit pandas openpyxl groq
```

3. Set the Groq API key as an environment variable:

```
export GROQ="your_groq_api_key_here"  # macOS / Linux
set GROQ="your_groq_api_key_here"     # Windows (cmd)
```

4. Running the Flask API:

```
python api.py
```

By default Flask starts in debug mode and binds to `http://127.0.0.1:5000`.

5. Running the Streamlit app:

```
streamlit run app.py
```

Streamlit will open a browser window (usually at `http://localhost:8501`).

---

## API usage examples

Note: `api.py` expects the image to be present on the server side (filename path relative to the process's working directory). It does not accept image uploads via HTTP in the current implementation.

- Start the Flask API, then:

1) Run OCR on a server-side image file:

```
Invoke-RestMethod -Uri "http://127.0.0.1:5000/ocr?image=test.jpg" -Method GET | ConvertTo-Json -Depth 4
```

Response (JSON):

```
{
  "status": "success",
  "raw_data": [
    {"line_number": 1, "text": "First line"},
    {"line_number": 2, "text": "Second line"},
    ...
  ]
}
```

2) Download the last Excel produced by the OCR:

```
Invoke-WebRequest -Uri "http://127.0.0.1:5000/download" -OutFile "ocr_output.xlsx"
```

This returns `ocr_output.xlsx` (attachment) created from the last `/ocr` call.

3) Health check:

```
Invoke-RestMethod -Uri "http://127.0.0.1:5000/health" -Method GET
```

Response:

```
{"status":"healthy","message":"OCR API is running"}
```

---

## Streamlit app usage

- Open `http://localhost:8501` after running:

```
streamlit run app.py
```

- Use the "Upload Image" control to select a JPG/PNG image from your machine.
- The app will:
  - Convert the uploaded file to base64 and call the Groq chat API (same prompt).
  - Convert the response to an Excel file in memory and present a Download button to get `ocr_output.xlsx`.

The Streamlit path processes the uploaded file in-memory and does not rely on server-side saved files.

---

## Output format

- JSON (via the Flask API `/ocr`) returns `raw_data` as a list of objects:
  - `{ "line_number": <int>, "text": "<line text>" }`

- Excel file:
  - A single sheet `Extracted Text`
  - Two columns:
    - `line_number`
    - `text`

---

## Prompting considerations

The code prompts the model:

- "Extract ALL the text from this image exactly as it appears and nothing else but in a dataframe structured format. Strictly DON'T include anything other than the text from the provided image (no code)."

Real LLM outputs can sometimes include disclaimers or formatting. The code currently splits model output by newline and stores each non-empty line. For more robust parsing, you may want to request structured JSON in the prompt and validate JSON parsing.

---

## License

Add your preferred license file (e.g., MIT). This repository currently has no license file included.

---

## Known Improvements
- Convert `api.py` to accept file uploads (multipart/form-data) and return a unique download URL.
- Prepare a `requirements.txt` and a dockerfile for containerized deployment.
