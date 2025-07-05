from utils.response_formatter import get_response_formatter as _get_response_formatter

_response_formatter_instance = None

def get_response_service():
    """Get the response service instance (singleton pattern)"""
    global _response_formatter_instance
    if _response_formatter_instance is None:
        _response_formatter_instance = _get_response_formatter()
    return _response_formatter_instance 