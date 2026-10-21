import os
import re
import requests
from playwright.sync_api import sync_playwright

URL = ("https://mlb.tickets.com/?agency=MLB_MPV&orgid=4&pid=9777633"
       "#/event/9777633/ticketlist/?view=sections&quantity=1"
       "&sort=price_asc&ada=false&seatSelection=false")
NTFY_TOPIC = os.environ["NTFY_TOPIC"]
LABEL = "Ticket price for this event starts at"

def get_price():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)

        row = page.locator("div", has_text=LABEL).last
        row.wait_for(timeout=45000)
        text = row.inner_text()
        browser.close()

    match = re.search(r"\$([\d,]+\.\d{2})", text)
    if not match:
        raise RuntimeError(f"Couldn't find a price in: {text!r}")
    return float(match.group(1).replace(",", ""))

def notify(msg):
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=msg.encode("utf-8"),
        headers={"Title": "Brewers ticket available!", "Priority": "high"},
        timeout=30,
    )

def main():
    price = get_price()
    print("Current price:", price)
    if price != 0.00:
        notify(f"Tickets available, starting at ${price:.2f}\n{URL}")

if __name__ == "__main__":
    main()
