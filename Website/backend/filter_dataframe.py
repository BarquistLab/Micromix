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
# FUNCTION: calculate_gated_mask
# PURPOSE: Generates a final composite mask for a DataFrame based on multiple individual condition masks and a logical gate (AND/OR logic). This allows for complex filtering logic across several conditions.
# PARAMETERS:
#   mask_length: Integer indicating the length of the masks to be combined.
#   masks: List of individual condition masks (boolean arrays) to be combined using logical gate.
#   df_mask_length: Integer indicating the length of the DataFrame mask to be generated.
#   target_boolean: Boolean value (True or False) indicating the target condition for the mask combination logic (True for OR logic, False for AND logic).
# RETURNS: A boolean array (mask) that represents the combined condition evaluation across all provided masks.
# NOTES: This function is crucial for implementing complex query logic on DataFrames, enabling more sophisticated data filtering and analysis operations.
#---

# This function calculates a final gated mask for the DataFrame based on multiple condition masks and a target boolean value.
# It's used to apply complex filter logic (like "AND" or "OR") across multiple conditions.
def calculate_gated_mask(mask_length, masks, df_mask_length, target_boolean):
    # Initialize a default mask for the DataFrame with the specified length.
    # All values are initially set to False
    df_mask = [False] * df_mask_length
    
    # Iterate through each position in the mask (corresponding to DataFrame rows).
    for i in range(mask_length):
        # For each row, iterate through all condition masks to check their criteria.
        for j in range(len(masks)):
            # If the current condition mask at row 'i' matches the target_boolean (indicating a match for the condition),
            # set the final mask at 'i' to match the target_boolean (True for inclusion, False for exclusion)
            # and stop checking further conditions for this row (because one match is sufficient for "OR" logic).
            if masks[j][i] == target_boolean:
                df_mask[i] = target_boolean
                break
            # If the current condition mask at row 'i' does not match the target_boolean,
            # set the final mask at 'i' to the opposite of the target_boolean. This is crucial for "AND" logic,
            # where a non-match in any condition should lead to exclusion but is conditionally used based on logic implementation.
            else:
                df_mask[i] = not target_boolean
                
    # After evaluating all conditions for all rows, return the final composite mask.
    # This mask can then be used to filter the DataFrame, keeping rows that meet the combined condition(s).
    return df_mask





#---
# FUNCTION: main
# PURPOSE: Serves as the primary entry point for applying a series of user-defined queries (filters, transformations, etc.) to a pandas DataFrame, enabling comprehensive data manipulation and analysis.
# PARAMETERS:
#   query: A structured list of dictionaries, each representing a specific query (or operation) to be applied to the DataFrame.
#   df: The pandas DataFrame to which the queries will be applied.
# RETURNS: The modified DataFrame after all queries have been applied.
# NOTES: This function orchestrates the application of various data manipulation tasks such as filtering, replacing values, hiding columns, and more, based on the specifications contained within the query parameter.
#---

def main(query, df):
    # Initial print statement to check the state of the DataFrame before any operations.
    print("Initial DataFrame:", df.head())  # Display first few rows for a quick overview
    
    # Create a copy of the original DataFrame to maintain the original data for reference or further use.
    unfiltered_df = df.copy()
    # import experimental_features
    # df = experimental_features.adjust_numeric_dtype(df) # This reduces the dataframe's size by around 50% but increases computation time by 30% and needs rounding due to lower FP precision
    

    # Loop through each query. Each 'sub_query' represents a set of conditions or operations to be applied to the DataFrame.
    for sub_query in query:
        print("Processing sub-query:", sub_query) # Debug print to indicate which sub-query is being processed.
        masks = []  # Initialize an empty list to store masks generated by filter conditions within this sub-query.
        logical_operator = ""  # Variable to store the logical operator (AND/OR) used to combine filter conditions.

        # Loop through elements of the sub_query. Each 'block' represents an individual condition or operation.
        for i in range(len(sub_query)):
            block = sub_query[i]

            # Check if the block is a filter condition (as opposed to a logical operator like AND/OR).
            if block["properties"]["type"] != "logic":
                # Extract comparison operator, area of the DataFrame to apply the filter, and any column flag.
                comparison_operator, filter_area, any_column = setup_query_parameters(block["forms"], df)

                # Generate a mask based on the filter condition described in 'block'.
                df_mask = filter_for(block["forms"], block["properties"], df, comparison_operator, filter_area)
                
                # Attempt to handle masks that cover multiple columns.
                # If the mask_area is larger than one column, we need to convert the mask from a 2D array to a 1D list.
                try:
                    if df_mask.shape[1] > 1:
                        # Maybe bad. This converts the df_mask to a python list, only in certain circumstances. Replacing values in the 2D array isn't easy otherwise.
                        df_mask = list(df_mask)
                        # Modify mask based on 'any_column' flag, to indicate inclusion/exclusion in the filter.
                        for j in range(len(df_mask)):
                            if any_column in df_mask[j]:
                                df_mask[j] = any_column
                            else:
                                df_mask[j] = not any_column
                except Exception as e:
                    print(e) # Print any exceptions for debugging.
                    pass
                
                # Append the generated mask to the list of masks for this sub-query.
                masks.append(df_mask)
            else:
                # If the block represents a logical operation, store its type (AND/OR).
                logical_operator = block["forms"]["operator"]

        
        # After processing all blocks in the sub-query, combine the masks based on the logical operator.
        if logical_operator == "or":

             # For OR logic, combine masks so that a row is included if it matches any condition.
             df_mask = calculate_gated_mask(len(df_mask), masks, len(df_mask), True)
        elif logical_operator == "and":
             # For AND logic, combine masks so that a row is included only if it matches all conditions.
             df_mask = calculate_gated_mask(len(df_mask), masks, len(df_mask), False)
        

        # Apply the final combined mask to the DataFrame, or perform other operations based on the block type.
        block = sub_query[0] # Reference to the first block in the sub-query, used for determining operation type.
        block_type = block["properties"]["type"]
        

        # Apply different operations based on the block type specified in the sub-query.
        if block_type == "filter":
            # Apply the filter to the DataFrame.
            # If the operation is 'filter', apply the previously calculated mask to the DataFrame to retain rows that match the filter criteria.
            df = df[df_mask]
            print("DataFrame after filter:", df.head()) # Debugging: Print the first few rows of the DataFrame after applying the filter.

        
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
    print("Final DataFrame after all sub-queries:", df.head())
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
