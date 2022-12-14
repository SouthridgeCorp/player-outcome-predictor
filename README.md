# player-outcome-predictor
Predictive modeling to forecast player outcomes over a T20 tournament

# Video Walkthrough of v1.0
- https://www.loom.com/share/c4e6488e34ab4e1b9c9c3990e3c304cb

- Note - pre-trained models for 2022 Int'l T20s can be found [here](https://drive.google.com/drive/folders/1TH2U8_VzX888XBz3N_EqNxsdrYg9MYJG)
- Also refer to README_Performance_Report_v1.0.md

## Getting the data ready
Before running the app, input data must be prepared: 
- Run `scripts/helpers/parse_cricsheet_inputs.py`
- The `parse_cricsheet_inputs.py` script parses T20 match information from cricsheet and generates the datasets to be 
used by the predictor app  This script converts `scripts/helpers/resources/IPLMatches.csv` to a format which is acceptable by the app
- The output of the script is a csv list of the matches we know about and a list of tournaments we know about
- For detailed instructions on how to run the script and its expected inputs & outputs, please refer to 
`scripts/helpers/README_parse_cricsheet_inputs.md`

### Setting up configuration for a deployment
#### Config.toml
* The app expects all config variables to be present in `./.streamlit/config.toml`.  
* If saving feedback in local files, copy `config.local.toml` to `./.streamlit/config.toml` 
before further customisations
* If saving feedback in snowflake, copy `config.snowflake.toml` to `./.streamlit/config.toml` before further customisations.
(Snowflake will require additional credentials for logging in - see Secrets section below)
* If saving feedback in Google drive, copy `config.google.toml` to `./.streamlit/config.toml` before further 
customisation. Please also setup your secrets for Google as defined below.

#### Secrets.toml
IMPORTANT: Credentials in Secrets must never be checked in and always maintained as local edits

##### For Local Feedback
Please touch `.streamlit/secrets.toml` (but can leave it blank)

##### For Google

You can directly read from the [link](https://docs.streamlit.io/knowledge-base/tutorials/databases/private-gsheet) or read below:
- Create a google cloud account to access google sheets programmatically.
- Select or create a project if asked.
- Head over APIs & Services dashboard. Search Google Sheets API and enable it.
- Go to the Service Accounts page and create an account with the Viewer permission.
- First, note down the email address of the account you just created (important for next step!)
- Then, create a JSON key file for the new account and download it. We will need this json file to populate the contents of the secrets.toml file.
- Create .streamlit/secrets.toml in your app's root directory.
Content of the file should be like below. You should fill the following contents with the information contained in the json file.

```
# .streamlit/secrets.toml

private_gsheets_url = "https://docs.google.com/spreadsheets/d/12345/edit?usp=sharing"

[gcp_service_account]
type = "service_account"
project_id = "xxx"
private_key_id = "xxx"
private_key = "xxx"
client_email = "xxx"
client_id = "xxx"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "xxx"
```

##### For Snowflake
Contact Gireesh to configure Snowflake access


## Setting up the virtual environment using docker
 - Install docker-engine and docker-compose on your system from [here](https://docs.docker.com/engine/install/).
 - Open a terminal, move to the project root directory and run `docker pull python` to download a python image from the dockerhub.

## Run the streamlit application locally with docker
   - Run `docker-compose up` to build a docker image and start the container locally.
     - This command assumes port 8501 is not in use.
   - Open [localhost:8501](localhost:8501) in your browser.
   
## Run the streamlit application locally without docker
 - `streamlit run app.py` from the repository root 

### Host the streamlit application externally
* Follow the instruction on https://share.streamlit.io/deploy
* Currently only deployments from main seem to work
* Contact gireesh if you are unable to get access

### Retrieve and investigate available feedback

* Depends on the storage method. Check test/test_utils/test_config_utils.py to understand how feedback files are stored
depending on the configured storage method
* Two storage methods are currently supported: Local and Snowflake
* Contact gireesh if you need access to snowflake

### Repo Structure
```
project
???   README.md [technical readme for this repo]
???   working_backwards.md [working backwards questions for the product]
???   press_release.md [press release for the product]
???   faq.md [faq for the product]
???   requirements.txt [python library dependecies for this repo]
???   app.py [streamlit app for this repo]
???   
????????????.FDm [sample toml files which can be used to configure the app]   
???   
????????????data [ignored by git, repo for data generated by the app]   
???   
????????????resources [version controlled data folder]
???   ????????????test [folder to locate data for test cases]
???   ????????????working_backwards [folder with content to be served for working backwards]
???   ????????????press_release [folder with content to be served for press_relase]
???   ????????????faq [folder with content to be served for faq]
???   ????????????computational_model [folder with content to be served for computational model]
???   ????????????architecture_hypothesis [folder with content to be served for architecture_hypothesis] 
???   
????????????pages [python module for hosting all pages of the streamlit application]
    ???   1_????_About.py [serves resources/press_release]
    ???   2_????_Data_Selection.py 
    ???   3_????_Configure_Sportiqo_Rewards.py
    ???   4_????_Review_Perfect_Simulation.py
    ???   5_????_Review_Inferential_Models.py
    ???   6_????_Review_Predictive_Simulations.py
    ???   7_????_Simulate_Tournament.py
    ???   8_????_FAQ.py [serves resources/faq and resources/working_backwards]
    ???   9_????_Architecture_Hypothesis.py [serves resources/architecture_hypothesis]
    ???   10_????_Computational_Model.py [serves resources/computational_model]
    ???   11_????_Feedback.py [serves page to collect feedback]
???   
????????????historical_data [python module for serving historical_data]
????????????data_selection [python module for serving data_selections]
????????????rewards_configuration [python module for configuring rewards formula]
????????????simulators [python module for simulators]
    ????????????perfect_simulator [python module for perfect simulator]
    ????????????predictive_simulator [python module for predictive simulator]
    ????????????tournament_simulator [python module for tournament simulator]
????????????inferential_models [python module for inferential models]
    ????????????bowling_outcomes_models [python module for inferential models that classify bowling_outcomes]
        ????????????first_innings_by_ball_model [python module for inferential models that operate on the first innings at the ball resolution]
        ????????????second_innings_by_ball_model [python module for inferential models that operate on the second innings at the ball resolution]
???   
????????????utils [python module for serving configuration from schemas]
    ???   graph_utils.py [utility functions for rendering mermaid graphs]
    ???   page_utils.py [utility functions for rendering streamlit tab pages]
    ???   config_utils.py [business logic for the module]
???   
????????????test [python module with all test cases]
```

## Running Tests
`pytest test`

