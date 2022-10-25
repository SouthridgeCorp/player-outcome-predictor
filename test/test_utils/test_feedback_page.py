import pandas as pd

from utils.config_utils import ConfigUtils
from datetime import datetime

utils_obj = ConfigUtils("./resources/test/utils/config_utils/test_cases.google.toml")

now = datetime.now()
date = now.date()
current_time = now.strftime('%H:%M:%S')
datetime_val = str(date) + '/' + str(current_time)

data = {
    "DATE": datetime_val,
    "USER_NAME": ["Alison"],
    "USER_EMAIL": ["alison@gmail.com"],
    "USER_PERSONA": ["target user val"],
    "ALTERNATE_USER_PERSONA": ["alternate target val"],
    "QUESTIONS": ["questions val"],
    "PAGE_NAME": ["name of the page where the feedback component lives"]
}
df = pd.DataFrame(data)


def test_save_to_drive():
    utils_obj.save_google_feedback(df)
    test_result = utils_obj.search_google_sheet(df)
    utils_obj.clean_google_sheet()

    assert test_result
