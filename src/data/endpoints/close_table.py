from src.data.endpoints.combined import get_current_api

def close_table():

    try:
        api = get_current_api()

        if api.table_closed:
            print(f"Table {api.table_num} already closed, skipping")
            return True

        success = api.close_table()

        if success:
            print(f"✓ close_table: Successfully closed table {api.table_num}")
            return True
        else:
            print(f"✗ close_table: Failed to close table {api.table_num}")
            return False

    except RuntimeError:

        return None
    except Exception as e:
        print(f"Error in close_table: {str(e)}")
        import traceback
        traceback.print_exc()
        return False