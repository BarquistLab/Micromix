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
# FUNCTION: filter_genelists
# PURPOSE: Applies a series of filtering conditions defined in 'query' to a given DataFrame 'df2'. These conditions can include both filtering criteria and logical operators (AND/OR) to combine these criteria. The function is primarily used for filtering rows based on gene list criteria.
# PARAMETERS:
#   query - A structured list of dictionaries, each representing a specific filtering condition or logical operator to be applied to the DataFrame.
#   df2 - The DataFrame to which the filtering conditions will be applied. It is assumed that any necessary transformations have already been applied to this DataFrame.
# RETURNS: A modified DataFrame 'df3' that has been filtered according to the specified criteria in 'query' and any duplicates removed.
# NOTES:
#   - The function processes each condition (block) within each query, generating masks for filtering and collecting logical operators for combining these masks.
#   - After generating all necessary masks and logical operators, the function applies these to filter the DataFrame, taking care to handle the combination of masks according to the specified logic.
#   - It also handles duplicate rows that may result from filtering across multiple columns, ensuring the final DataFrame does not contain duplicates.
#---
def filter_genelists(query, df2):
    

    masks = []  # List to store boolean masks for each filter condition
    logics = []  # List to store logical operators (AND/OR) for combining filters
    block_types = []  # List to store the types of blocks encountered (e.g., filter, logic)


    # Loop through each query. 
    #Each 'sub_query' represents a set of conditions or operations to be applied to the DataFrame.
    for sub_query in query:

            # Variable to store the logical operator (AND/OR) used to combine filter conditions.
            logical_operator = ""

            # Loop through elements of the sub_query. Each 'block' represents an individual condition or operation.
            for i in range(len(sub_query)):
                block = sub_query[i]

                # dont want to capture filter values just yet 
                # this is done after the df has been filtered with the masks
                if block['name'] != 'Filter values':
                
                    #store all the block types, so can look into the filters below 
                    block_types.append(block["properties"]["type"])

                    
                    # Process filter blocks to generate masks
                    # loop through the queries and if logic, append to logic blocks
                    # Not interested in any of the transformations, as these have been applied earlier
                    if block["properties"]["type"] == "filter":
                        
                        # Extract comparison operator, area of the DataFrame to apply the filter, and any column flag.
                        comparison_operator, filter_area, any_column = setup_query_parameters(block["forms"], df2)
 
                        # Generate a mask based on the filter condition described in 'block'.
                        df_mask = filter_for(block["forms"], block["properties"], df2, comparison_operator, filter_area)

                        #Append to masks
                        masks.append(df_mask) 
                        #print(f"Appended mask for filter {i+1}. Current number of masks in list: {len(masks)}")
 
                    
                    # Is a logic block
                    elif block["properties"]["type"] == "logic":
                        # Collect logical operators for combining masks
                        logics.append(block["forms"]["operator"])





    #All masks have been created - the following code applies the masks to the df

    #Look at filters within block_type
    if "filter" in block_types:

        #print("len(logics) = ",len(logics))
        #print("len(masks) = ",len(masks))
        
        #Basically, if there is only one mask, that should be applied.
        #If more that one mask, then logic (AND/OR) will need to be applied (apply_logics)
        if len(masks) > 1:
            final_mask = apply_logics(masks, logics) 
        else:
            # Use the single mask directly if only one exists
            final_mask = masks[0]


        #The drop duplicates() part is important, because if multiple columns are searched, then the mask
        #will return duplicate entries, particularly if the searched value can appear across multiple columns.
        #When searching for != and across many columns, hundreds of thousands of rows are returned and the page
        #becomes unresponsive. For now this works fine, but if wanting to optimise this in future versions, the way
        #masks are applied could be refined to avoid additional rows being added.

        # Apply the final mask to df2 and remove duplicates
        df3 = df2[final_mask].drop_duplicates()


        # Debugging: Print the size of the DataFrame after applying the filter.
        #print("DataFrame after filter:", df3.shape) 
 

        return df3










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
def setup_query_parameters(forms, df2):
    
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
                filter_area = list(df2.columns)
            else:
                # Only columns with numeric values can be compared when the comparison operator is not equal (=).
                filter_area = list(df2.select_dtypes(include=[np.number]).columns)
        else:
            # The user has specified particular columns for the operation.
            filter_area = forms["filter_area"]
    except KeyError:
        
        # Handle cases where the user specifies a target table, adjusting target columns accordingly.
        try:
            prefix = '(' + forms["target_table"] + ') '
            try:
                # If there is a target_table, it'll search for columns that start with '(target_table) '
                filter_area = [col for col in list(df2.columns) if col.startswith(
                    prefix) and col != forms["target_column"]]
            except KeyError:
                filter_area = [col for col in list(
                    df2.columns) if col.startswith(prefix)]
            any_column = False
        except KeyError:
            # Default to numeric columns if no specific area is determined.
            filter_area = list(df2.select_dtypes(include=[np.number]).columns)
    
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
def filter_for(forms, properties, df2, comparison_operator, filter_area):
    
    
    #print("properties--query:: ",properties["query"]) 
    #The above print shows the key info we are wanting to capture: properties["query"]
    #Under filtering for genelists, we are only interested in values of "expression" and "annotation_code"

    #expression=related to filtering - includess ncRNAs genesets, and also filtering for row-values
    #GO and KEGG, and also PULs etc = annotation_code --> things that link up to the json files

    #remove column = no value
    #round = no value
    #change values = no value
    #calculations, such as log = no value
    
    #The below code only searches for expression and annotation code - which are linked to genelists

    


    #---
    #Identify what query is being passed
    #---

    #Expression = "filter" and "ncRNAs"
    if properties["query"] == "expression":
        
        # Initialize a default mask with all False values for the length of the DataFrame
        # For "all columns", start with True since we're using an AND logic
        if "all columns" in forms["filter_area"]:
            df_mask = pd.Series([True] * len(df2), index=df2.index)
            logic = 'and'
        else:
            df_mask = pd.Series([False] * len(df2), index=df2.index)
            logic = 'or'

        #there are two possibilities here: filtering for gene lists, or user specified query that can contain numerical values
        #check if numerical or string
        #print("forms[filter-value]:: ",forms["filter_value"])


        # Attempt to convert the filter value to a float. 
        # This is done to determine if we are working with numeric filtering.
        # Check for an integer, or nan or empty
        try:  
            if forms["filter_value"].lower() != "nan" or forms["filter_value"] == " ":
                filter_value = float(forms["filter_value"])
                #The value is numeric - so apply

                for column in filter_area:
                # Skip non-numeric columns for numeric filters
                    if df2[column].dtype.kind in 'biufc':
                        column_mask = comparison_operator(df2[column], filter_value)
                        if logic == 'and':
                            df_mask &= column_mask
                        else:
                            df_mask |= column_mask
                    else:
                        print(f"Column {column} is not numeric. Skipping...")

            else:
                # This block handles cases where filter_value is explicitly 'nan' or an empty string,

                # Use the logical operator provided in forms to decide the type of NaN filtering.
                # create a mask for NaN values in filter_area columns
                if forms["logical_operator"] == '= equal to':
                    df_mask = pd.isna(df2[filter_area].values)
                elif forms["logical_operator"] == '!= not':
                    df_mask = pd.notna(df2[filter_area].values)
                else:
                    raise ValueError("Must use '= equal to' or '!= not' when searching for NaN values.")
        

        # Filter for string or semi-colon-seperated list of strings
        except ValueError:  
            #if string/s =
            if comparison_operator == operator.eq:
                # If filtering for equality, split the filter_value by semicolons to support multiple string values.
                filter_value = str(forms["filter_value"]).split('; ')
                #print("filter value len", len(filter_value))
                
                #NOTE:
                #The challenge here is when there are multiple columns selected, the mask is applied to multiple columns.
                #Say a locus tag is being searched for (string), then if two columns match, twice the rows are returned.
                #Same as not=, you end up getting lots of rows returned. 
                #So, need to loop over all the columns and create separate masks, then combine at the end
                #it doesnt matter if the len of filter_value > 1 or not - its about the matching columns
                #only really applies if any_columns or all_columns are selected
                #This was fixed by dropping duplicate rows above:  df3 = df2[final_mask].drop_duplicates()

                # Create a mask where each row in filter_area columns matches any of the values in filter_value
                df_mask = df2[filter_area].isin(filter_value).values
            #if string/s !=
            elif comparison_operator == operator.ne:
                # Similarly for not equal, split and create a mask for values not in filter_value.
                filter_value = str(forms["filter_value"]).split('; ')
                df_mask = ~df2[filter_area].isin(filter_value).values
            else:
                raise ValueError("When searching for a string, you can only use '= equal to' or '!= not equal to'")





    #Anything that requires looking within the json annotation file - KEGG, GO etc
    elif properties["query"] == "annotation_code":

        import json
        #open annotation file
        with open('static/gene_annotations.json') as json_file:
            gene_annotations = json.load(json_file)
        df_genes = df2[filter_area].tolist()
        filter_value = []
        # print(properties["code_type"])
        for gene_locus in gene_annotations:
            if gene_locus in df_genes and forms["filter_annotation"] in list(gene_annotations[gene_locus][properties["code_type"]]):
                filter_value.append(gene_locus)
        #create mask
        df_mask = df2[filter_area].isin(filter_value) #filter_value = user entered 


    
    # Return a unique set of rows based on the final mask to avoid duplicates
    return df_mask











