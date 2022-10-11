import streamlit as st


def setup_page(page_title_text):
    """
    Basic setup for a streamlit page. Applies the FDm logo & standardized styling.
    :param page_title_text: The name of the page, to be displayed as the page title and the header.
    :return: Nothing
    """
    # Basic page styling
    st.set_page_config(
        layout="wide",
        page_title=page_title_text,
        initial_sidebar_state="auto",
        page_icon="👋",
    )
    hide_streamlit_style = '''
    <style>
    footer {visibility: hidden;}
    </style>
    '''
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    # Show the logo & page title side-by-side
    col1, col2 = st.columns([1, 8])
    with col1:
        st.image("./images/tab_logo.png", width=100)
    with col2:
        st.title(page_title_text)
