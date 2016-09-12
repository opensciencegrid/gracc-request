from xml.dom import minidom
from ast import literal_eval


class Facility(object):
    """Facility class to hold information about facilities"""
    def __init__(self, name):
        self.name = name
        self.id = 0
        self.sites = {}
        self.facility = {}

    def parse(self, parent_elt):
        """Grabs the facility ID from the XML element passed in from outside the class"""
        facilityelt = parent_elt.getElementsByTagName('Facility')[0]
        self.id = int(facilityelt.getElementsByTagName('ID')[0].firstChild.data)
        return

    def build_dict(self):
        """Builds and returns the facility dictionary of form {'Name': <name>, 'ID': <ID>,
        'Sites': <sites dictionary>}"""
        self.facility['Name'] = self.name
        self.facility['ID'] = self.id
        self.facility['Sites'] = self.sites
        return self.facility


class Site(object):
    """Site class to hold information at the site level"""
    def __init__(self, name):
        self.name = name
        self.id = 0
        self.resourcegroups = {}
        self.supportcenter = {}
        self.site = {}

    def parse(self, parent_elt):
        """Gets the site ID, Support Center information from the XML element passed in"""
        siteelt = parent_elt.getElementsByTagName('Site')[0]
        self.id = int(siteelt.getElementsByTagName('ID')[0].firstChild.data)
        self.supportcenter = self.get_support_center_dict(parent_elt)
        return

    def get_support_center_dict(self, parent_elt):
        """Parses the XML element passed in to generate and return a dictionary of Support Center information.  The
        format is {'Name':<name>, 'ID':<ID>}"""
        self.supportcenter = {}
        supportcenterelt = parent_elt.getElementsByTagName('SupportCenter')[0]
        supportcentername = supportcenterelt.getElementsByTagName('Name')[0].firstChild.data
        supportcenterid = supportcenterelt.getElementsByTagName('ID')[0].firstChild.data
        self.supportcenter['Name'] = supportcentername
        self.supportcenter['ID'] = supportcenterid
        return self.supportcenter

    def build_dict(self):
        """Builds and returns the site dictionary.  The format is {'Name':<name>, 'ID': <id>,
        'SupportCenter': {<support center dictionary>}, 'ResourceGroups': {<Resource Groups Dictionary>}}"""
        self.site['Name'] = self.name
        self.site['ID'] = self.id
        self.site['SupportCenter'] = self.supportcenter
        self.site['ResourceGroups'] = self.resourcegroups
        return self.site


class ResourceGroup(object):
    """Class to hold the Resource Group-level information"""
    def __init__(self, name):
        self.name = name
        self.id = 0
        self.resources = {}
        self.rg = {}

    def parse(self, parent_elt):
        """Grabs the Resource Group ID from the XML element passed in"""
        self.id = parent_elt.getElementsByTagName('GroupID')[0].firstChild.data
        return

    def build_dict(self):
        """Builds and returns the Resource Group dictionary.  The format is {'Name':<name>, 'ID':<id>, 'Resources':
        {<Resources Dictionary>}}"""
        self.rg['Name'] = self.name
        self.rg['ID'] = self.id
        self.rg['Resources'] = self.resources
        return self.rg


