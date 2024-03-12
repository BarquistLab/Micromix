#!/usr/bin/env python3

#------------------------
#
# Script to count documents within a time range
#
#------------------------

from pymongo import MongoClient
from bson.son import SON
from bson.objectid import ObjectId
from datetime import datetime, timedelta

#Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["test"]
collection = db["visualizations"]

#Note
#Dates will need to be manually changed
start = datetime(2023, 10, 1) #YYYYMMDD
end = datetime(2024, 3, 1)

#Count the total number of DB entries
count = collection.count_documents({"timestamp": {"$gte": start, "$lt": end}})
print(f"{count} documents found with timestamp between {start} and {end}")
