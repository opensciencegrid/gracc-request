import unittest

from graccreq.oim import projects


class TestOIMProjects(unittest.TestCase):
    def test_minimal(self):
        
        
        project = projects.OIMProjects()
        
        stuff = project.parseDoc({'ProjectName': 'atlas-org-unm'})
        
        self.assertEqual(stuff["PIName"], "Robert William Gardner Jr")
        self.assertEqual(stuff["Organization"], "University of New Mexico")
        self.assertEqual(stuff["Department"], "Physics")
        self.assertEqual(stuff["FieldOfScience"], 'High Energy Physics')
        
        return True
        
