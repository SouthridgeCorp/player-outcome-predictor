import streamlit as st
import utils.page_utils as page_utils
from utils.app_utils import data_selection_instance
import seaborn as sns
import matplotlib.pyplot as plt
from simulators.utils.predictive_utils import calculate_probability_toss_winner_fields_first
import pandas as pd
def app():
    page_utils.setup_page(" Review Predictive Simulation ")

    data_selection = data_selection_instance()

    st.header("Explanability")

    matches_df = data_selection.get_all_matches()



    st.subheader("When does the toss winner choose fielding?")

    all_matches, group_by_venue = st.columns(2)
    group_by_team, group_by_team_venue = st.columns(2)
    sns.set()
    with all_matches:
        st.write("Across all matches")
        fig, ax = plt.subplots()
        ax.hist(matches_df['toss_decision'], density=True)
        st.pyplot(fig)

    with group_by_venue:
        st.write("When grouped by venue")
        sns.set_theme(style="ticks")
        all_matches_df = matches_df.reset_index()
        ag = all_matches_df.groupby(['toss_decision', 'venue']).count().unstack()
        ag = ag.transpose()
        ag = ag.fillna(0)
        ag = ag.reset_index()
        ag['normalised_fielding'] = ag['field'] / (ag['field'] + ag['bat'])
        ag = ag[ag['level_0'] == 'index']
        ag.set_index('venue', inplace=True, verify_integrity=True )
        st.bar_chart(ag, y='normalised_fielding')

    with group_by_team:
        st.write("When grouped by team")
        sns.set_theme(style="ticks")
        all_matches_df = matches_df.reset_index()
        ag = all_matches_df.groupby(['toss_decision', 'toss_winner']).count().unstack()
        ag = ag.transpose()
        ag = ag.fillna(0)
        ag = ag.reset_index()
        ag['normalised_fielding'] = ag['field'] / (ag['field'] + ag['bat'])
        ag = ag[ag['level_0'] == 'index']
        ag.set_index('toss_winner', inplace=True, verify_integrity=True)
        st.bar_chart(ag, y='normalised_fielding')

    with group_by_team_venue:
        probabilities = calculate_probability_toss_winner_fields_first(matches_df)
        g = sns.JointGrid(data=probabilities, x="toss_winner", y="venue", marginal_ticks=True)

        # Add the joint and marginal histogram plots
        img = g.plot_joint(
           sns.histplot, discrete=(True, False),
           cmap="light:#03012d", pmax=.8, cbar=True
        )
        g.plot_marginals(sns.histplot, element="step", color="#03012d")
        st.pyplot(img)



    st.markdown('''
## Review Predictive Simulations Tab [v0.4]:

### Objective:
- Lets the user review all the `error_measures` and `simulation_evaluation_metrics` for each innings, match, tournament_stage 
and tournament in the `testing_window`, as projected by the `predictive_simulation_model`
- The user will be able to view aggregations on both `error_measures` and `simulation_evaluation_metrics` at the following granularities:
    - `by_player_and_innnings`
    - `by_player_and_match`
    - `by_player_and_tournament_stage`
    - `by_player_and_tournament`
- Lets the user view the projected `top_k` best performing players in each team as measured by `evaluation_metrics.rewards_by_player`:
    - `top_k_players_by_team_and_tournament`
    - `top_k_batsmen_by_team_and_tournament`
    - `top_k_bowlers_by_team_and_tournament`

### Definitions:

#### `predictive_simulation_model`

A model that generates a set of `credible_scenarios` by using the `inferential_models` to simulate entire tournaments
by building them from ball by ball outcomes. Each `credible_scenario` will be associated with a set of `simulation_evaluation_metrics`.
    ''')


app()
