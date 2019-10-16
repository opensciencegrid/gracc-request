import unittest
import os

from graccreq.oim import nsfscience


class TestOIMNSFScience(unittest.TestCase):
    def test_minimal(self):

        # Get the current file path of this file
        curdir = os.path.dirname(os.path.abspath(__file__))
        test_csv = os.path.join(curdir, "../", "mapping-table-test.csv")

        science = nsfscience.NSFScience(url="file://" + test_csv)

        stuff = science.parseDoc({'OIM_FieldOfScience': 'Medical Imaging'})
        self.assertEqual(stuff['OIM_NSFFieldOfScience'], 'Health')

        stuff = science.parseDoc({'OIM_FieldOfScience': 'Evolutionary Sciences'})
        self.assertEqual(stuff['OIM_NSFFieldOfScience'], 'Biological Sciences')

        # Test when the field of science does not exist
        stuff = science.parseDoc({'OIM_FieldOfScience': 'Does Not exist'})
        self.assertEqual(len(stuff), 0)

        # When the record doesn't have a message
        stuff = science.parseDoc({})
        self.assertEqual(len(stuff), 0)


        return True


if __name__ == '__main__':
    unittest.main()
