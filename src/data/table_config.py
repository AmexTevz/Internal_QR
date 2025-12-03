"""
Table Configuration
Maps table numbers to their corresponding table IDs (GUIDs)
Location: /src/data/table_config.py
"""

# Table ID to Table Number mapping - First 10 tables
TABLE_MAPPING = {
    1: "7230F695-E841-4283-8611-53C9C0C46FFB",
    2: "7A10BDF2-92BD-475C-B506-F9494612F83F",
    3: "4F075B94-A58B-48E1-B906-40ACDC26B9AC",
    4: "0DC4518B-85FA-4A8E-84FB-0767B6F0EDD9",
    5: "1697B1EB-1013-40EF-85E0-625BFED736C2",
    6: "69670409-B895-4655-832F-3265CF32E1D9",
    7: "F77BB632-2CFB-400C-9F7C-28A4569A3DFB",
    8: "B25F66BA-C7B0-43A3-9BFC-A21B97845480",
    9: "2A57EDE7-79D7-454E-B171-F5C662531FBD",
    10: "38A31859-CA10-452C-BF40-ED361D7F6749",  # Default table
}

# Default table number (maintains backward compatibility)
DEFAULT_TABLE_NUMBER = 10

# Base URL template
BASE_URL_TEMPLATE = "https://nextgen-frontend-dev-b0chfba5a6hyb3ga.eastus-01.azurewebsites.net/{table_id}"


def get_table_id(table_number):
    """
    Get table ID (GUID) for a given table number.

    Args:
        table_number: Table number (1-10)

    Returns:
        str: Table ID (GUID)

    Raises:
        ValueError: If table number is invalid
    """
    if table_number not in TABLE_MAPPING:
        raise ValueError(
            f"Invalid table number: {table_number}. "
            f"Valid tables: {sorted(TABLE_MAPPING.keys())}"
        )
    return TABLE_MAPPING[table_number]


def get_table_url(table_number):
    """
    Get full URL for a given table number.

    Args:
        table_number: Table number (1-10)

    Returns:
        str: Full table URL
    """
    table_id = get_table_id(table_number)
    return BASE_URL_TEMPLATE.format(table_id=table_id)


def get_all_table_numbers():
    """
    Get list of all available table numbers.

    Returns:
        list: Sorted list of table numbers
    """
    return sorted(TABLE_MAPPING.keys())