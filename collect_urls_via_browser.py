
import asyncio
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv

load_dotenv()
COOKIES = os.getenv("COOKIES")

async def collect_urls(user_url, output_file, max_scrolls=1000):
    async with async_playwright() as p:
        # Use headless=False so user can see progress and handle any human-verification
        browser = await p.chromium.launch(headless=False)

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        if COOKIES:
            print("Injecting cookies from .env...")
            cookie_list = []
            # Split by ; but ignore ones inside quotes if any (rare in cookies)
            for pair in COOKIES.split(';'):
                if '=' in pair:
                    name, value = pair.strip().split('=', 1)
                    cookie_list.append({
                        'name': name,
                        'value': value,
                        'domain': '.xiaohongshu.com',
                        'path': '/'
                    })
            await context.add_cookies(cookie_list)

        page = await context.new_page()
        print(f"Opening: {user_url}")
        await page.goto(user_url)
        
        # Checking login state
        print("Checking login state and waiting for load...")
        await asyncio.sleep(5)
        
        # Check if we are on the login page
        if "login" in page.url:
            print("\n[!] WARNING: Redirected to login page. Please log in manually in the browser window.")
            print("[!] The script will wait 60 seconds for you to complete login...")
            # Wait for user to login (URL changes or timeout)
            for _ in range(60):
                if "login" not in page.url:
                    print("Login detected! Continuing...")
                    break
                await asyncio.sleep(2)
            else:
                print("Timeout waiting for login. Proceeding with current state...")

        collected_ids = set()

        # Step 0: Try to extract tokens from INITIAL_STATE for the first page
        print("Extracting tokens from INITIAL_STATE...")
        try:
            # Extract ONLY what we need to avoid "serialization chain too long" error
            notes_data = await page.evaluate("""() => {
                const state = window.__INITIAL_STATE__;
                if (state && state.user && state.user.notes) {
                    const notesList = state.user.notes;
                    const items = Array.isArray(notesList[0]) ? notesList[0] : notesList;
                    return items.map(n => ({
                        id: n.id || n.noteId,
                        xsecToken: n.xsecToken
                    }));
                }
                return [];
            }""")
            
            if notes_data:
                new_count = 0
                for note in notes_data:
                    note_id = note.get("id") 
                    xsec_token = note.get("xsecToken")
                    if note_id and note_id not in collected_ids:
                        collected_ids.add(note_id)
                        full_url = f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec_token}&xsec_source=pc_user"
                        with open(output_file, 'a') as f:
                            f.write(full_url + '\n')
                        new_count += 1
                if new_count > 0:
                    print(f"Extracted {new_count} notes from initial state. Total: {len(collected_ids)}")
        except Exception as e:
            print(f"Initial state extraction failed: {e}")
        
        async def handle_response(response):
            if "/api/sns/web/v1/user_posted" in response.url:
                try:
                    res_json = await response.json()
                    if res_json.get("code") == 0 and "data" in res_json:
                        notes = res_json["data"].get("notes", [])
                        new_count = 0
                        for note in notes:
                            note_id = note.get("note_id")
                            xsec_token = note.get("xsec_token")
                            if note_id and note_id not in collected_ids:
                                collected_ids.add(note_id)
                                full_url = f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec_token}&xsec_source=pc_user"
                                with open(output_file, 'a') as f:
                                    f.write(full_url + '\n')
                                new_count += 1
                        if new_count > 0:
                            print(f"Intercepted {new_count} new notes from API. Total: {len(collected_ids)}")
                except Exception as e:
                    pass

        page.on("response", handle_response)
        
        scroll_count = 0
        last_height = await page.evaluate("document.body.scrollHeight")
        while scroll_count < max_scrolls:
            # Scroll down
            await page.evaluate("window.scrollBy(0, 1000)")
            await asyncio.sleep(1.5 + scroll_count % 2) # Fluctuating delay
            
            # End condition: check if height changed
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height and scroll_count > 10:
                # Try a few more scrolls just in case
                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, 2000)")
                    await asyncio.sleep(2)
                if await page.evaluate("document.body.scrollHeight") == last_height:
                    print("Reached end of page or loading limit.")
                    break
            last_height = new_height
            scroll_count += 1
            if scroll_count % 10 == 0:
                print(f"Scroll {scroll_count}... Current total: {len(collected_ids)}")
            
        print(f"Finished. Total unique URLs saved to {output_file}: {len(collected_ids)}")
        await browser.close()

if __name__ == "__main__":
    user_url = "https://www.xiaohongshu.com/user/profile/5b6150c56b58b741e26b8c7f"
    output_file = "/Users/jxiaox/Investment/Spider_XHS/collected_urls.txt"
    
    # Clear file first to start fresh
    if os.path.exists(output_file):
        os.remove(output_file)
        
    print(f"Starting collection. Each scroll will append new URLs to {output_file}")
    asyncio.run(collect_urls(user_url, output_file, max_scrolls=2000))

