"""
Node: Save Ledger Entry
Creates ledger entries from extracted data and uploads audio to Supabase Storage
"""
from __future__ import annotations

from loguru import logger
from models import PipelineState
from services.ledger_service import ledger_service
from services.audio_storage_service import audio_storage_service


def save_ledger_node(state: PipelineState) -> PipelineState:
    """
    Save ledger entry from extracted data.
    
    Flow:
    1. Upload audio to Supabase Storage
    2. Generate presigned URL (7-day expiry)
    3. Create ledger entry with items and expenses
    4. Store audio segments for playback verification
    """
    logger.info("─── NODE: save_ledger_node ───")
    
    user_id = state.get("user_id")
    session_id = state.get("session_id")
    audio_path = state.get("audio_path")
    extracted_data = state.get("extracted_data", {})
    segments = state.get("segments", [])
    
    if not user_id:
        logger.warning("No user_id in state, skipping ledger save")
        return state
    
    # ── Step 1: Upload audio to Supabase Storage ─────────────────────
    audio_url = None
    storage_path = None
    
    if audio_path:
        try:
            logger.info(f"Uploading audio to Supabase Storage: {audio_path}")
            storage_path = audio_storage_service.upload_audio(
                file_path=audio_path,
                user_id=user_id,
                session_id=session_id,
            )
            
            if storage_path:
                # Generate presigned URL (valid for 7 days)
                audio_url = audio_storage_service.get_presigned_url(
                    storage_path=storage_path,
                    expires_in=604800,  # 7 days in seconds
                )
                logger.info(f"Audio uploaded successfully: {storage_path}")
            else:
                logger.warning("Audio upload failed, continuing without audio URL")
                
        except Exception as e:
            logger.error(f"Audio upload error (non-fatal): {e}")
            # Continue without audio - don't fail the entire pipeline
    
    # ── Step 2: Get transcription_id from state ──────────────────────
    # This should be set by main.py after storing transcription
    transcription_id = state.get("transcription_id")
    
    if not transcription_id:
        logger.warning("No transcription_id in state, ledger entry won't be linked")
    
    # ── Step 3: Create ledger entry ──────────────────────────────────
    try:
        ledger_entry_id = ledger_service.create_entry_from_transcription(
            user_id=user_id,
            transcription_id=transcription_id,
            extracted_data=extracted_data,
            audio_url=audio_url,
        )
        
        if ledger_entry_id:
            state["ledger_entry_id"] = ledger_entry_id
            logger.info(f"Ledger entry created: {ledger_entry_id}")
            
            # ── Step 4: Store audio segments ─────────────────────────
            if segments and audio_url:
                try:
                    audio_storage_service.store_audio_segments(
                        transcription_id=transcription_id,
                        segments=segments,
                        audio_url=audio_url,
                    )
                    logger.info(f"Stored {len(segments)} audio segments")
                except Exception as e:
                    logger.error(f"Failed to store audio segments (non-fatal): {e}")
        else:
            logger.warning("Ledger entry creation returned None")
            
    except Exception as e:
        logger.error(f"Ledger entry creation failed: {e}")
        # Don't fail the pipeline - this is a non-critical error
        state["error"] = f"Ledger save failed: {str(e)}"
    
    return state
