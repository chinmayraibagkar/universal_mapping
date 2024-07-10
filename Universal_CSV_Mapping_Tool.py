import streamlit as st
import pandas as pd

st.header("Welcome to the CSV Mapper")

# Initialize session state variables if they don't exist
if 'df1' not in st.session_state:
    st.session_state.df1 = None
if 'df2' not in st.session_state:
    st.session_state.df2 = None
if 'mapped_sheet' not in st.session_state:
    st.session_state.mapped_sheet = None

# Create file uploaders in Streamlit
file1 = st.file_uploader("Choose a 1st CSV file", accept_multiple_files=False, type=['csv'])
file2 = st.file_uploader("Choose a 2nd CSV file", accept_multiple_files=False, type=['csv'])

if file1 is not None:
    try:
        # Try reading the file with the default encoding
        st.session_state.df1 = pd.read_csv(file1, encoding='latin-1')
    except UnicodeDecodeError:
        try:
            # If default encoding fails, try 'ISO-8859-1'
            st.session_state.df1 = pd.read_csv(file1, encoding='ISO-8859-1')
        except Exception as e:
            # If both attempts fail, show an error message
            st.error(f"Error reading {file1.name}: {e}")

if file2 is not None:
    try:
        # Try reading the file with the default encoding
        st.session_state.df2 = pd.read_csv(file2, encoding='latin-1')
    except UnicodeDecodeError:
        try:
            # If default encoding fails, try 'ISO-8859-1'
            st.session_state.df2 = pd.read_csv(file2, encoding='ISO-8859-1')
        except Exception as e:
            # If both attempts fail, show an error message
            st.error(f"Error reading {file2.name}: {e}")

if st.session_state.df1 is not None and st.session_state.df2 is not None:
    columns_to_map_from_sheet_1 = st.multiselect("Select columns to map from sheet 1", st.session_state.df1.columns, key="columns1")
    columns_to_map_from_sheet_2 = st.multiselect("Select columns to map from sheet 2", st.session_state.df2.columns, key="columns2")
    st.session_state.partial_match = st.checkbox("Allow partial match")

    if st.button("Map Sheets"):
        try:
            if st.session_state.partial_match:
                # Ensure columns are strings for partial matching
                for col1 in columns_to_map_from_sheet_1:
                    st.session_state.df1[col1] = st.session_state.df1[col1].astype(str)
                for col2 in columns_to_map_from_sheet_2:
                    st.session_state.df2[col2] = st.session_state.df2[col2].astype(str)

                # Create keys for matching
                st.session_state.df1['key1'] = st.session_state.df1[columns_to_map_from_sheet_1].agg(' '.join, axis=1)
                st.session_state.df2['key2'] = st.session_state.df2[columns_to_map_from_sheet_2].agg(' '.join, axis=1)

                # Perform partial match
                def partial_merge(df1, df2, key1, key2):
                    df1['merge_key'] = df1[key1].apply(lambda x: next((y for y in df2[key2] if x in y), None))
                    merged_df = df1.merge(df2, left_on='merge_key', right_on=key2, how='inner')
                    return merged_df.drop(columns=['merge_key'])

                st.session_state.mapped_sheet = partial_merge(st.session_state.df1, st.session_state.df2, 'key1', 'key2')

            else:
                # Ensure columns have the same data type before merging
                for col1, col2 in zip(columns_to_map_from_sheet_1, columns_to_map_from_sheet_2):
                    st.session_state.df1[col1] = st.session_state.df1[col1].astype(str)
                    st.session_state.df2[col2] = st.session_state.df2[col2].astype(str)

                st.session_state.df1['merge_key'] = st.session_state.df1[columns_to_map_from_sheet_1].agg('-'.join, axis=1)
                st.session_state.df2['merge_key'] = st.session_state.df2[columns_to_map_from_sheet_2].agg('-'.join, axis=1)

                st.session_state.mapped_sheet = pd.merge(st.session_state.df1, st.session_state.df2, how='inner', on='merge_key')

            st.dataframe(st.session_state.mapped_sheet)
        except Exception as e:
            st.error(f"Error during merging: {e}")

if st.session_state.mapped_sheet is not None:
    columns_to_keep = st.multiselect("Select columns to keep", st.session_state.mapped_sheet.columns, key="columns3")
    filtered_sheet = st.session_state.mapped_sheet[columns_to_keep]

    st.subheader("Pivot Table Functionality")

    if filtered_sheet is not None:
        pivot_index = st.multiselect("Pivot Table: Select index (rows)", filtered_sheet.columns)
        pivot_columns = st.multiselect("Pivot Table: Select columns", filtered_sheet.columns)
        pivot_values = st.multiselect("Pivot Table: Select values", filtered_sheet.columns)
        aggfunc = st.selectbox("Pivot Table: Select aggregation function", ['sum', 'mean', 'count', 'min', 'max'])

        if st.button("Generate Pivot Table"):
            if not pivot_index or not pivot_values:
                st.error("Please select at least one index and one value for the pivot table.")
            else:
                try:
                    pivot_table = pd.pivot_table(filtered_sheet, index=pivot_index, columns=pivot_columns, values=pivot_values, aggfunc=aggfunc)
                    st.dataframe(pivot_table)

                    csv2 = pivot_table.to_csv(index=False)
                    st.download_button(
                        label="Download pivoted data as CSV",
                        data=csv2,
                        file_name='custom_pivot_data.csv',
                        mime='text/csv',
                    )
                except Exception as e:
                    st.error(f"Error generating pivot table: {e}")

    st.dataframe(filtered_sheet)
    csv1 = filtered_sheet.to_csv(index=False)
    st.download_button(
        label="Download Mapped Data as CSV",
        data=csv1,
        file_name='custom_mapped_data.csv',
        mime='text/csv',
    )

