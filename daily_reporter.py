"""
OLX Daily Price Reporter
=========================
This script automates the scraping, filtering, and reporting of targeted iPhone listings in Lahore.
It runs daily, filters out accessories, targets specific models with strict price ranges,
isolates ads posted within the last 24 hours, fetches detailed descriptions, compiles a multi-sheet Excel report,
and emails it using smtplib.

---
HOW TO SCHEDULE THIS SCRIPT TO RUN DAILY AT 12:00 AM:
-----------------------------------------------------

Windows Task Scheduler:
1. Open "Task Scheduler" (search for it in the Start menu).
2. Click "Create Basic Task..." in the Actions pane on the right.
3. Configure the General settings:
   - Name: OLX Daily Price Reporter
   - Description: Scrapes iPhone pricing from OLX Pakistan, generates an Excel report, and emails it.
4. Trigger:
   - Select "Daily".
   - Start Date: Today, Time: 12:00 AM (00:00:00).
   - Recur every: 1 days.
5. Action:
   - Select "Start a program".
6. Start a Program:
   - Program/script: Enter the path to your Python executable (e.g. `py` or `C:\\Users\\<User>\\AppData\\Local\\Programs\\Python\\Python311\\python.exe`).
   - Add arguments (optional): Enter the absolute path to this script (e.g. `d:\\Ahsan's Project\\daily_reporter.py`).
   - Start in (optional): Enter the directory of this script (e.g. `d:\\Ahsan's Project`).
7. Click Finish. Ensure your computer is powered on or set the task to "Run whether user is logged on or not" in the task properties (requires administrator credentials).

Linux / macOS Cron Job:
1. Open a terminal.
2. Edit your cron table:
   `crontab -e`
3. Add the following line at the bottom to execute the script every day at midnight (12:00 AM):
   `0 0 * * * /usr/bin/python3 "/absolute/path/to/daily_reporter.py" >> "/absolute/path/to/daily_reporter.log" 2>&1`
4. Save and exit the editor.
"""

import os
import re
import time
import random
import smtplib
import logging
from email.message import EmailMessage
from bs4 import BeautifulSoup
import requests
import pandas as pd

# --- LOGGING CONFIGURATION ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("daily_reporter.log", encoding='utf-8')
    ]
)

# --- EMAIL & SMTP CONFIGURATION ---
# Replace these values or set them as Environment Variables
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "sender_email@gmail.com")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "your_app_password")  # Use an App Password, not a normal password!
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", "recipient_email@gmail.com")

# --- TARGET MODELS & STRICT CONFIGURATION ---
TARGETS = {
    "iPhone 14 Pro Max PTA": {"min": 180000, "max": 350000},
    "iPhone 15 Pro Max PTA": {"min": 250000, "max": 450000},
    "iPhone 15 Pro Max Non-PTA": {"min": 150000, "max": 320000},
    "iPhone 16 Pro Max Non-PTA": {"min": 200000, "max": 420000},
    "iPhone 17 Pro Non-PTA": {"min": 220000, "max": 450000},
    "iPhone 17 Pro Max Non-PTA": {"min": 260000, "max": 550000}
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
]

def clean_price(price_str):
    if not price_str:
        return None
    price_clean = price_str.lower().replace("rs", "").replace(",", "").strip()
    try:
        if "lac" in price_clean or "lakh" in price_clean:
            num_part = re.search(r'[\d\.]+', price_clean)
            if num_part:
                return float(float(num_part.group()) * 100000)
        elif "crore" in price_clean:
            num_part = re.search(r'[\d\.]+', price_clean)
            if num_part:
                return float(float(num_part.group()) * 10000000)
        else:
            num_part = re.search(r'\d+', price_clean)
            if num_part:
                return float(num_part.group())
    except Exception as e:
        logging.warning(f"Error parsing price '{price_str}': {e}")
    return None


def is_last_24_hours(date_str):
    """
    Returns True if listing date indicates it was posted in the last 24 hours.
    OLX uses strings like "2 hours ago", "5 mins ago", "1 hour ago", "moments ago", "now".
    Older ads show "1 day ago", "3 days ago", "1 week ago", "2 weeks ago", etc.
    """
    if not date_str:
        return False
    date_lower = date_str.lower()
    
    # Sub-day indicators on OLX Pakistan
    indicators = ["hour", "minute", "min", "second", "now"]
    
    # Exclude day, week, month, year indicators
    exclusions = ["day", "week", "month", "year"]
    
    if any(ind in date_lower for ind in indicators) and not any(exc in date_lower for exc in exclusions):
        return True
    return False


