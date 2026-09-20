# Copyright (C) 2026 Michael MacMullen
from pydantic import BaseModel
import uuid


class Mailbox(BaseModel):
    id: uuid.UUID
    address: str
    password_hash: bytes


class Mail(BaseModel):
    id: uuid.UUID
    recipient_address: str
    sender_address: str
    subject: str
    content: str