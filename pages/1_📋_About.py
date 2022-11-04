import streamlit as st
import utils.page_utils as page_utils

def app():

    page_utils.setup_page(" Press Release ")
    with open('resources/press_release/press_release.md', 'r') as f:
        press_release = f.read()
    st.markdown(press_release)

app()