import utils.page_utils as page_utils
import utils.match_utils.singleton
import streamlit as st
import datetime


def set_start_end_date(is_testing, tournaments):
    """
    Helper function for building out the date / time widget for testing & training
    :param is_testing: True = Inputs are for the testing mode, False = Inputs are for the training mode
    :param tournaments: The tournaments object that consists of all tournament meta-data
    :return: None
    """
    if is_testing:
        mode = "testing"
        start_date = tournaments.testing_start
        end_date = tournaments.testing_end
    else:
        mode = "training"
        start_date = tournaments.training_start
        end_date = tournaments.training_end

    st.header(f"Select the {mode} window")

    start_date = st.date_input('Start date', start_date, min_value=start_date, max_value=datetime.date.today(),
                               key=f"{mode}_start")
    end_date = st.date_input('End date', end_date, min_value=start_date, max_value=datetime.date.today(),
                             key=f"{mode}_end")

    if start_date > end_date:
        st.error('Error: End date must fall after start date.')

    if is_testing:
        tournaments.testing_start = start_date
        tournaments.testing_end = end_date
    else:
        tournaments.training_start = start_date
        tournaments.training_end = end_date

    st.subheader(f"Summary for the {mode} window")
    st.markdown(f"**Start Date** = {start_date}")
    st.markdown(f"**End Date**= {end_date}")

    if len(tournaments.selected) == 0:
        st.markdown(f"_Please select tournaments for {mode}_")
    else:
        st.markdown(f"_Selected Tournaments & Match counts for {mode}:_")
    for tournament in tournaments.selected:
        matches = tournaments.get_matches(tournament)
        match_count = matches.get_selected_match_count(start_date, end_date)
        st.markdown(f"- **{tournament.upper()}** = {match_count} matches")


def app():
    """
    Input page for requesting the training & testing window, which will be used to configure the rest of the models.
    :return: None
    """
    page_utils.setup_page("Static Configuration")
    helper = utils.match_utils.singleton.get_helper()
    tournaments = helper.tournaments

    tournament_selector, training_column, testing_column = st.columns(3)

    with tournament_selector:
        st.header("Select the Tournaments ")
        tournaments.set_selected_names(st.multiselect("Please select tournaments for training & testing",
                                                      tournaments.df["name"].to_list()))

    with training_column:
        set_start_end_date(False, tournaments)

    with testing_column:
        set_start_end_date(True, tournaments)

    st.header("List of tournaments available for training & testing")

    with st.expander("Expand to see the list"):
        st.dataframe(tournaments.df, use_container_width=True)


app()
