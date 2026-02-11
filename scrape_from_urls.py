
# -*- coding: utf-8 -*-
from main import Data_Spider
from xhs_utils.common_util import init
import os
import re

def scrape_from_file(url_file, batch_size=1000):
    cookies_str, base_path = init()
    data_spider = Data_Spider()
    
    if not os.path.exists(url_file):
        print(f"Error: {url_file} does not exist.")
        return

    with open(url_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"Total URLs found: {len(urls)}")
    
    # Process in batches
    for i in range(0, len(urls), batch_size):
        batch = urls[i : i + batch_size]
        print(f"\n--- Processing Batch {i//batch_size + 1} ({len(batch)} notes) ---")
        
        # Use the specific user ID for the Excel filename to keep consistency
        excel_name = "5b6150c56b58b741e26b8c7f" 
        
        data_spider.spider_some_note(batch, cookies_str, base_path, 'all', excel_name)

if __name__ == "__main__":
    url_file = "/Users/jxiaox/Investment/Spider_XHS/collected_urls.txt"
    scrape_from_file(url_file)
