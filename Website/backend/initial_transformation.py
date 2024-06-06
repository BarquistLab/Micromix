import pandas as pd
import numpy as np
import operator
import pprint



#---
# GLOBAL DICTIONARY: COMPARISON_OPERATORS
# PURPOSE: Maps textual descriptions of comparison operations to their corresponding Python operator functions. This facilitates the dynamic application of comparison operations in data filtering and manipulation tasks.
# CONTENTS:
#   This dictionary contains key-value pairs where keys are string descriptions of comparison operators (e.g., '< less than') and values are the actual Python operator functions (e.g., operator.lt for less than).
# USAGE: Utilized in filtering functions to apply user-specified comparison operations on DataFrame columns.
#---

#Can be added or removed
COMPARISON_OPERATORS = {
    '< less than': operator.lt,
    '> more than': operator.gt,
    '>= more or equal to': operator.ge,
    '<= less or equal to': operator.le,
    '= equal to': operator.eq,
    '!= not': operator.ne
}




#---
# FUNCTION: transform_df
# PURPOSE: Applies a series of transformations to a pandas DataFrame based on a structured query input.
# PARAMETERS:
#   query - A structured list detailing the transformations to apply.
#   df - The DataFrame to transform.
# RETURNS: A DataFrame modified according to the specified transformations.
# NOTES: Supports operations such as replace, round, hide, logarithmic scaling, fold change calculations, index conversion, and more.
#---
def transform_df(query, df):
    
    #Store original df
    unfiltered_df = df.copy()

    masks = []
    transformations = []

    #Loop through each block and store information about each transformation
    for sub_query in query:
        for block in sub_query:
            if block["properties"]["type"] != "logic":
                
                #Store
                transformation = {"type": block["properties"]["type"],
                                  "details": block["forms"],
                                  "properties": block["properties"]}
                #append
                transformations.append(transformation)
    

    # Apply each transformation in the order they were provided.
    for transformation in transformations:
        
        #The specific transformation type - such as replace, hide etc
        ttype = transformation["type"]
        #The specific details
        details = transformation["details"]
        #print("ttype:: ",ttype)



        # Specific handling based on the type of transformation.

        

        #---
        #(Change values) 
        #---
        if ttype == "replace":
            
            #Capture string or numeric value
            try:
                input_value = float(details["filter_value"])
                target_value = float(details["target_value"])
                is_numeric = True
            except ValueError:
                input_value = str(details["filter_value"])
                target_value = str(details["target_value"])
                is_numeric = False


            #print("is_numeric::", is_numeric)
            #print("logical operator::", details["logical_operator"])
            
            #Make sure if string is entered, only = and != can be used
            if not is_numeric:
                if details["logical_operator"] not in ["= equal to", "!= not"]:  
                    raise ValueError("For string filters, only '= equal to' or '!= not' operators are allowed.")


            # Apply replacement logic
            comparison_operator, filter_area, any_column = setup_query_parameters(details, df)
            df_mask = filter_for(details, transformation["properties"], df, comparison_operator, filter_area)

    
            #Debugging
            #print("df_mask::", df_mask)
            #print("type(df_mask)::", type(df_mask))
            #print("df::", df)
            #print("df.shape::", df.shape)
            #print("df_mask.shape::", df_mask.shape)
            #print("target_value", target_value)
            #print("filter_area::", filter_area)


            # Loop through each column specified in the filter_area. 
            # 'enumerate' is used to also get the index 'i' for accessing the corresponding mask in df_mask.
            for i, column in enumerate(filter_area):
                
                # First, check if the current column from filter_area actually exists in the DataFrame 'df'.
                if column in df.columns: 

                    # If df_mask is a 2-dimensional array (implying multiple columns are involved),
                    # extract the mask for the current column by using 'i' to index the second dimension of df_mask.
                    # 'flatten' is called to ensure the mask is a 1D array.
                    # If df_mask is 1-dimensional (implying a single column or a single condition applied across multiple columns),
                    # just flatten df_mask to ensure it's 1D.
                    specific_mask = df_mask[:, i].flatten() if df_mask.ndim > 1 else df_mask.flatten()


                    # Convert the specific_mask array into a pandas Series. This conversion aligns the mask with the DataFrame's index.
                    # This step is crucial because operations between a DataFrame and a Series are aligned on the index by pandas,
                    # ensuring the mask is applied correctly row-wise.
                    specific_mask_series = pd.Series(specific_mask, index=df.index, dtype=bool)

                    # Apply the mask to the specific column in the DataFrame. The '.mask' method replaces values where the condition is True.
                    # Here, 'specific_mask_series' contains True for rows that should be replaced with 'other=target_value'.
                    # Rows corresponding to False in 'specific_mask_series' remain unchanged.
                    df[column] = df[column].mask(specific_mask_series, other=target_value)


                    # Attempt to convert the modified column back to numeric types, if possible. 
                    # This is done because the operation might involve changing data types (e.g., replacing text with numbers).
                    # 'downcast="integer"' attempts to downcast floats to integers where possible, reducing memory usage.
                    try:
                        df[column] = pd.to_numeric(df[column], downcast="integer")
                    except Exception:
                        # If conversion to numeric fails (for instance, if the column contains non-numeric data after replacement),
                        # force the column to be of string type to ensure consistency.
                        df[column] = df[column].astype(str)
                else:
                    # If a specified column in 'filter_area' does not exist in 'df', print a warning message.
                    # This is a safety check to avoid attempting operations on non-existent columns.
                    print(f"Column {column} does not exist in DataFrame.")





        #---
        # (Round Values) 
        #---
        elif ttype == "round":
            
            # Check if the operation is to be applied to all columns. If so, round all columns to the specified number of decimal places.
            if "all columns" in details["target_column"]:
                # Target all columns for rounding.
                target_area = list(df.columns)
                # Apply rounding
                df[target_area] = np.round(df[target_area], int(details["round_value"]))

            else:
                # Target specific column/s for rounding.
                target_area = details["target_column"]
                # Apply rounding
                df[target_area] = np.round(df[target_area], int(details["round_value"]))



        #---
        # (Hide Column) 
        #---
        elif ttype == "hide":
            
            # Determine if the operation targets all columns or specific ones.
            if "all columns" in details["target_column"]:
                # Preparing to target all columns, though not directly applicable in 'drop'.
                target_area = list(df.columns)
            else:
                # If specific columns are targeted, prepare to drop those columns.
                target_area = details["target_column"]
                # Drop (hide) the specified columns from the DataFrame.
                df.drop(target_area, axis=1, inplace=True)




        #---
        # (Convert to log) 
        #---
        elif ttype == "logarithmic":
            # NOTE: PERFORMANCE: Be careful with rounding when it comes to precision and performance. Maybe use pandas rounding function.
            # df[filter_area] = np.round(np.log(df[filter_area].values) / np.log(float(block["forms"]["log_value"])), 3) 

            # Prepare for log transformation by determining the target columns based on user input.
            comparison_operator, filter_area, any_column = setup_query_parameters(details, df)

            # Apply log transformation to the targeted filter area, dividing by log of specified base.
            # The 'details["log_value"]' specifies the base of logarithm.

            # df[filter_area] = np.log(df[filter_area].values) / np.log(float(block["forms"]["log_value"]))
            log_base = float(details["log_value"])
            df[filter_area] = np.log(df[filter_area].values) / np.log(log_base)

            # Replace any infinite values resulting from the log transformation with NaN, to avoid data errors.
            df.replace([np.inf, -np.inf], np.nan, inplace=True)
        




        #---
        # (Calculate fold change) 
        #---
        elif ttype == "fold_change":
            # df[filter_area] = np.round(df[filter_area].div(df[block["forms"]["target_column"]].values,axis=0), 3) 
            # NOTE: PERFORMANCE: Be careful with rounding when it comes to precision and performance. Maybe use pandas rounding function.

            # Calculates the fold change for selected columns based on a reference (target) column.
            # First, it retrieves the necessary comparison operator and filter area for the operation.
            comparison_operator, filter_area, any_column = setup_query_parameters(details, df)

            # Divide the values in the filter area by the values in the target column to get the fold change.
            # This operation is performed row-wise ('axis=0' indicates row-wise operation).
            df[filter_area] = df[filter_area].div(df[details["target_column"]].values, axis=0)

            try:
                # Optionally, apply logarithmic transformation to the fold change values to get log fold change.
                # The log base is specified by the user ('log_value'). This step is useful for data normalization, especially in gene expression analysis.

                #NOTE:
                # For relative gene expression - Dividing first and calculating the log AFTER might loose precision.
                # Alternative would be to calculate log(df) - log(target_column).
                # df[filter_area] = np.round(np.log(df[filter_area].values) / np.log(float(block["forms"]["log_value"])), 3) 
                # NOTE: PERFORMANCE: Be careful with rounding when it comes to precision and performance. Maybe use pandas rounding function.
                log_base = float(details["log_value"])
                df[filter_area] = np.log(df[filter_area].values) / np.log(log_base)
            except:
                # If the log transformation fails (e.g., log of negative numbers), skip this step.
                pass
            
            # Remove base columns.
            # After calculating fold change, optionally drop the base (reference) columns to simplify the DataFrame.
            # This is useful if the original values are no longer needed after fold change calculation.
            df.drop(details["target_column"], axis=1, inplace=True)
            
            # Replace any resulting infinite values with NaN to maintain data integrity.
            df.replace([np.inf, -np.inf], np.nan, inplace=True)
        

        


        #---
        # (Convert to index column) 
        #---
        elif ttype == "convert_to_index":
            # This block is designed to convert specified columns into index columns. This is typically used for
            # reformatting or organizing data in preparation for analysis or visualization - ie, which col to show within a plugin.

            # Determine the target columns based on user input. If 'all columns' is specified, all DataFrame columns are targeted (which is kinda weird).
            # Otherwise, specific columns specified by the user are targeted.
            if "all columns" in details["target_column"]:
                target_area = list(df.columns)
            else:
                target_area = details["target_column"]

            
            # Iterate over the specified target columns for conversion.
            for target_column in target_area:
                # Check if the target column name starts with a specific pattern (e.g., '(').
                # This can be used to identify columns with a specific naming convention.
                if target_column.startswith("("):
                    try:
                        # Convert the column data to string type, ensuring consistent data type for manipulation.
                        df[target_column] = df[target_column].astype(str)
                        # Rename the column by removing a specified prefix (e.g., everything before and including ') ').
                        # This can be used to clean up column names or to adhere to a specific naming convention.
                        df.rename(columns={target_column: target_column.split(") ", 1)[1]}, inplace=True)

                    except IndexError as e:
                        # If the column name does not follow the expected pattern, catch the exception and skip it.
                        pass





        #---
        # (Calculate transcript length) 
        #---
        elif ttype == "transcript_length":
             
            # This block calculates the length of transcripts based on start and end positions provided in the DataFrame.
            # It is particularly useful in genomics data processing for measuring the length of gene transcripts.

            # Setup query parameters to retrieve any necessary filtering criteria, though specific filtering is not performed here.
            comparison_operator, filter_area, any_column = setup_query_parameters(details, df)

            # Define metadata including the titles of start, end, and result columns based on user input.
            metadata = {
                "start_column_title": filter_area,  # Column containing start positions of transcripts
                "end_column_title": details["target_column"],  # Column containing end positions of transcripts
                "new_column_title": details["target_value"]  # Column where the calculated transcript lengths will be stored
            }

            # Call 'tpm_transform' to perform the transcript length calculation.
            import tpm_transform
            df = tpm_transform.main("count_transcript_length", metadata, df, unfiltered_df)
            # 'unfiltered_df' may be passed to retain access to the original DataFrame before any transformations.
        


        #---
        # (Calculate TPM) 
        #---
        elif ttype == "calculate_tpm":
            # This block calculates Transcripts Per Million (TPM), a normalization method for RNA sequencing data.
            # TPM accounts for both the sequencing depth and gene length, allowing for comparison across samples.

            # Metadata preparation: Extract information from the user input on the columns to be used for TPM calculation.
            metadata = {
                "start_column_title": details["start_column"],  # Start position of the transcript
                "end_column_title": details["end_column"],  # End position of the transcript
                "counts_column": details["counts_column"]  # Column containing raw gene counts
            }

            # Import 'tpm_transform' designed to handle the calculation of TPM based on the provided metadata.
            # The module's 'main' function calculates TPM for each transcript and updates the DataFrame accordingly.
            import tpm_transform
            df = tpm_transform.main("calculate_tpm", metadata, df, unfiltered_df)
            # 'unfiltered_df' may be passed to retain access to the original DataFrame before any transformations.
        
        


        
    #Return the df after applying the different transformations   
    return df






