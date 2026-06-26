import os
import re
import requests

API_TOKEN = os.environ["PIPEDRIVE_API_TOKEN"]
JOB_FIELD_KEY = os.environ["PIPEDRIVE_JOB_FIELD_KEY"]
COMPANY_DOMAIN = os.environ["PIPEDRIVE_COMPANY_DOMAIN"]

BASE_URL = f"https://{COMPANY_DOMAIN}.pipedrive.com/api/v1"

START_NUMBER = 1000
PREFIX = "SB-"

def extract_number(value):
    if not value:
        return None
    match = re.search(r"SB-(\d+)", str(value))
    return int(match.group(1)) if match else None

def get_all_not_deleted_deals():
    deals = []
    start = 0
    limit = 100

    while True:
        response = requests.get(
            f"{BASE_URL}/deals",
            params={
                "api_token": API_TOKEN,
                "start": start,
                "limit": limit,
                "sort": "add_time ASC"
            }
        )
        response.raise_for_status()
        data = response.json()

        batch = data.get("data") or []
        deals.extend(batch)

        pagination = data.get("additional_data", {}).get("pagination", {})
        if not pagination.get("more_items_in_collection"):
            break

        start = pagination.get("next_start")

    return deals

deals = get_all_not_deleted_deals()
print(f"Found {len(deals)} open/won/lost deals")

used_numbers = []

for deal in deals:
    current = deal.get(JOB_FIELD_KEY)
    num = extract_number(current)
    if num:
        used_numbers.append(num)

next_number = max(used_numbers) + 1 if used_numbers else START_NUMBER
print(f"Next available job number: {PREFIX}{next_number}")

for deal in deals:
    deal_id = deal["id"]
    title = deal.get("title", "")
    current = deal.get(JOB_FIELD_KEY)

    if extract_number(current):
        print(f"Skipped {deal_id} | {title} — already has {current}")
        continue

    new_job_number = f"{PREFIX}{next_number}"

    update = requests.put(
        f"{BASE_URL}/deals/{deal_id}",
        params={"api_token": API_TOKEN},
        json={JOB_FIELD_KEY: new_job_number}
    )

    if not update.ok:
        print("FAILED")
        print("Deal ID:", deal_id)
        print("Title:", title)
        print("Status:", update.status_code)
        print("Response:", update.text)
        raise SystemExit(1)

    print(f"Updated {deal_id} | {title} → {new_job_number}")
    next_number += 1
