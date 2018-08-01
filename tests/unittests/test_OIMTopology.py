#!/usr/bin/python

import unittest
import os

from graccreq.oim import OIMTopology


class BasicOIMTopologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.topology = OIMTopology.OIMTopology()

    def test_fqdn(self):
        """OIMTopology match by gracc probe to topology FQDN"""
        testdict = self.topology.get_information_by_fqdn('jobsub01.fnal.gov')
        self.assertEqual(testdict['OIM_Facility'], 'Fermi National Accelerator'
                                               ' Laboratory')
        self.assertEqual(testdict['OIM_Site'], 'FermiGrid')
        self.assertEqual(testdict['OIM_ResourceGroup'], 'GPGRID')
        self.assertEqual(testdict['OIM_Resource'],'FNAL_JOBSUB_01')
        self.assertEqual(testdict['OIM_Match'], 'FQDN')
        return True

    def test_resource(self):
        """OIMTopology match by gracc SiteName to topology resource"""
        testdict = self.topology.get_information_by_resource('AGLT2_CE_2')
        self.assertEqual(testdict['OIM_Facility'], 'University of Michigan')
        self.assertEqual(testdict['OIM_Site'], 'AGLT2')
        self.assertEqual(testdict['OIM_ResourceGroup'], 'AGLT2')
        self.assertEqual(testdict['OIM_Resource'],'AGLT2_CE_2')
        self.assertEqual(testdict['OIM_WLCGAPELNormalFactor'], 10.21)
        self.assertEqual(testdict['OIM_Match'], 'Resource')
        return True

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.topology.lockfile):
            os.unlink(cls.topology.lockfile)


