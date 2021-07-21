from string import ascii_lowercase
import csv
import time
from string import ascii_lowercase

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

opts = Options()
opts.add_argument("user-agent=Ferdinand")


PATH = "/home/ferdinand/chromedriver"
driver = webdriver.Chrome(PATH)
delay = 3


def get_joined_value(list, start_index, end_index):
    result = ""
    current_index = start_index
    while current_index < end_index:
        result += " {}".format(list[current_index])
        current_index += 1

    return result.strip()


def get_index_of_string_containing(list, string):
    for index, value in enumerate(list):
        if string in value:
            return index
    return None


def get_doctor_data(element):
    split = element.get_attribute('innerText').split("\n")
    split = [s.replace('\xa0', ' ') for s in split]
    name = split[0]
    specialization = ""

    phone = [x for x in split if "Phone:" in x]
    if phone and len(phone) > 0:
        phone = phone[0]
        phone = phone.split(":")[1].strip()
    fax = [x for x in split if "Fax:" in x]
    if fax and len(fax) > 0:
        fax = fax[0]
        fax = fax.split(":")[1].strip()

    # join the list starting from specialization to end
    spec_idx = None
    try:
        spec_idx = split.index("Area(s) of Specialization:")
    except Exception:
        pass

    if spec_idx:
        specialization = get_joined_value(
            split, spec_idx + 2, len(split))

    # get starting index
    loc_idx = None
    try:
        loc_idx = split.index("Location of Practice:")
    except Exception:
        pass

    # ending index can be phone, fax, specialization in order
    phone_idx = get_index_of_string_containing(split, "Phone:")
    fax_idx = get_index_of_string_containing(split, "Fax:")

    location = ""

    if loc_idx:
        last_index = len(split)
        if phone_idx:
            last_index = phone_idx
        elif fax_idx:
            last_index = fax_idx
        elif spec_idx:
            last_index = spec_idx

        location = get_joined_value(split, loc_idx + 1, last_index)

    data = {
        "name": name,
        "phone": phone,
        "fax": fax,
        "location": location,
        "specialization": specialization
    }

    return data


def page_jump(current_page):
    # skip all other pages until start page
    if current_page < start_page:
        page_jumps = int(start_page / 5)
        remainder = start_page % 5 - 1

        while page_jumps > 0:
            time.sleep(1)
            element = WebDriverWait(driver, delay).until(
                EC.presence_of_element_located((By.LINK_TEXT, 'Next 5')))

            next_page_btn = driver.find_element_by_link_text("Next 5")
            next_page_btn.send_keys(Keys.RETURN)
            page_jumps -= 1
            current_page += 5

        if page_jumps == 0:
            while remainder > 0:
                time.sleep(1)
                element = WebDriverWait(driver, delay).until(
                    EC.presence_of_element_located((By.LINK_TEXT, str(current_page + 1))))
                next_page_btn = driver.find_element_by_link_text(
                    str(current_page + 1))
                next_page_btn.send_keys(Keys.RETURN)
                remainder -= 1
                current_page += 1


def go_to_next_page(current_page):
    if current_page % 5 == 0:
        element = WebDriverWait(driver, delay).until(
            EC.presence_of_element_located((By.LINK_TEXT, 'Next 5')))
        next_page_btn = driver.find_element_by_link_text("Next 5")
        next_page_btn.send_keys(Keys.RETURN)
    else:
        element = WebDriverWait(driver, delay).until(
            EC.presence_of_element_located((By.LINK_TEXT, str(current_page + 1))))
        next_page_btn = driver.find_element_by_link_text(
            str(current_page + 1))
        next_page_btn.send_keys(Keys.RETURN)


def main_stuff(current_page, is_last_page):
    page_jump(current_page)
    # invoke refresh every 5 pages to prevent network errors
    if current_page % 5 == 0:
        driver.refresh()

    time.sleep(1)
    
    element = WebDriverWait(driver, delay).until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, '.doctor-search-results article')))
    doctor_results = driver.find_elements_by_css_selector(
        ".doctor-search-results article")

    for element in doctor_results:
        data = get_doctor_data(element)
        doctors.append(data)

    if not is_last_page:
        go_to_next_page(current_page)


def retry_main_stuff(current_page, retries, is_last_page):
    i = 0
    while i < retries: 
        try:
            main_stuff(current_page, is_last_page)
            break
        except Exception as e:
            print("ERROR while parsing: {}".format(e))
            driver.refresh()
        i += 1


skip = 'abcdefghij'

for c in ascii_lowercase:
    if c in skip:
        continue

    url = "https://doctors.cpso.on.ca/?search=general"
    driver.get(url)
    assert "CPSO - Find a Doctor" in driver.title

    driver.refresh()
    print("Starting with letter {}".format(c))
    time.sleep(5)

    WebDriverWait(driver, delay).until(
        EC.presence_of_element_located((By.ID, 'txtLastName')))
    input_text = driver.find_element_by_id("txtLastName")
    input_text.send_keys(c)

    WebDriverWait(driver, delay).until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, '#general-search-tab input.submit')))
    search_btn = driver.find_element_by_css_selector(
        "#general-search-tab input.submit")
    search_btn.send_keys(Keys.RETURN)

    WebDriverWait(driver, delay).until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "div.row:nth-child(3) > div:nth-child(2) > p:nth-child(1)")))
    last_page_element = driver.find_element_by_css_selector(
        "div.row:nth-child(3) > div:nth-child(2) > p:nth-child(1)")
    page_text = last_page_element.get_attribute("innerText").split(" ")
    last_page = int(page_text[-1])

    start_page = 1
    current_page = 1
    # last_page = 1000

    doctors = []

    try:
        while current_page <= last_page:
            is_last_page = current_page == last_page
            retry_main_stuff(current_page, 5, is_last_page)
            
            current_page += 1
                
    except Exception as e:
        print("ERROR: {}".format(e))
        print("current char", c)
        print("current page", current_page)
        pass
    
    # save the file per letter and pages
    if current_page > start_page:
        print("Saving file")
        with open('letter-{}__pages-{}-{}.csv'.format(c, start_page, current_page), mode='w') as d:
            fieldnames = ['name', 'phone', 'fax', 'location', 'specialization']
            writer = csv.DictWriter(d, fieldnames=fieldnames)

            for doctor in doctors:
                name = doctor.get('name', '')
                phone = doctor.get('phone', '')
                fax = doctor.get('fax', '')
                location = doctor.get('location', '')
                specialization = doctor.get('specialization', '')
                writer.writerow({
                    'name': name,
                    'phone': phone,
                    'fax': fax,
                    'location': location,
                    'specialization': specialization
                })


driver.close()
