import os
import requests

API_TOKEN = os.environ["PIPEDRIVE_API_TOKEN"]
COMPANY_DOMAIN = os.environ["PIPEDRIVE_COMPANY_DOMAIN"]

BASE_URL = f"https://{COMPANY_DOMAIN}.pipedrive.com/api/v1"

response = requests.get(
    f"{BASE_URL}/dealFields",
    params={"api_token": API_TOKEN}
)

response.raise_for_status()

fields = response.json()["data"]

print("===== DEAL FIELDS =====")

for field in fields:
    print(
        f'Name: {field.get("name")} | '
        f'Key: {field.get("key")} | '
        f'Type: {field.get("field_type")}'
    )