def fetch_olx_html(keyword):
    formatted_keyword = keyword.strip().lower().replace(" ", "-")
    url = f"https://www.olx.com.pk/items/q-{formatted_keyword}"
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }
    
    try:
        logging.info(f"Scraping listings for query: '{keyword}'...")
        res = requests.get(url, headers=headers, timeout=12)
        if res.status_code == 200:
            return res.text
        else:
            logging.error(f"HTTP error {res.status_code} fetching listings for '{keyword}'.")
            return None
    except Exception as e:
        logging.error(f"Network error requesting '{keyword}': {e}")
        return None


def fetch_ad_description(link):
    """
    Parses listing details page to extract full listing description.
    """
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }
    try:
        res = requests.get(link, headers=headers, timeout=8)
        if res.status_code == 200:
            soup = BeautifulSoup(res.content, 'html.parser')
            # Selector: aria-label="Description" is semantic and class independent
            desc_div = soup.find(attrs={"aria-label": "Description"})
            if desc_div:
                desc_text = desc_div.get_text().strip()
                if desc_text.lower().startswith("description"):
                    desc_text = desc_text[len("description"):].strip()
                return desc_text
    except Exception as e:
        logging.warning(f"Error fetching description for {link}: {e}")
    return "N/A"


def parse_olx_listings(html_content, target_name):
    if not html_content:
        return []
        
    soup = BeautifulSoup(html_content, 'html.parser')
    articles = soup.find_all('article')
    
    parsed_items = []
    min_limit = TARGETS[target_name]["min"]
    max_limit = TARGETS[target_name]["max"]
    
    for article in articles:
        # Title
        title_el = article.find(attrs={"aria-label": "Title"})
        title = title_el.get_text().strip() if title_el else None
        
        # Price
        price_el = article.find(attrs={"aria-label": "Price"})
        price_raw = price_el.get_text().strip() if price_el else None
        price_val = clean_price(price_raw)
        
        # Location
        loc_el = article.find(attrs={"aria-label": "Location"})
        location = loc_el.get_text().strip() if loc_el else None
        if location:
            location = re.sub(r'[\uFFFD\u2022\u00A0]', '', location).strip()
            
        # Date Listed
        date_el = article.find(attrs={"aria-label": "Creation date"})
        date_str = date_el.get_text().strip() if date_el else None
        
        # Link URL
        link_el = article.find('a', href=True)
        link = link_el['href'] if link_el else None
        if link and not link.startswith('http'):
            link = "https://www.olx.com.pk" + link
            
        # Validation checks:
        # 1. Title and clean price must be present.
        # 2. Location must contain "Lahore" case-insensitive.
        # 3. Must be posted within the last 24 hours.
        # 4. Clean price must fall strictly between min and max price limits.
        # 5. Skip accessories using negative keyword screening.
        if title and price_val is not None and location and date_str:
            # Location check
            if "lahore" not in location.lower():
                continue
                
            # Date check (last 24 hours)
            if not is_last_24_hours(date_str):
                continue
                
            # Strict price boundaries
            if price_val < min_limit or price_val > max_limit:
                continue
                
            # Accessory exclusion
            accessory_keywords = [
                'case', 'cover', 'glass', 'protector', 'box only', 'charger', 'cable', 
                'pouch', 'silicone', 'handsfree', 'handfree', 'box copy', 'empty box', 
                'housing', 'lens', 'wrap', 'sticker', 'bag', 'stand', 'holder'
            ]
            if any(word in title.lower() for word in accessory_keywords):
                continue
                
            parsed_items.append({
                "Title": title,
                "Price": price_val,
                "Location": location,
                "Date Posted": date_str,
                "Link": link
            })
            
    # Scraping detailed descriptions for final filtered items
    # Since these are filtered to Lahore and last 24h, the count is small and safe.
    final_items = []
    for idx, item in enumerate(parsed_items):
        logging.info(f"Deep scraping description {idx+1}/{len(parsed_items)}: {item['Title']}")
        desc = fetch_ad_description(item["Link"])
        item["Description"] = desc
        final_items.append(item)
        # Polite scraping delay
        time.sleep(random.uniform(0.7, 1.3))
        
    return final_items


