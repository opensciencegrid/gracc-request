import unittest

from graccreq.oim import projects


class TestOIMProjects(unittest.TestCase):
    def test_minimal(self):

        project = projects.OIMProjects()

        stuff = project.parseDoc({'ProjectName': 'atlas.org.unm'})

        self.assertEqual(stuff["OIM_PIName"], "Robert William Gardner Jr")
        self.assertEqual(stuff["OIM_Organization"], "University of New Mexico")
        self.assertEqual(stuff["OIM_Department"], "Physics")
        self.assertEqual(stuff["OIM_FieldOfScience"], 'High Energy Physics')
        self.assertEqual(stuff["OIM_InstitutionID"], 'https://osg-htc.org/iid/pclpz1bwbpdi')
        self.assertEqual(stuff["OIM_FieldOfScienceID"], '40.08')
        self.assertEqual(stuff["OIM_BroadFieldOfScience"], 'Physical sciences')
        self.assertEqual(stuff["OIM_MajorFieldOfScience"], 'Physics')
        self.assertEqual(stuff["OIM_DetailedFieldOfScience"], None)
        self.assertEqual(stuff["OIM_InstitutionName"], "University of New Mexico")

        return True


    def test_caseless(self):

        project = projects.OIMProjects()
        stuff = project.parseDoc({'ProjectName': 'des'})
        self.assertEqual(stuff["OIM_Organization"], "Fermilab")

        return True

if __name__ == '__main__':
    unittest.main()
