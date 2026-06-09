# OLX Price Tracker & Analyzer 📊

A premium, enterprise-grade market intelligence and price analytics platform built for scraping, monitoring, and visualizing listings from OLX Pakistan in real-time.

---

## Key Features

*   🔍 **Universal Custom Search**: Search any product keyword (e.g., *Samsung S24*, *Cars*, *Sofa*) or select from predefined target models.
*   ⚡ **Instant Filters (Out-of-Form)**: Toggle options like *Exclude Accessories* and *Deep Scrape Descriptions* or adjust *Price Scope* and *Location Filter* with real-time UI responsiveness.
*   📈 **Market Analytics Dashboard**: Rich data visualizations including:
    *   **Price Metrics Card**: High-contrast display showing Lowest, Highest, Average, and Median Prices.
    *   **Price Frequency Distribution**: Interactive histogram representing the listing density.
    *   **Price Spread & Outliers**: Box plot mapping pricing variance and outlier detections.
*   🏷️ **Smart Ad Parser**: Custom scraper that targets universal HTML listing containers (`data-aut-id="itemBox"`) to bypass categories and extract clean, validated ad content.
*   ⏰ **Automated Daily Reporter**: Standalone scheduled runner (`daily_reporter.py`) that scrapes the market, updates an Excel database (`daily_olx_report.xlsx`), and mails out structured analytical updates.

---

## Project Structure

```
├── app.py                  # Core Streamlit Web Application
├── daily_reporter.py       # Automated Daily Scraper & Emailer
├── requirements.txt        # Dependencies and Libraries
├── .gitignore              # Git ignored log, build and excel artifacts
└── README.md               # Documentation
```

---

## Installation & Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Alisha-Ayyaz/OLX-Price-Analyzer.git
   cd OLX-Price-Analyzer
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Dashboard**:
   ```bash
   streamlit run app.py
   ```
   Open [http://localhost:8501/](http://localhost:8501/) in your web browser.

---

## Automating the Reporter

To configure the daily reporter for email alerts:
1. Open `daily_reporter.py` and set your sender/receiver details.
2. Run the reporter:
   ```bash
   python daily_reporter.py
   ```