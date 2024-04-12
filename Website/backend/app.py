#--------------------------------
#
# Designed by Titus Ebbecke 2021-2022
# Modifications by Regan Hayward 2023+
#
#--------------------------------

# This Flask application serves as the backend for a data visualization platform that connects to a Vue.js frontend. 
# It supports operations like file upload, data export, and dynamic plugin management for data visualization.
# MongoDB is used for storing visualization configurations, plugins, and processed data.


# To-Do: Configure CORS to only allow specific requests.

import os
from flask import Flask, flash, request, redirect, url_for, jsonify, send_from_directory, Response, send_file
from werkzeug.utils import secure_filename
from flask_cors import CORS
import uuid
import json
from flask import json
import process_file # Custom module for processing uploaded files
import visualize # Custom module for handling visualization logic
from pymongo import MongoClient
from bson.json_util import loads, dumps, ObjectId
from io import BytesIO
import pandas as pd


# Define allowed file extensions for matrix data and icon uploads to ensure security and data integrity.
ALLOWED_EXTENSIONS_MATRIX = {'txt', 'xlsx', 'csv', 'tsv'}
ALLOWED_EXTENSIONS_ICON = {'svg', 'png', 'jpg', 'jpeg', 'gif'}

# Pre-configured plugins with their MongoDB ObjectIds. These plugins are available by default.
PRE_CONFIGURED_PLUGINS =  [ObjectId('5f984ac1b478a2c8653ed827'), ObjectId('5f284a560831e4a42a30d698'), ObjectId('5f284bc60831e4a42a30d699'), ObjectId('5fc156db0ccdd1e1e454f116')]

# Define a template for matrix configuration, used in data visualization layouts.
MATRIX = [
    {
        "id": uuid.uuid4().hex,  # Generate a unique ID for each matrix configuration
        "width": 5,
        "height": 5,
        "x": 2,
        "y": 2,
        "isActive": False  # Determines if the matrix is currently active in the visualization
    }
]

# Mockup for a database entry, showcasing the structure used to store visualization configurations in MongoDB.
DB_ENTRY_MOCKUP = {
    'active_matrices': [],  # Active matrix configurations
    'transformed_dataframe': [],  # Processed data ready for visualization
    'preview_matrices': MATRIX,  # Matrix configurations for preview purposes
    'vis_links': [],  # Links to generated visualizations
    'plugins_id': PRE_CONFIGURED_PLUGINS,  # IDs of available plugins
    'active_plugin_id': '',  # Currently active plugin
    'active_organism_id': 'bacteroides-thetaiotaomicron-e2ad6b25-40cb-4594-8685-f4fcb3ceb0e7'  # Example organism ID
}

# Define error messages to standardize responses for various error conditions.
ERROR_MESSAGES = {
    'export_error': {
        'expected': {
            'type': 'Export Error',
            'message': 'The dataframe could not be converted. Please try to change the download type or check your source data.'
        },
        'unexpected': {
            'type': 'Unexpected Export Error',
            'message': 'An unexpected export error has occured. The file cannot be downloaded.'
        }
    },
    'query_error': {
        'expected': {
            'type': 'Filter Error',
            'message': 'The dataframe could not be filtered. Please verify your queries.'
        },
        'unexpected': {
            'type': 'Unexpected Filter Error',
            'message': 'An unexpected filter error has occured.'
        }
    },
    'locking_error': {
        'expected': {
            'type': 'Locking Error',
            'message': "The config could not be locked, because it's corrupted or offline. Please secure your data by downloading it."
        },
        'unexpected': {
            'type': 'Unexpected Locking Error',
            'message': 'An unexpected locking error has occured. The config could not saved. Please secure your data by downloading it.'
        }
    },
    'visualization_error': {
        'expected': {
            'type': 'Visualization Error',
            'message': "The visualization couldn't be initialized because it is either offline or your dataframe is unsupported. Please try a different table."
        },
        'unexpected': {
            'type': 'Unexpected Visualization Error',
            'message': 'An unexpected visualization error has occured.'
        }
    },
    'config_error': {
        'expected': {
            'type': 'Config Error',
            'message': "The config could not be loaded, because it's corrupted or offline. Please try to go back to the homepage."
        },
        'unexpected': {
            'type': 'Unexpected Config Error',
            'message': 'An unexpected error has occured while loading the config.'
        }
    },
    'upload_error': {
        'expected': {
            'type': 'Upload Error',
            'message': "The dataframe could not be uploaded or merged. Try to adjust your data or change the slot."
        },
        'unexpected': {
            'type': 'Unexpected Upload Error',
            'message': 'An unexpected error has occured while uploading the data. Did you select the target matrix in the preview?'
        }
    },
}


#---
# Flask application configuration
#---

# configuration
DEBUG = True

# # instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)

