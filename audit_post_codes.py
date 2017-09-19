"""
The script was used to generate a set recording the number of occurances of each instance of postal code. 
This script takes in an OSM file, parses by XML tag, and scans for postal codes using addr:postcode format. 

I elected to have the data saved to a set (rather than an enumerated dictionary) since I really just want to scan
the data to make sure it looks good. If I saw gross abnormalities I would enumerate the instances to investigate,
but this turned out to be not necessary.
"""
import xml.etree.cElementTree as ET

OSMFILE = "sample.osm"

def is_post_code(elem):
    return (elem.attrib['k'] == "addr:postcode")


def post_codes_audit(osmfile):
    osm_file = open(osmfile, "r")
    post_code = set()
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_post_code(tag):
                    post_code.add(tag.attrib['v'])
    return post_code
    osm_file.close()


def test():
    post_codes = post_codes_audit(OSMFILE)
    print post_codes


if __name__ == '__main__':
    test()