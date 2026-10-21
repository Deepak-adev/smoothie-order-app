
if ingredients_list:
    ingredients_string = ""

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen

        # Find the API search term for the selected fruit
        search_on = pd_df.loc[
            pd_df["FRUIT_NAME"] == fruit_chosen,
            "SEARCH_ON"
        ].iloc[0]

        st.subheader(f"{fruit_chosen} Nutrition Information")

        try:
            smoothiefroot_response = requests.get(
                "https://my.smoothiefroot.com/api/fruit/"
                + requests.utils.quote(str(search_on), safe=""),
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
