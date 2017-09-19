"""
The script was used to generate a dictionary recording the number of occurances of each instance of 
street type. This script takes in an OSM file, parses by XML tag, and scans for street_types using a 
regular expression pattern to identify street_types.

Based on this dictionary, I created a comprehensive list of 'approved' street types. 

I also created a dictionary matching common street type mistakes to the appropriate 'approved' street type.
"""
import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

OSMFILE = "sample.osm"
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)


def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type in street_types:
            street_types[street_type] += 1
        else:
            street_types[street_type] = 1


def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")


def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types

street_types_dict = audit(OSMFILE)

def test():
    st_types = audit(OSMFILE)
    return st_types


if __name__ == '__main__':
    test()