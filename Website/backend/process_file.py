import uuid
import pandas as pd
from bson.json_util import ObjectId, dumps
import numpy as np
from io import BytesIO

# Constants for controlling the display limits of the matrices and preview elements.
max_preview_rows = 12
max_preview_columns = 8
max_y = 1
active_matrices = [[]]


#---
# FUNCTION: convert_to_df
# PURPOSE: Converts an input file of a specified extension to a pandas DataFrame while applying any provided metadata formatting.
# PARAMETERS:
#   input_file: The file to be converted.
#   extension: The file extension to determine the appropriate pandas reader function.
#   metadata: A dictionary containing formatting details like column separators, decimal characters, and specific columns to use.
# RETURNS: A pandas DataFrame after applying specified formatting and transformations.
#---

def convert_to_df(input_file, extension, metadata):
    import experimental_features
    # Conditional logic to handle different file types using pandas reader functions.
    if extension == ".xlsx":
        df = pd.read_excel(input_file)
    # Additional handling for CSV files with specific formatting options.
    elif extension == ".csv":
        if len(metadata["database_columns"]) > 0:
            df = pd.read_csv(input_file, sep=metadata["formatting"]["file"]["csv_seperator"], decimal=metadata["formatting"]["file"]["decimal_character"], on_bad_lines='skip', usecols=metadata["database_columns"])
        else:
            df = pd.read_csv(input_file, sep=metadata["formatting"]["file"]["csv_seperator"], decimal=metadata["formatting"]["file"]["decimal_character"], on_bad_lines='skip')
    # Handling for text files with tab separation (TSV).
    elif extension == ".txt" or extension == ".tsv":
        df = pd.read_csv(input_file, sep='\t', decimal=metadata["formatting"]["file"]["decimal_character"], on_bad_lines='skip')
    # Special case for handling strings directly as CSV data.
    elif extension == "string":
        from io import StringIO
        df = pd.read_csv(StringIO(input_file), sep='\t', decimal=metadata["formatting"]["text"]["decimal_character"], on_bad_lines='skip')
        df.columns = pd.to_numeric(df.columns,errors='ignore')
    else:
        print("Error: No valid extension. Please upload .xlsx (Excel), .csv, or .txt (TSV).")
        return "Error"
    # df.fillna(np.nan, inplace=True)
    df.columns = df.columns.str.replace('.', '_') # Handle dots in column names. (# Dot's mess with the df. Replace it with an underscore: _)
    df = experimental_features.adjust_numeric_dtype(df)
    return df



#---
# FUNCTION: insert_update_entry
# PURPOSE: Inserts a new entry or updates an existing one in a MongoDB collection based on the 'locked' status of the entry.
# PARAMETERS:
#   entry: The document to insert or update.
#   collection: The MongoDB collection where the document resides.
#   metadata: Additional data used for determining the operation.
# RETURNS: The MongoDB entry ID of the inserted or updated document.
# NOTES: This function ensures that updates are only performed on unlocked entries to prevent unintended modifications.
#---
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



#---
# FUNCTION: remove_matrix
# PURPOSE: Removes a specified matrix from the active_matrices list in a database entry, then updates the database.
# PARAMETERS:
#   mockup_db_entry: A template or fallback database entry used if no active matrices remain after removal.
#   metadata: Contains details such as the database entry ID to identify the correct entry.
#   db: The database connection object to perform operations.
#   remove_id: The unique identifier of the matrix to be removed.
# RETURNS: The MongoDB entry ID of the updated or replaced database entry.
# NOTES: This function ensures the active_matrices list is correctly maintained and updates related fields in the database entry.
#---

# NOTE: remove_matrix is just shy of being redundant enough with add_matrix to not merge them into one function

