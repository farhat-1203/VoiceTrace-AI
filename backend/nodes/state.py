from typing import TypedDict, Optional, List
from dataclasses import dataclass
from enum import Enum

class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    LOW = "LOW"
    APPROXIMATE = "APPROXIMATE"

class PipelineMode(str, Enum):
    ASYNC_INGESTION = "async_ingestion"
    POST_CALL_PROCESSING = "post_call_processing"

@dataclass
class ExtractedItem:
    name: str
    quantity: Optional[float]
    price_each: Optional[float]
    unit: Optional[str]
    confidence: ConfidenceLevel
    # These come from WhisperX word timestamps
    # Critical for Voice Playback with Highlights feature
    audio_start_seconds: Optional[float]
    audio_end_seconds: Optional[float]
    source_phrase: Optional[str]  # verbatim phrase that produced this

@dataclass  
class ExtractedExpense:
    category: str
    amount: float
    confidence: ConfidenceLevel
    audio_start_seconds: Optional[float]
    audio_end_seconds: Optional[float]

@dataclass
class ConfidenceFlag:
    field_name: str
    item_name: str
    extracted_value: Optional[float]
    question_hindi: str  # "Kela kitna becha? (roughly)"
    question_type: str   # "number" | "yesno"
    ledger_entry_id: str

@dataclass
class AnomalyAlert:
    alert_type: str      # "earnings" | "expense"
    message_hindi: str   # "Aaj ka kharcha double tha. Kya hua?"
    severity: str        # "medium" | "high"
    today_value: float
    usual_value: float
    trigger_vapi_call: bool

class VoiceLedgerState(TypedDict):
    # Input
    audio_path: str
    vendor_id: str
    mode: PipelineMode
    
    # Transcription outputs
    transcript: Optional[str]
    word_timestamps: Optional[List[dict]]  # WhisperX full output
    language_detected: Optional[str]
    
    # Safety outputs
    guardrail_passed: Optional[bool]
    guardrail_category: Optional[str]
    sanitized_transcript: Optional[str]
    
    # Extraction outputs
    items_sold: Optional[List[ExtractedItem]]
    expenses: Optional[List[ExtractedExpense]]
    total_revenue: Optional[float]
    total_expense: Optional[float]
    net_profit: Optional[float]
    sentiment: Optional[str]
    stock_out_mentions: Optional[List[str]]
    event_tag: Optional[str]
    
    # Confidence and clarification
    confidence_flags: Optional[List[ConfidenceFlag]]
    has_low_confidence: Optional[bool]
    
    # Anomaly detection
    anomaly_alerts: Optional[List[AnomalyAlert]]
    should_trigger_vapi: Optional[bool]
    
    # Memory and embeddings
    memory_chunks: Optional[List[str]]
    embedding_stored: Optional[bool]
    retrieved_context: Optional[List[str]]
    
    # Ledger
    ledger_entry_id: Optional[str]
    
    # Pipeline metadata for tracing
    trace_id: str
    pipeline_start_time: float
    node_timings: dict
    errors: List[str]