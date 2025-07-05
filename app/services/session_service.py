from utils.session_manager import get_session_manager as _get_session_manager

_session_manager_instance = None

def get_session_manager():
    """Get the session manager instance (singleton pattern)"""
    global _session_manager_instance
    if _session_manager_instance is None:
        _session_manager_instance = _get_session_manager()
    return _session_manager_instance 