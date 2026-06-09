import streamlit as st
import pandas as pd
import re
import random
import time
import io

# --- Page Configuration ---
st.set_page_config(
    page_title="OLX Price Tracker & Analyzer",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Injecting Custom Premium Styles (Teal, Navy, Gold, White) ---
st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
        
        /* Font Styles */
        html, body, [data-testid="stSidebar"], .stMarkdown {
            font-family: 'Outfit', sans-serif;
        }
        
        /* Clean White Main Background */
        .stApp {
            background-color: #FFFFFF !important;
            color: #333333 !important;
        }
        
        /* Dark Navy Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #0C2340 !important;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }
        /* Style labels, headings, and paragraphs to be white */
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] span[data-testid="stWidgetLabel"] {
            color: #FFFFFF !important;
        }
        /* Style inputs in sidebar to remain readable */
        [data-testid="stSidebar"] input {
            background-color: #FFFFFF !important;
            color: #0C2340 !important;
            border-radius: 6px !important;
        }
        /* Style dropdown selectbox containers */
        [data-testid="stSidebar"] div[data-baseweb="select"] {
            background-color: #FFFFFF !important;
            border-radius: 6px !important;
        }
        [data-testid="stSidebar"] div[data-baseweb="select"] * {
            color: #0C2340 !important;
        }
        /* Style the primary button in sidebar (Teal background, White text) */
        [data-testid="stSidebar"] button {
            background-color: #008080 !important;
            color: #FFFFFF !important;
            border: 1px solid #008080 !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }
        [data-testid="stSidebar"] button * {
            color: #FFFFFF !important;
        }
        [data-testid="stSidebar"] button:hover {
            background-color: #0C2340 !important;
            border-color: #0C2340 !important;
            color: #FFFFFF !important;
        }
        [data-testid="stSidebar"] button:hover * {
            color: #FFFFFF !important;
        }
        
        /* Sidebar custom container card class */
        .sidebar-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.15);
        }
        
        /* Main page Title Container */
        .header-container {
            background-color: #FFFFFF;
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(12,35,64,0.06);
            margin-bottom: 25px;
            border-bottom: 4px solid #008080;
            text-align: center;
        }
        .header-title {
            color: #0C2340;
            font-size: 2.8rem;
            font-weight: 700;
            margin: 0;
        }
        .header-subtitle {
            color: #008080;
            font-weight: 600;
            font-size: 1.15rem;
            margin-top: 6px;
        }
        
        /* Premium Alert Card Style */
        .success-alert {
            background-color: #E0F2F1;
            border-left: 5px solid #008080;
            color: #004D40;
            padding: 12px 20px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            margin-bottom: 25px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        /* Premium Directory Card Wrapper */
        .directory-container {
            background-color: #FFFFFF;
            border: 1px solid #e0e0e0;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.03);
            margin-top: 25px;
        }
        
        /* Premium Chart Card Wrapper */
        .chart-card {
            background-color: #FFFFFF;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.02);
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# --- Realistic User-Agent Pool ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
]

# --- Target Models Default Configuration ---
TARGETS = {
    "iPhone 14 Pro Max PTA": {"min": 180000, "max": 350000},
    "iPhone 15 Pro Max PTA": {"min": 250000, "max": 450000},
    "iPhone 15 Pro Max Non-PTA": {"min": 150000, "max": 320000},
    "iPhone 16 Pro Max Non-PTA": {"min": 200000, "max": 420000},
    "iPhone 17 Pro Non-PTA": {"min": 220000, "max": 450000},
    "iPhone 17 Pro Max Non-PTA": {"min": 260000, "max": 550000}
}

# --- Helper Functions ---

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
    except Exception:
        pass
    return None


def fetch_olx_data(keyword):
    import requests
    formatted_query = keyword.strip().replace(" ", "-").lower()
    url = f"https://www.olx.com.pk/items/q-{formatted_query}?sorting=desc-creation"
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }
    try:
        response = requests.get(url, headers=headers, timeout=12)
        if response.status_code == 200:
            return response.text, url
        elif response.status_code == 403:
            raise Exception("OLX Pakistan blocked the request (403 Forbidden). OLX uses active anti-bot systems.")
        else:
            raise Exception(f"Failed to fetch data (HTTP Status: {response.status_code}).")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Connection timeout or network error: {str(e)}")


