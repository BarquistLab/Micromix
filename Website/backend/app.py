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
import numpy as np


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



# Function to check if the uploaded file's extension is within the allowed set.
# This helps prevent the upload of potentially malicious files.
def allowed_file(filename, extension_whitelist):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in extension_whitelist




#=============
# ROUTE 
#=============

# Route for exporting data in various formats (Excel or CSV) based on user's choice.
# Fetches the specific visualization data from MongoDB, prepares it, and sends the file to the user.
@app.route('/export', methods=['POST'])
def export_df():
    try:
        # Extract form data containing export options and the unique visualization identifier.
        export_form = json.loads(request.form['export_form'])
        url = json.loads(request.form['url'])
        db_entry = db.visualizations.find_one({"_id": ObjectId(url)}, {'_id': False})

        # Prepare dictionaries to hold filtered and unfiltered data for export.
        dataframe_dict = {}
        try:
            df_filtered = pd.read_parquet(BytesIO(db_entry['filtered_dataframe']))
            dataframe_dict["filtered"] = {"df": df_filtered, "name": "Filtered Data"}
        except (KeyError, TypeError):
            pass  # Skip if no filtered data is available.

        dataframe_dict["unfiltered"] = {}
        try:
            dataframe_dict["unfiltered"]["df"] = pd.read_parquet(BytesIO(db_entry['transformed_dataframe']))
        except KeyError:  # This is probably unnecessary, as every entry should have a transformed_dataframe, in theory.
            print("NOTE: 'transformed_dataframe' not found, using 'dataframe' instead.")
            dataframe_dict["unfiltered"]["df"] = pd.read_parquet(BytesIO(db_entry['dataframe']))
        dataframe_dict["unfiltered"]["name"] = "Source Data"

        # Determine the file type for export and prepare the response.
        if export_form["file_type"] == 'excel':
            res = df_to_excel(dataframe_dict)
        elif export_form["file_type"] == 'csv':
            res = df_to_csv(dataframe_dict, export_form['csv_seperator'])
        return res
    except Exception as e:
        print(str(e))
        return respond_error(ERROR_MESSAGES['export_error']['expected']['type'], str(e))



# Helper function to convert dataframes into an Excel file and return it as a Flask response.
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

