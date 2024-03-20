import pandas as pd # NOTE: Maybe unnecessary? No np. references.

#---
# FUNCTION: main
# PURPOSE: Serves as the entry point for applying specified transformations to DataFrame data, based on transformation type and provided metadata.
# PARAMETERS:
#   transformation_type: A string key representing the transformation to be applied.
#   metadata: A dictionary containing metadata that specifies how transformations should be applied, including necessary column titles.
#   df: The DataFrame to be transformed.
#   unfiltered_df: A secondary DataFrame that might be used for transformations requiring a comparison or baseline data.
# RETURNS: The transformed DataFrame.
# NOTES: This function delegates the transformation work to specific functions mapped by the TRANSFORMATION_FUNCTIONS dictionary.
#---
def main(transformation_type, metadata, df, unfiltered_df):
    df_transformed = TRANSFORMATION_FUNCTIONS[transformation_type](metadata, df, unfiltered_df)
    return df_transformed


#---
# FUNCTION: count_transcript_length
# PURPOSE: Calculates the length of transcripts based on start and end columns in the DataFrame and adds this information as a new column.
# PARAMETERS:
#   metadata: Metadata specifying the column titles to be used for calculation.
#   df: The DataFrame containing the transcript start and end positions.
#   unfiltered_df: Not used in this function but included for consistency with the transformation function signature.
# RETURNS: The DataFrame with an added column showing the calculated transcript lengths.
# NOTES: This function is an example of a simple transformation applied to biological data.
#---
def count_transcript_length(metadata, df, unfiltered_df):
    df[metadata["new_column_title"]] = (df[metadata["end_column_title"]] - df[metadata["start_column_title"]]) + 1
    return df

#---
# FUNCTION: calculate_tpm
# PURPOSE: Calculates Transcripts Per Million (TPM) for RNA sequencing data in the DataFrame and renames the counts column to reflect TPM values.
# PARAMETERS:
#   metadata: Metadata specifying the columns to be used in the calculation.
#   df: The DataFrame containing gene expression counts and transcript start and end positions.
#   unfiltered_df: A DataFrame used to calculate the total counts across all samples, necessary for the TPM calculation.
# RETURNS: The DataFrame with the counts column transformed into TPM values.
# NOTES: This transformation is crucial for normalizing RNA sequencing data, making it comparable across samples.
#---
def calculate_tpm(metadata, df, unfiltered_df):
    transcript_length = df[metadata["end_column_title"]] - df[metadata["start_column_title"]]
    import numpy as np
    # Calculate TPM following the formula and update the DataFrame.
    args = {metadata["counts_column"] : df[metadata["counts_column"]] / transcript_length * (1 / (unfiltered_df[metadata["counts_column"]].sum()) * (df[metadata["counts_column"]] / transcript_length)) * 1e6}
    df = df.assign(**args)
    df.rename(columns={metadata["counts_column"]: "TPM "+metadata["counts_column"]}, inplace=True)
    return df


TRANSFORMATION_FUNCTIONS = {
    # A dictionary mapping transformation type strings to their corresponding function implementations.
    
    # "relative_expression": relative_expression,
    "count_transcript_length": count_transcript_length,
    "calculate_tpm": calculate_tpm
}