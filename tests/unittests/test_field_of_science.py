import unittest

import pandas as pd

from graccreq.oim import field_of_science


class TestOIMProjects(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.FOS = field_of_science.FieldOfScience()

    def test_physics(self):

        broad_fos, major_fos, detailed_fos = self.FOS.map_id_to_fields_of_science('40.08')
        self.assertEqual(broad_fos, 'Physical sciences')
        self.assertEqual(major_fos, 'Physics')
        self.assertEqual(detailed_fos, None)

        return True

    def test_chemistry(self):

          broad_fos, major_fos, detailed_fos = self.FOS.map_id_to_fields_of_science('40.05')
          self.assertEqual(broad_fos, 'Physical sciences')
          self.assertEqual(major_fos, 'Chemistry')
          self.assertEqual(detailed_fos, None)

          return True

    def test_astrophysics_full(self):

        broad_fos, major_fos, detailed_fos = self.FOS.map_id_to_fields_of_science('40.0202')
        self.assertEqual(broad_fos, 'Physical sciences')
        self.assertEqual(major_fos, 'Astronomy and astrophysics')
        self.assertEqual(detailed_fos, 'Astrophysics')

        return True

    def test_astrophysics_partial(self):

          broad_fos, major_fos, detailed_fos = self.FOS.map_id_to_fields_of_science('40.02')
          self.assertEqual(broad_fos, 'Physical sciences')
          self.assertEqual(major_fos, 'Astronomy and astrophysics')
          self.assertEqual(detailed_fos, None)

          return True

    def test_particle_physics_full(self):

        broad_fos, major_fos, detailed_fos = self.FOS.map_id_to_fields_of_science('40.0804')
        self.assertEqual(broad_fos, 'Physical sciences')
        self.assertEqual(major_fos, 'Physics')
        self.assertEqual(detailed_fos, 'Elementary particle physics')

        return True

    def test_interdisciplinary(self):

        broad_fos, major_fos, detailed_fos = self.FOS.map_id_to_fields_of_science('30')
        self.assertEqual(broad_fos, 'Multidisciplinary/ interdisciplinary sciences')
        self.assertEqual(major_fos, None)
        self.assertEqual(detailed_fos, None)

        return True

    def test_interdisciplinary_full(self):

        broad_fos, major_fos, detailed_fos = self.FOS.map_id_to_fields_of_science('30.1701')
        self.assertEqual(broad_fos, 'Multidisciplinary/ interdisciplinary sciences')
        self.assertEqual(major_fos, 'Multidisciplinary/ interdisciplinary sciences, other')
        self.assertEqual(detailed_fos, 'Behavioral and cognitive sciences')

        return True

    def test_full_id(self):

        broad_fos, major_fos, detailed_fos = self.FOS.map_id_to_fields_of_science('51.2308')
        self.assertEqual(broad_fos, 'Health sciences')
        self.assertEqual(major_fos, 'Health sciences, other')
        self.assertEqual(detailed_fos, 'Rehabilitation and therapeutic sciences')

        return True

    def test_statistics(self):

        broad_fos, major_fos, detailed_fos = self.FOS.map_id_to_fields_of_science('27.05')
        self.assertEqual(broad_fos, 'Mathematics and statistics')
        self.assertEqual(major_fos, 'Statistics')
        self.assertEqual(detailed_fos, None)

        return True

    def test_mathematics(self):

        broad_fos, major_fos, detailed_fos = self.FOS.map_id_to_fields_of_science('27.01')
        self.assertEqual(broad_fos, 'Mathematics and statistics')
        self.assertEqual(major_fos, 'Mathematics')
        self.assertEqual(detailed_fos, None)

        return True

    def test_partial_bio(self):

        broad_fos, major_fos, detailed_fos = self.FOS.map_id_to_fields_of_science('26.13')
        self.assertEqual(broad_fos, 'Biological and biomedical sciences')
        self.assertEqual(major_fos, 'Ecology, evolutionary biology, and epidemiology')
        self.assertEqual(detailed_fos, None)

        return True

    def test_engineering_full(self):

        broad_fos, major_fos, detailed_fos = self.FOS.map_id_to_fields_of_science('14.0501')
        self.assertEqual(broad_fos, 'Engineering')
        self.assertEqual(major_fos, 'Biological, biomedical, and biosystems engineering')
        self.assertEqual(detailed_fos, 'Bioengineering and biomedical engineering')

        return True

    def test_computer_science_partial(self):

        broad_fos, major_fos, detailed_fos = self.FOS.map_id_to_fields_of_science('11.07')
        self.assertEqual(broad_fos, 'Computer and information sciences')
        self.assertEqual(major_fos, 'Computer science')
        self.assertEqual(detailed_fos, None)

        return True

    def test_sub_detailed(self):

          broad_fos, major_fos, detailed_fos = self.FOS.map_id_to_fields_of_science('30.3201b')
          self.assertEqual(broad_fos, 'Geosciences, atmospheric, and ocean sciences')
          self.assertEqual(major_fos, 'Ocean, marine, and atmospheric sciences')
          self.assertEqual(detailed_fos, 'Marine sciences')

          return True

    def test_sub_detailed_second_opinion(self):

        broad_fos, major_fos, detailed_fos = self.FOS.map_id_to_fields_of_science('11.0701a')
        self.assertEqual(broad_fos, 'Computer and information sciences')
        self.assertEqual(major_fos, 'Computer science')
        self.assertEqual(detailed_fos, 'Computer science')

        return True

    def test_invalid_id(self):
        broad_fos, major_fos, detailed_fos = self.FOS.map_id_to_fields_of_science('invalid')
        self.assertEqual(broad_fos, None)
        self.assertEqual(major_fos, None)
        self.assertEqual(detailed_fos, None)

        return True

    def test_non_existent_id(self):
        broad_fos, major_fos, detailed_fos = self.FOS.map_id_to_fields_of_science('99.99')
        self.assertEqual(broad_fos, None)
        self.assertEqual(major_fos, None)
        self.assertEqual(detailed_fos, None)

        return True

    def test_partial_match(self):
        broad_fos, major_fos, detailed_fos = self.FOS.map_id_to_fields_of_science('40')
        self.assertEqual(broad_fos, 'Physical sciences')
        self.assertEqual(major_fos, None)
        self.assertEqual(detailed_fos, None)

        return True

    def test_empty_id(self):
        broad_fos, major_fos, detailed_fos = self.FOS.map_id_to_fields_of_science('')
        self.assertEqual(broad_fos, None)
        self.assertEqual(major_fos, None)
        self.assertEqual(detailed_fos, None)

        return True

    def test_na_id(self):
        broad_fos, major_fos, detailed_fos = self.FOS.map_id_to_fields_of_science(pd.NA)
        self.assertEqual(broad_fos, None)
        self.assertEqual(major_fos, None)
        self.assertEqual(detailed_fos, None)

        return True


if __name__ == '__main__':
    unittest.main()
