import utils.app_utils
import utils.page_utils as page_utils
import streamlit as st
from utils.app_utils import data_selection_instance, reset_session_states, show_data_selection_summary
from data_selection.data_selection import DataSelectionType


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


def set_training_start_end_date(tournaments):
    """
    Helper function for building out the date / time widget for testing & training
    :param is_testing: True = Inputs are for the testing mode, False = Inputs are for the training mode
    :param tournaments: The tournaments object that consists of all tournament meta-data
    :return: None
    """
    st.header(f"Training Window")

    seasons_df = tournaments.get_tournament_and_season_details()

    end_date = tournaments.get_first_testing_date()

    dates = seasons_df[seasons_df['date'] < end_date]['date'].tolist()

    start_date = st.selectbox("Select the training start date", dates,
                              key="training_start", on_change=reset_session_states)

    tournaments.set_training_window(start_date, end_date)


def select_testing_window(tournaments, data_selection):
    st.header(f"Testing Window")

    tournament_list = tournaments.df["name"].to_list()
    tournament_name = st.selectbox("Select the tournament", tournament_list,
                                   key="testing_tournaments", on_change=reset_session_states)
    tournament = tournaments.get_key(tournament_name)

    seasons = data_selection.get_all_seasons(tournament)
    season = st.selectbox("Select the season", seasons, key="testing_seasons")

    tournaments.set_testing_details(tournament_name, season)


def set_selection_type(data_selection):

    st.header(f"Selection Type")

    selection_types = [DataSelectionType.AND_SELECTION, DataSelectionType.OR_SELECTION]

    selection_type = st.radio("Selection Type:", options=selection_types, on_change=reset_session_states)

    data_selection.set_selection_type(selection_type)

def app():
    """
    Input page for requesting the training & testing window, which will be used to configure the rest of the models.
    :return: None
    """
    page_utils.setup_page("Data Selection")

    # get a data selection instance from the singleton
    data_selection = data_selection_instance()
    tournaments = data_selection.get_helper().tournaments

    testing_column, training_column, selection_type_column = st.columns(3, gap="large")

    with testing_column:
        select_testing_window(tournaments, data_selection)

    with training_column:
        set_training_start_end_date(tournaments)

    with selection_type_column:
        set_selection_type(data_selection)

    show_data_selection_summary(data_selection)

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
