import streamlit as st

import utils.page_utils as page_utils
from simulators.perfect_simulator import Granularity, PerfectSimulator
from utils.app_utils import data_selection_instance, rewards_instance



def data_selection_summary(tournaments):
    selected_tournaments, training, testing = st.columns(3)

    with selected_tournaments:
        st.subheader("Selected Tournaments:")
        st.write(tournaments.get_selected_tournaments())

    with training:
        st.subheader("Training Details:")
        training_start_date, training_end_date = tournaments.get_start_end_dates(False)
        st.write(f"Start Date: {training_start_date}")
        st.write(f"End Date: {training_end_date}")

    with testing:
        st.subheader("Testing Details:")
        testing_start_date, testing_end_date = tournaments.get_start_end_dates(True)
        st.write(f"Start Date: {testing_start_date}")
        st.write(f"End Date: {testing_end_date}")


@st.cache
def get_perfect_simulator_data(perfect_simulator, granularity, rewards_config):
    return perfect_simulator.get_simulation_evaluation_metrics_by_granularity(True, granularity)


def app():
    data_selection = data_selection_instance()
    tournaments = data_selection.get_helper().tournaments
    rewards = rewards_instance()

    page_utils.setup_page(" Review Perfect Simulation ")

    data_selection_summary(tournaments)

    granularity_list = ['None', Granularity.TOURNAMENT, Granularity.STAGE, Granularity.MATCH, Granularity.INNING]
    granularity = st.selectbox("Please select the granularity for reviewing Simulator stats", granularity_list)

    if granularity == 'None':
        st.write("Please select a valid Granularity")
    else:

        perfect_simulator = PerfectSimulator(data_selection, rewards)

        evaluation_column, top_players_column = st.columns(2)
        with st.spinner("Calculating Simulation Metrics.."):
            perfect_simulator_df = get_perfect_simulator_data(perfect_simulator, granularity, rewards)

        with st.spinner('Calculating Error Measures'):
            errors_df = perfect_simulator.get_error_measures(True, perfect_simulator_df, granularity,
                                                             perfect_simulator_df)

        with st.spinner("Calculating Top Players.."):
            perfect_simulator_df = data_selection.merge_with_players(perfect_simulator_df, 'player_key')
            perfect_simulator_df = perfect_simulator_df.sort_values('total_rewards', ascending=False)

        with evaluation_column:
            with st.spinner("Writing Evaluation & Error Metrics.."):
                st.subheader('Evaluation & Error Metrics')
                st.write(errors_df)

        with top_players_column:
            with st.spinner("Writing Top Players"):
                st.subheader('Top 100 Players')
                # CSS to inject contained in a string
                hide_dataframe_row_index = """
                            <style>
                            .row_heading.level0 {display:none}
                            .blank {display:none}
                            </style>
                            """

                # Inject CSS with Markdown
                st.markdown(hide_dataframe_row_index, unsafe_allow_html=True)
                st.dataframe(perfect_simulator_df[['name', 'total_rewards']].head(10))

    st.markdown('''
## Review Perfect Simulation Tab [v0.2]:

### Objective:
- Lets the user review all the `error_measures` and `simulation_evaluation_metrics` for each innings, match, tournament_stage 
and tournament in the `testing_window`, as projected by the `perfect_simulation_model`

- The user will be able to view aggregations on both `error_measures` and `evaluation_metrics` at the following granularities:
    - `by_player_and_innnings`
    - `by_player_and_match`
    - `by_player_and_tournament_stage`
    - `by_player_and_tournament`

- Lets the user view the `top_k` best performing players in each team as measured by `evaluation_metrics.rewards_by_player`:
    - `top_k_players_by_team_and_tournament`
    - `top_k_batsmen_by_team_and_tournament`
    - `top_k_bowlers_by_team_and_tournament`

### Definitions:

#### `perfect_simulation_model`:

A retrospective simulationmodel that assumes full knowledge of everything that transpired in each ball, innings, match,
tournament_stage and tournament to produce `simulation_evaluation_metrics`

#### `simulation_evaluation_metrics`

A data structure that is used to compare the outputs of two or more simiulations. It is composed of:
- `rewards_by_player_and_innings`
- `batting_rewards_by_player_and_innings`
- `bowling_rewards_by_player_and_innings`
- `fielding_rewards_by_player_and_innings`

#### `error_measures`

Consists of the following metrics calculated for each `simulation_evaluation_metric` in the course of comparison:
- `mean_absolute_error`
- `mean_absolute_percentage_error`

    ''')


app()
