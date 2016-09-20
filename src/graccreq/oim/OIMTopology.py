import xml.etree.ElementTree as ET
from datetime import timedelta, date
import urllib2
from os.path import exists
import re


cachefile = '/var/tmp/resource_group.xml'
# cachefile = '/private/etc/resource_group.xml'

testdoc_op = {'SiteName': 'AGLT2_SL6', 'VOName': 'Fermilab',
           'ProbeName': 'condor:gate02.grid.umich.edu'}  # Should be opportunistic
testdoc_ded= {'SiteName': 'AGLT2_SL6', 'VOName': 'ATLAS',
           'ProbeName':'condor:gate02.grid.umich.edu'}  # Should be dedicated

testdoc_fail_probe = {'SiteName': 'AGLT2_SL6', 'VOName': 'Fermilab',
           'ProbeName': 'condor:gate02.grid.umich.edu1231231'}  # Should return {}


testdoc_fail = {'SiteName': 'AGLT2_SL6123123123', 'VOName': 'Fermilab',
           'ProbeName': 'condor:gate02.grid.umich.edu1231231'}  # Should return {}


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
    def __init__(self, newfile=True):
        self.xml_file = None
        self.e = None
        self.root = None
        self.resourcepath = None

        if newfile:
            self.get_file_from_OIM()
            self.parse()
        else:
            print "Not attempting to get new file.  Will run from cached file"
            self.set_xml_to_cache()
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
            oim_xml_url = urllib2.urlopen(oim_url)
            try:
                self.cache_file(oim_xml_url)
                print "Got new file and cached it"
            except Exception:
                print "Couldn't cache file"
                self.xml_file = None
        except (urllib2.HTTPError, urllib2.URLError) as e:
            print e
            print "Couldn't download file.  Will try running this " \
                  "from cached file" \
                  " at {}".format(cachefile)
            self.set_xml_to_cache()

        return

    def cache_file(self, url):
        """Writes opened urllib2.urlopen object to cache file path specified in
        global variable cachefile

        Arguments:
            url (urllib2.urlopen object) - URL to read from
        """
        with open(cachefile, 'w') as f:
            f.write(url.read())
        self.xml_file = cachefile
        return

    def set_xml_to_cache(self):
        """Set self.xml_file variable to the cache file path, if it exists"""
        if exists(cachefile):
            self.xml_file = cachefile
        else:
            print "There is no cache file"
            self.xml_file = None
        return

    def parse(self):
        """Parses XML file using ElementTree.parse().  Also sets XML root for
        further processing"""
        if self.xml_file:
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

    def generate_dict_for_gracc(self, doc):
        """Generates a dictionary for appending to GRACC records.  Based on
        the probe name or site name, we return a dictionary with the relevant
        OIM information, in the format that's ready to append to GRACC record

        Arguments:
            doc (dict): GRACC document (record)

        Returns dictionary containing OIM information to append to GRACC record
        """
        probe_fqdn = re.match('.+:(.+)', doc['ProbeName']).group(1)
        voname = doc['VOName']
        rawsite = doc['SiteName']

        rawdict = self.get_information_by_fqdn(probe_fqdn)
        # If match by fqdn doesn't work, the other mode we should try is
        # matching OIM resource group to gracc record SiteName.  I've noticed
        # this to be the case a number of times
        if not rawdict:
            print "Trying match by SiteName to Resource"
            rawdict = self.get_information_by_resource(rawsite)
        if not rawdict:
            return {}   # If it still doesn't work, return a blank dictionary
        returndict = rawdict.copy()

        # Parse VOOwnership to determine opportunistic vs. dedicated
        if voname.lower() in [elt.lower()
                              for elt in rawdict['VOOwnership'].keys()]:
            returndict['UsageModel'] = 'DEDICATED'
        else:
            returndict['UsageModel'] = 'OPPORTUNISTIC'

        # Delete unnecessary keys
        del returndict['Contacts']
        del returndict['VOOwnership']

        return returndict



def main():
    # Mainly for testing.  Note:  testdoc is a global variable at the top
    topology = OIMTopology(newfile=True)
    print topology.get_information_by_fqdn('fifebatch1.fnal.gov')
    print topology.get_information_by_resource('AGLT2_SL6')
    topology2 = OIMTopology(newfile=False)
    print topology2.get_information_by_fqdn('fifebatch2.fnal.gov')

    # GRACC functions
    print topology.generate_dict_for_gracc(testdoc_ded)
    print topology.generate_dict_for_gracc(testdoc_op)
    print topology.generate_dict_for_gracc(testdoc_fail_probe)
    print topology.generate_dict_for_gracc(testdoc_fail)


if __name__ == '__main__':
    main()

