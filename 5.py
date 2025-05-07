# !pip install selenium python-dotenv beautifulsoup4
import os
import json
import warnings
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
load_dotenv()

class Experience:
    def __init__(self, position_title, from_date, to_date, duration, location, description, institution_name, linkedin_url):
        self.__dict__.update(locals())
        del self.__dict__["self"]

class Education:
    def __init__(self, from_date, to_date, description, degree, institution_name, linkedin_url):
        self.__dict__.update(locals())
        del self.__dict__["self"]

class LinkedInScraper:
    def __init__(self, driver, linkedin_url):
        self.driver = driver
        self.linkedin_url = linkedin_url
        self.profile_data = {}
        self.experiences = []
        self.educations = []

    def add_experience(self, exp):
        self.experiences.append(exp.__dict__)

    def add_education(self, edu):
        self.educations.append(edu.__dict__)

    def wait_for_element_to_load(self, by=By.CLASS_NAME, name=None, base=None):
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        base = base or self.driver
        return WebDriverWait(base, 10).until(EC.presence_of_element_located((by, name)))

    def scroll_to_half(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        sleep(2)

    def scroll_to_bottom(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(2)

    def focus(self):
        self.driver.execute_script("window.focus();")
        sleep(2)

    def extract_basic_info(self):
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'lxml')

        name_tag = soup.find('h1')
        self.profile_data['name'] = name_tag.get_text().strip() if name_tag else "Not found"

        headline_tag = soup.find('div', {'class': 'text-body-medium break-words'})
        self.profile_data['headline'] = headline_tag.get_text().strip() if headline_tag else "Not found"

        about_tag = soup.find('div', {'class': 'display-flex ph5 pv3'})
        self.profile_data['about'] = about_tag.get_text().strip() if about_tag else "Not found"

        self.profile_data['url'] = self.linkedin_url

    def get_experiences(self):
        url = os.path.join(self.linkedin_url, "details/experience")
        self.driver.get(url)
        self.focus()
        main = self.wait_for_element_to_load(by=By.TAG_NAME, name="main")
        self.scroll_to_half()
        self.scroll_to_bottom()
        main_list = self.wait_for_element_to_load(name="pvs-list__container", base=main)

        for position in main_list.find_elements(By.CLASS_NAME, "pvs-list__paged-list-item"):
            position = position.find_element(By.CSS_SELECTOR, "div[data-view-name='profile-component-entity']")
            company_logo_elem, position_details = position.find_elements(By.XPATH, "*")

            company_linkedin_url = company_logo_elem.find_element(By.XPATH, "*").get_attribute("href")
            if not company_linkedin_url:
                continue

            position_details_list = position_details.find_elements(By.XPATH, "*")
            position_summary_details = position_details_list[0] if len(position_details_list) > 0 else None
            position_summary_text = position_details_list[1] if len(position_details_list) > 1 else None
            outer_positions = position_summary_details.find_element(By.XPATH, "*").find_elements(By.XPATH, "*")

            position_title, company, work_times, location = "", "", "", ""
            if len(outer_positions) == 4:
                position_title = outer_positions[0].find_element(By.TAG_NAME, "span").text
                company = outer_positions[1].find_element(By.TAG_NAME, "span").text
                work_times = outer_positions[2].find_element(By.TAG_NAME, "span").text
                location = outer_positions[3].find_element(By.TAG_NAME, "span").text
            elif len(outer_positions) == 3:
                if "·" in outer_positions[2].text:
                    position_title = outer_positions[0].find_element(By.TAG_NAME, "span").text
                    company = outer_positions[1].find_element(By.TAG_NAME, "span").text
                    work_times = outer_positions[2].find_element(By.TAG_NAME, "span").text
                else:
                    company = outer_positions[0].find_element(By.TAG_NAME, "span").text
                    work_times = outer_positions[1].find_element(By.TAG_NAME, "span").text
                    location = outer_positions[2].find_element(By.TAG_NAME, "span").text
            else:
                company = outer_positions[0].find_element(By.TAG_NAME, "span").text

            times = work_times.split("·")[0].strip() if work_times else ""
            duration = work_times.split("·")[1].strip() if "·" in work_times else None
            from_date = " ".join(times.split(" ")[:2]) if times else ""
            to_date = " ".join(times.split(" ")[3:]) if times else ""

            if position_summary_text and position_summary_text.find_elements(By.CLASS_NAME, "pvs-list__container"):
                inner_positions = (position_summary_text.find_element(By.CLASS_NAME, "pvs-list__container")
                                  .find_elements(By.CLASS_NAME, "pvs-list__paged-list-item"))
            else:
                inner_positions = []

            if len(inner_positions) > 1:
                for description in inner_positions:
                    res = description.find_element(By.TAG_NAME, "a").find_elements(By.XPATH, "*")
                    position_title_elem = res[0] if len(res) > 0 else None
                    work_times_elem = res[1] if len(res) > 1 else None
                    location_elem = res[2] if len(res) > 2 else None

                    position_title = position_title_elem.find_element(By.TAG_NAME, "*").text if position_title_elem else ""
                    work_times = work_times_elem.text if work_times_elem else ""
                    location = location_elem.text if location_elem else ""

                    times = work_times.split("·")[0].strip() if work_times else ""
                    duration = work_times.split("·")[1].strip() if "·" in work_times else None
                    from_date = " ".join(times.split(" ")[:2]) if times else ""
                    to_date = " ".join(times.split(" ")[3:]) if times else ""

                    self.add_experience(Experience(position_title, from_date, to_date, duration, location, "", company, company_linkedin_url))
            else:
                description = position_summary_text.text if position_summary_text else ""
                self.add_experience(Experience(position_title, from_date, to_date, duration, location, description, company, company_linkedin_url))

    def get_educations(self):
        url = os.path.join(self.linkedin_url, "details/education")
        self.driver.get(url)
        self.focus()
        main = self.wait_for_element_to_load(by=By.TAG_NAME, name="main")
        self.scroll_to_half()
        self.scroll_to_bottom()
        main_list = self.wait_for_element_to_load(name="pvs-list__container", base=main)

        for position in main_list.find_elements(By.CLASS_NAME, "pvs-list__paged-list-item"):
            position = position.find_element(By.CSS_SELECTOR, "div[data-view-name='profile-component-entity']")
            institution_logo_elem, position_details = position.find_elements(By.XPATH, "*")

            institution_linkedin_url = institution_logo_elem.find_element(By.XPATH, "*").get_attribute("href")
            position_details_list = position_details.find_elements(By.XPATH, "*")
            position_summary_details = position_details_list[0] if len(position_details_list) > 0 else None
            position_summary_text = position_details_list[1] if len(position_details_list) > 1 else None

            outer_positions = position_summary_details.find_element(By.XPATH, "*").find_elements(By.XPATH, "*")
            institution_name = outer_positions[0].find_element(By.TAG_NAME, "span").text
            degree = outer_positions[1].find_element(By.TAG_NAME, "span").text if len(outer_positions) > 1 else None

            if len(outer_positions) > 2:
                times = outer_positions[2].find_element(By.TAG_NAME, "span").text
                if times:
                    parts = times.split(" ")
                    from_date = parts[0]
                    to_date = parts[-1]
                else:
                    from_date = to_date = None
            else:
                from_date = to_date = None

            description = position_summary_text.text if position_summary_text else ""
            self.add_education(Education(from_date, to_date, description, degree, institution_name, institution_linkedin_url))

    def scrape(self):
        self.extract_basic_info()
        self.get_experiences()
        self.get_educations()
        self.profile_data['experiences'] = self.experiences
        self.profile_data['educations'] = self.educations
        return self.profile_data

# --------------------------- RUNNING SCRAPER --------------------------
driver = webdriver.Chrome()
driver.get("https://www.linkedin.com/login")

email = driver.find_element(By.ID, "username")
email.send_keys(os.getenv("EMAIL"))
password = driver.find_element(By.ID, "password")
password.send_keys(os.getenv("PASSWORD"))
password.submit()

linkedin_url = "https://www.linkedin.com/in/suraj-reddy-atla"
driver.get(linkedin_url)

scraper = LinkedInScraper(driver, linkedin_url)
data = scraper.scrape()

with open('data/profile_data_tutorial.json', 'w') as f:
    json.dump(data, f, indent=4)

driver.quit()
