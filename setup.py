"""
Setup script for building Seeding Sovereignty as a macOS app using py2app.
"""

from setuptools import setup

APP = ["main.py"]
DATA_FILES = [
    "credentials.json",  # Include the OAuth client credentials file
    "config.json",  # Include the configuration file
]
OPTIONS = {
    "argv_emulation": True,  # Enable drag-and-drop support
    "iconfile": None,  # You can add an .icns file here later
    "plist": {
        "CFBundleName": "Seeding Sovereignty",
        "CFBundleDisplayName": "Seeding Sovereignty",
        "CFBundleIdentifier": "com.yourname.seedingsovereignty",
        "CFBundleVersion": "0.1.0",
        "CFBundleShortVersionString": "0.1.0",
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "10.13",  # macOS High Sierra
    },
    "packages": [
        "seeding_sovereignty",
        "googleapiclient",
        "google_auth_oauthlib",
        "google_auth_httplib2",
        "requests",
        "dotenv",
    ],
    "includes": [
        "google.auth",
        "google.auth.transport",
        "google.oauth2",
        "googleapiclient.discovery",
        "googleapiclient.errors",
    ],
    "excludes": [
        "matplotlib",  # Exclude unused libraries to reduce size
        "numpy",
        "scipy",
    ],
    "resources": [
        "credentials.json",  # Also include in resources to ensure they're in the right place
        "config.json",
    ],
    "optimize": 2,  # Optimize Python bytecode
}

setup(
    name="Seeding Sovereignty",
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
    python_requires=">=3.9",
)
