import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_sheet(sheet_name="Speech_Analysis", creds_file="credentials.json"):
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client = gspread.authorize(creds)
    return client.open(sheet_name).sheet1

def append_to_sheet(sheet, text, sentiment, summary):
    sheet.append_row([text, sentiment, summary])