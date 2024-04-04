import pandas as pd
import numpy as np
import operator


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


#each filter appies a mask to the df - the more filters there are, the more rounds the df is filtered by subsequent masks



#---
# FUNCTION: main
# PURPOSE: Serves as the primary entry point for applying a series of user-defined queries (filters, transformations, etc.) to a pandas DataFrame, enabling comprehensive data manipulation and analysis.
# PARAMETERS:
#   query: A structured list of dictionaries, each representing a specific query (or operation) to be applied to the DataFrame.
#   df: The pandas DataFrame containing the full dataframe, which the queries will be applied.
# RETURNS: The modified DataFrame after all queries have been applied.
# NOTES: This function orchestrates various data manipulation tasks such as filtering, replacing values, hiding columns, and more, based on the specifications contained within the query parameter.
#---

def main(query, df):
    # Initial print statement to check the state of the DataFrame before any operations.
    #print("Initial DataFrame:", df.head()) 
    
    #This is basically a check and is only true when queries have been added, 
    #then all of those queries have been removed. So there are no queries, but the df is still filtered based
    #upon the last filter. So this allows the full df to be reloaded
    # - if excluded, there are no search queries and thus the following for loop with throw an error 
    if len(query) == 0:
        return df #retun the unfiltered df
    else:
        #Continue with filtering

        # Create a copy of the original DataFrame to maintain the original data for reference or further use.
        unfiltered_df = df.copy()
        masks = [] #where all masks with be concatenated to
        logics = [] #store the logical operator (AND/OR) used to combine filter conditions.

        # import experimental_features
        # df = experimental_features.adjust_numeric_dtype(df) # This reduces the dataframe's size by around 50% but increases computation time by 30% and needs rounding due to lower FP precision

        # Loop through each query. Each 'sub_query' represents a set of conditions or operations to be applied to the DataFrame.
        for sub_query in query:

            # Loop through elements of the sub_query. Each 'block' represents an individual condition or operation.
            for i in range(len(sub_query)):
                block = sub_query[i]

                if block["properties"]["type"] != "logic":
                    # Extract comparison operator, area of the DataFrame to apply the filter, and any column flag.
                    comparison_operator, filter_area, any_column = setup_query_parameters(block["forms"], df)

                    # Generate a mask based on the filter condition described in 'block'.
                    df_mask = filter_for(block["forms"], block["properties"], unfiltered_df, comparison_operator, filter_area)

                    #append each mask to masks
                    masks.append(df_mask)
                    #useful for debugging to make sure each mark is being captured
                    #print(f"Appended mask for filter {i+1}. Current number of masks in list: {len(masks)}")
                else:

                    logics.append(block["forms"]["operator"])

                    
        # Reference to the first block in the sub-query, used for determining operation type. (AND/OR)
        block = sub_query[0] 
        block_type = block["properties"]["type"]

        
        #--
        # Apply different operations based on the block type specified in the sub-query.
        #--

        #Filter - which is most of the dropdown boxes below the search area containing lists of genes (GO, KEGG, manual gene lists etc)
        if block_type == "filter":
            #make sure there are more than 2 masks - which will require combining into a single mask 
            if len(masks) > 1:
                final_mask = apply_logics(masks, logics)
            else:
                #no masks, which means there is only a single search query and no AND/OR - so just take the first mask (T/F)
                final_mask = masks[0]
            df = unfiltered_df[final_mask]


        # Replace operation: modify values in the DataFrame based on the mask and target value.
        elif block_type == "replace":
            # If the operation is 'replace', attempt to convert the target value for replacement to float, falling back to string if conversion fails.
            try:
                target_value = float(block["forms"]["target_value"])
            except ValueError:
                target_value = str(block["forms"]["target_value"])

            # Replace values in the specified 'filter_area' of the DataFrame where the mask is False (i.e., condition not met) with 'target_value'.    
            df[filter_area] = df[filter_area].where(
                ~df_mask, other=target_value)
            # TO-DO fix numeric to string replacement

            # Iterate through each column in 'filter_area' to ensure data types are consistent, converting numeric columns to integers if possible.
            for column in filter_area:
                try:
                    # If all values of the target column are now numeric, try to change the dtype of that column to numeric
                    df[column] = pd.to_numeric(df[column], downcast="integer")
                except Exception:
                    df[column] = df[column].astype(str) # If conversion fails, ensure the column is treated as a string.


        # If the operation is 'hide', determine columns to be dropped from the DataFrame based on the user's selection ('all columns' or a specific list).
        elif block_type == "hide":
            if "all columns" in block["forms"]["target_column"]:
                target_area = list(df.columns) # Drop the specified columns from the DataFrame.
            else:
                target_area = block["forms"]["target_column"]
            df.drop(target_area, axis=1, inplace=True)


        # If the operation is 'logarithmic', apply a logarithmic transformation to the values in 'filter_area' based on a specified base.
        elif block_type == "logarithmic":
            # df[filter_area] = np.round(np.log(df[filter_area].values) / np.log(float(block["forms"]["log_value"])), 3) # NOTE: PERFORMANCE: Be careful with rounding when it comes to precision and performance. Maybe use pandas rounding function.
            df[filter_area] = np.log(
                df[filter_area].values) / np.log(float(block["forms"]["log_value"]))
            df.replace([np.inf, -np.inf], np.nan, inplace=True)  # Replace infinite values with NaN.


        # If the operation is 'fold_change', calculate the fold change between columns specified in 'filter_area' and a 'target_column'.
        elif block_type == "fold_change":
            # df[filter_area] = np.round(df[filter_area].div(df[block["forms"]["target_column"]].values,axis=0), 3) # NOTE: PERFORMANCE: Be careful with rounding when it comes to precision and performance. Maybe use pandas rounding function.
            df[filter_area] = df[filter_area].div(df[block["forms"]["target_column"]].values, axis=0)
            # Optional: Apply a logarithmic transformation to the fold change values for normalization.
            try:
                # For relative gene expression. NOTE: Dividing first and calculating the log AFTER might loose precision.
                # Alternative would be to calculate log(df) - log(target_column).
                # df[filter_area] = np.round(np.log(df[filter_area].values) / np.log(float(block["forms"]["log_value"])), 3) # NOTE: PERFORMANCE: Be careful with rounding when it comes to precision and performance. Maybe use pandas rounding function.
                df[filter_area] = np.log(
                    df[filter_area].values) / np.log(float(block["forms"]["log_value"]))
            except:
                pass
            # Remove base columns.
            df.drop(block["forms"]["target_column"], axis=1, inplace=True) # Optionally, remove the original 'target_column' used for comparison.
            df.replace([np.inf, -np.inf], np.nan, inplace=True) # Replace infinite values with NaN.
        

        # If the operation is 'round', round the values in the specified columns ('all columns' or a specific list) to a number of decimal places.
        elif block_type == "round":
            if "all columns" in block["forms"]["target_column"]:
                target_area = list(df.columns)
            else:
                target_area = block["forms"]["target_column"]
            df[target_area] = np.round(
                df[target_area], int(block["forms"]["round_value"]))
        

        # This block is specific to calculating the length of transcripts based on start and end positions specified in the metadata.
        elif block_type == "transcript_length":
            metadata = {
                "start_column_title": filter_area,
                "end_column_title": block["forms"]["target_column"],
                "new_column_title": block["forms"]["target_value"]
            }
            import transform_dataframe
            df = transform_dataframe.main("count_transcript_length", metadata, df, unfiltered_df)
        

        # If the operation is 'calculate_tpm', perform TPM (Transcripts Per Million) normalization using specified columns for counts and transcript lengths.
        elif block_type == "calculate_tpm":
            metadata = {
                "start_column_title": block["forms"]["start_column"],
                "end_column_title": block["forms"]["end_column"],
                "counts_column": block["forms"]["counts_column"]
            }
            import transform_dataframe
            df = transform_dataframe.main("calculate_tpm", metadata, df, unfiltered_df)


        # If the operation is 'convert_to_index', rename columns that match a certain pattern, effectively indexing them based on provided criteria.    
        elif block_type == "convert_to_index":
            if "all columns" in block["forms"]["target_column"]:
                target_area = list(df.columns)
            else:
                target_area = block["forms"]["target_column"]
            for target_column in target_area:
                if target_column.startswith("("):
                    try:
                        df[target_column] = df[target_column].astype(str) # Ensure the column is treated as a string.
                        # Rename the column by removing a specified prefix pattern, effectively re-indexing it.
                        df.rename(columns={target_column: target_column.split(") ", 1)[ 
                                1]}, inplace=True)
                    except IndexError as e:
                        pass
    
    
        # After all sub-queries have been processed, print the final state of the DataFrame.
        #print("Final DataFrame after all sub-queries:", df.head())
        return df