#---
# FUNCTION: apply_logics
# PURPOSE: Combines multiple boolean masks (filters) using logical operators (AND/OR) specified in the 'logics' list to create a single composite mask. This composite mask can be used to filter a DataFrame based on combined criteria.
# PARAMETERS:
#   masks - A list of boolean masks, where each mask corresponds to a set of filtering conditions applied to the DataFrame. Each element in a mask is True if the row meets the condition, and False otherwise.
#   logics - A list of logical operators ("or", "and") corresponding to how the masks should be combined. The length of 'logics' should be one less than the length of 'masks' since each operator is applied between two masks.
# RETURNS: A single boolean mask resulting from the combination of the input masks according to the specified logical operators. This mask can be applied to a DataFrame to filter rows that meet the combined conditions.
# NOTES:
#   - The function starts with the first mask as the base and iteratively applies each subsequent mask using the corresponding logical operator.
#   - It handles edge cases, such as when there are no masks provided or only a single mask is available, by returning the appropriate mask without applying logical operations.
#   - The function ensures the list of logical operators is appropriately sized to match the number of operations needed between masks, adjusting if necessary.
#---
def apply_logics(masks, logics):


    #Debugging
    #print(f"Number of masks: {len(masks)}")
    #print(f"Number of logics: {len(logics)}")
    #print("Masks:", [str(mask)[:50] + "..." for mask in masks])  # Print shortened versions of masks for readability
    #print("Logics:", logics)
    

    # Handle the case where there's only one mask (or none).
    #probably unnecessary as the loop to get into this function checks for the same thing
    if len(masks) == 0:
        raise ValueError("No masks to apply logics to.")
    elif len(masks) == 1:
        # Only one mask available, return it as no logical operation is needed.
        return masks[0]



    # If there are not enough masks to apply each logic, adjust logics to match the number of mask pairs.
    # This happens when users remove queries, the AND/OR part stays.
    # NOTE: in future versions, this really should be optimised
    if len(logics) >= len(masks):
        logics = logics[:len(masks)-1]
        #print("Adjusted Logics:", logics)

    
    
    # Start with the first mask.
    result_mask = masks[0]
    # Apply each logic to combine the current result with the next mask.
    for i, logic in enumerate(logics):
        if logic == "or":
            # Combine using logical OR.
            result_mask = np.logical_or(result_mask, masks[i + 1])
        elif logic == "and":
            # Combine using logical AND.
            result_mask = np.logical_and(result_mask, masks[i + 1])
        else:
            raise ValueError(f"Unsupported logical operator: {logic}")
    
    # Return the composite mask after applying all logical operations.
    return result_mask