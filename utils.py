""" This file only contains functions that preprocess something"""

from datetime import datetime

# Unicode Emojis
uni_emojis = {"skull": u"\U0001F480", "check": u"\U00002705", "up":"\U00002197\U0000FE0F", "pct": "\U0001F523"}


def trendingHashtags(api, countryCode):
	""" Verify if the country has a covid hashtag trending to use """

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

def genTextOutput(api, data_dict, country):
	""" Get a data dict with a certain pattern
		to fill on the formatted output
	"""



	

	""" Hashtag not available for now
	
	# Check the trends of the country and verify
	# if it has a covid trending to use
	hashtag = trendingHashtags(api, country)

	"""

	output = f'''
General:
{uni_emojis["skull"]} {data_dict["general"]["deaths"]} deaths
{uni_emojis["check"]} {data_dict["general"]["confirmed"]} confirmed cases
{uni_emojis["up"]} {data_dict["general"]["recovered"]} recovered cases'''

	return output

def stringToDate(date, fmt="%Y-%m-%d"):
	""" Convert full date string to a abreviaton of Date """
	new_date = datetime.strptime(date, fmt)

	return new_date.date()

def convertDate(date, fmt):
	""" Convert Date format for the format used on the finalTweet"""
	new_date = datetime.strptime(date, fmt)
	new_date = new_date.strftime("%Y-%m-%d")

	return new_date