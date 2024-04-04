import pandas as pd
import numpy as np
import operator
import pprint



#---
# FUNCTION: row_filters
# PURPOSE:  Applies rowfilters to a passed df. 
#           These filters can be based on numerical values, string values, or both, and affect either specific columns, 
#           any column, or all columns within the DataFrame. Each filter's logic is determined by the user's input, 
#           which dictates how rows are filtered (e.g., rows where column values are greater than, less than, equal to, 
#           or not equal to the specified filter value)
#---
def row_filters(query, filtered_df, all_filters):

    # Iterate over each row filter and apply in sequential order
    for i in range(len(all_filters)):
    
        # Extract filter parameters: value, logic operator, and target columns
        filter_input_value = all_filters[i]["forms"]["filter_value"]
        filter_logic = all_filters[i]["forms"]["logical_operator"]
        filter_columns = all_filters[i]["forms"]["filter_area"]

        # Convert input to numeric if possible, otherwise keep as string
        try:
            numeric_value = float(filter_input_value)
            is_numeric = True
        except ValueError:
            numeric_value = filter_input_value
            is_numeric = False


        # Enforce specific logic operators for string filters
        if not is_numeric and filter_logic not in ['= equal to', '!= not']:
            raise ValueError("String filters must use '= equal to' or '!= not'.")
    
        
        # Determine the columns to filter based on user imput: all, any, or specified columns
        if "all columns" in filter_columns or "any column" in filter_columns:
            cols_to_filter = filtered_df.select_dtypes(include=[np.number if is_numeric else object]).columns
        else:
            cols_to_filter = filter_columns

        
        # Initialize the mask based on column selection criteria
        if "all columns" in filter_columns:
            mask = pd.Series([True] * len(filtered_df), index=filtered_df.index)
        else:  # Default to False for any_columns or specific column selections
            mask = pd.Series([False] * len(filtered_df), index=filtered_df.index)

        

        # Apply filter logic to selected columns
        for col in cols_to_filter:
            if is_numeric:
                current_col_mask = apply_numeric_filter(filtered_df[col], filter_logic, numeric_value) #numeric
            else:
                current_col_mask = apply_string_filter(filtered_df[col], filter_logic, numeric_value) #string
        

            # Update the composite mask based on the current column's mask
            if "all columns" in filter_columns:
                # Require all conditions to be met (AND)
                mask &= current_col_mask
            else:  # Applies to "any_columns" and specific column selections
                # Only one condition needs to be met (OR)
                mask |= current_col_mask


        # Apply the composite mask to the DataFrame to filter rows
        filtered_df = filtered_df[mask]
        #print("filtered_df")
        #pprint.pprint(filtered_df)

    #Display the filtered DataFrame
    #print(filtered_df)

    return filtered_df
    


#---
# FUNCTION: apply_numeric_filter
# PURPOSE:  Apply numeric filter based on the provided logic
#---
def apply_numeric_filter(col_series, logic, value):
    # Apply numeric filter based on the provided logic
    if logic == '> more than':
        return col_series > value
    elif logic == '>= more or equal to':
        return col_series >= value
    elif logic == '< less than':
        return col_series < value
    elif logic == '<= less or equal to':
        return col_series <= value
    elif logic == '= equal to':
        return col_series == value
    elif logic == '!= not':
        return col_series != value


#---
# FUNCTION: apply_string_filter
# PURPOSE:  Apply string filter based on the provided logic
#---
def apply_string_filter(col_series, logic, value):
    # Apply string filter based on the provided logic
    if logic == '= equal to':
        return col_series == value
    elif logic == '!= not':
        return col_series != value
    