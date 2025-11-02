from flask import Flask, request, jsonify, send_file
import base64
import pandas as pd
from io import BytesIO
import groq
import os
from dotenv import load_dotenv

load_dotenv()

groq_api_key = os.environ["GROQ"]

flask_app = Flask(__name__)

def simple_vision_ocr_from_path(image_name):
    global groq_api_key

    if not os.path.exists(image_name):
        raise FileNotFoundError(f"Image file '{image_name}' not found in current folder.")
    with open(image_name, "rb") as f:
        image_bytes = f.read()

    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    client = groq.Groq(api_key=groq_api_key)

    prompt = (
        "Extract ALL the text from this image exactly as it appears and nothing else but in a dataframe structured format. Strictly DON'T include anything other than the text from the provided image (no code)."
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        },
                    },
                ],
            }
        ],
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        temperature=0.1,
        max_tokens=2048,
    )

    text = chat_completion.choices[0].message.content.strip()

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    df = pd.DataFrame({"line_number": range(1, len(lines) + 1), "text": lines})

    flask_app.last_json_data = df.to_dict("records")
    flask_app.last_excel = BytesIO()
    df.to_excel(flask_app.last_excel, index=False, sheet_name="Extracted Text")
    flask_app.last_excel.seek(0)

    return df


@flask_app.route("/ocr", methods=["GET"])
def ocr_api():
    
    try:
        image_name = request.args.get("image")
        if not image_name:
            return jsonify({"error": "Please provide ?image=<filename> in URL"}), 400

        df = simple_vision_ocr_from_path(image_name)
        return jsonify({
            "status": "success",
            "raw_data": df.to_dict("records")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@flask_app.route("/download", methods=["GET"])
def download_excel():
    try:
        if hasattr(flask_app, "last_excel"):
            excel_copy = BytesIO(flask_app.last_excel.getvalue())
            excel_copy.seek(0)

            return send_file(
                excel_copy,
                download_name="ocr_output.xlsx",
                as_attachment=True,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            return jsonify({"error": "No OCR data available. Please run /ocr first."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@flask_app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "message": "OCR API is running"})


if __name__ == "__main__":
    flask_app.run(debug=True)
