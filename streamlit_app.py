
import streamlit as st
import pandas as pd
import requests
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import col

st.title("🥤 Custom Smoothie Order")
st.write("Create your smoothie and explore fruit nutrition!")

session = get_active_session()

my_dataframe = session.table(
    "SMOOTHIES.PUBLIC.FRUIT_OPTIONS"
).select(col("FRUIT_NAME"), col("SEARCH_ON"))

pd_df = my_dataframe.to_pandas()

fruit_list = pd_df["FRUIT_NAME"].tolist()

name_on_order = st.text_input("Name on smoothie order:")

ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    options=fruit_list,
    max_selections=5
)

ingredients_string = ""

for fruit_chosen in ingredients_list:
    ingredients_string += fruit_chosen

    search_on = pd_df.loc[
        pd_df["FRUIT_NAME"] == fruit_chosen, "SEARCH_ON"
    ].iloc[0]

    st.write("Search value for", fruit_chosen, "is", search_on)

    try:
        response = requests.get(
            f"https://my.smoothiefroot.com/api/fruit/{requests.utils.quote(search_on)}",
            timeout=10
        )

        if response.status_code == 200:
            fruit_data = response.json()
            st.write(f"Nutrition information for {fruit_chosen}:")
            st.json(fruit_data)
        else:
            st.info(f"No API data available for {fruit_chosen}.")
    except requests.RequestException:
        st.info(f"Could not retrieve API data for {fruit_chosen}.")

if ingredients_list:
    st.write("Your ingredients:", ", ".join(ingredients_list))

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
            params=[ingredients_string, name_on_order.strip()]
        ).collect()

        st.success(f"Your smoothie is ordered, {name_on_order.strip()}!")
