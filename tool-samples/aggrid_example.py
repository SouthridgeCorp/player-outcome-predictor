import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
import pandas as pd

DATA_SOURCE_PATH = "tool-samples/data/production/collabs/collabs.csv"

def app():


    def data_upload():
        ''' This function uploads csv from local file in the DATA_SOURCE_PATH '''
        df = pd.read_csv(DATA_SOURCE_PATH)
        return df
    def show_grid(newline, editing, cleanadd, cleanediting):
        ''' This function displays aggrid and updates aggrid according to add_button_state(new_line) is True or False '''
        df = data_upload()
        if newline:
            df.loc[0] = [None] * len(df.columns) #adding blank line to df
            df.to_csv(DATA_SOURCE_PATH, index=False)
            st.session_state["add_button_state"] = False
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_grid_options()
        gb.configure_pagination(enabled=True)
        gb.configure_default_column(editable=editing)
        grid_table = AgGrid(
            df,
            height=400,
            gridOptions=gb.build(),
            fit_columns_on_grid_load=True,
            allow_unsafe_jscode=True,
        )
        clean_buttons(cleanadd, cleanediting)
        return grid_table
    def update(grid_table):
        ''' This function updated aggrid from local csv file, and we set add_button_state=False for adding blank lines '''

        df=pd.DataFrame(grid_table['data'])
        df.to_csv(DATA_SOURCE_PATH, index=False)
        st.session_state["add_button_state"] = False
        st.session_state["start_editing_button_state"] = False
        st.session_state["clean_startediting"] = False
        st.session_state["clean_addbutton"] = False

    # When the button is pressed in Streamlit, the status of the button is changed to True, but it does not become false again, so it does not work like a click event.
    # When we want to add a row for the second time, we need to save it as button_state=False so that there is no problem.

    placeholder_addline = st.empty()
    add_button = placeholder_addline.button('Add New Line')
    placeholder_start = st.empty()
    start_editing_button = placeholder_start.button('Start Editing')

    def clean_buttons(clean_addbutton=False, clean_startediting=False):
        if clean_addbutton:
            placeholder_addline.empty()
        if clean_startediting:
            placeholder_start.empty()

    if "add_button_state" not in st.session_state:
        st.session_state["add_button_state"] = False
    if "start_editing_button_state" not in st.session_state:
        st.session_state["start_editing_button_state"] = False
    if "clean_addbutton" not in st.session_state:
        st.session_state["clean_addbutton"]= False
    if "clean_startediting" not in st.session_state:
        st.session_state["clean_startediting"] = False

    if add_button:
        st.session_state["add_button_state"]  = True
        if "holder" not in st.session_state:
            st.session_state["holder"] = True
        st.session_state["clean_addbutton"] = True
        st.session_state["clean_startediting"] = True
        st.session_state["start_editing_button_state"] = True

    if start_editing_button:
        st.session_state["start_editing_button_state"] = True
        st.session_state["add_button_state"] = False
        st.warning("You've opened <Editing Mode>, to save your change press button of Done Editing!")
        st.session_state["clean_startediting"] = True
        st.session_state["clean_addbutton"] = True


    grid_table = show_grid(st.session_state["add_button_state"], st.session_state["start_editing_button_state"], st.session_state["clean_addbutton"],st.session_state["clean_startediting"])
    placeholder_done = st.empty()
    done_editing_button = placeholder_done.button("Done Editing", on_click=update, args=[grid_table])

    if done_editing_button:
        st.success("You've saved your change successfully!")

app()