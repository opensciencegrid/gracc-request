import urllib.request, urllib.error, urllib.parse
import xml.etree.ElementTree as ET

class OIMProjects(object):
    
    oim_url = "https://topology.opensciencegrid.org/miscproject/xml?count_sg_1&count_active=on&count_enabled=on"
    
    wanted_attributes = ['Name', 'PIName', 'Organization', 'Department', 'FieldOfScience']
    
    def __init__(self, url=None):
        """
        This is where you would create the cache of the projects
        """
        
        self.dict_name = {}

        if url is not None:
            self.oim_url = url

        # Get the Project information
        header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36' }
        req = urllib.request.Request(self.oim_url, headers=header)
        oim_xml = urllib.request.urlopen(req)
        self._processProjects(oim_xml)
        
        
        
    def _processProjects(self, oim_xml):
        
        # Parse the XML from OIM
        root = ET.parse(oim_xml)
        real_root = root.getroot()
        
        # For each project in the root tag
        for element in real_root:
            new_dict = {}
            # For each element describing the project
            for ele in list(element):
                if ele.tag not in self.wanted_attributes:
                    continue
                newtag = 'OIM_{0}'.format(ele.tag)
                # Add OIM to ele.tag string
                new_dict[newtag] = ele.text
            # Here, make 'Name' 'OIM_Name'
            if 'OIM_Name' in new_dict:
                self.dict_name[new_dict['OIM_Name'].lower()] = new_dict
                del new_dict['OIM_Name']
        
    def parseDoc(self, doc):
        """
        Parse a record from GRACC, and return new records that should be appended
        
        :param dict doc: A dictionary of the record.
        :return dict: A new dictionary that has attributes that should be appended to the doc
        """
        # Well this is easy!
        if 'ProjectName' in doc and doc['ProjectName'].lower() in self.dict_name:
            return self.dict_name[doc['ProjectName'].lower()]
        else:
            return {}
        
        

