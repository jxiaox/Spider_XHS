# -*- coding: utf-8 -*-
from main import Data_Spider

from xhs_utils.common_util import init
import os

# Initialize environment (loads cookies from .env)
cookies_str, base_path = init()

# Initialize Spider
data_spider = Data_Spider()

# Target Profile: 还是叫吴富贵吧
user_url = 'https://www.xiaohongshu.com/user/profile/5b6150c56b58b741e26b8c7f'

print(f"Starting scrape for user: {user_url}")
print(f"Output directory: {base_path}")

# Run scraping
# save_choice='all' saves info, images, and video
data_spider.spider_user_all_note(user_url, cookies_str, base_path, 'all')
