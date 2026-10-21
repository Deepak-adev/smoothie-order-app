
import streamlit as st
import pandas as pd
import requests
from snowflake.snowpark.functions import col

# App title
st.title("🥤 Customize Your Smoothie! 🥤")
st.write("Choose the fruits you want in your custom Smoothie!")

# Connect to Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# Load fruit options
my_dataframe = session.table(
    "SMOOTHIES.PUBLIC.FRUIT_OPTIONS"
).select(
    col("FRUIT_NAME"),
    col("SEARCH_ON")
)

pd_df = my_dataframe.to_pandas()

# Customer name
name_on_order = st.text_input("Name on Smoothie:")

if name_on_order.strip():
    st.write(f"The name on your Smoothie will be: {name_on_order.strip()}")

# Choose up to five fruits
fruit_list = pd_df["FRUIT_NAME"].tolist()

ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    options=fruit_list,
    max_selections=5
)

# Fetch and display nutrition information for each selected fruit
ingredients_string = ""

if ingredients_list:
    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen

        st.subheader(fruit_chosen + " Nutrition Information")

        try:
            smoothiefroot_response = requests.get(
                "https://my.smoothiefroot.com/api/fruit/"
                + requests.utils.quote(fruit_chosen, safe=""),
                timeout=10
            )

            if smoothiefroot_response.status_code == 200:
                sf_df = pd.json_normalize(
                    smoothiefroot_response.json()
                )

                st.dataframe(
                    sf_df,
                    use_container_width=True
                )

            elif smoothiefroot_response.status_code == 404:
                st.info(
                    "Sorry, that fruit is not in our database."
                )

            else:
                st.warning(
                    f"API returned HTTP "
                    f"{smoothiefroot_response.status_code}."
                )

        except requests.RequestException as error:
            st.warning(f"Could not retrieve fruit data: {error}")

    st.write("Your ingredients:", ", ".join(ingredients_list))

# Submit smoothie order
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
                f"Your smoothie is ordered, "
                f"{name_on_order.strip()}!",
                icon="✅"
            )

        except Exception as error:
            st.error(f"Could not save your order: {error}")
