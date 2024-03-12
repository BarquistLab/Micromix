#--------------------------------
#
# Designed by Titus Ebbecke 2021-2022
# Modifications by Regan Hayward 2023+
#
#--------------------------------
# 
# 
# To-Do: Configure CORS to only allow specific requests.

import os
from flask import Flask, flash, request, redirect, url_for, jsonify, send_from_directory, Response, send_file
from werkzeug.utils import secure_filename
from flask_cors import CORS
import uuid
import json
from flask import json
import process_file
import visualize
from pymongo import MongoClient
from bson.json_util import loads, dumps, ObjectId
from io import BytesIO
import pandas as pd
import numpy as np




# variables
ALLOWED_EXTENSIONS_MATRIX = {'txt', 'xlsx', 'csv', 'tsv'}
ALLOWED_EXTENSIONS_ICON = {'svg', 'png', 'jpg', 'jpeg', 'gif'}
PRE_CONFIGURED_PLUGINS =  [ObjectId('5f984ac1b478a2c8653ed827'), ObjectId('5f284a560831e4a42a30d698'), ObjectId('5f284bc60831e4a42a30d699'), ObjectId('5fc156db0ccdd1e1e454f116')]
MATRIX = [
    {
        "id": uuid.uuid4().hex,
        "width": 5,
        "height": 5,
        "x": 2,
        "y": 2,
        "isActive": False
    }
]
DB_ENTRY_MOCKUP = {
    'active_matrices': [],
    'transformed_dataframe': [],
    'preview_matrices': MATRIX,
    'vis_links': [],
    'plugins_id': PRE_CONFIGURED_PLUGINS,
    'active_plugin_id': '',
    'active_organism_id': 'bacteroides-thetaiotaomicron-e2ad6b25-40cb-4594-8685-f4fcb3ceb0e7'
}

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





# configuration
DEBUG = True

# # instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)

app.config['CORS_HEADERS'] = 'Content-Type'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['FLASK_DEBUG']=1 
app.config['DEBUG'] = True
cors = CORS(app, resources={r"/*":{"origins": "*"}})

UPLOAD_FOLDER = '/static'  # NOTE: Change this to /uploads in production
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#@app.route have to be above if __name__ == '__main__':
@app.route('/status', methods=['GET'])
def the_status():
    return jsonify('alive!')


@app.route('/health-check')
def health():
    data = {'status': 'server is live'}

    resp = app.response_class(
    status=200,
    response= json.dumps(data),
    mimetype='application/json'
        )
    return resp

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# MongoDB
client = MongoClient()
db = client.micromix
visualizations = db.visualizations
plugins = db.plugins


def allowed_file(filename, extension_whitelist):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in extension_whitelist

@app.route('/export', methods=['POST'])
def export_df():
    try:
        export_form = json.loads(request.form['export_form'])
        url = json.loads(request.form['url'])
        db_entry = db.visualizations.find_one(
            {"_id": ObjectId(url)}, {'_id': False})
        dataframe_dict = {}
        try:
            df_filtered = pd.read_parquet(BytesIO(db_entry['filtered_dataframe']))
            dataframe_dict["filtered"] = {}
            dataframe_dict["filtered"]["df"] = df_filtered
            dataframe_dict["filtered"]["name"] = "Filtered Data"
        except (KeyError, TypeError):
            pass
        dataframe_dict["unfiltered"] = {}
        try:
            dataframe_dict["unfiltered"]["df"] = pd.read_parquet(BytesIO(db_entry['transformed_dataframe']))
        except KeyError: # This is probably unnecessary, as every entry should have a transformed_dataframe, in theory.
            print("NOTE: db_entry['transformed_dataframe'] not found, using db_entry['dataframe'] instead.")
            dataframe_dict["unfiltered"]["df"] = pd.read_parquet(BytesIO(db_entry['dataframe']))
        dataframe_dict["unfiltered"]["name"] = "Source Data"
        if export_form["file_type"] == 'excel':
            res = df_to_excel(dataframe_dict)
        elif export_form["file_type"] == 'csv':
            res = df_to_csv(dataframe_dict, export_form['csv_seperator'])
        return res
    except Exception as e:
        print(str(e))
        return respond_error(ERROR_MESSAGES['export_error']['expected']['type'], str(e))

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