def main():
    logging.info("Starting Daily OLX Price Automation Run...")
    
    results = {}
    summary_data = []
    
    # Process each targeted iPhone
    for target in TARGETS:
        html = fetch_olx_html(target)
        # Avoid rapid blocks by adding delay between queries
        time.sleep(2.0)
        
        listings = parse_olx_listings(html, target)
        df = pd.DataFrame(listings)
        
        if not df.empty:
            results[target] = df
            ads_found = len(df)
            min_p = df["Price"].min()
            max_p = df["Price"].max()
            avg_p = df["Price"].mean()
            
            summary_data.append({
                "Target Model": target,
                "Ads Found": ads_found,
                "Min Price (PKR)": min_p,
                "Max Price (PKR)": max_p,
                "Average Price (PKR)": avg_p
            })
            logging.info(f"[{target}] Found {ads_found} matches in Lahore (last 24 hours). Avg Price: Rs. {avg_p:,.2f}")
        else:
            logging.info(f"[{target}] No matching listings found in Lahore in the last 24 hours.")
            summary_data.append({
                "Target Model": target,
                "Ads Found": 0,
                "Min Price (PKR)": 0,
                "Max Price (PKR)": 0,
                "Average Price (PKR)": 0
            })
            
    summary_df = pd.DataFrame(summary_data)
    
    # Generate Excel Report
    filename = "daily_olx_report.xlsx"
    logging.info(f"Compiling Excel file: {filename}")
    
    try:
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            summary_df.to_excel(writer, sheet_name="Summary", index=False)
            
            for target, df in results.items():
                # Excel sheets cannot have names longer than 31 characters
                sheet_name = target[:31]
                # Reorder columns for presentation
                df_out = df[["Title", "Price", "Location", "Date Posted", "Description", "Link"]]
                df_out.to_excel(writer, sheet_name=sheet_name, index=False)
                
        logging.info("Excel report generated successfully.")
    except Exception as e:
        logging.error(f"Failed to generate Excel report: {e}")
        return
        
    # Send Email Report
    logging.info(f"Sending email report to {RECIPIENT_EMAIL}...")
    
    msg = EmailMessage()
    msg['Subject'] = f"OLX Pakistan Price Tracker - Daily Report {pd.Timestamp.now().strftime('%Y-%m-%d')}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL
    
    # Render HTML summary table for the email body
    summary_html = summary_df.to_html(index=False, justify='center', border=1)
    
    # Custom email styling
    html_content = f"""
    <html>
        <head>
            <style>
                table {{
                    font-family: Arial, sans-serif;
                    border-collapse: collapse;
                    width: 80%;
                    margin: 20px 0;
                }}
                th {{
                    background-color: #0072FF;
                    color: white;
                    padding: 8px;
                }}
                td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: center;
                }}
                tr:nth-child(even) {{
                    background-color: #f2f2f2;
                }}
                h2 {{
                    color: #333;
                }}
            </style>
        </head>
        <body>
            <h2>OLX Pakistan Daily Price Intelligence</h2>
            <p>Here is the daily price summary for target iPhone models located in Lahore, posted within the last 24 hours.</p>
            {summary_html}
            <p>Please find the attached spreadsheet containing detailed listing links, pricing, and scraped descriptions.</p>
            <br>
            <p>Best Regards,<br>OLX Automation Agent</p>
        </body>
    </html>
    """
    
    msg.set_content("Please find attached the daily OLX price report.")
    msg.add_alternative(html_content, subtype='html')
    
    # Attach Excel file
    try:
        with open(filename, 'rb') as f:
            file_data = f.read()
            msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=filename)
            
        # SMTP connection
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            # If default placeholders are unchanged, log warning and exit instead of raising error
            if SENDER_EMAIL == "sender_email@gmail.com" or SENDER_PASSWORD == "your_app_password":
                logging.warning("SMTP credentials are placeholders. E-mail not sent. Please update sender credentials at the top of the script.")
                print(f"\n[REPORT DONE] Excel file successfully created locally: {filename}")
                return
                
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            logging.info("Email sent successfully!")
            
    except Exception as e:
        logging.error(f"Failed to email report: {e}")

if __name__ == "__main__":
    main()
