# Importing libraries
import time
import random
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Suppress chained assignment warnings in pandas
pd.options.mode.chained_assignment = None

# Delay function to mimic human browsing behavior by adding random time intervals
def delay():
    time.sleep(random.randint(3, 10))

# Function to perform lazy loading on a webpage by simulating scrolls
def lazy_loading(driver):
    """Scrolls the webpage to load all elements lazily."""
    element = driver.find_element(By.TAG_NAME, 'body')
    for _ in range(20):  # Scroll multiple times
        element.send_keys(Keys.PAGE_DOWN)
        delay()

# Constants
AMAZON_URL = "https://www.amazon.in"

# Function to log in to Amazon with provided credentials
def amazon_login(driver, username, password):
    """Logs into Amazon using the specified username and password."""
    driver.get(AMAZON_URL)
    time.sleep(2)
    try:
        driver.find_element(By.ID, "nav-link-accountList").click()  # Open login form
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ap_email"))
        ).send_keys(username + Keys.RETURN)  # Enter email and proceed
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ap_password"))
        ).send_keys(password + Keys.RETURN)  # Enter password and log in
        time.sleep(2)
    except Exception as e:
        print("Login failed:", e)
        driver.quit()
        raise

# Function to fetch product links and rankings from the current page
def fetch_product_links_and_ranks(driver):
    """Extracts product links and rankings from the current page."""
    product_links = []
    rankings = []
    content = driver.page_source
    homepage_soup = BeautifulSoup(content, 'html.parser')  # Parse the page source
    all_products = homepage_soup.find('div', attrs={"class": "p13n-desktop-grid"})  # Locate the grid of products
    if all_products:
        for product_section in all_products.find_all('div', {'id': 'gridItemRoot'}):
            # Extract product links
            for product_link in product_section.find_all('a', {'tabindex': '-1'}):
                href = product_link['href']
                product_links.append(href if href.startswith('https:') else f'https://www.amazon.in{href}')
            # Extract rankings
            rank = product_section.find('span', {'class': 'zg-bdg-text'})
            rankings.append(rank.text if rank else 'N/A')
    return product_links, rankings

# Function to extract detailed product data from a product page
def extract_product_data(driver, url, category_name):
    """Extracts product details like name, price, discount, images, and more."""
    driver.get(url)
    try:
        product_name = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "productTitle"))
        ).text.strip()
    except:
        product_name = "Product name not available"

    try:
        price_element = driver.execute_script(
            'return document.querySelector(".a-price span.a-offscreen")'
        )
        price = driver.execute_script("return arguments[0].textContent", price_element).strip() if price_element else "Price not available"
    except:
        price = "Price not available"

    try:
        description_list = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.a-unordered-list.a-vertical.a-spacing-mini"))
        )
        description_items = description_list.find_elements(By.TAG_NAME, "li")
        description_data = [
            item.find_element(By.TAG_NAME, "span").text.strip() for item in description_items
        ]
    except:
        description_data = ["Description not available"]

    try:
        ratings = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "acrPopover"))
        ).text.strip()
    except:
        ratings = "Ratings not available"

    try:
        product_image_urls = [
            my_elem.get_attribute("src")
            for my_elem in WebDriverWait(driver, 20).until(
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "div#altImages>ul li[data-ux-click] img"))
            )
        ]
    except:
        product_image_urls = ["Image not available"]

    try:
        discount_element = driver.find_element(By.CSS_SELECTOR, ".savingsPercentage")
        sales_discount = discount_element.text.strip().replace("-", "")
    except:
        sales_discount = "0%"

    try:
        discount_value = int(sales_discount.replace('%', ''))
    except:
        discount_value = 0

    # Skip products with discounts of 50% or less
    if discount_value <= 50:
        return None

    try:
        ships_from = extract_ships_from(driver)
    except:
        ships_from = "Ships from information not available"

    try:
        sold_by = extract_sold_by(driver)
    except:
        sold_by = "Sold by information not available"

    try:
        bought_element = driver.find_element(By.XPATH, "//span[@id='social-proofing-faceout-title-tk_bought']")
        products_bought = bought_element.text.strip()
    except:
        products_bought = "Products bought information not available"

    return {
        "Name": product_name,
        "Price": price,
        "Description": description_data,
        "Rating": ratings,
        "Featured Images": product_image_urls,
        "Sales Discount": sales_discount,
        "Ships From": ships_from,
        "Sold By": sold_by,
        "Products Bought in Past Month": products_bought,
        "Category Name": category_name
    }

