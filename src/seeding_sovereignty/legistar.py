"""Module for interacting with the NYC Council Legistar API."""

import os
from typing import List, Dict, Any
import requests
from xml.etree import ElementTree
import logging

BASE_URL = "https://webapi.legistar.com/v1/nyc/matters"
TOTAL_COUNCIL_COUNT = 51
SPONSORS_NEEDED = 26
CHUNK_SIZE = 15


def get_matter_sponsors(matter_id: str) -> List[Dict[str, Any]]:
    """Fetch sponsor information for a given matter ID.

    Args:
        matter_id: The ID of the matter to get sponsors for

    Returns:
        List of sponsor dictionaries, sorted by sequence number
    """
    # Get API token from environment variable
    api_token = os.getenv("NYC_COUNCIL_API_KEY")
    if not api_token:
        raise ValueError("NYC_COUNCIL_API_KEY environment variable not set")

    # Make the API request
    response = requests.get(
        f"{BASE_URL}/{matter_id}/sponsors",
        params={"token": api_token},
        headers={"Accept": "application/xml"},
    )

    if response.status_code != 200:
        logging.error(response.url)
        raise requests.exceptions.HTTPError(
            f"API request failed with status code {response.status_code}"
        )

    # Parse XML response
    root = ElementTree.fromstring(response.content)
    sponsors = []

    # Extract sponsor information
    for sponsor in root.findall(
        ".//{http://schemas.datacontract.org/2004/07/LegistarWebAPI.Models.v1}GranicusMatterSponsor"
    ):
        sponsor_dict = {}
        for child in sponsor:
            # Remove namespace from tag name
            tag = child.tag.split("}")[-1]
            sponsor_dict[tag] = child.text

        sponsors.append(sponsor_dict)

    # Sort sponsors by sequence number
    return sorted(sponsors, key=lambda x: int(x.get("MatterSponsorSequence", 999)))


def extend_matter_info(matter: Dict[str, Any]) -> Dict[str, Any]:
    """Extend matter information with needed information.

    Args:
        matter: Dictionary containing matter information

    Returns:
        Extended matter information with sponsor information
    """
    sponsors = get_matter_sponsors(matter["MatterId"])
    # logging.info([sponsor for sponsor in sponsors])
    prime_sponsor = next(
        (
            sponsor
            for sponsor in sponsors
            if sponsor.get("MatterSponsorSequence") == "0"
        ),
        None,
    )

    matter["PrimeSponsor"] = None

    if prime_sponsor:
        matter["PrimeSponsor"] = prime_sponsor.get("MatterSponsorName")
    else:
        logging.warning(f"No prime sponsor found for {matter['MatterFile']}")

    sponsor_count = len(set([sponsor["MatterSponsorSequence"] for sponsor in sponsors]))
    sponsors_list = set(
        [
            sponsor["MatterSponsorName"]
            for sponsor in sponsors
            if sponsor["MatterSponsorSequence"] != "0"
        ]
    )
    matter["SponsorCount"] = sponsor_count
    matter["Sponsors"] = sponsors_list
    matter["SponsorsRemainingNeeded"] = max(SPONSORS_NEEDED - sponsor_count, 0)

    related_bills = find_related_bills(matter["MatterName"], matter["MatterFile"])
    matter["RelatedBills"] = related_bills

    return matter


