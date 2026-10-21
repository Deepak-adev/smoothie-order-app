
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

# Load fruit names and API search terms
my_dataframe = session.table(
    "SMOOTHIES.PUBLIC.FRUIT_OPTIONS"
).select(
    col("FRUIT_NAME"),
    col("SEARCH_ON")
)

pd_df = my_dataframe.to_pandas()

# Customer name
name_on_order = st.text_input("Name on smoothie order:")

# Select fruits
fruit_list = pd_df["FRUIT_NAME"].tolist()

ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    options=fruit_list,
    max_selections=5
)

# Build the order and fetch nutrition data
ingredients_string = ""

if ingredients_list:
    for fruit_chosen in ingredients_list:
        # Add the selected fruit to the order string
        ingredients_string += fruit_chosen

        # Find the API search term for this fruit
        search_on = pd_df.loc[
            pd_df["FRUIT_NAME"] == fruit_chosen,
            "SEARCH_ON"
        ].iloc[0]

        # Request data for the selected fruit
        try:
            smoothiefroot_response = requests.get(
                "https://my.smoothiefroot.com/api/fruit/"
                + requests.utils.quote(str(search_on), safe=""),
                timeout=10
            )

            if smoothiefroot_response.status_code == 200:
                # Convert API JSON to a DataFrame
                sf_df = pd.json_normalize(
                    smoothiefroot_response.json()
                )

                st.write(f"Nutrition data for {fruit_chosen}")
                st.dataframe(
                    sf_df,
                    use_container_width=True
                )

            elif smoothiefroot_response.status_code == 404:
                st.info(
                    f"No API data found for {fruit_chosen}. "
                    "Try checking its SEARCH_ON value."
                )
            else:
                st.warning(
                    f"API returned HTTP "
                    f"{smoothiefroot_response.status_code} "
                    f"for {fruit_chosen}."
                )

        except requests.RequestException as error:
            st.warning(
                f"Could not retrieve data for {fruit_chosen}: {error}"
            )

    st.write("Your ingredients:", ", ".join(ingredients_list))

# Submit the smoothie order
if st.button("Submit Order"):
    if not name_on_order.strip():
        st.warning("Please enter your name.")
    elif not ingredients_list:
        st.warning("Please select at least one ingredient.")
    else:
        try:
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

        except Exception as error:
            st.error(f"Could not save your order: {error}")