# Configure Cross-Origin Resource Sharing (CORS) to allow all origins. This should be restricted in production.
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # Limit file size to prevent denial-of-service attacks
app.config['FLASK_DEBUG']=1 
app.config['DEBUG'] = True
cors = CORS(app, resources={r"/*":{"origins": "*"}})


UPLOAD_FOLDER = '/static'  # NOTE: Change this to /uploads in production for better organization
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Entry point for the Flask application.
# Ensure the Flask server runs in debug mode on 0.0.0.0, making it accessible on all network interfaces.
# The server listens on port specified by the PORT environment variable, defaulting to 8080 if not set.
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

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
plugins = db.plugins



#---
#FUNCTION: allowed_file
#---
# Function to check if the uploaded file's extension is within the allowed set.
# This helps prevent the upload of potentially malicious files.
def allowed_file(filename, extension_whitelist):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in extension_whitelist




#=============
# ROUTE 'export/'
#=============

# Route for exporting data in various formats (Excel or CSV) based on user's choice.
# Fetches the specific visualization data from MongoDB, prepares it, and sends the file to the user.
@app.route('/export', methods=['POST'])

#---
# FUNCTION: export_df
# PURPOSE: This function is designed to export data from a database as either a CSV or Excel file based on user input.
#          It handles both "filtered" and "unfiltered" datasets, retrieving them from a database, and prepares them
#          according to the specified format (CSV or Excel) as chosen by the user. The function dynamically handles
#          errors related to missing data or incorrect format specifications. 
#---

def export_df():
    try:
        # Extract form data containing export options and the unique visualization identifier.
        #  Parse the export form and URL from the request form data to get the user's export preferences and the ID of the data to export.
        export_form = json.loads(request.form['export_form'])
        url = json.loads(request.form['url'])
        db_entry = db.visualizations.find_one({"_id": ObjectId(url)}, {'_id': False})

        # Prepare dictionaries to hold filtered and unfiltered data for export.
        # Find the visualization entry in the database using its unique ID but exclude the entry's own ID from the results.
        
        # Initialize a dictionary to store the dataframes to be exported, both filtered and unfiltered.
        dataframe_dict = {}
        
        
        # Attempt to load the filtered dataframe if available and add it to the dataframe dictionary.
        try:
            df_filtered = pd.read_parquet(BytesIO(db_entry['filtered_dataframe']))
            dataframe_dict["filtered"] = {"df": df_filtered, "name": "Filtered Data"}
        except (KeyError, TypeError):
            # If filtered data is not available or there's an error, skip without failing.
            pass  # Skip if no filtered data is available.

        # Always attempt to add the unfiltered data to the export.
        dataframe_dict["unfiltered"] = {}
        try:
            # Attempt to load the transformed dataframe as the unfiltered data.
            dataframe_dict["unfiltered"]["df"] = pd.read_parquet(BytesIO(db_entry['transformed_dataframe']))
        except KeyError:
            # Fallback to the original dataframe if the transformed version isn't available.
            print("NOTE: 'transformed_dataframe' not found, using 'dataframe' instead.")
            dataframe_dict["unfiltered"]["df"] = pd.read_parquet(BytesIO(db_entry['dataframe']))
        
        # Assign a name to the unfiltered data for clarity in the export.
        dataframe_dict["unfiltered"]["name"] = "Source Data"

        # Determine the file type requested for the export and call the respective function to prepare the file.
        if export_form["file_type"] == 'excel':
            res = df_to_excel(dataframe_dict)
        elif export_form["file_type"] == 'csv':
            res = df_to_csv(dataframe_dict, export_form['csv_seperator'])

        # Return the prepared file for download.
        return res
    except Exception as e:
        # In case of any error during the process, log it and return a standardized error response.
        print(str(e))
        return respond_error(ERROR_MESSAGES['export_error']['expected']['type'], str(e))
    


#---
# FUNCTION: df_to_excel
# PURPOSE: Helper function to convert dataframes into an Excel file and return it as a Flask response.
#---

def df_to_excel(dataframe_dict):
    from io import BytesIO
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    # Load the filtered, and unfiltered dataframe as excel sheets.
    for dataframe_parent in dataframe_dict:
        dataframe_dict[dataframe_parent]["df"].to_excel(writer, sheet_name=dataframe_dict[dataframe_parent]["name"], index=False)
    writer.close()
    output.seek(0)
    return send_file(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, attachment_filename="dataframes.xlsx")
    # This is the only instance where the send_file module from flask is used. You can try an approach with Response as below, however this exact implementation has caused the excel file to be corrupted.
    # return Response(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-disposition": "attachment; filename=filename.xlsx"})


#---
# FUNCTION: df_to_csv
# PURPOSE:  Helper function to convert a dataframe into a CSV file and return it as a Flask response.
#---

