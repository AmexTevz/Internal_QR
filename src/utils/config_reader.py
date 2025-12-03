def read_store_data(file_path):
    try:
        with open(file_path, 'r') as file:
            stores = [line.strip() for line in file if line.strip()]
            return stores
    except FileNotFoundError:
        raise FileNotFoundError(f"Store data file not found: {file_path}")
    except Exception as e:
        raise Exception(f"Error reading store data: {str(e)}")

def get_all_stores():
    stores = read_store_data('src/data/stores.csv')
    return stores