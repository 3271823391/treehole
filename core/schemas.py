from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EmotionAnalysis(BaseModel):
    intent: str = "venting"
    valence: float = 0.0
    arousal: float = 0.3
    anxiety: float = 0.2
    anger: float = 0.1
    sadness: float = 0.2
    risk_self_harm: float = Field(default=0.0, ge=0.0, le=1.0)
    risk_violence: float = Field(default=0.0, ge=0.0, le=1.0)
    summary: str = "neutral"
    error: str | None = None


class ReplyPlan(BaseModel):
    warmth: float = Field(default=0.7, ge=0.0, le=1.0)
    calmness: float = Field(default=0.7, ge=0.0, le=1.0)
    firmness: float = Field(default=0.4, ge=0.0, le=1.0)
    verbosity: float = Field(default=0.5, ge=0.0, le=1.0)
    safety_mode: bool = False
    style_flags: list[str] = Field(default_factory=list)


class TurnRecord(BaseModel):
    round_id: int
    user_text: str
    assistant_text: str = ""
    analysis: EmotionAnalysis
    plan: ReplyPlan
    error: str | None = None


class ConversationState(BaseModel):
    conv_key: str
    round_seq: int = 0
    summary: str = ""
    turns: list[TurnRecord] = Field(default_factory=list)
