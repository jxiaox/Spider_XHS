
import requests
import json
import re
import os
from dotenv import load_dotenv

load_dotenv()
COOKIES = os.getenv("COOKIES")

def inspect_user(user_url):
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'cookie': COOKIES
    }
    res = requests.get(user_url, headers=headers)
    html = res.text
    
    start_pattern = '__INITIAL_STATE__='
    start_index = html.find(start_pattern)
    if start_index == -1:
        print("INITIAL_STATE not found")
        return
        
    start_brace = html.find('{', start_index)
    
    # Simple brace counting to find the end of the JSON object
    brace_count = 0
    end_brace = -1
    for i in range(start_brace, len(html)):
        if html[i] == '{':
            brace_count += 1
        elif html[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end_brace = i + 1
                break
                
    if end_brace == -1:
        print("End brace not found")
        return

    json_str = html[start_brace:end_brace]
    json_str = json_str.replace("undefined", "null")
    data = json.loads(json_str)
    
    print("Keys in INITIAL_STATE:", data.keys())
    if 'user' in data:
        print("Keys in ['user']:", data['user'].keys())
        # Check for user info
        user_info = data['user'].get('userPageData', {})
        print("User Page Data keys:", user_info.keys())
        
        # Look for xsec_token
        # Sometimes it's in userPageData or directly in user
        print("XSec Token in userPageData:", user_info.get('xsecToken'))
        
    # Check noteQueries
    queries = data.get('user', {}).get('noteQueries', [])
    if queries:
        print(f"Found {len(queries)} note queries")
        for i, q in enumerate(queries):
            print(f"Query {i} cursor: {q.get('cursor')}")
            print(f"Query {i} xsecToken: {q.get('xsecToken')}")
            print(f"Query {i} xsecSource: {q.get('xsecSource')}")
            
    # Also check notes
    notes = data.get('user', {}).get('notes', [[]])[0]
    if notes:
        print(f"Found {len(notes)} initial notes")
        for i, note in enumerate(notes[:5]):
            nc = note.get('noteCard', {})
            print(f"Note {i} ID: {note.get('id')} xsecToken: {nc.get('xsecToken')}")
            
    # Also check basicInfo
    basic_info = data.get('user', {}).get('userPageData', {}).get('basicInfo', {})

    print("Basic Info keys:", basic_info.keys())
    print("XSec Token in basicInfo:", basic_info.get('xsecToken'))


if __name__ == "__main__":
    user_url = "https://www.xiaohongshu.com/user/profile/5b6150c56b58b741e26b8c7f"
    inspect_user(user_url)
