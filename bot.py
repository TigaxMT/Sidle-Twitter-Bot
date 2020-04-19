from tweepy import OAuthHandler, API
from datetime import datetime
import pytz
import schedule
import time
import threading
import sys
import requests
import json
import os
import pandas as pd
import matplotlib.pyplot as plt

uni_emojis = {"skull": u"\U0001F480", "check": u"\U00002705", "up":"\U00002197\U0000FE0F", "pct": "\U0001F523"}

def trendingHashtags(api, countryCode):
	# verify if the country has a covid hashtag trending to use

	trends_av = api.trends_available()
	found_hashtag = False
	hashtag = "#COVID19"

	for trend in trends_av:
		if trend["countryCode"] == countryCode.upper():
			trends = api.trends_place(trend["woeid"])[0]["trends"]
			trend_names = [ trend["name"] for trend in trends if "#covid" in trend["name"].lower() ]
			
			if len(trend_names) > 0:
				found_hashtag = True
				break
	
	if found_hashtag:
		hashtag = trend_names[0]

	return hashtag

def stringToDate(date):
	# Convert full date string to a abreviaton of Date
	new_date = datetime.strptime(date, "%Y-%m-%d")

	return new_date.strftime("%b %d")

def finalTweet(api, timeline, msg, country):
	# Tweet our output message + image graph

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
	ax.plot("Date", "Confirmed Cases", data=total_confirmed, label="Confirmed Cases")
	ax.plot("Date", "Deaths", data=total_confirmed, label="Deaths")
	ax.plot("Date", "Active Cases", data=total_confirmed, label="Active Cases")


	ax.set_xlim(total_confirmed["Date"].loc[0], total_confirmed["Date"].loc[len(total_confirmed["Date"])-1])
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
	# Make the request
	url = "https://corona-api.com/countries/%s" % country
	r = requests.get(url=url)

	data = r.json()
		
	# Verify if exists the country
	if "message" in data.keys():
		pass

	else:
		# Check the trends of the country and verify
		# if it has a covid trending to use
		hashtag = trendingHashtags(api, country)

		timezone = pytz.timezone(tz)
		timeline = data["data"]["timeline"]
		data_date = data["data"]["updated_at"]
		data_today = data["data"]["today"]
		data = data["data"]["latest_data"]

		output = f'''
					\nToday({datetime.now(timezone).strftime("%I%p")}, {tz.split("/")[1]}):
{uni_emojis["skull"]} {data_today["deaths"]} deaths
{uni_emojis["check"]} {data_today["confirmed"]} confirmed cases

General:
{uni_emojis["skull"]} {data["deaths"]} deaths
{uni_emojis["check"]} {data["confirmed"]} confirmed cases
{uni_emojis["up"]} {data["recovered"]} recovered cases
{uni_emojis["pct"]} {round(data["calculated"]["death_rate"],2)}% of death ratio
{uni_emojis["pct"]} {round(data["calculated"]["recovery_rate"],2)} of recovery ratio
{uni_emojis["pct"]} {data["calculated"]["cases_per_million_population"]} cases per million

{hashtag}'''

		return output, timeline

def covid(api, country):
	# Create the output and call the finalTweet func
	# for the specified country

	if country == "pt":
		pt = u"\U0001F1F5\U0001F1F9"
		out, timeline = makeReq(api, "pt", "Europe/Lisbon")
		pt += out
		finalTweet(api, timeline, pt, "Portugal")

	elif country == "br":
		br = u"\U0001F1E7\U0001F1F7"
		out, timeline = makeReq(api, "br", "America/Sao_Paulo")
		br += out
		finalTweet(api, timeline, br, "Brazil")

	elif country == "us":
		us = u"\U0001F1FA\U0001F1F8"
		out, timeline = makeReq(api, "us", "America/New_York")
		us += out
		finalTweet(api, timeline, us, "USA")

	elif country == "it":
		it = u"\U0001F1EE\U0001F1F9"
		out, timeline = makeReq(api, "it", "Europe/Rome")
		it += out
		finalTweet(api, timeline, it, "Italy")

	elif country == "es":
		es = u"\U0001F1EA\U0001F1F8"
		out, timeline = makeReq(api, "es", "Europe/Madrid")
		es += out
		finalTweet(api, timeline, es, "Spain")

	elif country == "fr":
		fr = u"\U0001F1EB\U0001F1F7"
		out, timeline = makeReq(api, "fr", "Europe/Paris")
		fr += out
		finalTweet(api, timeline, fr, "France")

	elif country == "de":
		de = u"\U0001F1E9\U0001F1EA"
		out, timeline = makeReq(api, "de", "Europe/Berlin")
		de += out
		finalTweet(api, timeline, de, "Germany")

	return


def threaded_job(job, api, country):
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

	# Schedule to run everyday, in Europe/Lisbon timezone 
	schedule.every().day.at("20:45").do(threaded_job, covid, api, "fr")#fr, Paris
	schedule.every().day.at("20:30").do(threaded_job, covid, api, "de")#de, Berlin
	schedule.every().day.at("20:15").do(threaded_job, covid, api, "it")#it, Rome
	schedule.every().day.at("20:00").do(threaded_job, covid, api, "pt")#pt, Lisbon
	schedule.every().day.at("21:00").do(threaded_job, covid, api, "es")#es, Madrid
	schedule.every().day.at("21:15").do(threaded_job, covid, api, "br")#br, Brasilia
	schedule.every().day.at("22:00").do(threaded_job, covid, api, "us")#usa, New York

	while True:
		schedule.run_pending()

		# For performance measures
		time.sleep(60)

if __name__ == '__main__':
    main()
