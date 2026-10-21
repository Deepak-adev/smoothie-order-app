
import streamlit as st
import pandas as pd
import requests
from snowflake.snowpark.functions import col

# --------------------------------------------------
# App title
# --------------------------------------------------
st.title("🥤 Custom Smoothie Order")
st.write("Create your smoothie and explore fruit nutrition!")

# --------------------------------------------------
# Connect to Snowflake
# --------------------------------------------------
cnx = st.connection("snowflake")
session = cnx.session()

# --------------------------------------------------
# Load fruit options and search terms
# --------------------------------------------------
my_dataframe = session.table(
    "SMOOTHIES.PUBLIC.FRUIT_OPTIONS"
).select(
    col("FRUIT_NAME"),
    col("SEARCH_ON")
)

pd_df = my_dataframe.to_pandas()

# --------------------------------------------------
# Customer name
# --------------------------------------------------
name_on_order = st.text_input("Name on smoothie order:")

# --------------------------------------------------
# Fruit selection
# --------------------------------------------------
fruit_list = pd_df["FRUIT_NAME"].tolist()

ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    options=fruit_list,
    max_selections=5
)

# --------------------------------------------------
# Build ingredients and retrieve API data
# --------------------------------------------------
ingredients_string = ""
nutrition_records = []

for fruit_chosen in ingredients_list:
    # Preserve the exact selected fruit name for the order
    ingredients_string += fruit_chosen

    # Get the API search term for this fruit
    search_on = pd_df.loc[
        pd_df["FRUIT_NAME"] == fruit_chosen,
        "SEARCH_ON"
    ].iloc[0]

    st.caption(
        f"API search term for {fruit_chosen}: {search_on}"
    )

    try:
        response = requests.get(
            "https://my.smoothiefroot.com/api/fruit/"
            + requests.utils.quote(str(search_on), safe=""),
            timeout=10
        )

        if response.status_code == 200:
            fruit_data = response.json()

            st.write(f"Nutrition information: {fruit_chosen}")
            st.json(fruit_data)

            # Convert the API JSON response into a DataFrame
            sf_df = pd.json_normalize(fruit_data)
            nutrition_records.append({
                "Fruit": fruit_chosen,
                "Nutrition data": sf_df.to_dict(orient="records")[0]
            })

            with st.expander(
                f"View DataFrame for {fruit_chosen}"
            ):
                st.dataframe(sf_df, use_container_width=True)

        elif response.status_code == 404:
            st.info(
                f"No nutrition data found for {fruit_chosen}. "
                "The API may not support this search term."
            )
        else:
            st.info(
                f"API returned HTTP {response.status_code} "
                f"for {fruit_chosen}."
            )

    except requests.RequestException as error:
        st.warning(
            f"Could not retrieve API data for {fruit_chosen}: "
            f"{error}"
        )
    except ValueError:
        st.warning(
            f"The API response for {fruit_chosen} "
            "was not valid JSON."
        )

# --------------------------------------------------
# Display selected ingredients
# --------------------------------------------------
if ingredients_list:
    st.write("Your ingredients:", ", ".join(ingredients_list))

# --------------------------------------------------
# Workshop API test: Watermelon
# --------------------------------------------------
with st.expander("Test SmoothieFroot API with Watermelon"):
    try:
        smoothiefroot_response = requests.get(
            "https://my.smoothiefroot.com/api/fruit/watermelon",
            timeout=10
        )

        st.write("API response status:")
        st.text(smoothiefroot_response)

        if smoothiefroot_response.status_code == 200:
            smoothiefroot_data = smoothiefroot_response.json()

            st.write("JSON response:")
            st.json(smoothiefroot_data)

            st.write("SmoothieFroot DataFrame:")
            sf_df = pd.json_normalize(smoothiefroot_data)
            st.dataframe(sf_df, use_container_width=True)
        else:
            st.warning(
                "Watermelon API request returned HTTP "
                f"{smoothiefroot_response.status_code}."
            )

    except requests.RequestException as error:
        st.warning(f"Watermelon API request failed: {error}")

# --------------------------------------------------
# Submit order
# --------------------------------------------------
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
