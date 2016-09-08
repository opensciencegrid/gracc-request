import urllib2
import xml.etree.ElementTree

class OIMProjects(object):
    
    oim_url = "http://myosg.grid.iu.edu/miscproject/xml?count_sg_1&count_active=on&count_enabled=on"
    
    def __init__(self):
        """
        This is where you would create the cache of the projects
        """
        
        # Get the Project information
        oim_xml = urllib2.urlopen(oim_url)
        _processProjects(oim_xml)
        
        
        
    def _processProjects(self, oim_xml):
        
        root = ET.fromstring(country_data_as_string)
        
        
    def parseDoc(self, doc):
        """
        Parse a record from GRACC, and return new records that should be appended
        
        :param dict doc: A dictionary of the record.
        :return dict: A new dictionary that has attributes that should be appended to the doc
        """
        newDoc = {}
        return newDoc