def fetch_description(detail_url):
    import requests
    from bs4 import BeautifulSoup
    if not detail_url:
        return "No link available"
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        res = requests.get(detail_url, headers=headers, timeout=8)
        if res.status_code == 200:
            soup = BeautifulSoup(res.content, 'html.parser')
            desc_div = soup.find(attrs={"aria-label": "Description"})
            if desc_div:
                desc_text = desc_div.get_text().strip()
                if desc_text.lower().startswith("description"):
                    desc_text = desc_text[len("description"):].strip()
                return desc_text
    except Exception:
        pass
    return "See listing details via URL link"


def parse_listings(html_content):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    articles = soup.find_all(attrs={"data-aut-id": "itemBox"})
    if not articles:
        articles = soup.find_all('article')
    
    data = []
    for article in articles:
        title_el = article.find(attrs={"aria-label": "Title"})
        title = title_el.get_text().strip() if title_el else None
        
        price_el = article.find(attrs={"aria-label": "Price"})
        price_raw = price_el.get_text().strip() if price_el else None
        price_val = clean_price(price_raw)
        
        loc_el = article.find(attrs={"aria-label": "Location"})
        location = loc_el.get_text().strip() if loc_el else None
        if location:
            location = re.sub(r'[\uFFFD\u2022\u00A0]', '', location).strip()
            
        date_el = article.find(attrs={"aria-label": "Creation date"})
        date = date_el.get_text().strip() if date_el else None
        
        img_el = article.find('img')
        img_url = None
        if img_el:
            img_url = img_el.get('src') or img_el.get('data-src') or img_el.get('srcset')
            if img_url and ',' in img_url:
                img_url = img_url.split(',')[0].split(' ')[0]
                
        link_el = article.find('a', href=True)
        link = link_el['href'] if link_el else None
        if link and not link.startswith('http'):
            link = "https://www.olx.com.pk" + link
            
        if title and price_raw:
            data.append({
                "Image": img_url,
                "Title": title,
                "Price (Raw)": price_raw,
                "Price": price_val,
                "Location": location or "N/A",
                "Date Posted": date or "N/A",
                "Link": link
            })
            
    return pd.DataFrame(data)


# --- UI Premium Metric Renderer (Custom styled borders/texts) ---
def render_premium_metric(label, value, icon, border_color, text_color):
    st.markdown(f"""
    <div style="
        background-color: #FFFFFF;
        border: 1px solid #e2e8f0;
        border-top: 4px solid {border_color};
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(12, 35, 64, 0.04);
        transition: all 0.3s ease;
        margin: 8px 0;
    ">
        <div style="font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1.2px; color: #718096; font-weight: 600; margin-bottom: 8px;">
            {icon} {label}
        </div>
        <div style="font-size: 1.7rem; font-weight: 700; color: {text_color};">
            {value}
        </div>
    </div>
    """, unsafe_allow_html=True)