def remove_matrix(mockup_db_entry, metadata, db, remove_id):
    print('remove_id', remove_id)
    from pymongo import MongoClient

    # Retrieve the current database entry based on ID from metadata.
    db_entry = db.visualizations.find_one({"_id": ObjectId(metadata['db_entry_id'])}, {'_id': False})
    
     # Remove the specified matrix and clean up empty subarrays
    db_entry['active_matrices'] = [[i for i in nested if i['id'] != remove_id] for nested in db_entry['active_matrices']] # remove entries matching the remove_id
    db_entry['active_matrices'] = [j for j in db_entry['active_matrices'] if j != []] # remove empty subarrays
    
     # Correct positions and update related fields.
    db_entry['active_matrices'] = correct_matrice_positions(db_entry['active_matrices'])
    db_entry['vis_links'] = []
    db_entry['active_plugin_id'] = ''
    db_entry['filtered_dataframe'] = []
    
    # Insert or update the database entry based on the presence of active matrices.
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


#---
# FUNCTION: rename_df_columns
# PURPOSE: Appends a title to the column names of a DataFrame if they represent numeric data.
# PARAMETERS:
#   df: The pandas DataFrame whose columns are to be renamed.
#   title: The title to append to the column names.
# RETURNS: The DataFrame with updated column names.
# NOTES: This function is used to provide context to the data in the DataFrame by indicating its source or category.
#---
def rename_df_columns(df, title):
    categories = list(df.select_dtypes(np.number).columns)
    # Conditionally append the title to numeric column names
    df.columns = ['(' + title + ') ' + x if x in categories else x for x in df.columns] # Append the dataframe title to the column names
    return df


#---
# FUNCTION: remove_df_title
# PURPOSE: Removes a title from the beginning of a string, specifically designed to strip titles from column names.
# PARAMETERS:
#   title: The string (column name) from which the title is to be removed.
# RETURNS: The modified string with the title removed.
# NOTES: This is useful for reverting changes made by the `rename_df_columns` function or cleaning column names.
#---
def remove_df_title(title):
    if title.startswith('('):
        try:
            title = title.split(') ', 1)[1]
        except:
            pass
    print('title: ', title)
    return title




#---
# FUNCTION: add_matrix
# PURPOSE: Adds a new matrix (data representation) to an existing visualization, handling both new and existing visualizations.
# PARAMETERS:
#   input_file: The file containing the data to be added.
#   metadata: Metadata including transformation details and titles for the data.
#   extension: The file extension to determine how to read the data.
#   db: Database connection object for accessing and updating visualization entries.
#   pre_configured_plugins: Pre-configured plugin IDs for the visualization.
# RETURNS: The MongoDB entry ID of the updated or newly created database entry.
# NOTES: This function involves converting the input file to a DataFrame, applying any specified transformations,
#        updating the active_matrices list, and either creating a new database entry or updating an existing one.
#---

# NOTE: This is a giant pile of 'mess'. Currently there only exists one dataframe and any kind of 
# addition or subtractions means completely rebuilding this df from every source df in active_matrices.

def add_matrix(input_file, metadata, extension, db, pre_configured_plugins):
    from pymongo import MongoClient
    # Check if this operation is for an existing visualization based on the presence of a database entry ID in the metadata.
    if metadata['db_entry_id'] != '': # If you edit an existing visualization
        # Retrieve the existing visualization entry from the database.
        db_entry = db.visualizations.find_one({"_id": ObjectId(metadata['db_entry_id'])}, {'_id': False})
        df = convert_to_df(input_file, extension, metadata)
        # Apply a data transformation if specified in the metadata.
        if metadata['transformation'] != '':
            transformation_type = metadata['transformation']['type']
            import transform_dataframe
            for matrix in sum(db_entry['active_matrices'], []):
                if matrix['id'] == metadata['matrix_id']:
                    df_old = pd.read_parquet(BytesIO(matrix['dataframe']))
                    try:
                        # Attempt to strip titles from the columns of the old DataFrame before transformation.
                        df_old.rename(columns=lambda title: remove_df_title(title), inplace=True) # Remove the title from the old base df.
                    except:
                        print("Error: The old dataframe's columns couldn't be renamed: ", df_old.columns)
                    break
            # Perform the transformation and update the DataFrame.
            df = transform_dataframe.main(transformation_type, metadata, df_old, df)
        # Rename DataFrame columns to include the visualization title.
        df = rename_df_columns(df, metadata["title"])
        # Update the active matrices with the new or transformed DataFrame.
        db_entry['active_matrices'], added_axis = make_active_matrix(metadata, df, db_entry['active_matrices'], df_to_parquet(df))
        # Merge all active matrices into a single DataFrame for the visualization.
        db_entry = merge_db_entry(db_entry, sum(db_entry['active_matrices'], []))
    # If you create a new visualization
    else: 
        # For new visualizations, convert the input file to a DataFrame and initialize a new database entry.
        df = convert_to_df(input_file, extension, metadata)
        df = rename_df_columns(df, metadata["title"])
        db_entry = new_db_entry(df, metadata, pre_configured_plugins)

    # Update the database entry with additional visualization properties.
    db_entry['preview_matrices'] = make_preview_matrices(db_entry['active_matrices'])
    db_entry['vis_links'] = []
    db_entry['filtered_dataframe'] = []
    db_entry['active_plugin_id'] = ''
    db_entry['active_organism_id'] = metadata['local_active_organism_id']

    # Insert the new visualization entry into the database or update the existing one.
    if metadata['db_entry_id'] == '': # Enter new DB entry when creating a new visualization
        db_entry_id = db.visualizations.insert_one(db_entry).inserted_id
    else:  #Update existing DB entry when modifying an existing visualization
        db_entry_id = insert_update_entry(db_entry, db.visualizations, metadata)
    return db_entry_id




