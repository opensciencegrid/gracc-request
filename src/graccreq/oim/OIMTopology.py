import xml.etree.ElementTree as ET
from datetime import timedelta, date
import urllib2
import re
import time
import os.path
import pickle
import filelock
import logging

SEC_IN_DAY = 86400
cachefile = '/tmp/resourcedict.pickle'
lockfile = '/tmp/lockfile_OIM_cache'
curtime = int(time.time())


class OIMTopology(object):
    """Class to hold and sort through relevant OIM Topology information"""
    def __init__(self):
        self.e = None
        self.root = None
        self.resourcedict = {}
        self.probe_exp = re.compile('.+:(.+)')
        self.have_info = False
        self.lockfile = lockfile
        self.cachelock = filelock.FileLock(self.lockfile)

        logging.info("Trying to read from cachefile")
        # Lock our cachefile, try to read from it
        with self.cachelock:
            logging.debug("Read lock acquired")
            assert self.cachelock.is_locked
            self.have_info = self.read_from_cache()
            logging.debug("Read lock released")
        assert not self.cachelock.is_locked

        # If that didn't work, get file from OIM, parse it, write to cache:
        if not self.have_info:
            logging.info(
                "Not reading from cache - getting fresh file from OIM")
            self.xml_file = self.get_file_from_OIM()
            if self.xml_file:
                self.parse()
                if self.resourcedict:
                    self.have_info = True
                    with self.cachelock:
                        logging.debug("Write lock")
                        assert self.cachelock.is_locked
                        self.write_to_cache()
                    logging.debug("Write lock released")
                    assert not self.cachelock.is_locked

    def read_from_cache(self):
        """Method to unpickle resourcedict from cache.
        Returns True on success, False otherwise"""
        # We check that the cachefile exists and is less than 1 day old
        if os.path.exists(cachefile):
            if curtime - int(os.path.getctime(cachefile)) < SEC_IN_DAY:
                try:
                    with open(cachefile, 'rb') as cache:
                        self.resourcedict = pickle.load(cache)
                    logging.info("Loaded from Cache")
                    return True
                except pickle.UnpicklingError:
                    logging.warn("Could not unpickle cache file")
            else:
                logging.info("Will not read from cache (cache file is too old)")
        else:
            logging.info("Cache file doesn't exist")
        return False

    def write_to_cache(self):
        """Method to pickle up the resourcedict into the cachefile.
        Returns True if successful, False if not."""
        try:
            with open(cachefile, 'wb') as cache:
                pickle.dump(self.resourcedict, cache)
            logging.info("Pickled new resource dict to Cache file")
            return True
        except pickle.PicklingError:
            logging.warn("Could not pickle new resource dict to Cache file")
            return False

    @staticmethod
    def get_file_from_OIM():
        """Gets a new file from OIM.  Passes in today's date"""
        today = date.today()
        startdate = today - timedelta(days=7)
        rawdateslist = [startdate.month, startdate.day, startdate.year,
                        today.month, today.day, today.year]
        dateslist = ['0' + str(elt) if len(str(elt)) == 1 else str(elt)
                     for elt in rawdateslist]

        oim_url = 'http://myosg.grid.iu.edu/rgsummary/xml?' \
                  'summary_attrs_showhierarchy=on&summary_attrs_showwlcg=on' \
                  '&summary_attrs_showservice=on&summary_attrs_showfqdn=on' \
                  '&summary_attrs_showvoownership=on' \
                  '&summary_attrs_showcontact=on' \
                  '&gip_status_attrs_showtestresults=on' \
                  '&downtime_attrs_showpast=&account_type=cumulative_hours' \
                  '&ce_account_type=gip_vo&se_account_type=vo_transfer_volume'\
                  '&bdiitree_type=total_jobs&bdii_object=service' \
                  '&bdii_server=is-osg&start_type=7daysago' \
                  '&start_date={0}%2F{1}%2F{2}&end_type=now' \
                  '&end_date={3}%2F{4}%2F{5}&all_resources=on' \
                  '&facility_sel%5B%5D=10009&gridtype=on&gridtype_1=on' \
                  '&active=on&active_value=1&disable_value=1' \
            .format(*dateslist)  # Take date into account to generate URL

        try:
            oim_xml = urllib2.urlopen(oim_url)
        except (urllib2.HTTPError, urllib2.URLError) as e:
            logging.warn(e)
            return None

        return oim_xml

    def parse(self):
        """Parses XML file using ElementTree.parse().  Also builds dictionary
        of Resource Name :{resource information} format for future lookups"""
        try:
            self.e = ET.parse(self.xml_file)
            self.root = self.e.getroot()
            logging.debug("Parsing OIM file")
        except Exception as e:
            logging.warn(e)
            logging.warn("Couldn't parse OIM file")
            self.have_info = False
            return

        # Look in all Resources
        for resourcename_elt in self.root.findall('./ResourceGroup/'
                                                  'Resources/Resource/Name'):
            resourcename = resourcename_elt.text
            if resourcename not in self.resourcedict:
                # Find the Resource Group Path that has the named resource
                resource_grouppath = './ResourceGroup/Resources/Resource/' \
                                     '[Name="{0}"]/../..'.format(resourcename)
                self.resourcedict[resourcename] = \
                    self.store_resource_information(resource_grouppath, resourcename)
        return

    def store_resource_information(self, resource_grouppath, resourcename):
        """Uses parsed XML file and finds the relevant information based on the
        dictionary of XPaths.  Searches by resource.

        Arguments:
            resource_grouppath (string): XPath path to Resource Group
            Element to be parsed
            resourcename (string): Name of resource

        Returns dictionary that has relevant OIM information
        """

        # This could (and probably should) be moved to a config file
        # XPaths for searches by Resource Group
        rg_pathdictionary = {
            'OIM_Facility': './Facility/Name',
            'OIM_Site': './Site/Name',
            'OIM_ResourceGroup': './GroupName'}

        # XPaths for searches by Resource
        r_pathdictionary = {
            'OIM_Resource': './Name',
            'OIM_ID': './ID',
            'OIM_FQDN': './FQDN',
            'OIM_WLCGAccountingName': './WLCGInformation/AccountingName',
            'OIM_WLCGAPELNormalFactor': './WLCGInformation/APELNormalFactor',
        }

        returndict = {}

        # Resource group-specific info
        resource_group_elt = self.root.find(resource_grouppath)
        # Resource-specific info
        resource_elt = resource_group_elt.find(
            './Resources/Resource/[Name="{0}"]'.format(resourcename))

        # Dictionary of Elements/Dict for Resource and Resource group.  Purely
        # to allow for easier iteration below
        eltdict = {"ResourceGroup":
                       {"Element": resource_group_elt, "Dict": rg_pathdictionary},
                   "Resource":
                       {"Element": resource_elt, "Dict": r_pathdictionary}
                   }

        for level, info in eltdict.iteritems():
            for key, path in info["Dict"].iteritems():
                try:
                    if key == 'OIM_WLCGAPELNormalFactor':
                        returndict[key] = float(info["Element"].find(path).text)
                    else:
                        returndict[key] = info["Element"].find(path).text
                except AttributeError:
                    # Skip this.  It means there's no information for this key
                    pass

        # All information that requires a bit more scrubbing
        returndict['VOOwnership'] = \
            self.store_VOOwnership_information(resource_elt)
        returndict['Contacts'] = \
            self.store_Contact_information(resource_elt)

        return returndict

    @staticmethod
    def store_VOOwnership_information(elt):
        """Using resource name and XPath, finds VOOwnership information from
        parsed XML file

        Arguments:
            elt:  ElementTree Element object (should be Resource Element)

        Returns dictionary in VO: Percentage format
        """
        ownershipdict = {}
        for el in elt.find('./VOOwnership').findall('Ownership'):
            ownershipdict[el.find('VO').text] = float(el.find('Percent').text)
        return ownershipdict

    @staticmethod
    def store_Contact_information(elt):
        """Finds contact information of a resource by resource name and XPath
        from parsed XML file.

        Arguments:
            elt:  ElementTree Element object (should be Resource Element)

        Returns dictionary of contact information in format
        Name:{Email: 'email_address', ContactRank:'contact_rank'}
        """
        contactsdict = {}
        for el in elt.findall('./ContactLists/ContactList/'
                              '[ContactType="Resource Report Contact"]'
                              '/Contacts/Contact'):
            contactsdict[el.find('Name').text] = {}
            name = contactsdict[el.find('Name').text]
            name['Email'] = None
            name['ContactRank'] = str(el.find('ContactRank').text)

        return contactsdict

    @staticmethod
    def add_matched_to(indict, level):
        """Add information to instance copy of resource dict that indicates
        at which level (resource, resource group, etc.) in the resource dict a
        GRACC entry was matched.

        For example, if we're matching the GRACC record to the resource dict
        Resource, this will add "Resource" as a value to the "OIM_Match" key

        Returns the dictionary indict with the added OIM_Match: value pair."""
        indict['OIM_Match'] = level
        return indict

    @staticmethod
    def add_matched_from(indict, level):
        """Similar to add_matched_to, this adds information to the instance
         copy of resource dict as to what field in the GRACC record was used
         to match.

         For example, if we use the Host_description from the GRACC record
         and match that to the Resource in the resource dict, this will set the
         value of OIM_Match to "Host_description-Resource"

         Returns the dictionary indict with the amended OIM_Match: value pair"""
        indict['OIM_Match'] = '{0}-{1}'.format(level, indict['OIM_Match'])
        return indict

    def get_information_by_resource(self, resourcename):
        """Gets the relevant information from the parsed OIM XML file based on
        the Resource Name.  Meant to be called after OIMTopology.parse().

        Arguments:
            resourcename (string) - Resource Name

        Returns: Dictionary that has relevant OIM information.

        Note:  We wrap the return statement in the self.add_matched_to call so
        that the dict returned has the OIM_Match field as well.
        """
        if not self.have_info:
            return {}
        
        if resourcename in self.resourcedict:
            return self.add_matched_to(self.resourcedict[resourcename],
                                       'Resource')
        else:
            return {}

    def get_information_by_fqdn(self, fqdn):
        """Gets the relevant information from the parsed OIM XML file based on
        the FQDN.  Meant to be called after OIMTopology.parse().

        Arguments:
            fqdn (string) - FQDN of the resource

        Returns: Dictionary that has relevant OIM information

        Note:  We wrap the return statement in the self.add_matched_to call so
        that the dict returned has the OIM_Match field as well.
        """
        if not self.have_info:
            return {}

        for resourcename, rdict in self.resourcedict.iteritems():
            if 'OIM_FQDN' in rdict and rdict['OIM_FQDN'] == fqdn:
                return self.add_matched_to(rdict, 'FQDN')
        else:
            return {}

    def get_information_by_site(self, sitename):
        """Gets the relevant information from the parsed OIM XML file based on
        the Site Name.  Meant to be called after OIMTopology.parse().

        Arguments:
            sitename (string) - Site Name

        Returns: Dictionary that has relevant OIM information

        Note:  We wrap the return statement in the self.add_matched_to call so
        that the dict returned has the OIM_Match field as well.
        """
        if not self.have_info:
            return {}

        returndict = {}
        for resourcename, rdict in self.resourcedict.iteritems():
            if 'OIM_Site' in rdict and rdict['OIM_Site'] == sitename:
                returndict['OIM_Site'] = rdict['OIM_Site']
                returndict['OIM_Facility'] = rdict['OIM_Facility']
        if returndict:
            return self.add_matched_to(returndict, 'Site')
        else:
            return {}

    def get_information_by_resourcegroup(self, rgname):
        """Gets the relevant information from the parsed OIM XML file based on
        the Resource Group Name.  Meant to be called after OIMTopology.parse().

        Arguments:
            rgname (string) - Resource Name

        Returns: Dictionary that has relevant OIM information

        Note:  We wrap the return statement in the self.add_matched_to call so
        that the dict returned has the OIM_Match field as well.
        """
        if not self.have_info:
            return {}

        returndict = {}
        for resourcename, rdict in self.resourcedict.iteritems():
            if 'OIM_ResourceGroup' in rdict and \
                            rdict['OIM_ResourceGroup'] == rgname:
                returndict['OIM_Site'] = rdict['OIM_Site']
                returndict['OIM_Facility'] = rdict['OIM_Facility']
                returndict['OIM_ResourceGroup'] = rdict['OIM_ResourceGroup']
        if returndict:
            return self.add_matched_to(returndict, 'ResourceGroup')
        else:
            return {}

    def check_hostdescription(self, doc):
        """Matches host description to resource name, site name, or resource
        group name (in that order)

        Arguments:
            doc (dict):  GRACC record

        Returns dictionary of relevant information to append to GRACC record
        """
        # Match host desc to resource name
        # if that fails, to site
        # if that fails, to resource group
        # if that fails, return {}

        returndict = self.get_information_by_resource(doc['Host_description'])
        if not returndict:
            returndict = self.get_information_by_site(doc['Host_description'])
        if not returndict:
            returndict = \
                self.get_information_by_resourcegroup(doc['Host_description'])

        if returndict:
            return self.add_matched_from(returndict, 'Host_description')
        else:
            return {}

    def check_probe(self, doc):
        """Gets information from OIM based on the probe name passed in

        Arguments:
            doc (a dictionary that represents a GRACC record

        Returns a dictionary with the pertinent OIM Topology info, or a blank
         dictionary if a match was not found
        """
        probe_fqdn_check = self.probe_exp.match(doc['ProbeName'])
        if probe_fqdn_check:
            probe_fqdn = probe_fqdn_check.group(1)
            returndict = self.get_information_by_fqdn(probe_fqdn)
            if returndict:
                return self.add_matched_from(returndict, 'ProbeName')
        else:
            return {}

    def check_site_to_resource(self, doc):
        """Note:  This matches on Gracc SiteName = OIM Resource Name!

        Arguments:
            doc (a dictionary that represents a GRACC record

        Returns a dictionary with the pertinent OIM Topology info, or a blank
         dictionary if a match was not found
        """
        returndict = self.get_information_by_resource(doc['SiteName'])
        if returndict:
            return self.add_matched_from(returndict, 'SiteName')
        else:
            return {}

    @staticmethod
    def check_VO(doc, rdict):
        """Checks the VOName of a GRACC record against the VOOwnership
        dictionary from OIM.

        Returns a string of 'DEDICATED', 'OPPORTUNISTIC', or 'UNKNOWN'
        """
        if 'VOName' in doc:
            voname = doc['VOName']
            # Parse VOOwnership to determine opportunistic vs. dedicated
            if voname.lower() in [elt.lower()
                                  for elt in rdict['VOOwnership'].keys()]:
                return 'DEDICATED'
            else:
                return 'OPPORTUNISTIC'
        else:
            return 'UNKNOWN'

    def generate_dict_for_gracc(self, doc):
        """Generates a dictionary for appending to GRACC records.  Based on
        the probe name or site name, we return a dictionary with the relevant
        OIM information, in the format that's ready to append to GRACC record

        Arguments:
            doc (dict): GRACC document (record)

        Returns dictionary containing OIM information to append to GRACC record
        """
        logging.info("Adding OIMTopology information")
        if not self.have_info:
            logging.debug("No OIM Topology information for this instance of"
                          "OIMTopology.  Returning no information")
            return {}

        rawdict = {}

        # Payload records should be matched on host description only
        if 'ResourceType' in doc and doc['ResourceType'] == 'Payload':
            logging.debug("Matching payload records on host description")
            rawdict = self.check_hostdescription(doc)

        # Otherwise, try to match by probe and then site
        else:
            if 'ProbeName' in doc:
                logging.debug("Trying to match by probe")
                rawdict = self.check_probe(doc)

            if not rawdict and 'SiteName' in doc:
                logging.debug("Trying to match by site")
                rawdict = self.check_site_to_resource(doc)

        # None of the matches were successful
        if not rawdict:
            return {}

        returndict = rawdict.copy()

        # Append VO Ownership info
        if 'VOOwnership' in returndict:
            returndict['OIM_UsageModel'] = self.check_VO(doc, rawdict)

        keys_to_delete = ['Contacts', 'VOOwnership', 'ID']
        # Delete unnecessary keys
        for key in keys_to_delete:
            if key in returndict:
                del returndict[key]

        return returndict


def main():
    # Mainly for testing.
    testdoc = {'SiteName': 'AGLT2_SL6', 'VOName': 'ATLAS',
               'ProbeName': 'condor:gate02.grid.umich.edu'}

    topology = OIMTopology()

    for i in range(50):
        print topology.generate_dict_for_gracc(testdoc)


if __name__ == '__main__':
    main()

