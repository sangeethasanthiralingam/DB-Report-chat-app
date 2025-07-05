from utils.chat_processor import get_chat_processor as _get_chat_processor

_chat_processor_instance = None

def get_chat_service():
    """Get the chat service instance (singleton pattern)"""
    global _chat_processor_instance
    if _chat_processor_instance is None:
        _chat_processor_instance = _get_chat_processor()
    return _chat_processor_instance 