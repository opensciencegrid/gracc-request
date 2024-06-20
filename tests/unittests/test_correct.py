import unittest

from graccreq.correct import Corrections

class MockCorrections(Corrections):
    def __init__(self, regex=False, force_overwrite=False):
        self.corrections = {}
        self.match_fields = []
        self.dest_field = ''
        self.regex = regex
        self.force_overwrite = force_overwrite

class TestCorrections(unittest.TestCase):
    def test_simple_corrections(self):
        c = MockCorrections()
        c.match_fields=['name']
        c.source_field='corrected_name'
        c.dest_field='name'
        c._add_correction({'_source':{'name':'foo','corrected_name':'FOO'}})
        c._add_correction({'_source':{'name':'bar','corrected_name':'BAR'}})

        doc = c.correct({'name':'foo'})
        self.assertEqual(doc['name'],'FOO')
        self.assertEqual(doc['Rawname'],'foo')

        doc = {'name': 'bar'}
        c.correct(doc)
        self.assertEqual(doc['name'],'BAR')
        self.assertEqual(doc['Rawname'],'bar')

        return True

    def test_complex_corrections(self):
        c = MockCorrections()
        c.match_fields=['name','type']
        c.source_field='corrected_name'
        c.dest_field='name'
        c._add_correction({'_source':{'name':'foo','type':'baz','corrected_name':'FOO'}})
        c._add_correction({'_source':{'name':'bar','type':'baz','corrected_name':'BAR'}})
        c._add_correction({'_source':{'name':'bar','type':'qux','corrected_name':'NOTBAR'}})

        doc = c.correct({'name':'foo','type':'baz'})
        self.assertEqual(doc['name'],'FOO')
        self.assertEqual(doc['Rawname'],'foo')

        doc = {'name': 'bar','type':'baz'}
        c.correct(doc)
        self.assertEqual(doc['name'],'BAR')
        self.assertEqual(doc['Rawname'],'bar')

        doc = {'name': 'bar','type':'bux'}
        c.correct(doc)
        self.assertEqual(doc['name'],'bar')
        self.assertEqual(doc['Rawname'],'bar')

        return True

    def test_new_field_corrections(self):
        c = MockCorrections()
        c.match_fields=['ReportableVOName']
        c.source_field='CorrectedReportableVOName'
        c.dest_field='CorrectedReportableVOName'

        c._add_correction({'_source': {
            'ReportableVOName': 'FERMILAB',
            'CorrectedReportableVOName': 'Fermilab',
        }})

        doc = c.correct({'ReportableVOName': 'FERMILAB'})
        self.assertEqual(doc['CorrectedReportableVOName'], "Fermilab")

    def test_force_new_field_corrections(self):
        c = MockCorrections(force_overwrite=True)
        c.match_fields=['ReportableVOName']
        c.source_field='CorrectedReportableVOName'
        c.dest_field='CorrectedReportableVOName'

        # Add a correction that won't match
        c._add_correction({'_source': {
            'ReportableVOName': 'FERMILAB',
            'CorrectedReportableVOName': 'Fermilab',
        }})

        doc = c.correct({'ReportableVOName': 'ATLAS'})
        self.assertEqual(doc['CorrectedReportableVOName'], "ATLAS")

    def test_regex_corrections(self):
        c = MockCorrections(regex=True)
        c.match_fields = ['Host_description']
        c.source_field = 'Corrected_OIM_Site'
        c.dest_field = 'OIM_Site'

        c._add_correction({'_source': {
            'Host_description': 'comet-[\d\-]+\.sdsc\.edu',
            'Corrected_OIM_Site': 'SDSC Comet',
            'type': 'host_description_regex'
        }})
        c._add_correction({'_source': {
            'Host_description': '.*\.bridges\.psc\.edu',
            'Corrected_OIM_Site': 'PSC Bridges',
            'type': 'host_description_regex'
        }})

        c._add_correction({'_source': {
            'Host_description': 'SDSC\_Comet',
            'Corrected_OIM_Site': 'COMETVCCE',
            'type': 'host_description_regex'
        }})

        c._add_correction({'_source': {
            'Host_description': 'TACC',
            'Corrected_OIM_Site': 'Texas Advanced Computing Center',
            'type': 'host_description_regex'
        }})

        doc = c.correct({'Host_description': 'comet-03-11.sdsc.edu'})
        self.assertEqual(doc['OIM_Site'], "SDSC Comet")
        self.assertEqual(doc['RawOIM_Site'], "")

        doc = c.correct({'Host_description': 'r359.pvt.bridges.psc.edu'})
        self.assertEqual(doc['OIM_Site'], "PSC Bridges")
        self.assertEqual(doc['RawOIM_Site'], "")

        doc = c.correct({'Host_description': 'SDSC_Comet'})
        self.assertEqual(doc['OIM_Site'], 'COMETVCCE')
        self.assertEqual(doc['RawOIM_Site'], "")

        doc = c.correct({'Host_description': 'TACC'})
        self.assertEqual(doc['OIM_Site'], 'Texas Advanced Computing Center')
        self.assertEqual(doc['RawOIM_Site'], "")

        import logging
        logging.basicConfig()
        c._add_correction({'_source': {
            'Host_description': '.*\.bridges\.psc\.edu(',
            'Corrected_OIM_Site': 'PSC Bridges',
            'type': 'host_description_regex'
            },
            '_id': "shouldfail"
        })
