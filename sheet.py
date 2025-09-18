from datetime import datetime
import csv
import gspread
import pandas as pd
import re
from oauth2client.service_account import ServiceAccountCredentials

HEADERS = ["Lead ID", "Name", "Needs", "Product Name", "Category", "Price (INR)", "Recommendation", "Next Step"]

def get_sheet(sheet_name="Speech_Analysis", creds_file="credentials.json"):
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client = gspread.authorize(creds)
    return client.open(sheet_name).sheet1

def ensure_headers(sheet):
    all_values = sheet.get_all_values()
    if not all_values or all_values[0] != HEADERS:
        sheet.insert_row(HEADERS, 1, value_input_option='RAW')

def create_crm_lead_from_call(sheet, transcript, sentiment, customer_summary, intent, suggestion):
    ensure_headers(sheet)
    timestamp = datetime.now()
    lead_id = f"L{timestamp.strftime('%Y%m%d%H%M%S')}"
    customer_name = extract_customer_name(transcript)
    needs = f"Summary: {customer_summary}"
    product_name, category, price, recommendation = get_ai_recommendation(intent, sentiment, customer_summary)
    next_step = get_next_step(sentiment, intent)
    row = [lead_id, customer_name, needs, product_name, category, price, recommendation, next_step]
    sheet.append_row(row, value_input_option='RAW')

def extract_customer_name(transcript):
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

def load_product_database():
    df1 = pd.read_csv('CRM_data - Sheet1.csv').fillna('')
    df2 = pd.read_csv('CRM_data - Sheet2.csv').fillna('')
    df1['keywords'] = df1.apply(lambda row: extract_keywords(row['Needs'] + " " + row['Product Name']), axis=1)
    return df1, df2

def extract_keywords(text):
    words = re.findall(r'\b\w+\b', text.lower())
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
        'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
    }
    return [word for word in words if len(word) > 2 and word not in stop_words]

def get_ai_recommendation(intent, sentiment, summary):
    df_products, df_history = load_product_database()
    analysis_text = f"{intent} {sentiment} {summary}".lower()
    scored_products = []
    merged = pd.merge(df_products, df_history, how='left', left_on='Product Name', right_on='Product Name')
    merged = merged.fillna('')
    for _, product in merged.iterrows():
        score = calculate_relevance_score(analysis_text, product)
        scored_products.append((score, product))
    scored_products.sort(key=lambda x: x[0], reverse=True)
    best = scored_products[0][1] if scored_products and scored_products[0][0] > 0 else df_products.sample(1).iloc[0]
    return best['Product Name'], best['Category'], str(best['Price (INR)']), best.get('Recommendation', 'Recommended product')

def calculate_relevance_score(analysis_text, product):
    score = 0
    for keyword in product.get('keywords', []):
        if keyword in analysis_text:
            score += 2
    pain_points = product.get('Needs', '').lower()
    for word in analysis_text.split():
        if word in pain_points:
            score += 1
    category_keywords = {
        'Ergonomic Accessory': ['back', 'pain', 'sitting', 'posture', 'comfort', 'ergonomic', 'chair', 'desk', 'overheating', 'cooling', 'glasses', 'partition'],
        'Headset': ['noise', 'audio', 'call', 'meeting', 'sound', 'headset', 'speaker', 'conference'],
        'Laptop': ['laptop', 'computer', 'slow', 'performance', 'work', 'computing', 'basic'],
        'Smart Device': ['security', 'smart', 'device', 'automation', 'lock', 'wifi', 'network', 'power', 'ups', 'team', 'collaboration', 'starter', 'docking', 'adapter', 'vpn']
    }
    cat = product.get('Category', '')
    if cat in category_keywords:
        for keyword in category_keywords[cat]:
            if keyword in analysis_text:
                score += 1.5
    return score

def get_next_step(sentiment, intent):
    if sentiment == "positive" and "buy" in intent.lower():
        return "Schedule demo call"
    if sentiment == "positive":
        return "Send product brochure"
    if sentiment == "negative":
        return "Offer bundle discounts"
    return "Schedule follow-up call"
