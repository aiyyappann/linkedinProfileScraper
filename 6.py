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
        try:
            return WebDriverWait(base, 10).until(EC.presence_of_element_located((by, name)))
        except:
            return None

    def scroll_to_half(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        sleep(2)

    def scroll_to_bottom(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(2)

    def focus(self):
        self.driver.execute_script("window.focus();")
        sleep(2)

    def is_open_to_work(self):
        try:
            title_text = self.driver.find_element(By.CLASS_NAME, "pv-top-card-profile-picture") \
                .find_element(By.TAG_NAME, "img") \
                .get_attribute("title")
            return "#OPEN_TO_WORK" in title_text
        except:
            return False

    def extract_basic_info(self):
        try:
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')

            name_tag = soup.find('h1')
            self.profile_data['name'] = name_tag.get_text().strip() if name_tag else "Not found"

            headline_tag = soup.find('div', {'class': 'text-body-medium break-words'})
            self.profile_data['headline'] = headline_tag.get_text().strip() if headline_tag else "Not found"

            about_tag = soup.find('div', {'class': 'display-flex ph5 pv3'})
            self.profile_data['about'] = about_tag.get_text().strip() if about_tag else "Not found"

            self.profile_data['url'] = self.linkedin_url
            self.profile_data['open_to_work'] = self.is_open_to_work()
        except:
            self.profile_data['name'] = "Not found"
            self.profile_data['headline'] = "Not found"
            self.profile_data['about'] = "Not found"
            self.profile_data['open_to_work'] = False

    def get_experiences(self):
        try:
            url = os.path.join(self.linkedin_url, "details/experience")
            self.driver.get(url)
            self.focus()

            main = self.wait_for_element_to_load(by=By.TAG_NAME, name="main")
            if not main: return
            self.scroll_to_half()
            self.scroll_to_bottom()
            main_list = self.wait_for_element_to_load(name="pvs-list__container", base=main)
            if not main_list: return

            for position in main_list.find_elements(By.CLASS_NAME, "pvs-list__paged-list-item"):
                try:
                    position = position.find_element(By.CSS_SELECTOR, "div[data-view-name='profile-component-entity']")
                    company_logo_elem, position_details = position.find_elements(By.XPATH, "*")

                    company_linkedin_url = company_logo_elem.find_element(By.XPATH, "*").get_attribute("href") or ""
                    position_details_list = position_details.find_elements(By.XPATH, "*")
                    position_summary_details = position_details_list[0] if len(position_details_list) > 0 else None
                    position_summary_text = position_details_list[1] if len(position_details_list) > 1 else None
                    outer_positions = position_summary_details.find_element(By.XPATH, "*").find_elements(By.XPATH, "*")

                    position_title, company, work_times, location = "", "", "", ""
                    if len(outer_positions) == 4:
                        position_title = outer_positions[0].text
                        company = outer_positions[1].text
                        work_times = outer_positions[2].text
                        location = outer_positions[3].text
                    elif len(outer_positions) == 3:
                        if "·" in outer_positions[2].text:
                            position_title = outer_positions[0].text
                            company = outer_positions[1].text
                            work_times = outer_positions[2].text
                        else:
                            company = outer_positions[0].text
                            work_times = outer_positions[1].text
                            location = outer_positions[2].text
                    else:
                        company = outer_positions[0].text

                    times = work_times.split("·")[0].strip() if work_times else ""
                    duration = work_times.split("·")[1].strip() if "·" in work_times else None
                    from_date = " ".join(times.split(" ")[:2]) if times else ""
                    to_date = " ".join(times.split(" ")[3:]) if times else ""

                    inner_positions = []
                    if position_summary_text:
                        container = position_summary_text.find_elements(By.CLASS_NAME, "pvs-list__container")
                        if container:
                            inner_positions = container[0].find_elements(By.CLASS_NAME, "pvs-list__paged-list-item")

                    if len(inner_positions) > 1:
                        for description in inner_positions:
                            try:
                                res = description.find_element(By.TAG_NAME, "a").find_elements(By.XPATH, "*")
                                position_title_elem = res[0] if len(res) > 0 else None
                                work_times_elem = res[1] if len(res) > 1 else None
                                location_elem = res[2] if len(res) > 2 else None

                                position_title = position_title_elem.text if position_title_elem else ""
                                work_times = work_times_elem.text if work_times_elem else ""
                                location = location_elem.text if location_elem else ""

                                times = work_times.split("·")[0].strip() if work_times else ""
                                duration = work_times.split("·")[1].strip() if "·" in work_times else None
                                from_date = " ".join(times.split(" ")[:2]) if times else ""
                                to_date = " ".join(times.split(" ")[3:]) if times else ""

                                self.add_experience(Experience(position_title, from_date, to_date, duration, location, "", company, company_linkedin_url))
                            except:
                                continue
                    else:
                        description = position_summary_text.text if position_summary_text else ""
                        self.add_experience(Experience(position_title, from_date, to_date, duration, location, description, company, company_linkedin_url))
                except:
                    continue
        except:
            pass

    def get_educations(self):
        try:
            url = os.path.join(self.linkedin_url, "details/education")
            self.driver.get(url)
            self.focus()

            main = self.wait_for_element_to_load(by=By.TAG_NAME, name="main")
            if not main: return
            self.scroll_to_half()
            self.scroll_to_bottom()

            main_list = self.wait_for_element_to_load(name="pvs-list__container", base=main)
            if not main_list: return

            for position in main_list.find_elements(By.CLASS_NAME, "pvs-list__paged-list-item"):
                try:
                    position = position.find_element(By.CSS_SELECTOR, "div[data-view-name='profile-component-entity']")
                    institution_logo_elem, position_details = position.find_elements(By.XPATH, "*")
                    institution_linkedin_url = institution_logo_elem.find_element(By.XPATH, "*").get_attribute("href")

                    position_details_list = position_details.find_elements(By.XPATH, "*")
                    position_summary_details = position_details_list[0] if len(position_details_list) > 0 else None
                    position_summary_text = position_details_list[1] if len(position_details_list) > 1 else None

                    outer_positions = position_summary_details.find_element(By.XPATH, "*").find_elements(By.XPATH, "*")
                    institution_name = outer_positions[0].text
                    degree = outer_positions[1].text if len(outer_positions) > 1 else None

                    from_date, to_date = None, None
                    if len(outer_positions) > 2:
                        times = outer_positions[2].text
                        parts = times.split(" ")
                        from_date = parts[0] if parts else None
                        to_date = parts[-1] if parts else None

                    description = position_summary_text.text if position_summary_text else ""
                    self.add_education(Education(from_date, to_date, description, degree, institution_name, institution_linkedin_url))
                except:
                    continue
        except:
            pass
    def get_licenses_and_certifications(self):
        try:
            url = os.path.join(self.linkedin_url, "details/licenses-certifications")
            self.driver.get(url)
            self.focus()
            self.scroll_to_half()
            self.scroll_to_bottom()
            main = self.wait_for_element_to_load(by=By.TAG_NAME, name="main")
            main_list = self.wait_for_element_to_load(name="pvs-list__container", base=main)
            if not main_list:
                print("Main list not found.")
                return

            certs = []
            for cert in main_list.find_elements(By.CLASS_NAME, "pvs-list__paged-list-item"):
                try:
                    content = cert.text.split('\n')
                    name = content[0] if len(content) > 0 else None
                    org = content[1] if len(content) > 1 else None
                    issued = content[2] if len(content) > 2 and "Issued" in content[2] else None
                    credential_url = ""

                    # Handle extracting the credential URL
                    try:
                        credential_url = cert.find_element(By.TAG_NAME, "a").get_attribute("href")
                    except Exception as e:
                        print("Failed to get credential URL:", e)

                    certs.append({
                        "name": name,
                        "issuing_organization": org,
                        "issued": issued,
                        "credential_url": credential_url
                    })
                except Exception as e:
                    print("Error extracting certification details:", e)
                    continue

            self.profile_data['licenses_and_certifications'] = certs
        except Exception as e:
            print("Failed to extract licenses & certifications:", e)
            self.profile_data['licenses_and_certifications'] = []


    def get_interests(self):
        try:
            url = os.path.join(self.linkedin_url, "details/interests")
            self.driver.get(url)
            self.focus()

            main = self.wait_for_element_to_load(by=By.TAG_NAME, name="main")
            if not main:
                print("Main section not found for interests.")
                return

            self.scroll_to_half()
            self.scroll_to_bottom()

            interest_blocks = main.find_elements(By.CLASS_NAME, "pvs-list__paged-list-item")
            if not interest_blocks:
                print("No interests found.")
                return

            interests = []
            for item in interest_blocks:
                try:
                    name_element = item.find_element(By.TAG_NAME, "span")
                    name = name_element.text.strip()
                    if name:
                        interests.append(name)
                except Exception as e:
                    print("Error extracting an interest:", e)
                    continue

            self.profile_data['interests'] = interests

        except Exception as e:
            print("Failed to extract interests:", e)
            self.profile_data['interests'] = []



    def get_skills(self):
        try:
            url = os.path.join(self.linkedin_url, "details/skills")
            self.driver.get(url)
            self.focus()
            self.scroll_to_half()
            self.scroll_to_bottom()
            main = self.wait_for_element_to_load(by=By.TAG_NAME, name="main")
            main_list = self.wait_for_element_to_load(name="pvs-list__container", base=main)

            skills = []
            for item in main_list.find_elements(By.CLASS_NAME, "pvs-list__paged-list-item"):
                try:
                    skill = item.find_element(By.TAG_NAME, "span").text
                    skills.append(skill)
                except:
                    continue
            self.profile_data['skills'] = skills
        except Exception as e:
            print("Failed to extract skills:", e)
            self.profile_data['skills'] = []

    def get_publications(self):
        try:
            url = os.path.join(self.linkedin_url, "details/publications")
            self.driver.get(url)
            self.focus()
            self.scroll_to_half()
            self.scroll_to_bottom()
            main = self.wait_for_element_to_load(by=By.TAG_NAME, name="main")
            main_list = self.wait_for_element_to_load(name="pvs-list__container", base=main)

            pubs = []
            for pub in main_list.find_elements(By.CLASS_NAME, "pvs-list__paged-list-item"):
                try:
                    content = pub.text.split('\n')
                    title = content[0] if len(content) > 0 else ""
                    publisher = content[1] if len(content) > 1 else ""
                    date = content[2] if len(content) > 2 else ""
                    pubs.append({
                        "title": title,
                        "publisher": publisher,
                        "date": date
                    })
                except:
                    continue
            self.profile_data['publications'] = pubs
        except Exception as e:
            print("Failed to extract publications:", e)
            self.profile_data['publications'] = []

    def get_projects(self):
        try:
            url = os.path.join(self.linkedin_url, "details/projects")
            self.driver.get(url)
            self.focus()
            self.scroll_to_half()
            self.scroll_to_bottom()
            main = self.wait_for_element_to_load(by=By.TAG_NAME, name="main")
            main_list = self.wait_for_element_to_load(name="pvs-list__container", base=main)

            projects = []
            for project in main_list.find_elements(By.CLASS_NAME, "pvs-list__paged-list-item"):
                try:
                    content = project.text.split('\n')
                    name = content[0] if len(content) > 0 else ""
                    date = content[1] if len(content) > 1 else ""
                    description = " ".join(content[2:]) if len(content) > 2 else ""
                    projects.append({
                        "name": name,
                        "date": date,
                        "description": description
                    })
                except:
                    continue
            self.profile_data['projects'] = projects
        except Exception as e:
            print("Failed to extract projects:", e)
            self.profile_data['projects'] = []

    def get_languages(self):
        try:
            url = os.path.join(self.linkedin_url, "details/languages")
            self.driver.get(url)
            self.focus()
            self.scroll_to_half()
            self.scroll_to_bottom()

            main = self.wait_for_element_to_load(by=By.TAG_NAME, name="main")
            if not main:
                raise Exception("Main tag not found.")

            main_list = self.wait_for_element_to_load(name="pvs-list__container", base=main)
            if not main_list:
                raise Exception("Languages list container not found.")

            languages = []
            items = main_list.find_elements(By.CLASS_NAME, "pvs-list__paged-list-item")

            for lang in items:
                try:
                    text_lines = lang.text.strip().split('\n')
                    language = text_lines[0] if len(text_lines) > 0 else "Unknown"
                    proficiency = text_lines[1] if len(text_lines) > 1 else "Not specified"
                    languages.append({
                        "language": language,
                        "proficiency": proficiency
                    })
                except Exception as inner_err:
                    print("Failed to parse language item:", inner_err)
                    continue

            self.profile_data['languages'] = languages

        except Exception as outer_err:
            print("Failed to extract languages section:", outer_err)
            self.profile_data['languages'] = []


    def scrape(self):
        try:
            self.extract_basic_info()
        except Exception as e:
            print("Basic info error:", e)

        try:
            self.get_experiences()
        except Exception as e:
            print("Experience extraction error:", e)

        try:
            self.get_educations()
        except Exception as e:
            print("Education extraction error:", e)

        try:
            self.get_licenses_and_certifications()
        except Exception as e:
            print("Licenses & Certifications error:", e)

        try:
            self.get_skills()
        except Exception as e:
            print("Skills extraction error:", e)

        try:
            self.get_publications()
        except Exception as e:
            print("Publications extraction error:", e)

        try:
            self.get_interests()  # ✅ Add this line
        except Exception as e:
            print("Interests extraction error:", e)

        try:
            self.get_projects()
        except Exception as e:
            print("Projects extraction error:", e)

        try:
            self.profile_data["open_to_work"] = self.is_open_to_work()
        except Exception as e:
            print("Open to Work status check failed:", e)
            self.profile_data["open_to_work"] = False
        try:
            self.get_languages()  # Added method to scrape languages
        except Exception as e:
            print("Languages extraction error:", e)


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

linkedin_url = "https://www.linkedin.com/in/laxmimerit"
driver.get(linkedin_url)

scraper = LinkedInScraper(driver, linkedin_url)
data = scraper.scrape()

os.makedirs("data", exist_ok=True)
with open('data/profile_data_tutorial.json', 'w') as f:
    json.dump(data, f, indent=4)

driver.quit()
