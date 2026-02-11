from xhs_utils.common_util import init
from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.cookie_util import trans_cookies
import json

print("Initializing...")
cookies_str, _ = init()
print(f"Loaded Cookies Length: {len(cookies_str)}")
print(f"First 50 chars: {cookies_str[:50]}")

try:
    print("Parsing cookies...")
    cookies_dict = trans_cookies(cookies_str)
    print("Parsed keys:", list(cookies_dict.keys()))
    if 'a1' not in cookies_dict:
        print("ERROR: 'a1' cookie missing!")
    if 'webId' not in cookies_dict:
        print("WARNING: 'webId' cookie missing!")
except Exception as e:
    print(f"Cookie parsing failed: {e}")

api = XHS_Apis()
user_url = "https://www.xiaohongshu.com/user/profile/5b6150c56b58b741e26b8c7f"

print(f"\nTesting get_user_all_notes for: {user_url}")
success, msg, res = api.get_user_all_notes(user_url, cookies_str)

print(f"Success: {success}")
print(f"Msg: {msg}")
if not success:
    print("Detailed debug might be needed in apis/xhs_pc_apis.py")