# Helper function to extract "Ships From" information
def extract_ships_from(driver):
    try:
        ships_from_element = driver.find_element(By.XPATH, "//span[@class='a-size-small tabular-buybox-text-message'][normalize-space()='Amazon']")
        ships_from = ships_from_element.text.strip()
    except:
        ships_from = "Ships from information not available"
    return ships_from

# Helper function to extract "Sold By" information
def extract_sold_by(driver):
    try:
        sold_by_element = driver.find_element(By.XPATH, "//span[@class='a-size-small tabular-buybox-text-message']//a[@id='sellerProfileTriggerId']")
        sold_by = sold_by_element.text.strip()
    except:
        sold_by = "Sold by information not available"
    return sold_by

# Function to extract category name from a given URL
def extract_category_name(url):
    """Extracts category name from the URL."""
    try:
        category_name = url.split('/')[5]
    except:
        category_name = "Category name not available"
    return category_name

# Main function to handle the script's workflow
def main():
    email = input("Enter your Amazon email: ")
    password = input("Enter your Amazon password: ")

    # List of category URLs to scrape
    category_urls = [
        'https://www.amazon.in/gp/bestsellers/kitchen/ref=zg_bs_nav_kitchen_0',
        'https://www.amazon.in/gp/bestsellers/shoes/ref=zg_bs_nav_shoes_0',
        # 'https://www.amazon.in/gp/bestsellers/computers/ref=zg_bs_nav_computers_0',
        # 'https://www.amazon.in/gp/bestsellers/electronics/ref=zg_bs_nav_electronics_0',
        # 'https://www.amazon.in/gp/bestsellers/apparel/ref=zg_bs_nav_apparel_0',
        # 'https://www.amazon.in/gp/bestsellers/automotive/ref=zg_bs_nav_automotive_0',
        # 'https://www.amazon.in/gp/bestsellers/beauty/ref=zg_bs_nav_beauty_0',
        # 'https://www.amazon.in/gp/bestsellers/home-improvement/ref=zg_bs_nav_home-improvement_0',
        # 'https://www.amazon.in/gp/bestsellers/books/ref=zg_bs_nav_books_0',
        # 'https://www.amazon.in/gp/bestsellers/baby/ref=zg_bs_nav_baby_0',
        
    ]

    all_data = []

    # Iterate over each category URL
    for url in category_urls:
        category_name = extract_category_name(url)
        data = []

        # Set up Selenium WebDriver with headless mode
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        driver = webdriver.Chrome(service=Service(), options=options)

        # Login to Amazon
        amazon_login(driver, email, password)

        # Scrape data for multiple pages (adjust range as needed)
        for page in range(1, 2):
            page_url = f'{url}?_encoding=UTF8&pg={page}'
            driver.get(page_url)
            lazy_loading(driver)  # Load all elements
            product_links, rankings = fetch_product_links_and_ranks(driver)

            # Extract data for each product
            for idx, product_url in enumerate(product_links):
                product_data = extract_product_data(driver, product_url, category_name)
                if product_data:
                    product_data["Best Seller Ranking"] = rankings[idx] if idx < len(rankings) else "N/A"
                    product_data["URL"] = product_url
                    data.append(product_data)

        driver.quit()  # Close the WebDriver for each category
        all_data.extend(data)

    # Save collected data to CSV if below threshold
    if not all_data:
        print("No products with discounts greater than 50% were found.")
    elif len(all_data) <= 1500:
        df = pd.DataFrame(all_data)
        df.to_csv('amazon_best_sellers_all_categories.csv', index=False)
        print(f"Data for {len(all_data)} products saved to 'amazon_best_sellers_all_categories.csv'.")
    else:
        print(f"Data collection exceeded the limit with {len(all_data)} entries. No file was saved.")

# Entry point of the script
if __name__ == "__main__":
    main()
