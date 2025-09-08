
# sheet_utils.py

import csv
import os
from datetime import datetime
import pandas as pd

HEADERS = ["Timestamp", "Transcript", "Sentiment", "Customer Summary", "Intent", "Suggestion"]
CSV_FILE = "call_log.csv"


# ----------------- Local CSV Helpers -----------------
def append_to_csv(timestamp, transcript, sentiment, customer_summary, intent, suggestion):
    """Append a row to local CSV log file."""
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(HEADERS)  # add headers if file is new
        writer.writerow([timestamp, transcript, sentiment, customer_summary, intent, suggestion])


def read_csv():
    """Read call history from local CSV file into DataFrame."""
    if not os.path.isfile(CSV_FILE):
        return pd.DataFrame(columns=HEADERS)
    return pd.read_csv(CSV_FILE)


# ----------------- (Optional) Google Sheet Helpers -----------------
# Keep these only if you still want export to Sheets
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_sheet(sheet_name="Speech_Analysis", creds_file="credentials.json"):
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).sheet1
    return sheet

def append_to_sheet(sheet, timestamp, transcript, sentiment, customer_summary, intent, suggestion):
    """Append row to Google Sheet (if needed)."""
    row = [timestamp, transcript, sentiment, customer_summary, intent, suggestion]
    try:
        sheet.append_row(row, value_input_option='RAW')
        print("Data appended to Google Sheet successfully.")
    except Exception as e:
        print(f"Error appending to sheet: {e}")











# import gspread
# from oauth2client.service_account import ServiceAccountCredentials
# import pandas as pd

# HEADERS = ["Timestamp", "Transcript", "Sentiment", "Customer Summary", "Intent", "Suggestion"]

# def get_sheet(sheet_name="Speech_Analysis", creds_file="credentials.json"):
#     scope = ["https://spreadsheets.google.com/feeds",
#              "https://www.googleapis.com/auth/drive"]
#     creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
#     client = gspread.authorize(creds)
#     sheet = client.open(sheet_name).sheet1

#     # Ensure headers exist
#     values = sheet.get_all_values()
#     if not values:
#         sheet.insert_row(HEADERS, index=1)
#     else:
#         first_row = [c.strip() for c in values[0]]
#         if first_row != HEADERS:
#             # Overwrite headers if needed (keeps existing data below)
#             sheet.delete_rows(1)
#             sheet.insert_row(HEADERS, index=1)

#     return sheet

# def append_to_sheet(sheet, timestamp, transcript, sentiment, customer_summary, intent, suggestion):
#     row = [timestamp, transcript, sentiment, customer_summary, intent, suggestion]
#     try:
#         sheet.append_row(row, value_input_option='RAW')
#         print("Data appended to sheet successfully.")
#     except Exception as e:
#         print(f"Error appending to sheet: {e}")

# def read_sheet_as_df(sheet):
#     """Returns a pandas DataFrame with proper columns (or empty df)."""
#     try:
#         records = sheet.get_all_records()
#         if not records:
#             return pd.DataFrame(columns=HEADERS)
#         df = pd.DataFrame(records)
#         # enforce columns order
#         for col in HEADERS:
#             if col not in df.columns:
#                 df[col] = ""
#         return df[HEADERS]
#     except Exception as e:
#         print(f"Error reading sheet: {e}")
#         return pd.DataFrame(columns=HEADERS)









# import gspread
# from oauth2client.service_account import ServiceAccountCredentials

# def get_sheet(sheet_name="Speech_Analysis", creds_file="credentials.json"):
#     scope = ["https://spreadsheets.google.com/feeds",
#              "https://www.googleapis.com/auth/drive"]
#     creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
#     client = gspread.authorize(creds)
#     sheet = client.open(sheet_name).sheet1

#     values = sheet.get_all_values()
#     if not values or all(cell.strip() == "" for cell in values[0]):
#         headers = ["Time", "Transcript", "Sentiment", "Customer Summary", "Intent", "Suggested Action"]
#         try:
#             sheet.insert_row(headers, index=1)  
#             print("Headers added to the sheet.")
#         except Exception as e:
#             print(f"Error adding headers: {e}")

#     return sheet
# # def append_to_sheet(sheet, text, sentiment, summary):
# #     sheet.append_row([text, sentiment, summary])


# def append_to_sheet(sheet, timestamp, transcript, sentiment, customer_summary, intent=None, suggested_action=None):
#     if intent is None:
#         intent = "N/A"
#     # if intent_summary is None:
#     #     intent_summary = "N/A"

#     row = [timestamp, transcript, sentiment, customer_summary, intent,  suggested_action or "N/A"]
#     try:
#         sheet.append_row(row, value_input_option='RAW')  
#         print("Data appended to sheet successfully.")
#     except Exception as e:
#         print(f"Error appending to sheet: {e}")