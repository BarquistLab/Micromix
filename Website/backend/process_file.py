import uuid
import pandas as pd
from bson.json_util import ObjectId, dumps
import numpy as np
from io import BytesIO

max_preview_rows = 12
max_preview_columns = 8
max_y = 1
active_matrices = [[]]

def convert_to_df(input_file, extension, metadata,):
    import experimental_features
    if extension == ".xlsx":
        df = pd.read_excel(input_file)
    elif extension == ".csv":
        if len(metadata["database_columns"]) > 0:
            df = pd.read_csv(input_file, sep=metadata["formatting"]["file"]["csv_seperator"], decimal=metadata["formatting"]["file"]["decimal_character"], on_bad_lines='skip', usecols=metadata["database_columns"])
        else:
            df = pd.read_csv(input_file, sep=metadata["formatting"]["file"]["csv_seperator"], decimal=metadata["formatting"]["file"]["decimal_character"], on_bad_lines='skip')
    elif extension == ".txt" or extension == ".tsv":
        df = pd.read_csv(input_file, sep='\t', decimal=metadata["formatting"]["file"]["decimal_character"], on_bad_lines='skip')
    elif extension == "string":
        from io import StringIO
        df = pd.read_csv(StringIO(input_file), sep='\t', decimal=metadata["formatting"]["text"]["decimal_character"], on_bad_lines='skip')
        df.columns = pd.to_numeric(df.columns,errors='ignore')
    else:
        print("Error: No valid extension. Please upload .xlsx (Excel), .csv, or .txt (TSV).")
        return "Error"
    # df.fillna(np.nan, inplace=True)
    df.columns = df.columns.str.replace('.', '_') # Dot's mess with the df. Replace it with an underscore: _
    df = experimental_features.adjust_numeric_dtype(df)
    return df

def insert_update_entry(entry, collection, metadata):
    # NOTE: WARNING: This function aims to prevent any updates on locked sessions. 
    # Be very careful when touching this!
    # More secure methods to avoid unwanted updates are welcome.
    if entry['locked'] == True: # Insert new entry if visualization is locked or new
        entry['locked'] = False
        db_entry_id = collection.insert_one(entry).inserted_id
        return_msg = db_entry_id
    elif entry['locked'] == False: # Update existing entry if existing visualization is modified and not locked
        collection.update_one({'_id': ObjectId(metadata['db_entry_id'])}, {'$set': entry})
        db_entry_id = ObjectId(metadata['db_entry_id'])
        return_msg = db_entry_id
    else:
        return_msg = "Error: The 'locked' state of this entry is not clear."
    return return_msg

# NOTE: remove_matrix is just shy of being redundant enough with add_matrix to not merge them into one function
def remove_matrix(mockup_db_entry, metadata, db, remove_id):
    print('remove_id', remove_id)
    from pymongo import MongoClient
    db_entry = db.visualizations.find_one({"_id": ObjectId(metadata['db_entry_id'])}, {'_id': False})
    db_entry['active_matrices'] = [[i for i in nested if i['id'] != remove_id] for nested in db_entry['active_matrices']] # remove entries matching the remove_id
    db_entry['active_matrices'] = [j for j in db_entry['active_matrices'] if j != []] # remove empty subarrays
    db_entry['active_matrices'] = correct_matrice_positions(db_entry['active_matrices'])
    db_entry['vis_links'] = []
    db_entry['active_plugin_id'] = ''
    db_entry['filtered_dataframe'] = []
    if len(sum(db_entry['active_matrices'], []))>0:
        print('sum long enough')
        db_entry = merge_db_entry(db_entry, sum(db_entry['active_matrices'], []))
        db_entry['preview_matrices'] = make_preview_matrices(db_entry['active_matrices'])

        # db_entry['vis_links'] = visualize.route(db.plugins, pd.DataFrame.from_dict(db_entry['transformed_dataframe']), metadata['categories'], db_entry['plugins_id']) # CHANGE: Right now every new visualization creates a new MongoDB entry
        db_entry_id = insert_update_entry(db_entry, db.visualizations, metadata)
    else:
        mockup_db_entry['locked'] = db_entry['locked']
        db_entry_id = insert_update_entry(mockup_db_entry, db.visualizations, metadata)
    return db_entry_id

