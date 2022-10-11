import streamlit as st
from utils.graph_utils import render_mermaid
import utils.page_utils as page_utils
import utils.config_utils as config_utils

def app():

    with open('resources/architecture_hypothesis/architecture_hypothesis.mermaid.md', 'r') as f:
        graph = f.read()
        image, url = render_mermaid(graph)
        page_utils.setup_page(f"[Architecture Hypothesis]({url})")
        st.image(image)
app()