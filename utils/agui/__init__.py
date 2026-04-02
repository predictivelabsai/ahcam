"""
AG-UI integration for FastHTML + LangGraph.

Adapted from AHMF for AHCAM collection account management domain.
"""

from .core import setup_agui, AGUISetup, AGUIThread, UI, StreamingCommand
from .styles import get_chat_styles, get_custom_theme, CHAT_UI_STYLES
from .chat_store import (
    save_conversation, save_message,
    load_conversation_messages, list_conversations,
    delete_conversation,
)

__all__ = [
    "setup_agui",
    "AGUISetup",
    "AGUIThread",
    "UI",
    "StreamingCommand",
    "get_chat_styles",
    "get_custom_theme",
    "CHAT_UI_STYLES",
    "save_conversation",
    "save_message",
    "load_conversation_messages",
    "list_conversations",
    "delete_conversation",
]
