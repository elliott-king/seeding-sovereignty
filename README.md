# Overview
Welcome to the Seeding Sovereignty (Google) Sheets Script! This script will update the "NYC Climate Justice Bills (Seeding Sovereignty)" google sheet, in the "Introductions 2024" tab. If you are looking to replicate this outside of NYC, feel free to adapt this code to your local government API.

> [!NOTE]  
> Most names used are case-sensitive, and expect the exact letters that I put in quotes.

## What it does:
Using the name of each bill you want, this will fetch information from the City Council Legistar API, and fill it into the corresponding row. If you want to show information about a bill, just include the bill name in the correct column. Upon running this, certain columns in the sheet will be automatically filled out. Note that all columns must exist in the sheet if you want this to work. You can, however, "hide" the column in Google sheets.

<img width="538" height="370" alt="Screenshot 2025-08-21 at 9 58 57 PM" src="https://github.com/user-attachments/assets/edce46d7-9525-4f10-8855-53f816c7a5d9" />

**Source column**
"File #": the values in this column must be the file number of the bill (eg, "Int 0107-2024"). This is our source of truth, this is what I use to fetch information. If you want to get more bills, add their file number to this column.

**Target columns**: these columns will be updated with data when this program is run, and will overwrite all pre-existing data.
- "Name": the bill's name. These can get pretty wordy.
- "Prime Sponsor": the main council sponsor.
- "Original Summary": the official summary of the bill. I use the term "original" here to indicate that this is auto-generated. If you want to write your own summary, make a different column.
- "# Current Co-Sponsors": the number of city councilmembers sponsoring the bill. This is calculated by the program, so let me know if there is a bug.
- "# Co-Sponsors Needed": this is just 26 - # Current Co-Sponsors
- "Current Co-Sponsors": the names of the councilmembers sponsoring this bill. This is copied from the legistar & may have weird values like "(by request of the Brooklyn Borough President)" or something that was in the original data
- "Bill History": this title is slightly misleading. This should be a list of bills from different years with the same name. If a bill rolls over to a new session, there doesn't seem to be a direct database relationship between the two versions of the bill, although they usually have the same name. You may want to double-check the contents here, and some bill duplicates may be omitted. If you find a newer bill, and want to add it to the GSheet, just copy the file number & add it to the "File #" column!

## How to run it
The provided MacOS app should run with a click.
1. Double-click the application
   1. If Macos prevents it from running, you may have to right-click & run it using the menu that opens
2. No window will show, but you should see the app in the Mac dock at the bottom of your screen
3. You may be prompted to login to Google.
   1. Make sure you use the email address that you email me with.
   2. If it says "continue" vs "back to safety", be unsafe & hit "continue"
4. Wait for the app to leave the dock, then check your Google sheet.

## <to organize: organization setup>
- gcloud project
  - google auth platform
    - setup
    - create client
      - desktop app
    - oauth consent & branding
    - data access: scopes
      - https://www.googleapis.com/auth/drive.file
  - api: oauth consent screen
    - audience - add test users (since we are external)
  - sheets api
    - credentials (app data)
    - service account
      - role: editor
      - access to other users?
  - generate API key (?)
    - needed for the upload
    - apis & services -> credentials -> create api key


values
- [x] Remaining Sponsors Needed
  - current - 26 (needs 26 sponsors)
- [x] cosponsors (names) ("cm sponsors")
  - [x] # needed
  - [x] # not sponsoring
  - [ ] not sponsoring name
- [KINDA] bill history
  - example: Int 0005-2024 has one from 2023
  - possible (?) is this searchable?
    - by same name exactly?
    - by some sort of linking ID?
- [x] summary: from api
  - comments on summary
- [x] prime sponsor
- [ ] additional information (?)
- [ ] What are the edited/reference columns?


# Actions
chilli action (within app), per bill, per cc member
- only need to edit dist number & name of rep
- possible Chilli support here
- [no] do they have API?
- [no] Ask Christian if OSS (so I can change myself)

## follow-up with py2app app
- how to replicate
- NOTE: right click to open if admin issues

## deliverable asks from SS
- pre-emptive questions: what do you expect to get?


# Seeding Sovereignty

This is a simple python app that updates the Seeding Sovereignty bill spreadsheet based on NYC City Council legistar-API data. You can also build it into a MacOS app so it can be run with a single click.

## Setup

1. Install Poetry if you haven't already:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Activate the virtual environment:
   ```bash
   poetry shell
   ```

4. Legistar API
  The New York City Council uses Legistar for its API.
   1. Get a token [here](https://council.nyc.gov/legislation/api/)
   2. The API reference is [here](https://webapi.legistar.com/Home/Examples)

5. Set Up Google Sheets & Google Cloud Console
   1. (walk through cloud console)
   2. need to change the SAMPLE_SPREADSHEET_ID & SHEET_NAME
6. Building to Macos app
   - note about right-click
   - log location

## Running
run with `poetry run python -m main`

### With py2app
This script can be built into a Macos-native binary so it can be run with a single click:
```bash
;rm -rf dist/ build/ && poetry run python setup.py py2app && cd dist && zip -r "Seeding Sovereignty.zip" "Seeding Sovereignty.app"
```

## Project Structure

```
seeding-sovereignty/
├── src/
│   └── seeding_sovereignty/
│       ├── __init__.py
│       ├── sheets.py        # Google Sheets integration
│       └── legistar.py      # NYC Council Legistar API client
├── credentials.json         # Google OAuth credentials - add these
├── config.json             # App configuration - secrets passed to the
├── setup.py                # macOS app build config
├── pyproject.toml          # Project dependencies and config
└── README.md              # Project documentation
```

### config.json
TODO:

### credentials.json

## License

This project is licensed under the terms of the LICENSE file. 
