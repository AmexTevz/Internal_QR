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
    10: "38A31859-CA10-452C-BF40-ED361D7F6749",
    11: "5CF63A35-1900-4F75-B689-73AC850A08FA",
    12: "CD1CC80A-E6D0-4A59-A153-9ABDA682C336",
    13: "5904EDF5-C79E-410C-A4CD-644F7A335167",
    14: "BD551B32-C097-4CE4-AB62-0D2FECC2C2B0",
    15: "853BE38D-46A3-4B42-9F0A-8D7E521D449E",
    16: "457CC58B-EAD9-4B89-BE23-B02CB39CFE23",
    17: "CA0EF643-B1F6-40CB-9265-973ED58D3DF8",
    18: "B4D4AEB6-DB90-49B5-A136-67F659311125",
    19: "E264FC25-1A82-4209-8118-CA25A1BBD0BB",
    20: "8690275A-3D98-4228-A4D4-3C8A094EF9EC",
    21: "F28D7143-84C1-4971-8C31-C5897D91BBBB",
    22: "84895675-44A3-4EE4-A453-0D33C64104FF",
    23: "B2D3FB51-5573-48E6-8670-E87F093E1F2A",
    24: "0DACEE34-E39B-4339-98AC-6981C9DCA247",
    25: "F1CA441A-49B9-4DAF-97F0-8389EAF7C2CD"
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