def rename_df_columns(df, title):
    categories = list(df.select_dtypes(np.number).columns)
    df.columns = ['(' + title + ') ' + x if x in categories else x for x in df.columns] # Append the dataframe title to the column names
    return df

def remove_df_title(title):
    if title.startswith('('):
        try:
            title = title.split(') ', 1)[1]
        except:
            pass
    print('title: ', title)
    return title

# NOTE: This is a giant pile of 'mess'. Currently there only exists one dataframe and any kind of addition or subtractions means completely rebuilding this df from every source df in active_matrices.
def add_matrix(input_file, metadata, extension, db, pre_configured_plugins):
    from pymongo import MongoClient
    if metadata['db_entry_id'] != '': # If you edit an existing visualization
        db_entry = db.visualizations.find_one({"_id": ObjectId(metadata['db_entry_id'])}, {'_id': False})
        df = convert_to_df(input_file, extension, metadata)
        if metadata['transformation'] != '':
            transformation_type = metadata['transformation']['type']
            import transform_dataframe
            for matrix in sum(db_entry['active_matrices'], []):
                if matrix['id'] == metadata['matrix_id']:
                    df_old = pd.read_parquet(BytesIO(matrix['dataframe']))
                    try:
                        df_old.rename(columns=lambda title: remove_df_title(title), inplace=True) # Remove the title from the old base df.
                    except:
                        print("Error: The old dataframe's columns couldn't be renamed: ", df_old.columns)
                    break
            df = transform_dataframe.main(transformation_type, metadata, df_old, df)
        df = rename_df_columns(df, metadata["title"])
        db_entry['active_matrices'], added_axis = make_active_matrix(metadata, df, db_entry['active_matrices'], df_to_parquet(df))
        db_entry = merge_db_entry(db_entry, sum(db_entry['active_matrices'], []))
    else: # If you create a new visualization
        df = convert_to_df(input_file, extension, metadata)
        df = rename_df_columns(df, metadata["title"])
        db_entry = new_db_entry(df, metadata, pre_configured_plugins)
    db_entry['preview_matrices'] = make_preview_matrices(db_entry['active_matrices'])
    db_entry['vis_links'] = []
    db_entry['filtered_dataframe'] = []
    db_entry['active_plugin_id'] = ''
    db_entry['active_organism_id'] = metadata['local_active_organism_id']
    if metadata['db_entry_id'] == '': # Enter new DB entry when creating a new visualization
        db_entry_id = db.visualizations.insert_one(db_entry).inserted_id
    else: # Update existing DB entry when modifying an existing visualization
        db_entry_id = insert_update_entry(db_entry, db.visualizations, metadata)
    return db_entry_id

def merge_db_entry(db_entry, flattened_am):
    df_merged = pd.read_parquet(BytesIO(flattened_am[0]['dataframe']))
    for i in range(len(flattened_am)): # Looping through. This could be replaced in the future by merging only with the single transformed_dataframe.
        df_merged = pd.merge(df_merged, pd.read_parquet(BytesIO(flattened_am[i]['dataframe'])), how='outer') # NOTE: Performance
    # df_merged.fillna(np.nan, inplace=True) # Replace NA values with 0
    db_entry['transformed_dataframe'] = df_to_parquet(df_merged)
    return db_entry

def df_to_parquet(df):
    from bson.binary import Binary
    output = BytesIO()
    df.to_parquet(output)
    output.seek(0)
    # df = pd.read_parquet(BytesIO(test))
    return Binary(output.getvalue())

