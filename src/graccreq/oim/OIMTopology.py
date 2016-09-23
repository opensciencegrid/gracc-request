import xml.etree.ElementTree as ET
from datetime import timedelta, date
import urllib2
import re


class OIMTopology(object):
    """Class to hold and sort through relevant OIM Topology information"""
    def __init__(self):
        self.e = None
        self.root = None
        self.resourcedict = {}

        self.xml_file = self.get_file_from_OIM()
        if self.xml_file:
            self.parse()

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
            print e
            return None

        return oim_xml

    def parse(self):
        """Parses XML file using ElementTree.parse().  Also builds dictionary
        of Resource Name :{resource information} format for future lookups"""
        try:
            self.e = ET.parse(self.xml_file)
            self.root = self.e.getroot()
            print "Parsing file"
        except Exception as e:
            print e
            print "Couldn't parse OIM file"
            self.xml_file = None
            return
        
        for resourcename_elt in self.root.findall('./ResourceGroup/'
                                                  'Resources/Resource/Name'):
            resourcename = resourcename_elt.text
            if resourcename not in self.resourcedict:
                resource_grouppath = './ResourceGroup/Resources/Resource/' \
                                     '[Name="{0}"]/../..'.format(resourcename)
                self.resourcedict[resourcename] = \
                    self.get_resource_information(resource_grouppath,
                                                  resourcename)

        return

    def get_resource_information(self, resource_grouppath, resourcename):
        """Uses parsed XML file and finds the relevant information based on the
        dictionary of XPaths.  Searches by resource.

        Arguments:
            resource_grouppath (string): XPath path to Resource Group
            Element to be parsed
            resourcename (string): Name of resource

        Returns dictionary that has relevant OIM information
        """

        # This could (and probably should) be moved to a config file
        rg_pathdictionary = {
            'Facility': './Facility/Name',
            'Site': './Site/Name',
            'ResourceGroup': './GroupName'}

        r_pathdictionary = {
            'Resource': './Name',
            'ID': './ID',
            'FQDN': './FQDN',
            'WLCGAccountingName': './WLCGInformation/AccountingName'
        }

        returndict = {}

        # Resource group-specific info
        resource_group_elt = self.root.find(resource_grouppath)
        for key, path in rg_pathdictionary.iteritems():
            try:

                returndict[key] = resource_group_elt.find(path).text
            except AttributeError:
                # Skip this.  It means there's no information for this key
                pass

        # Resource-specific info
        resource_elt = resource_group_elt.find(
            './Resources/Resource/[Name="{0}"]'.format(resourcename))
        for key, path in r_pathdictionary.iteritems():
            try:
                returndict[key] = resource_elt.find(path).text
            except AttributeError:
                # Skip this.  It means there's no information for this key
                pass

        # All information that requires a bit more scrubbing
        returndict['VOOwnership'] = \
            self.get_VO_Ownership_by_resource(resource_elt)
        returndict['Contacts'] = \
            self.get_Contact_Info_by_resource(resource_elt)

        return returndict

    @staticmethod
    def get_VO_Ownership_by_resource(elt):
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
    def get_Contact_Info_by_resource(elt):
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

    def get_information_by_resource(self, resourcename):
        """Gets the relevant information from the parsed OIM XML file based on
        the Resource Name.  Meant to be called after OIMTopology.parse().

        Arguments:
            resourcename (string) - Resource Name

        Returns: Dictionary that has relevant OIM information
        """
        if not self.xml_file:
            return {}
        
        if resourcename in self.resourcedict:
            return self.resourcedict[resourcename]
        else:
            return {}

    def get_information_by_fqdn(self, fqdn):
        """Gets the relevant information from the parsed OIM XML file based on
        the FQDN.  Meant to be called after OIMTopology.parse().

        Arguments:
            fqdn (string) - FQDN of the resource

        Returns: Dictionary that has relevant OIM information"""
        if not self.xml_file:
            return {}

        for resourcename, resourcedict in self.resourcedict.iteritems():
            if 'FQDN' in resourcedict:
                if resourcedict['FQDN'] == fqdn:
                    return resourcedict
        else:
            return {}

    def check_probe(self, doc):
        """Check to see if ProbeName key is in the gracc record

        Arguments:
            doc (a dictionary that represents a GRACC record

        Returns a dictionary with the pertinent OIM Topology info, or a blank
         dictionary if a match was not found
        """
        if 'ProbeName' in doc:
            probe_exp = re.compile('.+:(.+)')
            probe_fqdn = probe_exp.match(doc['ProbeName']).group(1)
            probeinfo = self.get_information_by_fqdn(probe_fqdn)
            if probeinfo:
                # Probe matching was successful
                return probeinfo
            else:
                return self.check_site(doc)
        else:
            # No ProbeName in record
            return self.check_site(doc)

    def check_site(self, doc):
        """Check to see if SiteName key is in the gracc record

        Arguments:
            doc (a dictionary that represents a GRACC record

        Returns a dictionary with the pertinent OIM Topology info, or a blank
         dictionary if a match was not found
        """
        if 'SiteName' in doc:
            rawsite = doc['SiteName']
            return self.get_information_by_resource(rawsite)
        else:
            # Neither SiteName nor ProbeName is in the record
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
        if not self.xml_file:
            return {}

        rawdict = self.check_probe(doc)

        if not rawdict:
            # None of the matches were successful
            return {}

        returndict = rawdict.copy()
        returndict['UsageModel'] = self.check_VO(doc, rawdict)

        # Delete unnecessary keys
        del returndict['Contacts']
        del returndict['VOOwnership']
        del returndict['ID']

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

