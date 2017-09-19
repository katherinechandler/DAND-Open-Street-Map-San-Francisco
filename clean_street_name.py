'''
This function checks if street_name is in the approved values list; if it is not, it will check if it is in the mapping dictionary and change to the approved name. If the street_name doesn't appear in either data source, the line will not be saved to the output.
'''

def clean_street_name(street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type in approved_list:
            return street_name
        elif street_type in type_mapping_dict:
            return street_name.replace(street_type, type_mapping_dict[street_type])
        else:
            return None