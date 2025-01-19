import frappe 
from selenium import webdriver
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
from webdriver_manager.chrome import ChromeDriverManager
from frappe.utils import now_datetime
from selenium import webdriver


ia = IMDb()
wiki = wikipediaapi.Wikipedia(user_agent="MyIMDbFetcher/1.0 (sandip.pandit230496@gmail.com)", language="en")
driver_path = "/usr/local/bin/chromedriver/chromedriver"
chrome_path = "/usr/bin/google-chrome"


class movieDatafetcher():
    def __init__(self, background_job, genre=None, rating=None, release_start_date=None, 
                 release_end_date=None, type=None, number_of_movies=None, company=None):
        self.background_task = frappe.get_doc("Background Job", background_job)


        self.movie_filter = frappe.get_doc("Data Source", self.background_task.data_source_id)
        self.status = self.background_task.status

        self.genre = genre
        self.rating = rating
        self.release_start_date = release_start_date
        self.release_end_date = release_end_date
        self.type = type
        self.number_of_movies = number_of_movies
        self.company = company


        print(self.genre,self.rating,self.release_start_date,self.release_end_date,self.type,self.number_of_movies,self.company,"*************")

    all_movies_data = []
    final_movie_details=[]

    def flatten_and_join_values(data):
        if isinstance(data, list):
            return ', '.join(data)
        return data

    def to_camel_case(text):
        words = text.split(" ")
        return words[0].lower() + ''.join(word.capitalize() for word in words[1:])

    def to_snake_case(text):
        text = re.sub(r'(?<!^)(?=[A-Z])', '_', text).replace(" ", "_").replace("-", "_").lower()
        return text
    
    def update_task_status(self, status: str=None):
        self.background_task.status = status
        self.background_task.save()

    def search_imdb(self,movie_name=None, genre=None, rating=None,rating_end=None, release_start_date=None, release_end_date=None,type=None,number_of_movies=None,company=None):
        
        driver=selenium_driver_setting()
        try:
            driver.get("https://www.imdb.com/search/title/")
        
            list_of_movies = []
            self.update_task_status("Processing")

            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.ipc-page-grid--bias-left"))
            )

            expand_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'ipc-page-grid--bias-left')]//span[text()='Expand all']"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", expand_button)
            driver.execute_script("arguments[0].click();", expand_button)

            if type:
                converted_type=self.to_camel_case(type)
                movie_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, f'[data-testid="test-chip-id-{converted_type}"]'))
                )
                ActionChains(driver).move_to_element(movie_button).click().perform()
                movie_button.click()


            if genre:
                try:
                    genre_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, f'[data-testid="test-chip-id-{genre}"]'))
                    )
                    ActionChains(driver).move_to_element(genre_button).click().perform()
                except Exception as e:
                    print(f"Failed to select genre '{genre}': {e}")
            else:
                print("No genre specified.")

            if company:
                try:
                    company_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, f'[data-testid="test-chip-id-{company} (US)"]'))
                    )
                    ActionChains(driver).move_to_element(company_button).click().perform()
                except Exception as e:
                    print(f"Failed to select genre '{genre}': {e}")
            else:
                print("No company specified.")


            if release_start_date:
                try:
                    release_start_date_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, f'[data-testid="releaseYearMonth-start"]'))
                    )
                    ActionChains(driver).move_to_element(release_start_date_button).click().perform()
                    release_start_date_button.send_keys(release_start_date)
                
                except Exception as e:
                    print(f"Failed to select genre '{genre}': {e}")

            if release_end_date:
                try:
                    release_end_date_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="releaseYearMonth-end"]'))
                    )
                    
                    driver.execute_script("arguments[0].scrollIntoView(true);", release_end_date_button)
                    
                    driver.execute_script("arguments[0].click();", release_end_date_button)

                    release_end_date_button.send_keys(release_end_date)
                    print(f"End Date '{release_end_date}' successfully entered.")
                
                except Exception as e:
                    print(f"Failed to set Release End Date: {e}")
            else:
                print("No Release End Date specified.")


            
            if rating:
                try:
                    rating_start = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, f'[data-testid="imdbratings-start"]'))
                    )
                    ActionChains(driver).move_to_element(rating_start).click().perform()
                    rating_start.click()
                    rating_start.send_keys(rating)

                except Exception as e:
                    print(f"Failed to select rating '{rating}': {e}")
            else:
                print("No genre specified.")

            if rating_end:
                try:
                    rating_end_text = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, f'[data-testid="imdbratings-end"]'))
                    )
                    ActionChains(driver).move_to_element(rating_end_text).click().perform()
                    rating_end_text.click()
                    rating_end_text.send_keys(rating_end)

                except Exception as e:
                    print(f"Failed to select rating '{rating}': {e}")
            else:
                print("No genre specified.")
            
            body = driver.find_element(By.TAG_NAME, "body")
            ActionChains(driver).move_to_element(body).click().perform()

            see_result_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "sc-13add9d7-4"))
            )
            driver.execute_script("arguments[0].click();", see_result_button)

            if number_of_movies:
                try:
                    load_more_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, "ipc-see-more__button"))
                    )

                    if not load_more_button:
                        pass

                    else:
                        number_of_movies_to_be_fetched=number_of_movies//50
                        for i in range(number_of_movies_to_be_fetched-1):
                            ActionChains(driver).move_to_element(load_more_button).click().perform()
                            
                            time.sleep(2)

                except Exception as e:
                    print(f"Failed to click '50 more' button: {e}")

            

            time.sleep(10)
            movie_items = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.ipc-metadata-list > li"))
            )

            if movie_items:
                print("\nMovie Links:\n")
                for index, item in enumerate(movie_items, 1):
                    try:
                        movie_link = item.find_element(By.CSS_SELECTOR, "a.ipc-title-link-wrapper")
                        movie_name = movie_link.text.split(".")[1]
                        list_of_movies.append(movie_name)
                        print(f"{movie_name}")
                    except Exception as e:
                        print(f"{index}. Could not extract movie link: {e}")

            driver.quit()
            for movie in list_of_movies:
                wiki_data = search_wiki(movie)
                if wiki_data:
                    self.final_movie_details.append(wiki_data)

            save_to_db(self.final_movie_details)
            print("done")
            self.update_task_status("Completed")
            self.background_task.end_time=now_datetime()
            self.background_task.save()
            return "success"
                

        except WebDriverException as e:
            print("An error occurred in Selenium:")
            print(str(e))
            self.background_task.error_log=str(e)
            self.update_task_status("Failed")
            return "failed"

        finally:
            driver.quit()
            self.background_task.save()

