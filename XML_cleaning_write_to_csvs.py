"""
I then added my cleaning function to a modified version of the code used in the case study to iterate over the 
XML data and write it to CSV files appropriate for the dictated schema.

"""

import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET

import cerberus

import schema

OSM_PATH = "san_francisco_california.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

# the approved names and mapping for un-approved names
approved_list = ['Boulevard', 'Court', 'Bridgeway','Way','Circle','Alameda','Highway','Real','Embarcadero','Path','Lane','Center','Plaza','Drive','Place','Parkway','Gardens','Road','Square','Alley','Walk','Street','Terrace','Broadway','Avenue']

type_mapping_dict = {'Ave': 'Avenue',
 'Ave.': 'Avenue',
 'Blvd': 'Boulevard',
 'Blvd.': 'Boulevard',
 'Dr': 'Drive',
 'Dr.': 'Drive',
 'Plz': 'Plaza',
 'Plz.': 'Plaza',
 'Rd': 'Road',
 'Rd.': 'Road',
 'St': 'Street',
 'St.': 'Street',
 'avenue': 'Avenue',
 'boulevard': 'Boulevard',
 'drive': 'Drive',
 'plaza': 'Plaza',
 'road': 'Road',
 'street': 'Street'}

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

def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    # YOUR CODE HERE
    return_dict = {}

    for the_tag in element.iter("tag"):
        
        v_value = the_tag.attrib['v']
        
        if is_street_name(the_tag):
            v_value = clean_street_name(the_tag.attrib['v'])
            
            if not v_value:
                continue
        
        second_tags = {}
        second_tags['id'] = element.attrib['id']
        second_tags['key'] = the_tag.attrib['k']
        second_tags['value'] = v_value

        if ':' in the_tag.attrib['k']:
            second_tags['type'] = the_tag.attrib['k'].split(':',1)[0]
            second_tags['key'] = the_tag.attrib['k'].split(':',1)[1]
        else:
            second_tags['type'] = 'regular'

        tags.append(second_tags)
    
    if element.tag == 'node':
        for x in element.attrib:
            if x in NODE_FIELDS:
                node_attribs[x] = element.attrib[x]
        
        return_dict['node'] = node_attribs
        return_dict['node_tags'] = tags
    
    elif element.tag == 'way':
        for x in element.attrib:
            if x in WAY_FIELDS:
                way_attribs[x] = element.attrib[x]
        
        i=0
        
        return_dict['way'] = way_attribs
        
        for the_nd in element.iter("nd"):
            second_way_tags = {}
            second_way_tags['id'] = element.attrib['id']
            second_way_tags['node_id'] = the_nd.attrib['ref']
            second_way_tags['position'] = i
            i +=1
                
            way_nodes.append(second_way_tags)
        
        return_dict['way_nodes'] = way_nodes
        return_dict['way_tags'] = tags

    
    return return_dict    

# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=False)
