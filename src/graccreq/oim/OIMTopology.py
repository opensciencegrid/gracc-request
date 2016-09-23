import xml.etree.ElementTree as ET
from datetime import timedelta, date
import urllib2
from os.path import exists
import re


# This could (and probably should) be moved to a config file
pathdictionary = {
    'Facility': '../../Facility/Name',
    'Site': '../../Site/Name',
    'ResourceGroup': '../../GroupName',
    'Resource': '/Name',
    'ID': '/ID',
    'FQDN': '/FQDN',
    'WLCGAccountingName': '/WLCGInformation/AccountingName'
}


class OIMTopology(object):
    """Class to hold and sort through relevant OIM Topology information"""
    def __init__(self):
        self.e = None
        self.root = None
        self.resourcepath = None

        self.xml_file = self.get_file_from_OIM()
        if self.xml_file:
            self.parse()

    def get_file_from_OIM(self):
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
        """Parses XML file using ElementTree.parse().  Also sets XML root for
        further processing"""
        try:
            self.e = ET.parse(self.xml_file)
            self.root = self.e.getroot()
            print "Parsed file"
        except Exception as e:
            print e
            print "Couldn't parse OIM file"
            self.xml_file = None
        return

    def get_information_by_resource(self, resourcename):
        """Gets the relevant information from the parsed OIM XML file based on
        the Resource Name.  Meant to be called after OIMTopology.parse().

        Arguments:
            resourcename (string) - Resource Name

        Returns: Dictionary that has relevant OIM information
        """
        if not self.xml_file:
            return {}

        # So we don't have to type this over and over again
        self.resourcepath = './ResourceGroup/Resources/Resource/[Name="{0}"]'\
            .format(resourcename)
        if self.root.find('{0}'.format(self.resourcepath)) is None:
            print "No Resource with that Name"
            return {}

        return self.get_resource_information()

    def get_information_by_fqdn(self, fqdn):
        """Gets the relevant information from the parsed OIM XML file based on
        the FQDN.  Meant to be called after OIMTopology.parse().

        Arguments:
            fqdn (string) - FQDN of the resource

        Returns: Dictionary that has relevant OIM information"""
        if not self.xml_file:
            return {}

        # So we don't have to type this over and over again
        self.resourcepath = './ResourceGroup/Resources/Resource/[FQDN="{0}"]'\
            .format(fqdn)
        if self.root.find('{0}'.format(self.resourcepath)) is None:
            self.resourcepath = './ResourceGroup/Resources/Resource/'\
                '[FQDNAliases="{0}"]'.format(fqdn)
        if self.root.find('{0}'.format(self.resourcepath)) is None:
            print "No Resource with that FQDN: {0}".format(fqdn)
            return {}

        return self.get_resource_information()

    def get_resource_information(self):
        """Uses parsed XML file and finds the relevant information based on the
        dictionary of XPaths.  Searches by resource.

        Global Variable:
            pathdictionary (dict):  Dictionary of keys : XPaths to find
                OIM information about those keys from parsed XML file

        Returns dictionary that has relevant OIM information
        """
        returndict = {}
        for key, path in pathdictionary.iteritems():
            searchpath = '{0}{1}'.format(self.resourcepath, path)
            try:
                returndict[key] = self.root.find(searchpath).text
            except AttributeError:
                # Skip this.  It means there's no information for this key
                pass

            # All information that requires a bit more scrubbing
            returndict['VOOwnership'] = self.get_VO_Ownership_by_resource()
            returndict['Contacts'] = self.get_Contact_Info_by_resource()

        return returndict

    def get_VO_Ownership_by_resource(self):
        """Using resource name and XPath, finds VOOwnership information from
        parsed XML file

        Returns dictionary in VO: Percentage format
        """
        ownershipdict = {}
        for elt in self.root.find('{0}/VOOwnership'.format(self.resourcepath))\
                .findall('Ownership'):
            ownershipdict[elt.find('VO').text] = float(elt.find('Percent')
                                                       .text)
        return ownershipdict

    def get_Contact_Info_by_resource(self):
        """Finds contact information of a resource by resource name and XPath
        from parsed XML file.

        Returns dictionary of contact information in format
        Name:{Email: 'email_address', ContactRank:'contact_rank'}
        """
        contactsdict = {}
        for elt in self.root.findall(
                '{0}/ContactLists/ContactList/'
                '[ContactType="Resource Report Contact"]/Contacts/Contact'
                .format(self.resourcepath)):
            contactsdict[elt.find('Name').text] = {}
            name = contactsdict[elt.find('Name').text]
            name['Email'] = None
            name['ContactRank'] = str(elt.find('ContactRank').text)

        return contactsdict

    def check_probe(self, doc):
        """Check to see if ProbeName key is in the gracc record

        Arguments:
            doc (a dictionary that represents a GRACC record

        Returns a dictionary with the pertinent OIM Topology info, or a blank
         dictionary if a match was not found
        """
        if 'ProbeName' in doc:
            probe_fqdn = re.match('.+:(.+)', doc['ProbeName']).group(1)
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

        if 'VOName' in doc:
            voname = doc['VOName']
            # Parse VOOwnership to determine opportunistic vs. dedicated
            if voname.lower() in [elt.lower()
                                  for elt in rawdict['VOOwnership'].keys()]:
                returndict['UsageModel'] = 'DEDICATED'
            else:
                returndict['UsageModel'] = 'OPPORTUNISTIC'
        else:
            returndict['UsageModel'] = 'UNKNOWN'

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
    print topology.generate_dict_for_gracc(testdoc)


if __name__ == '__main__':
    main()

