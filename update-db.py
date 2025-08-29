from datetime import datetime, timedelta

import requests
from dateutil.parser import parse
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
		
def main():
	get_pages()
	update_pages()

if __name__ == "__main__":
	main()