def df_to_csv(dataframe_dict, seperator):
    # CSV doesn't support multi-sheets, so only one dataframe can be exported.
    if len(dataframe_dict["filtered"]["df"].index) == 0: # If the dataframe is not filtered, export the unfiltered one.
        df = dataframe_dict["unfiltered"]["df"]
    else:
        df = dataframe_dict["filtered"]["df"]
    return Response(df.to_csv(sep=seperator, index=False, encoding='utf-8'), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=dataframe.csv"})

def upload_db_entry(db_entry, mongo_update, url):
    if 'locked' in db_entry and db_entry['locked'] == True:
        db_entry['locked'] = False
        db_entry_id = db.visualizations.insert_one(db_entry).inserted_id
        print('new entry!')
    else:
        db_entry_id = ObjectId(url)
        db.visualizations.update_one({'_id': db_entry_id}, mongo_update)
        print('This is the same entry')
        print(db_entry['active_plugin_id'])
    return db_entry_id

@app.route('/query', methods=['POST'])
def search_query():
    try:
        import filter_dataframe
        query = json.loads(request.form['query'])
        url = json.loads(request.form['url'])
        db_entry = db.visualizations.find_one(
            {"_id": ObjectId(url)}, {'_id': False})
        df = pd.read_parquet(BytesIO(db_entry['transformed_dataframe']))
        # print('query: ', query)
        filtered_df = filter_dataframe.main(query, df)
        mongo_update = {
            '$set': {
                'filtered_dataframe': df_to_parquet(filtered_df),
                'vis_links': [],
                'query': query
            }
        }
        db_entry_id = upload_db_entry(db_entry, mongo_update, url)
        return Response(dumps({'db_entry_id': db_entry_id}, allow_nan=True), mimetype="application/json")
    except Exception as e:
        print(str(e))
        return respond_error(ERROR_MESSAGES['query_error']['expected']['type'], str(e))

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

@app.route('/visualization', methods=['POST'])
def make_vis_link():
    try:
        plugin = json.loads(request.form['plugin'])
        url = json.loads(request.form['url'])
        print('url: ', url, 'plugin: ', plugin)
        db_entry = db.visualizations.find_one(
            {"_id": ObjectId(url)}, {'_id': False})
        # CHANGE: Right now every new visualization creates a new MongoDB entry
        if len(db_entry['filtered_dataframe']) > 0:
            vis_link = visualize.route(db.plugins, pd.read_parquet(
            BytesIO(db_entry['filtered_dataframe'])), plugin, ObjectId(url))
        else:
            vis_link = visualize.route(db.plugins, pd.read_parquet(
            BytesIO(db_entry['transformed_dataframe'])), plugin, ObjectId(url))
        db.visualizations.update_one({'_id': ObjectId(url)}, {
            '$push': {'vis_links': vis_link}})
        print(vis_link)
        return Response(dumps({'vis_link': vis_link}, allow_nan=True), mimetype="application/json")
    except Exception as e:
        print(str(e))
        return respond_error(ERROR_MESSAGES['visualization_error']['expected']['type'], str(e))

@app.route('/plugins', methods=['POST'])
def add_plugin():
    from pymongo import MongoClient
    from bson.json_util import ObjectId
    metadata = json.loads(request.form['form'])
    source, extension = upload_file(request, ALLOWED_EXTENSIONS_ICON, metadata)
    plugin_name = secure_filename(source.filename)
    source.save(os.path.join(
        "/Users/", plugin_name))
    metadata['filename'] = plugin_name
    db_plugin_entry_id = db.plugins.insert_one(metadata).inserted_id
    if metadata['db_entry_id'] == '':
        import copy
        db_entry = copy.deepcopy(DB_ENTRY_MOCKUP)
        db_entry['plugins_id'].append(db_plugin_entry_id)
        db_entry['locked'] = False
        db_entry_id = db.visualizations.insert_one(db_entry).inserted_id
        print('db_entry_id empty url:', db_entry_id)
    else:
        db_entry = db.visualizations.find_one(
            {"_id": ObjectId(metadata['db_entry_id'])}, {'_id': False})
        plugins_id = db_entry['plugins_id']
        plugins_id.append(db_plugin_entry_id)
        db.visualizations.update_one({'_id': ObjectId(metadata['db_entry_id'])}, {
                                     '$push': {'plugins_id': db_plugin_entry_id}})
        print("metadata['db_entry']", metadata['db_entry_id'])
        db_entry_id = ObjectId(metadata['db_entry_id'])
        print('db_entry_id filled id: ', db_entry_id)
    print('db_plugins_id: ', db_plugin_entry_id)
    return Response(dumps({'db_entry_id': db_entry_id}, allow_nan=True), mimetype="application/json")

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

def respond_error(error_type, error_message):
    return Response(dumps({'error_type': error_type, 'error_message': error_message}, allow_nan=True), mimetype="application/json")

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

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/matrix/<matrix_id>', methods=['GET', 'POST'])
def remove_matrix(matrix_id):
    metadata = json.loads(request.form['form'])
    print('###### metadata: ', metadata)
    db_entry_id = process_file.remove_matrix(
        DB_ENTRY_MOCKUP, metadata, db, matrix_id)
    return Response(dumps({'db_entry_id': db_entry_id}, allow_nan=True), mimetype="application/json")

def df_to_parquet(df):
    from bson.binary import Binary
    output = BytesIO()
    df.to_parquet(output)
    output.seek(0)
    # df = pd.read_parquet(BytesIO(test))
    return Binary(output.getvalue())

#client.close()
