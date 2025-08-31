import json
import os
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

def create_calendars_dir():
	if not os.path.exists("calendars"):
		os.makedirs("calendars")


def get_organizers_from_json():
    organizers = []
    for short_name, organizer in get_organizers_json().items():
        organizers.append((organizer, short_name))
    return organizers

def create_calendar(organizer=None):
	cal = Calendar()

	now = datetime.now()
	query = {
		"start": {
			"$gte": now - timedelta(days=30),
			"$lte": now + timedelta(days=90)
		}
	}
	if organizer:
		if organizer[1] == "no":
			query = {
				"start": query["start"],
				"$or": [
					{"meta.parent.title": {"$exists": False}},
					{"meta.parent.title": None},
					{"meta.parent.title": ""},
					{"meta.parent.title": {"$nin": [o[0] for o in get_organizers_from_json()]}}
				]
			}
		else:
			query = {
				"start": query["start"],
				"meta.parent.title": organizer[1]
			}		
	events = div_db.find(query)

	no_end_date_count = 0
	for event in events:
		e = Event()
		e.name = event.get("title", "No title")
		e.description = event.get("description_de") or event.get("description_en") or ""
		
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
				e.location = e.location.replace("diversity Jugendzentrum", "diversity München Jugendzentrum")
			cal.events.add(e)
	if not organizer:
		print(f"{no_end_date_count} of {len(cal.events)} events had no end date")

	if organizer:
		create_calendars_dir()
		filename = f"calendars/{organizer[0]}.ics"
	else:
		filename = "all.ics"
	with open(filename, "w", encoding="utf-8") as f:
		f.writelines(cal)

def create_calendars():
	create_calendar()
	create_calendars_dir()
	organizers = get_organizers_from_json()
	print(f"Creating {len(organizers)} filtered calendars...")
	for organizer in organizers:
		create_calendar(organizer)
	print("Calendars created.")
		
def main():
	check_organizers()
	create_calendars()

if __name__ == "__main__":
	main()
