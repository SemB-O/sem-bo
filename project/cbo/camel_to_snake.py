import re

def get_snake_case_table_name(name):
    clean_name = name.split('.')[0]
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', clean_name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()