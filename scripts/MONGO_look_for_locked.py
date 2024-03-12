#!/usr/bin/env python3

#------------------------
#
# Looks in the local MongoDB to identify which session IDs are locked
# The locked session IDs are also stored in 'locked_document_ids'
#
#------------------------


from pymongo import MongoClient

#Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["micromix"]
collection = db["visualizations"]

# Search for documents where 'locked' is True
documents_with_locked_true = collection.find({"locked": True})

# Count the documents where 'locked' is True
count_locked_docs_true = collection.count_documents({"locked": True})

#Store the locked IDs 
# Initialize a list to store the document IDs
locked_document_ids = []

# Iterate over the cursor and add each document's '_id' to the list
for doc in documents_with_locked_true:
    locked_document_ids.append(doc['_id'])


# Loop through all locked records and print to screen
if count_locked_docs_true > 0:
    print(f"Found {count_locked_docs_true} documents with 'locked' set to True:")
    for doc in documents_with_locked_true:
        print(f"Document ID: {doc['_id']}, Locked: {doc.get('locked')}")
else:
    print("No documents found with 'locked' set to True in the 'visualizations' collection.")