def get_matter_info(file_names: List[str]) -> List[Dict[str, Any]]:
    """Fetch matter information from the Legistar API for given file names.

    Args:
        file_names: List of file names to search for
                   (e.g., ["Int 0651-2024", "Int 0005-2024"])

    Returns:
        List of dictionaries containing matter information, sorted to match input order

    Raises:
        ValueError: If not all requested files were found in the API response
    """
    # Get API token from environment variable
    api_token = os.getenv("NYC_COUNCIL_API_KEY")
    if not api_token:
        raise ValueError("NYC_COUNCIL_API_KEY environment variable not set")

    all_matters = []

    # Process files in chunks to avoid API issues
    for i in range(0, len(file_names), CHUNK_SIZE):
        # flake8: noqa: E501
        chunk = file_names[i : i + CHUNK_SIZE]

        # Construct the filter parameter with OR conditions
        filter_parts = [f"MatterFile eq '{file_name}'" for file_name in chunk]
        filter_param = " or ".join(filter_parts)

        # Make the API request
        response = requests.get(
            BASE_URL,
            params={"token": api_token, "$filter": filter_param},
            headers={"Accept": "application/xml"},
        )

        if response.status_code != 200:
            logging.error(response.url)
            raise requests.exceptions.HTTPError(
                f"API request failed with status code {response.status_code}"
            )

        # Parse XML response
        root = ElementTree.fromstring(response.content)

        # Extract matter information
        for matter in root.findall(
            ".//{http://schemas.datacontract.org/2004/07/LegistarWebAPI.Models.v1}GranicusMatter"
        ):
            matter_dict = {}
            for child in matter:
                # Remove namespace from tag name
                tag = child.tag.split("}")[-1]
                matter_dict[tag] = child.text

            all_matters.append(matter_dict)

    # Sort matters to match input file_names order
    file_name_to_matter = {matter["MatterFile"]: matter for matter in all_matters}

    # Check if all requested files were found
    missing_files = [name for name in file_names if name not in file_name_to_matter]
    if missing_files:
        raise ValueError(
            f"Could not find the following files in the API response: {', '.join(missing_files)}"
        )

    sorted_matters = [file_name_to_matter[file_name] for file_name in file_names]

    # Add derived info
    return [extend_matter_info(matter) for matter in sorted_matters]


def print_matter_info(file_names: List[str]) -> None:
    """Print matter information for given file names.

    Args:
        file_names: List of file names to search for
    """
    try:
        matters = get_matter_info(file_names)
        for matter in matters:
            extended_matter = extend_matter_info(matter)
            logging.info(f"Matter Name: {extended_matter.get('MatterName')}")
            logging.info(f"Matter File: {extended_matter.get('MatterFile')}")
            logging.info(f"Matter Summary: {extended_matter.get('MatterEXText5')}")
            logging.info(f"Prime Sponsor: {extended_matter.get('PrimeSponsor')}")
            logging.info(f"Sponsor Count: {extended_matter.get('SponsorCount')}")
            logging.info(f"Sponsors: {extended_matter.get('Sponsors')}")
            logging.info(
                f"Sponsors Remaining Needed: {extended_matter.get('SponsorsRemainingNeeded')}"
            )
            logging.info(f"Related Bills: {extended_matter.get('RelatedBills')}")
            logging.info("-" * 50)
    except Exception as e:
        logging.error(f"Error: {str(e)}")


def find_related_bills(matter_name: str, matter_file: str) -> List[str]:
    """Find related bills from different years that have the same name.

    Args:
        matter_name: The name of the matter to search for related bills

    Returns:
        List of MatterFile strings for related bills (excluding the input matter)

    Raises:
        ValueError: If API key is not set
        requests.exceptions.HTTPError: If API request fails
    """
    # Get API token from environment variable
    api_token = os.getenv("NYC_COUNCIL_API_KEY")
    if not api_token:
        raise ValueError("NYC_COUNCIL_API_KEY environment variable not set")

    # Make the API request with filter for exact name match
    response = requests.get(
        BASE_URL,
        params={"token": api_token, "$filter": f"MatterName eq '{matter_name}'"},
        headers={"Accept": "application/xml"},
    )

    if response.status_code != 200:
        logging.error(response.url)
        raise requests.exceptions.HTTPError(
            f"API request failed with status code {response.status_code}"
        )

    # Parse XML response
    root = ElementTree.fromstring(response.content)
    related_files = []

    # Extract matter information
    for matter in root.findall(
        ".//{http://schemas.datacontract.org/2004/07/LegistarWebAPI.Models.v1}GranicusMatter"
    ):
        matter_dict = {}
        for child in matter:
            # Remove namespace from tag name
            tag = child.tag.split("}")[-1]
            matter_dict[tag] = child.text

        # Add to list if it has a MatterFile
        if "MatterFile" in matter_dict and matter_dict["MatterFile"] != matter_file:
            related_files.append(matter_dict["MatterFile"])

    return related_files


if __name__ == "__main__":
    # Example usage
    test_files = ["Int 0026-2024"]
    # test_files = ["Int 0026-2024", "Int 0005-2024"]
    print_matter_info(test_files)
