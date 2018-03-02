import unittest

from graccreq.oim import projects


class TestOIMProjects(unittest.TestCase):
    def test_minimal(self):
        
        
        project = projects.OIMProjects()
        
        stuff = project.parseDoc({'ProjectName': 'atlas-org-unm'})
        
        self.assertEqual(stuff["OIM_PIName"], "Robert William Gardner Jr")
        self.assertEqual(stuff["OIM_Organization"], "University of New Mexico")
        self.assertEqual(stuff["OIM_Department"], "Physics")
        self.assertEqual(stuff["OIM_FieldOfScience"], 'High Energy Physics')
        
        return True
    
    def test_caseless(self):

        project = projects.OIMProjects()
        stuff = project.parseDoc({'ProjectName': 'des'})
        self.assertEqual(stuff["OIM_Organization"], "Fermilab")

        return True
        
