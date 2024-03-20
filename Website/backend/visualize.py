# This is the main point for visualizations.
# Parse all relevant dataframes to this module and decide what plugin to use with route().

#---
# FUNCTION: route
# PURPOSE: Dynamically loads a specified plugin module and uses it to process data, 
#          returning a visualization link. This function enables the flexible use of 
#          various plugins for data processing and visualization generation based on 
#          a given dataset and plugin specifications.
# PARAMETERS:
#   - collection: The database collection to operate on (not used in the current implementation but potentially useful for future extensions).
#   - df: The DataFrame to be processed by the plugin.
#   - plugin: A dictionary containing plugin details (name and ID).
#   - db_entry_id: The database entry ID for the data being processed.
# RETURNS: A dictionary with plugin name, plugin ID, and the generated link to the visualization.
#---


def route(collection, df, plugin, db_entry_id):
    import importlib
    from bson.json_util import ObjectId
    from pymongo import MongoClient
    
    #Print to console
    print("Loading plugin....")
    
     # Dynamically import the plugin module based on the plugin name provided.
    plugin_module = importlib.import_module("plugins.{}".format(plugin['name']))
    
    # Initialize a dictionary to store visualization metadata.
    visualization = {}
    visualization['plugin_name'] = plugin['name']
    visualization['plugin_id'] = str(plugin['_id'])

    # Call the main function of the plugin module with the DataFrame and db_entry_id as arguments.
    # Store the returned link (to the generated visualization) in the visualization dictionary.
    visualization['link'] = plugin_module.main({"df":df, "db_entry_id": db_entry_id})
    
     # Print the visualization link(s) for debugging
    print('vis_links: ', visualization)
    
    # Return the visualization dictionary, including the name, ID, and link of the plugin-generated visualization.
    return visualization