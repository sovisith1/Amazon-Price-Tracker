# Amazon Price Tracker

A real-time Amazon price tracking tool built with Python. This command-line utility scrapes the current price and product name from any Amazon product URL, logs the data with timestamps, and allows users to query lowest and average prices across customizable time windows (7–730 days). A background thread automatically updates the price every 60 seconds for uninterrupted tracking.

Features:
• Real-time price scraping using requests + BeautifulSoup
• Background thread updates price every minute
• Logs historical data to CSV for long-term tracking
• Query lowest or average price over 7, 30, 90, 180, 365, or 730 days
• Built-in data analytics with pandas
• Robust CLI with user input validation and helpful error messages

Tech Stack:
• Python 3
• Requests, BeautifulSoup4, pandas, csv, datetime, threading

Example output:
Paste Amazon product URL:

Initial scrape …
Now tracking: Apple iPad Pro 11-Inch (M4): Built for Apple Intelligence, Ultra Retina XDR Display, 256GB, 12MP Front/Back Camera, LiDAR Scanner, Wi-Fi 6E, Face ID, All-Day Battery Life — Space Black  —  $899.00

Background polling every 60 s started.


Metric: 1) Lowest  2) Average
Choose 1 or 2 (q to quit): 1

Timeframe:
  1) Past 7 days
  2) Past 30 days
  3) Past 90 days
  4) Past 180 days
  5) Past 365 days
  6) Past 730 days
Choose option (q to quit): q

Stopping. Bye!