# Only supports exporting a single dataframe due to the nature of CSV format.
def df_to_csv(dataframe_dict, seperator):
    # CSV doesn't support multi-sheets, so only one dataframe can be exported.
    if len(dataframe_dict["filtered"]["df"].index) == 0: # If the dataframe is not filtered, export the unfiltered one.
        df = dataframe_dict["unfiltered"]["df"]
    else:
        df = dataframe_dict["filtered"]["df"]
    return Response(df.to_csv(sep=seperator, index=False, encoding='utf-8'), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=dataframe.csv"})


#---
# FUNCTION: upload_db_entry
# PURPOSE:  Function to handle the uploading of database entries.
#---

# It checks if the current db_entry is locked and creates a new entry if it is,
# otherwise, it updates the existing entry with new information.
def upload_db_entry(db_entry, mongo_update, url):
    # If the entry is locked, indicate a need for creating a new entry to avoid overwriting.
    if 'locked' in db_entry and db_entry['locked'] == True:
        db_entry['locked'] = False  # Unlock the db_entry for the new entry.
        db_entry_id = db.visualizations.insert_one(db_entry).inserted_id  # Insert the new db_entry and get its ID.
        #print('new entry!')
    else:
        db_entry_id = ObjectId(url)  # Use the existing db_entry's ID.
        db.visualizations.update_one({'_id': db_entry_id}, mongo_update)  # Update the existing db_entry.
        #print('This is the same entry')
        print("Active plugin id: ",db_entry['active_plugin_id'])
    return db_entry_id  # Return the ID of the db_entry that was inserted/updated.



#=============
# ROUTE '/query/
#=============

# Route to handle queries from the frontend. 
# It filters the database based on the query provided.
@app.route('/query', methods=['POST'])


#---
#FUNCTION: search_query
#PURPOSE: This function is responsible for handling POST requests that contain a user-defined query for filtering data.
# It extracts the query and the unique identifier (URL) for the database entry (visualization configuration),
# applies the filter to the specified dataset, updates the database with the filtered data,
# and returns the updated database entry ID.
#---
 
def search_query():
    try:
        # Dynamically import a custom module designed for applying filters to dataframes.
        # This module contains and applies query logic to the dataframe to produce a subset of the data based on the specified criteria.
        import filter_dataframe  # Load custom module.

        # Extract the query and the unique identifier from the POST request data.
        query = json.loads(request.form['query'])
        url = json.loads(request.form['url'])
        
        # Retrieve the database entry for the visualization configuration using the provided unique identifier.
        # This entry includes the 'transformed_dataframe', which is the dataset to be filtered.
        db_entry = db.visualizations.find_one({"_id": ObjectId(url)}, {'_id': False})

        # Load the dataframe from its Parquet representation stored in MongoDB.
        # Parquet is a columnar storage file format that supports efficient compression and encoding schemes.
        df = pd.read_parquet(BytesIO(db_entry['transformed_dataframe']))  # Load the dataframe.
        # print('query: ', query)

        # Apply the user-defined query to filter the dataframe. The `filter_dataframe.main` function
        # is assumed to take the query and the original dataframe as inputs and return a new dataframe
        # that only contains the rows that match the query criteria.
        filtered_df = filter_dataframe.main(query, df)  # Filter the dataframe based on the query.
        
        # Prepare an update operation for the MongoDB document. This operation sets the new 'filtered_dataframe'
        # (after converting it to Parquet and then to binary for storage), resets 'vis_links' to an empty list
        # (as the existing visualizations may no longer be relevant to the filtered data), and stores the query itself.
        mongo_update = {
            '$set': {
                'filtered_dataframe': df_to_parquet(filtered_df),
                'vis_links': [],
                'query': query
            }
        }
        
        # Apply the update to the database entry and retrieve the updated entry's ID.
        # This step involves calling a previously defined function `upload_db_entry` which abstracts
        # the logic for updating or creating database entries.
        db_entry_id = upload_db_entry(db_entry, mongo_update, url)  # Update the db_entry with the new filtered data.

        # Return a response to the client that includes the ID of the updated database entry.
        # This allows the client to reference the updated visualization configuration.
        return Response(dumps({'db_entry_id': db_entry_id}, allow_nan=True), mimetype="application/json")
    
    except Exception as e:
         # In case of any errors during the process, log the error and return a standardized error response.
        # This helps with debugging and ensures the client is aware of the failure.
        print(str(e))
        return respond_error(ERROR_MESSAGES['query_error']['expected']['type'], str(e))




#=============
# ROUTE '/locked'
#=============
    
# Route to lock the session, preventing further modifications to the db_entry.
@app.route('/locked', methods=['POST'])

#---
#FUNCTION: lock_session
#PURPOSE:  This function is designed to "lock" a visualization session by setting a 'locked' flag in the database. 
#          Once locked, the session's data cannot be altered, ensuring the current state of the visualization 
#          is preserved. This is particularly useful for finalizing a visualization for presentation or further analysis.
#---

def lock_session():
    print('locking')
    try:
        # The MongoClient import is redundant here if it's already imported globally. 
        # It's included for clarity within this snippet but should be considered for removal 
        # to adhere to best practices regarding imports (i.e., imports at the beginning of a file).
        from pymongo import MongoClient

        # Extract the unique identifier (URL) of the visualization session from the request form data.
        # This ID is used to find the specific database document corresponding to the session.
        url = json.loads(request.form['url'])
        print('URL: ', url)  # Logging the URL for debugging purposes.

        # Update the specified visualization document in the MongoDB 'visualizations' collection,
        # setting its 'locked' field to True. This operation effectively locks the session, preventing
        # any further modifications to its associated data and configuration.
        db.visualizations.update_one({'_id': ObjectId(url)}, {'$set': {'locked': True}})

        # Upon successful locking of the session, return a simple success message. 
        # In a more comprehensive application, this might be replaced with a more detailed response 
        # or a status code indicating success.
        return "success"
    except Exception as e:
        # If an error occurs during the process, log the error message for troubleshooting purposes.
        # Then, return a standardized error response using the `respond_error` function,
        # which likely formats the error into a JSON response suitable for client-side handling.
        print('###### ERROR')
        return respond_error(ERROR_MESSAGES['locking_error']['expected']['type'], str(e))



#=============
# ROUTE '/active_plugin'
#=============
    
# Route to set the active plugin based on user selection.
@app.route('/active_plugin', methods=['POST'])


#---
# FUNCTION: set_active_plugin
# PURPOSE: This function updates the current visualization session to set a specified plugin as the "active" plugin. 
#          This allows users to dynamically change how data is visualized by selecting different plugins according to their analysis needs.
#---

def set_active_plugin():
    try:
        # Importing MongoClient in each function may not be necessary if it's already imported globally.
        # This import is shown for clarity but should be done at the top of the file in practice.
        from pymongo import MongoClient

        # Extract the ID of the plugin to be activated from the request's form data.
        # This ID is crucial for identifying which plugin should be marked as active in the database.
        active_plugin_id = json.loads(request.form['active_plugin_id'])
        print(active_plugin_id)  # Logging for debugging purposes.

        # Similarly, extract the URL (unique identifier for the visualization session/document) from the request.
        url = json.loads(request.form['url'])

        # Retrieve the specific database entry for the visualization session using its unique identifier.
        # This entry contains current configuration data, including which plugin is currently active.
        db_entry = db.visualizations.find_one({"_id": ObjectId(url)}, {'_id': False})

        # Prepare the update operation to change the 'active_plugin_id' field to the new plugin's ID.
        # This operation specifies exactly how the document should be updated in the database.
        mongo_update = {'$set': {'active_plugin_id': active_plugin_id}}

        # Call the `upload_db_entry` function to apply the update to the database. This function likely abstracts
        # the logic for either creating a new entry or updating an existing one, depending on the context.
        db_entry_id = upload_db_entry(db_entry, mongo_update, url)

        # If the update operation is successful, return a simple success message to the requester.
        # In a real-world application, this might be more detailed or structured to provide feedback to the user.
        return "success"
    except Exception as e:
        # In case of an error (such as a database update failure or an issue with the request data),
        # log the error for troubleshooting and return a standardized error response.
        # The `respond_error` function formats this response in a way that's expected by the client-side application.
        print(e)
        return respond_error('Error in active plugin loading', str(e))




#=============
# ROUTE '/visualization'
#=============
    
# This route handles the generation and retrieval of visualization links based on the dataset
# and the plugin selected by the user. It serves as an endpoint for the front-end to request
# visualization of data through specific visualization plugins.
@app.route('/visualization', methods=['POST'])

#---
# FUNCTION: make_vis_link
# PURPOSE: The purpose of the `make_vis_link` function is to dynamically generate a visualization link
#          for a specific dataset using a selected visualization plugin. This function takes a plugin ID
#          and a dataset identifier from a client-side request, retrieves the corresponding dataset from
#          the database, applies the specified visualization plugin to generate a visualization, and updates
#          the database with the link to the newly created visualization. This enables users to interactively
#          explore their data through various visualization techniques and facilitates a dynamic, user-driven
#          approach to data analysis within the application. The function ensures that each visualization
#          is traceable and accessible through a unique link, enhancing the data exploration experience by
#          allowing users to switch between different visualizations seamlessly.
#---

def make_vis_link():
    try:
        # Parse the plugin ID and the MongoDB document ID (url) from the POST request.
        # These are essential for identifying which plugin to use for visualization
        # and which dataset (stored as a document in the 'visualizations' collection) to visualize.
        plugin = json.loads(request.form['plugin'])
        url = json.loads(request.form['url'])
        print('url: ', url, 'plugin: ', plugin)

        # Retrieve the MongoDB document (visualization entry) using the document ID provided in the request.
        # This entry contains all necessary data and metadata for visualization, such as the dataset itself,
        # any applied filters, and visualization configurations.
        # POTENTIAL CHANGE: Right now every new visualization creates a new MongoDB entry
        db_entry = db.visualizations.find_one({"_id": ObjectId(url)}, {'_id': False})

        # Check if there is a filtered version of the dataset available. If so, use it for visualization.
        # This allows the visualization to reflect any filtering or data manipulation performed by the user.
        # If not, fallback to using the original (unfiltered) dataset.
        if len(db_entry['filtered_dataframe']) > 0:
            vis_link = visualize.route(db.plugins, pd.read_parquet(
            BytesIO(db_entry['filtered_dataframe'])), plugin, ObjectId(url))
        else:
            vis_link = visualize.route(db.plugins, pd.read_parquet(
            BytesIO(db_entry['transformed_dataframe'])), plugin, ObjectId(url))

        # Once the visualization link is generated, update the corresponding MongoDB document
        # to include this new visualization link. This uses the '$push' operation to add the link
        # to an array of visualization links ('vis_links'), ensuring that multiple visualizations
        # can be associated with a single dataset.
        db.visualizations.update_one({'_id': ObjectId(url)}, {
            '$push': {'vis_links': vis_link}})

        print(vis_link)

        # Return the visualization link as a JSON response to the frontend, allowing the user to
        # access the generated visualization.
        return Response(dumps({'vis_link': vis_link}, allow_nan=True), mimetype="application/json")

    # Handle any exceptions that might occur during the process, such as issues with data retrieval,
    # problems during the visualization generation process, or database update failures. Log the error
    # for debugging purposes and return a standardized error response to the frontend.
    except Exception as e:
        print(str(e))
        return respond_error(ERROR_MESSAGES['visualization_error']['expected']['type'], str(e))




#=============
# ROUTE '/plugins'
#=============
    
# This route is dedicated to adding new visualization plugins into the system.
# It handles the POST request containing plugin metadata and potentially an icon file,
# saves the plugin data into MongoDB, and associates it with a specific visualization if provided.
@app.route('/plugins', methods=['POST'])


#---
# FUNCTION: add_plugin
# PURPOSE: The purpose of the `add_plugin` function is to facilitate the addition of new visualization plugins
#          into the system. It handles incoming requests that contain metadata and possibly an icon file for 
#          the new plugin, saving this information to the database. This function not only stores the plugin's 
#          metadata but also manages its association with existing or new visualization configurations. 
#          By doing so, it enriches the application's visualization capabilities, allowing users to 
#          dynamically explore data through a broader range of visual interpretations and analyses.
#          This extensibility supports continuous improvement and customization of the visualization experience.
#---

def add_plugin():
    # Dynamically import necessary modules for MongoDB operations and handling ObjectIds.
    from pymongo import MongoClient
    from bson.json_util import ObjectId

    # Extract the plugin metadata sent from the frontend in the form data of the request.
    metadata = json.loads(request.form['form'])

    # Attempt to upload the plugin icon file using a helper function `upload_file`
    # which also checks the file against a whitelist of allowed extensions for security.
    source, extension = upload_file(request, ALLOWED_EXTENSIONS_ICON, metadata)

    # Secure the filename to prevent directory traversal vulnerabilities and save the file to a predefined location.
    # Here, '/Users/' is used, but typically, you would save this in a directory within the application's scope,
    # or a static assets directory configured to serve files.
    plugin_name = secure_filename(source.filename)
    source.save(os.path.join("/Users/", plugin_name))

    # Update the metadata with the actual filename used to save the plugin icon.
    # This allows the system to reference and retrieve the icon when needed.
    metadata['filename'] = plugin_name

    # Insert the plugin metadata into the 'plugins' collection in MongoDB and retrieve the inserted document's ID.
    db_plugin_entry_id = db.plugins.insert_one(metadata).inserted_id

    # Check if the plugin is being added to a new visualization or an existing one.
    # If 'db_entry_id' is not provided, it indicates a new visualization configuration.
    if metadata['db_entry_id'] == '':
        import copy
        # Create a deep copy of a predefined database entry mockup.
        # This mockup provides a template for how visualization configurations are structured.
        db_entry = copy.deepcopy(DB_ENTRY_MOCKUP)

        # Append the newly added plugin's ID to the list of plugins associated with this visualization.
        db_entry['plugins_id'].append(db_plugin_entry_id)

        # Ensure the new visualization is not marked as locked to allow further modifications.
        db_entry['locked'] = False

        # Insert the new visualization configuration into the 'visualizations' collection and retrieve its ID.
        db_entry_id = db.visualizations.insert_one(db_entry).inserted_id
        print('db_entry_id empty url:', db_entry_id)
    else:
        # If 'db_entry_id' is provided, fetch the existing visualization configuration from the database.
        db_entry = db.visualizations.find_one({"_id": ObjectId(metadata['db_entry_id'])}, {'_id': False})

        # Append the newly added plugin's ID to the existing visualization's list of plugins.
        plugins_id = db_entry['plugins_id']
        plugins_id.append(db_plugin_entry_id)

        # Update the existing visualization document in the database with the new list of plugin IDs.
        db.visualizations.update_one({'_id': ObjectId(metadata['db_entry_id'])}, {'$push': {'plugins_id': db_plugin_entry_id}})
        print("metadata['db_entry']", metadata['db_entry_id'])
        db_entry_id = ObjectId(metadata['db_entry_id'])
        print('db_entry_id filled id: ', db_entry_id)

    # After successfully adding the plugin and potentially updating a visualization configuration,
    # respond to the frontend with the ID of the visualization document that was either created or updated.
    print('db_plugins_id: ', db_plugin_entry_id)
    return Response(dumps({'db_entry_id': db_entry_id}, allow_nan=True), mimetype="application/json")




#=============
# ROUTE '/config'
#=============

@app.route('/config', methods=['GET', 'POST'])

#---
# FUNCTION: respond_config
# PURPOSE: The purpose of the `respond_config` function is to retrieve and return the configuration of a 
#          specific visualization session based on its unique identifier. This configuration includes 
#          information about the dataset, any applied filters, and the set of plugins associated with 
#          the session. The function supports dynamic interaction with the visualization data, enabling 
#          users to save their work and return to it later or share it with others. It caters to both 
#          retrieving an existing configuration and initializing a new session with a default configuration.
#---

def respond_config():
    print('responding...')
    
    # Check if a unique identifier (URL) for the visualization configuration has been provided.
    if request.form['url'] != 'undefined':
       # Convert the string representation of the ObjectId back into an ObjectId type.
        db_entry_id = ObjectId(loads(request.form['url']))
        print('Object_ID: ', db_entry_id)  # Log the ObjectId for debugging purposes.

        # Retrieve the visualization configuration document from the MongoDB 'visualizations' collection.
        db_entry = db.visualizations.find_one({"_id": db_entry_id})
        
        # Convert the ObjectId to a string for JSON serialization compatibility.
        # print(len(bson.BSON.encode(db_entry)))
        db_entry['_id'] = str(db_entry['_id'])

        #db_entry['plugins'] = [plugin for plugin in db.plugins.find(
        #    {'_id': {'$in': db_entry['plugins_id']}})]
        
        # Here we load all plugins found in the dedicated plugins db. Going forward, we'll load plugins from a local json file, making this key unnecessary.
        # db_entry['plugins'] = [plugin for plugin in db.plugins.find(
        #     {'_id': {'$in': db_entry['plugins_id']}})]
        
        
        # Check if the 'transformed_dataframe' field is stored as binary data (bytes).
        # If so, convert it from its Parquet format to JSON for client-side use.
        # The conversion process replaces any NaN values with None to ensure JSON serialization compatibility.
        if type(db_entry['transformed_dataframe']) == bytes: # The mockup db_entry stores the empty transformed_dataframe as a list, so don't convert that one.
            # PERFORMANCE: We have to replace NaN cells with None for JSON.
            db_entry['transformed_dataframe'] = pd.read_parquet(BytesIO(db_entry['transformed_dataframe'])).to_json(orient='records')
        # Attempt to convert the 'filtered_dataframe' in the same manner as 'transformed_dataframe',
        # if it exists. This field represents any user-applied filters on the dataset.
        try:
            # PERFORMANCE: We have to replace NaN cells with None for JSON.
            db_entry['filtered_dataframe'] = pd.read_parquet(BytesIO(db_entry['filtered_dataframe'])).to_json(orient='records')
        except:
            pass  # If the 'filtered_dataframe' doesn't exist or an error occurs, ignore it.
        
        # Testing - For size benchmarks
        # import bson
        # print('######### Size of document')
        # print(len(bson.BSON.encode(db_entry)))

        # Return the visualization configuration document as a JSON response to the client.
        return Response(dumps({'db_entry': db_entry}, allow_nan=True), mimetype="application/json")
    else:
        # If the 'url' parameter is undefined, it indicates a request to initialize a new visualization session.
        print('undefined')
        import copy
        # Create a new visualization configuration using a predefined template (DB_ENTRY_MOCKUP).
        db_entry = copy.deepcopy(DB_ENTRY_MOCKUP)
        
        # print(db_entry)
        #db_entry['plugins'] = [plugin for plugin in db.plugins.find(
        #    {'_id': {'$in': db_entry['plugins_id']}})]
        
        # Return the new visualization configuration as a JSON response, allowing the client to start a new session.
        return Response(dumps({'db_entry': db_entry}, allow_nan=True), mimetype="application/json")


#---
# FUNCTION: respond_error
# PURPOSE: Error handling 
#---
    
def respond_error(error_type, error_message):
    return Response(dumps({'error_type': error_type, 'error_message': error_message}, allow_nan=True), mimetype="application/json")


#=============
# ROUTE '/upload'
#=============
@app.route('/upload', methods=['GET', 'POST'])

#---
# FUNCTION: add_matrix
# PURPOSE: The purpose of the `add_matrix` function is to handle the upload and integration of data matrices 
#          into the visualization system. It processes metadata and data files provided by the user, adjusting 
#          for specific data formatting nuances (e.g., decimal and separator characters in CSV files), and 
#          incorporates these matrices into existing or new visualization configurations. This function supports 
#          a variety of data sources, including direct file uploads and text inputs, enhancing the flexibility 
#          and usability of the data visualization platform.
#---

def add_matrix():
    try:
        # Parse the provided metadata from the form data, which includes information about the data source and formatting.
        metadata = json.loads(request.form['form'])
        
        # Adjust for data formatting specifics, such as decimal characters and CSV separators, which can vary by locale.
        if metadata['source']['database'] != None: # NOTE: Unelegant. Determine decimal and seperator characters of database csv's.
            metadata['formatting']['file']['csv_seperator'] = metadata['source']['database']['seperator']
            metadata['formatting']['file']['decimal_character'] = metadata['source']['database']['decimal_character'] # This is because all database files were exported with german decimals
        
        # Call the helper function `upload_file` to process the data file upload or text input based on the provided metadata.
        source, extension = upload_file(request, ALLOWED_EXTENSIONS_MATRIX, metadata)

        # Integrate the uploaded matrix into the system by adding it to the appropriate visualization configuration.
        db_entry_id = process_file.add_matrix(source, metadata, extension, db, PRE_CONFIGURED_PLUGINS)

        # Return the ID of the updated or newly created database entry as a JSON response.
        return Response(dumps({'db_entry_id': db_entry_id}, allow_nan=True), mimetype='application/json')
    except Exception as e:
        # Handle any exceptions that occur during the upload process and return an error message.
        print(str(e))
        return respond_error(ERROR_MESSAGES['upload_error']['expected']['type'], str(e))


#---
# FUNCTION: respond_data
# PURPOSE: Helper function to return a standardized success response with additional payload data. 
#---
    
def respond_data(label, payload):
    response_object = {'status': 'success'}
    response_object[label] = payload
    return response_object



#---
# FUNCTION: upload_file
# PURPOSE: serves as a multifaceted utility for processing data submissions 
#          to the visualization platform. It is designed to accept and validate user submissions 
#          through various formats, including direct file uploads, text inputs, and references to database 
#          exports. Its primary role is to ensure that the submitted data is accessible in a standardized 
#          format for further processing, while also enforcing security measures through file extension 
#          whitelisting. This function adapts to the diverse ways users might provide their data, 
#          facilitating a smoother integration into the visualization pipeline.
#---

def upload_file(request, extension_whitelist, metadata):
    # Check if the submission includes a file upload.
    if 'file' in request.files:
        file = request.files['file']

        # Validate that a file was actually selected for upload. If not, inform the user and redirect appropriately.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        # If a file is present and its extension is within the allowed set, proceed with processing.
        if file and allowed_file(file.filename, extension_whitelist):
            print('true')  # Debugging output to confirm file acceptance.
            extension = os.path.splitext(file.filename)[1]  # Extract the file's extension for further validation or processing.

        # Return both the file object and its extension as indicators of successful file processing.
        return file, extension

    # If the submission is through pasted text, directly return the text and indicate its format as a string.
    elif metadata['source']['text'] != None:
        return metadata['source']['text'], "string"

    # For submissions that refer to database exports, construct the path to the static file 
    # based on the filename provided in the metadata and return it along with the file's extension.
    # This allows for the processing of data that has been pre-uploaded or resides within a specific directory.
    elif metadata['source']['database'] != None:
        file = "static/" + metadata['source']['database']['filename']
        extension = os.path.splitext(metadata['source']['database']['filename'])[1]
        return file, extension

    # If none of the above conditions are met, return a "failure" status to indicate that the submission
    # did not conform to the expected formats or encountered an issue in processing.
    return "failure"




#=============
# ROUTE '/uploads/<filename>'
#=============
@app.route('/uploads/<filename>')

#---
# FUNCTION: uploaded_file
# PURPOSE: The purpose of the `uploaded_file` function is to serve files from a specified directory 
#          within the application's file system to the client. This function facilitates the retrieval 
#          and display of uploaded files, such as data matrices, visualization assets, or plugin icons, 
#          by generating a secure path to the requested file and sending it as a response to the client. 
#          It is particularly useful in scenarios where users need to access or download files that 
#          have been previously uploaded to the platform, ensuring that these files are served in a 
#          controlled and secure manner. By leveraging Flask's `send_from_directory` method, the function 
#          also automatically handles MIME type detection and appropriate header setting, enhancing the 
#          file delivery process.
#---

def uploaded_file(filename):
    # Utilize Flask's `send_from_directory` function to safely serve the requested file from the 
    # application's designated upload folder. This approach prevents direct filesystem access by the client, 
    # mitigating potential security risks associated with file serving.
    # The `app.config['UPLOAD_FOLDER']` variable contains the path to the directory from which files are served,
    # which should be configured securely within the application settings.
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)




