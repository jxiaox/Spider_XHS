
import os
import requests
import json
import time
from dotenv import load_dotenv
from xhs_utils.xhs_util import generate_request_params, splice_str

load_dotenv()
COOKIES = os.getenv("COOKIES")

def test_api(user_id, cursor, xsec_token="", xsec_source="pc_user"):
    base_url = "https://edith.xiaohongshu.com"
    api = "/api/sns/web/v1/user_posted"
    params = {
        "num": "30",
        "cursor": cursor,
        "user_id": user_id,
        "image_formats": "jpg,webp,avif",
        "xsec_token": xsec_token,
        "xsec_source": xsec_source,
    }
    splice_api = splice_str(api, params)
    print(f"URL: {splice_api}")
    
    headers, cookies, data = generate_request_params(COOKIES, splice_api, '', 'GET')
    
    print("Headers:", {k: v for k, v in headers.items() if k.lower() != 'cookie'})
    
    response = requests.get(base_url + splice_api, headers=headers, cookies=cookies)
    print("Status Code:", response.status_code)
    try:
        res_json = response.json()
        print("Response Keys:", res_json.keys())
        print("Data Keys:", res_json.get('data', {}).keys())
        if 'notes' in res_json.get('data', {}):
             print(f"Found {len(res_json['data']['notes'])} notes")
        else:
             print("Full Response Data:", json.dumps(res_json.get('data', {}), ensure_ascii=False))
    except Exception as e:
        print("Error parsing JSON:", e)
        print("Raw Response:", response.text[:500])

if __name__ == "__main__":
    user_id = "5b6150c56b58b741e26b8c7f"
    # Cursor from the logs
    cursor = "69745c9500000000210322e3"
    
    print("--- Testing with pc_user ---")
    test_api(user_id, cursor, xsec_source="pc_user")
    
    time.sleep(2)
    print("\n--- Testing with pc_search ---")
    test_api(user_id, cursor, xsec_source="pc_search")
