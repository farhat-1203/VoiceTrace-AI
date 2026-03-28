"""
Node: Transcribe audio using Groq Whisper with language detection
"""
from loguru import logger
from models import PipelineState
from services.transcription import transcription_service


def transcribe_node(state: PipelineState) -> PipelineState:
    """Transcribe the audio file to text with aligned segments and language detection."""
    logger.info("─── NODE: transcribe_node ───")
    try:
        result = transcription_service.transcribe(state["audio_path"])
        state["transcript"] = result["text"]
        state["segments"] = result["segments"]
        state["detected_language"] = result.get("language", "unknown")
        logger.info(
            f"Transcript ({len(result['text'])} chars, lang={state['detected_language']}): "
            f"{result['text'][:100]}..."
        )
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        state["error"] = f"Transcription failed: {str(e)}"
        state["transcript"] = ""
        state["segments"] = []
        state["detected_language"] = "unknown"
    return state