#---
# FUNCTION: merge_db_entry
# PURPOSE: Merges multiple DataFrames (from a flattened active matrices list) into a single DataFrame, and updates the database entry with this merged DataFrame stored in a binary format suitable for MongoDB.
# PARAMETERS:
#   db_entry: The current database entry being worked on.
#   flattened_am: A flattened list of active matrices, each containing a reference to a DataFrame stored as a binary object.
# RETURNS: The updated database entry with the merged DataFrame.
# NOTES: This function is critical for consolidating multiple DataFrames into a single, comprehensive DataFrame. It utilizes an outer join to ensure all data is retained, which may highlight the need for performance optimization in future updates.
#---
def merge_db_entry(db_entry, flattened_am):
    # Initialize merging with the first DataFrame to establish the base for subsequent merges.
    df_merged = pd.read_parquet(BytesIO(flattened_am[0]['dataframe']))

    # Iterate over each matrix, merging its DataFrame with the accumulated DataFrame.
    for i in range(len(flattened_am)): # Looping through. This could be replaced in the future by merging only with the single transformed_dataframe.
        df_merged = pd.merge(df_merged, pd.read_parquet(BytesIO(flattened_am[i]['dataframe'])), how='outer') # NOTE: Performance
    # df_merged.fillna(np.nan, inplace=True) # Replace NA values with 0
    
    # Convert the merged DataFrame back into a binary format for storage in the database.
    db_entry['transformed_dataframe'] = df_to_parquet(df_merged)
    return db_entry



#---
# FUNCTION: df_to_parquet
# PURPOSE: Converts a pandas DataFrame into a binary format using Parquet, suitable for storage in a binary field in MongoDB.
# PARAMETERS:
#   df: The pandas DataFrame to be converted.
# RETURNS: A binary representation of the DataFrame.
# NOTES: Parquet is chosen for its efficient compression and retrieval capabilities, making it ideal for storing large DataFrames in binary database fields.
#---
def df_to_parquet(df):
    from bson.binary import Binary
    # Create a BytesIO stream to hold the Parquet-formatted data.
    output = BytesIO()
    # Convert the DataFrame to Parquet and write to the stream.
    df.to_parquet(output)
    # Rewind the stream to the beginning for reading.
    output.seek(0)
    # Return the binary data, ready for database insertion.
    # df = pd.read_parquet(BytesIO(test))
    return Binary(output.getvalue())


