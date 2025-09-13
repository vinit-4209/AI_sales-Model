from datetime import datetime
import csv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

HEADERS = ["Lead ID", "Name", "Pain Points", "Deal Stage", "Product Name", "Category", "Price (INR)", "Recommendation", "Next Step"]


def get_sheet(sheet_name="Speech_Analysis", creds_file="credentials.json"):
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).sheet1
    return sheet


def ensure_headers(sheet):
    """Check if sheet is empty and add headers if needed"""
    try:
        # Get all values from the sheet
        all_values = sheet.get_all_values()
        
        # If sheet is empty (no rows), add headers
        if not all_values:
            sheet.append_row(HEADERS, value_input_option='RAW')
            print("Headers added to Google Sheet.")
        else:
            # Check if first row contains headers
            first_row = all_values[0] if all_values else []
            if first_row != HEADERS:
                # If first row doesn't match headers, insert headers at the top
                sheet.insert_row(HEADERS, 1, value_input_option='RAW')
                print("Headers inserted at the top of Google Sheet.")
    except Exception as e:
        print(f"Error ensuring headers: {e}")


def create_crm_lead_from_call(sheet, transcript, sentiment, customer_summary, intent, suggestion):
    """Create a proper CRM lead from call data with AI analysis"""
    ensure_headers(sheet)
    
    # Generate unique lead ID
    timestamp = datetime.now()
    lead_id = f"L{timestamp.strftime('%Y%m%d%H%M%S')}"
    
    # Extract customer name from transcript (simple pattern matching)
    import re
    name_patterns = [
        r'my name is ([A-Za-z\s]+)',
        r'i am ([A-Za-z\s]+)',
        r'this is ([A-Za-z\s]+)',
        r'call me ([A-Za-z\s]+)'
    ]
    
    customer_name = "Unknown Customer"
    for pattern in name_patterns:
        match = re.search(pattern, transcript, re.IGNORECASE)
        if match:
            customer_name = match.group(1).strip().title()
            break
    
    # Determine pain points from sentiment and intent
    pain_points = f"Customer expressed {sentiment} sentiment. Intent: {intent}. Summary: {customer_summary}"
    
    # Determine deal stage based on sentiment and intent
    if sentiment == "positive" and "buy" in intent.lower():
        deal_stage = "Negotiation"
    elif sentiment == "positive":
        deal_stage = "Qualification"
    elif sentiment == "negative":
        deal_stage = "Proposal"
    else:
        deal_stage = "Qualification"
    
    # AI-powered product recommendation based on intent and sentiment
    product_name, category, price, recommendation = get_ai_recommendation(intent, sentiment, customer_summary)
    
    # Determine next step based on deal stage and sentiment
    next_step = get_next_step(deal_stage, sentiment, intent)
    
    # Create the lead
    row = [lead_id, customer_name, pain_points, deal_stage, product_name, category, price, recommendation, next_step]
    
    try:
        sheet.append_row(row, value_input_option='RAW')
        print(f"CRM lead {lead_id} created successfully for {customer_name}")
        return lead_id
    except Exception as e:
        print(f"Error creating CRM lead: {e}")
        return None


def load_product_database(csv_file="CRM_data - Sheet1.csv"):
    """Load product database from CSV file for intelligent recommendations"""
    products = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                products.append({
                    'name': row['Product Name'],
                    'category': row['Category'],
                    'price': row['Price (INR)'],
                    'recommendation': row['Recommendation'],
                    'pain_points': row['Pain Points'].lower(),
                    'keywords': extract_keywords(row['Pain Points'] + " " + row['Product Name'])
                })
        print(f"Loaded {len(products)} products from database")
        return products
    except Exception as e:
        print(f"Error loading product database: {e}")
        return []


def extract_keywords(text):
    """Extract relevant keywords from text for matching"""
    import re
    # Convert to lowercase and extract words
    words = re.findall(r'\b\w+\b', text.lower())
    # Filter out common words and keep meaningful ones
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
    keywords = [word for word in words if len(word) > 2 and word not in stop_words]
    return keywords