# --- HTML/CSS Elegant Data Table Renderer ---
def render_html_table(df):
    html = """
    <div style="overflow-x: auto; border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.02);">
    <table style="width: 100%; border-collapse: collapse; background-color: #ffffff; text-align: left; font-family: 'Outfit', sans-serif;">
        <thead>
            <tr style="background-color: #0C2340; color: #ffffff; border-bottom: 2px solid #e2e8f0;">
                <th style="padding: 12px 15px; font-weight: 600; text-align: center; font-size: 0.95rem;">Preview</th>
                <th style="padding: 12px 15px; font-weight: 600; font-size: 0.95rem;">Product Title</th>
                <th style="padding: 12px 15px; font-weight: 600; font-size: 0.95rem;">Cleaned Price</th>
                <th style="padding: 12px 15px; font-weight: 600; font-size: 0.95rem;">Location</th>
                <th style="padding: 12px 15px; font-weight: 600; text-align: center; font-size: 0.95rem;">Date Posted</th>
                <th style="padding: 12px 15px; font-weight: 600; font-size: 0.95rem;">Listing Description</th>
                <th style="padding: 12px 15px; font-weight: 600; text-align: center; font-size: 0.95rem;">URL</th>
            </tr>
        </thead>
        <tbody>
    """
    for i, (idx, row) in enumerate(df.iterrows()):
        bg_color = "#ffffff" if i % 2 == 0 else "#f8fafc"
        
        # Date Recency Styling
        date_str = str(row["Date Posted"])
        date_lower = date_str.lower()
        if any(x in date_lower for x in ["hour", "minute", "min", "second", "now"]):
            date_html = f'<span style="color: #2E7D32; background-color: #E8F5E9; padding: 4px 10px; border-radius: 12px; font-size: 0.82rem; font-weight: 600; display: inline-block;"><i class="fa-solid fa-clock"></i> {date_str}</span>'
        else:
            date_html = f'<span style="color: #D97706; background-color: #FEF3C7; padding: 4px 10px; border-radius: 12px; font-size: 0.82rem; font-weight: 600; display: inline-block;"><i class="fa-solid fa-calendar"></i> {date_str}</span>'
            
        # Image Thumbnail Border Styling
        img_url = row["Image"] if row["Image"] else "https://images.olx.com.pk/thumbnails/617848815-400x300.jpeg"
        img_html = f'<div style="text-align: center;"><img src="{img_url}" style="border: 2px solid #cbd5e1; border-radius: 6px; width: 60px; height: 45px; object-fit: cover; box-shadow: 0 1px 3px rgba(0,0,0,0.05);"></div>'
        
        # Clickable icon link
        url_html = f'<div style="text-align: center;"><a href="{row["Link"]}" target="_blank" style="text-decoration: none; font-size: 1.25rem; color: #008080;" title="Open Ad Link">🔗</a></div>'
        
        desc_text = row["Description"] if row["Description"] else "N/A"
        if len(desc_text) > 120:
            desc_text = desc_text[:117] + "..."
            
        html += f"""
            <tr style="background-color: {bg_color}; border-bottom: 1px solid #e2e8f0; color: #334155; transition: background-color 0.2s ease;">
                <td style="padding: 10px 15px;">{img_html}</td>
                <td style="padding: 10px 15px; font-weight: 500; color: #0C2340; font-size: 0.92rem;">{row["Title"]}</td>
                <td style="padding: 10px 15px; font-weight: 700; color: #008080; font-size: 0.95rem;">Rs. {row["Price"]:,.0f}</td>
                <td style="padding: 10px 15px; font-size: 0.88rem; color: #475569;"><i class="fa-solid fa-location-dot" style="color: #DAA520; margin-right: 4px;"></i> {row["Location"]}</td>
                <td style="padding: 10px 15px; text-align: center;">{date_html}</td>
                <td style="padding: 10px 15px; font-size: 0.85rem; color: #64748b; max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{desc_text}</td>
                <td style="padding: 10px 15px;">{url_html}</td>
            </tr>
        """
    html += """
        </tbody>
    </table>
    </div>
    """
    return html


