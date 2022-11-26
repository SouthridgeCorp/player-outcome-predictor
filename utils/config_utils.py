import re
import toml
import pandas as pd
import os
import logging
import numpy as np
import streamlit as st
from gspread_pandas import Spread, Client
from google.oauth2 import service_account
import snowflake.connector
from snowflake.connector.pandas_tools import pd_writer, write_pandas
from sqlalchemy import create_engine
import ssl

ssl._create_default_https_context = ssl._create_unverified_context
from datetime import datetime

def init_snowflake_connection():
    connection = snowflake.connector.connect(**st.secrets["snowflake"])
    return connection

def init_snowflake_sql_engine(database_name, schema_name):
    conn_string = f"snowflake://{st.secrets['snowflake']['user']}" \
                  f":{st.secrets['snowflake']['password']}@" \
                  f"{st.secrets['snowflake']['account']}/{database_name}/{schema_name}"
    engine = create_engine(conn_string)
    return engine


def create_utils_object():
    if 'ConfigUtils' not in st.session_state:
        st.session_state['ConfigUtils'] = ConfigUtils("./.streamlit/config.toml")
    return st.session_state['ConfigUtils']


def set_app_comment_window(page_name):
    utils_obj = create_utils_object()
    st.title("Feedback! 💬")

    st.write("Add your comment to the page:", page_name)
    form = st.form("comment")
    # We are saving user info to session state to use it from other pages. We need to check if user info saved to session state before.
    # It is enough to check one value of user info like name_val in below.
    if 'name_val' not in st.session_state:
        st.session_state['name_val'] = form.text_input(utils_obj.config['feedback_form']['questions']['USER_NAME'])
        st.session_state['email_val'] = form.text_input(utils_obj.config['feedback_form']['questions']['USER_EMAIL'])
        st.session_state['target_user_val'] = form.radio(
            utils_obj.config['feedback_form']['questions']['USER_PERSONA'],
            utils_obj.config['app']['user_personas'])
    else:  # auto populating
        st.session_state['name_val'] = form.text_input(utils_obj.config['feedback_form']['questions']['USER_NAME'],
                                                       value=st.session_state['name_val'])
        st.session_state['email_val'] = form.text_input(utils_obj.config['feedback_form']['questions']['USER_EMAIL'],
                                                        value=st.session_state['email_val'])

        st.session_state['target_user_val'] = form.radio(
            utils_obj.config['feedback_form']['questions']['USER_PERSONA'],
            utils_obj.config['app']['user_personas'],
            index=utils_obj.config['app']['user_personas'].index(st.session_state['target_user_val'])
        )

    alternate_target_val = form.text_input(
        utils_obj.config['feedback_form']['questions']['ALTERNATE_USER_PERSONA'])

    questions_val = form.text_area(
        utils_obj.config['feedback_form']['questions']['QUESTIONS'])
    now = datetime.now().date().strftime("%Y/%m/%d")

    feedback_form_data = dict(zip(list(utils_obj.config['feedback_form']['schema'].keys()),
                                  [now, st.session_state['name_val'], st.session_state['email_val'],
                                   st.session_state['target_user_val'], alternate_target_val, questions_val,
                                   page_name]))

    submit = form.form_submit_button("Add comment")

    if submit:
        if utils_obj.isValid(feedback_form_data['USER_EMAIL']):
            st.write("Received Feedback")
            st.write(feedback_form_data)
            utils_obj.save_feedback(feedback_form_data)
        else:
            st.error("Invalid Email ID!!")


