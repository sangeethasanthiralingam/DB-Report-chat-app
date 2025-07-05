from utils.data_processor import get_data_processor as _get_data_processor

_data_processor_instance = None

def get_data_service():
    """Get the data service instance (singleton pattern)"""
    global _data_processor_instance
    if _data_processor_instance is None:
        _data_processor_instance = _get_data_processor()
    return _data_processor_instance 