# --- Mock Data ---
@st.cache_data
def get_mock_data(keyword, location_filter):
    base_price = 100000
    for key in TARGETS:
        if key.lower() in keyword.lower():
            base_price = (TARGETS[key]["min"] + TARGETS[key]["max"]) // 2
            break
    mock_items = []
    locations = [f"Gulberg, {location_filter}", f"DHA, {location_filter}", f"Johar Town, {location_filter}", f"Samanabad, {location_filter}", f"Model Town, {location_filter}"]
    dates = ["2 hours ago", "5 hours ago", "12 hours ago", "1 day ago", "3 days ago", "4 days ago", "1 week ago"]
    
    # 20 matching listings
    for i in range(1, 21):
        price = int(base_price + random.randint(-25000, 30000))
        title = f"{keyword} Premium quality Item {i}"
        if "car" in keyword.lower():
            title = f"{keyword.capitalize()} Model {2020 + i % 5} Automatic Clean Condition"
            price = int(1200000 + random.randint(-200000, 500000))
        elif "sofa" in keyword.lower():
            title = f"Comfortable 5-Seater Wooden {keyword.capitalize()} Set"
            price = int(45000 + random.randint(-15000, 15000))
        
        mock_items.append({
            "Image": "https://images.olx.com.pk/thumbnails/617848815-400x300.jpeg",
            "Title": title,
            "Price (Raw)": f"Rs {price:,}",
            "Price": float(price),
            "Location": random.choice(locations),
            "Date Posted": random.choice(dates),
            "Link": "https://www.olx.com.pk"
        })
        
    # Accessories
    for i in range(1, 5):
        price = random.randint(600, 3000)
        mock_items.append({
            "Image": "https://images.olx.com.pk/thumbnails/608985210-600x450.jpeg",
            "Title": f"Premium MagSafe protective case for {keyword}" if "phone" in keyword.lower() or "iphone" in keyword.lower() else f"Accessory item for {keyword}",
            "Price (Raw)": f"Rs {price:,}",
            "Price": float(price),
            "Location": random.choice(locations),
            "Date Posted": random.choice(dates),
            "Link": "https://www.olx.com.pk"
        })
    return pd.DataFrame(mock_items)


# --- MAIN INTERFACE RENDER ---

# Premium Top Title Header Card
st.markdown("""
    <div class="header-container">
        <h1 class="header-title">OLX Price Tracker & Analyzer</h1>
        <div class="header-subtitle">
            <i class="fas fa-chart-line"></i> Targeted device price intelligence center
        </div>
    </div>
""", unsafe_allow_html=True)

# --- SIDEBAR INTERFACE ---
st.sidebar.markdown('### 📱 Device intelligence Hub')

# Sidebar Card wrapper 1
st.sidebar.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
preset_list = list(TARGETS.keys()) + ["Custom Search"]
selected_preset = st.sidebar.selectbox(
    "Select Target Model Preset:",
    options=preset_list
)

if selected_preset == "Custom Search":
    custom_search_input_variable = st.sidebar.text_input("Enter custom keyword (e.g., Samsung S24):", value="iPhone 13")
    default_min = 50000.0
    default_max = 500000.0
    default_location = "Lahore"
else:
    custom_search_input_variable = ""
    default_min = float(TARGETS[selected_preset]["min"])
    default_max = float(TARGETS[selected_preset]["max"])
    default_location = "Lahore"

if selected_preset == "Custom Search":
    final_search_query = custom_search_input_variable 
else:
    final_search_query = selected_preset

search_query = final_search_query
location_filter = st.sidebar.text_input("📍 Filter Location (City):", value=default_location)
st.sidebar.markdown('</div>', unsafe_allow_html=True)

