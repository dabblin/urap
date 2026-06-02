"""Pydantic model for the LeadStatusObject — single source of truth for all channel state."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ChannelStatus(str, Enum):
    IDLE = "idle"
    SENT = "sent"
    OPENED = "opened"
    REPLIED = "replied"
    BOUNCED = "bounced"
    PAUSED = "paused"
    OPT_OUT = "opted_out"
    CONNECTED = "connected"
    MESSAGED = "messaged"
    DIALED = "dialed"
    ANSWERED = "answered"
    VOICEMAIL = "voicemail"


class GlobalStatus(str, Enum):
    PROSPECTING = "prospecting"
    ENGAGED = "engaged"
    INTERESTED = "interested"
    MEETING_SET = "meeting_set"
    QUALIFIED = "qualified"
    NOT_INTERESTED = "not_interested"
    UNSUBSCRIBE = "unsubscribe"


class ContactData(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    company: str
    title: str
    intent_signals: List[str] = Field(default_factory=list)


class ChannelState(BaseModel):
    email: ChannelStatus = ChannelStatus.IDLE
    sms: ChannelStatus = ChannelStatus.IDLE
    linkedin: ChannelStatus = ChannelStatus.IDLE
    voice: ChannelStatus = ChannelStatus.IDLE


class ConsentRecord(BaseModel):
    source: str  # TrustedForm cert URL
    consented_at: datetime
    ip_address: str
    one_to_one_rule: bool
    platform_name: str


class LeadStatusObject(BaseModel):
    lead_id: str
    tenant_id: str
    contact_data: ContactData
    channel_state: ChannelState = Field(default_factory=ChannelState)
    global_status: GlobalStatus = GlobalStatus.PROSPECTING
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    assigned_agent: Optional[str] = None
    consent_record: Optional[ConsentRecord] = None
