import utils.page_utils as page_utils
import streamlit as st
from utils.app_utils import data_selection_instance, reset_session_states, show_data_selection_summary
from data_selection.data_selection import DataSelectionType
import logging

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)


def on_training_date_change(tournaments, end_date):
    """
    Record the training dates when the user selects something from the training start date dropdown
    """
    value = st.session_state.training_start
    tournaments.set_training_window(value, end_date)
    # A change to this object is a big deal - make sure subsequent pages also reset their caches
    reset_session_states()


def on_testing_tournament_change(tournaments):
    """
    Callback function to persist the value of changing the testing tournament dropdown
    """
    value = st.session_state.testing_tournaments
    tournaments.set_testing_details(value, "")
    # A change to this object is a big deal - make sure subsequent pages also reset their caches
    reset_session_states()


def on_testing_season_change(tournaments):
    """
    Callback function to persist the value of changing the testing season dropdown
    """
    value = st.session_state.testing_seasons
    test_tournament_key, test_tournament_name, test_season = tournaments.get_testing_details()
    tournaments.set_testing_details(test_tournament_name, value)
    # A change to this object is a big deal - make sure subsequent pages also reset their caches
    reset_session_states()


def set_training_start_end_date(tournaments):
    """
    Helper function for building out the date / time widget for training
    :param tournaments: The tournaments object that consists of all tournament meta-data
    :return: None
    """
    st.header(f"Training Window")

    # get a list of all seasons available
    seasons_df = tournaments.get_tournament_and_season_details()

    # figure out the current tournament start date and hardcode the end date to the start of testing
    start_date, end_date = tournaments.get_training_start_end_dates()
    end_date = tournaments.get_first_testing_date()

    # Get a list of start dates for each season of each tournament, up until the start of the testing season
    dates = seasons_df[seasons_df['date'] < end_date]['date'].tolist()
    dates.sort(reverse=True)
    index = 0

    # Set up the dropdown function & the training window
    if start_date in dates:
        index = dates.index(start_date)
    start_date = st.selectbox("Select the training start date", dates, index=index,
                              key="training_start", on_change=on_training_date_change, args=([tournaments, end_date]))

    tournaments.set_training_window(start_date, end_date)


def select_testing_window(tournaments, data_selection):
    """
    Sets up the dropdowns to source testing windows
    """
    st.header(f"Testing Window")

    # Get current selection details
    tournament_list = tournaments.df["name"].to_list()
    test_tournament_key, test_tournament_name, test_season = tournaments.get_testing_details()
    tournament_index = 0
    season_index = 0

    # Setup the tournament details
    if test_tournament_name in tournament_list:
        tournament_index = tournament_list.index(test_tournament_name)

    tournament_name = st.selectbox("Select the tournament", tournament_list,
                                   key="testing_tournaments", on_change=on_testing_tournament_change,
                                   args=([tournaments]), index=tournament_index)

    # Setup the corresponding season details
    seasons = data_selection.get_all_seasons(tournaments.get_key(tournament_name))
    if test_season in seasons:
        season_index = seasons.index(test_season)

    season = st.selectbox("Select the season", seasons, key="testing_seasons", on_change=on_testing_season_change,
                          args=([tournaments]), index=season_index)

    tournaments.set_testing_details(tournament_name, season)


def set_selection_type(data_selection):
    """
    Show the UI for selecting the data type selection
    """
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

    logger.debug("Setting up data selection")
    # get a data selection instance from the singleton
    data_selection = data_selection_instance()
    tournaments = data_selection.get_helper().tournaments

    testing_column, training_column, selection_type_column = st.columns(3, gap="large")

    with testing_column:
        logger.debug("Selecting testing window")
        select_testing_window(tournaments, data_selection)

    with training_column:
        logger.debug("Selecting training window")
        set_training_start_end_date(tournaments)

    with selection_type_column:
        logger.debug("Selecting type")
        set_selection_type(data_selection)

    logger.debug("Showing data selection summary")
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
