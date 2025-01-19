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
from .movie_details_fetcher import movieDatafetcher



def run_data_processor(background_job,**kwargs):
    processor=movieDatafetcher(background_job,**kwargs)
    print("##############################################################")
    processor.search_imdb()


@frappe.whitelist(allow_guest=True)
def trigger_data_source(data_source=None):

    try:

        task = frappe.get_doc({
            "doctype": "Background Job",
            "data_source_id": data_source,
            "status": "Scheduled",
            "start_time": now_datetime()
        })
        task.insert()
        frappe.db.commit()

        data_source_doc = frappe.get_doc("Data Source", data_source)
        

        data_source_doc.save()
        frappe.db.commit()

        frappe.enqueue(
            method=run_data_processor,
            queue="default",  
            timeout=1200,
            job_id="custom_data_fetcher.custom_data_fetcher.automation.search_imdb",
            genre="Action",
            rating=8.5,
            release_start_date="2021-03",
            type="Movie",
            number_of_movies=2,
            company="Walt Disney",
            background_job=task.name
        )
        frappe.msgprint("The search_imdb process has been enqueued successfully.")
    except Exception as e:
        frappe.log_error(title="Error Raised During Fetching", message=str(e))


