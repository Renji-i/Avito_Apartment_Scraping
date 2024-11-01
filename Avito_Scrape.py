import time
import random
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options

def get_text_or_nan(driver, xpath):
    """Helper function to get text or return 'NaN' if not found."""
    try:
        return driver.find_element(By.XPATH, xpath).text
    except NoSuchElementException:
        return "NaN"

# Setup WebDriver with options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Uncomment if you want headless mode
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36")
driver = webdriver.Chrome(options=chrome_options)
driver.set_page_load_timeout(60)  # Set a timeout of 60 seconds

# Starting URL (first page)
base_url = "https://www.avito.ma/fr/maroc/immobilier"
annonce_links = []
driver.get(base_url)

# Collect all announcement links
for page_number in range(1, 3):  # Change the range for more pages
    url = f"{base_url}?o={page_number}"
    driver.get(url)

    apartment_elements = driver.find_elements(By.XPATH, "//a[@class='sc-1jge648-0 eTbzNs']")
    for annonce in apartment_elements:
        link = annonce.get_attribute('href')
        annonce_links.append(link)

with open('link.txt', 'w', encoding="utf-8") as f:
    for i in annonce_links:
        f.write(i + "\n")
print("Page links saved to 'link.txt'.")

# Scrape all properties from the links
property_data = []  # List to store property details

try:
    with open("property_details.csv", "w", encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Title", "Price", "Location", "Surface", "Rooms", "Bathrooms", "Floor", "Construction Year"])

        for property_link in annonce_links:
            for attempt in range(5):  # Retry logic
                try:
                    time.sleep(random.uniform(2, 5))  # Random delay before each request
                    driver.get(property_link)
                    wait = WebDriverWait(driver, 30)
                    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/div/main/div/div[3]/div[1]/div[2]/div[1]/div[1]/div[2]/div[1]/div[1]/div[1]/h1')))

                    # Extract property details
                    title = get_text_or_nan(driver, '//*[@id="__next"]/div/main/div/div[3]/div[1]/div[2]/div[1]/div[1]/div[2]/div[1]/div[1]/div[1]/h1')
                    price = get_text_or_nan(driver, '//*[@id="__next"]/div/main/div/div[3]/div[1]/div[2]/div[1]/div[1]/div[2]/div[1]/div[1]/div[2]/p')
                    location = get_text_or_nan(driver, '//*[@id="__next"]/div/main/div/div[3]/div[1]/div[2]/div[1]/div[1]/div[2]/div[1]/div[2]/span[1]')
                    
                    # Optional fields, handle missing elements with get_text_or_nan
                    surface = get_text_or_nan(driver, "//li[.//span[text()='Surface habitable']]/span[@class='sc-1x0vz2r-0 gSLYtF']")
                    rooms = get_text_or_nan(driver,  '//*[@id="__next"]/div/main/div/div[3]/div[1]/div[2]/div[1]/div[1]/div[2]/div[4]/div[1]/div[1]/div/span')
                    bathrooms = get_text_or_nan(driver,  '//*[@id="__next"]/div/main/div/div[3]/div[1]/div[2]/div[1]/div[1]/div[2]/div[4]/div[1]/div[2]/div/span')
                    floor = get_text_or_nan(driver, "//li[.//span[text()='Étage']]/span[@class='sc-1x0vz2r-0 gSLYtF']")
                    construction_year = get_text_or_nan(driver, "//li[.//span[text()='Âge du bien']]/span[@class='sc-1x0vz2r-0 gSLYtF']")
                    
                    # Write data row
                    writer.writerow([title, price, location, surface, rooms, bathrooms, floor, construction_year])
                    print(f"Details saved for listing: {title}")
                    break  # Break if successful
                except TimeoutException:
                    print(f"Timeout while trying to access {property_link}, retrying in {2 ** attempt} seconds...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                except Exception as e:
                    print(f"Error while accessing {property_link}: {e}")
                    with open("error_log.txt", "a", encoding="utf-8") as error_log:
                        error_log.write(f"{property_link} - {e}\n")
                    break  # Exit the retry loop on other exceptions

except KeyboardInterrupt:
    print("Process interrupted by user.")

finally:
    driver.quit()  # Ensure the browser closes
    print("Scraping completed. Data saved to 'property_details.csv'.")
