import json
import math
import random
import execjs
from xhs_utils.cookie_util import trans_cookies
import urllib.parse

import os

# Calculate absolute path to static directory relative to this file
current_dir = os.path.dirname(os.path.abspath(__file__))
# Assumes xhs_util.py is in xhs_utils/, and static/ is a sibling of xhs_utils/
# i.e. project_root/xhs_utils/xhs_util.py -> project_root/static/
static_dir = os.path.join(os.path.dirname(current_dir), 'static')

try:
    js_path = os.path.join(static_dir, 'xhs_xs_xsc_56.js')
    js = execjs.compile(open(js_path, 'r', encoding='utf-8').read())
except Exception as e:
    # Fallback or re-raise with clear message
    print(f"Error loading {js_path}: {e}")
    # Try local static directory if exists (e.g. if structure is flat)
    try:
        js = execjs.compile(open('static/xhs_xs_xsc_56.js', 'r', encoding='utf-8').read())
    except:
        raise e



try:
    xray_path = os.path.join(static_dir, 'xhs_xray.js')
    
    # Read the JS content
    with open(xray_path, 'r', encoding='utf-8') as f:
        xray_content = f.read()

    # Calculate absolute paths for the packs
    pack1_path = os.path.join(static_dir, 'xhs_xray_pack1.js')
    pack2_path = os.path.join(static_dir, 'xhs_xray_pack2.js')

    # Replace relative requires with absolute paths to ensure they work regardless of CWD
    # We replace the simple relative path which is the first attempt in the try-catch block
    # Escaping backslashes for Windows compatibility if needed, but here assuming Mac (forward slashes mostly fine in JS strings inside Node on Mac)
    xray_content = xray_content.replace("'./xhs_xray_pack1.js'", f"'{pack1_path}'")
    xray_content = xray_content.replace("'./xhs_xray_pack2.js'", f"'{pack2_path}'")

    xray_js = execjs.compile(xray_content)

except Exception as e:
    # Fallback
    try:
        xray_js = execjs.compile(open('static/xhs_xray.js', 'r', encoding='utf-8').read())
    except:
        raise e

def generate_x_b3_traceid(len=16):
    x_b3_traceid = ""
    for t in range(len):
        x_b3_traceid += "abcdef0123456789"[math.floor(16 * random.random())]
    return x_b3_traceid

def generate_xs_xs_common(a1, api, data='', method='POST'):
    ret = js.call('get_request_headers_params', api, data, a1, method)
    xs, xt, xs_common = ret['xs'], ret['xt'], ret['xs_common']
    return xs, xt, xs_common

def generate_xs(a1, api, data=''):
    ret = js.call('get_xs', api, data, a1)
    xs, xt = ret['X-s'], ret['X-t']
    return xs, xt

def generate_xray_traceid():
    return xray_js.call('traceId')
def get_common_headers():
    return {
        "authority": "www.xiaohongshu.com",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "zh-CN,zh;q=0.9",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "referer": "https://www.xiaohongshu.com/",
        "sec-ch-ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Google Chrome\";v=\"122\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
def get_request_headers_template():
    return {
        "authority": "edith.xiaohongshu.com",
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "cache-control": "no-cache",
        "content-type": "application/json;charset=UTF-8",
        "origin": "https://www.xiaohongshu.com",
        "pragma": "no-cache",
        "referer": "https://www.xiaohongshu.com/",
        "sec-ch-ua": "\"Not A(Brand\";v=\"99\", \"Microsoft Edge\";v=\"121\", \"Chromium\";v=\"121\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
        "x-b3-traceid": "",
        "x-mns": "unload",
        "x-s": "",
        "x-s-common": "",
        "x-t": "",
        "x-xray-traceid": generate_xray_traceid()
    }

def generate_headers(a1, api, data='', method='POST'):
    xs, xt, xs_common = generate_xs_xs_common(a1, api, data, method)
    x_b3_traceid = generate_x_b3_traceid()
    headers = get_request_headers_template()
    headers['x-s'] = xs
    headers['x-t'] = str(xt)
    headers['x-s-common'] = xs_common
    headers['x-b3-traceid'] = x_b3_traceid
    if data:
        data = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    return headers, data

def generate_request_params(cookies_str, api, data='', method='POST'):
    cookies = trans_cookies(cookies_str)
    a1 = cookies['a1']
    headers, data = generate_headers(a1, api, data, method)
    return headers, cookies, data

def splice_str(api, params):
    params = {k: v if v is not None else '' for k, v in params.items()}
    query_string = urllib.parse.urlencode(params)
    return f"{api}?{query_string}"

