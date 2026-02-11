# -*- coding: utf-8 -*-
from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import init
import json

def test_login():
    cookies_str, base_path = init()
    xhs_apis = XHS_Apis()
    
    print("Testing get_self_info...")
    success, msg, res_json = xhs_apis.get_user_self_info2(cookies_str)
    
    print(f"Success: {success}")
    print(f"Msg: {msg}")
    if res_json:
        print(f"Data keys: {res_json.get('data', {}).keys()}")
        print(json.dumps(res_json, indent=2, ensure_ascii=False))
    else:
        print("No response json")

if __name__ == "__main__":
    test_login()