# Sidebar Card wrapper 2 (Price Filters)
st.sidebar.markdown('### <i class="fa-solid fa-filter" style="margin-right:8px;"></i> Price Scope', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
min_price_input = st.sidebar.number_input("💵 Min Price (PKR):", min_value=0.0, value=default_min, step=5000.0)
max_price_input = st.sidebar.number_input("💵 Max Price (PKR):", min_value=0.0, value=default_max, step=5000.0)
st.sidebar.markdown('</div>', unsafe_allow_html=True)

# Sidebar Card wrapper 3 (Advanced toggles)
st.sidebar.markdown('### ⚙️ Automation Settings', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
exclude_accessories = st.sidebar.toggle("Exclude Accessories", value=True, help="Automatically screens out cases, sleeves, and chargers.")
deep_scrape = st.sidebar.toggle("Deep Scrape Descriptions", value=False, help="Performs request-per-ad detailed scraping for full descriptions.")
st.sidebar.markdown('</div>', unsafe_allow_html=True)

fetch_btn = st.sidebar.button("Fetch & Analyze Data", type="primary", use_container_width=True)

# Session States
if "raw_df" not in st.session_state:
    st.session_state.raw_df = None
if "current_query" not in st.session_state:
    st.session_state.current_query = ""
if "url_fetched" not in st.session_state:
    st.session_state.url_fetched = ""
if "is_mock" not in st.session_state:
    st.session_state.is_mock = False

# --- Fetch Action ---
if fetch_btn and search_query:
    with st.spinner("Accessing OLX Pakistan for real-time market data..."):
        try:
            html_content, target_url = fetch_olx_data(search_query)
            df = parse_listings(html_content)
            
            # Scrape description now if deep_scrape is active
            if deep_scrape and not df.empty:
                # Filter df to scrape only the relevant ads to save time/resources
                df_to_scrape = df.dropna(subset=['Price'])
                df_to_scrape = df_to_scrape[
                    (df_to_scrape['Price'] >= min_price_input) & 
                    (df_to_scrape['Price'] <= max_price_input)
                ]
                if location_filter.strip():
                    df_to_scrape = df_to_scrape[
                        df_to_scrape['Location'].str.lower().str.contains(location_filter.strip().lower(), na=False)
                    ]
                if exclude_accessories:
                    accessory_keywords = [
                        'case', 'cover', 'glass', 'protector', 'box only', 'charger', 'cable', 
                        'pouch', 'silicone', 'handsfree', 'handfree', 'box copy', 'empty box', 
                        'housing', 'lens', 'wrap', 'sticker', 'bag', 'stand', 'holder', 'earbuds'
                    ]
                    pattern = '|'.join(accessory_keywords)
                    df_to_scrape = df_to_scrape[~df_to_scrape['Title'].str.lower().str.contains(pattern, na=False, regex=True)]
                
                desc_map = {}
                if not df_to_scrape.empty:
                    with st.spinner("Scraping detailed listing descriptions..."):
                        total = len(df_to_scrape)
                        progress_text = st.empty()
                        progress_bar = st.progress(0.0)
                        
                        for idx, (row_idx, row) in enumerate(df_to_scrape.iterrows()):
                            progress_text.write(f"Scraping detailed description for ad {idx + 1} of {total}...")
                            desc = fetch_description(row["Link"])
                            desc_map[row["Link"]] = desc
                            progress_bar.progress((idx + 1) / total)
                            time.sleep(random.uniform(0.6, 1.4))
                            
                        progress_text.empty()
                        progress_bar.empty()
                
                df['Description'] = df['Link'].map(lambda x: desc_map.get(x, "Description scraping disabled (activate in sidebar toggle)"))
            else:
                df['Description'] = "Description scraping disabled (activate in sidebar toggle)"
                
            st.session_state.raw_df = df
            st.session_state.current_query = search_query
            st.session_state.url_fetched = target_url
            st.session_state.is_mock = False
            
            if df.empty:
                st.warning("No listings found. The DOM structure may have updated.")
        except Exception as e:
            st.error(f"Scraper blocked: {str(e)}")
            st.info(f"Loading premium mock simulation dataset for '{search_query}' in {location_filter}...")
            df_mock = get_mock_data(search_query, location_filter)
            df_mock['Description'] = "See listing details via URL link"
            
            st.session_state.raw_df = df_mock
            st.session_state.current_query = search_query
            st.session_state.url_fetched = f"https://www.olx.com.pk/items/q-{search_query.replace(' ', '-')}"
            st.session_state.is_mock = True

# --- Dashboard Logic ---
if st.session_state.raw_df is not None and not st.session_state.raw_df.empty:
    import plotly.express as px
    df_filtered = st.session_state.raw_df.copy()
    
    # 1. Clean missing prices
    df_filtered = df_filtered.dropna(subset=['Price'])
    
    # 2. Strict Price Range Filter
    df_filtered = df_filtered[
        (df_filtered['Price'] >= min_price_input) & 
        (df_filtered['Price'] <= max_price_input)
    ]
    
    # 3. Location Filter (strict matching)
    if location_filter.strip():
        df_filtered = df_filtered[
            df_filtered['Location'].str.lower().str.contains(location_filter.strip().lower(), na=False)
        ]
        
    # 4. Exclude Accessories
    if exclude_accessories:
        accessory_keywords = [
            'case', 'cover', 'glass', 'protector', 'box only', 'charger', 'cable', 
            'pouch', 'silicone', 'handsfree', 'handfree', 'box copy', 'empty box', 
            'housing', 'lens', 'wrap', 'sticker', 'bag', 'stand', 'holder', 'earbuds'
        ]
        pattern = '|'.join(accessory_keywords)
        df_filtered = df_filtered[~df_filtered['Title'].str.lower().str.contains(pattern, na=False, regex=True)]

    # Render results
    if df_filtered.empty:
        st.warning("⚠️ All listings were filtered out by your current settings. Broaden your price limits or location filters.")
    else:
        # Ensure Description column exists
        if 'Description' not in df_filtered.columns:
            df_filtered['Description'] = "Description scraping disabled (activate in sidebar toggle)"

        # Stylized Success Alert Card
        st.markdown(f"""
            <div class="success-alert">
                <i class="fa-solid fa-circle-check" style="font-size: 1.4rem; color: #008080; margin-right: 12px;"></i>
                <div style="font-weight: 600;">Successfully fetched and analyzed {len(df_filtered)} listings matching your criteria!</div>
            </div>
        """, unsafe_allow_html=True)
        
        if not st.session_state.is_mock:
            st.markdown(f"🌐 **Scrape Reference URL:** [{st.session_state.url_fetched}]({st.session_state.url_fetched})")

        # --- Premium Metric Cards (Color Coded Borders & Texts) ---
        total_ads = len(df_filtered)
        min_price = df_filtered['Price'].min()
        max_price = df_filtered['Price'].max()
        avg_price = df_filtered['Price'].mean()
        median_price = df_filtered['Price'].median()
        
        m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
        with m_col1:
            # Teal Border/Text (Quantity)
            render_premium_metric("Total Ads Found", f"{total_ads}", "🏷️", "#008080", "#008080")
        with m_col2:
            # Light Green Border/Text (Deal)
            render_premium_metric("Lowest Price", f"Rs. {min_price:,.0f}", "📉", "#2E7D32", "#2E7D32")
        with m_col3:
            # Soft Red Border/Text (Premium)
            render_premium_metric("Highest Price", f"Rs. {max_price:,.0f}", "📈", "#C62828", "#C62828")
        with m_col4:
            # Navy Border/Text (Market Average)
            render_premium_metric("Average Price", f"Rs. {avg_price:,.0f}", "💸", "#0C2340", "#0C2340")
        with m_col5:
            # Navy Border/Text (Market Average)
            render_premium_metric("Median Price", f"Rs. {median_price:,.0f}", "⚖️", "#0C2340", "#0C2340")

        st.markdown("---")

        # --- Visual Analytics Cards ---
        st.markdown("### 📊 Visual Price Analytics")
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("""
                <div style="background-color: #0C2340; color: white; padding: 8px 15px; border-radius: 6px 6px 0 0; font-weight: 600; font-size: 1rem; text-align: center;">
                    📊 Price Frequency Distribution
                </div>
            """, unsafe_allow_html=True)
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            
            # Histogram
            fig_hist = px.histogram(
                df_filtered, 
                x="Price", 
                nbins=8,
                labels={"Price": "Price (PKR)", "count": "Count"},
                hover_data=["Title", "Location", "Date Posted"],
                color_discrete_sequence=["#008080"] # Teal bars
            )
            fig_hist.update_layout(
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF",
                font_color="#333333",
                margin=dict(l=20, r=20, t=20, b=20),
                xaxis=dict(showgrid=True, gridcolor="#e2e8f0", tickprefix="Rs. "),
                yaxis=dict(showgrid=True, gridcolor="#e2e8f0"),
                bargap=0.1
            )
            st.plotly_chart(fig_hist, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with chart_col2:
            st.markdown("""
                <div style="background-color: #008080; color: white; padding: 8px 15px; border-radius: 6px 6px 0 0; font-weight: 600; font-size: 1rem; text-align: center;">
                    ⚖️ Price Spread & Outliers Box Plot
                </div>
            """, unsafe_allow_html=True)
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            
            # Box Plot (Teal body, Deep Navy median and dots)
            fig_box = px.box(
                df_filtered,
                y="Price",
                points="all",
                hover_data=["Title", "Location", "Date Posted"],
                labels={"Price": "Price (PKR)"},
                color_discrete_sequence=["#008080"]
            )
            fig_box.update_traces(
                marker=dict(color="#0C2340"), # Navy blue for outliers/individual points
                line=dict(color="#0C2340"),   # Navy blue for median lines/whiskers
                fillcolor="#008080"           # Teal box fill
            )
            fig_box.update_layout(
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF",
                font_color="#333333",
                margin=dict(l=20, r=20, t=20, b=20),
                yaxis=dict(showgrid=True, gridcolor="#e2e8f0", tickprefix="Rs. ")
            )
            st.plotly_chart(fig_box, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # --- Directory Card Wrapper ---
        table_html = render_html_table(df_filtered)
        directory_html = f"""
<div class="directory-container">
    <h3 style="color: #0C2340; font-weight: 700; margin-top: 0; margin-bottom: 18px; display: flex; align-items: center; font-size: 1.25rem;">
        <i class="fa-solid fa-folder-open" style="color: #008080; margin-right: 10px;"></i> LISTINGS DIRECTORY
    </h3>
    {table_html}
</div>
"""
        # Clean up all line indentations so Markdown parser doesn't trigger code blocks
        clean_directory_html = "\n".join([line.strip() for line in directory_html.split("\n")])
        st.markdown(clean_directory_html, unsafe_allow_html=True)
        
        # CSV download below wrapper
        df_csv = df_filtered[["Title", "Price", "Location", "Date Posted", "Description", "Link"]]
        csv_data = df_csv.to_csv(index=False).encode('utf-8')
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="📥 Download Data as CSV",
            data=csv_data,
            file_name="olx_filtered_data.csv",
            mime="text/csv",
            use_container_width=True
        )

else:
    # --- Landing Page ---
    st.markdown("""
        <div style="background-color: #F8FAFC; border: 1px dashed #cbd5e1; border-radius: 8px; padding: 25px; text-align: center; margin-top: 20px;">
            <i class="fa-solid fa-square-poll-vertical" style="font-size: 2.5rem; color: #008080; margin-bottom: 12px;"></i>
            <h4 style="color: #0C2340; margin: 0; font-weight: 600;">Welcome to OLX Price Tracking Center</h4>
            <p style="color: #64748b; font-size: 0.95rem; margin-top: 8px;">Select a preset or type a device query in the sidebar, set your price thresholds, and click <b>Fetch & Analyze Data</b> to build the market analysis dashboard.</p>
        </div>
    """, unsafe_allow_html=True)
