import utils.app_utils
import utils.page_utils as page_utils
import streamlit as st
from utils.app_utils import data_selection_instance, reset_session_states



def on_date_change(tournaments, key, is_testing):
    """
    Callback function to persist the value of changing dates via the slider
    """
    start_date, end_date = st.session_state[key]
    tournaments.set_start_end_dates(start_date, end_date, is_testing=is_testing)
    # A change to this object is a big deal - make sure subsequent pages also reset their caches
    reset_session_states()


def on_tournament_change(tournaments):
    """
    Callback function to persist the value of changing tournaments through the multi-select dropdown
    """
    values = st.session_state.tournaments
    tournaments.set_selected_tournament_names(values)
    # A change to this object is a big deal - make sure subsequent pages also reset their caches
    reset_session_states()


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

    start_date, end_date = tournaments.get_start_end_dates(is_testing)

    key = f"{mode}_start"
    start_date, end_date = \
        st.slider("Select the {mode} window:", min_value=tournaments.first_match_date,
                  max_value=tournaments.last_match_date,
                  value=(start_date, end_date), key=key, on_change=on_date_change,
                  args=(tournaments, key, is_testing))

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

    # get a data selection instance from the singleton
    data_selection = data_selection_instance()
    tournaments = data_selection.get_helper().tournaments

    testing_column, training_column = st.columns(2, gap="large")

    with testing_column:
        tournaments = tournaments.df["name"].to_list()
        tournament = st.selectbox("Select the Testing window", tournaments, key="testing_tournaments")


    with training_column:
        set_start_end_date(False, tournaments)


    st.header("List of tournaments available for training & testing")

    with st.expander("Expand to see the list"):
        st.dataframe(tournaments.df, use_container_width=True)

    show_player_universe = st.checkbox("Show Player Universe")

    if show_player_universe:

        st.header("Player Universe Selected")
        with st.spinner("Calculating Player Universe"):
            pu = data_selection.get_frequent_players_universe()
        if pu.empty:
            st.write("Please select the target tournaments before calculating the player universe")
        else:
            st.dataframe(pu, use_container_width=True)
app()
