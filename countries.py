""" 
Here are the specific requests for each country.
If a country doesn't your own API, the script uses the common API.
"""
import requests
import pandas as pd
from utils import convertDate

def pt_req():
	""" Function requests to an API that have direct connection with the DGS data"""

	url = "https://covid19-api.vost.pt/Requests/get_full_dataset"
	r = requests.get(url=url)
	data = r.json()

	# Select only the kind of data that we want
	date = data["data"]
	confirmed = data["confirmados"]
	new_confirmed = data["confirmados_novos"]
	recover = data["recuperados"]
	deaths = data["obitos"]

	# Convert it from dict to list
	date = [value for _, value in date.items() ]
	confirmed = [value for _, value in confirmed.items() ]
	new_confirmed = [value for _, value in new_confirmed.items() ]
	recover = [value for _, value in recover.items() ]
	deaths = [value for _, value in deaths.items() ]

	# Create the active list (list with active cases)
	# Using the confirmed - recovered cases
	active = [conf-rec for conf, rec in zip(confirmed, recover)]


	finalList = []

	# Now we need to create a list like "timeline" on the finalTweet() function
	for i in range(len(date)):
		finalList.append({
			"date": convertDate(date[i], "%d-%m-%Y"),
			"confirmed": confirmed[i],
			"deaths": deaths[i],
			"active": active[i]
			})


	# Created just for the ouput generator
	today = {
		"deaths": deaths[-1] - deaths[-2],
		"confirmed": new_confirmed[-1]
	}

	general = {
		"deaths": deaths[-1],
		"confirmed": confirmed[-1],
		"recovered": recover[-1]
	}

	return finalList, today, general



# Global dict with the country function names
countries_dict = {"pt": pt_req}