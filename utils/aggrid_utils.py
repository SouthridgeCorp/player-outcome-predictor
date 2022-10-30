import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder


class AgGridTable:
    """
    This class facilitates access to a Streamlit AgGrid table which can be configured as per different requirements
    """

    def __init__(self, source_df: pd.DataFrame):
        """
        Initialise the class
        :param source_df: The dataframe which will be shown in AgGrid
        """
        self.df = source_df

    def get_grid(self,
                 key: str, editing: bool = False, pagination: bool = False, non_editable_columns: list = []) -> AgGrid:
        """
        This function creates an AgGrid instance, displays it and provides an instance which can be used to track
        updates
        :param key: The streamlit key for this component, must be unique for the context (since AgGrid is
        a streamlit component)
        :param editing: Indicates whether all columns in the grid are editable in the UI
        :param pagination: Indicates if the table should show pagination
        :param non_editable_columns: A list of columns which must be non-editable even if the entire grid is editable.
        The names of the column should be present in the source_df
        :return: An AgGrid instance which has been displayed in streamlit already
        """
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
