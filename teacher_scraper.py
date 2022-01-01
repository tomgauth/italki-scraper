from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
import time
from datetime import datetime, timedelta
import csv
from pathlib import Path
import re
import os


def get_teacher_page(teacher_id):
	options = Options()
	options.headless = True
	options.add_argument("--window-size=1920,1200")
	options.add_argument('--lang=es')
	driver = webdriver.Chrome(options=options)
	driver.get(f"https://www.italki.com/teacher/{teacher_id}/french?hl=en")
	driver.maximize_window()
	return driver



def remove_header(driver):	
	try:
		bar = driver.find_element_by_xpath(".//div[@class='flex flex-row items-center px-4 py-3 md:px-10 md:py-4 Header-banner']")
		driver.execute_script("""var element = arguments[0];
								 element.parentNode.removeChild(element);""", bar)
	except:
		pass


def last_online(driver):	
	card = driver.find_element_by_xpath(".//div[@class='teacherCard-left']")
	return card.text


def card_right(driver):	
	result = {}
	card = driver.find_element_by_xpath(".//div[@class='teacherCard-right-body']")
	result['rating'] = float(card.find_element_by_xpath(".//div[@class='italki-ratings leading-none']").text)
	spans = card.find_elements_by_xpath(".//span")
	result['total_lessons'] = int(re.findall(r"\d+", spans[0].text)[0])
	result['total_students'] = int(re.findall(r"\d+", spans[1].text)[0])
	result['lessons_per_student'] = round(result['total_lessons'] / result['total_students'], 2)
	return result
	
def card_middle(driver):
	result = {}	
	card = driver.find_element_by_xpath(".//div[@class='teacherCard-middle']")
	result['tagline'] = card.find_element_by_xpath(".//div[@class='teacherCard-personalInfo']").text
	spans = card.find_elements_by_xpath(".//span")
	result['from'] = spans[2].text
	result['location'] = spans[3].text
	result['timezone'] = spans[5].text
	return result

def teacher_since(driver):	
	div_teacher_time = driver.find_element_by_xpath(".//span[@class='aboutMeTime']").text
	teacher_time = re.sub('italki teacher since ', '', div_teacher_time)
	teacher_time = re.sub(',', '', teacher_time)
	date_format = "%b %d %Y"
	formatted_date = datetime.strptime(teacher_time, date_format).strftime("%m/%d/%Y")
	return formatted_date

def card_statistics(driver):
	result = {}	
	card_statistics = driver.find_element_by_xpath(".//div[@class='teacherCard-box']")
	divs = card_statistics.find_elements_by_xpath(".//div[@class='statistic']")
	comp_lessons_rows = divs[0].find_elements_by_xpath(".//span[@class='ProgressBar-col-number-bg']")
	result['num_lessons_2months_ago'] = int(comp_lessons_rows[0].text)
	result['num_lessons_1month_ago'] = int(comp_lessons_rows[1].text)
	result['num_lessons_last_month'] = int(comp_lessons_rows[2].text)
		
	response_rate = divs[1].find_element_by_xpath(".//div[@class='statistic-number']").text
	result['response_rate'] = int(re.sub('%', '', response_rate))

	attendance_rate = divs[2].find_element_by_xpath(".//div[@class='statistic-number']").text
	result['attendance_rate'] = int(re.sub('%', '', attendance_rate))
	return result


def reviews(driver):
	result = {}	
	review_header = driver.find_element_by_xpath(".//header[@class='reviews-header']")
	spans = review_header.find_elements_by_xpath(".//span")
	num_reviews = spans[0].text
	result['num_reviews'] = int(re.sub(' Reviews', '', num_reviews))
	return num_reviews


def scrape_teacher(teacher_id):
	driver = get_teacher_page(teacher_id)
	time.sleep(3)
	row = {}
	try:
		row['last_online'] = last_online(driver)
	except:
		print("last_online failed")
		row['last_online'] = None
		pass

	try:
		row['total_lessons'] = card_right(driver)['total_lessons']
		row['total_students'] = card_right(driver)['total_students']
		row['lessons_per_student'] = card_right(driver)['lessons_per_student']
	except:
		print("total_lessons failed")
		row['total_lessons'] = None
		row['total_students'] = None
		row['lessons_per_student'] = None
		pass

	try:
		row['from'] = card_middle(driver)['from']
		row['location'] = card_middle(driver)['location']
		row['timezone'] = card_middle(driver)['timezone']
	except:
		print("from failed")
		row['from'] = None
		row['location'] = None
		row['timezone'] = None	
		pass

	try:
		row['teacher_since'] = teacher_since(driver)
	except:
		print("teacher_since failed")
		row['teacher_since'] = None
		pass

	try:
		row['num_reviews'] = reviews(driver)		
	except:
		print("num_reviews failed")
		row['num_reviews'] = None
		pass

	try:
		row['num_lessons_2months_ago'] = card_statistics(driver)['num_lessons_2months_ago'] 
		row['num_lessons_1month_ago'] = card_statistics(driver)['num_lessons_1month_ago'] 
		row['num_lessons_last_month'] = card_statistics(driver)['num_lessons_last_month'] 
		row['response_rate'] = card_statistics(driver)['response_rate'] 
		row['attendance_rate'] = card_statistics(driver)['attendance_rate'] 
	except:
		print("num_lessons_2months_ago failed")
		row['num_lessons_2months_ago'] = None
		row['num_lessons_1month_ago'] = None
		row['num_lessons_last_month'] = None
		row['response_rate'] = None
		row['attendance_rate'] = None
		pass

	return row

