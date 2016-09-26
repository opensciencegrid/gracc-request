#!/usr/bin/python

import unittest

from graccreq.oim import OIMTopology


class BasicOIMTopologyTests(unittest.TestCase):
    def setUpClass(cls):
        self.topology = OIMTopology.OIMTopology()

    def test_fqdn(self):
        """OIMTopology match by gracc probe to topology FQDN"""
        testdict = self.topology.get_information_by_fqdn('fifebatch1.fnal.gov')
        self.assertEqual(testdict['Facility'], 'Fermi National Accelerator'
                                               ' Laboratory')
        self.assertEqual(testdict['Site'], 'FermiGrid')
        self.assertEqual(testdict['ResourceGroup'], 'FNAL_FIFE_SUBMIT')
        self.assertEqual(testdict['Resource'],'FIFE_SUBMIT_1')
        return True

    def test_resource(self):
        """OIMTopology match by gracc SiteName to topology resource"""
        testdict = self.topology.get_information_by_resource('AGLT2_SL6')
        self.assertEqual(testdict['Facility'], 'University of Michigan')
        self.assertEqual(testdict['Site'], 'AGLT2')
        self.assertEqual(testdict['ResourceGroup'], 'AGLT2')
        self.assertEqual(testdict['Resource'],'AGLT2_SL6')
        return True


class GRACCDictTests(BasicOIMTopologyTests):
    def setUp(self):
        super(GRACCDictTests, self).setUp()
        self.testdoc_op = {'SiteName': 'AGLT2_SL6', 'VOName': 'Fermilab',
                           'ProbeName': 'condor:gate02.grid.umich.edu'}
        self.testdoc_ded = {'SiteName': 'AGLT2_SL6', 'VOName': 'ATLAS',
                            'ProbeName': 'condor:gate02.grid.umich.edu'}
        self.testdoc_fail_probe = {'SiteName': 'AGLT2_SL6',
                                   'VOName': 'Fermilab',
                                   'ProbeName':
                                       'condor:gate02.grid.umich.edu1231231'}
        self.testdoc_noprobe = {'SiteName': 'AGLT2_SL6',
                                   'VOName': 'Fermilab'}
        self.testdoc_nositeorprobe = {'VOName': 'Fermilab'}
        self.testdoc_no_vo = {'SiteName': 'AGLT2_SL6',
                                   'ProbeName':
                                       'condor:gate02.grid.umich.edu1231231'}
        self.testdoc_fail = {'SiteName': 'AGLT2_SL6123123123',
                             'VOName': 'Fermilab',
                             'ProbeName':
                                 'condor:gate02.grid.umich.edu1231231'}
        self.topology2 = OIMTopology.OIMTopology()

    def test_blankdict(self):
        """If URL retrieval fails or parsing didn't work, we should get a
        blank dictionary"""
        self.topology2.xml_file = None  # URL retrieval or parsing didn't work
        test_dict = self.topology2.generate_dict_for_gracc(self.testdoc_ded)
        self.assertFalse(test_dict)
        return True

    def test_dedicated(self):
        """Matching by probename, so the incorrect SiteName should be
        ignored"""
        ded = self.topology.generate_dict_for_gracc(self.testdoc_ded)
        self.assertEqual(ded['Facility'], 'University of Michigan')
        self.assertEqual(ded['Site'], 'AGLT2')
        self.assertEqual(ded['ResourceGroup'], 'AGLT2')
        self.assertEqual(ded['Resource'],'AGLT2_CE_2')
        self.assertEqual(ded['UsageModel'], 'DEDICATED')
        return True

    def test_opportunistic(self):
        """Matching by probename, so the incorrect SiteName should be
        ignored"""
        op = self.topology.generate_dict_for_gracc(self.testdoc_op)
        self.assertEqual(op['Facility'], 'University of Michigan')
        self.assertEqual(op['Site'], 'AGLT2')
        self.assertEqual(op['ResourceGroup'], 'AGLT2')
        self.assertEqual(op['Resource'], 'AGLT2_CE_2')
        self.assertEqual(op['UsageModel'], 'OPPORTUNISTIC')
        return True

    def test_fallbacktosite(self):
        """Probe name is wrong, so should match on site name to Resource 
        Group"""
        fail_probe = self.topology.generate_dict_for_gracc(
            self.testdoc_fail_probe)
        self.assertEqual(fail_probe['Facility'], 'University of Michigan')
        self.assertEqual(fail_probe['Site'], 'AGLT2')
        self.assertEqual(fail_probe['ResourceGroup'], 'AGLT2')
        self.assertNotEqual(fail_probe['Resource'],'AGLT2_CE_2')
        self.assertEqual(fail_probe['Resource'],'AGLT2_SL6')
        self.assertEqual(fail_probe['UsageModel'], 'OPPORTUNISTIC')
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
        self.assertEqual(fail_probe['Facility'], 'University of Michigan')
        self.assertEqual(fail_probe['Site'], 'AGLT2')
        self.assertEqual(fail_probe['ResourceGroup'], 'AGLT2')
        self.assertNotEqual(fail_probe['Resource'],'AGLT2_CE_2')
        self.assertEqual(fail_probe['Resource'],'AGLT2_SL6')
        self.assertEqual(fail_probe['UsageModel'], 'OPPORTUNISTIC')
        return True

    def test_noprobe_nosite(self):
        fail_probe = self.topology.generate_dict_for_gracc(
            self.testdoc_nositeorprobe)
        self.assertFalse(fail_probe)
        return True

    def test_no_vo(self):
        fail_probe = self.topology.generate_dict_for_gracc(
            self.testdoc_no_vo)
        self.assertEqual(fail_probe['UsageModel'], 'UNKNOWN')
        return True


if __name__ == '__main__':
    unittest.main()