#---
# FUNCTION: new_db_entry
# PURPOSE: Creates a new database entry structure for a visualization, initializing it with a DataFrame, metadata, and pre-configured plugins. This includes converting the DataFrame to a binary format for storage and setting up the active matrices structure.
# PARAMETERS:
#   df: The DataFrame to include in the new database entry.
#   metadata: Metadata for the new entry, such as titles and transformation details.
#   pre_configured_plugins: A list of IDs for plugins pre-configured for use with this visualization.
# RETURNS: A dictionary representing the new database entry, ready for insertion into the database.
# NOTES: This function is a crucial part of initializing new visualizations, ensuring they're set up with all necessary information and data from the outset.
#---
def new_db_entry(df, metadata, pre_configured_plugins):
    db_entry = {}
    # Initialize the database entry with default and provided values.
    db_entry['locked'] = False
    db_entry['active_matrices'] = [[]]
    db_entry['plugins_id'] = pre_configured_plugins
    # db_entry['active_plugin_id'] = ""
    db_entry['transformed_dataframe'] = df_to_parquet(df)
    
    # Create and position the initial active matrix based on the provided DataFrame and metadata.
    db_entry['active_matrices'], added_axis = make_active_matrix(metadata, df, db_entry['active_matrices'], df_to_parquet(df))
    return db_entry



#---
# FUNCTION: make_active_matrix
# PURPOSE: Integrates a new matrix, based on provided DataFrame and metadata, into the active_matrices structure, adjusting its position and size according to specified parameters and the current layout.
# PARAMETERS:
#   metadata: Contains metadata for the matrix, including position (x, y), title, and any other relevant information.
#   df: The pandas DataFrame from which the matrix's content is derived, used to determine the matrix's size if it's smaller than the maximum preview dimensions.
#   active_matrices: The current structure of matrices (a nested list) being visualized, which will be updated with the new matrix.
#   dataframe: The binary representation of the DataFrame, to be stored in the new matrix's 'dataframe' field.
# RETURNS: A tuple containing the updated active_matrices structure and an indicator (added_axis) of whether a new row or column was added to the layout.
# NOTES: The function handles positioning logic to ensure the matrix is added in the correct location within the layout, potentially adjusting the overall structure of active_matrices. The presence of both 'df' and 'dataframe' parameters might be confusing; 'df' is used for dimension calculations, while 'dataframe' is the binary data to be stored.
#---
def make_active_matrix(metadata, df, active_matrices, dataframe): # NOTE: Why is there a df and a dataframe argument?
    # This is neither readable, nor necessary, but it works for now. I'm truly sorry (Titus).
    
    #print('make_active_matrix')
    # Create the new matrix with specified properties and the binary dataframe.
    added_matrix = make_single_matrix(metadata['x'],metadata['y'],max_preview_columns,max_preview_rows,metadata['title'],True, dataframe)
    
    # Initialize added_axis to indicate if a new row or column is added.
    added_axis = 1
    
    # Adjust the active_matrices structure based on the new matrix's y position
    if added_matrix['y']-1>len(active_matrices): # If new matrix is below current matrices (y-axis)
        active_matrices.append([])
        added_axis = 0
    elif added_matrix['y']<=1: # If new matrix is above current matrices (y-axis)
        active_matrices.insert(0, [])
        added_matrix['y']=2
        added_axis = 0

    # Adjust the matrix size if it's smaller than the max preview dimensions.
    if df.shape[0]<max_preview_rows:
        added_matrix['height'] = df.shape[0]
    if df.shape[1]<max_preview_columns:
        added_matrix['width'] = df.shape[1]

    # Yeah it doesn't get better here. Basically: If you upload the data to x=1 or y=1, it has to insert the matrix at index 0 to shift all other matrices 1 to the left or down.
    # Insert the matrix at the correct position within active_matrices.
    if added_matrix['y'] == 1:
        active_matrices[0].insert(added_matrix['x']-2, added_matrix)
    elif added_matrix['x'] == 1:
        active_matrices[added_matrix['y']-2].insert(0, added_matrix)
    else:
        try:
            active_matrices[added_matrix['y']-2][added_matrix['x']-2] = added_matrix
        except:
            active_matrices[added_matrix['y']-2].insert(added_matrix['x']-2, added_matrix)
    
    
    # Correct positions of all matrices after the addition.
    # print('active_matrices#####: ', active_matrices)
    active_matrices = correct_matrice_positions(active_matrices)
    # print('active_matrices corrected: ', active_matrices)
    return active_matrices, added_axis



