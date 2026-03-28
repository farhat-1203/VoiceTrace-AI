"""
Audio Storage Service - Manages audio file uploads to S3 or Supabase Storage
Links audio files to transcriptions and ledger entries with presigned URLs
"""
from __future__ import annotations

import os
from typing import Optional, Literal
from datetime import timedelta
from loguru import logger

from services.supabase_service import supabase_service


class AudioStorageService:
    """Handles audio file storage and presigned URL generation."""

    BUCKET_NAME = "audio-recordings"
    
    def __init__(self):
        # Determine storage backend from environment
        self.storage_backend: Literal["s3", "supabase"] = os.getenv("AUDIO_STORAGE_BACKEND", "supabase")
        
        if self.storage_backend == "s3":
            self._init_s3()
        else:
            self._ensure_bucket()
    
    def _init_s3(self):
        """Initialize S3 client if using S3 backend."""
        try:
            import boto3
            from botocore.config import Config
            
            self.s3_bucket = os.getenv("AWS_S3_BUCKET", "voicetrace-audio")
            self.s3_region = os.getenv("AWS_REGION", "us-east-1")
            
            # Initialize S3 client
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=self.s3_region,
                config=Config(signature_version='s3v4')
            )
            
            logger.info(f"S3 storage initialized: bucket={self.s3_bucket}, region={self.s3_region}")
        except ImportError:
            logger.error("boto3 not installed. Install with: pip install boto3")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize S3: {e}")
            raise

    def _ensure_bucket(self):
        """Create the audio storage bucket if it doesn't exist."""
        try:
            if not supabase_service._client:
                return
            
            # Check if bucket exists
            buckets = supabase_service._client.storage.list_buckets()
            bucket_names = [b.name for b in buckets]
            
            if self.BUCKET_NAME not in bucket_names:
                logger.info(f"Creating Supabase Storage bucket: {self.BUCKET_NAME}")
                supabase_service._client.storage.create_bucket(
                    self.BUCKET_NAME,
                    options={"public": False}  # Private bucket
                )
            else:
                logger.info(f"Supabase Storage bucket '{self.BUCKET_NAME}' exists")
                
        except Exception as e:
            logger.warning(f"Could not ensure bucket exists: {e}")

    def upload_audio(
        self,
        file_path: str,
        user_id: str,
        session_id: str,
    ) -> Optional[str]:
        """
        Upload audio file to S3 or Supabase Storage.
        
        Args:
            file_path: Local path to audio file
            user_id: Owner's user ID
            session_id: Unique session identifier
        
        Returns:
            Storage path or None on failure
        """
        if self.storage_backend == "s3":
            return self._upload_to_s3(file_path, user_id, session_id)
        else:
            return self._upload_to_supabase(file_path, user_id, session_id)
    
    def _upload_to_s3(
        self,
        file_path: str,
        user_id: str,
        session_id: str,
    ) -> Optional[str]:
        """Upload audio file to S3."""
        try:
            if not os.path.exists(file_path):
                logger.error(f"Audio file not found: {file_path}")
                return None
            
            # Generate storage path: user_id/session_id.ext
            ext = os.path.splitext(file_path)[1]
            storage_path = f"{user_id}/{session_id}{ext}"
            
            # Upload to S3
            self.s3_client.upload_file(
                file_path,
                self.s3_bucket,
                storage_path,
                ExtraArgs={
                    'ContentType': self._get_mime_type(ext),
                    'Metadata': {
                        'user_id': user_id,
                        'session_id': session_id
                    }
                }
            )
            
            logger.info(f"Uploaded audio to S3: s3://{self.s3_bucket}/{storage_path}")
            return storage_path
            
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            return None
    
    def _upload_to_supabase(
        self,
        file_path: str,
        user_id: str,
        session_id: str,
    ) -> Optional[str]:
        """Upload audio file to Supabase Storage."""
        try:
            if not os.path.exists(file_path):
                logger.error(f"Audio file not found: {file_path}")
                return None
            
            # Generate storage path: user_id/session_id.ext
            ext = os.path.splitext(file_path)[1]
            storage_path = f"{user_id}/{session_id}{ext}"
            
            # Read file
            with open(file_path, "rb") as f:
                file_data = f.read()
            
            # Upload to Supabase Storage
            result = supabase_service._client.storage.from_(self.BUCKET_NAME).upload(
                path=storage_path,
                file=file_data,
                file_options={"content-type": self._get_mime_type(ext)}
            )
            
            logger.info(f"Uploaded audio to Supabase Storage: {storage_path}")
            return storage_path
            
        except Exception as e:
            logger.error(f"Supabase upload failed: {e}")
            return None

    def get_presigned_url(
        self,
        storage_path: str,
        expires_in: int = 3600,  # 1 hour default
    ) -> Optional[str]:
        """
        Generate a presigned URL for audio playback.
        
        Args:
            storage_path: Path in storage
            expires_in: URL expiry time in seconds
        
        Returns:
            Presigned URL or None on failure
        """
        if self.storage_backend == "s3":
            return self._get_s3_presigned_url(storage_path, expires_in)
        else:
            return self._get_supabase_presigned_url(storage_path, expires_in)
    
    def _get_s3_presigned_url(
        self,
        storage_path: str,
        expires_in: int = 3600,
    ) -> Optional[str]:
        """Generate presigned URL for S3 object."""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.s3_bucket,
                    'Key': storage_path
                },
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            logger.error(f"S3 presigned URL generation failed: {e}")
            return None
    
    def _get_supabase_presigned_url(
        self,
        storage_path: str,
        expires_in: int = 3600,
    ) -> Optional[str]:
        """Generate presigned URL for Supabase Storage object."""
        try:
            result = supabase_service._client.storage.from_(self.BUCKET_NAME).create_signed_url(
                path=storage_path,
                expires_in=expires_in
            )
            
            if result and "signedURL" in result:
                return result["signedURL"]
            
            logger.error(f"Failed to generate presigned URL for {storage_path}")
            return None
            
        except Exception as e:
            logger.error(f"Presigned URL generation failed: {e}")
            return None

    def store_audio_segments(
        self,
        transcription_id: str,
        segments: list[dict],
        audio_url: Optional[str] = None,
    ) -> bool:
        """
        Store audio segment metadata for playback verification.
        
        Args:
            transcription_id: Reference to transcription
            segments: List of segment dicts with start, end, text
            audio_url: Optional presigned URL to full audio
        
        Returns:
            Success status
        """
        try:
            for idx, segment in enumerate(segments):
                segment_data = {
                    "transcription_id": transcription_id,
                    "segment_index": idx,
                    "start_time": float(segment.get("start", 0)),
                    "end_time": float(segment.get("end", 0)),
                    "text": segment.get("text", ""),
                    "audio_url": audio_url,
                }
                
                supabase_service._client.table("audio_segments").insert(segment_data).execute()
            
            logger.info(f"Stored {len(segments)} audio segments for transcription {transcription_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store audio segments: {e}")
            return False

    def link_segment_to_entity(
        self,
        segment_id: str,
        entity_type: str,  # 'item', 'expense', 'earning'
        entity_id: str,
    ) -> bool:
        """Link an audio segment to an extracted entity for playback verification."""
        try:
            supabase_service._client.table("audio_segments").update({
                "entity_type": entity_type,
                "entity_id": entity_id,
            }).eq("id", segment_id).execute()
            
            return True
        except Exception as e:
            logger.error(f"Failed to link segment to entity: {e}")
            return False

    def get_segments_for_transcription(self, transcription_id: str) -> list[dict]:
        """Get all audio segments for a transcription."""
        try:
            result = supabase_service._client.table("audio_segments")\
                .select("*")\
                .eq("transcription_id", transcription_id)\
                .order("segment_index")\
                .execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get audio segments: {e}")
            return []

    def _get_mime_type(self, ext: str) -> str:
        """Get MIME type for audio file extension."""
        mime_map = {
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".m4a": "audio/mp4",
            ".ogg": "audio/ogg",
            ".flac": "audio/flac",
            ".webm": "audio/webm",
        }
        return mime_map.get(ext.lower(), "audio/mpeg")

    def delete_audio(self, storage_path: str) -> bool:
        """Delete an audio file from storage."""
        try:
            supabase_service._client.storage.from_(self.BUCKET_NAME).remove([storage_path])
            logger.info(f"Deleted audio from storage: {storage_path}")
            return True
        except Exception as e:
            logger.error(f"Audio deletion failed: {e}")
            return False


# Module-level singleton
audio_storage_service = AudioStorageService()