#---
# FUNCTION: setup_query_parameters
# PURPOSE: Prepares the necessary parameters for filtering or transforming a DataFrame based on user-defined criteria.
# PARAMETERS:
#   forms - A dictionary containing the details of the user-defined query, including the area of the DataFrame to filter/transform, and the logical operation to apply.
#   df - The DataFrame to which the query will be applied.
# RETURNS: A tuple containing the comparison operator function, the target area of the DataFrame (columns) for the operation, and a flag indicating if any column can satisfy the condition (for filtering operations).
# NOTES:
#   - This function translates the logical operator provided by the user into a Python operator function that can be applied to the DataFrame.
#   - It determines the target columns for the operation based on user input, handling cases where the operation is to be applied to any column, all columns, or specific columns.
#   - The function supports dynamic column selection based on the presence of a target_table in the query, adjusting the target columns accordingly.
#---
def setup_query_parameters(forms, df):

    # Initialize the any_column flag to True, assuming that operations can apply to any column by default.
    any_column = True
    
    # Determine the area of the DataFrame to which the operation should apply based on user input.
    try:
        if "any column" in forms["filter_area"]:
            forms["filter_area"] = "any column"
        elif "all columns" in forms["filter_area"]:
            forms["filter_area"] = "all columns"
            any_column = False ## Set to False as the operation must apply to all columns specifically.
        else:
            # The operation applies to specific columns mentioned by the user, not any or all columns.
            any_column = False
    except:
        pass
    

    # Translate the user's logical operator into a Python operator function for later application.
    try:
        comparison_operator = COMPARISON_OPERATORS[forms["logical_operator"]]
    except KeyError:
        # If no comparison operator is explicity given, set it to "equal (=)"
        comparison_operator = operator.eq
    

    # Identify the target columns for the operation based on user specifications
    try:
        if "any column" in forms["filter_area"] or "all columns" in forms["filter_area"]:
            if comparison_operator == operator.eq:
                # If the operation applies to any or all columns and seeks equality, all columns are targeted.
                filter_area = list(df.columns)
            else:
                # Only columns with numeric values can be compared when the comparison operator is not equal (=).
                filter_area = list(df.select_dtypes(
                    include=[np.number]).columns)
        else:
             # The user has specified particular columns for the operation.
             filter_area = forms["filter_area"]
    except KeyError:
        
        # Handle cases where the user specifies a target table, adjusting target columns accordingly.
        try:
            prefix = '(' + forms["target_table"] + ') '
            try:
                # If there is a target_table, it'll search for columns that start with '(target_table) '
                filter_area = [col for col in list(df.columns) if col.startswith(prefix) and col != forms["target_column"]]
            except KeyError:
                filter_area = [col for col in list(
                    df.columns) if col.startswith(prefix)]
            any_column = False
        except KeyError:
            # Default to numeric columns if no specific area is determined.
            filter_area = list(df.select_dtypes(include=[np.number]).columns)
    
    # Return the prepared parameters for use in the query application process.
    return comparison_operator, filter_area, any_column





