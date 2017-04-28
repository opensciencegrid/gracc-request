import xml.etree.ElementTree as ET
import urllib2
import logging
import re
from copy import deepcopy


VOURL = "https://myosg.grid.iu.edu/vosummary/xml?summary_attrs_showfield_of_science=on&all_vos=on&active=on&active_value=1&oasis_value=1&sort_key=name"

class OIMVOInfo(object):
    wanted_attributes = {'FieldsOfScience':{'PrimaryFields': 'Field', 'SecondaryFields': 'Field'}}
    vodict = {}

    def __init__(self):
        self.xmlfile = self.__get_oim_info()
        self.__get_vo_info()


    def __get_oim_info(self):
        try:
            oim_xml = urllib2.urlopen(VOURL)
        except (urllib2.HTTPError, urllib2.URLError) as e:
            logging.error(e)
            return None
        return oim_xml

    def __get_vo_info(self):
        pathattr = re.compile('.//.+/(\w+)/.+')

        root = ET.parse(self.xmlfile)
        root = root.getroot()

        for voelt in root:
            VOName = voelt.find('Name').text
            if VOName not in self.vodict:
                self.vodict[VOName] = {}
            cur_dict = self.vodict[VOName]

            xpath_list_raw = []

            def recurse_attrs(cur_level, curlist):
                if not isinstance(cur_level, dict):
                    curlist.append(cur_level)
                    xpath_list_raw.append(curlist)
                else:
                    for key in cur_level:
                        nowlist = deepcopy(curlist)
                        nowlist.append(key)
                        recurse_attrs(cur_level[key], nowlist)

            recurse_attrs(self.wanted_attributes, [])

            xpaths = []
            for pathlist in xpath_list_raw:
                path = './/' + '/'.join(pathlist)
                xpaths.append(path)


            for path in xpaths:
                m = pathattr.match(path)
                if m:
                    key = m.group(1)
                lst = []
                for elt in voelt.findall(path):
                    lst.append(elt.text)

                if len(lst) != 0:
                    cur_dict[key] = lst

        return

    def parse_doc(self):
        # Parse doc, if anything to update, then do it.
        pass


if __name__ == '__main__':
    x = OIMVOInfo()
    print x.vodict
