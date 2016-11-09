#!/usr/bin/python

import unittest

from graccreq.oim import OIMTopology


class BasicOIMTopologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.topology = OIMTopology.OIMTopology()

    def test_fqdn(self):
        """OIMTopology match by gracc probe to topology FQDN"""
        testdict = self.topology.get_information_by_fqdn('fifebatch1.fnal.gov')
        self.assertEqual(testdict['OIMFacility'], 'Fermi National Accelerator'
                                               ' Laboratory')
        self.assertEqual(testdict['OIMSite'], 'FermiGrid')
        self.assertEqual(testdict['OIMResourceGroup'], 'FNAL_FIFE_SUBMIT')
        self.assertEqual(testdict['OIMResource'],'FIFE_SUBMIT_1')
        return True

    def test_resource(self):
        """OIMTopology match by gracc SiteName to topology resource"""
        testdict = self.topology.get_information_by_resource('AGLT2_SL6')
        self.assertEqual(testdict['OIMFacility'], 'University of Michigan')
        self.assertEqual(testdict['OIMSite'], 'AGLT2')
        self.assertEqual(testdict['OIMResourceGroup'], 'AGLT2')
        self.assertEqual(testdict['OIMResource'],'AGLT2_SL6')
        return True


class GRACCDictTests(BasicOIMTopologyTests):
    @classmethod
    def setUpClass(cls):
        cls.testdoc_op = {'SiteName': 'AGLT2_SL6', 'VOName': 'Fermilab',
                           'ProbeName': 'condor:gate02.grid.umich.edu'}
        cls.testdoc_ded = {'SiteName': 'AGLT2_SL6', 'VOName': 'ATLAS',
                            'ProbeName': 'condor:gate02.grid.umich.edu'}
        cls.testdoc_fail_probe = {'SiteName': 'AGLT2_SL6',
                                   'VOName': 'Fermilab',
                                   'ProbeName':
                                       'condor:gate02.grid.umich.edu1231231'}
        cls.testdoc_noprobe = {'SiteName': 'AGLT2_SL6',
                                   'VOName': 'Fermilab'}
        cls.testdoc_nositeorprobe = {'VOName': 'Fermilab'}
        cls.testdoc_no_vo = {'SiteName': 'AGLT2_SL6',
                                   'ProbeName':
                                       'condor:gate02.grid.umich.edu1231231'}
        cls.testdoc_fail = {'SiteName': 'AGLT2_SL6123123123',
                             'VOName': 'Fermilab',
                             'ProbeName':
                                 'condor:gate02.grid.umich.edu1231231'}
        cls.testdoc_payload_suc = {'SiteName': 'AGLT2_SL6', 'VOName': 'ATLAS',
                                   'ProbeName': 'condor:gate02.grid.umich.edu',
                                   'Host_description': 'BNL_ATLAS_1',
                                   'ResourceType': 'Payload'}
        cls.testdoc_payload_site = {'SiteName': 'AGLT2_SL6', 'VOName': 'ATLAS',
                                    'Host_description': 'UConn-OSG',
                                    'ResourceType': 'Payload'}
        cls.testdoc_payload_rg = {'SiteName': 'AGLT2_SL6', 'VOName': 'ATLAS',
                                  'Host_description': 'Hyak',
                                  'ResourceType': 'Payload'}
        cls.testdoc_payload_fail = {'SiteName': 'AGLT2_SL6', 'VOName': 'ATLAS',
                                    'Host_description': 'GPGrid12345',
                                    'ResourceType': 'Payload'}

    def test_blankdict(self):
        """If URL retrieval fails or parsing didn't work, we should get a
        blank dictionary"""
        class Empty(self.topology.__class__):
            def __init__(self): pass
        topology2 = Empty()
        topology2.__class__ = self.topology.__class__
        topology2.xml_file = None  # URL retrieval or parsing didn't work
        test_dict = topology2.generate_dict_for_gracc(self.testdoc_ded)
        self.assertFalse(test_dict)
        return True

    def test_dedicated(self):
        """Matching by probename, so the incorrect SiteName should be
        ignored"""
        ded = self.topology.generate_dict_for_gracc(self.testdoc_ded)
        self.assertEqual(ded['OIMFacility'], 'University of Michigan')
        self.assertEqual(ded['OIMSite'], 'AGLT2')
        self.assertEqual(ded['OIMResourceGroup'], 'AGLT2')
        self.assertEqual(ded['OIMResource'],'AGLT2_CE_2')
        self.assertEqual(ded['OIMUsageModel'], 'DEDICATED')
        return True

    def test_opportunistic(self):
        """Matching by probename, so the incorrect SiteName should be
        ignored"""
        op = self.topology.generate_dict_for_gracc(self.testdoc_op)
        self.assertEqual(op['OIMFacility'], 'University of Michigan')
        self.assertEqual(op['OIMSite'], 'AGLT2')
        self.assertEqual(op['OIMResourceGroup'], 'AGLT2')
        self.assertEqual(op['OIMResource'], 'AGLT2_CE_2')
        self.assertEqual(op['OIMUsageModel'], 'OPPORTUNISTIC')
        return True

    def test_fallbacktosite(self):
        """Probe name is wrong, so should match on site name to Resource 
        Group"""
        fail_probe = self.topology.generate_dict_for_gracc(
            self.testdoc_fail_probe)
        self.assertEqual(fail_probe['OIMFacility'], 'University of Michigan')
        self.assertEqual(fail_probe['OIMSite'], 'AGLT2')
        self.assertEqual(fail_probe['OIMResourceGroup'], 'AGLT2')
        self.assertNotEqual(fail_probe['OIMResource'],'AGLT2_CE_2')
        self.assertEqual(fail_probe['OIMResource'],'AGLT2_SL6')
        self.assertEqual(fail_probe['OIMUsageModel'], 'OPPORTUNISTIC')
        return True
    
    def test_fail(self):
        """Probe name and SiteName are wrong"""
        fail_dict = self.topology.generate_dict_for_gracc(
            self.testdoc_fail)
        self.assertEqual(fail_dict, {})
        return True

    def test_noprobe(self):
        """No Probe name in gracc doc at all"""
        fail_probe = self.topology.generate_dict_for_gracc(
            self.testdoc_noprobe)
        self.assertEqual(fail_probe['OIMFacility'], 'University of Michigan')
        self.assertEqual(fail_probe['OIMSite'], 'AGLT2')
        self.assertEqual(fail_probe['OIMResourceGroup'], 'AGLT2')
        self.assertNotEqual(fail_probe['OIMResource'],'AGLT2_CE_2')
        self.assertEqual(fail_probe['OIMResource'],'AGLT2_SL6')
        self.assertEqual(fail_probe['OIMUsageModel'], 'OPPORTUNISTIC')
        return True

    def test_noprobe_nosite(self):
        fail_probe = self.topology.generate_dict_for_gracc(
            self.testdoc_nositeorprobe)
        self.assertFalse(fail_probe)
        return True

    def test_no_vo(self):
        fail_probe = self.topology.generate_dict_for_gracc(
            self.testdoc_no_vo)
        self.assertEqual(fail_probe['OIMUsageModel'], 'UNKNOWN')
        return True

    def test_payload(self):
        """Payload record - should be successful match for BNL_ATLAS_1
        resource"""
        pg = self.topology.generate_dict_for_gracc(self.testdoc_payload_suc)
        self.assertEqual(pg['OIMFacility'], 'Brookhaven National Laboratory')
        self.assertEqual(pg['OIMSite'], 'Brookhaven ATLAS Tier1')
        self.assertEqual(pg['OIMResourceGroup'], 'BNL-ATLAS')
        self.assertEqual(pg['OIMResource'], 'BNL_ATLAS_1')
        self.assertEqual(pg['OIMUsageModel'], 'DEDICATED')
        return True

    def test_payload_site(self):
        """Payload record - should be successful match for UConn-OSG Site"""
        st = self.topology.generate_dict_for_gracc(self.testdoc_payload_site)
        self.assertEqual(st['OIMFacility'], 'University of Connecticut')
        self.assertEqual(st['OIMSite'], 'UConn-OSG')
        rg = st.get('OIMResourceGroup')
        res = st.get('OIMResource')
        um = st.get('OIMUsageModel')
        self.assertFalse(rg)
        self.assertFalse(res)
        self.assertFalse(um)
        return True

    def test_payload_rg(self):
        """Payload record - should be successful match for Hyak Resource
        Group"""
        rg = self.topology.generate_dict_for_gracc(self.testdoc_payload_rg)
        self.assertEqual(rg['OIMFacility'], 'University of Washington')
        self.assertEqual(rg['OIMSite'], 'UW-IT')
        self.assertEqual(rg['OIMResourceGroup'], 'Hyak')
        res = rg.get('OIMResource')
        um = rg.get('OIMUsageModel')
        self.assertFalse(res)
        self.assertFalse(um)
        return True
    
    def test_payload_fail(self):
        """Payload record - should fail to match"""
        fail = self.topology.generate_dict_for_gracc(self.testdoc_payload_fail)
        self.assertFalse(fail)
        return True


if __name__ == '__main__':
    unittest.main()
