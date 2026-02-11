import os
import requests
import json
import re
from dotenv import load_dotenv

def debug_profile_html(user_url):
    load_dotenv()
    cookies_str = os.getenv("COOKIES")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.xiaohongshu.com/"
    }
    
    cookies = {}
    if cookies_str:
        for pair in cookies_str.split(';'):
            if '=' in pair:
                name, value = pair.strip().split('=', 1)
                cookies[name] = value

    print(f"Fetching {user_url}...")
    response = requests.get(user_url, headers=headers, cookies=cookies)
    html = response.text
    
    start_idx = html.find("window.__INITIAL_STATE__=")
    if start_idx == -1:
        print("ERROR: window.__INITIAL_STATE__ not found!")
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
    
    json_str = html[start_brace:end_brace]
    json_str = json_str.replace("undefined", "null")
    try:
        data = json.loads(json_str)
        print("Profile INITIAL_STATE loaded.")
        
        # Look for notes and tokens
        if 'user' in data and 'notes' in data['user']:
           notes_list = data['user']['notes']
           # notes_list is likely a list of lists since the error was 'list' object has no attribute 'get'
           # Let's check the first item
           print(f"Notes structure type: {type(notes_list)}")
           if len(notes_list) > 0:
               print(f"First note type: {type(notes_list[0])}")
               # If it's a list, it might be nested
               if isinstance(notes_list[0], list):
                   notes = notes_list[0]
               else:
                   notes = notes_list
               
               print(f"Processing {len(notes)} notes...")
               for i, note in enumerate(notes[:5]):
                   if isinstance(note, dict):
                       n_id = note.get('id') or note.get('noteId')
                       token = note.get('xsecToken')
                       print(f"Note {i}: ID={n_id}, xsecToken={token}")
                   else:
                       print(f"Note {i} is not a dict: {type(note)}")
        else:
            print("Notes not found in data['user']. Keys: ", data.get('user', {}).keys())
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    user_url = "https://www.xiaohongshu.com/user/profile/5b6150c56b58b741e26b8c7f"
    debug_profile_html(user_url)
