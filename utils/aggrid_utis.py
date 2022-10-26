import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder


class AgGridTable:
    def __init__(self, source_df):
        self.df = source_df


    def get_grid(self, key, editing = False, pagination = False, non_editable_columns = [] ) -> AgGrid:
        ''' This function displays aggrid and updates aggrid according to add_button_state(new_line) is True or False '''

        gb = GridOptionsBuilder.from_dataframe(self.df)
        gb.configure_grid_options()
        gb.configure_pagination(enabled=pagination)
        gb.configure_default_column(editable=editing)
        gb.configure_columns(non_editable_columns, editable=False)
        grid_table = AgGrid(
            self.df,
            gridOptions=gb.build(),
            fit_columns_on_grid_load=True,
            allow_unsafe_jscode=True,
            key=key
        )
        return grid_table