class GRACCDictTests(BasicOIMTopologyTests):
    @classmethod
    def setUpClass(cls):
        cls.testdoc_op = {'SiteName': 'AGLT2_CE_2', 'VOName': 'Fermilab',
                           'ProbeName': 'condor:gate02.grid.umich.edu'}
        cls.testdoc_ded = {'SiteName': 'AGLT2_CE_2', 'VOName': 'ATLAS',
                            'ProbeName': 'condor:gate02.grid.umich.edu'}
        cls.testdoc_fail_probe = {'SiteName': 'AGLT2_CE_2',
                                   'VOName': 'Fermilab',
                                   'ProbeName':
                                       'condor:gate02.grid.umich.edu1231231'}
        cls.testdoc_fail_probe_case_sensitive = {'SiteName': 'aglt2_ce_2',
                                   'VOName': 'Fermilab',
                                   'ProbeName':
                                       'condor:gate02.grid.umich.edu1231231'}

        cls.testdoc_noprobe = {'SiteName': 'AGLT2_CE_2',
                                   'VOName': 'Fermilab'}
        cls.testdoc_nositeorprobe = {'VOName': 'Fermilab'}
        cls.testdoc_no_vo = {'SiteName': 'AGLT2_CE_2',
                                   'ProbeName':
                                       'condor:gate02.grid.umich.edu1231231'}
        cls.testdoc_fail = {'SiteName': 'AGLT2_CE_2123123123',
                             'VOName': 'Fermilab',
                             'ProbeName':
                                 'condor:gate02.grid.umich.edu1231231'}
        cls.testdoc_payload_suc = {'SiteName': 'AGLT2_CE_2', 'VOName': 'ATLAS',
                                   'ProbeName': 'condor:gate02.grid.umich.edu',
                                   'Host_description': 'BNL_ATLAS_1',
                                   'ResourceType': 'Payload'}
        cls.testdoc_payload_site = {'SiteName': 'AGLT2_CE_2', 'VOName': 'ATLAS',
                                    'Host_description': 'UConn-OSG',
                                    'ResourceType': 'Payload'}
        cls.testdoc_payload_rg = {'SiteName': 'AGLT2_CE_2', 'VOName': 'ATLAS',
                                  'Host_description': 'Hyak',
                                  'ResourceType': 'Payload'}
        cls.testdoc_case_sensitive = {'SiteName': 'AGLT2_CE_2', 'VOName': 'ATLAS',
                                  'Host_description': 'hYaK',
                                  'ResourceType': 'Payload'}
        cls.testdoc_payload_fail = {'SiteName': 'AGLT2_CE_2', 'VOName': 'ATLAS',
                                    'Host_description': 'GPGrid12345',
                                    'ResourceType': 'Payload'}


    def test_blankdict(self):
        """If URL retrieval fails or parsing didn't work, we should get a
        blank dictionary"""
        class Empty(self.topology.__class__):
            def __init__(self): pass
        topology2 = Empty()
        topology2.__class__ = self.topology.__class__
        topology2.have_info = False  # URL retrieval or parsing didn't work
        test_dict = topology2.generate_dict_for_gracc(self.testdoc_ded)
        self.assertFalse(test_dict)
        return True

    def test_caching(self):
        """Test to make sure that we can read from cache and that lock is
        released after reading file"""
        testclass = OIMTopology.OIMTopology()
        self.assertTrue(testclass.have_info)
        self.assertFalse(testclass.cachelock.is_locked)

        if os.path.exists(testclass.lockfile):
            os.unlink(testclass.lockfile)

        return True

    def test_dedicated(self):
        """Matching by probename, so the incorrect SiteName should be
        ignored"""
        ded = self.topology.generate_dict_for_gracc(self.testdoc_ded)
        self.assertEqual(ded['OIM_Facility'], 'University of Michigan')
        self.assertEqual(ded['OIM_Site'], 'AGLT2')
        self.assertEqual(ded['OIM_ResourceGroup'], 'AGLT2')
        self.assertEqual(ded['OIM_Resource'],'AGLT2_CE_2')
        self.assertEqual(ded['OIM_UsageModel'], 'DEDICATED')
        self.assertEqual(ded['OIM_Match'], 'ProbeName-FQDN')
        return True

    def test_opportunistic(self):
        """Matching by probename, so the incorrect SiteName should be
        ignored"""
        op = self.topology.generate_dict_for_gracc(self.testdoc_op)
        self.assertEqual(op['OIM_Facility'], 'University of Michigan')
        self.assertEqual(op['OIM_Site'], 'AGLT2')
        self.assertEqual(op['OIM_ResourceGroup'], 'AGLT2')
        self.assertEqual(op['OIM_Resource'], 'AGLT2_CE_2')
        self.assertEqual(op['OIM_UsageModel'], 'OPPORTUNISTIC')
        self.assertEqual(op['OIM_Match'], 'ProbeName-FQDN')
        return True


    def test_fallbacktosite(self):
        """Probe name is wrong, so should match on site name to Resource 
        Group"""
        fail_probe = self.topology.generate_dict_for_gracc(
            self.testdoc_fail_probe)
        self.assertEqual(fail_probe['OIM_Facility'], 'University of Michigan')
        self.assertEqual(fail_probe['OIM_Site'], 'AGLT2')
        self.assertEqual(fail_probe['OIM_ResourceGroup'], 'AGLT2')
        self.assertNotEqual(fail_probe['OIM_Resource'],'AGLT2_SL6')
        self.assertEqual(fail_probe['OIM_Resource'],'AGLT2_CE_2')
        self.assertEqual(fail_probe['OIM_UsageModel'], 'OPPORTUNISTIC')
        self.assertEqual(fail_probe['OIM_Match'], 'SiteName-Resource')
        return True


    def test_fallbacktosite_case_sensitive(self):
        """Probe name is wrong, so should match on site name to Resource
        Group.  Same as fallbacktosite, but with case sensitivity checking"""
        fail_probe = self.topology.generate_dict_for_gracc(
            self.testdoc_fail_probe_case_sensitive)
        self.assertEqual(fail_probe['OIM_Facility'], 'University of Michigan')
        self.assertEqual(fail_probe['OIM_Site'], 'AGLT2')
        self.assertEqual(fail_probe['OIM_ResourceGroup'], 'AGLT2')
        self.assertNotEqual(fail_probe['OIM_Resource'],'AGLT2_SL6')
        self.assertEqual(fail_probe['OIM_Resource'],'AGLT2_CE_2')
        self.assertEqual(fail_probe['OIM_UsageModel'], 'OPPORTUNISTIC')
        self.assertEqual(fail_probe['OIM_Match'], 'SiteName-Resource')
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
        self.assertEqual(fail_probe['OIM_Facility'], 'University of Michigan')
        self.assertEqual(fail_probe['OIM_Site'], 'AGLT2')
        self.assertEqual(fail_probe['OIM_ResourceGroup'], 'AGLT2')
        self.assertNotEqual(fail_probe['OIM_Resource'],'AGLT2_SL6')
        self.assertEqual(fail_probe['OIM_Resource'],'AGLT2_CE_2')
        self.assertEqual(fail_probe['OIM_UsageModel'], 'OPPORTUNISTIC')
        self.assertEqual(fail_probe['OIM_Match'], 'SiteName-Resource')
        return True

    def test_noprobe_nosite(self):
        fail_probe = self.topology.generate_dict_for_gracc(
            self.testdoc_nositeorprobe)
        self.assertFalse(fail_probe)
        return True

    def test_no_vo(self):
        fail_probe = self.topology.generate_dict_for_gracc(
            self.testdoc_no_vo)
        self.assertEqual(fail_probe['OIM_UsageModel'], 'UNKNOWN')
        return True

    def test_payload(self):
        """Payload record - should be successful match for BNL_ATLAS_1
        resource"""
        pg = self.topology.generate_dict_for_gracc(self.testdoc_payload_suc)
        self.assertEqual(pg['OIM_Facility'], 'Brookhaven National Laboratory')
        self.assertEqual(pg['OIM_Site'], 'Brookhaven ATLAS Tier1')
        self.assertEqual(pg['OIM_ResourceGroup'], 'BNL-ATLAS')
        self.assertEqual(pg['OIM_Resource'], 'BNL_ATLAS_1')
        self.assertEqual(pg['OIM_UsageModel'], 'DEDICATED')
        self.assertEqual(pg['OIM_Match'], 'Host_description-Resource')
        return True

    def test_payload_site(self):
        """Payload record - should be successful match for UConn-OSG Site"""
        st = self.topology.generate_dict_for_gracc(self.testdoc_payload_site)
        self.assertEqual(st['OIM_Facility'], 'University of Connecticut')
        self.assertEqual(st['OIM_Site'], 'UConn-OSG')
        rg = st.get('OIM_ResourceGroup')
        res = st.get('OIM_Resource')
        um = st.get('OIM_UsageModel')
        self.assertFalse(rg)
        self.assertFalse(res)
        self.assertFalse(um)
        self.assertEqual(st['OIM_Match'],'Host_description-Site')
        return True

    def test_payload_rg(self):
        """Payload record - should be successful match for Hyak Resource
        Group"""
        rg = self.topology.generate_dict_for_gracc(self.testdoc_payload_rg)
        self.assertEqual(rg['OIM_Facility'], 'University of Washington')
        self.assertEqual(rg['OIM_Site'], 'UW-IT')
        self.assertEqual(rg['OIM_ResourceGroup'], 'Hyak')
        res = rg.get('OIM_Resource')
        um = rg.get('OIM_UsageModel')
        self.assertFalse(res)
        self.assertFalse(um)
        self.assertEqual(rg['OIM_Match'], 'Host_description-ResourceGroup')
        return True

    def test_payload_case_sensitive(self):
        """Payload record, same as test_payload_rg, but with the case wrong
        in the test doc - should be successful match for Hyak Resource
        Group"""
        rg = self.topology.generate_dict_for_gracc(self.testdoc_case_sensitive)
        self.assertEqual(rg['OIM_Facility'], 'University of Washington')
        self.assertEqual(rg['OIM_Site'], 'UW-IT')
        self.assertEqual(rg['OIM_ResourceGroup'], 'Hyak')
        res = rg.get('OIM_Resource')
        um = rg.get('OIM_UsageModel')
        self.assertFalse(res)
        self.assertFalse(um)
        self.assertEqual(rg['OIM_Match'], 'Host_description-ResourceGroup')
        return True
    
    def test_payload_fail(self):
        """Payload record - should fail to match"""
        fail = self.topology.generate_dict_for_gracc(self.testdoc_payload_fail)
        self.assertFalse(fail)
        return True


if __name__ == '__main__':
    unittest.main()
