import toml

def get_test_cases(target_module,test_class):
    """Loads all test case definitions which are relevant to the target_module and returns them as a list"""

    ## TODO: Replace test_cases.toml with test_cases.snowflake.toml when we are ready
    test_cases = toml.load(f'resources/test/{target_module}/test_cases.toml')

    selected_test_cases = [tc for tc in test_cases['test_case'] if tc['test_class']==test_class]
    return selected_test_cases