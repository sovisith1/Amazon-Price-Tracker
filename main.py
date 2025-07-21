#!/usr/bin/env python3
"""
amazon_price_tracker_live.py
-----------------------------------------------------------------
• Ask once for an Amazon product URL
• Immediately scrape and log (date, product_name, price) to CSV
• Spawn a background thread that re-scrapes every 60 s forever
• In the foreground, let the user repeatedly query:
      – Lowest   or   Average price
      – Past 7 / 30 / 90 / 180 / 365 / 730 days
-----------------------------------------------------------------
Dependencies: requests, beautifulsoup4, pandas
Install once with:  python3 -m pip install requests beautifulsoup4 pandas
"""

import csv
import datetime as dt
import sys
import threading
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

CSV_FILE = Path("price_data.csv")
POLL_SECONDS = 60  # <-- fixed 1-minute interval

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

TIME_WINDOWS = {
    "1": ("Past 7 days", 7),
    "2": ("Past 30 days", 30),
    "3": ("Past 90 days", 90),
    "4": ("Past 180 days", 180),
    "5": ("Past 365 days", 365),
    "6": ("Past 730 days", 730),
}


# ───────────────────────── scraping helpers ─────────────────────────
def get_product_info(url: str) -> tuple[str, float]:
    resp = requests.get(url, headers=HEADERS, timeout=15)
    if resp.status_code != 200:
        raise RuntimeError(f"Amazon HTTP {resp.status_code}")

    soup = BeautifulSoup(resp.text, "html.parser")

    title_tag = soup.find(id="productTitle")
    if not title_tag:
        raise RuntimeError("product title not found")
    product_name = title_tag.get_text(strip=True)

    price_selectors = [
        ("id", "priceblock_ourprice"),
        ("id", "priceblock_dealprice"),
        ("id", "priceblock_saleprice"),
        ("class_", "a-price-whole"),
    ]
    price_text = None
    for attr, val in price_selectors:
        tag = soup.find(**{attr: val})
        if tag:
            price_text = tag.get_text(strip=True)
            break
    if not price_text:
        raise RuntimeError("price not found")

    price_text = price_text.replace("$", "").replace(",", "")
    try:
        price = float(price_text)
    except ValueError:
        raise RuntimeError(f"cannot parse price {price_text!r}")

    return product_name, price


def append_to_csv(date: dt.date, product_name: str, price: float) -> None:
    new_file = not CSV_FILE.exists()
    with CSV_FILE.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["date", "product_name", "price"])
        w.writerow([date.isoformat(), product_name, f"{price:.2f}"])


def load_data() -> pd.DataFrame:
    if CSV_FILE.exists():
        df = pd.read_csv(CSV_FILE, parse_dates=["date"])
    else:
        df = pd.DataFrame(columns=["date", "product_name", "price"])
        df["date"] = pd.to_datetime(df["date"])
    return df


# ───────────────────────── background poller ───────────────────────
def poller(url: str, product_name: str):
    """Daemon thread: scrape & log every POLL_SECONDS."""
    while True:
        try:
            name, price = get_product_info(url)
            # If Amazon tweaked the name, fall back to original for matching
            append_to_csv(dt.date.today(), product_name, price)
        except Exception as e:
            print(f"[poller] {e}")
        time.sleep(POLL_SECONDS)


# ───────────────────────── menu helpers ────────────────────────────
def choose_metric() -> str:
    print("\nMetric: 1) Lowest  2) Average")
    while True:
        c = input("Choose 1 or 2 (q to quit): ").strip().lower()
        if c in ("1", "2"):
            return "lowest" if c == "1" else "average"
        if c == "q":
            raise KeyboardInterrupt
        print("Invalid choice.")


def choose_window() -> int:
    print("\nTimeframe:")
    for k, (label, _) in TIME_WINDOWS.items():
        print(f"  {k}) {label}")
    while True:
        c = input("Choose option (q to quit): ").strip().lower()
        if c in TIME_WINDOWS:
            return TIME_WINDOWS[c][1]
        if c == "q":
            raise KeyboardInterrupt
        print("Invalid choice.")


# ───────────────────────── main flow ───────────────────────────────
def main() -> None:
    url = input("Paste Amazon product URL: ").strip()

    # initial scrape & log
    print("\nInitial scrape …")
    try:
        product_name, price = get_product_info(url)
    except Exception as e:
        sys.exit(f"Error: {e}")

    append_to_csv(dt.date.today(), product_name, price)
    print(f"Now tracking: {product_name}  —  ${price:.2f}")
    print("Logging to", CSV_FILE.resolve())

    # start daemon poller
    t = threading.Thread(target=poller, args=(url, product_name), daemon=True)
    t.start()
    print(f"\nBackground polling every {POLL_SECONDS} s started.\n")

    # interactive query loop
    try:
        while True:
            metric = choose_metric()
            days = choose_window()

            df = load_data()
            pdf = df[df["product_name"] == product_name]
            cutoff = pd.Timestamp(dt.date.today() - dt.timedelta(days=days))
            window = pdf[pdf["date"] >= cutoff]

            if window.empty:
                print("  Not enough data yet — try again later.\n")
                continue

            if metric == "lowest":
                val = window["price"].min()
                print(f"  LOWEST price in last {days} days: ${val:.2f}\n")
            else:
                val = window["price"].mean()
                print(f"  AVERAGE price in last {days} days: ${val:.2f}\n")

    except KeyboardInterrupt:
        print("\nStopping. Bye!")


if __name__ == "__main__":
    main()