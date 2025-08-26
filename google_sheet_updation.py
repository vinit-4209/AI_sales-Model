import gspread
from google.oauth2.service_account import Credentials

# Define the scope (permissions)
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Authenticate using credentials.json
creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
client = gspread.authorize(creds)

# Open Google Sheet by name (make sure it's created in your Google Drive)
sheet = client.open("Speech_Analysis").sheet1

# Example: add a row
sheet.append_row(["Testing connection", "It works!"])
print("Data sent to Google Sheets successfully.")
