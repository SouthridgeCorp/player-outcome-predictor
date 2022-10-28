import utils.page_utils as page_utils
import historical_data.singleton
import streamlit as st
import utils.config_utils
from data_selection.data_selection import DataSelection


def set_start_end_date(is_testing, tournaments):
    """
    Helper function for building out the date / time widget for testing & training
    :param is_testing: True = Inputs are for the testing mode, False = Inputs are for the training mode
    :param tournaments: The tournaments object that consists of all tournament meta-data
    :return: None
    """
    if is_testing:
        mode = "testing"
    else:
        mode = "training"

    st.header(f"Select the {mode} window")

    start_date, end_date = \
        st.slider("Select the {mode} window:", min_value=tournaments.first_match_date,
                  max_value=tournaments.last_match_date,
                  value=(tournaments.first_match_date, tournaments.last_match_date), key=f"{mode}_start")

    if start_date > end_date:
        st.error('Error: End date must fall after start date.')

    tournaments.set_start_end_dates(start_date, end_date, is_testing)

    st.subheader(f"Summary for the {mode} window")
    st.markdown(f"**Start Date** = {start_date}")
    st.markdown(f"**End Date**= {end_date}")

    if len(tournaments.selected) == 0:
        st.markdown(f"_Please select tournaments for {mode}_")
    else:
        st.markdown(f"_Selected Tournaments & Match counts for {mode}:_")
    for tournament in tournaments.selected:
        matches = tournaments.matches(tournament)
        match_count = matches.get_selected_match_count(start_date, end_date)
        st.markdown(f"- **{tournament.upper()}** = {match_count} matches")


def app():
    """
    Input page for requesting the training & testing window, which will be used to configure the rest of the models.
    :return: None
    """
    page_utils.setup_page("Data Selection")
    config_utils = utils.config_utils.create_utils_object()

    # get the helper from the singleton instance
    helper = historical_data.singleton.get_helper(config_utils)

    # get a data selection instance from the singleton
    data_selection = DataSelection(historical_data)
    tournaments = helper.tournaments

    tournament_selector, training_column, testing_column = st.columns(3, gap="large")

    with tournament_selector:
        st.header("Select the Tournaments ")
        tournaments.set_selected_tournament_names(st.multiselect("Please select tournaments for training & testing",
                                                                 tournaments.df["name"].to_list()))

    with training_column:
        set_start_end_date(False, tournaments)

    with testing_column:
        set_start_end_date(True, tournaments)

    st.header("List of tournaments available for training & testing")

    with st.expander("Expand to see the list"):
        st.dataframe(tournaments.df, use_container_width=True)

    st.header("Player Universe Selected")
    with st.expander("Expand to see the player universe"):
        pu = data_selection.get_frequent_players_universe()
        st.dataframe(pu, use_container_width=True)
app()
