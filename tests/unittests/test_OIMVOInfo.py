import unittest

from graccreq.oim import voinfo

class TestOIMVOInfo(unittest.TestCase):
    """Unit tests for OIM VO Info module"""

    def setUp(self):
        self.v = voinfo.OIMVOInfo()

    def test_no_overwrite(self):
        testdoc = {
            "ResourceType": "Batch",
            "VOName": "atlas",
            "RawProjectName": "N/A",
            "ProjectName": "N/A",
        }
        retdoc = self.v.parse_doc(testdoc)
        self.assertEqual(retdoc['OIM_FieldOfScience'], 'High Energy Physics')
        self.assertEqual(testdoc, retdoc)
        return True

    def test_override(self):
        testdoc = {
            "OIM_Organization": "Georgia Institute of Technology",
            "ResourceType": "Batch",
            "VOName": "osg",
            "RawProjectName": "VERITAS",
            "OIM_Department": "School of Physics & Center for Relativistic Astrophysics",
            "ReportableVOName": "osg",
            "RawVOName": "/osg/LocalGroup=users",
            "ProjectName": "VERITAS",
            "OIM_FieldOfScience": "Astrophysics",
        }
        retdoc = self.v.parse_doc(testdoc)
        self.assertEqual(retdoc['OIM_FieldOfScience'], 'Multi-Science Community')

        for key in testdoc.iterkeys():
            if key != 'OIM_FieldOfScience':
                self.assertEqual(testdoc[key], retdoc[key])
        return True

if __name__ == '__main__':
    unittest.main()
