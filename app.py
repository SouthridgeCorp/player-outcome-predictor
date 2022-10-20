import streamlit as st
import utils.page_utils as page_utils


# Launching pad for the entire application.
#
# Steps to customize your app:
# 1. Name the app correctly using setup_page() as demonstrated in app()
# 2. Add new pages / tabs under the pages/ directory. Streamlit renders these tabs alphabetically.
#
# Refer to https://docs.streamlit.io/library/get-started/multipage-apps for details.
def app():
    page_utils.setup_page("Player Outcome Predictor: v{0.1}")
    with open('README.md', 'r') as f:
        readme = f.read()
    st.markdown(readme)
app()

