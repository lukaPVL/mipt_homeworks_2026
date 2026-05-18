from dataclasses import dataclass
from typing import Optional

@dataclass
class MessageDto:
    role: str
    content: str

@dataclass
class ChatResponseDto:
    content: str
    success: bool = True
    error_message: Optional[str] = None
