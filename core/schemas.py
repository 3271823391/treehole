from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EmotionAnalysis(BaseModel):
    sentiment: Literal["positive", "neutral", "negative"] = "neutral"
    intent: str = "venting"
    arousal: float = 0.2
    valence: float = 0.0
    anxiety: float = 0.0
    anger: float = 0.0
    sadness: float = 0.0
    risk_self_harm: float = Field(default=0.0, ge=0.0, le=1.0)
    risk_violence: float = Field(default=0.0, ge=0.0, le=1.0)
    risk_abuse: float = Field(default=0.0, ge=0.0, le=1.0)
    notes: str = ""


class ReplyPlan(BaseModel):
    warmth: float = 0.6
    calmness: float = 0.6
    firmness: float = 0.3
    verbosity: float = 0.45
    empathy: float = 0.7
    directness: float = 0.5
    safety_mode: bool = False
    style_flags: list[str] = Field(default_factory=list)
    banned_phrases: list[str] = Field(default_factory=list)


class TurnRecord(BaseModel):
    round_id: int
    user_text: str
    assistant_text: str = ""
    analysis: EmotionAnalysis
    plan: ReplyPlan
    error: str = ""
    created_at: float


class ConversationState(BaseModel):
    conv_key: str
    user_id: str
    device_id: str
    character_id: str
    round_seq: int = 0
    summary: str = ""
    turns: list[TurnRecord] = Field(default_factory=list)
    last_plan: ReplyPlan | None = None
