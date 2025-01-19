from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException
import time
from imdb import IMDb
import wikipediaapi
import pandas as pd
import math
import re
import frappe
from webdriver_manager.chrome import ChromeDriverManager
from frappe.utils import now_datetime

ia = IMDb()
wiki = wikipediaapi.Wikipedia(user_agent="MyIMDbFetcher/1.0 (sandip.pandit230496@gmail.com)", language="en")

driver_path = "/usr/local/bin/chromedriver/chromedriver"

def flatten_and_join_values(data):
    if isinstance(data, list):
        return ', '.join(data)
    return data

def to_snake_case(text):
    text = re.sub(r'(?<!^)(?=[A-Z])', '_', text).replace(" ", "_").replace("-", "_").lower()
    return text

def configure_chrome_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--enable-logging")
    options.add_argument("--v=1")
    options.add_argument("--remote-debugging-port=9222")
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(30)
    return driver

def select_filter(driver, css_selector, error_message):
    try:
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector))
        )
        ActionChains(driver).move_to_element(button).click().perform()
    except Exception as e:
        print(f"{error_message}: {e}")

def search_imdb(movie_name=None, genre=None, rating=None, release_start_date=None, release_end_date=None, type=None, number_of_movies=None, company=None):
    print("Started opening...")
    base_url = "https://www.imdb.com/search/title/"
    driver = configure_chrome_driver()
    list_of_movies = []

    try:
        driver.get(base_url)

        # Apply filters if provided
        if genre:
            select_filter(driver, f'[data-testid="test-chip-id-{genre}"]', f"Failed to select genre '{genre}'")
        
        if company:
            select_filter(driver, f'[data-testid="test-chip-id-{company} (US)"]', f"Failed to select company '{company}'")
        
        if release_start_date:
            select_filter(driver, f'[data-testid="releaseYearMonth-start"]', f"Failed to select start release date '{release_start_date}'")
        
        if release_end_date:
            select_filter(driver, f'[data-testid="releaseYearMonth-end"]', f"Failed to select end release date '{release_end_date}'")

        if rating:
            select_filter(driver, f'[data-testid="imdbratings-start"]', f"Failed to select rating '{rating}'")
        
        body = driver.find_element(By.TAG_NAME, "body")
        ActionChains(driver).move_to_element(body).click().perform()

        # Wait and load movies
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.ipc-metadata-list > li"))
        )

        movie_items = driver.find_elements(By.CSS_SELECTOR, "ul.ipc-metadata-list > li")
        for index, item in enumerate(movie_items, 1):
            try:
                movie_link = item.find_element(By.CSS_SELECTOR, "a.ipc-title-link-wrapper")
                movie_name = movie_link.text.split(".")[1]
                list_of_movies.append(movie_name)
                print(f"{index}. {movie_name}")
            except Exception as e:
                print(f"{index}. Could not extract movie link: {e}")

        driver.quit()
        
        # Process each movie
        final_movie_details = []
        for movie in list_of_movies:
            wiki_data = search_wiki(movie)
            if wiki_data:
                final_movie_details.append(wiki_data)

        save_to_db(final_movie_details)
        return "success"

    except WebDriverException as e:
        print("An error occurred in Selenium:", str(e))
        return "failed"

    finally:
        driver.quit()

def search_wiki(title=None):
    base_url_wiki = "https://en.wikipedia.org/wiki/Main_Page"
    driver = configure_chrome_driver()

    try:
        driver.get(base_url_wiki)

        if title:
            input_box = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'cdx-text-input__input'))
            )
            ActionChains(driver).move_to_element(input_box).click().perform()
            input_box.send_keys(title)
            input_box.send_keys(Keys.ENTER)

            # Wait for the page to load
            summary = wiki_fetcher(title)
            return {
                "movie_name": title,
                "summary": summary,
                "infobox_data": extract_infobox_data(driver)
            }

    except Exception as e:
        print(f"An error occurred while searching for {title}: {e}")
        return None
    finally:
        driver.quit()

