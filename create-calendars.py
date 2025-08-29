import json
import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime, timedelta

from ics import Calendar, Event
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["div"]
div_db = db["pages"]


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
				"$gte": now - timedelta(days=30),
				"$lte": now + timedelta(days=90)
			},
			"meta.parent.title": {
				"$in": organizers
			}
		}
	else:
		query = {
			"start": {
				"$gte": now - timedelta(days=30),
				"$lte": now + timedelta(days=90)
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
					e.duration = {"minutes": 2*60 + 58}
					e.description += "\n\n(Error: The event had an invalid end date)"
			else:
				no_end_date_count += 1
				e.duration = {"minutes": 2*60 + 57}
				e.description += "\n\n(Error: The event had no end date)"

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
	with ThreadPoolExecutor(max_workers=32) as executor:
		futures = [executor.submit(create_calendar, name, organizers) for name, organizers in organizer_combinations.items()]
		for future in futures:
			future.result()
	print("Calendars created.")
		
def main():
	check_organizers()
	create_calendars()

if __name__ == "__main__":
	main()
