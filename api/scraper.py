import time
import os
import pandas as pd
from datetime import date
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException
import requests
from bs4 import BeautifulSoup

class Scraper:
    def __init__(self, payload):
        self.width = 400
        self.height = 1200
        self.baseUrl = payload["fbUrl"]
        self.totalEvent = int(payload["totalEvent"]) if len(payload["totalEvent"]) > 0 else ''
        self.university = payload["university"]
        self.dateFrom = payload["dateFrom"]
        self.dateTo = payload["dateTo"]
    
    # Function to add NULL for missing data
    def handle_missing_data(self, data):
        return data if data else "NULL"
    
    def validateDate(self, dfs):
        final_df = pd.concat(dfs, ignore_index=True)
        pattern = r'\b(0[1-9]|[12][0-9]|3[01])\s(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\b'
        pattern2 = r'((1[0-2]|0?[1-9]):([0-5][0-9])(am|pm| am| pm))|no time available'
        final_df['is_valid1'] = final_df['Date'].str.contains(pattern)
        final_df['is_valid2'] = final_df['End Date'].str.contains(pattern)
        final_df['is_valid3'] = final_df['Time'].str.match(pattern2)
        final_df = final_df[final_df["is_valid1"]]
        final_df = final_df[final_df["is_valid2"]]
        final_df = final_df[final_df["is_valid3"]]
        final_df = final_df.drop_duplicates(subset=['Title'], keep='first')
        print('final_df', final_df)
        return final_df

    def scrapeFb(self):
        # Set up the driver
        options = webdriver.ChromeOptions()
        options.add_argument(f'--window-size={self.width},{self.height}')  # Set window dimensions
        driver = webdriver.Chrome(options=options)

        # Set the desired number of events
        desired_events = self.totalEvent

        # Calculate the page height
        page_height = driver.execute_script("return document.body.scrollHeight")

        driver.get(self.baseUrl)

        # Calculate the target end time for scrolling
        scroll_end_time = time.time() + desired_events / 5  # Scroll for 10 seconds from now

        # Perform automatic scrolling using JavaScript
        scroll_amount = 500  # You can adjust this value to control the scrolling amount
        scroll_pause_time = 0.1  # Time to pause between scrolls

        # Scroll through the page until the target end time is reached
        while time.time() < scroll_end_time:
            driver.execute_script(f"window.scrollTo(0, {scroll_amount});")
            scroll_amount += 500
            time.sleep(scroll_pause_time)

        event_titles = []
        event_locations = []
        event_dates = []
        event_end = []
        event_times = []
        image_urls = []
        event_interests = []
        event_urls = []
        event_descriptions = []  # Added a list for descriptions

        # For fetching 15-Records
        for num in range(1, desired_events*2):
            full_xpath_for_title = "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div/div[1]/div[1]/div/div/div/div[2]/div[3]/div[" + str(
                num) + "]/div/div/div/a/div[2]/div/div[2]/span/span/object/a/span"
            full_xpath_for_location = "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div/div[1]/div[1]/div/div/div/div[2]/div[3]/div[" + str(
                num) + "]/div/div/div/a/div[2]/div/div[3]/span/span/span"
            full_xpath_for_date = "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div/div[1]/div[1]/div/div/div/div[2]/div[3]/div[" + str(
                num) + "]/div/div/div/a/div[2]/div/div[1]/span/span/span"
            full_xpath_for_image = f"/html/body/div[1]/div/div[1]/div/div[3]/div/div/div/div[1]/div[1]/div/div/div/div[2]/div[3]/div[{num}]/div/div/div/a/div[1]/div/img"
            full_xpath_for_url = f"/html/body/div[1]/div/div[1]/div/div[3]/div/div/div/div[1]/div[1]/div/div/div/div[2]/div[3]/div[{num}]/div/div/div/a"
            full_xpath_for_interest = f"/html/body/div[1]/div/div[1]/div/div[3]/div/div/div/div[1]/div[1]/div/div/div/div[2]/div[3]/div[{num}]/div/div/div/a/div[2]/span/div/span/span"
            full_xpath_for_description = f"/html/body/div[1]/div/div[1]/div/div[3]/div/div/div/div[1]/div[1]/div/div/div/div[2]/div[3]/div[{num}]/div/div/div/a/div[2]/div/div[4]/div/span/span/span"

            # Wait for the element to be visible
            wait = WebDriverWait(driver, 0.1)  # Adjust the timeout as needed

            # For titles
            print("Trying to fetch title for event")
            try:
                event_title_elements = wait.until(EC.visibility_of_all_elements_located((By.XPATH, full_xpath_for_title)))
                for event_title_element in event_title_elements:
                    event_titles.append(event_title_element.text)
            except TimeoutException:  # if the title isn't found
                event_titles.append("title unknown")

            # For locations
            try:
                event_location_elements = wait.until(EC.visibility_of_all_elements_located((By.XPATH, full_xpath_for_location)))
                for event_location_element in event_location_elements:
                    event_locations.append(event_location_element.text)
            except TimeoutException:  # if the location isn't found
                event_locations.append("location unknown")

            # For dates
            try:
                event_date_elements = wait.until(EC.visibility_of_all_elements_located((By.XPATH, full_xpath_for_date)))
                for event_date_element in event_date_elements:
                    if event_date_element.text[5:11] != "NING N":
                        event_dates.append(event_date_element.text[5:11])
                    else:
                        event_dates.append(date.today().strftime("%d %b"))
            except TimeoutException:  # if the date isn't found
                event_dates.append("date unknown")

            # For end dates
            try:
                event_date_elements = wait.until(EC.visibility_of_all_elements_located((By.XPATH, full_xpath_for_date)))
                for event_date_element in event_date_elements:
                    if event_date_element.text[12:14].isnumeric(): 
                        event_end.append(event_date_element.text[12:14])
                    else:
                        if event_date_element.text[5:11] != "NING N":
                            event_end.append(event_date_element.text[5:11])
                        else:
                            event_end.append(date.today().strftime("%d %b"))
            except TimeoutException:  # if the end date isn't found
                event_end.append("date unknown")

            # For times
            try:
                event_date_elements = wait.until(EC.visibility_of_all_elements_located((By.XPATH, full_xpath_for_date)))
                for event_date_element in event_date_elements:
                    if event_date_element.text[-13:] != "HAPPENING NOW":
                        if int(event_date_element.text[-12:-10]) < 12:
                            day_night = " am"
                            event_times.append(event_date_element.text[-13:-7]+day_night)
                        else:
                            day_night = " pm"
                            new_time_1 = int(event_date_element.text[-13:-10])-12
                            new_time_2 = event_date_element.text[-10:-7]
                            event_times.append(str(new_time_1)+str(new_time_2)+day_night)
                    
                    else:
                        event_times.append(event_date_element.text[-13:])
            except TimeoutException:  # if the date isn't found
                event_times.append("time unknown")

            print("Trying to fetch interest for event")

            try:
                interest_element = wait.until(EC.visibility_of_element_located((By.XPATH, full_xpath_for_interest)))
                event_interests.append(interest_element.text)
            except TimeoutException:
                event_interests.append("data_not_found")

            # For descriptions
            try:
                description_element = wait.until(EC.visibility_of_element_located((By.XPATH, full_xpath_for_description)))
                event_descriptions.append(description_element.text)
            except TimeoutException:
                event_descriptions.append("no description available")

            # For images
            print("Trying to fetch image for event")
            try:
                image_element = wait.until(EC.presence_of_element_located((By.XPATH, full_xpath_for_image)))
                image_url = image_element.get_attribute("src")
                image_urls.append(image_url)
            except TimeoutException:  # if the image URL isn't found
                image_urls.append("image_url_not_found")

            try:
                url_element = wait.until(EC.presence_of_element_located((By.XPATH, full_xpath_for_url)))
                event_url = url_element.get_attribute("href")
                event_urls.append(event_url)
            except TimeoutException:
                event_urls.append("url_not_found")

        # Create a dictionary from the lists, including the "Description" column
        data = {
            "Title": event_titles,
            "Location": event_locations,
            "Date": event_dates,
            "End Date": event_end,
            "Time": event_times,
            "Image URLs": image_urls,
            "Description": event_descriptions,
            "Link": event_urls,
            "Facebook Interests": event_interests,
            "Source Code": "fb"  
        }

        # Create a DataFrame from the dictionary
        df = pd.DataFrame(data)

        # Quit the WebDriver
        driver.quit()
        return df;
    
    def scrapeUts(self):
        # Function to add NULL for missing data
        def handle_missing_data(data):
            return data if data else "NULL"
        URL_UTS = "https://www.uts.edu.au/partners-and-community/events/whatson"
        page_uts = requests.get(URL_UTS)
        soup_uts = BeautifulSoup(page_uts.content, "html.parser")
        event_elements_uts = soup_uts.find_all("article")
        data_uts = []
        source_code = 'uts'
        for event_element in event_elements_uts:
            title_element = event_element.find("h3", class_="event__title")
            date_element = event_element.find("time")
            if title_element and date_element:
                event_title = handle_missing_data(title_element.get_text(strip=True))
                event_date = handle_missing_data(date_element.get_text(strip=True))
                end_date = handle_missing_data(date_element.get_text(strip=True))
                event_time_element = event_element.find_next("div", class_="event__time")
                event_time = handle_missing_data(event_time_element.get_text(strip=True)) if event_time_element else "NULL"
                link_element = event_element.find("a", class_="event--image__link")
                event_link = "https://www.uts.edu.au" + link_element["href"] if link_element else "no link available"
                # Adding "description" column with "NULL" for consistency
                event_description = "no description available"
                data_uts.append([event_title,"The University of Technology Sydney", event_date[:6], end_date[-17:-11], event_time[:8], "no image available", event_description, event_link, "NA", source_code])
                df_uts = pd.DataFrame(data_uts, columns=["Title", "Location", "Date", "End Date", "Time", "Image URLs", "Description", "Link", "Facebook Interests", "Source Code"])
                return df_uts

    def scrapeUnsw(self):
        URL_UNSW = "https://www.student.unsw.edu.au/events"
        page_unsw = requests.get(URL_UNSW)
        soup_unsw = BeautifulSoup(page_unsw.content, "html.parser")
        titles = []
        locations = []
        dates = []
        end_dates = []
        times = []
        images=[]
        descriptions = []
        links=[]
        interests = []
        source_code = []
        event_elements_unsw = soup_unsw.find_all("article")

        for event_element in event_elements_unsw:
            title_element = event_element.find("h3")
            description_element = event_element.find("p")
            time_element = event_element.find("time")
            link_element = event_element.find("a", href=True)
            titles.append(title_element.text.strip() if title_element else "no title found")
            descriptions.append(description_element.text.strip() if description_element else "no description available")
            needs_end = False
            dates.append(time_element.text.strip()[0:6] if time_element and "," not in time_element.text.strip()[0:6] else "no start specified")
            end_dates.append(time_element.text.strip()[0:6] if time_element and "," not in time_element.text.strip()[0:6] else "no end specified")
            locations.append("The University of New South Wales")
            temp_time = time_element.text.strip()[-6:] if time_element and ":" in time_element.text.strip()[-6:-2] else "no time specified"
            temp_time = ' '.join([temp_time[:4], temp_time[4:]])
            times.append(temp_time)
            images.append("no image available")
            interests.append("NA")
            links.append("https://www.student.unsw.edu.au/"+link_element["href"] if link_element else "")
            source_code.append('unsw')

        df_unsw = pd.DataFrame(list(zip(titles, locations, dates, end_dates, times, images, descriptions, links, interests, source_code)), columns=["Title", "Location", "Date", "End Date", "Time", "Image URLs", "Description", "Link", "Facebook Interests", "Source Code"])
        return df_unsw
    
    def scrapeUsyd(self):
        URL_SYDNEY = "https://www.sydney.edu.au/engage/global-engagement/events.html"
        page_sydney = requests.get(URL_SYDNEY)
        soup_sydney = BeautifulSoup(page_sydney.content, "html.parser")
        event_elements_sydney = soup_sydney.find_all("ul")[5]
        data_sydney = []
        source_code = 'usyd'
        for event_element in event_elements_sydney.find_all("li"):
            event_text = event_element.get_text(strip=True)
            event_parts = event_text.split(":", 1)
            if len(event_parts) == 2:
                event_date, event_title = event_parts
                data_sydney.append([event_title.strip(),"Sydney University",event_date.strip()[3:9],event_date.strip()[3:9],"no time available","no image available","no description available", "no link available","NA", source_code])
        df_sydney = pd.DataFrame(data_sydney, columns=["Title", "Location", "Date", "End Date", "Time", "Image URLs", "Description", "Link", "Facebook Interests", "Source Code"])
        return df_sydney
    
    def scrapeWsu(self):
        URL_WSU = "https://www.westernsydney.edu.au/home/events"
        page_wsu = requests.get(URL_WSU)
        soup_wsu = BeautifulSoup(page_wsu.content, "html.parser")
        event_details_div_wsu = soup_wsu.find("div", class_="event_details")
        event_elements_wsu = event_details_div_wsu.find_all("li", class_="lst__items_date")
        data_wsu = []
        source_code = 'wsu'
        for event_element in event_elements_wsu:
            event_date = event_element.find("span", class_="date_day").get_text()
            end_date = event_date
            event_time = "no time available"
            event_month = event_element.find("span", class_="date_month").get_text()
            event_title = event_element.find("a", class_="a__b")
            event_description = event_element.find("p", class_="no_marg_padd").get_text()
            event_title_link = event_title['href']
            event_title_text = event_title.get_text()
            data_wsu.append([event_title_text, "Western Sydney University", f"{event_date} {event_month}",f"{event_date} {event_month}", event_time, "no image available", event_description, event_title_link, "NA", source_code])
        df_wsu = pd.DataFrame(data_wsu, columns=["Title", "Location", "Date", "End Date", "Time", "Image URLs", "Description", "Link", "Facebook Interests", "Source Code"])
        return df_wsu