class Resource(object):
    """Class to hold the resource-level information"""
    def __init__(self, name):
        self.name = name
        self.id = 0
        self.fqdn = ''
        self.resource = {}

    def parse(self, parent_elt):
        """Grabs the Resource ID, FQDN, VO Ownership information, WLCG information, and Contacts from the XML element
        passed in"""
        self.id = parent_elt.getElementsByTagName('ID')[0].firstChild.data
        self.fqdn = parent_elt.getElementsByTagName('FQDN')[0].firstChild.data
        self.resource['VOOwnership'] = self.get_vo_ownership_dict(parent_elt)
        self.resource['WLCG'] = self.get_wlcg_info(parent_elt)
        self.resource['Contacts'] = self.get_contact_info(parent_elt)
        return

    def get_vo_ownership_dict(self, parent_elt):
        """Generates and returns the VO Ownership dictionary from the XML element passed in.  The format is {<first_VO:
        <ownership>, <second_vo>:<ownership>, etc}"""
        self.vo_ownership = {}
        ownershiplist = parent_elt.getElementsByTagName('VOOwnership')[0].getElementsByTagName('Ownership')
        for ownership in ownershiplist:
            self.vo_ownership[str(ownership.getElementsByTagName('VO')[0].firstChild.data)] = float(
                ownership.getElementsByTagName('Percent')[0].firstChild.data)
        return self.vo_ownership

    def get_wlcg_info(self, parent_elt):
        """Generates and returns the WLCG information dictionary from the XML element passed in.  The format is
        {'Available': <True/False>, 'AccountingName':<accountingname>}"""
        self.wlcg = {}
        wlcgelt = parent_elt.getElementsByTagName('WLCGInformation')[0]
        if wlcgelt.firstChild.nodeValue == "(Information not available)":
            self.wlcg['Available'] = False
        else:
            self.wlcg['Available'] = True
            try:
                self.wlcg['AccountingName'] = str(wlcgelt.getElementsByTagName('AccountingName')[0].firstChild.data)
            except AttributeError:
                self.wlcg['AccountingName'] = None
        return self.wlcg

    def get_contact_info(self, parent_elt):
        """Generates and returns the contacts information for each resource.  The format is {'Name1': {'Email': <None
        for now>, 'ContactRank': <rank>}, 'Name2': 'Email': <None for now>, 'ContactRank':<rank>}, etc.}"""
        self.contacts = {}
        contactlistselt = parent_elt.getElementsByTagName('ContactLists')[0]

        clelt_list = contactlistselt.getElementsByTagName('ContactList')
        for clelt in clelt_list:
            # We only care about the Resource Report Contact list
            if clelt.getElementsByTagName('ContactType')[0].firstChild.data == 'Resource Report Contact':
                contactselt = clelt.getElementsByTagName('Contacts')[0]
                celts = contactselt.getElementsByTagName('Contact')

                for celt in celts:
                    name = celt.getElementsByTagName('Name')[0].firstChild.data
                    self.contacts[name] = {}
                    contact = self.contacts[name]

                    contact['Email'] = None
                    contact['ContactRank'] = str(celt.getElementsByTagName('ContactRank')[0].firstChild.data)

        return self.contacts

    def build_dict(self):
        """Generates and returns Resource dictionary.  Format is {'Name': <name>, 'ID': <id>, 'FQDN': <fqdn>,
        'VOOwnership': {<vo ownership dictionary>}, 'WLCG': {<WLCG dictionary>}, 'Contacts': {<Contacts dictionary}}"""
        self.resource['Name'] = str(self.name)
        self.resource['ID'] = int(self.id)
        self.resource['FQDN'] = str(self.fqdn)
        self.resource['VOOwnership'] = self.vo_ownership
        self.resource['WLCG'] = self.wlcg
        self.resource['Contacts'] = self.contacts
        return self.resource


