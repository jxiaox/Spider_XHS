import asyncio
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv

load_dotenv()
COOKIES = os.getenv("COOKIES")

async def inspect_links(user_url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        if COOKIES:
            print("Injecting cookies...")
            cookie_list = []
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
        await asyncio.sleep(5)
        
        print("Extracting all note links...")
        links_info = await page.evaluate('''
            () => {
                const links = Array.from(document.querySelectorAll('a'));
                return links
                    .filter(a => a.href.includes('/explore/'))
                    .map(a => ({href: a.href, text: a.innerText.substring(0, 20)}))
                    .slice(0, 10);
            }
        ''')
        
        for i, info in enumerate(links_info):
            print(f"Link {i}: {info['href']}")
            
        await browser.close()

if __name__ == "__main__":
    user_url = "https://www.xiaohongshu.com/user/profile/5b6150c56b58b741e26b8c7f"
    asyncio.run(inspect_links(user_url))