def extract_infobox_data(driver):
    try:
        info_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'infobox'))
        )
        rows = info_box.find_elements(By.TAG_NAME, 'tr')
        table_data = []

        for row in rows:
            try:
                headers = [header.text.strip() for header in row.find_elements(By.TAG_NAME, 'th')]
                data = [data.text.strip() for data in row.find_elements(By.TAG_NAME, 'td')]
                if headers and data:
                    table_data.append({header: data for header, data in zip(headers, data)})
            except Exception as e:
                print(f"Error processing row: {e}")
        
        return table_data
    except Exception as e:
        print(f"Infobox data extraction failed: {e}")
        return []

def wiki_fetcher(title):
    page = wiki.page(title)
    return page.summary if page.exists() else "No summary available"

def save_to_db(final_data):
    if isinstance(final_data, list):
        for data in final_data:
            try:
                doc = frappe.get_doc({"doctype": "Movie Database", **data})
                doc.insert()
                frappe.db.commit()
            except Exception as e:
                print(f"Error inserting data: {e}")
    elif isinstance(final_data, dict):
        try:
            doc = frappe.get_doc({"doctype": "Movie Database", **final_data})
            doc.insert()
            frappe.db.commit()
        except Exception as e:
            print(f"Error inserting data: {e}")

def save_to_excel(data):
    df = pd.DataFrame(data)
    df.to_excel("movies_wikipedia_sections.xlsx", index=False)
    print("Data saved to Excel")

@frappe.whitelist(allow_guest=True)
def trigger_data_source(data_source=None):
    try:
        frappe.enqueue(
            method="custom_data_fetcher.custom_data_fetcher.automation.search_imdb",
            queue="default",  
            timeout=300,
            job_id="custom_data_fetcher.custom_data_fetcher.automation.search_imdb",
            genre="Action",
            rating=7,
            release_start_date="2019-03",
            type="Movie",
            number_of_movies=10,
            company="Walt Disney"
        )
        frappe.msgprint("The search_imdb process has been enqueued successfully.")
    except Exception as e:
        frappe.log_error(title="Error Raised During Fetching", message=str(e))

def save_to_db(final_data):

    if isinstance(final_data, list):  # Check if it's a list
        for data in final_data:
            try:
                doc = frappe.get_doc({"doctype": "Movie Database", **data})
                doc.insert()
                frappe.db.commit()  # Commit the transaction after each insert
            except Exception as e:
                print(f"Error inserting data: {data}. Error: {e}")
    elif isinstance(final_data, dict): 
        try:
            doc = frappe.get_doc({"doctype": "Movie Database", **final_data})
            doc.insert()
            frappe.db.commit()
        except Exception as e:
            print(f"Error inserting data: {final_data}. Error: {e}")
    else:
        print("Invalid data format. Expected a list or dictionary.")


def llm_source(summary,temperature=0.7):
    import os
    from langchain.llms import OpenAI 
    from langchain.chains import ConversationChain

# Set your OpenAI API key
    os.environ["OPENAI_API_KEY"] = "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"  # Replace with your OpenAI API key
    """
    Function to rephrase a given movie summary using LangChain's LLM.
    
    Parameters:
    - summary (str): The original movie summary to be rephrased.
    - temperature (float): The temperature setting for the OpenAI model. Defaults to 0.7.
    
    Returns:
    - str: The rephrased movie summary.
    """
    try:
        # Initialize LangChain's OpenAI model (adjust for older versions if necessary)
        llm = OpenAI(temperature=temperature)  # Use ChatOpenAI if newer version
        conversation = ConversationChain(llm=llm)
        
        # User input for the AI model
        user_input = f"Rephrase the following movie summary and add some new insights or touches: {summary}"
        
        # Get response
        response = conversation.predict(input=user_input)
        return response
    except Exception as e:
        return f"An error occurred: {str(e)}"
    
# def enqueue_data_processor(task.name):
