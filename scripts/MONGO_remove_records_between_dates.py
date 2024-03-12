#!/usr/bin/env python3

#------------------------
#
# Script counts and removes records in the DB from a manual date range
#
#------------------------

from pymongo import MongoClient
from bson.objectid import ObjectId  # Import ObjectId
from datetime import datetime, timedelta


#Connect to Db
print("---Connecting to DB (1/5)---")
client = MongoClient("mongodb://localhost:27017/")
db = client["micromix"]
collection = db["visualizations"]
print("---Connected to DB (2/5)---")


# Define the start and end of your date range
#Note
#Dates will need to be manually changed
#If running this script with Cron, date ranges could be automated
start = datetime(2023, 6, 1) #(YYYY-MM-DD) 
end = datetime(2023, 11, 1) 


# List of _id values to exclude, wrapped in ObjectId()
#Note:
#Here, you can add in entries that you want to exclude from being removed.
#This is useful when people want a link for a publication etc
#There is another script in this folder that identifies if a document has a locked session,
#this script prints and stores the locked session IDs, which could be implemented into this script if required
exclude_ids = [
    ObjectId("63fe15d43a205e6170d48dea"),  # Example _id values
    ObjectId("6527fc4c8ee09e91bf3178ad"),
    # Add more ObjectIds as needed
]

# Count records - excluding the IDs that you want to keep (above)
# exclude the specified _id values using $nin
print("---Counting records (3/5)---")
count = collection.count_documents({
    "timestamp": {"$gte": start, "$lt": end},
    "_id": {"$nin": exclude_ids}
})
print(f"{count} documents found with timestamp between {start} and {end}, excluding specified records")


# Prompt user before deleting records
user_input = input("\033[31mDo you want to delete the records? (yes/no): \033[0m").strip().lower()
if user_input == 'yes':
    print("---Deleting records (4/5)---")
    result = collection.delete_many({
        "timestamp": {"$gte": start, "$lt": end},
        "_id": {"$nin": exclude_ids}
    })
    print(f"Deleted {result.deleted_count} documents, excluding specified records")

    # Re-count to verify deletion, excluding the specified _id values
    print("---Counting records again (5/5)---")
    count = collection.count_documents({
        "timestamp": {"$gte": start, "$lt": end},
        "_id": {"$nin": exclude_ids}
    })
    print(f"{count} documents found with timestamp between {start} and {end}, excluding specified records")
elif user_input == 'no':
    print("Exiting script without deleting records.")
else:
    print("Invalid input. Exiting script.")
