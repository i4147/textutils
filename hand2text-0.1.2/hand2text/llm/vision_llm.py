import base64
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def vision_llm_transcribe(image_path: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        msg = "OPENAI_API_KEY not set"
        raise RuntimeError(msg)
    client = OpenAI(api_key=api_key)
    base64_image = encode_image(image_path)
    vision_models = [
        "gpt-4o",
        "gpt-4-vision-preview",
        "gpt-4-turbo",
    ]
    for model in vision_models:
        try:
            print(f"[VISION] Trying model: {model}")
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at transcribing handwritten text from images.",
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Transcribe the handwritten text in this image. Preserve formatting.",
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                            },
                        ],
                    },
                ],
                max_tokens=1000,
            )
            print(f"[VISION] Successfully used model: {model}")
            content = resp.choices[0].message.content
            return content or ""
        except Exception as e:
            print(f"[VISION] Error with model {model}: {e!s}")
            continue
    print("[VISION] All vision models failed. Falling back to OCR + GPT-3.5")
    from .refine import refine_text
    from ..ocr.ocr import image_to_text

    ocr_text = image_to_text(image_path)
    is_empty = not ocr_text or ocr_text.isspace()
    refined_text = refine_text(ocr_text, is_empty)
    return refined_text
