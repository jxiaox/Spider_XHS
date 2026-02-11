from xhs_utils.common_util import init
from apis.xhs_pc_apis import XHS_Apis
import json

cookies_str, _ = init()
api = XHS_Apis()

# A failing note from logs
url = "https://www.xiaohongshu.com/explore/696ca65c0000000021032c7f?xsec_token=ABGhFyXbSRImaNvR4gFQswhIhYdmIyxzf2JbamIsnlkmU="

print(f"Testing URL: {url}")
success, msg, res = api.get_note_info(url, cookies_str)
print(f"Success: {success}")
print(f"Msg: {msg}")
if res:
    print(json.dumps(res, indent=2, ensure_ascii=False))
