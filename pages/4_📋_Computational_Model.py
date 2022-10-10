import streamlit as st
from utils.graph_utils import render_mermaid
import utils.page_utils as page_utils
import utils.config_utils as config_utils


def app():
    with open('resources/computational_model/computational_model.md', 'r') as f:
        computational_model = f.read()
        image, url = render_mermaid(computational_model)

    page_utils.setup_page(f"[Computational Model]({url})")
    st.image(image, "Computational Model")
    config_utils.set_app_comment_window("Computational Model")

app()