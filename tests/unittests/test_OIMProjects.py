import unittest

from graccreq.oim import projects


class TestOIMProjects(unittest.TestCase):
    def test_minimal(self):
        
        
        project = projects.OIMProjects()
        
        stuff = project.parseDoc({'ProjectName': 'atlas-org-unm'})
        
        print stuff
        
        return True
        
