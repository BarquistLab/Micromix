# Experimental features


#---
# FUNCTION: adjust_numeric_dtype
# PURPOSE: Optimizes the data types of numeric columns in a pandas DataFrame to minimize memory usage. It converts numeric columns to the most memory-efficient types possible without losing information.
# PARAMETERS:
#   props: The pandas DataFrame whose numeric columns are to be optimized in terms of data type for memory efficiency.
# RETURNS: The DataFrame with optimized numeric data types.
# NOTES: This function is particularly useful in data processing pipelines where DataFrame memory footprint is a concern, such as with large datasets. It checks each numeric column to see if it can be safely converted to a smaller integer or float type and performs the conversion if so. Missing values are handled by temporarily filling them to ensure type conversions do not introduce errors.
#---
def adjust_numeric_dtype(props):
    # This function reduces memory usage by up to 75%.
    # It iterates over columns and adjusts their data types to the integer-format
    # with the lowest memory consumption.
    import pandas as pd
    import numpy as np
    # start_mem_usg = props.memory_usage().sum() / 1024**2 
    # print("Memory usage of properties dataframe is :",start_mem_usg," MB")
    NAlist = [] # Keeps track of columns that have missing values filled in. 
    for col in props.columns:
        if props[col].dtype != object:  # Exclude string columns to focus on numeric data.
            
            # Print current column type
            # print("******************************")
            # print("Column: ",col)
            # print("dtype before: ",props[col].dtype)
            # make variables for Int, max and min
            IsInt = False
            mx = props[col].max()
            mn = props[col].min()
            # Integer does not support NA, therefore, NA needs to be filled
            if not np.isfinite(props[col]).all(): 
                NAlist.append(col)
                props[col].fillna(mn-1,inplace=True)  
            
            # Test if column can be converted to an integer without loss of information
            asint = props[col].fillna(0).astype(np.int64)
            result = (props[col] - asint)
            result = result.sum()
            if result > -0.01 and result < 0.01:
                IsInt = True
            
            # Make Integer/unsigned Integer datatypes
            # Convert to the most memory-efficient integer type.
            if IsInt:
                if mn >= 0:   # Use unsigned integers if all values are non-negative.
                    if mx < 255:
                        props[col] = props[col].astype(np.uint8)
                    elif mx < 65535:
                        props[col] = props[col].astype(np.uint16)
                    elif mx < 4294967295:
                        props[col] = props[col].astype(np.uint32)
                    else:
                        props[col] = props[col].astype(np.uint64)
                else:
                    if mn > np.iinfo(np.int8).min and mx < np.iinfo(np.int8).max:
                        props[col] = props[col].astype(np.int8)
                    elif mn > np.iinfo(np.int16).min and mx < np.iinfo(np.int16).max:
                        props[col] = props[col].astype(np.int16)
                    elif mn > np.iinfo(np.int32).min and mx < np.iinfo(np.int32).max:
                        props[col] = props[col].astype(np.int32)
                    elif mn > np.iinfo(np.int64).min and mx < np.iinfo(np.int64).max:
                        props[col] = props[col].astype(np.int64)    
            # Make float datatypes 32 bit
            # else:
            #     props[col] = props[col].astype(np.float32)
            # Print new column type
            # print("dtype after: ",props[col].dtype)
            # print("******************************")
    # Print final result
    # print("___MEMORY USAGE AFTER COMPLETION:___")
    # mem_usg = props.memory_usage().sum() / 1024**2 
    # print("Memory usage is: ",mem_usg," MB")
    # print("This is ",100*mem_usg/start_mem_usg,"% of the initial size")
    # print("NAlist: ", NAlist)
    return props