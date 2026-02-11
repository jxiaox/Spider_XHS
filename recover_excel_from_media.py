# -*- coding: utf-8 -*-
import os
import json
from xhs_utils.common_util import init
from xhs_utils.data_util import save_to_xlsx, get_scraped_note_ids

def recover_excel():
    cookies_str, base_path = init()
    
    # We know the specific user path based on the user's request
    # "还是叫吴富贵吧_5b6150c56b58b741e26b8c7f"
    media_root = base_path['media']
    user_media_path = os.path.join(media_root, '还是叫吴富贵吧_5b6150c56b58b741e26b8c7f')
    
    excel_path = os.path.join(base_path['excel'], '5b6150c56b58b741e26b8c7f.xlsx')
    
    if not os.path.exists(user_media_path):
        print(f"Media path not found: {user_media_path}")
        return

    existing_ids = get_scraped_note_ids(excel_path)
    print(f"Found {len(existing_ids)} existing notes in Excel.")
    
    recovered_notes = []
    
    # Iterate through each note directory
    for entry in os.scandir(user_media_path):
        if entry.is_dir():
            json_path = os.path.join(entry.path, 'info.json')
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        note_info = json.load(f)
                        note_id = str(note_info.get('note_id'))
                        
                        if note_id and note_id not in existing_ids:
                            recovered_notes.append(note_info)
                            # Add to existing_ids to avoid duplicates in this run if any
                            existing_ids.add(note_id) 
                except Exception as e:
                    print(f"Error reading {json_path}: {e}")
    
    if recovered_notes:
        print(f"Recovering {len(recovered_notes)} notes to Excel...")
        save_to_xlsx(recovered_notes, excel_path)
        print("Recovery complete.")
    else:
        print("No missing notes found to recover.")

if __name__ == '__main__':
    recover_excel()