def get_ai_recommendation(intent, sentiment, summary):
    """AI-powered product recommendation based on call analysis using CSV database"""
    # Load product database
    products = load_product_database()
    if not products:
        # Fallback to basic recommendation if database not available
        return get_fallback_recommendation(intent, sentiment, summary)
    
    # Combine all text for analysis
    analysis_text = f"{intent} {sentiment} {summary}".lower()
    
    # Score each product based on keyword matching
    scored_products = []
    for product in products:
        score = calculate_relevance_score(analysis_text, product)
        scored_products.append((score, product))
    
    # Sort by score (highest first)
    scored_products.sort(key=lambda x: x[0], reverse=True)
    
    # Return the best match
    if scored_products and scored_products[0][0] > 0:
        best_product = scored_products[0][1]
        return best_product['name'], best_product['category'], best_product['price'], best_product['recommendation']
    else:
        # If no good match, return a random product from the database
        import random
        random_product = random.choice(products)
        return random_product['name'], random_product['category'], random_product['price'], random_product['recommendation']


def calculate_relevance_score(analysis_text, product):
    """Calculate how relevant a product is to the analysis text"""
    score = 0
    
    # Direct keyword matching
    for keyword in product['keywords']:
        if keyword in analysis_text:
            score += 2
    
    # Pain points matching
    pain_points_lower = product['pain_points']
    for word in analysis_text.split():
        if word in pain_points_lower:
            score += 1
    
    # Category-based scoring
    category_keywords = {
        'Ergonomic Accessory': ['back', 'pain', 'sitting', 'posture', 'comfort', 'ergonomic', 'chair', 'desk', 'overheating', 'cooling', 'glasses', 'partition'],
        'Headset': ['noise', 'audio', 'call', 'meeting', 'sound', 'headset', 'speaker', 'conference'],
        'Laptop': ['laptop', 'computer', 'slow', 'performance', 'work', 'computing', 'basic'],
        'Smart Device': ['security', 'smart', 'device', 'automation', 'lock', 'wifi', 'network', 'power', 'ups', 'team', 'collaboration', 'starter', 'docking', 'adapter', 'vpn']
    }
    
    product_category = product['category']
    if product_category in category_keywords:
        for keyword in category_keywords[product_category]:
            if keyword in analysis_text:
                score += 1.5
    
    return score


def get_fallback_recommendation(intent, sentiment, summary):
    """Fallback recommendation when CSV database is not available"""
    intent_lower = intent.lower()
    
    # Basic fallback recommendations
    if any(word in intent_lower for word in ['back', 'pain', 'sitting', 'posture', 'comfort']):
        return "Ergonomic Chair X", "Ergonomic Accessory", "12000", "Supports posture and reduces back pain"
    elif any(word in intent_lower for word in ['noise', 'audio', 'call', 'meeting', 'sound']):
        return "Bose Headset 700", "Headset", "15000", "Noise cancellation boosts focus and productivity"
    elif any(word in intent_lower for word in ['laptop', 'computer', 'slow', 'performance', 'work']):
        return "Laptop Pro 15", "Laptop", "65000", "High-performance laptop for faster computing"
    elif any(word in intent_lower for word in ['security', 'smart', 'device', 'automation']):
        return "Smart Lock Plus", "Smart Device", "8000", "Advanced locking for office security"
    else:
        return "Team Hub", "Smart Device", "15000", "Enhances communication and coordination"


def get_next_step(deal_stage, sentiment, intent):
    """Determine next step based on deal stage and analysis"""
    if deal_stage == "Qualification":
        return "Send product brochure"
    elif deal_stage == "Negotiation":
        return "Schedule demo call"
    elif deal_stage == "Proposal":
        return "Offer bundle discounts"
    else:
        return "Schedule follow-up call"
