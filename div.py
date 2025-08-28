import json
import os
from datetime import datetime, timedelta

import requests
from dateutil.parser import parse
from ics import Calendar, Event
from pymongo import MongoClient
from pymongo.errors import BulkWriteError


client = MongoClient("mongodb://localhost:27017/")
db = client["div"]
div_db = db["pages"]


def convert_dates(obj):
	if isinstance(obj, dict):
		return {k: convert_dates(v) for k, v in obj.items()}
	elif isinstance(obj, list):
		return [convert_dates(i) for i in obj]
	elif isinstance(obj, str):
		try:
			# Try parsing string as datetime, if it fails, return string as is
			dt = parse(obj)
			# Confirm parsed result is datetime and the string reasonably matches a date format
			if isinstance(dt, datetime):
				return dt
		except (ValueError, OverflowError):
			pass
		return obj
	else:
		return obj


def upsert_page(page):
	page = convert_dates(page)
	page["_id"] = page["id"]
	page["last_fetched"] = datetime.now()
	try:
		result = div_db.replace_one({"_id": page["_id"]}, page, upsert=True)
		if result.matched_count > 0:
			print(f"Updated page with id {page['_id']}")
		else:
			print(f"Inserted new page with id {page['_id']}")
	except BulkWriteError as bwe:
		print(f"Bulk write error: {bwe.details}")


def get_page(id: int):
	response = requests.request("GET", f"https://diversity-muenchen.de/api/v2/pages/{id}/")
	if response.status_code == 404:
		print("Page not found")
		return None
	elif response.status_code != 200:
		print(f"Error: {response.status_code}")
		exit()
	upsert_page(response.json())
	return response.json()["id"]


def get_pages():
	highest_id = div_db.find().sort("id", -1).limit(1)
	try:
		id = highest_id[0]["id"]+1
	except IndexError:
		id = 0
	print(f"Starting from id {id}")
	fails = 0
	while True:
		if not get_page(id) == id:
			fails += 1
			if fails > 10:
				print("No more pages found, exiting.")
				break
		else:
			fails = 0
		id += 1


def update_pages():
	now = datetime.now()
	query = {
		"$or": [
      		{"meta.type": "home.EventOrganizer"},

			{ "last_fetched": { "$lt": now - timedelta(days=7) } },
			{
				"$and": [
					{ "last_fetched": { "$lt": now - timedelta(hours=1) } },
					{ "start": { 
						"$gte": now - timedelta(days=1),
						"$lte": now + timedelta(days=14)
					} }
				]
			},
			{
				"$and": [
					{ "last_fetched": { "$lt": now - timedelta(days=1) } },
					{ "start": { "$lte": now + timedelta(days=90) } }
				]
			}
		]
	}
	pages = div_db.find(query)
	for page in pages:
		get_page(page["id"])


def get_organizers():
	query = {
		"meta.type": "home.EventOrganizer"
	}
	return div_db.find(query)


def get_organizers_json():
	with open("organizers.json", "r", encoding="utf-8") as f:
		return json.load(f)


def check_organizers():
	organizers_file = get_organizers_json()
	organizers = get_organizers()
	for organizer in organizers:
		if not any(o == organizer["title"] for o in organizers_file):
			print(f"Organizer {organizer['id']} - {organizer.get('title', 'No title')} is missing in organizers.json")


# returns every combination possible from the organizers.json as an array
# the array should use the values of the combination out of the organizers.json it is using as keys by joining them without spaces
# the values of these keys should be a list of the keys used to create the combination
# example:
# input:{"JuLes": "jl","Wilma": "wi"}
# should return for example:
# {"jlwi": ["JuLes", "Wilma"], "jl": ["JuLes"], "wi": ["Wilma"]}
# the combination "wijl": ["Wilma", "JuLes"] would not be valid as the order of the keys does matter
def generate_organizer_combinations():
    organizers = get_organizers_json()
    keys = list(organizers.keys())
    n = len(keys)
    combinations = {}
    # Use bitmask to select keys in order
    for i in range(1, 2**n):
        subsequence_keys = []
        subsequence_values = []
        for j in range(n):
            if (i & (1 << j)) > 0:
                subsequence_keys.append(keys[j])
                subsequence_values.append(organizers[keys[j]])
        combination_key = ''.join(subsequence_values)
        combinations[combination_key] = subsequence_keys
    return combinations


def create_calendar(name=None, organizers=None):
	cal = Calendar()

	now = datetime.now()
	if organizers:
		query = {
			"start": {
				"$gte": now - timedelta(years=1),
				"$lte": now + timedelta(years=1)
			},
			"meta.parent.title": {
				"$in": organizers
			}
		}
	else:
		query = {
			"start": {
				"$gte": now - timedelta(years=1),
				"$lte": now + timedelta(years=1)
			}
		}
	events = div_db.find(query)

	no_end_date_count = 0
	for event in events:
		e = Event()
		e.name = event.get("title", "No title")
		e.description = event.get("description_en") or event.get("description_de") or ""
		
		start_date = event.get("start", None)
		if start_date:
			e.begin = start_date

			end_date = event.get("end", None)
			if end_date:
				try:
					e.end = end_date
				except ValueError:
					print("Invalid end date for event id:", event["id"])
					e.duration = {"hours": 2}
			else:
				no_end_date_count += 1
				e.duration = {"hours": 2}

			if "location" in event and event["location"] is not None:
				loc = event["location"]
				loc_str = ", ".join(
					filter(
						None,
						[
							loc.get("name"),
							loc.get("address"),
							loc.get("plz"),
							loc.get("city"),
						],
					)
				)
				e.location = loc_str
			cal.events.add(e)
	if not organizers:
		print(f"{no_end_date_count} of {len(cal.events)} events had no end date")

	if name:
		if not os.path.exists("calendars"):
			os.makedirs("calendars")
		filename = f"calendars/{name}.ics"
	else:
		filename = "all.ics"
	with open(filename, "w", encoding="utf-8") as f:
		f.writelines(cal)


def create_calendars():
	create_calendar()
	organizer_combinations = generate_organizer_combinations()
	print(f"Creating {len(organizer_combinations)} calendars for organizer combinations...")
	i = 0
	for name, organizers in organizer_combinations.items():
		if name.startswith("jl"):
			i += 1
		create_calendar(name, organizers)
	
	print(f"Created {i} calendars for combinations starting with 'jl'")
	print("Calendars created.")
		
def main():
	get_pages()
	update_pages()
	check_organizers()
	create_calendars()

if __name__ == "__main__":
	main()
