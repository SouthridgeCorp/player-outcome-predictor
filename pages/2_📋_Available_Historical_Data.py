import utils.page_utils as page_utils
import utils.match_utils.data_reader_utils as reader_utils
import streamlit as st


def app():
    '''
    Input page for requesting the training & testing window, which will be used to configure the rest of the models.
    :return: None
    '''
    page_utils.setup_page("Available Historical Data")
    tournaments = reader_utils.Tournaments()

    st.header("Select the training & testing windows")
    tournaments.training_start, tournaments.training_end = \
        st.select_slider("Select the training window:", options=tournaments.df['start_date'],
                         value=(tournaments.training_start, tournaments.training_end))

    tournaments.testing_start, tournaments.testing_end = \
        st.select_slider("Select the testing window:", options=tournaments.df['start_date'],
                         value=(tournaments.testing_start, tournaments.testing_end))

    st.caption(f"Testing window: {tournaments.training_start} to {tournaments.training_end}")
    st.caption(f"Training window: {tournaments.testing_start} to {tournaments.testing_end}")

    st.header("List of tournaments available for training & testing")
    with st.expander("Expand to see the list"):
        st.dataframe(tournaments.df, use_container_width=True)


app()
