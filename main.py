import json
import os
import time
import random
import sys
from loguru import logger
from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import init
from xhs_utils.data_util import handle_note_info, download_note, save_to_xlsx, get_scraped_note_ids


class Data_Spider():
    def __init__(self):
        self.xhs_apis = XHS_Apis()
        self.stop_id_set = set() # Initialize stop_id_set
        self.throttle_min = 220
        self.throttle_max = 240

    def spider_note(self, note_url: str, cookies_str: str, proxies=None):
        """
        爬取一个笔记的信息
        """
        note_info = None
        try:
            success, msg, note_info = self.xhs_apis.get_note_info(note_url, cookies_str, proxies)
            
            # Fallback to HTML if API fails or empty
            if not success or (success and ('data' not in note_info or 'items' not in note_info['data'] or len(note_info['data']['items']) == 0)):
                logger.warning(f"API failed/empty for {note_url}, trying HTML fallback...")
                try:
                    import urllib.parse
                    parsed = urllib.parse.urlparse(note_url)
                    # path might be /explore/id or /discovery/item/id
                    path_parts = parsed.path.split('/')
                    note_id = path_parts[-1]
                    
                    f_success, f_msg, f_info = self.xhs_apis.get_note_info_from_html(note_id, note_url, cookies_str, proxies)
                    if f_success:
                        success = True
                        note_info = f_info
                        msg = "Recovered from HTML"
                        logger.info(f"HTML Fallback successful for {note_id}")
                    else:
                        logger.error(f"HTML Fallback failed: {f_msg}")
                except Exception as e:
                    logger.error(f"Fallback exception: {e}")

            if success:
                try:
                    if 'data' in note_info and 'items' in note_info['data'] and len(note_info['data']['items']) > 0:
                        note_info = note_info['data']['items'][0]
                        note_info['url'] = note_url
                        note_info = handle_note_info(note_info)
                    else:
                        success = False
                        msg = "No items found in response"
                except Exception as e:
                    success = False
                    msg = f"Error parsing items: {e}"
        except Exception as e:
            success = False
            msg = e
        logger.info(f'爬取笔记信息 {note_url}: {success}, msg: {msg}')
        return success, msg, note_info

    def spider_some_note(self, notes: list, cookies_str: str, base_path: dict, save_choice: str, excel_name: str = '', proxies=None):
        """
        爬取一些笔记的信息
        :param notes:
        :param cookies_str:
        :param base_path:
        :return:
        """
        if (save_choice == 'all' or save_choice == 'excel') and excel_name == '':
            raise ValueError('excel_name 不能为空')
        note_list = []
        buffer_list = []
        file_path = ""
        if save_choice == 'all' or save_choice == 'excel':
            file_path = os.path.abspath(os.path.join(base_path['excel'], f'{excel_name}.xlsx'))
        
        scraped_ids = set()
        if os.path.exists(file_path):
             scraped_ids = get_scraped_note_ids(file_path)
             
        for txt_file in ["scraped_urls.txt", "deleted_urls.txt"]:
            txt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), txt_file)
            if os.path.exists(txt_path):
                with open(txt_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if '/explore/' in line:
                            try:
                                nid = line.split('/explore/')[1].split('?')[0]
                                scraped_ids.add(nid)
                            except: pass

        logger.info(f"Found {len(scraped_ids)} already scraped or deleted notes to skip.")

        total_notes = len(notes)
        for index, note_url in enumerate(notes, 1):
            logger.info(f"Progress: [{index}/{total_notes}] Processing note...")
            # Extract note_id from url
            note_id = note_url.split('/explore/')[-1].split('?')[0]
            if note_id in scraped_ids:
                logger.info(f"Skipping already scraped note: {note_id}")
                continue

            retries = 3
            success_overall = False
            while retries > 0:
                success, msg, note_info = self.spider_note(note_url, cookies_str, proxies)
                if success and note_info is not None:
                    note_list.append(note_info)
                    buffer_list.append(note_info)
                    
                    # Log Title and Time
                    try:
                        title = note_info.get('title', 'No Title')
                        readable_time = note_info.get('upload_time', 'Unknown Time')
                        logger.info(f"Scraped Note: 【{title}】 Upload Time: {readable_time}")
                    except Exception as e:
                        logger.warning(f"Failed to log details: {e}")

                    # Incremental download media
                    if save_choice == 'all' or 'media' in save_choice:
                        download_note(note_info, base_path['media'], save_choice)
                    
                    # Immediate Save to Excel
                    if (save_choice == 'all' or save_choice == 'excel'):
                         save_to_xlsx([note_info], file_path)
                    
                    # Record successful scrape
                    scraped_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scraped_urls.txt")
                    with open(scraped_log_path, "a", encoding="utf-8") as f:
                        f.write(f"{note_url}\n")
                    
                    success_overall = True
                    break # Break from retry loop on success
                elif "登录已过期" in str(msg):
                    logger.error(f"Login expired! Scraper stopping. Msg: {msg}")
                    sys.exit(1)
                elif "访问频次异常" in str(msg):
                    logger.warning(f"Frequency limit hit. Sleeping 900s. Retries left: {retries}")
                    time.sleep(900)
                    retries -= 1
                elif "异常" in str(msg) or "300013" in str(msg):
                    logger.warning(f"Rate limit hit. Sleeping 45s. Retries left: {retries}")
                    time.sleep(45 + random.uniform(1, 10))
                    retries -= 1
                else:
                    retries -= 1
                    logger.warning(f"Failed to scrape note {note_url}. Retrying... ({retries} left). Msg: {msg}")
                    time.sleep(self.throttle_min)
            
            if not success_overall:
                failed_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "failed_urls.txt")
                with open(failed_log_path, "a", encoding="utf-8") as f:
                    f.write(f"{note_url}\n")
                logger.error(f"Note failed all retries. Recorded in {failed_log_path}: {note_url}")
            
            # Sleep after processing each note (or after failed retries)
            random_sleep = random.uniform(self.throttle_min, self.throttle_max)
            logger.info(f"Sleeping {random_sleep:.2f}s...")
            time.sleep(random_sleep)
        
        # Save remaining buffer
        if (save_choice == 'all' or save_choice == 'excel') and buffer_list:
            save_to_xlsx(buffer_list, file_path)


    def spider_from_file(self, file_path, cookies_str, base_path, proxies=None):
        """
        New Entry Point: Scrape notes specifically from a local file containing URLs.
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return

        logger.info(f"Loading URLs from {file_path}...")
        all_note_info = []
        with open(file_path, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        for url in urls:
            try:
                if '/explore/' not in url:
                    continue
                note_id = url.split('/explore/')[1].split('?')[0]
                params = url.split('?')[1].split('&')
                xsec_token = ""
                for p in params:
                    if p.startswith('xsec_token='):
                        xsec_token = p.split('=')[1]
                        break
                
                all_note_info.append({
                    'note_id': note_id,
                    'note_url': url,
                    'xsec_token': xsec_token,
                    'xsec_source': 'pc_user'
                })
            except Exception as e:
                logger.warning(f"Failed to parse URL {url}: {e}")
        
        logger.info(f"Loaded {len(all_note_info)} notes from local file.")
        
        # Build Skip List
        scraped_ids = set()
        user_id = "5b6150c56b58b741e26b8c7f" # Hardcoded for this specific user/task context
        excel_path = os.path.join(base_path['excel'], f'{user_id}.xlsx')
        
        if os.path.exists(excel_path):
             scraped_ids = get_scraped_note_ids(excel_path)

        # Check scraped_urls.txt and deleted_urls.txt
        for txt_file in ["scraped_urls.txt", "deleted_urls.txt"]:
            txt_path = os.path.abspath(os.path.join(base_path['excel'], f"../../{txt_file}")) 
            if os.path.exists(txt_path):
                with open(txt_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if '/explore/' in line:
                             try:
                                nid = line.split('/explore/')[1].split('?')[0]
                                scraped_ids.add(nid)
                             except: pass
        
        logger.info(f"Total Skippable Notes: {len(scraped_ids)}")

        for simple_note_info in all_note_info:
            if simple_note_info.get('type') == 'video':
                continue
                
            note_id = simple_note_info['note_id']
            if note_id in scraped_ids:
                # logger.info(f"Skipping already scraped note: {note_id}")
                continue
            
            # Using spider_some_note which expects a list of URLs
            # But wait, spider_some_note iterates and calls spider_note.
            # We can construct the URL list to pass to it.
            # However, spider_some_note also does some logging.
            # Let's just construct the list of URLs to process.
            
            target_url = simple_note_info['note_url']
            # Pass single note to verify one by one? 
            # spider_some_note takes a list. Let's pass a list of 1 to keep flow control here?
            # Or pass the whole remaining list. Passing whole list is better for the loop inside spider_some_note.
            pass

        # Filter note_list to only process unsaved ones
        final_note_urls = []
        for info in all_note_info:
             if info['note_id'] not in scraped_ids and info.get('type') != 'video':
                  final_note_urls.append(info['note_url'])
        
        logger.info(f"Remaining Notes to Scrape: {len(final_note_urls)}")
        
        # Call the existing method to scrape the list
        # spider_some_note(self, note_list: list, cookies_str: str, base_path: dict, save_choice: str, excel_name: str = '', proxies=None)
        self.spider_some_note(final_note_urls, cookies_str, base_path, 'all', str(user_id), proxies)


    def spider_user_all_note(self, user_url: str, cookies_str: str, base_path: dict, save_choice: str, excel_name: str = '', proxies=None):
        """
        爬取一个用户的所有笔记
        :param user_url:
        :param cookies_str:
        :param base_path:
        :return:
        """
        note_list = []
        try:
            # Determine excel path and read existing IDs
            if save_choice == 'all' or save_choice == 'excel':
                if excel_name == '':
                    excel_name = user_url.split('/')[-1].split('?')[0]
                file_path = os.path.abspath(os.path.join(base_path['excel'], f'{excel_name}.xlsx'))
            
            scraped_ids = set()
            if os.path.exists(file_path):
                 scraped_ids = get_scraped_note_ids(file_path)

            # Also load from scraped_urls.txt and deleted_urls.txt if exists (for double safety)
            for txt_file in ["scraped_urls.txt", "deleted_urls.txt"]:
                txt_path = os.path.abspath(os.path.join(base_path['excel'], f"../../{txt_file}")) 
                if os.path.exists(txt_path):
                    with open(txt_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if not line: continue
                            # Format: https://www.xiaohongshu.com/explore/<note_id>?...
                            try:
                                if '/explore/' in line:
                                    nid = line.split('/explore/')[1].split('?')[0]
                                    scraped_ids.add(nid)
                            except:
                                pass
            
            logger.info(f"Total Skippable Notes (Excel + Txt): {len(scraped_ids)}")

            # Try to load from collected_urls.txt first
            collected_urls_path = os.path.join(os.path.dirname(file_path), "../../collected_urls.txt")
            collected_urls_path = os.path.abspath(collected_urls_path)
            
            all_note_info = []
            if os.path.exists(collected_urls_path):
                logger.info(f"Loading URLs from {collected_urls_path}...")
                with open(collected_urls_path, 'r', encoding='utf-8') as f:
                    urls = [line.strip() for line in f if line.strip()]
                
                for url in urls:
                    try:
                        # Parse note_id and xsec_token from URL
                        # Format: https://www.xiaohongshu.com/explore/<note_id>?xsec_token=<token>&xsec_source=pc_user
                        note_id = url.split('/explore/')[1].split('?')[0]
                        params = url.split('?')[1].split('&')
                        xsec_token = ""
                        for p in params:
                            if p.startswith('xsec_token='):
                                xsec_token = p.split('=')[1]
                                break
                        
                        all_note_info.append({
                            'note_id': note_id,
                            'note_url': url,
                            'xsec_token': xsec_token,
                            'xsec_source': 'pc_user'
                        })
                    except Exception as e:
                        logger.warning(f"Failed to parse URL {url}: {e}")
                
                logger.info(f"Loaded {len(all_note_info)} notes from local file.")
                success = True
            else:
                # Fallback to API if file missing
                logger.info("Local URLs file not found, falling back to API fetch...")
                # Pass None to force deep scrape (diable early termination in API)
                success, msg, all_note_info = self.xhs_apis.get_user_all_notes(user_url, cookies_str, proxies, stop_id_set=None)
            
            if success:
                logger.info(f'用户 {user_url} 作品数量: {len(all_note_info)}')
                for simple_note_info in all_note_info:
                    # Skip video notes as requested by user
                    if simple_note_info.get('type') == 'video':
                        # logger.info(f"Skipping video note: {simple_note_info['note_id']}")
                        continue
                        
                    note_url = f"https://www.xiaohongshu.com/explore/{simple_note_info['note_id']}?xsec_token={simple_note_info['xsec_token']}&xsec_source=pc_user"
                    note_list.append(note_url)
            self.spider_some_note(note_list, cookies_str, base_path, save_choice, excel_name, proxies)
        except Exception as e:
            success = False
            msg = e
        logger.info(f'爬取用户所有视频 {user_url}: {success}, msg: {msg}')
        return note_list, success, msg

    def spider_some_search_note(self, query: str, require_num: int, cookies_str: str, base_path: dict, save_choice: str, sort_type_choice=0, note_type=0, note_time=0, note_range=0, pos_distance=0, geo: dict = None,  excel_name: str = '', proxies=None):
        """
            指定数量搜索笔记，设置排序方式和笔记类型和笔记数量
            :param query 搜索的关键词
            :param require_num 搜索的数量
            :param cookies_str 你的cookies
            :param base_path 保存路径
            :param sort_type_choice 排序方式 0 综合排序, 1 最新, 2 最多点赞, 3 最多评论, 4 最多收藏
            :param note_type 笔记类型 0 不限, 1 视频笔记, 2 普通笔记
            :param note_time 笔记时间 0 不限, 1 一天内, 2 一周内天, 3 半年内
            :param note_range 笔记范围 0 不限, 1 已看过, 2 未看过, 3 已关注
            :param pos_distance 位置距离 0 不限, 1 同城, 2 附近 指定这个必须要指定 geo
            返回搜索的结果
        """
        note_list = []
        try:
            success, msg, notes = self.xhs_apis.search_some_note(query, require_num, cookies_str, sort_type_choice, note_type, note_time, note_range, pos_distance, geo, proxies)
            if success:
                notes = list(filter(lambda x: x['model_type'] == "note", notes))
                logger.info(f'搜索关键词 {query} 笔记数量: {len(notes)}')
                for note in notes:
                    note_url = f"https://www.xiaohongshu.com/explore/{note['id']}?xsec_token={note['xsec_token']}"
                    note_list.append(note_url)
            if save_choice == 'all' or save_choice == 'excel':
                excel_name = query
            self.spider_some_note(note_list, cookies_str, base_path, save_choice, excel_name, proxies)
        except Exception as e:
            success = False
            msg = e
        logger.info(f'搜索关键词 {query} 笔记: {success}, msg: {msg}')
        return note_list, success, msg

if __name__ == '__main__':

    cookies_str, base_path = init()
    data_spider = Data_Spider()


    # 1 爬取列表的所有笔记信息 笔记链接 如下所示 注意此url会过期！
    notes = [
        r'https://www.xiaohongshu.com/explore/683fe17f0000000023017c6a?xsec_token=ABBr_cMzallQeLyKSRdPk9fwzA0torkbT_ubuQP1ayvKA=&xsec_source=pc_user',
        r'https://www.xiaohongshu.com/explore/6846cbe700000000030393c0?xsec_token=ABsh2hg0nLYfcnruza3Gx_BPJQWqc-k7ys6Fs43N-x638=&xsec_source=pc_user' # Should be skipped
    ]
    data_spider.spider_some_note(notes, cookies_str, base_path, 'all', 'test')

    # 2 爬取用户的所有笔记信息 用户链接 如下所示 注意此url会过期！
    user_url = 'https://www.xiaohongshu.com/user/profile/64c3f392000000002b009e45?xsec_token=AB-GhAToFu07JwNk_AMICHnp7bSTjVz2beVIDBwSyPwvM=&xsec_source=pc_feed'
    data_spider.spider_user_all_note(user_url, cookies_str, base_path, 'all')

    # 3 搜索指定关键词的笔记
    query = "榴莲"
    query_num = 10
    sort_type_choice = 0  # 0 综合排序, 1 最新, 2 最多点赞, 3 最多评论, 4 最多收藏
    note_type = 0 # 0 不限, 1 视频笔记, 2 普通笔记
    note_time = 0  # 0 不限, 1 一天内, 2 一周内天, 3 半年内
    note_range = 0  # 0 不限, 1 已看过, 2 未看过, 3 已关注
    pos_distance = 0  # 0 不限, 1 同城, 2 附近 指定这个1或2必须要指定 geo
    # geo = {
    #     # 经纬度
    #     "latitude": 39.9725,
    #     "longitude": 116.4207
    # }
    data_spider.spider_some_search_note(query, query_num, cookies_str, base_path, 'all', sort_type_choice, note_type, note_time, note_range, pos_distance, geo=None)