#---
# FUNCTION: setup_query_parameters
# PURPOSE: Extracts and prepares the parameters required for executing a filter operation on a DataFrame. This includes determining the appropriate comparison operator, identifying the target columns (filter area), and setting flags for column selection logic.
# PARAMETERS:
#   forms: A dictionary containing the details of the filter form submitted by the user, including selected comparison operators and target columns.
#   df: The pandas DataFrame on which the filter operation will be performed.
# RETURNS: A tuple containing the determined comparison operator, the list of target columns (filter area), and a boolean flag indicating whether any column can satisfy the filter condition.
# NOTES: Essential for translating user input into actionable parameters for DataFrame filtering, facilitating dynamic and customizable data analysis workflows.
#---

def setup_query_parameters(forms, df):
    # NOTE: This should be reworked. There should be at least 4 functions: 1 for "Filters", 1 for "Hide", 1 for "Transformation", 1 for "Replace"
    # If this is set to False, all columns must satisfy the filter value.
    any_column = True
    try:
        if "any column" in forms["filter_area"]:
            forms["filter_area"] = "any column"
        elif "all columns" in forms["filter_area"]:
            forms["filter_area"] = "all columns"
            any_column = False
        else:
            any_column = False
    except:
        pass
    try:
        comparison_operator = COMPARISON_OPERATORS[forms["logical_operator"]]
    except KeyError:
        # If no comparison operator is explicity given, set it to "equal (=)"
        comparison_operator = operator.eq
    try:
        if "any column" in forms["filter_area"] or "all columns" in forms["filter_area"]:
            if comparison_operator == operator.eq:
                filter_area = list(df.columns)
            else:
                # Only columns with numeric values can be compared when the comparison operator is not equal (=).
                filter_area = list(df.select_dtypes(
                    include=[np.number]).columns)
        else:
            filter_area = forms["filter_area"]
    except KeyError:
        try:
            string = '(' + forms["target_table"] + ') '
            try:
                # If there is a target_table, it'll search for columns that start with '(target_table) '
                filter_area = [col for col in list(df.columns) if col.startswith(
                    string) and col != forms["target_column"]]
            except KeyError:
                filter_area = [col for col in list(
                    df.columns) if col.startswith(string)]
            any_column = False
        except KeyError:
            filter_area = list(df.select_dtypes(include=[np.number]).columns)
    return comparison_operator, filter_area, any_column