#---
# FUNCTION: correct_matrice_positions
# PURPOSE: Corrects the x and y positions of matrices within the active_matrices structure to ensure consistency and accuracy in positioning, especially after matrices have been added or removed.
# PARAMETERS:
#   active_matrices: A nested list of matrix dictionaries, each representing a matrix with properties including position (x, y).
# RETURNS: The updated active_matrices list with corrected positions for each matrix.
# NOTES: This function is crucial for maintaining the integrity of the spatial arrangement of matrices, which can affect their display and interaction within a visualization.
#---
def correct_matrice_positions(active_matrices):
    # Iterate through each matrix to update its x and y positions based on its index within the nested list structure.
    for matrixY in range(len(active_matrices)):
            for matrixX in range(len(active_matrices[matrixY])):
                active_matrices[matrixY][matrixX]['x'] = matrixX+2
                active_matrices[matrixY][matrixX]['y'] = matrixY+2
    return active_matrices


#---
# FUNCTION: make_preview_matrices
# PURPOSE: Generates a list of preview matrices from the active matrices, used for providing a simplified view of the data structure for preview purposes.
# PARAMETERS:
#   active_matrices: A nested list of matrix dictionaries from which to generate the preview matrices.
# RETURNS: A list of preview matrices, each representing a portion of the visualization layout.
# NOTES: This function enhances the user interface by creating a simplified representation of complex data structures, aiding in visualization and layout planning.
#---
def make_preview_matrices(active_matrices):
    import copy
    # Initialize the list to hold preview matrices.
    preview_matrices = [] ## flush all preview_matrices to rebuild it later. Bad perfomance < more readable algorithm
    # Flatten the active_matrices list to simplify processing.
    flattened_active_matrices = copy.deepcopy(sum(active_matrices, []))

    # Directly copy existing matrices as part of the preview.
    for matrix in flattened_active_matrices:
        preview_matrices.append(matrix)
    # for topMatrix in range(len(active_matrices[0])):
    #     preview_matrices.append(make_single_matrix(topMatrix+2, 1, active_matrices[0][topMatrix]['width'], 2, "", False, False))
    # for bottomMatrix in range(len(active_matrices[0])):
    #     preview_matrices.append(make_single_matrix(bottomMatrix+2, len(active_matrices)+2, active_matrices[len(active_matrices)-1][bottomMatrix]['width'], 2, "", False, False))
    
    # Generate preview matrices for the left and right edges of the layout.
    for leftMatrix in range(len(active_matrices)):
        preview_matrices.append(make_single_matrix(1, leftMatrix+2, 2, active_matrices[leftMatrix][0]['height'], "", False, False))
    for rightMatrix in range(len(active_matrices)):
        preview_matrices.append(make_single_matrix(len(active_matrices[0])+2, rightMatrix+2, 2, active_matrices[rightMatrix][len(active_matrices[0])-1]['height'], "", False, False))
    return preview_matrices


#---
# FUNCTION: make_single_matrix
# PURPOSE: Creates a single matrix dictionary with specified properties, including position, size, title, and data content.
# PARAMETERS:
#   x, y: The x and y positions of the matrix within the visualization layout.
#   width, height: The width and height of the matrix, determining its size.
#   title: The title of the matrix, which may be used for labeling or identification.
#   active: A boolean indicating whether the matrix is active or part of the main visualization (True) or a supplementary preview element (False).
#   dataframe: The binary representation of the DataFrame associated with this matrix, stored for data persistence and retrieval.
# RETURNS: A dictionary representing the matrix with the specified properties.
# NOTES: This function is a foundational element for building and manipulating the data structure of a visualization, allowing for dynamic and flexible layout designs.
#---
def make_single_matrix(x, y, width, height, title, active, dataframe):
    # Define and return the matrix dictionary
    ADD_MATRIX = {
        'title': title,
        'id': uuid.uuid4().hex,  # Generate a unique identifier for the matrix.
        "width": width,
        'height': height,
        'x': x,
        'y': y,
        'isActive': active,
        'dataframe': dataframe  # Store the data content as a binary object.
    }
    return ADD_MATRIX