import unittest

from graccreq.correct import Corrections

class MockCorrections(Corrections):
    def __init__(self):
        self.corrections = {}
        self.match_fields = []
        self.dest_field = ''

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
