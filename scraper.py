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
from teacher_scraper import *



def get_page():
	options = Options()
	options.headless = True
	options.add_argument("--window-size=1920,1200")
	options.add_argument('--lang=es')
	driver = webdriver.Chrome(options=options)
	driver.get("https://www.italki.com/teachers/french?hl=en")
	driver.maximize_window()
	driver.save_screenshot('screenshot.png')
	return driver


def click_cookie(driver):
	try:
		cookie_button = driver.find_element_by_xpath("//button[@class='ant-btn ant-btn-primary']")
		cookie_button.click()
		print("cookie window removed")
	except:
		pass

def get_total_teachers(driver):
	total = driver.find_element_by_xpath("//div[@class=' bg-gray6 rounded-1 text-tiny leading-4 text-gray3 md:ml-2 py-1 px-2 mb-1 md:mb-0']")
	total = re.findall(r"\d+", total.text)[0]
	return int(total)


def unscroll_page(driver, max_clicks=19, frequency=2):
	for attempt in range(max_clicks):
		buttons = driver.find_elements_by_xpath("//button[@class='ant-btn  w-50 ant-btn-white']")
		print(attempt, " done")
		try:
			buttons[0].click()
			print("button clicked")
		except:
			print("click failed")			
			pass
		time.sleep(frequency)	


def open_calendars(driver):
	remove_sticky_filters(driver)
	teachers = get_all_teachers(driver)
	total = len(teachers)
	successes = 0
	print("opening calendars")
	for teacher in teachers:
		try:
			tabs = teacher.find_elements_by_xpath(".//div[@class=' ant-tabs-tab']")
			calendar = tabs[1] # 2nd tab that is not active				
			calendar.click()
			successes += 1
			print(successes, "/", total, " caledars opened!")
		except:
			print("opening calendar failed for teacher: ", teacher)
			pass





def get_all_teachers(driver, limit='all'):
	all_teachers = driver.find_elements_by_class_name('teacher-card')
	return all_teachers


def create_empty_csv():
	now = datetime.now()
	date_time = now.strftime("%d-%m-%Y--%Hh%Mm%Ss")       
	csv_name = f'{date_time}.csv'
	return csv_name	

def write_to_csv(file, row):
	with open(file,'a', newline='', encoding="utf-8") as f:
		writer = csv.writer(f)
		if os.stat(file).st_size == 0:
			print('empty file creating first row')
			writer.writerow(row)		
		writer.writerow(row.values())
	f.close()


def create_csv(rows):  # create_csv(csv_name, rows)
    # creates a csv file if it doesn't already exist
    # 'numbered_category_name': numbered_category_name
    now = datetime.now()
    date_time = now.strftime("%d-%m-%Y--%Hh%Mm%Ss")       
    path = f'{date_time}.csv'
    p = Path(path)
    with open(path, 'w', newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row[0])
        for row in rows:
            writer.writerow(row.values())
    f.close()


def remove_sticky_filters(driver):
	try:
		bar = driver.find_element_by_xpath(".//div[@class='ant-row bg-bg2 border-b border-t border-gray6 h-16']")
		driver.execute_script("""var element = arguments[0];
								 element.parentNode.removeChild(element);""", bar)
	except:
		pass

def scrape_time_table(driver, teacher):
	# get the tabs	
	print('scraping time table')
	schedule = {}
	# remove_sticky_filters(driver)	
	# tabs = teacher.find_elements_by_xpath(".//div[@class=' ant-tabs-tab']")
	# calendar = tabs[1] # 2nd tab that is not active				
	# calendar.click()
	calendar_shown = teacher.find_element_by_xpath(".//div[@class='small-schedule relative']")		
	print(calendar_shown)
	if not calendar_shown:
		time.sleep(2)
	days = teacher.find_elements_by_xpath(".//div[@class='jsx-3909687884 small-schedule-section flex-1 flex flex-col']")	
	if len(days) == 0:
		time.sleep(1)
	print("days: ",len(days))	
	today = datetime.today()	
	for day in days:
		time_slots = day.find_elements_by_xpath(".//div[@class='jsx-3909687884 small-schedule-cell']")
		availability = []
		for time_slot in time_slots:			
			try:
				available_time = time_slot.find_element_by_xpath(".//div[@class='jsx-3909687884 small-schedule-cell-active h-full w-full b']")					
				availability.append(time_slots.index(time_slot) * 4)
			except:					
				pass		
		date = today + timedelta(days=days.index(day))
		schedule[days.index(day)] = {
			'availability' : availability,
			'date' : date.strftime("%d-%m-%Y")
		}

	# print(schedule)		
	return schedule


def teacher_level(teacher):
	try:
		level = teacher.find_element_by_xpath(".//span[@class=' font-light text-tiny leading-4 text-gray3 md:uppercase align-middle ']").text
	except:
		level = ''
	return level



def scrape_teachers(driver, all_teachers, csv_name, scrape_profile=True):
	rows = []
	count = 0
	for teacher in all_teachers:
		row = {}
		try:
			row['ranking'] = all_teachers.index(teacher) + 1
		except:
			print("could not get ranking!")
			row['ranking'] = None

		try:
			row['name'] = teacher.find_element_by_xpath(".//div[@class=' overflow-hidden mb-2 max-w-full']").text
		except:
			row['name'] = None		

		try:
			div_prices = teacher.find_element_by_xpath(".//div[@class='flex']")	
			div_trial_price = div_prices.find_elements_by_class_name('flex-1')[0]
			row['trial_price'] = div_trial_price.find_elements_by_tag_name('span')[1].text
		except:
			row['trial_price'] = None

		try:
			div_price = div_prices.find_elements_by_class_name('flex-1')[1]
			row['price'] = div_price.find_elements_by_tag_name('span')[1].text
		except:
			row['price'] = None

		try:	
			row['num_lessons'] = teacher.find_element_by_xpath(".//p[@class='font-light text-tiny']").text
		except:
			row['num_lessons'] = None

		try:		
			avatar_url = teacher.find_element_by_xpath(".//img").get_attribute('src')
			row['teacher_id'] = re.findall(r"\d{8}", avatar_url)[0]
		except:
			row['teacher_id'] = None

		row['level'] = teacher_level(teacher)
		schedule = scrape_time_table(driver, teacher)
		try:
			row['day0'] = schedule[0]['availability']
			row['day1'] = schedule[1]['availability'] 
			row['day2'] = schedule[2]['availability']
			row['day3'] = schedule[3]['availability']		
			row['day4'] = schedule[4]['availability']
			row['day5'] = schedule[5]['availability']
			row['day6'] = schedule[6]['availability']
		except:
			pass

		if scrape_profile == True:
			teacher_details = scrape_teacher(row['teacher_id'])
			for item in teacher_details:
				row[item] = teacher_details[item]


		rows.append(row)
		count += 1
		print(row['name']," scraped")
		write_to_csv(csv_name, row)		
		print(count," teachers/", len(all_teachers), " added!")

	return rows


def main():
	list_driver = get_page()
	click_cookie(list_driver)
	remove_sticky_filters(list_driver)
	unscroll_page(list_driver)
	open_calendars(list_driver)
	all_teachers = get_all_teachers(list_driver)
	teacher = all_teachers[3]
	csv_name = create_empty_csv()
	scrape_teachers(list_driver, all_teachers, csv_name)
	



if __name__ == "__main__":
    main()

# gets the page
# clicks on the button to show more until the button disappears
# for each teacher_bar:
#	scrape the data
#	get the ranking
# 	save in a csv file