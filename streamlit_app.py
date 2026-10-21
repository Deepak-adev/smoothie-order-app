
import streamlit as st
import pandas as pd
import requests
from snowflake.snowpark.functions import col

# App title
st.title("🥤 Custom Smoothie Order")
st.write("Create your smoothie and explore fruit nutrition!")

# Connect to Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# Load fruit options and search terms
my_dataframe = session.table(
    "SMOOTHIES.PUBLIC.FRUIT_OPTIONS"
).select(
    col("FRUIT_NAME"),
    col("SEARCH_ON")
)

pd_df = my_dataframe.to_pandas()

# Customer name
name_on_order = st.text_input("Name on smoothie order:")

# Fruit selection
fruit_list = pd_df["FRUIT_NAME"].tolist()

ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    options=fruit_list,
    max_selections=5
)

# Build the ingredients string and display nutrition data
ingredients_string = ""

for fruit_chosen in ingredients_list:
    ingredients_string += fruit_chosen

    search_on = pd_df.loc[
        pd_df["FRUIT_NAME"] == fruit_chosen,
        "SEARCH_ON"
    ].iloc[0]

    st.caption(f"API search term for {fruit_chosen}: {search_on}")

    try:
        response = requests.get(
            f"https://my.smoothiefroot.com/api/fruit/"
            f"{requests.utils.quote(search_on, safe='')}",
            timeout=10
        )

        if response.status_code == 200:
            fruit_data = response.json()
            st.write(f"Nutrition information for {fruit_chosen}")
            st.json(fruit_data)
        else:
            st.info(
                f"No nutrition data found for {fruit_chosen} "
                f"(HTTP {response.status_code})."
            )

    except requests.RequestException:
        st.info(f"Could not retrieve API data for {fruit_chosen}.")

# Display selected ingredients
if ingredients_list:
    st.write("Your ingredients:", ", ".join(ingredients_list))

# Submit order
if st.button("Submit Order"):
    if not name_on_order.strip():
        st.warning("Please enter your name.")
    elif not ingredients_list:
        st.warning("Please select at least one ingredient.")
    else:
        session.sql(
            """
            INSERT INTO SMOOTHIES.PUBLIC.ORDERS
                (INGREDIENTS, NAME_ON_ORDER)
            VALUES (?, ?)
            """,
            params=[
                ingredients_string,
                name_on_order.strip()
            ]
        ).collect()

        st.success(
            f"Your smoothie is ordered, {name_on_order.strip()}!",
            icon="✅"
        )


# Test the SmoothieFroot API
smoothiefroot_response = requests.get(
    "https://my.smoothiefroot.com/api/fruit/watermelon"
)

st.text(smoothiefroot_response)