#=============
# ROUTE '/matrix/<matrix_id>'
#=============
@app.route('/matrix/<matrix_id>', methods=['GET', 'POST'])

#---
# FUNCTION: remove_matrix
# PURPOSE: The purpose of the `remove_matrix` function is to facilitate the deletion of a specific data matrix 
#          from a user's visualization configuration. This function is essential for users who need to refine 
#          or correct their data sets by removing irrelevant or erroneous matrices. It enhances the user's 
#          ability to manage and organize their data effectively within the visualization platform. Upon 
#          receiving a request with the unique identifier of the matrix to be removed, along with any 
#          necessary metadata, this function orchestrates the removal process, updates the visualization 
#          configuration in the database, and informs the client of the successful update. This dynamic 
#          interaction allows for a flexible and user-centric approach to data visualization preparation 
#          and presentation.
#---

def remove_matrix(matrix_id):
    # Parse the JSON metadata sent with the request. This metadata could include details
    # about the visualization configuration or user-specific information necessary for
    # the removal process.
    metadata = json.loads(request.form['form'])
    print('###### metadata: ', metadata)  # Logging the received metadata for debugging purposes.

    # Call the `remove_matrix` function from the `process_file` module, passing in the necessary
    # parameters including the predefined DB_ENTRY_MOCKUP, the received metadata, the database connection (`db`),
    # and the matrix ID to be removed. The `process_file` module presumably contains logic to
    # update the database entry corresponding to the visualization configuration, removing
    # the specified matrix from it.
    # The `DB_ENTRY_MOCKUP` might be used here as a template or reference structure for the database entries,
    # ensuring consistency in the data format.
    db_entry_id = process_file.remove_matrix(DB_ENTRY_MOCKUP, metadata, db, matrix_id)

    # Return a response to the client, including the ID of the database entry that was updated
    # as a result of the matrix removal. This response allows the client to track the changes
    # and possibly make further requests based on the updated state of the visualization configuration.
    # The use of `dumps` with `allow_nan=True` ensures that the JSON serialization process
    # can handle NaN values, which are common in data processing and visualization contexts.
    return Response(dumps({'db_entry_id': db_entry_id}, allow_nan=True), mimetype="application/json")




