# crm_functions.py
import pandas as pd
import os
from groq import Groq
from dotenv import load_dotenv

# -------------------- Initialization --------------------
load_dotenv()

# ✅ Global Groq client (only created once)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ✅ Global cache for CRM data
_cached_df = None


# -------------------- CSV Functions --------------------
def _load_crm_data(csv_file="CRM_data.csv"):
    """Load CRM data once and cache it in memory."""
    global _cached_df
    if _cached_df is None:
        try:
            _cached_df = pd.read_csv(csv_file)
            print(f"[CRM] Loaded {len(_cached_df)} records from {csv_file}")
        except Exception as e:
            print(f"[CRM] Error loading {csv_file}: {e}")
            _cached_df = pd.DataFrame()
    return _cached_df


def get_client_data_from_csv(phone_number, csv_file="CRM_data.csv"):
    """
    Fetch client data from CSV based on phone number.
    """
    try:
        df = _load_crm_data(csv_file)
        clean_phone = str(phone_number).replace(" ", "").replace("-", "").replace("+", "")
        
        for _, row in df.iterrows():
            csv_phone = str(row['Phone']).replace(" ", "").replace("-", "").replace("+", "")
            if clean_phone in csv_phone or csv_phone in clean_phone:
                return {
                    'Name': row['Name'],
                    'Phone': row['Phone'],
                    'Email Id': row['Email Id'],
                    'Product Name': row['Product Name'],
                    'Category': row['Category'],
                    'Price (INR)': row['Price (INR)'],
                    'Purchase Date': row['Purchase Date']
                }
        return None

    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None


def summarize_client_data(client_data):
    """
    Generate AI-powered client summary and product recommendations using Groq.

    Args:
        client_data (dict): Client data from CRM

    Returns:
        str: AI-generated summary and recommendations
    """
    try:
        # Initialize Groq client
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        # Prepare the prompt
        prompt = f"""
        As an AI sales assistant, analyze this customer data and provide insights and product recommendations:

        Customer Information:
        - Name: {client_data['Name']}
        - Phone: {client_data['Phone']}
        - Email: {client_data['Email Id']}
        - Last Purchase: {client_data['Product Name']}
        - Category: {client_data['Category']}
        - Price: ₹{client_data['Price (INR)']}
        - Purchase Date: {client_data['Purchase Date']}

        Please provide:
        1. A brief customer profile summary (1-2 sentences)
        2. Analysis of their purchase history (2 sentences max)
        3. 2-3 specific product recommendations based on their category and price range
           (only product names and prices, clear for a sales rep)

        Keep the response concise, actionable, and human-readable.
        """

        # Generate response using Groq
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert sales assistant that analyzes customer data "
                        "and provides actionable insights and product recommendations "
                        "for sales representatives."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1000
        )

        # Return the AI-generated text
        raw_output = response.choices[0].message.content or ""
        return raw_output.strip()

    except Exception as e:
        return f"Error generating AI summary: {str(e)}. Please check your Groq API key."


def get_related_products(category, price_range, csv_file="CRM_data.csv"):
    """
    Get related products from the same category and price range.
    """
    try:
        df = _load_crm_data(csv_file)
        min_price, max_price = price_range

        related = df[
            (df['Category'].astype(str).str.lower() == str(category).lower()) &
            (df['Price (INR)'] >= min_price) &
            (df['Price (INR)'] <= max_price)
        ]

        return related[['Product Name', 'Price (INR)', 'Category']].to_dict('records')

    except Exception as e:
        print(f"Error getting related products: {e}")
        return []