# Helper function to convert a dataframe into a CSV file and return it as a Flask response.
# Only supports exporting a single dataframe due to the nature of CSV format.
def df_to_csv(dataframe_dict, seperator):
    # CSV doesn't support multi-sheets, so only one dataframe can be exported.
    if len(dataframe_dict["filtered"]["df"].index) == 0: # If the dataframe is not filtered, export the unfiltered one.
        df = dataframe_dict["unfiltered"]["df"]
    else:
        df = dataframe_dict["filtered"]["df"]
    return Response(df.to_csv(sep=seperator, index=False, encoding='utf-8'), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=dataframe.csv"})

# Function to handle the uploading of database entries.
# It checks if the current db_entry is locked and creates a new entry if it is,
# otherwise, it updates the existing entry with new information.
def upload_db_entry(db_entry, mongo_update, url):
    # If the entry is locked, indicate a need for creating a new entry to avoid overwriting.
    if 'locked' in db_entry and db_entry['locked'] == True:
        db_entry['locked'] = False  # Unlock the db_entry for the new entry.
        db_entry_id = db.visualizations.insert_one(db_entry).inserted_id  # Insert the new db_entry and get its ID.
        print('new entry!')
    else:
        db_entry_id = ObjectId(url)  # Use the existing db_entry's ID.
        db.visualizations.update_one({'_id': db_entry_id}, mongo_update)  # Update the existing db_entry.
        print('This is the same entry')
        print(db_entry['active_plugin_id'])
    return db_entry_id  # Return the ID of the db_entry that was inserted/updated.



#=============
# ROUTE 
#=============

# Route to handle queries from the frontend. 
#It filters the database based on the query provided.
@app.route('/query', methods=['POST'])
def search_query():
    try:
        import filter_dataframe  # Custom module for filtering dataframes based on queries.
        query = json.loads(request.form['query'])
        url = json.loads(request.form['url'])
        db_entry = db.visualizations.find_one({"_id": ObjectId(url)}, {'_id': False})
        df = pd.read_parquet(BytesIO(db_entry['transformed_dataframe']))  # Load the dataframe.
        # print('query: ', query)
        filtered_df = filter_dataframe.main(query, df)  # Filter the dataframe based on the query.
        # Prepare the update to set the filtered_dataframe and clear existing visualizations and queries.
        mongo_update = {
            '$set': {
                'filtered_dataframe': df_to_parquet(filtered_df),
                'vis_links': [],
                'query': query
            }
        }
        db_entry_id = upload_db_entry(db_entry, mongo_update, url)  # Update the db_entry with the new filtered data.
        return Response(dumps({'db_entry_id': db_entry_id}, allow_nan=True), mimetype="application/json")
    except Exception as e:
        print(str(e))
        return respond_error(ERROR_MESSAGES['query_error']['expected']['type'], str(e))




#=============
# ROUTE 
#=============
    
# Route to lock the session, preventing further modifications to the db_entry.
@app.route('/locked', methods=['POST'])
def lock_session():
    print('locking')
    try:
        from pymongo import MongoClient
        url = json.loads(request.form['url'])
        print('URL: ', url)
        db.visualizations.update_one({'_id': ObjectId(url)}, {
            '$set': {'locked': True}})
        return "success"
    except Exception as e:
        print('###### ERROR')
        return respond_error(ERROR_MESSAGES['locking_error']['expected']['type'], str(e))



#=============
# ROUTE 
#=============
    
# Route to set the active plugin based on user selection.
@app.route('/active_plugin', methods=['POST'])
def set_active_plugin():
    try:
        from pymongo import MongoClient
        active_plugin_id = json.loads(request.form['active_plugin_id'])
        print(active_plugin_id)
        url = json.loads(request.form['url'])
        db_entry = db.visualizations.find_one(
            {"_id": ObjectId(url)}, {'_id': False})
        mongo_update = {'$set': {'active_plugin_id': active_plugin_id}}
        db_entry_id = upload_db_entry(db_entry, mongo_update, url)
        return "success"
    except Exception as e:
        print(e)
        return respond_error('Error in active plugin loading', str(e))




#=============
# ROUTE 
#=============
    
# This route handles the generation and retrieval of visualization links based on the dataset
# and the plugin selected by the user. It serves as an endpoint for the front-end to request
# visualization of data through specific visualization plugins.

@app.route('/visualization', methods=['POST'])
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
# ROUTE 
#=============
    
# This route is dedicated to adding new visualization plugins into the system.
# It handles the POST request containing plugin metadata and potentially an icon file,
# saves the plugin data into MongoDB, and associates it with a specific visualization if provided.

@app.route('/plugins', methods=['POST'])
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
# ROUTE 
#=============
@app.route('/config', methods=['GET', 'POST'])
def respond_config():
    print('responding...')
    if request.form['url'] != 'undefined':
        # import bson
        # from pymongo import MongoClient
        db_entry_id = ObjectId(loads(request.form['url']))
        print('Object_ID: ', db_entry_id)
        db_entry = db.visualizations.find_one({"_id": db_entry_id})
        # print(len(bson.BSON.encode(db_entry)))
        db_entry['_id'] = str(db_entry['_id'])

        #db_entry['plugins'] = [plugin for plugin in db.plugins.find(
        #    {'_id': {'$in': db_entry['plugins_id']}})]
        
        # Here we load all plugins found in the dedicated plugins db. Going forward, we'll load plugins from a local json file, making this key unnecessary.
        # db_entry['plugins'] = [plugin for plugin in db.plugins.find(
        #     {'_id': {'$in': db_entry['plugins_id']}})]
        
        
        if type(db_entry['transformed_dataframe']) == bytes: # The mockup db_entry stores the empty transformed_dataframe as a list, so don't convert that one.
            # PERFORMANCE: We have to replace NaN cells with None for JSON.
            db_entry['transformed_dataframe'] = pd.read_parquet(BytesIO(db_entry['transformed_dataframe'])).to_json(orient='records')
        try:
            # PERFORMANCE: We have to replace NaN cells with None for JSON.
            db_entry['filtered_dataframe'] = pd.read_parquet(BytesIO(db_entry['filtered_dataframe'])).to_json(orient='records')
        except:
            pass
        # For size benchmarks
        # import bson
        # print('######### Size of document')
        # print(len(bson.BSON.encode(db_entry)))
        return Response(dumps({'db_entry': db_entry}, allow_nan=True), mimetype="application/json")
    else:
        print('undefined')
        import copy
        db_entry = copy.deepcopy(DB_ENTRY_MOCKUP)
        # print(db_entry)
        #db_entry['plugins'] = [plugin for plugin in db.plugins.find(
        #    {'_id': {'$in': db_entry['plugins_id']}})]
        return Response(dumps({'db_entry': db_entry}, allow_nan=True), mimetype="application/json")


#Error handling
def respond_error(error_type, error_message):
    return Response(dumps({'error_type': error_type, 'error_message': error_message}, allow_nan=True), mimetype="application/json")


#=============
# ROUTE 
#=============
@app.route('/upload', methods=['GET', 'POST'])
def add_matrix():
    try:
        metadata = json.loads(request.form['form'])
        if metadata['source']['database'] != None: # NOTE: Unelegant. Determine decimal and seperator characters of database csv's.
            metadata['formatting']['file']['csv_seperator'] = metadata['source']['database']['seperator']
            metadata['formatting']['file']['decimal_character'] = metadata['source']['database']['decimal_character'] # This is because all database files were exported with german decimals
        source, extension = upload_file(request, ALLOWED_EXTENSIONS_MATRIX, metadata)
        db_entry_id = process_file.add_matrix(source, metadata, extension, db, PRE_CONFIGURED_PLUGINS)
        return Response(dumps({'db_entry_id': db_entry_id}, allow_nan=True), mimetype='application/json')
    except Exception as e:
        print(str(e))
        return respond_error(ERROR_MESSAGES['upload_error']['expected']['type'], str(e))

def respond_data(label, payload):
    response_object = {'status': 'success'}
    response_object[label] = payload
    return response_object

def upload_file(request, extension_whitelist, metadata):
    if 'file' in request.files:
        file = request.files['file']
        # If user does not select file, browser also submit an empty part without filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename, extension_whitelist):
            print('true')
            extension = os.path.splitext(file.filename)[1]
        return file, extension
    # If data is pasted text with "Text" as source
    elif metadata['source']['text'] != None:
        return metadata['source']['text'], "string"
    elif metadata['source']['database'] != None:
        file = "static/" + metadata['source']['database']['filename']
        extension = os.path.splitext(metadata['source']['database']['filename'])[1]
        return file, extension
    return "failure"


#=============
# ROUTE 
#=============
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)




#=============
# ROUTE 
#=============
@app.route('/matrix/<matrix_id>', methods=['GET', 'POST'])

#---
# FUNCTION: remove_matrix
#---

# Function to handle the removal of a specific matrix from a visualization configuration.
# It is triggered by a request containing the matrix ID to be removed and additional metadata
# that might be needed for the operation.

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
#---
# This function converts a given pandas DataFrame to a Parquet file format and then encapsulates
# the Parquet data into a binary format. The binary format is suitable for storage in MongoDB,
# which allows for efficient serialization and deserialization of structured data like Parquet files.
# Parquet is a columnar storage file format optimized for fast retrieval of columns of data,
# not only saving storage space but also improving I/O efficiency compared to row-based formats like CSV.

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