def selenium_driver_setting():
        options = Options()
        options.binary_location = chrome_path
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver


def flatten_and_join_values(data):
    if isinstance(data, list):
        return ', '.join(data)
    return data

def to_camel_case(text):
    words = text.split(" ")
    return words[0].lower() + ''.join(word.capitalize() for word in words[1:])

def to_snake_case(text):
    text = re.sub(r'(?<!^)(?=[A-Z])', '_', text).replace(" ", "_").replace("-", "_").lower()
    return text

def update_task_status(self, status: str=None):
    self.background_task.status = status
    self.background_task.save()

# def search_wiki(title):
#     driver=selenium_driver_setting()
#     base_url_wiki = "https://en.wikipedia.org/wiki/Main_Page"

#     print(title,"###############################")
#     try:
#         driver.maximize_window()
#         driver.get(base_url_wiki)

#         if title:
#             input_box = WebDriverWait(driver, 10).until(
#                 EC.element_to_be_clickable((By.CLASS_NAME, 'cdx-text-input__input'))
#             )

#             ActionChains(driver).move_to_element(input_box).click().perform()
#             input_box.send_keys(title)
#             input_box.send_keys(Keys.ENTER)

#             summary = wiki_fetcher(title)
#             # summary=llm_source(summary)

#             try:
#                 info_box = WebDriverWait(driver, 10).until(
#                     EC.presence_of_element_located((By.CLASS_NAME, 'infobox'))
#                 )
#             except Exception as e:
#                 print(f"Infobox not found for {title}. Error: {e}")
#                 return {
#                     "movie_name": title,
#                     "summary": summary,
#                     "Infobox Data": []
#                 }

#             while True:
#                 try:
#                     tbody = info_box.find_element(By.TAG_NAME, 'tbody')
#                     rows = tbody.find_elements(By.TAG_NAME, 'tr')
#                     break
#                 except Exception as e:
#                     print(f"Retrying due to stale element error: {e}")
#                     time.sleep(1)

