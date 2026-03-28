"""
Node: Transcribe audio using WhisperX
"""
from loguru import logger
from models import PipelineState
from services.transcription import transcription_service


def transcribe_node(state: PipelineState) -> PipelineState:
    """Transcribe the audio file to text with aligned segments."""
    logger.info("─── NODE: transcribe_node ───")
    try:
        result = transcription_service.transcribe(state["audio_path"])
        state["transcript"] = result["text"]
        state["segments"] = result["segments"]
        logger.info(f"Transcript ({len(result['text'])} chars): {result['text'][:100]}...")
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        state["error"] = f"Transcription failed: {str(e)}"
        state["transcript"] = ""
        state["segments"] = []
    return state
