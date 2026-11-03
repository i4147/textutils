import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def refine_text(raw_text: str, is_empty: bool = False) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in environment")
    client = OpenAI(api_key=api_key)
    if is_empty or not raw_text.strip():
        system_message = "You are an expert at transcribing and cleaning up OCR text from handwritten notes."
        user_message = "The OCR failed to extract any meaningful text from this handwritten image. Please respond with: 'The OCR system could not extract text from this handwritten image. Please try with a clearer image, different OCR settings, or manual transcription.'"
    else:
        system_message = "You are an expert at transcribing and cleaning up OCR text from handwritten notes. You understand common OCR errors with handwriting and can intelligently correct them."
        user_message = f"Clean up and correct the following OCR text from handwritten notes. The text might have significant errors due to the limitations of OCR with handwriting. Use your best judgment to reconstruct the likely original text, but don't invent content that's not supported by the OCR output.\n\nOCR text:\n{raw_text}"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
        max_tokens=2048,
        temperature=0.2,
    )
    content = response.choices[0].message.content
    return (content or "").strip()
