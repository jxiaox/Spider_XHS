import os
import sys
from loguru import logger
from main import Data_Spider, init

def main():
    """
    Independent script to scrape notes strictly from 'collected_urls.txt'.
    This allows separating the 'URL Collection' phase from the 'Content Scraping' phase.
    """
    logger.info("Initializing Scraper for Local List Processing...")
    
    # Initialize environment (loads cookies, sets up paths)
    cookies_str, base_path = init()
    
    data_spider = Data_Spider()
    
    # Locate collected_urls.txt
    # It is expected to be in the same directory as this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "collected_urls.txt")
    
    if not os.path.exists(file_path):
        logger.error(f"Target file not found: {file_path}")
        logger.info("pPlease run 'collect_urls_via_browser.py' first to generate the list.")
        return

    logger.info(f"Target File: {file_path}")
    
    # Run the scraping process using the specialized method
    try:
        data_spider.spider_from_file(file_path, cookies_str, base_path)
        logger.success("Scraping from local list completed.")
    except Exception as e:
        logger.exception(f"An error occurred during execution: {e}")

if __name__ == "__main__":
    main()