#---
# FUNCTION: filter_for
# PURPOSE: Generates a mask (boolean array) to filter a DataFrame based on the user-defined criteria specified in forms and properties.
# PARAMETERS:
#   forms: A dictionary containing the details of the filter criteria (e.g., value to filter by, columns to apply the filter).
#   properties: A dictionary specifying additional properties of the query, including the type of query (e.g., "expression" or "annotation_code").
#   df: The DataFrame on which the filter is to be applied.
#   comparison_operator: The Python operator function (e.g., operator.eq for equality) to use for comparison based on the logical operator specified by the user.
#   filter_area: The specific columns of the DataFrame to which the filter should be applied.
# RETURNS: A boolean mask array that can be used to filter the DataFrame. Each element in the array corresponds to a row in the DataFrame and indicates whether that row should be included (True) or excluded (False) based on the filter criteria.
# NOTES:
#   This function supports filtering based on numerical values, strings, and specific annotations. It can handle various logical operations (e.g., equals, not equals, greater than) and apply these to one or more specified columns.
#---
def filter_for(forms, properties, df, comparison_operator, filter_area):
    
    # Directly search for the entered string
    if properties["query"] == "expression":  
        # Handle direct string or numerical comparisons.

        try:  # Filter for integers and floats
            # Attempt to convert the filter value to a float for numerical comparison.
            if forms["filter_value"].lower() != "nan" or forms["filter_value"] == " ":
                filter_value = float(forms["filter_value"])
                # Generate a mask based on the comparison operation and the filter value.
                df_mask = comparison_operator(df[filter_area].values, filter_value)
            else:
                raise NameError
            # print('df_mask: ', df_mask)
        except ValueError:  # Filter for string or semi-colon-seperated list of strings
            if comparison_operator == operator.eq:
                filter_value = str(forms["filter_value"]).split('; ')
                df_mask = df[filter_area].isin(filter_value).values
            elif comparison_operator == operator.ne:
                filter_value = str(forms["filter_value"]).split('; ')
                df_mask = ~df[filter_area].isin(filter_value).values
        except NameError: # Handle cases where the filter value is intended to identify NaN values specifically.
            if forms["logical_operator"] == '= equal to':
                df_mask = pd.isna(df[filter_area].values)
            elif forms["logical_operator"] == '!= not':
                df_mask = pd.notna(df[filter_area].values)
            else:
                raise ValueError(
                    "Must use '= equal to' or '!= not' when searching for NaN values.")
    

    #This can potentially be removed??
    # Search for locus tag's that include the entered annotation id (GO, KEGG, COG, etc.)
    elif properties["query"] == "annotation_code":
        
        import json
        with open('static/gene_annotations.json') as json_file:
            gene_annotations = json.load(json_file)
        df_genes = df[filter_area].tolist()
        filter_value = []
        # print(properties["code_type"])
        for gene_locus in gene_annotations:
            if gene_locus in df_genes and forms["filter_annotation"] in list(gene_annotations[gene_locus][properties["code_type"]]):
                filter_value.append(gene_locus)
        df_mask = df[filter_area].isin(filter_value)
    
    

    # If the filter does not rely on a mask (e.g. dropping a column)
    else:  
        # Default case: no mask is generated.
        df_mask = None


    return df_mask
