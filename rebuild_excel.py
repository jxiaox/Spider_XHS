# -*- coding: utf-8 -*-
"""Rebuild the Excel file from info.json files in media_datas directory."""
import os
import json
import openpyxl

media_dir = '/Users/jxiaox/Investment/Spider_XHS/datas/media_datas/还是叫吴富贵吧_5b6150c56b58b741e26b8c7f'
excel_path = '/Users/jxiaox/Investment/Spider_XHS/datas/excel_datas/5b6150c56b58b741e26b8c7f.xlsx'
corrupted_path = excel_path + '.corrupted'

# Backup corrupted file
if os.path.exists(excel_path):
    os.rename(excel_path, corrupted_path)
    print(f"Backed up corrupted file to {corrupted_path}")

headers = ['笔记id', '笔记url', '笔记类型', '用户id', '用户主页url', '昵称', '头像url', '标题', '描述', '点赞数量', '收藏数量', '评论数量', '分享数量', '视频封面url', '视频地址url', '图片地址url列表', '标签', '上传时间', 'ip归属地']

wb = openpyxl.Workbook()
ws = wb.active
ws.append(headers)

count = 0
errors = 0

for folder_name in sorted(os.listdir(media_dir)):
    folder_path = os.path.join(media_dir, folder_name)
    if not os.path.isdir(folder_path):
        continue
    info_path = os.path.join(folder_path, 'info.json')
    if not os.path.exists(info_path):
        continue
    try:
        with open(info_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        row = [str(data.get(k, '')) for k in [
            'note_id', 'note_url', 'note_type', 'user_id', 'home_url',
            'nickname', 'avatar', 'title', 'content', 'like_count',
            'collect_count', 'comment_count', 'share_count',
            'video_cover_url', 'video_url', 'pictures', 'show_tags',
            'upload_time', 'ip_location'
        ]]
        ws.append(row)
        count += 1
    except Exception as e:
        errors += 1
        print(f"Error processing {folder_name}: {e}")

wb.save(excel_path)
print(f"\nRebuilt Excel with {count} records ({errors} errors)")
print(f"Saved to {excel_path}")