class ConfigUtils:

    def __init__(self, path_to_toml_config=None):
        if (path_to_toml_config is None) and ('FDm' in st.secrets):
            logging.info("Loading config via streamlit")
            config = st.secrets['FDm']
        else:
            config = toml.load(path_to_toml_config)
        self.config = config
        self.spreadsheet = None
        self.worksheet = None
        self.create_feedback_storage()

    def get_feedback_path(self):
        """Returns the materialized path to the stored feedback form"""
        return f"{self.config['feedback_form']['storage_dir']}/" \
               f"{self.config['app']['environment']}/" \
               f"{self.config['feedback_form']['storage_path']}"

    def get_feedback_file(self):
        """Returns the materialized path to the stored feedback form"""
        return f"{self.get_feedback_path()}/" \
               f"{self.config['feedback_form']['storage_file']}"

    def get_feedback_df_schema(self):
        feedback_df_schema = np.dtype(
            [(key, eval(dtype))
             for key, dtype in self.config['feedback_form']['schema'].items()]
        )
        feedback_df = pd.DataFrame(np.empty(0, dtype=feedback_df_schema))
        return feedback_df

    def create_local_feedback_storage(self):
        """Ensures that a local feedback storage backend is created when called"""

        feedback_path = self.get_feedback_path()
        if not (os.path.exists(feedback_path)):
            logging.info(f"Creating feedback path directory: {feedback_path}")
            os.makedirs(feedback_path)

        feedback_file = self.get_feedback_file()
        if not (os.path.exists(feedback_file)):
            feedback_df = self.get_feedback_df_schema()
            feedback_df.to_csv(feedback_file,
                               index=False)
            logging.info(f"Initiated empty feedback form backend file at {feedback_file}")


    def get_feedback_snowflake_path(self):
        database_name = f"{self.config['feedback_form']['storage_dir']}_{self.config['app']['environment']}"
        schema_name, table_name = tuple(self.config['feedback_form']['storage_path'].split("."))
        return database_name, schema_name, table_name

    def create_snowflake_feedback_storage(self):
        """Ensures that a snowflake feedback storage backend is created when called"""

        self.feedback_snowflake_connection = init_snowflake_connection()

        database_name, schema_name, table_name = self.get_feedback_snowflake_path()

        setup_query = f"""
                CREATE TRANSIENT DATABASE IF NOT EXISTS {database_name}; 
                USE DATABASE {database_name};
                CREATE TRANSIENT SCHEMA IF NOT EXISTS {database_name}.{schema_name};  
                USE SCHEMA {schema_name};
                """

        cursor_list = self.feedback_snowflake_connection.execute_string(setup_query)
        for cursor in cursor_list:
            logging.info(f"Executed: {cursor.fetchall()}")

        feedback_df_schema = self.get_feedback_df_schema()

        self.feedback_snowflake_engine = init_snowflake_sql_engine(database_name,
                                                                   schema_name)

        with self.feedback_snowflake_engine.connect() as conn:
            res = feedback_df_schema.to_sql(index=False,
                                            name=table_name,
                                            con=conn,
                                            if_exists='append',
                                            method=pd_writer)

        logging.info(f"Initiated empty feedback form backend table at {database_name}.{schema_name}.{table_name}")

    def create_google_feedback_storage(self):
        spreadsheet, sh = self.get_spreadsheet()
        st.write(f"All feedback will be stored in {spreadsheet.url}")

    def create_feedback_storage(self):
        """Ensures that a feedback storage backend is created in line with the configuration if none is found
        No-op if feedback storage backend if found"""

        logging.info(f"Creating feedback form storage with method {self.config['feedback_form']['storage_method']}")

        if self.config['feedback_form']['storage_method'] == "local":
            self.create_local_feedback_storage()
        elif self.config['feedback_form']['storage_method'] == "snowflake":
            self.create_snowflake_feedback_storage()
        elif self.config['feedback_form']['storage_method'] == "google":
            self.create_google_feedback_storage()
        else:
            error_message = f"Unsupported feedback form storage method: {self.config['feedback_form']['storage_method']}"
            logging.error(error_message)
            raise (Exception(error_message))

    def delete_local_feedback_storage(self):
        feedback_path = self.get_feedback_path()
        if not (os.path.exists(feedback_path)):
            logging.info(f"Nothing found to delete at {feedback_path}")
        else:
            logging.info(f"Deleting all feedback from {feedback_path}")
            os.system(f"rm -rf {feedback_path}")
            logging.info(f"Deleted all feedback from {feedback_path}")

    def delete_snowflake_feedback_storage(self):
        database_name, schema_name, table_name = self.get_feedback_snowflake_path()
        delete_query = f"""
            DROP SCHEMA {database_name}.{schema_name}
        """
        with self.feedback_snowflake_connection.cursor() as cursor:
            cursor.execute(delete_query)
        self.feedback_snowflake_connection.close()
        logging.info(f"Deleted all feedback from {database_name}.{schema_name}")

    def delete_google_feedback_storage(self, worksheetname='User_Feedback'):
        spread, sh = self.get_spreadsheet()
        worksheet = sh.worksheet(worksheetname)
        df = pd.DataFrame(worksheet.get_all_records())
        df = df.iloc[:-1, :]
        worksheet.delete_rows(len(df) - 1, len(df))
        col = self.config['feedback_form']['schema'].keys()
        spread.df_to_sheet(df[col], sheet=worksheetname, index=False)

    def delete_feedback_storage(self):
        """Ensures that any available feedback storage backend has been deleted"""

        logging.info(f"Deleting feedback form storage with method {self.config['feedback_form']['storage_method']}")

        if self.config['feedback_form']['storage_method'] == "local":
            self.delete_local_feedback_storage()
        elif self.config['feedback_form']['storage_method'] == "snowflake":
            self.delete_snowflake_feedback_storage()
        elif self.config['feedback_form']['storage_method'] == "google":
            self.delete_google_feedback_storage()
        else:
            error_message = f"Unsupported feedback form storage method: {self.config['feedback_form']['storage_method']}"
            logging.error(error_message)

    def isValid(self, email):
        """
        Check if an email is valid or not.
        """
        regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
        return re.fullmatch(regex, email)

    def saved_to_local(self, df, feedback_storage_path):
        df_feed = pd.read_csv(feedback_storage_path)
        df_feed = pd.concat([df_feed, df])
        df_feed.to_csv(feedback_storage_path, index=False)

    def search_google_sheet(self, dataframe, worksheetname='User_Feedback'):
        _, sh = self.get_spreadsheet()
        worksheet = sh.worksheet(worksheetname)
        df = pd.DataFrame(worksheet.get_all_records())

        if (dataframe.iloc[0, :] == df.iloc[-1, :]).all() == True:
            test_check = True
        else:
            test_check = False
        return test_check

    def get_spreadsheet(self, worksheetname='User_Feedback'):
        if self.spreadsheet is None:
            # Create a Google Authentication connection object
            scope = ['https://spreadsheets.google.com/feeds',
                     'https://www.googleapis.com/auth/drive',
                     'https://www.googleapis.com/auth/spreadsheets'
                     ]

            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"], scopes=scope)
            client = Client(scope=scope, creds=credentials)

            spreadsheetname = "feedback"
            self.spreadsheet = Spread(spreadsheetname, client=client, sheet=worksheetname, create_sheet=True)
            # Check the connection
            self.worksheet = client.open(spreadsheetname)
            logging.info(f"Created a new connection to {self.spreadsheet.url}")

        return self.spreadsheet, self.worksheet

    def get_local_feedback(self):
        stored_feedback = pd.read_csv(self.get_feedback_file())
        return stored_feedback

    def get_snowflake_feedback(self):
        database_name, schema_name, table_name = self.get_feedback_snowflake_path()
        with self.feedback_snowflake_connection.cursor() as cur:
            cur.execute(f"SELECT * FROM {table_name.upper()}")
            stored_feedback = cur.fetch_pandas_all()
            return stored_feedback

    def get_feedback(self):
        if self.config['feedback_form']['storage_method'] == "local":
            return self.get_local_feedback()
        elif self.config['feedback_form']['storage_method'] == "snowflake":
            return self.get_snowflake_feedback()
        else:
            raise (
                Exception(
                    f"Unsupported option for feedback form storage: {self.config['feedback_form']['storage_method']}")
            )

    def save_local_feedback(self, feedback_form_df):
        stored_feedback = self.get_feedback()
        updated_feedback = pd.concat([stored_feedback, feedback_form_df])
        updated_feedback.to_csv(self.get_feedback_file(),
                                index=False)
        logging.info(f"Updated feedback saved to {self.get_feedback_file()} with shape {updated_feedback.shape}")

    def save_snowflake_feedback(self, feedback_form_df):
        database_name, schema_name, table_name = self.get_feedback_snowflake_path()
        success, num_chunks, num_rows, output = write_pandas(
            conn=self.feedback_snowflake_connection,
            df=feedback_form_df,
            table_name=table_name.upper(),
            database=database_name.upper(),
            schema=schema_name.upper()
        )
        updated_feedback = self.get_feedback()
        logging.info(f"Updated feedback saved to {database_name}.{schema_name}.{table_name}"
                     f" with shape {updated_feedback.shape}")

    def save_google_feedback(self, dataframe, worksheetname='User_Feedback'):
        spread, sh = self.get_spreadsheet()
        worksheet = sh.worksheet(worksheetname)
        df = pd.DataFrame(worksheet.get_all_records())
        df = pd.concat([df, dataframe])
        col = self.config['feedback_form']['schema'].keys()
        spread.df_to_sheet(df[col], sheet=worksheetname, index=False)
        return True

    def save_feedback(self, feedback_form_data):
        """Accepts feedback_form_data and submits it for saving in line with the configured storage method and
        path. Raises an exception if the configured method is not supported."""
        if "DATE" not in feedback_form_data:
            feedback_form_data['DATE'] = datetime.now().date().strftime("%Y/%m/%d")
        feedback_df = pd.DataFrame([feedback_form_data])
        feedback_schema_df = self.get_feedback_df_schema()
        feedback_df = pd.concat([feedback_schema_df,
                                 feedback_df])

        if self.config['feedback_form']['storage_method'] == "local":
            self.save_local_feedback(feedback_df)
        elif self.config['feedback_form']['storage_method'] == "snowflake":
            self.save_snowflake_feedback(feedback_df)
        elif self.config['feedback_form']['storage_method'] == "google":
            self.save_google_feedback(feedback_df)
        else:
            raise (Exception(
                f"Unsupported option for feedback form storage: {self.config['feedback_form']['storage_method']}"))

    def clean_google_sheet(self, spreadsheetname='User_Feedback'):

        spread, sh = self.get_spreadsheet()
        worksheet = sh.worksheet(spreadsheetname)
        df = pd.DataFrame(worksheet.get_all_records())
        df = df.iloc[:-1, :]
        worksheet.delete_rows(len(df) - 1, len(df))
        col = self.config['feedback_form']['schema'].keys()
        spread.df_to_sheet(df[col], sheet=spreadsheetname, index=False)

        return True

    # App specific logic

    def get_input_directory(self):
        return self.config['player_outcome_predictor']['historical_data']['input_directory']

    def get_tournament_file_name(self):
        return self.config['player_outcome_predictor']['historical_data']['tournament_file_name']

    def get_player_file_name(self):
        return self.config['player_outcome_predictor']['historical_data']['player_file_name']

    def get_rewards_info(self) -> (str, str, str):
        rewards_config = self.config['player_outcome_predictor']['rewards_configuration']
        return rewards_config["repo_path"], rewards_config["generated_path"], rewards_config["file_name"]

    def get_predictive_simulator_info(self) -> int:
        predictive_simulator = self.config['player_outcome_predictor']['predictive_simulator']
        return predictive_simulator["number_of_scenarios"]

    def get_tournament_simulator_info(self) -> (int, str, str):
        tournament_simulator = self.config['player_outcome_predictor']['tournament_simulator']
        data_path = tournament_simulator["data_path"]
        matches_file_name = f"{data_path}/{tournament_simulator['matches_file_name']}"
        playing_xi_file_name = f"{data_path}/{tournament_simulator['playing_xi_file_name']}"
        return tournament_simulator["number_of_scenarios"], matches_file_name, playing_xi_file_name

    def get_batter_runs_model_info(self) -> dict:
        batter_runs_config = self.config['player_outcome_predictor']['inferential_models']['batter_runs_model']
        if not os.path.isdir(batter_runs_config['model_directory_path']):
            os.makedirs(batter_runs_config['model_directory_path'])
        model_types = os.listdir(batter_runs_config['model_directory_path'])
        model_type_dict = dict()

        for model_type in model_types:
            model_type_path = f"{batter_runs_config['model_directory_path']}/{model_type}"
            model_type_dict[model_type] = os.listdir(model_type_path)
        ret = {
            'model_directory_path': batter_runs_config['model_directory_path'],
            'model_type_dict': model_type_dict
        }


        return ret

