import os
import requests
import json
import re
from dotenv import load_dotenv

# Import handle_note_info to test normalization
import sys
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
from xhs_utils.data_util import handle_note_info

def debug_note_html(note_url):
    load_dotenv()
    cookies_str = os.getenv("COOKIES")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://www.xiaohongshu.com/"
    }
    
    cookies = {}
    if cookies_str:
        for pair in cookies_str.split(';'):
            if '=' in pair:
                name, value = pair.strip().split('=', 1)
                cookies[name] = value

    print(f"Fetching {note_url}...")
    response = requests.get(note_url, headers=headers, cookies=cookies)
    html = response.text
    
    print(f"Status Code: {response.status_code}")
    print(f"HTML Length: {len(html)}")
    
    if "验证码" in html or "captcha" in html.lower():
        print("ALERT: HTML contains CAPTCHA or Verification message!")
        print(html[:1000])
        return

    start_idx = html.find("window.__INITIAL_STATE__=")
    if start_idx == -1:
        print("ERROR: window.__INITIAL_STATE__ not found in HTML!")
        print("HTML snippet around where it should be:")
        # Look for scripts
        scripts = re.findall(r'<script.*?>.*?</script>', html, re.DOTALL)
        for i, s in enumerate(scripts[:10]):
            print(f"Script {i}: {s[:200]}...")
        return

    start_brace = html.find("{", start_idx)
    count = 0
    end_brace = -1
    for i in range(start_brace, len(html)):
        if html[i] == '{':
            count += 1
        elif html[i] == '}':
            count -= 1
            if count == 0:
                end_brace = i + 1
                break
    
    if end_brace == -1:
        print("ERROR: End brace for INITIAL_STATE not found!")
        return

    json_str = html[start_brace:end_brace]
    json_str = json_str.replace("undefined", "null")
    try:
        data = json.loads(json_str)
        print("INITIAL_STATE JSON loaded successfully.")
        
        # Inspect structure
        if 'note' in data:
            note_data = data['note']
            print(f"Note context keys: {list(note_data.keys())}")
            if 'noteDetailMap' in note_data:
                detail_map = note_data['noteDetailMap']
                print(f"noteDetailMap keys: {list(detail_map.keys())}")
                for k, v in detail_map.items():
                    print(f"Key: {k}, Content snippet: {str(v)[:200]}...")
            else:
                print("noteDetailMap NOT found in 'note'!")
        else:
            print("'note' NOT found in INITIAL_STATE!")
            print(f"Top level keys: {list(data.keys())}")
            
    except Exception as e:
        print(f"JSON Parse Error: {e}")
        print(f"JSON String preview: {json_str[:500]}...")

if __name__ == "__main__":
    # Test one of the failing URLs
    test_url = "https://www.xiaohongshu.com/explore/695c674800000000210331d2"
    debug_note_html(test_url)