def new_db_entry(df, metadata, pre_configured_plugins):
    db_entry = {}
    db_entry['locked'] = False
    db_entry['active_matrices'] = [[]]
    db_entry['plugins_id'] = pre_configured_plugins
    # db_entry['active_plugin_id'] = ""
    db_entry['transformed_dataframe'] = df_to_parquet(df)
    db_entry['active_matrices'], added_axis = make_active_matrix(metadata, df, db_entry['active_matrices'], df_to_parquet(df))
    return db_entry

def make_active_matrix(metadata, df, active_matrices, dataframe): # NOTE: Why is there a df and a dataframe argument?
    # This is neither readable, nor necessary, but it works for now. I'm truly sorry.
    print('make_active_matrix')
    added_matrix = make_single_matrix(metadata['x'],metadata['y'],max_preview_columns,max_preview_rows,metadata['title'],True, dataframe)
    added_axis = 1
    if added_matrix['y']-1>len(active_matrices): # If new matrix is below current matrices (y-axis)
        active_matrices.append([])
        added_axis = 0
    elif added_matrix['y']<=1: # If new matrix is above current matrices (y-axis)
        active_matrices.insert(0, [])
        added_matrix['y']=2
        added_axis = 0
    if df.shape[0]<max_preview_rows:
        added_matrix['height'] = df.shape[0]
    if df.shape[1]<max_preview_columns:
        added_matrix['width'] = df.shape[1]
    # Yeah it doesn't get better here. Basically: If you upload the data to x=1 or y=1, it has to insert the matrix at index 0 to shift all other matrices 1 to the left or down.
    if added_matrix['y'] == 1:
        active_matrices[0].insert(added_matrix['x']-2, added_matrix)
    elif added_matrix['x'] == 1:
        active_matrices[added_matrix['y']-2].insert(0, added_matrix)
    else:
        try:
            active_matrices[added_matrix['y']-2][added_matrix['x']-2] = added_matrix
        except:
            active_matrices[added_matrix['y']-2].insert(added_matrix['x']-2, added_matrix)
    # print('active_matrices#########################: ', active_matrices)
    active_matrices = correct_matrice_positions(active_matrices)
    # print('active_matrices corrected: ', active_matrices)
    return active_matrices, added_axis

def correct_matrice_positions(active_matrices):
    for matrixY in range(len(active_matrices)):
            for matrixX in range(len(active_matrices[matrixY])):
                active_matrices[matrixY][matrixX]['x'] = matrixX+2
                active_matrices[matrixY][matrixX]['y'] = matrixY+2
    return active_matrices

def make_preview_matrices(active_matrices):
    import copy
    preview_matrices = [] # flush all preview_matrices to rebuild it later. Bad perfomance < more readable algorithm
    flattened_active_matrices = copy.deepcopy(sum(active_matrices, []))
    for matrix in flattened_active_matrices:
        preview_matrices.append(matrix)
    # for topMatrix in range(len(active_matrices[0])):
    #     preview_matrices.append(make_single_matrix(topMatrix+2, 1, active_matrices[0][topMatrix]['width'], 2, "", False, False))
    # for bottomMatrix in range(len(active_matrices[0])):
    #     preview_matrices.append(make_single_matrix(bottomMatrix+2, len(active_matrices)+2, active_matrices[len(active_matrices)-1][bottomMatrix]['width'], 2, "", False, False))
    for leftMatrix in range(len(active_matrices)):
        preview_matrices.append(make_single_matrix(1, leftMatrix+2, 2, active_matrices[leftMatrix][0]['height'], "", False, False))
    for rightMatrix in range(len(active_matrices)):
        preview_matrices.append(make_single_matrix(len(active_matrices[0])+2, rightMatrix+2, 2, active_matrices[rightMatrix][len(active_matrices[0])-1]['height'], "", False, False))
    return preview_matrices

def make_single_matrix(x, y, width, height, title, active, dataframe):
    ADD_MATRIX = {
        'title': title,
        'id': uuid.uuid4().hex,
        "width": width,
        'height': height,
        'x': x,
        'y': y,
        'isActive': active,
        'dataframe': dataframe
    }
    return ADD_MATRIX