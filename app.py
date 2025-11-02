import groq
import base64
import pandas as pd
import json
import re
from io import BytesIO
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

groq_api_key=os.environ["GROQ"]


st.set_page_config(page_title="🧠 Vision OCR", page_icon="🧾", layout="centered")

groq_api_key = groq_api_key

def simple_vision_ocr(image_bytes):
    
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    
    client = groq.Groq(api_key=groq_api_key)
    
    prompt = "Extract ALL the text from this image exactly as it appears and nothing else but in a dataframe structured format while handling and focusing more on the handwritten texts with more precision. Strictly DON'T include anything other than the text from the provided image(no codes)."
    
    try:
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
                            }
                        }
                    ]
                }
            ],
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.1,
            max_tokens=2048
        )
        
        text = chat_completion.choices[0].message.content.strip()
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        df = pd.DataFrame({
            'line_number': range(1, len(lines) + 1),
            'text': lines
        })
        output = BytesIO()
        df.to_excel(output, index=False, sheet_name="Extracted text")
        output.seek(0)        
        return output
    
    except Exception as e:
        print(f"Error: {e}")
        return None

st.title("🧾 Groq Vision OCR")
st.caption("Upload an image to extract text and download it as an Excel file")

uploaded_file = st.file_uploader("📤 Upload Image", type=["jpg", "jpeg", "png"])
if uploaded_file:
    with st.spinner("Processing image..."):
        image_bytes = uploaded_file.read()
        excel_data = simple_vision_ocr(image_bytes)

    if excel_data:
        st.success("✅ OCR complete! Download your Excel file below.")
        st.download_button(
            label="📥 Download Extracted Text (Excel)",
            data=excel_data,
            file_name="ocr_output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )