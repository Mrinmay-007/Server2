# from fastapi import APIRouter #type: ignore


# router = APIRouter()

# # Google Cloud Translate docs. 
# # BHASHINI official site, docs and GitBook. 
# # AI4Bharat (IndicTrans2 / IndicBART) & Hugging Face models. 

from fastapi import APIRouter, HTTPException, Query
from googletrans import Translator

router = APIRouter(
    prefix="/translate",
    tags=["Translation"]
)
translator = Translator()

# Supported Indian languages and their language codes for Google Translate
SUPPORTED_LANGUAGES = {
    "bengali": "bn",
    "bhojpuri": "bho",
    "gujarati": "gu",
    "hindi": "hi",
    "kannada": "kn",
    "maithili": "mai",
    "malayalam": "ml",
    "marathi": "mr",
    "meitei": "mni-Mtei",
    "odia": "or",
    "punjabi": "pa",
    "sanskrit": "sa",
    "tamil": "ta",
    "telugu": "te",
    "urdu": "ur",
    "santali": "sat",
    "awadhi": "awa",
    "bodo": "brx",
    "khasi": "kha",
    "kokborok": "trp",
    "marwadi": "mwr",
    "tulu": "tcy"
}


@router.get("/")
async def translate_text(
    text: str = Query(..., description="Text to translate (English)"),
    target_language: str = Query(..., description="Target Indian language name (e.g., 'hindi')")
):
    target_language = target_language.lower()

    if target_language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language. Choose from: {', '.join(SUPPORTED_LANGUAGES.keys())}"
        )

    try:
        lang_code = SUPPORTED_LANGUAGES[target_language]
        translated = translator.translate(text, src='en', dest=lang_code)
        return {
            "source_language": "English",
            "target_language": target_language.capitalize(),
            "translated_text": translated.text
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
