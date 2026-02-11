import json
import re
import urllib
import time
import requests
from xhs_utils.xhs_util import splice_str, generate_request_params, generate_x_b3_traceid, get_common_headers
from loguru import logger

"""
    获小红书的api
    :param cookies_str: 你的cookies
"""
class XHS_Apis():
    def __init__(self):
        self.base_url = "https://edith.xiaohongshu.com"

    def get_homefeed_all_channel(self, cookies_str: str, proxies: dict = None):
        """
            获取主页的所有频道
            返回主页的所有频道
        """
        res_json = None
        try:
            api = "/api/sns/web/v1/homefeed/category"
            headers, cookies, data = generate_request_params(cookies_str, api, '', 'GET')
            response = requests.get(self.base_url + api, headers=headers, cookies=cookies, proxies=proxies)
            res_json = response.json()
            success, msg = res_json["success"], res_json["msg"]
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, res_json

    def get_homefeed_recommend(self, category, cursor_score, refresh_type, note_index, cookies_str: str, proxies: dict = None):
        """
            获取主页推荐的笔记
            :param category: 你想要获取的频道
            :param cursor_score: 你想要获取的笔记的cursor
            :param refresh_type: 你想要获取的笔记的刷新类型
            :param note_index: 你想要获取的笔记的index
            :param cookies_str: 你的cookies
            返回主页推荐的笔记
        """
        res_json = None
        try:
            api = f"/api/sns/web/v1/homefeed"
            data = {
                "cursor_score": cursor_score,
                "num": 20,
                "refresh_type": refresh_type,
                "note_index": note_index,
                "unread_begin_note_id": "",
                "unread_end_note_id": "",
                "unread_note_count": 0,
                "category": category,
                "search_key": "",
                "need_num": 10,
                "image_formats": [
                    "jpg",
                    "webp",
                    "avif"
                ],
                "need_filter_image": False
            }
            headers, cookies, trans_data = generate_request_params(cookies_str, api, data, 'POST')
            response = requests.post(self.base_url + api, headers=headers, data=trans_data, cookies=cookies, proxies=proxies)
            res_json = response.json()
            success, msg = res_json["success"], res_json["msg"]
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, res_json

    def get_homefeed_recommend_by_num(self, category, require_num, cookies_str: str, proxies: dict = None):
        """
            根据数量获取主页推荐的笔记
            :param category: 你想要获取的频道
            :param require_num: 你想要获取的笔记的数量
            :param cookies_str: 你的cookies
            根据数量返回主页推荐的笔记
        """
        cursor_score, refresh_type, note_index = "", 1, 0
        note_list = []
        try:
            while True:
                success, msg, res_json = self.get_homefeed_recommend(category, cursor_score, refresh_type, note_index, cookies_str, proxies)
                if not success:
                    raise Exception(msg)
                if "items" not in res_json["data"]:
                    break
                notes = res_json["data"]["items"]
                note_list.extend(notes)
                cursor_score = res_json["data"]["cursor_score"]
                refresh_type = 3
                note_index += 20
                if len(note_list) > require_num:
                    break
        except Exception as e:
            success = False
            msg = str(e)
        if len(note_list) > require_num:
            note_list = note_list[:require_num]
        return success, msg, note_list

    def get_user_info(self, user_id: str, cookies_str: str, proxies: dict = None):
        """
            获取用户的信息
            :param user_id: 你想要获取的用户的id
            :param cookies_str: 你的cookies
            返回用户的信息
        """
        res_json = None
        try:
            api = f"/api/sns/web/v1/user/otherinfo"
            params = {
                "target_user_id": user_id
            }
            splice_api = splice_str(api, params)
            headers, cookies, data = generate_request_params(cookies_str, splice_api, '', 'GET')
            response = requests.get(self.base_url + splice_api, headers=headers, cookies=cookies, proxies=proxies)
            res_json = response.json()
            success, msg = res_json["success"], res_json["msg"]
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, res_json

    def get_user_self_info(self, cookies_str: str, proxies: dict = None):
        """
            获取用户自己的信息1
            :param cookies_str: 你的cookies
            返回用户自己的信息1
        """
        res_json = None
        try:
            api = f"/api/sns/web/v1/user/selfinfo"
            headers, cookies, data = generate_request_params(cookies_str, api, '', 'GET')
            response = requests.get(self.base_url + api, headers=headers, cookies=cookies, proxies=proxies)
            res_json = response.json()
            success, msg = res_json["success"], res_json["msg"]
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, res_json


    def get_initial_notes_from_html(self, user_url, cookies_str, proxies=None):
        try:
            headers, cookies, data = generate_request_params(cookies_str, user_url, '', 'GET')
            response = requests.get(user_url, headers=headers, cookies=cookies, proxies=proxies)
            html = response.text
            
            start_idx = html.find("window.__INITIAL_STATE__=")
            if start_idx == -1:
                return False, "Initial state not found", [], ""
            
            start_brace = html.find("{", start_idx)
            if start_brace == -1:
                return False, "Start brace not found", [], ""

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
                return False, "End brace not found", [], ""

            json_str = html[start_brace:end_brace]
            json_str = json_str.replace("undefined", "null")
            data = json.loads(json_str)
            
            # Extract notes from data['user']['notes'][0]
            notes_raw = data.get('user', {}).get('notes', [[]])[0]
            notes = []
            for item in notes_raw:
                # Normalize to match API structure (flatten noteCard)
                if 'noteCard' in item:
                    note = item['noteCard']
                    # ensure note_id is top level
                    if 'noteId' in note:
                        note['note_id'] = note['noteId']
                    if 'xsecToken' in note:
                        note['xsec_token'] = note['xsecToken']
                    notes.append(note)
                elif 'id' in item:
                     # fallback
                     item['note_id'] = item['id']
                     if 'xsecToken' in item:
                         item['xsec_token'] = item['xsecToken']
                     notes.append(item)

            # Extract cursor from data['user']['noteQueries'][0]['cursor']
            queries = data.get('user', {}).get('noteQueries', [{}])
            cursor = ""
            if queries and len(queries) > 0:
                cursor = queries[0].get('cursor', "")

            return True, "Success", notes, cursor

        except Exception as e:
            return False, str(e), [], ""

    def get_user_self_info2(self, cookies_str: str, proxies: dict = None):
        """
            获取用户自己的信息2
            :param cookies_str: 你的cookies
            返回用户自己的信息2
        """
        res_json = None
        try:
            api = f"/api/sns/web/v2/user/me"
            headers, cookies, data = generate_request_params(cookies_str, api, '', 'GET')
            response = requests.get(self.base_url + api, headers=headers, cookies=cookies, proxies=proxies)
            res_json = response.json()
            success, msg = res_json["success"], res_json["msg"]
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, res_json

    def get_user_note_info(self, user_id: str, cursor: str, cookies_str: str, xsec_token='', xsec_source='', proxies: dict = None):
        """
            获取用户指定位置的笔记
            :param user_id: 你想要获取的用户的id
            :param cursor: 你想要获取的笔记的cursor
            :param cookies_str: 你的cookies
            返回用户指定位置的笔记
        """
        res_json = None
        try:
            api = f"/api/sns/web/v1/user_posted"
            params = {
                "num": "30",
                "cursor": cursor,
                "user_id": user_id,
                "image_formats": "jpg,webp,avif",
                "xsec_token": xsec_token,
                "xsec_source": xsec_source,
            }
            splice_api = splice_str(api, params)
            headers, cookies, data = generate_request_params(cookies_str, splice_api, '', 'GET')
            response = requests.get(self.base_url + splice_api, headers=headers, cookies=cookies, proxies=proxies)
            res_json = response.json()
            success, msg = res_json["success"], res_json["msg"]
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, res_json


    def get_user_all_notes(self, user_url: str, cookies_str: str, proxies: dict = None, stop_id_set: set = None):
        """
           获取用户所有笔记
           :param user_id: 你想要获取的用户的id
           :param cookies_str: 你的cookies
           :param stop_id_set: 已存在的笔记ID集合，遇到其中的ID将停止抓取
           返回用户的所有笔记
        """
        cursor = ''
        note_list = []
        try:
            urlParse = urllib.parse.urlparse(user_url)
            user_id = urlParse.path.split("/")[-1]
            kvDist = {}
            if urlParse.query:
                kvs = urlParse.query.split('&')
                for kv in kvs:
                    parts = kv.split('=')
                    if len(parts) >= 2:
                        kvDist[parts[0]] = parts[1]
            xsec_token = kvDist.get('xsec_token', "")
            xsec_source = kvDist.get('xsec_source', "pc_user") # Default to pc_user for profiles
            page_count = 0
            while True:
                # Try HTML fetch for first page if cursor is empty
                if cursor == "" and page_count == 0:
                    logger.info("Attempting to fetch first page from HTML...")
                    h_success, h_msg, h_notes, h_cursor = self.get_initial_notes_from_html(user_url, cookies_str, proxies)
                    if h_success and len(h_notes) > 0:
                        logger.info(f"Initialized from HTML: {len(h_notes)} notes, Next Cursor: {h_cursor}")
                        note_list.extend(h_notes)
                        cursor = h_cursor
                        page_count += 1
                        # If cursor is empty after HTML fetch, we are done
                        if not cursor:
                            break
                        continue # Skip to next iteration (using API with cursor)
                    else:
                        logger.warning(f"HTML fetch failed or empty: {h_msg}. Falling back to API.")

                # AJAX Retry Logic
                max_retries = 3
                res_json = None
                for attempt in range(max_retries):
                    success, msg, res_json = self.get_user_note_info(user_id, cursor, cookies_str, xsec_token, xsec_source, proxies)
                    if success and res_json and "data" in res_json and "notes" in res_json["data"]:
                        break
                    
                    logger.warning(f"AJAX Attempt {attempt+1} failed or empty. Response: {res_json}. Msg: {msg}")
                    
                    if res_json and res_json.get("msg") == "登录已过期":
                        logger.error("Login expired detected in AJAX. Exiting scraper.")
                        import sys
                        sys.exit(1)

                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 30
                        logger.info(f"Sleeping {wait_time}s before retry...")
                        time.sleep(wait_time)
                
                if not res_json or "data" not in res_json or "notes" not in res_json["data"]:
                    logger.error(f"Failed to fetch notes after {max_retries} attempts. Final Response: {res_json}")
                    # If we already have some notes, just return them instead of crashing
                    if len(note_list) > 0:
                        break
                    raise Exception(f"Invalid response structure. Keys: {res_json.keys() if res_json else 'None'}")

                notes = res_json["data"]["notes"]
                logger.info(f"Fetched page {page_count}. Notes: {len(notes)}, Has More: {res_json['data'].get('has_more', False)}, Cursor: {res_json['data'].get('cursor', 'None')}")
                
                # Check for existing IDs to stop early
                if stop_id_set:
                    new_notes_on_page = []
                    for note in notes:
                        if str(note['note_id']) in stop_id_set:
                            logger.info(f"Skipping existing note {note['note_id']}")
                            continue 
                        new_notes_on_page.append(note)
                    note_list.extend(new_notes_on_page)
                else:
                    note_list.extend(notes)

                if 'cursor' in res_json["data"]:
                    cursor = str(res_json["data"]["cursor"])
                else:
                    break
                
                if len(notes) == 0 or not res_json["data"]["has_more"]:
                    break
                
                # Rate Limiting
                page_count += 1
                if page_count % 10 == 0:
                    logger.info("Fetched 10 pages. Sleeping for 2 minutes (120s)...")
                    time.sleep(120)
                else:
                    logger.info("Sleeping 20s after page fetch...") # Increase to 20s
                    time.sleep(20)
        except Exception as e:
            msg = str(e)
            if len(note_list) > 0:
                success = True
                logger.warning(f"Exception occurred but {len(note_list)} notes were fetched: {msg}")
            else:
                success = False
        return success, msg, note_list

    def get_user_like_note_info(self, user_id: str, cursor: str, cookies_str: str, xsec_token='', xsec_source='', proxies: dict = None):
        """
            获取用户指定位置喜欢的笔记
            :param user_id: 你想要获取的用户的id
            :param cursor: 你想要获取的笔记的cursor
            :param cookies_str: 你的cookies
            返回用户指定位置喜欢的笔记
        """
        res_json = None
        try:
            api = f"/api/sns/web/v1/note/like/page"
            params = {
                "num": "30",
                "cursor": cursor,
                "user_id": user_id,
                "image_formats": "jpg,webp,avif",
                "xsec_token": xsec_token,
                "xsec_source": xsec_source,
            }
            splice_api = splice_str(api, params)
            headers, cookies, data = generate_request_params(cookies_str, splice_api, '', 'GET')
            response = requests.get(self.base_url + splice_api, headers=headers, cookies=cookies, proxies=proxies)
            res_json = response.json()
            success, msg = res_json["success"], res_json["msg"]
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, res_json

    def get_user_all_like_note_info(self, user_url: str, cookies_str: str, proxies: dict = None):
        """
            获取用户所有喜欢笔记
            :param user_id: 你想要获取的用户的id
            :param cookies_str: 你的cookies
            返回用户的所有喜欢笔记
        """
        cursor = ''
        note_list = []
        try:
            urlParse = urllib.parse.urlparse(user_url)
            user_id = urlParse.path.split("/")[-1]
            kvs = urlParse.query.split('&')
            kvDist = {kv.split('=')[0]: kv.split('=')[1] for kv in kvs}
            xsec_token = kvDist['xsec_token'] if 'xsec_token' in kvDist else ""
            xsec_source = kvDist['xsec_source'] if 'xsec_source' in kvDist else "pc_user"
            while True:
                success, msg, res_json = self.get_user_like_note_info(user_id, cursor, cookies_str, xsec_token,
                                                                      xsec_source, proxies)
                if not success:
                    raise Exception(msg)
                notes = res_json["data"]["notes"]
                if 'cursor' in res_json["data"]:
                    cursor = str(res_json["data"]["cursor"])
                else:
                    break
                note_list.extend(notes)
                if len(notes) == 0 or not res_json["data"]["has_more"]:
                    break
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, note_list

    def get_user_collect_note_info(self, user_id: str, cursor: str, cookies_str: str, xsec_token='', xsec_source='', proxies: dict = None):
        """
            获取用户指定位置收藏的笔记
            :param user_id: 你想要获取的用户的id
            :param cursor: 你想要获取的笔记的cursor
            :param cookies_str: 你的cookies
            返回用户指定位置收藏的笔记
        """
        res_json = None
        try:
            api = f"/api/sns/web/v2/note/collect/page"
            params = {
                "num": "30",
                "cursor": cursor,
                "user_id": user_id,
                "image_formats": "jpg,webp,avif",
                "xsec_token": xsec_token,
                "xsec_source": xsec_source,
            }
            splice_api = splice_str(api, params)
            headers, cookies, data = generate_request_params(cookies_str, splice_api, '', 'GET')
            response = requests.get(self.base_url + splice_api, headers=headers, cookies=cookies, proxies=proxies)
            res_json = response.json()
            success, msg = res_json["success"], res_json["msg"]
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, res_json

    def get_user_all_collect_note_info(self, user_url: str, cookies_str: str, proxies: dict = None):
        """
            获取用户所有收藏笔记
            :param user_id: 你想要获取的用户的id
            :param cookies_str: 你的cookies
            返回用户的所有收藏笔记
        """
        cursor = ''
        note_list = []
        try:
            urlParse = urllib.parse.urlparse(user_url)
            user_id = urlParse.path.split("/")[-1]
            kvs = urlParse.query.split('&')
            kvDist = {kv.split('=')[0]: kv.split('=')[1] for kv in kvs}
            xsec_token = kvDist['xsec_token'] if 'xsec_token' in kvDist else ""
            xsec_source = kvDist['xsec_source'] if 'xsec_source' in kvDist else "pc_search"
            while True:
                success, msg, res_json = self.get_user_collect_note_info(user_id, cursor, cookies_str, xsec_token,
                                                                         xsec_source, proxies)
                if not success:
                    raise Exception(msg)
                notes = res_json["data"]["notes"]
                if 'cursor' in res_json["data"]:
                    cursor = str(res_json["data"]["cursor"])
                else:
                    break
                note_list.extend(notes)
                if len(notes) == 0 or not res_json["data"]["has_more"]:
                    break
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, note_list

    def get_note_info(self, url: str, cookies_str: str, proxies: dict = None):
        """
            获取笔记的详细
            :param url: 你想要获取的笔记的url
            :param cookies_str: 你的cookies
            :param xsec_source: 你的xsec_source 默认为pc_search pc_user pc_feed
            返回笔记的详细
        """
        res_json = None
        try:
            urlParse = urllib.parse.urlparse(url)
            note_id = urlParse.path.split("/")[-1]
            kvDist = {}
            if urlParse.query:
                kvs = urlParse.query.split('&')
                for kv in kvs:
                    parts = kv.split('=')
                    if len(parts) >= 2:
                        kvDist[parts[0]] = parts[1]
            api = f"/api/sns/web/v1/feed"
            data = {
                "source_note_id": note_id,
                "image_formats": [
                    "jpg",
                    "webp",
                    "avif"
                ],
                "extra": {
                    "need_body_topic": "1"
                },
                "xsec_source": kvDist.get('xsec_source', "pc_search"),
                "xsec_token": kvDist.get('xsec_token')
            }
            headers, cookies, data = generate_request_params(cookies_str, api, data, 'POST')
            response = requests.post(self.base_url + api, headers=headers, data=data, cookies=cookies, proxies=proxies)
            res_json = response.json()
            if res_json.get("code") == 300013 or "异常" in res_json.get("msg", ""):
                success = False
            else:
                success = res_json.get("success", False)
            msg = res_json.get("msg", "")
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, res_json


    def get_note_info_from_html(self, note_id: str, note_url: str, cookies_str: str, proxies: dict = None):
        """
        Fallback: Get note detail from HTML parsing with data normalization
        """
        try:
            headers, cookies, data = generate_request_params(cookies_str, note_url, '', 'GET')
            headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            
            response = requests.get(note_url, headers=headers, cookies=cookies, proxies=proxies)
            html = response.text
            
            start_idx = html.find("window.__INITIAL_STATE__=")
            if start_idx == -1:
                return False, "Initial state not found", {}
            
            start_brace = html.find("{", start_idx)
            if start_brace == -1:
                return False, "Start brace not found", {}

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
                return False, "End brace not found", {}

            json_str = html[start_brace:end_brace]
            json_str = json_str.replace("undefined", "null")
            data = json.loads(json_str)
            
            if 'note' in data and 'noteDetailMap' in data['note']:
                detail_map = data['note']['noteDetailMap']
                
                # Try exact match first, then fallback to first available item
                if note_id in detail_map:
                    note_wrapper = detail_map[note_id]
                elif len(detail_map) > 0:
                    # Fallback: take the first available item in the map
                    # This handles cases where the key is 'null' or mismatched
                    first_key = list(detail_map.keys())[0]
                    note_wrapper = detail_map[first_key]
                else:
                    return False, "Note map empty", {}

                if 'note' in note_wrapper:
                    raw_note = note_wrapper['note']
                else:
                    raw_note = note_wrapper
                
                # Check validity
                if not raw_note:
                     return False, "Extracted note data is empty", {}

                # Construct note_card matching handle_note_info expectations
                note_card = {}
                note_card['type'] = raw_note.get('type', 'normal')
                note_card['title'] = raw_note.get('title', '无标题')
                note_card['desc'] = raw_note.get('desc', '')
                note_card['time'] = raw_note.get('time', raw_note.get('lastUpdateTime', 0))
                note_card['last_update_time'] = raw_note.get('lastUpdateTime', 0)
                note_card['ip_location'] = raw_note.get('ipLocation', '未知')

                # User
                raw_user = raw_note.get('user', {})
                note_card['user'] = {
                    'user_id': raw_user.get('userId', ''),
                    'nickname': raw_user.get('nickname', ''),
                    'avatar': raw_user.get('avatar', ''),
                }

                # Interact Info
                raw_interact = raw_note.get('interactInfo', {})
                note_card['interact_info'] = {
                    'liked_count': raw_interact.get('likedCount', '0'),
                    'collected_count': raw_interact.get('collectedCount', '0'),
                    'comment_count': raw_interact.get('commentCount', '0'),
                    'share_count': raw_interact.get('shareCount', '0'),
                }

                # Image List - map to [{'info_list': [..., {'url': ...}]}]
                raw_images = raw_note.get('imageList', [])
                image_list = []
                for img in raw_images:
                    # Assuming structure matches generic logic or simplified
                    url = img.get('urlDefault', img.get('url', ''))
                    if url:
                            # Mock the info_list[1]['url'] structure
                            image_list.append({'info_list': [{}, {'url': url}]})
                note_card['image_list'] = image_list

                # Video - map to {'consumer': {'origin_video_key': ...}}
                if 'video' in raw_note:
                    raw_video = raw_note['video']
                    consumer = raw_video.get('consumer', {})
                    if 'originVideoKey' in consumer:
                        consumer['origin_video_key'] = consumer['originVideoKey']
                    note_card['video'] = {'consumer': consumer}

                # Tag List
                raw_tags = raw_note.get('tagList', [])
                note_card['tag_list'] = raw_tags # Assumes [{'name': '...'}]

                final_data = {
                    'id': raw_note.get('noteId', note_id), # Critical for handle_note_info
                    'note_id': raw_note.get('noteId', note_id),
                    'note_card': note_card
                }
                
                return True, "Success", {'data': {'items': [final_data]}}
            
            return False, "Note not found in HTML map", {}

        except Exception as e:
            return False, str(e), {}


    def get_search_keyword(self, word: str, cookies_str: str, proxies: dict = None):
        """
            获取搜索关键词
            :param word: 你的关键词
            :param cookies_str: 你的cookies
            返回搜索关键词
        """
        res_json = None
        try:
            api = "/api/sns/web/v1/search/recommend"
            params = {
                "keyword": urllib.parse.quote(word)
            }
            splice_api = splice_str(api, params)
            headers, cookies, data = generate_request_params(cookies_str, splice_api, '', 'GET')
            response = requests.get(self.base_url + splice_api, headers=headers, cookies=cookies, proxies=proxies)
            res_json = response.json()
            success, msg = res_json["success"], res_json["msg"]
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, res_json

    def search_note(self, query: str, cookies_str: str, page=1, sort_type_choice=0, note_type=0, note_time=0, note_range=0, pos_distance=0, geo="", proxies: dict = None):
        """
            获取搜索笔记的结果
            :param query 搜索的关键词
            :param cookies_str 你的cookies
            :param page 搜索的页数
            :param sort_type_choice 排序方式 0 综合排序, 1 最新, 2 最多点赞, 3 最多评论, 4 最多收藏
            :param note_type 笔记类型 0 不限, 1 视频笔记, 2 普通笔记
            :param note_time 笔记时间 0 不限, 1 一天内, 2 一周内天, 3 半年内
            :param note_range 笔记范围 0 不限, 1 已看过, 2 未看过, 3 已关注
            :param pos_distance 位置距离 0 不限, 1 同城, 2 附近 指定这个必须要指定 geo
            返回搜索的结果
        """
        res_json = None
        sort_type = "general"
        if sort_type_choice == 1:
            sort_type = "time_descending"
        elif sort_type_choice == 2:
            sort_type = "popularity_descending"
        elif sort_type_choice == 3:
            sort_type = "comment_descending"
        elif sort_type_choice == 4:
            sort_type = "collect_descending"
        filter_note_type = "不限"
        if note_type == 1:
            filter_note_type = "视频笔记"
        elif note_type == 2:
            filter_note_type = "普通笔记"
        filter_note_time = "不限"
        if note_time == 1:
            filter_note_time = "一天内"
        elif note_time == 2:
            filter_note_time = "一周内"
        elif note_time == 3:
            filter_note_time = "半年内"
        filter_note_range = "不限"
        if note_range == 1:
            filter_note_range = "已看过"
        elif note_range == 2:
            filter_note_range = "未看过"
        elif note_range == 3:
            filter_note_range = "已关注"
        filter_pos_distance = "不限"
        if pos_distance == 1:
            filter_pos_distance = "同城"
        elif pos_distance == 2:
            filter_pos_distance = "附近"
        if geo:
            geo = json.dumps(geo, separators=(',', ':'))
        try:
            api = "/api/sns/web/v1/search/notes"
            data = {
                "keyword": query,
                "page": page,
                "page_size": 20,
                "search_id": generate_x_b3_traceid(21),
                "sort": "general",
                "note_type": 0,
                "ext_flags": [],
                "filters": [
                    {
                        "tags": [
                            sort_type
                        ],
                        "type": "sort_type"
                    },
                    {
                        "tags": [
                            filter_note_type
                        ],
                        "type": "filter_note_type"
                    },
                    {
                        "tags": [
                            filter_note_time
                        ],
                        "type": "filter_note_time"
                    },
                    {
                        "tags": [
                            filter_note_range
                        ],
                        "type": "filter_note_range"
                    },
                    {
                        "tags": [
                            filter_pos_distance
                        ],
                        "type": "filter_pos_distance"
                    }
                ],
                "geo": geo,
                "image_formats": [
                    "jpg",
                    "webp",
                    "avif"
                ]
            }
            headers, cookies, data = generate_request_params(cookies_str, api, data, 'POST')
            response = requests.post(self.base_url + api, headers=headers, data=data.encode('utf-8'), cookies=cookies, proxies=proxies)
            res_json = response.json()
            success, msg = res_json["success"], res_json["msg"]
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, res_json

    def search_some_note(self, query: str, require_num: int, cookies_str: str, sort_type_choice=0, note_type=0, note_time=0, note_range=0, pos_distance=0, geo="", proxies: dict = None):
        """
            指定数量搜索笔记，设置排序方式和笔记类型和笔记数量
            :param query 搜索的关键词
            :param require_num 搜索的数量
            :param cookies_str 你的cookies
            :param sort_type_choice 排序方式 0 综合排序, 1 最新, 2 最多点赞, 3 最多评论, 4 最多收藏
            :param note_type 笔记类型 0 不限, 1 视频笔记, 2 普通笔记
            :param note_time 笔记时间 0 不限, 1 一天内, 2 一周内天, 3 半年内
            :param note_range 笔记范围 0 不限, 1 已看过, 2 未看过, 3 已关注
            :param pos_distance 位置距离 0 不限, 1 同城, 2 附近 指定这个必须要指定 geo
            :param geo: 定位信息 经纬度
            返回搜索的结果
        """
        page = 1
        note_list = []
        try:
            while True:
                success, msg, res_json = self.search_note(query, cookies_str, page, sort_type_choice, note_type, note_time, note_range, pos_distance, geo, proxies)
                if not success:
                    raise Exception(msg)
                if "items" not in res_json["data"]:
                    break
                notes = res_json["data"]["items"]
                note_list.extend(notes)
                page += 1
                if len(note_list) >= require_num or not res_json["data"]["has_more"]:
                    break
        except Exception as e:
            success = False
            msg = str(e)
        if len(note_list) > require_num:
            note_list = note_list[:require_num]
        return success, msg, note_list

    def search_user(self, query: str, cookies_str: str, page=1, proxies: dict = None):
        """
            获取搜索用户的结果
            :param query 搜索的关键词
            :param cookies_str 你的cookies
            :param page 搜索的页数
            返回搜索的结果
        """
        res_json = None
        try:
            api = "/api/sns/web/v1/search/usersearch"
            data = {
                "search_user_request": {
                    "keyword": query,
                    "search_id": "2dn9they1jbjxwawlo4xd",
                    "page": page,
                    "page_size": 15,
                    "biz_type": "web_search_user",
                    "request_id": "22471139-1723999898524"
                }
            }
            headers, cookies, data = generate_request_params(cookies_str, api, data, 'POST')
            response = requests.post(self.base_url + api, headers=headers, data=data.encode('utf-8'), cookies=cookies, proxies=proxies)
            res_json = response.json()
            success, msg = res_json["success"], res_json["msg"]
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, res_json

    def search_some_user(self, query: str, require_num: int, cookies_str: str, proxies: dict = None):
        """
            指定数量搜索用户
            :param query 搜索的关键词
            :param require_num 搜索的数量
            :param cookies_str 你的cookies
            返回搜索的结果
        """
        page = 1
        user_list = []
        try:
            while True:
                success, msg, res_json = self.search_user(query, cookies_str, page, proxies)
                if not success:
                    raise Exception(msg)
                if "users" not in res_json["data"]:
                    break
                users = res_json["data"]["users"]
                user_list.extend(users)
                page += 1
                if len(user_list) >= require_num or not res_json["data"]["has_more"]:
                    break
        except Exception as e:
            success = False
            msg = str(e)
        if len(user_list) > require_num:
            user_list = user_list[:require_num]
        return success, msg, user_list

    def get_note_out_comment(self, note_id: str, cursor: str, xsec_token: str, cookies_str: str, proxies: dict = None):
        """
            获取指定位置的笔记一级评论
            :param note_id 笔记的id
            :param cursor 指定位置的评论的cursor
            :param cookies_str 你的cookies
            返回指定位置的笔记一级评论
        """
        res_json = None
        try:
            api = "/api/sns/web/v2/comment/page"
            params = {
                "note_id": note_id,
                "cursor": cursor,
                "top_comment_id": "",
                "image_formats": "jpg,webp,avif",
                "xsec_token": xsec_token
            }
            splice_api = splice_str(api, params)
            headers, cookies, data = generate_request_params(cookies_str, splice_api, '', 'GET')
            response = requests.get(self.base_url + splice_api, headers=headers, cookies=cookies, proxies=proxies)
            res_json = response.json()
            success, msg = res_json["success"], res_json["msg"]
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, res_json

    def get_note_all_out_comment(self, note_id: str, xsec_token: str, cookies_str: str, proxies: dict = None):
        """
            获取笔记的全部一级评论
            :param note_id 笔记的id
            :param cookies_str 你的cookies
            返回笔记的全部一级评论
        """
        cursor = ''
        note_out_comment_list = []
        try:
            while True:
                success, msg, res_json = self.get_note_out_comment(note_id, cursor, xsec_token, cookies_str, proxies)
                if not success:
                    raise Exception(msg)
                comments = res_json["data"]["comments"]
                if 'cursor' in res_json["data"]:
                    cursor = str(res_json["data"]["cursor"])
                else:
                    break
                note_out_comment_list.extend(comments)
                if len(note_out_comment_list) == 0 or not res_json["data"]["has_more"]:
                    break
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, note_out_comment_list

    def get_note_inner_comment(self, comment: dict, cursor: str, xsec_token: str, cookies_str: str, proxies: dict = None):
        """
            获取指定位置的笔记二级评论
            :param comment 笔记的一级评论
            :param cursor 指定位置的评论的cursor
            :param cookies_str 你的cookies
            返回指定位置的笔记二级评论
        """
        res_json = None
        try:
            api = "/api/sns/web/v2/comment/sub/page"
            params = {
                "note_id": comment['note_id'],
                "root_comment_id": comment['id'],
                "num": "10",
                "cursor": cursor,
                "image_formats": "jpg,webp,avif",
                "top_comment_id": '',
                "xsec_token": xsec_token
            }
            splice_api = splice_str(api, params)
            headers, cookies, data = generate_request_params(cookies_str, splice_api, '', 'GET')
            response = requests.get(self.base_url + splice_api, headers=headers, cookies=cookies, proxies=proxies)
            res_json = response.json()
            success, msg = res_json["success"], res_json["msg"]
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, res_json

    def get_note_all_inner_comment(self, comment: dict, xsec_token: str, cookies_str: str, proxies: dict = None):
        """
            获取笔记的全部二级评论
            :param comment 笔记的一级评论
            :param cookies_str 你的cookies
            返回笔记的全部二级评论
        """
        try:
            if not comment['sub_comment_has_more']:
                return True, 'success', comment
            cursor = comment['sub_comment_cursor']
            inner_comment_list = []
            while True:
                success, msg, res_json = self.get_note_inner_comment(comment, cursor, xsec_token, cookies_str, proxies)
                if not success:
                    raise Exception(msg)
                comments = res_json["data"]["comments"]
                if 'cursor' in res_json["data"]:
                    cursor = str(res_json["data"]["cursor"])
                else:
                    break
                inner_comment_list.extend(comments)
                if not res_json["data"]["has_more"]:
                    break
            comment['sub_comments'].extend(inner_comment_list)
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, comment

    def get_note_all_comment(self, url: str, cookies_str: str, proxies: dict = None):
        """
            获取一篇文章的所有评论
            :param note_id: 你想要获取的笔记的id
            :param cookies_str: 你的cookies
            返回一篇文章的所有评论
        """
        out_comment_list = []
        try:
            urlParse = urllib.parse.urlparse(url)
            note_id = urlParse.path.split("/")[-1]
            kvs = urlParse.query.split('&')
            kvDist = {kv.split('=')[0]: kv.split('=')[1] for kv in kvs}
            success, msg, out_comment_list = self.get_note_all_out_comment(note_id, kvDist['xsec_token'], cookies_str, proxies)
            if not success:
                raise Exception(msg)
            for comment in out_comment_list:
                success, msg, new_comment = self.get_note_all_inner_comment(comment, kvDist['xsec_token'], cookies_str, proxies)
                if not success:
                    raise Exception(msg)
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, out_comment_list

    def get_unread_message(self, cookies_str: str, proxies: dict = None):
        """
            获取未读消息
            :param cookies_str: 你的cookies
            返回未读消息
        """
        res_json = None
        try:
            api = "/api/sns/web/unread_count"
            headers, cookies, data = generate_request_params(cookies_str, api, '', 'GET')
            response = requests.get(self.base_url + api, headers=headers, cookies=cookies, proxies=proxies)
            res_json = response.json()
            success, msg = res_json["success"], res_json["msg"]
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, res_json

    def get_metions(self, cursor: str, cookies_str: str, proxies: dict = None):
        """
            获取评论和@提醒
            :param cursor: 你想要获取的评论和@提醒的cursor
            :param cookies_str: 你的cookies
            返回评论和@提醒
        """
        res_json = None
        try:
            api = "/api/sns/web/v1/you/mentions"
            params = {
                "num": "20",
                "cursor": cursor
            }
            splice_api = splice_str(api, params)
            headers, cookies, data = generate_request_params(cookies_str, splice_api, '', 'GET')
            response = requests.get(self.base_url + splice_api, headers=headers, cookies=cookies, proxies=proxies)
            res_json = response.json()
            success, msg = res_json["success"], res_json["msg"]
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, res_json

    def get_all_metions(self, cookies_str: str, proxies: dict = None):
        """
            获取全部的评论和@提醒
            :param cookies_str: 你的cookies
            返回全部的评论和@提醒
        """
        cursor = ''
        metions_list = []
        try:
            while True:
                success, msg, res_json = self.get_metions(cursor, cookies_str, proxies)
                if not success:
                    raise Exception(msg)
                metions = res_json["data"]["message_list"]
                if 'cursor' in res_json["data"]:
                    cursor = str(res_json["data"]["cursor"])
                else:
                    break
                metions_list.extend(metions)
                if not res_json["data"]["has_more"]:
                    break
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, metions_list

    def get_likesAndcollects(self, cursor: str, cookies_str: str, proxies: dict = None):
        """
            获取赞和收藏
            :param cursor: 你想要获取的赞和收藏的cursor
            :param cookies_str: 你的cookies
            返回赞和收藏
        """
        res_json = None
        try:
            api = "/api/sns/web/v1/you/likes"
            params = {
                "num": "20",
                "cursor": cursor
            }
            splice_api = splice_str(api, params)
            headers, cookies, data = generate_request_params(cookies_str, splice_api, '', 'GET')
            response = requests.get(self.base_url + splice_api, headers=headers, cookies=cookies, proxies=proxies)
            res_json = response.json()
            success, msg = res_json["success"], res_json["msg"]
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, res_json

    def get_all_likesAndcollects(self, cookies_str: str, proxies: dict = None):
        """
            获取全部的赞和收藏
            :param cookies_str: 你的cookies
            返回全部的赞和收藏
        """
        cursor = ''
        likesAndcollects_list = []
        try:
            while True:
                success, msg, res_json = self.get_likesAndcollects(cursor, cookies_str, proxies)
                if not success:
                    raise Exception(msg)
                likesAndcollects = res_json["data"]["message_list"]
                if 'cursor' in res_json["data"]:
                    cursor = str(res_json["data"]["cursor"])
                else:
                    break
                likesAndcollects_list.extend(likesAndcollects)
                if not res_json["data"]["has_more"]:
                    break
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, likesAndcollects_list

    def get_new_connections(self, cursor: str, cookies_str: str, proxies: dict = None):
        """
            获取新增关注
            :param cursor: 你想要获取的新增关注的cursor
            :param cookies_str: 你的cookies
            返回新增关注
        """
        res_json = None
        try:
            api = "/api/sns/web/v1/you/connections"
            params = {
                "num": "20",
                "cursor": cursor
            }
            splice_api = splice_str(api, params)
            headers, cookies, data = generate_request_params(cookies_str, splice_api, '', 'GET')
            response = requests.get(self.base_url + splice_api, headers=headers, cookies=cookies, proxies=proxies)
            res_json = response.json()
            success, msg = res_json["success"], res_json["msg"]
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, res_json

    def get_all_new_connections(self, cookies_str: str, proxies: dict = None):
        """
            获取全部的新增关注
            :param cookies_str: 你的cookies
            返回全部的新增关注
        """
        cursor = ''
        connections_list = []
        try:
            while True:
                success, msg, res_json = self.get_new_connections(cursor, cookies_str, proxies)
                if not success:
                    raise Exception(msg)
                connections = res_json["data"]["message_list"]
                if 'cursor' in res_json["data"]:
                    cursor = str(res_json["data"]["cursor"])
                else:
                    break
                connections_list.extend(connections)
                if not res_json["data"]["has_more"]:
                    break
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, connections_list

    @staticmethod
    def get_note_no_water_video(note_id):
        """
            获取笔记无水印视频
            :param note_id: 你想要获取的笔记的id
            返回笔记无水印视频
        """
        success = True
        msg = '成功'
        video_addr = None
        try:
            headers = get_common_headers()
            url = f"https://www.xiaohongshu.com/explore/{note_id}"
            response = requests.get(url, headers=headers)
            res = response.text
            video_addr = re.findall(r'<meta name="og:video" content="(.*?)">', res)[0]
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, video_addr


    @staticmethod
    def get_note_no_water_img(img_url):
        """
            获取笔记无水印图片
            :param img_url: 你想要获取的图片的url
            返回笔记无水印图片
        """
        success = True
        msg = '成功'
        new_url = None
        try:
            # https://sns-webpic-qc.xhscdn.com/202403211626/c4fcecea4bd012a1fe8d2f1968d6aa91/110/0/01e50c1c135e8c010010000000018ab74db332_0.jpg!nd_dft_wlteh_webp_3
            if '.jpg' in img_url:
                img_id = '/'.join([split for split in img_url.split('/')[-3:]]).split('!')[0]
                # return f"http://ci.xiaohongshu.com/{img_id}?imageview2/2/w/1920/format/png"
                # return f"http://ci.xiaohongshu.com/{img_id}?imageview2/2/w/format/png"
                # return f'https://sns-img-hw.xhscdn.com/{img_id}'
                new_url = f'https://sns-img-qc.xhscdn.com/{img_id}'

            # 'https://sns-webpic-qc.xhscdn.com/202403231640/ea961053c4e0e467df1cc93afdabd630/spectrum/1000g0k0200n7mj8fq0005n7ikbllol6q50oniuo!nd_dft_wgth_webp_3'
            elif 'spectrum' in img_url:
                img_id = '/'.join(img_url.split('/')[-2:]).split('!')[0]
                # return f'http://sns-webpic.xhscdn.com/{img_id}?imageView2/2/w/1920/format/jpg'
                new_url = f'http://sns-webpic.xhscdn.com/{img_id}?imageView2/2/w/format/jpg'
            else:
                # 'http://sns-webpic-qc.xhscdn.com/202403181511/64ad2ea67ce04159170c686a941354f5/1040g008310cs1hii6g6g5ngacg208q5rlf1gld8!nd_dft_wlteh_webp_3'
                img_id = img_url.split('/')[-1].split('!')[0]
                # return f"http://ci.xiaohongshu.com/{img_id}?imageview2/2/w/1920/format/png"
                # return f"http://ci.xiaohongshu.com/{img_id}?imageview2/2/w/format/png"
                # return f'https://sns-img-hw.xhscdn.com/{img_id}'
                new_url = f'https://sns-img-qc.xhscdn.com/{img_id}'
        except Exception as e:
            success = False
            msg = str(e)
        return success, msg, new_url

