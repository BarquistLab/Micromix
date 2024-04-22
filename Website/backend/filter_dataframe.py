import pandas as pd
import numpy as np
import operator
import initial_transformation
import filter_genelists
import row_filters
import pprint

#-------
#Filtering Summary
#-------

#To simplify the underlying code of the filtering process, filtering within this script is split into three steps:

#Step 1) Check if any transformations have been queried - If so, run those first and return the transformed df.
#Step 2) Generate masks from genelists that have been queried - then apply the mask to the default or transformed dataframe.
#Step 3) Check if any row filters have been applied (filter values) - if so, apply to the df thats been passed from the above two steps




#---
# FUNCTION: main
# PURPOSE:  Applies filtering based upon user selection
#---
def main(query, df):
    
    #Debugging: The initial user filter (query) - pprint displays the dictionary in a readable format
    #print("The user query:")
    #pprint.pprint(query)

    

    
    #The current dropdown options
    #Note: if more are included in other releases, they will need to be added here (such as TPM) 
    transformations_to_check = {"Round Values", 
                             "Change Values", 
                             "Convert to index column", 
                             "Hide Column", 
                             "Calculate fold change",
                             "Convert to log",
                             "Calculate log fold change"}



    #Check if the query contains anything - if not, return the entire df
    if len(query) == 0:
        return df #return the unmsked df
    else:
        
        #---
        # Step 1
        #---

        #Set variables
        transformed_df = None
        transformations_to_apply = []


        #Loop through each of the blocks within the query and look for the specific transformations
        for entry in query:
            for sub_entry in entry:
                # Check if the 'name' key in sub_entry is one of the transformations to check
                if sub_entry['name'] in transformations_to_check:
                    #print(f"Found: {sub_entry['name']}")

                    #Store each of the transformations that are found
                    transformations_to_apply.append(sub_entry)
                    



        #If transformations_to_apply is created, then a transformation block was added by the user  
        if transformations_to_apply:
            #A transformation was included - perform transformation and return transformed df
            transformed_df = initial_transformation.transform_df(query, df)
            df2 = transformed_df
        else:
            #No transformation was selected - return the initial df
            df2 = df


        

        # Create a copy of the original DataFrame to maintain the original data for reference or further use.
        #unfiltered_df = df.copy()

        
        # This was designed by Titus - keeping in here if required in future releases
        # This reduces the dataframe's size by around 50% but increases computation time by 30% and needs rounding due to lower FP precision
        # import experimental_features
        # df = experimental_features.adjust_numeric_dtype(df) 
        




        #---
        # Step 2
        #---
        
        #This script is automatically run, as most users filter for gene lists
        #Within filter_genelists.py, only genelist-based blocks are processed, which is found in properties["query"] 
        #These include hard coded genelists (PULs, SPI1 etc), and also annotation-based genelists (KEGG, GO etc)
        filtered_df = filter_genelists.filter_genelists(query, df2)
        
        
        #check if filtered_df was created - which will only happen if a genelist filter is user selected
        if 'filtered_df' in locals() and filtered_df is not None:
            #print("filtered_df was created.")
            filtered_df = filtered_df
        else:
            #print("filtered_df was not created.")
            filtered_df = df2




        #---
        # Step 3
        #---

        #Have any row filters been applied? (this is the first button: Filter--> Filter Values)

        #similar to the transformations in Step 1 - this list can be added to if needed
        filters_to_check = {"Filter values"}
        all_filters = []

        #Look for and store and filters
        for entry in query:
            for sub_entry in entry:

                # Check if the 'name' key in sub_entry is a filter
                if sub_entry['name'] in filters_to_check:
                    
                    #store each of the row filters that are found 
                    all_filters.append(sub_entry)



        #Debugging:
        #print("len(all filters):: ", len(all_filters))
        #print("all filters:: ")
        #pprint.pprint(all_filters)

        row_filtered_df = row_filters.row_filters(query, filtered_df, all_filters)


        #check if row_filtered_df was created - which will only happen if a row filter is user selected
        if 'row_filtered_df' in locals() and row_filtered_df is not None:
            #A row filter was selected
            row_filtered_df = row_filtered_df
        else:
            #No row filters were applied - return the df passed from Step 2
            row_filtered_df = filtered_df


    return row_filtered_df
        


        
        

