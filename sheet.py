# sheet.py
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re

HEADERS = ["Timestamp", "Customer Name", "Full Transcript", "Overall Sentiment", "Overall Customer Summary"]

def get_sheet(sheet_name="Speech_Analysis", creds_file="credentials.json"):
    """
    Connect to Google Sheet and ensure headers exist.
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).sheet1
    ensure_headers(sheet)
    return sheet

def ensure_headers(sheet):
    """
    Ensure the sheet has proper headers.
    """
    all_values = sheet.get_all_values()
    if not all_values or all_values[0] != HEADERS:
        sheet.insert_row(HEADERS, 1, value_input_option='RAW')

def save_post_call_summary(sheet, customer_name, transcript, sentiment, summary):
    """
    Append the post-call summary row to Google Sheet.
    """
    timestamp = datetime.now().isoformat()
    row = [timestamp, customer_name, transcript, sentiment, summary]
    sheet.append_row(row, value_input_option='RAW')

def extract_customer_name(transcript):
    """
    Extract customer name from transcript using common patterns.
    """
    patterns = [
        r'my name is ([A-Za-z\s]+)',
        r'i am ([A-Za-z\s]+)',
        r'this is ([A-Za-z\s]+)',
        r'call me ([A-Za-z\s]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, transcript, re.IGNORECASE)
        if match:
            return match.group(1).strip().title()
    return "Unknown Customer"