if __name__ == '__main__':
    """
        此文件为小红书api的使用示例
        所有涉及数据爬取的api都在此文件中
        数据注入的api违规请勿尝试
    """
    xhs_apis = XHS_Apis()
    cookies_str = r''
    # 获取用户信息
    user_url = 'https://www.xiaohongshu.com/user/profile/67a332a2000000000d008358?xsec_token=ABTf9yz4cLHhTycIlksF0jOi1yIZgfcaQ6IXNNGdKJ8xg=&xsec_source=pc_feed'
    success, msg, user_info = xhs_apis.get_user_info('67a332a2000000000d008358', cookies_str)
    logger.info(f'获取用户信息结果 {json.dumps(user_info, ensure_ascii=False)}: {success}, msg: {msg}')
    success, msg, note_list = xhs_apis.get_user_all_notes(user_url, cookies_str)
    logger.info(f'获取用户所有笔记结果 {json.dumps(note_list, ensure_ascii=False)}: {success}, msg: {msg}')
    # 获取笔记信息
    note_url = r'https://www.xiaohongshu.com/explore/67d7c713000000000900e391?xsec_token=AB1ACxbo5cevHxV_bWibTmK8R1DDz0NnAW1PbFZLABXtE=&xsec_source=pc_user'
    success, msg, note_info = xhs_apis.get_note_info(note_url, cookies_str)
    logger.info(f'获取笔记信息结果 {json.dumps(note_info, ensure_ascii=False)}: {success}, msg: {msg}')
    # 获取搜索关键词
    query = "榴莲"
    success, msg, search_keyword = xhs_apis.get_search_keyword(query, cookies_str)
    logger.info(f'获取搜索关键词结果 {json.dumps(search_keyword, ensure_ascii=False)}: {success}, msg: {msg}')
    # 搜索笔记
    query = "榴莲"
    query_num = 10
    sort = "general"
    note_type = 0
    success, msg, notes = xhs_apis.search_some_note(query, query_num, cookies_str, sort, note_type)
    logger.info(f'搜索笔记结果 {json.dumps(notes, ensure_ascii=False)}: {success}, msg: {msg}')
    # 获取笔记评论
    note_url = r'https://www.xiaohongshu.com/explore/67d7c713000000000900e391?xsec_token=AB1ACxbo5cevHxV_bWibTmK8R1DDz0NnAW1PbFZLABXtE=&xsec_source=pc_user'
    success, msg, note_all_comment = xhs_apis.get_note_all_comment(note_url, cookies_str)
    logger.info(f'获取笔记评论结果 {json.dumps(note_all_comment, ensure_ascii=False)}: {success}, msg: {msg}')