#---
# FUNCTION: df_to_parquet
# PURPOSE:  This function converts a given pandas DataFrame to a Parquet file format and then encapsulates
#           the Parquet data into a binary format. The binary format is suitable for storage in MongoDB,
#           which allows for efficient serialization and deserialization of structured data like Parquet files.
#           Parquet is a columnar storage file format optimized for fast retrieval of columns of data,
#           not only saving storage space but also improving I/O efficiency compared to row-based formats like CSV.
#---

def df_to_parquet(df):
    # Import the necessary module to handle binary data in Python.
    # The Binary class specifically caters to binary data storage in MongoDB.
    from bson.binary import Binary

    # Create a BytesIO object, which is essentially an in-memory binary stream.
    # This object serves as a temporary storage for the Parquet data, allowing us
    # to perform operations on the data before it's finalized for storage.
    output = BytesIO()

    # Convert the pandas DataFrame to Parquet format and write the data to our BytesIO stream.
    # The 'to_parquet' function serializes the DataFrame as a Parquet, directly into the binary stream.
    df.to_parquet(output)

    # Reset the stream position to the beginning after writing.
    # This step is crucial for ensuring that subsequent read operations on the stream
    # start from the beginning of the data.
    output.seek(0)

    # The commented-out line appears to be a leftover from testing the function's correctness
    # by demonstrating how to read a Parquet file from a BytesIO stream back into a DataFrame.
    # This step isn't necessary for the purpose of converting and storing the DataFrame
    # but serves as a good reference for how to reverse the operation.
    # df = pd.read_parquet(BytesIO(test))


    # Convert the binary stream into a BSON binary object, which is the format expected by MongoDB
    # for storing binary data. This encapsulation makes the Parquet data ready for storage
    # in a MongoDB collection.
    return Binary(output.getvalue())


#client.close()
