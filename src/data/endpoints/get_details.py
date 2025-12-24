

import requests
import json
from src.data.endpoints.combined import get_current_api


def get_check_details():

    try:
        # Get the API instance for this worker
        api = get_current_api()


        data = api.get_check_details()

        if data:
            return data
        else:
            print(f"✗ get_check_details: Failed to retrieve data")
            return None

    except RuntimeError:
        # API not initialized yet (called at import time or before fixture)
        # This is OK - just return None silently
        return None
    except Exception as e:
        print(f"Error in get_check_details: {str(e)}")
        return None


# Backward compatibility
def get_check_details_legacy():
    """
    Legacy function name for backward compatibility.
    Use get_check_details() instead.
    """
    return get_check_details()