import xml.etree.ElementTree as ET
from datetime import timedelta, date
import urllib2
from os.path import exists


cachefile = '/var/tmp/resource_group.xml'
#cachefile = '/private/etc/resource_group.xml'


class OIMTopology(object):
    """Class to hold and sort through relevant OIM Topology information"""
    def __init__(self, newfile=True):
        if newfile:
            self.get_file_from_OIM()
            self.parse()
        else:
            print "Not attempting to get new file.  Will run from cached file"
            self.set_xml_to_cache()
            self.parse()

    def get_file_from_OIM(self):
        today = date.today()
        startdate = today - timedelta(days=7)
        rawdateslist = [startdate.month, startdate.day, startdate.year,
                        today.month, today.day, today.year]
        dateslist = ['0' + str(elt) if len(str(elt)) == 1 else str(elt)
                     for elt in rawdateslist]

        OIM_url = 'http://myosg.grid.iu.edu/rgsummary/xml?' \
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
            .format(*dateslist)  # Take into account to generate URL

        try:
            oim_xml = urllib2.urlopen(OIM_url)
            try:
                self.cache_file(oim_xml)
                print "Got new file and cached it"
            except:
                print "Couldn't cache file"
                self.xml_file = False
        except (urllib2.HTTPError, urllib2.URLError) as e:
            print e
            print "Couldn't download file.  Will try running this " \
                  "from cached file" \
                  " at {}".format(cachefile)
            self.set_xml_to_cache()

        return

    def cache_file(self, file):
        with open(cachefile, 'w') as f:
            f.write(file.read())
        self.xml_file = cachefile
        return

    def set_xml_to_cache(self):
        if exists(cachefile):
            self.xml_file = cachefile
        else:
            print "There is no cache file"
            self.xml_file = False
        return

    def parse(self):
        if self.xml_file:
            try:
                self.e = ET.parse(self.xml_file)
                self.root = self.e.getroot()
                print "Parsed file"
            except Exception as e:
                print e
                print "Couldn't parse OIM file"
                self.xml_file = False
        return

    def get_information_by_resource(self, resourcename):
        """Does the same as the get_information_by_resource but doesn't use the
        topology classes at all.  Returns the dict of information we need from
        the OIM topology file"""

        returndict = {}
        if not self.xml_file:
            return returndict
        # So we don't have to type this over and over again
        self.resourcepath = './ResourceGroup/Resources/Resource/[Name="{0}"]'\
            .format(resourcename)

        # All information that will be simple key:value pairs in our dictionary
        returndict['Facility'] = \
            self.root.find('{0}../../Facility/Name'.format(self.resourcepath))\
                .text
        returndict['Site'] = \
            self.root.find('{0}../../Site/Name'.format(self.resourcepath)).text
        returndict['ResourceGroup'] = \
            self.root.find('{0}../../GroupName'.format(self.resourcepath)).text
        returndict['Resource'] = \
            self.root.find('{0}/Name'.format(self.resourcepath)).text
        returndict['ID'] = \
            self.root.find('{0}/ID'.format(self.resourcepath)).text
        returndict['FQDN'] = \
            self.root.find('{0}/FQDN'.format(self.resourcepath)).text
        returndict['WLCGAccountingName'] = \
            self.root.find('{0}/WLCGInformation/AccountingName'.format(
                self.resourcepath)).text

        # All information that requires a bit more scrubbing
        returndict['VOOwnership'] = self.get_VO_Ownership()     # VO Ownership
        returndict['Contacts'] = self.get_Contact_Info()  # Contact Information

        return returndict

    def get_VO_Ownership(self):
        ownershipdict = {}
        for elt in self.root.find('{0}/VOOwnership'.format(self.resourcepath))\
                .findall('Ownership'):
            ownershipdict[elt.find('VO').text] = float(elt.find('Percent')
                                                       .text)
        return ownershipdict

    def get_Contact_Info(self):
        contactsdict = {}
        for elt in self.root.findall(
                '{0}/ContactLists/ContactList/'
                '[ContactType="Resource Report Contact"]/Contacts/Contact'\
                        .format(self.resourcepath)):
            contactsdict[elt.find('Name').text] = {}
            name = contactsdict[elt.find('Name').text]
            name['Email'] = None
            name['ContactRank'] = str(elt.find('ContactRank').text)
        return contactsdict

    def generate_dict_for_gracc(self, doc):
        resourcename = doc['SiteName']
        voname = doc['VOName']
        rawdict = self.get_information_by_resource(resourcename)
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
    topology = OIMTopology(newfile=True)
#    print topology.get_information_by_resource('AGLT2_SL6')
#    topology2 = OIMTopology(newfile=False)
#    print topology2.get_information_by_resource('AGLT2_SL6')
    doc = {'SiteName':'AGLT2_SL6', 'VOName': 'Fermilab'}
    print topology.generate_dict_for_gracc(doc)


if __name__ == '__main__':
    main()

