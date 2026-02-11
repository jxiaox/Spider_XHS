import requests
import re
from xhs_utils.common_util import init

def get_token():
    cookies_str, base_path = init()
    url = "https://www.xiaohongshu.com/user/profile/5b6150c56b58b741e26b8c7f"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "Cookie": cookies_str
    }
    
    try:
        resp = requests.get(url, headers=headers)
        print(f"Status: {resp.status_code}")
        
        with open("profile_debug.html", "w", encoding="utf-8") as f:
            f.write(resp.text)
        print("Saved HTML to profile_debug.html")

        # Search for xsec_token in text
        match = re.search(r'xsec_token":"([^"]+)"', resp.text)
        if match:
            print(f"Found xsec_token: {match.group(1)}")
        else:
            print("xsec_token not found in HTML regex")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_token()
