#--------------------------------
#
# Heatmap designed by Titus Ebbecke 2021-2022
# Modifications by Regan Hayward 2023+
#
#--------------------------------

import json
from pymongo import MongoClient
from flask import Flask, request, Response, jsonify, send_from_directory
import os
from flask_cors import CORS
from bson.json_util import loads, dumps, ObjectId
import pandas as pd
from io import BytesIO



# MongoDB Connection setup
# If running not in a container environment, you can use the following line to connect to a local MongoDB install
#client = MongoClient() #this is for testing on a local machine, when not inside a container
#When using containers, you need to modify 'sudo vim /etc/mongodb.conf' and add in an additional IP under bind_ip
# '172.17.0.1' is often the Docker default bridge network gateway, allowing containers to connect to the host.
client = MongoClient('172.17.0.1', 27017)
# Select the 'micromix' database within MongoDB for storing and retrieving application data.
db = client.micromix
# Define collections for storing visualizations and plugins information.
visualizations = db.visualizations


# #MongoDB needs to be installed
# Otherwise, use #client = MongoClient(os.environ.get("testend")) to point to the MongoDB server on the cloud

#client = MongoClient(os.environ.get("testend"))
#client = MongoClient() # For offline testing.
#db = client.micromix
#visualizations = db.visualizations

DEBUG = True
app = Flask(__name__)
CORS(app)

#Testing
app.config.from_object(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['FLASK_DEBUG']=1
app.config['DEBUG'] = True

#Testing
@app.route('/status', methods=['GET'])
def status():
  return 'alive'



@app.route('/config', methods=['GET', 'POST'])
def respond_config():
  #Print the ID to terminal
  print("DB Config=",request.form['url'])
  #Checking of a URL with DB id has been passed
  if request.form['url'] != 'undefined':
    #id identified and convert to ObjectId object
    print("id found in DB")
    db_entry_id = ObjectId(loads(request.form['url']))
    #Find the object id in the visualisations database
    db_entry = db.visualizations.find_one({"_id": db_entry_id})
    #Check if the df is filtered or transformed
    try:
      #Converts entry from .json into pandas parquet
      data = pd.read_parquet(BytesIO(db_entry['filtered_dataframe'])).to_json(orient='records')
    except:
      #The mockup db_entry stores the empty transformed_dataframe as a list, so don't convert that one.
      #Convert transformed into pandas parquet
      if type(db_entry['transformed_dataframe']) == bytes: 
        data = pd.read_parquet(BytesIO(db_entry['transformed_dataframe'])).to_json(orient='records')
      else:
        data = db_entry['transformed_dataframe']
  
  print("Data successfully passed to heatmap!")
  return Response(data, mimetype="application/json")
  

#---
#Save user defined heatmap settings
#---
@app.route('/save-settings', methods=['POST'])
def save_settings():
  #print("Save request received")

  #capture the sent data
  try:
    data = request.get_json()
    #Extract the data and db_id
    db_entry_id = data['dbEntryId']
    settings_data = data['settings']
    
    #Save location and filename
    folder_name = 'saved_sessions'
    filename = f"{folder_name}/{db_entry_id}.json"

    # Write to file
    with open(filename, 'w') as json_file:
      json.dump(settings_data, json_file, indent=4)
    return jsonify({"message": "Settings saved successfully"}), 200
  except Exception as e:
    print("Error saving settings:", e)
    return jsonify({"error": "Failed to save settings", "details": str(e)}), 500
  


#---
#Load user defined heatmap settings
#---
@app.route('/get-user-settings/<db_entry_id>', methods=['GET'])
def get_user_settings(db_entry_id):
    #print("--in get-user-settings--")
    #print("db_entry_id: ", db_entry_id)

    #Prepare file information
    directory = 'saved_sessions' #folder where sessions are saved
    filename = f"{db_entry_id}.json" #file name thats saved
    file_path = os.path.join(directory, filename)

    #Check if the file exists - if not, return the error to the frontend
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found", "details": "No settings found for the provided ID"}), 404

    #Try and load file
    try:
        # Load and return file
        return send_from_directory(directory, filename)
    except Exception as e:
        # Error message if not found
        response = {"error": "Failed to load settings", "details": str(e)}
        app.logger.error(response)  # Log the error details
        return jsonify(response), 500


client.close()
