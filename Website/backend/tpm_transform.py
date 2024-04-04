import pandas as pd # NOTE: Maybe unnecessary? No np. references.

def main(transformation_type, metadata, df, unfiltered_df):
    df_transformed = TRANSFORMATION_FUNCTIONS[transformation_type](metadata, df, unfiltered_df)
    return df_transformed

def count_transcript_length(metadata, df, unfiltered_df):
    df[metadata["new_column_title"]] = (df[metadata["end_column_title"]] - df[metadata["start_column_title"]]) + 1
    return df

def calculate_tpm(metadata, df, unfiltered_df):
    transcript_length = df[metadata["end_column_title"]] - df[metadata["start_column_title"]]
    import numpy as np
    args = {metadata["counts_column"] : df[metadata["counts_column"]] / transcript_length * (1 / (unfiltered_df[metadata["counts_column"]].sum()) * (df[metadata["counts_column"]] / transcript_length)) * 1e6}
    df = df.assign(**args)
    df.rename(columns={metadata["counts_column"]: "TPM "+metadata["counts_column"]}, inplace=True)
    return df

TRANSFORMATION_FUNCTIONS = {
    # "relative_expression": relative_expression,
    "count_transcript_length": count_transcript_length,
    "calculate_tpm": calculate_tpm
}