import json
from decimal import Decimal
from datetime import date, datetime

# Add this debug function
def debug_serialize(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    elif hasattr(obj, '__call__'):
        return str(obj)  # Convert methods to string for debugging
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
