from utils import stringToDate, trendingHashtags, genTextOutput
from countries import countries_dict, pt_req
from tweepy import OAuthHandler, API
import datetime
import schedule
import time
import threading
import sys
import requests
import json
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# Read the CSV where the countries data is save
df = pd.read_csv("countries.csv")

def finalTweet(api, timeline, msg, country):
	
	total_confirmed = []

	for i in range(len(timeline)):
		date = timeline[i]["date"]
		confirmed = timeline[i]["confirmed"]
		deaths = timeline[i]["deaths"]
		active = timeline[i]["active"]
		total_confirmed.append([date,confirmed, deaths, active])


	total_confirmed.reverse()
	total_confirmed = pd.DataFrame(total_confirmed)
	total_confirmed.columns = ["Date", "Confirmed Cases", "Deaths", "Active Cases"]
	total_confirmed["Date"] = total_confirmed["Date"].apply(stringToDate)


	# Graphing
	fig, ax = plt.subplots(figsize=(16,10))
	fig.gca().xaxis.set_major_formatter(mdates.DateFormatter("%B"))
	fig.gca().xaxis.set_major_locator(mdates.MonthLocator())
	ax.plot("Date", "Confirmed Cases", data=total_confirmed, label="Confirmed Cases")
	ax.plot("Date", "Deaths", data=total_confirmed, label="Deaths")
	ax.plot("Date", "Active Cases", data=total_confirmed, label="Active Cases")

	ax.grid(True)
	
	fig.autofmt_xdate()
	plt.xlabel("Date")
	plt.ylabel("Number of People")
	plt.title("Status of COVID-19 on " + country)
	plt.legend()

	plt.savefig(country.lower()+".png", bbox_inches='tight', dpi=300)
	api.update_with_media(country.lower()+".png", status=msg)
	os.remove(country.lower()+".png")


def makeReq(api, country, tz):
	""" Make the request to the API"""

	# First verify if we have a custom API for the country
	# we do that looping through the list and verify if any
	# function name has the country code
	if country in [key for key, value in countries_dict.items()]:

		timeline, today, general = countries_dict[country]()

		data_dict = {
			"data_today": today,
			"general": general
		}

		output = genTextOutput(api, data_dict, country)

		return output, timeline

	else:
		# Else just use the common API
		url = "https://corona-api.com/countries/%s" % country
		r = requests.get(url=url)
		data = r.json()
			
		# Verify if exists the country
		if "message" in data.keys():
			return None, None

		else:
			timeline = data["data"]["timeline"]
			#data_date = data["data"]["updated_at"]
			data_today = data["data"]["today"]
			data = data["data"]["latest_data"]

			data_dict = {
				"data_today": data_today,
				"general": data
			}

			output = genTextOutput(api, data_dict, country)

			return output, timeline

def covid(api, country):
	""" Call the apis and create the final tweet"""

	# Took the sample where the country code is
	country_df = df[ df["Country_Code"]==country ]


	# Create the country flag emoji
	ctr = country_df["Unicode_Emoji"].iloc[0]
	ctr = ctr.encode().decode("unicode-escape")


	# Get all the data from the API and create the tweet text
	out, timeline = makeReq(api, country, country_df["Timezone"].iloc[0])
	ctr += out

	# Add the graph image and tweet all the stuff
	finalTweet(api, timeline, ctr, country_df["Country_Name"].iloc[0])

	return


def threaded_job(job, api, country):
	""" Thread the covid() function"""

	job_th = threading.Thread(target=job, args=(api, country))
	job_th.start()

def main():

	try:
		auth = OAuthHandler(os.environ["CONSUMER_KEY"], os.environ["CONSUMER_SECRET"])
		auth.secure = True
		auth.set_access_token(os.environ["ACCESS_TOKEN"], os.environ["ACCESS_TOKEN_SECRET"])
		api = API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

	except BaseException as e:
		print("Error in main()", e)
		sys.exit(1)


	day = datetime.datetime.now().day
	
	# Schedule only on even days
	if day % 2 == 0:
		schedule.every().day.at("12:00").do(threaded_job, covid, api, "jp")#jp, Tokyo +8
		schedule.every().day.at("18:00").do(threaded_job, covid, api, "ru")#ru, Moscow +2
		schedule.every().day.at("19:00").do(threaded_job, covid, api, "es")#es, Madrid +1
		schedule.every().day.at("19:15").do(threaded_job, covid, api, "de")#de, Berlin +1
		schedule.every().day.at("20:00").do(threaded_job, covid, api, "pt")#pt, Lisbon +0
		schedule.every().day.at("01:00").do(threaded_job, covid, api, "us")#us, New York -5
		schedule.every().day.at("02:00").do(threaded_job, covid, api, "co")#co, Bogota -6

	# Schedule only on 31st days 
	elif day == 31:
		schedule.every().day.at("11:00").do(threaded_job, covid, api, "au")#au, Sydney +9
		schedule.every().day.at("18:00").do(threaded_job, covid, api, "ru")#ru, Moscow +2
		schedule.every().day.at("19:00").do(threaded_job, covid, api, "es")#es, Madrid +1
		schedule.every().day.at("20:00").do(threaded_job, covid, api, "pt")#pt, Lisbon +0
		schedule.every().day.at("20:15").do(threaded_job, covid, api, "gb")#gb, UK +0
		schedule.every().day.at("00:10").do(threaded_job, covid, api, "br")#br, Brasilia -4
		schedule.every().day.at("02:00").do(threaded_job, covid, api, "co")#co, Bogota -6

	# Schedule only on odd days
	else:
		schedule.every().day.at("11:00").do(threaded_job, covid, api, "au")#au, Sydney +9
		schedule.every().day.at("13:00").do(threaded_job, covid, api, "cn")#cn, Hong Kong +7
		schedule.every().day.at("19:00").do(threaded_job, covid, api, "fr")#fr, Paris +1
		schedule.every().day.at("19:15").do(threaded_job, covid, api, "it")#it, Rome +1
		schedule.every().day.at("20:00").do(threaded_job, covid, api, "gb")#gb, UK +0
		schedule.every().day.at("00:10").do(threaded_job, covid, api, "br")#br, Brasilia -4
		schedule.every().day.at("01:00").do(threaded_job, covid, api, "ca")#ca, Ottawa -5

	while True:
		schedule.run_pending()

		# Performance Measure
		time.sleep(60)

if __name__ == '__main__':
    main()
