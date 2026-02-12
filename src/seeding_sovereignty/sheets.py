import os.path
from typing import List, Dict, Any
import logging

from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError, ReauthFailError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

FILE_COLUMN = "File #"  # main id used in legistar search
NAME_COLUMN = "Name"
PRIME_SPONSOR_COLUMN = "Prime Sponsor"
SUMMARY_COLUMN = "Original Summary"
SPONSORS_COUNT_COLUMN = "# Current Co-Sponsors"
REMAINING_COLUMN = "# Co-Sponsors Needed"
SPONSORS_LIST_COLUMN = "Current Co-Sponsors"
INFO_COLUMN = "Bill History"


def build_sheet_name(year: str | int) -> str:
    return f"Introductions {year}"


def get_credentials() -> Credentials:
    """Get valid user credentials from storage or prompt user to log in.

    Returns:
        Credentials, the obtained credential.
    """
    creds = None
    token_path = os.getenv("GOOGLE_TOKEN_PATH", "token.json")
    credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save the credentials for the next run
                with open(token_path, "w") as token:
                    token.write(creds.to_json())
                return creds
            except RefreshError:
                os.remove(token_path)
            except ReauthFailError:
                os.remove(token_path)

        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
        creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, "w") as token:
            token.write(creds.to_json())
    return creds


def get_column_ranges(service, spreadsheet_id: str, sheet_name: str) -> Dict[str, str]:
    """Get column ranges based on headers in row 2.

    Args:
        service: Google Sheets API service instance
        spreadsheet_id: ID of the Google Sheet
        sheet_name: Name of the sheet to read from

    Returns:
        Dictionary mapping column types to their ranges
    """
    # Get all headers from row 2
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=f"{sheet_name}!2:2")
        .execute()
    )

    headers = result.get("values", [[]])[0]

    column_ranges = {}
    errors = []
    for header in [
        FILE_COLUMN,
        NAME_COLUMN,
        SUMMARY_COLUMN,
        SPONSORS_LIST_COLUMN,
        PRIME_SPONSOR_COLUMN,
        SPONSORS_COUNT_COLUMN,
        REMAINING_COLUMN,
        INFO_COLUMN,
    ]:
        try:
            col_index = headers.index(header)
            col_letter = chr(65 + col_index)  # Convert 0-based index to column letter
            column_ranges[header] = f"{sheet_name}!{col_letter}3:{col_letter}"
        except ValueError:
            errors.append(header)
            column_ranges[header] = None
            continue

    if errors:
        raise ValueError(f"Column header(s) not found in row 3: {errors}")

    logging.debug("column ranges:")
    logging.debug(column_ranges)
    return column_ranges


def collect_filenos(spreadsheet_id: str, year: str | int) -> List[str]:
    """Collect file numbers from the Google Sheet.

    Args:
        spreadsheet_id: ID of the Google Sheet to read from
        sheet_name: Name of the sheet to read from

    Returns:
        List of file numbers
    """
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)

    # Get column ranges
    sheet_name = build_sheet_name(year)
    column_ranges = get_column_ranges(service, spreadsheet_id, sheet_name)
    file_range = column_ranges[FILE_COLUMN]

    if not file_range:
        raise ValueError("Could not find 'File #' column in the sheet")

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = (
        sheet.values().get(spreadsheetId=spreadsheet_id, range=file_range).execute()
    )
    values = result.get("values", [])

    if not values:
        logging.warn("No data found.")
        return []

    # Flatten the list of lists into a list of strings
    return [row[0].strip() for row in values if row]


def upload_file_infos(
    matter_data: List[Dict[str, Any]],
    spreadsheet_id: str,
    year: str,
) -> None:
    """Upload matter information to the Google Sheet.

    Args:
        matter_data: List of matter dictionaries from the Legistar API
        spreadsheet_id: ID of the Google Sheet to update
        sheet_name: Name of the sheet to update
    """
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)
    sheet_name = build_sheet_name(year)

    # Get column ranges
    column_ranges = get_column_ranges(service, spreadsheet_id, sheet_name)

    # Prepare updates for each column
    updates = []

    # Update Name column
    if column_ranges[NAME_COLUMN]:
        name_values = [[matter["MatterName"]] for matter in matter_data]
        updates.append({"range": column_ranges[NAME_COLUMN], "values": name_values})

    # Update Summary column
    if column_ranges[SUMMARY_COLUMN]:
        summary_values = [[matter.get("MatterEXText5", "")] for matter in matter_data]
        updates.append(
            {"range": column_ranges[SUMMARY_COLUMN], "values": summary_values}
        )

    # Update Additional Information column
    if column_ranges[INFO_COLUMN]:
        info_values = [
            ["\n".join(matter.get("RelatedBills", ""))] for matter in matter_data
        ]
        updates.append({"range": column_ranges[INFO_COLUMN], "values": info_values})

    if column_ranges[SPONSORS_COUNT_COLUMN]:
        info_values = [[matter.get("SponsorCount", "")] for matter in matter_data]
        updates.append(
            {"range": column_ranges[SPONSORS_COUNT_COLUMN], "values": info_values}
        )

    if column_ranges[REMAINING_COLUMN]:
        info_values = [
            [matter.get("SponsorsRemainingNeeded", "")] for matter in matter_data
        ]
        updates.append(
            {"range": column_ranges[REMAINING_COLUMN], "values": info_values}
        )

    if column_ranges[PRIME_SPONSOR_COLUMN]:
        info_values = [[matter.get("PrimeSponsor", "")] for matter in matter_data]
        updates.append(
            {"range": column_ranges[PRIME_SPONSOR_COLUMN], "values": info_values}
        )

    if column_ranges[SPONSORS_LIST_COLUMN]:
        info_values = [
            ["\n".join(matter.get("Sponsors", ""))] for matter in matter_data
        ]
        updates.append(
            {"range": column_ranges[SPONSORS_LIST_COLUMN], "values": info_values}
        )

    # Batch update all columns
    if updates:
        body = {"valueInputOption": "RAW", "data": updates}

        result = (
            service.spreadsheets()
            .values()
            .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
            .execute()
        )

        logging.debug(
            f"Successfully updated GSheet: {result.get('totalUpdatedCells')} cells across {len(updates)} columns."
        )


if __name__ == "__main__":
    collect_filenos()
