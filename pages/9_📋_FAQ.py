import streamlit as st
from utils.graph_utils import render_mermaid
import os
import utils.page_utils as page_utils
import utils.config_utils as config_utils


def app():
    page_utils.setup_page("Working Backwards")
    wb_path = 'resources/working_backwards/'
    with open(f'{wb_path}/working_backwards.md', 'r') as f:
        wb = f.read()

    st.markdown(wb)

    for question in ['customer',
                     'opportunity',
                     'benefit',
                     'validation',
                     'user_experience'
                     ]:

        with open(f'{wb_path}/{question}.text.md') as f:
            text = f.read()
            st.markdown(text)
        mermaid_path = f'{wb_path}/{question}.mermaid.md'
        if os.path.exists(mermaid_path):
            with open(f'{wb_path}/{question}.mermaid.md') as f:
                graph = f.read()
                image, url = render_mermaid(graph)
                st.title(f"[{question} graph]({url})")
                st.image(image)

    with open(f'resources/faq/faq.md', 'r') as f:
        faq = f.read()
        st.markdown(faq)
    config_utils.set_app_comment_window("FAQ")


app()