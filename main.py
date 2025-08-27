#!/usr/bin/env python3
"""Entry point for the Seeding Sovereignty app."""

import sys
import os
import logging
import json
from datetime import datetime


def setup_config():
    """Set up configuration for the app."""
    if getattr(sys, "frozen", False):
        # We're running in a bundle
        bundle_dir = os.path.dirname(sys.executable)
        resources_dir = os.path.join(bundle_dir, "..", "Resources")
        config_file = os.path.join(resources_dir, "config.json")
        os.environ["GOOGLE_CREDENTIALS_PATH"] = os.path.join(
            resources_dir, "credentials.json"
        )
        os.environ["GOOGLE_TOKEN_PATH"] = os.path.join(
            bundle_dir, "token.json"
        )  # Keep token outside bundle
    else:
        # We're running in a normal Python environment
        bundle_dir = os.path.dirname(os.path.abspath(__file__))
        config_file = os.path.join(bundle_dir, "config.json")
        os.environ["GOOGLE_CREDENTIALS_PATH"] = os.path.join(
            bundle_dir, "credentials.json"
        )
        os.environ["GOOGLE_TOKEN_PATH"] = os.path.join(bundle_dir, "token.json")

    # Load config and set environment variables
    with open(config_file) as f:
        config = json.load(f)
        for key, value in config.items():
            os.environ[key] = value


# Set up configuration before anything else
setup_config()


def setup_logging():
    """Set up logging to write to a file next to the app bundle."""
    # Get the app's directory
    if getattr(sys, "frozen", False):
        # We're running in a bundle
        # Get the directory containing the .app bundle
        app_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))
        )
    else:
        # We're running in a normal Python environment
        app_dir = os.path.dirname(os.path.abspath(__file__))

    # Create logs directory next to the app
    logs_dir = os.path.join(app_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # Create log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"seeding_sovereignty_{timestamp}.log")

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),  # Also print to console
        ],
    )
    return log_file


# Set up logging first, before any imports
log_file = setup_logging()
logging.info("Starting Seeding Sovereignty...")
logging.info(f"Logs will be written to: {log_file}")

# Add the package directory to the path so we can import our modules
package_dir = os.path.join(os.path.dirname(__file__), "src")
sys.path.insert(0, package_dir)

# Now we can import our modules
try:
    from seeding_sovereignty.sheets import collect_filenos, upload_file_infos
    from seeding_sovereignty.legistar import get_matter_info
except ImportError as e:
    logging.error(f"Error importing modules: {e}")
    logging.error("Make sure you're running this from the project root directory.")
    sys.exit(1)


def main() -> None:
    """Main function to update Google Sheet with Legistar data."""
    try:
        setup_logging()

        # Get file names from Google Sheet
        file_names = collect_filenos()
        if not file_names:
            logging.error("No file names found in the sheet.")
            return

        logging.info(f"Found {len(file_names)} file names in the sheet.")
        logging.info(f"First few files: {', '.join(file_names[:5])} ...")

        # Get matter information from Legistar API
        matter_data = get_matter_info(file_names)
        if not matter_data:
            logging.error("No matter data found from Legistar API.")
            return

        logging.info("Uploading data to Google Sheets...")
        # Upload matter names back to Google Sheet
        upload_file_infos(matter_data)
        logging.info("Done!")
        logging.info("You can close this window now.")
    except Exception as e:
        logging.error(f"Error in main function: {e}")


if __name__ == "__main__":
    main()
