from pyquery import PyQuery as jquery
import MySQLdb
import re
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from selenium.common.exceptions import *

host = 'https://future-students.uq.edu.au'

connection = MySQLdb.connect('localhost', 'root', '19941005', 'uq_receptionist')
connection.set_character_set('utf8')
connection.cursor().execute('SET NAMES utf8;')
connection.cursor().execute('SET CHARACTER SET utf8;')
connection.cursor().execute('SET character_set_connection=utf8;')

# driver = webdriver.Chrome(executable_path="/Users/chknight/Code/chromedriver")
driver = webdriver.PhantomJS()
driver.maximize_window()


def find_element(xpath):
    time = 10
    while time > 0:
        try:
            driver.find_element_by_xpath(xpath=xpath)
        except:
            time -= 1


# clean the tag in html
def clean_text(raw_html):
    cleaner = re.compile('<.*?>')
    cleantext = re.sub(cleaner, '', raw_html)
    cleantext = cleantext.replace('\n', ' ')
    cleantext = cleantext.replace('&gt;', '')
    cleantext = re.sub(' +', ' ', cleantext)
    return cleantext


def fetch_course(url):
    courselist_page = jquery(url=url)
    courses = courselist_page.find('tr>td:first>a')
    result = []
    for course in courses.items():
        print(course.text())
        if 'Alrady' not in course.text():
            result.append(course.text())
    return result


def retrieve_program_page(url):
    driver.get(url=url)
    driver.save_screenshot('screenshot.png')
    try:
        if driver.find_element_by_xpath("//a[text()=\"I'm a domestic student\"]"):
            driver.find_element_by_xpath("//a[text()=\"I'm a domestic student\"]").click()
    except:
        print("Already click this button")
    try:
        head = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//h1')))
        page = jquery(driver.find_element_by_xpath("//html").get_attribute('innerHTML').replace('&gt;', '>'))
        print(head.text)
        head = clean_text(head.text)
        print(head)
        location = driver.find_element_by_xpath("//*[@data-sinet='LOCATION']").text
        duration = driver.find_element_by_xpath("//div[@class='program__duration-value sinet-field']").text
        commencing = driver.find_element_by_xpath("//div[@class='program__commencement-value sinet-field']").text
        print(location)
        print(duration)
        print(commencing)

        # fee of the program
        driver.find_element_by_xpath("//a[text()='Fees and scholarships']").click()
        fee = page.find('span[data-sinet="StudentInfo > Domestic > IndicativeFee > CSP"]').text()
        print(fee)


        # major or the program
        majors = []
        majorsElements = page.find('h3[data-sinet="[Plan] TITLE"]')
        for majorsElement in majorsElements.items():
            print(majorsElement.text())
            majors.append(majorsElement.text())
        majors = ','.join(majors)



        # summary of the program
        program_code = page.find("ul[class='program__table'] div[data-sinet='CODE']").text()
        program_unit = page.find("ul[class='program__table'] div[data-sinet='UNITS']").text()
        program_level = page.find("ul[class='program__table'] div[data-sinet='LEVEL_VALUE']").text()
        program_faculty = page.find("ul[class='program__table'] div[data-sinet='Faculty > FACULTY_KEY']").text()
        print(program_code)
        print(program_unit)
        print(program_level)
        print(program_faculty)

        course_url = page.find('#program-structure > a:nth-child(2)')
        course_url = course_url.attr['href']
        print(course_url)
        courses = "The course list is still not available"
        if course_url is not None:
            courses = fetch_course(course_url)
            courses = ','.join(courses)
        entry_requirements = page.find('#entry-requirements')
        entry_requirements = clean_text(entry_requirements.text().replace('Entry requirements ', ''))

        connection.cursor().execute('''INSERT into program_domestic (title, location, duration, commencing, fee, majors, program_code, program_unit, program_level, program_faculty, courses, entry_requirements)
                                values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', (
        head, location, duration, commencing, fee, majors, program_code, program_unit, program_level, program_faculty,
        courses, entry_requirements))
        connection.commit()
    except TimeoutException:
        print('No such program for international student')


# retrieve one page
def retrieve_page(page):
    program_lists = page.find(".program__secondary-link")
    for program in program_lists.items():
        retrieve_program_page(host + program.attr['href'])


# start the program
def retrieve_pages():
    url = "https://future-students.uq.edu.au/study/find-a-program/listing/undergraduate"
    page = jquery(url=url)
    retrieve_page(page)
    url = "https://future-students.uq.edu.au/study/find-a-program/listing/postgraduate"
    page = jquery(url=url)
    retrieve_page(page)

retrieve_pages()
