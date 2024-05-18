import streamlit as st
import pandas as pd
import numpy as np
import altair as alt



def normalize_value(value):
    """
    Converts a string representation of a number with potential suffixes ('k', 'M', 'B')
    to an integer.
    """
    if isinstance(value, str):
        if 'k' in value:
            return int(float(value.replace('k', '')) * 1e3)
        elif 'M' in value:
            return int(float(value.replace('M', '')) * 1e6)
        elif 'B' in value:
            return int(float(value.replace('B', '')) * 1e9)
        else:
            return int(value)
    return value

@st.cache_data
def prepare_data():
    population_df = pd.read_csv("pop.csv")
    life_expectancy_df = pd.read_csv("lex.csv")
    gni_df = pd.read_csv("ny_gnp_pcap_pp_cd.csv")

    # population
    # Set 'country' as the index to avoid filling it
    population_df.set_index('country', inplace=True)

    # Apply forward and backward fill across each row
    population_df = population_df.apply(lambda row: row.ffill().bfill(), axis=1)

    # Reset the index to restore the original DataFrame structure
    population_df.reset_index(inplace=True)

    # Set 'country' as the index to avoid filling it
    life_expectancy_df.set_index('country', inplace=True)

    # Apply forward and backward fill across each row
    life_expectancy_df = life_expectancy_df.apply(lambda row: row.ffill().bfill(), axis=1)

    # Reset the index to restore the original DataFrame structure
    life_expectancy_df.reset_index(inplace=True)

        # Set 'country' as the index to avoid filling it
    gni_df.set_index('country', inplace=True)

    # Apply forward and backward fill across each row
    gni_df = gni_df.apply(lambda row: row.ffill().bfill(), axis=1)

    # Reset the index to restore the original DataFrame structure
    gni_df.reset_index(inplace=True)

    # Transform population data
    population_tidy = population_df.melt(id_vars=['country'], var_name='year', value_name='population')

    # Transform life expectancy data
    life_expectancy_tidy = life_expectancy_df.melt(id_vars=['country'], var_name='year', value_name='life_expectancy')

    # Transform GNI per capita data
    gni_per_capita_tidy = gni_df.melt(id_vars=['country'], var_name='year', value_name='gni_per_capita')

    merged_df = (population_tidy
                .merge(life_expectancy_tidy, on=['country','year'], how='outer')
                .merge(gni_per_capita_tidy, on=['country','year'], how='outer'))

    for column in ['population', 'gni_per_capita']:
        merged_df[column] = merged_df[column].apply(normalize_value)

    merged_df['gni_per_capita'] = merged_df['gni_per_capita'].replace(0, np.nan)  # Replace zeros with NaN to avoid log(0)
    merged_df['gni_per_capita'] = np.log(merged_df['gni_per_capita']) 

    merged_df['year'] = merged_df['year'].astype(int)

    return merged_df


st.title('Gapminder')

st.write("Unlocking Lifetimes: Visualizing Progress in Longevity and Poverty Eradication")


# Create chart
df = prepare_data()

# Sidebar widgets
st.sidebar.header('Filter Data')
selected_year = st.sidebar.slider('Select Year', min_value=int(df['year'].min()), max_value=int(df['year'].max()),max_value=int(df['year'].max()))
selected_countries = st.sidebar.multiselect('Select Countries', df['country'].unique(),default=["Germany","Croatia"])

# Filter dataframe based on selected year and countries
filtered_df = df[(df['year'] == selected_year) & (df['country'].isin(selected_countries))]

# Create Altair chart
chart = alt.Chart(filtered_df).mark_circle().encode(
    x='GNI',
    y='Life Expectancy',
    size='Population',
    color='Country',
    tooltip=['country', 'year', 'population', 'life_expectancy', 'gni_per_capita']
).properties(
    width=800,
    height=500
).interactive()

# Show the chart
st.altair_chart(chart, use_container_width=True)