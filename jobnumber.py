import os
import re
import requests

API_TOKEN = os.environ["PIPEDRIVE_API_TOKEN"]
COMPANY_DOMAIN = os.environ["PIPEDRIVE_COMPANY_DOMAIN"]
JOB_FIELD_NAME = os.environ.get("PIPEDRIVE_JOB_FIELD_NAME", "JOB NUMBER")

BASE_URL = f"https://{COMPANY_DOMAIN}.pipedrive.com/api/v1"
START_NUMBER = 1000
PREFIX = "SB-"

def api_get(path, params=None):
    params = params or {}
    params["api_token"] = API_TOKEN
    r = requests.get(f"{BASE_URL}{path}", params=params)
    r.raise_for_status()
    return r.json()

def api_put(path, body):
    r = requests.put(
        f"{BASE_URL}{path}",
        params={"api_token": API_TOKEN},
        json=body
    )
    if not r.ok:
        print("FAILED UPDATE")
        print("Status:", r.status_code)
        print("Response:", r.text)
        raise SystemExit(1)
    return r.json()

def find_job_field_key():
    data = api_get("/dealFields")
    fields = data.get("data") or []

    for field in fields:
        if field.get("name", "").strip().lower() == JOB_FIELD_NAME.strip().lower():
            print(f"Found field: {field.get('name')} | key: {field.get('key')}")
            return field.get("key")

    print(f"Could not find deal field named: {JOB_FIELD_NAME}")
    print("Available deal fields:")
    for field in fields:
        print("-", field.get("name"))
    raise SystemExit(1)

def extract_number(value):
    if not value:
        return None
    match = re.search(r"SB-(\d+)", str(value))
    return int(match.group(1)) if match else None

def get_all_deals():
    all_deals = []
    start = 0
    limit = 100

    while True:
        data = api_get("/deals", {
            "start": start,
            "limit": limit,
            "sort": "add_time ASC"
        })

        deals = data.get("data") or []
        all_deals.extend(deals)

        pagination = data.get("additional_data", {}).get("pagination", {})
        if not pagination.get("more_items_in_collection"):
            break

        start = pagination.get("next_start")

    return all_deals

job_field_key = find_job_field_key()
deals = get_all_deals()

print(f"Found {len(deals)} open/won/lost deals")

used_numbers = []

for deal in deals:
    current = deal.get(job_field_key)
    number = extract_number(current)
    if number is not None:
        used_numbers.append(number)

next_number = max(used_numbers) + 1 if used_numbers else START_NUMBER

print(f"Next available job number: {PREFIX}{next_number}")

for deal in deals:
    deal_id = deal["id"]
    title = deal.get("title", "")
    current = deal.get(job_field_key)

    if extract_number(current) is not None:
        print(f"Skipped {deal_id} | {title} — already has {current}")
        continue

    new_job_number = f"{PREFIX}{next_number}"

    api_put(f"/deals/{deal_id}", {
        job_field_key: new_job_number
    })

    print(f"Updated {deal_id} | {title} → {new_job_number}")
    next_number += 1