class OIMTopology(object):
    """Class to hold the overall OIM topology information and parse it from an OIM xml file"""
    xml_file = 'resource_group_TEST.xml'

    def __init__(self, xml_file):
        self.xml_file = xml_file
        self.facilities = {}

    def parse(self):
        """Method to parse the OIM XML file, instantiate the appropriate classes, and generate the self.facilities
        dictionary"""
        d = minidom.parse(self.xml_file)
        resourcegroupselts = d.getElementsByTagName('ResourceGroup')

        # For each resource group in the XML file
        for rgelt in resourcegroupselts:
            facilityelt = rgelt.getElementsByTagName('Facility')[0]
            facilityname = facilityelt.getElementsByTagName('Name')[0].firstChild.data

            # If it's a new facility, instantiate a Facility object, parse the XML for the relevant info
            if facilityname not in self.facilities:
                facility = Facility(facilityname)
                facility.parse(rgelt)
                self.facilities[facilityname] = facility.build_dict()

            facility = self.facilities[facilityname]
            sites = facility['Sites']                   # facilities[facilityname]['Sites']

            siteelt = rgelt.getElementsByTagName('Site')[0]
            sitename = siteelt.getElementsByTagName('Name')[0].firstChild.data

            # If it's a new site, instantiate a Site object, parse the XML for the relevant info
            if sitename not in sites:
                site = Site(sitename)
                site.parse(rgelt)
                sites[sitename] = site.build_dict()

            site = sites[sitename]
            resourcegroups = site['ResourceGroups']     # facilities[facilityname]['Sites'][sitename]['ResourceGroups']

            groupname = rgelt.getElementsByTagName('GroupName')[0].firstChild.data

            # If it's a new resource group, instantiate a ResourceGroup object, parse the XML for the relevant info
            if groupname not in resourcegroups:
                rg = ResourceGroup(groupname)
                rg.parse(rgelt)
                resourcegroups[groupname] = rg.build_dict()

            rg = resourcegroups[groupname]    # facilities[facilityname]['Sites'][sitename]['ResourceGroups'][groupname]
            resourceelts = rgelt.getElementsByTagName('Resources')[0].getElementsByTagName('Resource')

            # Populate the resources dictionary to put into the rg dictionary
            resources = {}
            # For each resource
            for relt in resourceelts:
                # Don't care about disabled resources
                if literal_eval(relt.getElementsByTagName('Disable')[0].firstChild.data):
                    continue

                # We only care about resources that have CE or Connect services.  Once we see that one of those
                # is there at a facility, call it a Resource, get the info, and move onto the next resource
                services = relt.getElementsByTagName('Services')[0].getElementsByTagName('Service')

                for service in services:
                    if service.getElementsByTagName('Name')[0].firstChild.data in ['CE', 'Connect']:
                        resourcename = relt.getElementsByTagName('Name')[0].firstChild.data

                        # This should never happen, but just a check in case there's a duplicated resource in the
                        # XML file
                        if resourcename in resources:
                            continue

                        # Instantiate a new Resource object, parse the XML file for the relevant info
                        resource = Resource(resourcename)
                        resource.parse(relt)
                        resources[resourcename] = resource.build_dict()
                        break

            # Add the resources dictionary to the resourcegroups dictionary
            rg['Resources'] = resources
        return

    def test(self):
        """A function to test the generation of the facilities dictionary.  Run only after self.parse()"""
        for key, facility in self.facilities.iteritems():
            print "Facility: {}".format(facility['Name'])

            for key, site in facility['Sites'].iteritems():
                print "\tSite: {}".format(site['Name'])

                for key, resourcegroup in site['ResourceGroups'].iteritems():
                    print '\t\tResource Group: {}'.format(resourcegroup['Name'])

                    for key, resource in resourcegroup['Resources'].iteritems():
                        print '\t\t\tResource Name: {}'.format(resource['Name'])
                        print '\t\t\t\tID: {}'.format(resource['ID'])
                        print '\t\t\t\tWLCG: {}'.format(resource['WLCG'])
                        print '\t\t\t\tContacts: {}'.format(resource['Contacts'])
                        print '\t\t\t\tVOOwnership: {}'.format(resource['VOOwnership'])

    def get_information_by_facility(self, facility):
        # name, id, sites
        for key, items in self.facilities[facility].iteritems():
            print key, items
        return

    def get_information_by_site(self, *args):
        """Person should be able to put in the desired attributes, get information"""

        pass

    def get_information_by_resourcegroup(self, *args):
        pass

    def get_information_by_resource(self, *args):
        pass

    def get_vo_ownership_by_resource(self):
        pass


def main():
    #infile = 'shortsample_resourcegroup.xml'
    infile = 'resource_group_TEST.xml'
    topology = OIMTopology(infile)
    topology.parse()
    # print topology.facilities
    topology.test()
    topology.get_information_by_facility('JINR')

if __name__ == '__main__':
    main()