#---
# FUNCTION: filter_for
# PURPOSE: Applies a specified filter to a DataFrame based on user-defined criteria, such as matching expression values or annotation codes. Supports diverse filtering strategies including exact matches, range queries, and annotation-based selection.
# PARAMETERS:
#   forms: A dictionary detailing the filter form including the filter value and, if applicable, annotation codes.
#   properties: A dictionary containing properties of the filter operation, such as the query type (e.g., 'expression', 'annotation_code').
#   df: The pandas DataFrame to be filtered.
#   comparison_operator: The Python operator function to use for comparison-based filtering.
#   filter_area: The columns of the DataFrame to which the filter should be applied.
# RETURNS: A mask (boolean array) indicating rows of the DataFrame that satisfy the filter criteria.
# NOTES: Central to enabling flexible and powerful data filtering within the DataFrame, accommodating a wide range of user-defined filtering logic.
#---

def filter_for(forms, properties, df, comparison_operator, filter_area):
    if properties["query"] == "expression":  # Directly search for the entered string
        try:  # Filter for integers and floats
            if forms["filter_value"].lower() != "nan" or forms["filter_value"] == " ":
                filter_value = float(forms["filter_value"])
                df_mask = comparison_operator(
                    df[filter_area].values, filter_value)
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
        except NameError:
            # numeric_columns = df.select_dtypes(include=np.number).columns.tolist()
            # print([filter_area])
            # if type(filter_area) != list:
            #     filter_area = [filter_area]
            # filter_area = [x for x in filter_area if x in numeric_columns]
            if forms["logical_operator"] == '= equal to':
                df_mask = pd.isna(df[filter_area].values)
            elif forms["logical_operator"] == '!= not':
                df_mask = pd.notna(df[filter_area].values)
            else:
                raise ValueError(
                    "Must use '= equal to' or '!= not' when searching for NaN values.")
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
    else:  # If the filter does not rely on a mask (e.g. dropping a column)
        df_mask = None
    return df_mask



#---
# FUNCTION: apply_logics
# PURPOSE: Generates a final list containing True/False values to use to subset the dataframe
# PARAMETERS:
#   masks: An array containing T/F masks for each query
#   logics: another dict containing the logic (AND/OR)
# RETURNS: A final mask of T/F taking into consideration the order of AND/OR that was applied
#---

def apply_logics(masks, logics):
    #not using this code, as can end up having differering sizes - esp. when removing queries
    # Ensure there's at least one mask and the number of logics is one less than the number of masks
    #assert len(masks) > 0 and len(logics) == len(masks) - 1, "Invalid input sizes."

    # Start with the first mask as the base for subsequent logical operations.
    # This is because we need an initial condition to start applying logical operations ("and", "or").
    result_mask = masks[0]

    # Iterate over each logical operator provided in the 'logics' list.
    # 'enumerate' is used here to get both the index and the value of each item in the list,
    # allowing us to access the corresponding masks by their index.
    for i, logic in enumerate(logics):
        # If the current logical operator is "or", combine the current result_mask with the next mask in the list using a logical OR operation.
        # np.logical_or performs a logical OR operation between two arrays element-wise.
        # This means for each position in the arrays, if either is True, the result at that position is True.
        if logic == "or":
            result_mask = np.logical_or(result_mask, masks[i + 1])
        
        # If the current logical operator is "and", combine the current result_mask with the next mask in the list using a logical AND operation.
        # np.logical_and performs a logical AND operation between two arrays element-wise.
        # This means for each position in the arrays, both must be True for the result at that position to be True.
        elif logic == "and":
            result_mask = np.logical_and(result_mask, masks[i + 1])
        
        # If an unsupported logical operator is encountered, raise an error.
        # This is a safety check to ensure only "and" and "or" operations are allowed.
        # It helps prevent unexpected behavior from incorrect input.
        else:
            raise ValueError(f"Unsupported logical operator: {logic}")

    # Return the final result_mask after applying all logical operations.
    # This mask can then be used to filter or select data from a DataFrame or array.
    return result_mask
