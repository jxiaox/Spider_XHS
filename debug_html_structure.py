import sys
import os
import requests
import re
from dotenv import load_dotenv

sys.path.append("/Users/jxiaox/Investment/Spider_XHS")
from xhs_utils.xhs_util import generate_request_params

load_dotenv()

cookies_str = os.getenv("COOKIES")
note_id = "69781a610000000022023b3d"
note_url = f"https://www.xiaohongshu.com/explore/{note_id}"

headers, _, _ = generate_request_params(cookies_str, note_url, None)

try:
    response = requests.get(note_url, headers=headers)
    html = response.text
    print(f"HTML Length: {len(html)}")
    
    # Check Title Tag
    title_tag = re.search(r'<title>(.*?)</title>', html)
    if title_tag:
        print(f"Title Tag: {title_tag.group(1)}")
    else:
        print("Title Tag Not Found")

    # Check Meta Tags (property or name)
    og_title = re.search(r'<meta [^>]*property="og:title" [^>]*content="([^"]*)"', html)
    if og_title:
        print(f"OG Title: {og_title.group(1)}")
    else:
        print("OG Title Not Found")
    
    og_desc = re.search(r'<meta [^>]*property="og:description" [^>]*content="([^"]*)"', html)
    if og_desc:
         print(f"OG Desc: {og_desc.group(1)}")
    
    # Check for upload time in meta or schema
    date_pub = re.search(r'"datePublished":\s*"([^"]*)"', html)
    if date_pub:
        print(f"Schema Date: {date_pub.group(1)}")
    else:
        print("Schema Date Not Found")
    
    item_publish = re.search(r'<meta [^>]*itemprop="datePublished" [^>]*content="([^"]*)"', html)
    if item_publish:
        print(f"ItemProp Date: {item_publish.group(1)}")
    else:
        print("ItemProp Date Not Found")

    # Check for specific "time" in raw text if simple
    if "time" in html:
        print("Word 'time' found in HTML")
        
except Exception as e:
    print(e)
