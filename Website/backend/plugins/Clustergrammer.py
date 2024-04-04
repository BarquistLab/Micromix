def main(parameters):
    import requests
    import pandas as pd
    from io import StringIO
    df = parameters["df"]
    dataframe = prepare_df(df) # Define the path to the file you want to visualize.
    output = StringIO()
    dataframe.to_csv(output, sep='\t', index=False)
    output.name = "output.txt"
    output.seek(0)  
    upload_url = "https://amp.pharm.mssm.edu/clustergrammer/matrix_upload/" # Define the path to the visualizing server endpoint.
    response = requests.post(upload_url, files={'file': output})
    print(response.text)
    vis_link = response.text.replace("http://","https://")
    return vis_link

def prepare_df(df):
    import pandas as pd
    import copy
    import numpy as np
    dataframe = copy.deepcopy(df)

    # Append category title string before values for all cat columns.
    # dataframe[dataframe.columns[0:cat_amount]] = dataframe.columns[0:cat_amount] + \
    #     ': ' + dataframe[dataframe.columns[0:cat_amount]].astype(str)
    # Remove the category titles from first row.
    # categories = list(df.select_dtypes(exclude=[np.number]).columns) # Get all columns that are non numerics
    # value_columns = [x for x in list(df.columns) if x not in categories] # Get all columns that are not category columns
    value_columns = [name for name in list(df.columns) if name.startswith('(') and ") " in name]
    categories = [x for x in list(df.columns) if x not in value_columns] # Get all columns that are not value columns
    dataframe_reordered_columns = categories + value_columns
    dataframe = dataframe[dataframe_reordered_columns] # Put all categories column to the beginning of the dataframe.
    if len(categories) > 0:
        for category in categories:
            dataframe[category] = dataframe[category].name + ': ' + dataframe[category].astype(str)
            dataframe = dataframe.rename(columns={category: ''})
    else:
        dataframe.columns[0] = dataframe.columns[0].name + ': ' + dataframe.columns[0].astype(str)
        dataframe = dataframe.rename(columns={dataframe.columns[0]: ''})
    # Export the data frame as tab-seperated .txt.
    print('Output file has been generated and saved.')
    return dataframe