#             table_data = []

#             for row in rows:
#                 try:
#                     cell_headers = [
#                         header.text.strip() for header in row.find_elements(By.TAG_NAME, 'th')
#                     ]
#                     cell_contexts = [context.text.strip().split('\n') for context in row.find_elements(By.TAG_NAME, 'td')]

#                     if cell_headers and cell_contexts:
#                         row_data = {header: context for header, context in zip(cell_headers, cell_contexts)}
#                     else:
#                         continue
#                     table_data.append(row_data)
#                 except Exception as e:
#                     print(f"Error processing row: {e}")

#             consolidated_object = {}
#             for row in table_data:
#                 for key, value in row.items():
#                     consolidated_object[to_snake_case(key)] = flatten_and_join_values(value)
            
#             final_data = {
#                 "movie_name": title,
#                 "summary": summary,
#             }

#             for key,value in consolidated_object.items():
#                 final_data[key]=value
            
#             return final_data

#     except Exception as e:
#         print(f"An error occurred: {e}")
#         return {
#             "movie_name": title,
#             "summary": "Error fetching data.",
#             "infobox_data": []
#         }

#     finally:
#         driver.quit()


def search_wiki(title):
    driver = selenium_driver_setting()
    base_url_wiki = "https://en.wikipedia.org/wiki/Main_Page"

    try:
        driver.refresh()
        driver.maximize_window()
        driver.get(base_url_wiki)

        if title:
            input_box = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'cdx-text-input__input'))
            )
            WebDriverWait(driver, 10).until(EC.staleness_of(input_box))
            
            ActionChains(driver).move_to_element(input_box).click().perform()
            input_box.send_keys(title)
            input_box.send_keys(Keys.ENTER)

            # Wait for the input box or page to become stale after search

            # Fetch the summary
            summary = wiki_fetcher(title)

            try:
                # Locate the infobox
                info_box = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'infobox'))
                )
                tbody = info_box.find_element(By.TAG_NAME, 'tbody')

                # Wait for the infobox or tbody to become stale if needed
                WebDriverWait(driver, 10).until(EC.staleness_of(tbody))
                tbody = info_box.find_element(By.TAG_NAME, 'tbody')  # Refetch the tbody element

                rows = tbody.find_elements(By.TAG_NAME, 'tr')
            except Exception as e:
                print(f"Infobox not found for {title}. Error: {e}")
                return {
                    "movie_name": title,
                    "summary": summary,
                    "Infobox Data": []
                }

            # Process table rows to collect data
            table_data = []
            for row in rows:
                try:
                    # Refetch row elements to avoid stale references
                    cell_headers = [
                        header.text.strip() for header in row.find_elements(By.TAG_NAME, 'th')
                    ]
                    cell_contexts = [
                        context.text.strip().split('\n') for context in row.find_elements(By.TAG_NAME, 'td')
                    ]
                    if cell_headers and cell_contexts:
                        row_data = {header: context for header, context in zip(cell_headers, cell_contexts)}
                        table_data.append(row_data)
                except Exception as e:
                    print(f"Error processing row: {e}")

            # Convert table data into a consolidated object
            consolidated_object = {}
            for row in table_data:
                for key, value in row.items():
                    consolidated_object[to_snake_case(key)] = flatten_and_join_values(value)

            # Build the final data
            final_data = {
                "movie_name": title,
                "summary": summary,
            }
            for key, value in consolidated_object.items():
                final_data[key] = value

            return final_data

    except Exception as e:
        print(f"An error occurred: {e}")
        return {
            "movie_name": title,
            "summary": "Error fetching data.",
            "infobox_data": []
        }

    finally:
        driver.quit()






def wiki_fetcher(title):

    page = wiki.page(title)

    if page.exists():
        
        print(page.summary)

    else:
        print("Wikipedia page not found.")

    return page.summary


def save_to_excel(data):
    df = pd.DataFrame(data)
    file_name = "movies_wikipedia_sections.xlsx"
    df.to_excel(file_name, index=False) 
    print(f"Data saved to {file_name}")


def save_to_db(final_data):

    if isinstance(final_data, list): 

        for data in final_data:
            try:
                doc = frappe.get_doc({"doctype": "Movie Database", **data})
                doc.insert()
                frappe.db.commit() 
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
    



