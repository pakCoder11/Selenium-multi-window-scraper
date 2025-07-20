from selenium_driverless import webdriver
import asyncio
from multiprocessing import Pool
from math import ceil
import re
from bs4 import BeautifulSoup
from typing import List


# Define the asynchronous scraper function
async def async_scraper(url_list):
    # Use a headless Chrome browser for scraping

    chrome_options = webdriver.ChromeOptions() 
    # chrome_options.add_argument('--headless')  # Run in headless mode
    chrome_options.add_argument('--incognito')  # Bypass OS security model

    async with webdriver.Chrome(options=chrome_options) as browser:
        for url in url_list:
            try:
                # Open the target website
                await browser.get(url)
                await asyncio.sleep(1.0)  # Wait for the page to load

                # Extract the page's HTML
                html_content = await browser.page_source
                
                # Scrape the profile data from the HTML
                # data = scrape_profile(html_content) 

                emails_data = extract_emails_from_html(html_content)
                # Print the extracted data
                print(emails_data)

            except Exception as e:
                # Print any errors encountered during scraping
                print(f"Error scraping {url}: {e}")

# Wrapper for running the async scraper in a process
def scraper_wrapper(url_list):
    # Run the asynchronous scraper
    asyncio.run(async_scraper(url_list))

def read_links_from_file(file_path):
    # Read URLs from a file and return as a list
    with open(file_path, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file if line.strip()]

# Function to divide the URL list into chunks
def divide_urls(url_list, num_chunks):
    # Calculate the size of each chunk
    chunk_size = ceil(len(url_list) / num_chunks)
    # Divide the list into chunks
    return [url_list[i:i + chunk_size] for i in range(0, len(url_list), chunk_size)]

def extract_emails_from_html(html_content: str) -> List[str]:
    """
    Extract valid email addresses from HTML content and save them to a file.
    
    Args:
        html_content (str): The HTML content to extract emails from
        
    Returns:
        List[str]: List of valid email addresses found
    """
    # First convert HTML to plain text to remove HTML tags
    soup = BeautifulSoup(html_content, 'html.parser')
    text_content = soup.get_text()
    
    # Regular expression for basic email validation
    # This regex ensures:
    # 1. Username part contains only letters, numbers, dots, underscores
    # 2. Domain part contains only letters, numbers, dots
    # 3. Exactly one @ symbol
    # 4. At least one character before and after @ symbol
    # 5. Top level domain has at least 2 characters
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Find all potential email matches
    potential_emails = re.findall(email_pattern, text_content)
    
    # Additional validation to filter out invalid cases
    valid_emails = []
    for email in potential_emails:
        # Additional validation checks
        if _is_valid_email(email):
            valid_emails.append(email)
    
    # Write valid emails to file
    if valid_emails:
        with open('extracted_emails.txt', 'a', encoding='utf-8') as f:
            for email in valid_emails:
                f.write(email + '\n')
    
    return valid_emails

def _is_valid_email(email: str) -> bool:
    """
    Additional validation for email addresses.
    
    Args:
        email (str): Email address to validate
        
    Returns:
        bool: True if email is valid, False otherwise
    """
    if not email or '@' not in email:
        return False
    
    # Split email into local and domain parts
    local, domain = email.split('@')
    
    # Check if local or domain part is empty
    if not local or not domain:
        return False
    
    # Check if domain has at least one dot and valid parts
    if '.' not in domain:
        return False
    
    # Check domain parts (should contain at least one letter)
    domain_parts = domain.split('.')
    if not all(any(c.isalpha() for c in part) for part in domain_parts):
        return False
    
    # Check for consecutive dots
    if '..' in email:
        return False
    
    # Check for valid characters in local part
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_')
    if not all(c in allowed_chars for c in local):
        return False
    
    # Check length constraints
    if len(email) > 254 or len(local) > 64:
        return False
    
    return True

if __name__ == "__main__":
    # Read the list of URLs to scrape from a file
    list_ = read_links_from_file('urls_to_scrape.txt') 
    # print(list_)

    # Divide URLs into 5 chunks for parallel processing
    num_processes = 5
    url_chunks = divide_urls(list_, num_processes)

    # Use multiprocessing to run the scraper concurrently
    with Pool(num_processes) as pool:
        pool.map(scraper_wrapper, url_chunks)
