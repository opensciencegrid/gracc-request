import os
from typing import Union
import string

import pandas as pd

# Turn this path relative to this file into an absolute path with python
# File can be downloaded here => https://ncses.nsf.gov/pubs/nsf24300/assets/technical-notes/tables/nsf24300-taba-005.xlsx
SED_CIP_FILE_RELATIVE = "./static_data/SED-CIP-2022.xlsx"
SED_CIP_FILE = os.path.join(os.path.dirname(__file__), SED_CIP_FILE_RELATIVE)

class FieldOfScience:
    """
    Maps a SED-CIP code to their string representations
    """

    def __init__(self):
        self.cip_df = self.get_cip_df()

    def map_id_to_fields_of_science(self, id: str):

        # If we have a direct match, return it
        direct_match = self.cip_df[self.cip_df["SED-CIP code"] == id]
        if len(direct_match) > 0:
            return [direct_match["New broad field"].values[0], direct_match["New major field"].values[0], direct_match["New detailed field"].values[0]]

        # Otherwise we look for the most likely match
        return self._get_most_common_match(id)

    def _get_most_common_match(self, id):
        """
        Get the most common field of science (FOS) for a given id

        It is common for a Broad ID to have multiple valid string values.

        For instance:
        16.xxxx can be mapped to "Humanities", "Other non-science and engineering", or "Social sciences"

        When we are using only a broad ID to identify a FOS we intend to have the most common value returned.

        In the case above "Humanities" is used as the Broad Field for 95% of the rows with ids 16.xxxx so this
        function would return ["Humanities", None, None] for id = 16
        """

        # Extract the partial ids
        broad_id = self._get_id(id, 0)
        major_id = self._get_id(id, 1)
        detailed_id = self._get_id(id, 2)

        # Pull out the rows that match the given ids, if none match then return empty result
        try:
            matching_rows = self._get_matching_rows(broad_id, major_id, detailed_id)
        except ValueError as e:
            return [None, None, None]

        # Define the fields we hope to populate
        broad_field_of_science = None
        major_field_of_science = None
        detailed_field_of_science = None

        # Pull out the Broad Field that occurs the most often in the matching rows
        possible_broad_fields = set(map(lambda x: x[1]['New broad field'], matching_rows.iterrows()))
        if broad_id is not None:
            best_option = None
            max_rows = 0
            for possible_broad_field in possible_broad_fields:
                l = len(self.cip_df[(self.cip_df["BroadFieldId"] == broad_id) & (self.cip_df["New broad field"] == possible_broad_field)])

                if l > max_rows:
                    max_rows = l
                    best_option = possible_broad_field

            broad_field_of_science = best_option

        # Pull out the Major Field that occurs the most often in the matching rows
        possible_major_fields = set(map(lambda x: x[1]['New major field'], matching_rows.iterrows()))
        if major_id is not None:
            best_option = None
            max_rows = 0
            for possible_major_field in possible_major_fields:
                l = len(self.cip_df[(self.cip_df["BroadFieldId"] == broad_id) & (self.cip_df['MajorFieldId'] == major_id) & (
                            self.cip_df["New major field"] == possible_major_field)])
                if l > max_rows:
                    max_rows = l
                    best_option = possible_major_field

            major_field_of_science = best_option

        # Pull out the Detailed Field that occurs the most often in the matching rows
        possible_detailed_fields = set(map(lambda x: x[1]['New detailed field'], matching_rows.iterrows()))
        if detailed_id is not None:
            best_option = None
            max_rows = 0
            for possible_detailed_field in possible_detailed_fields:
                l = len(self.cip_df[(self.cip_df["BroadFieldId"] == broad_id) & (self.cip_df['MajorFieldId'] == major_id) & (
                            self.cip_df["DetailedFieldId"] == detailed_id) & (self.cip_df["New detailed field"] == possible_detailed_field)])
                if l > max_rows:
                    max_rows = l
                    best_option = possible_detailed_field

            detailed_field_of_science = best_option

        return [broad_field_of_science, major_field_of_science, detailed_field_of_science]

    def _get_matching_rows(self, broad_id, major_id, detailed_id):
        """Get the rows that match the given broad, major, and detailed ids"""

        # Check the finest grain first
        detailed_rows = self.cip_df[
            (self.cip_df["BroadFieldId"] == broad_id) & (self.cip_df['MajorFieldId'] == major_id) & (
                    self.cip_df["DetailedFieldId"] == detailed_id)]

        if len(detailed_rows) > 0:
            return detailed_rows

        # Check the major grain
        major_rows = self.cip_df[(self.cip_df["BroadFieldId"] == broad_id) & (self.cip_df['MajorFieldId'] == major_id)]

        if len(major_rows) > 0:
            return major_rows

        # Check the broad grain
        broad_rows = self.cip_df[self.cip_df["BroadFieldId"] == broad_id]

        if len(broad_rows) > 0:
            return broad_rows

        raise ValueError(f"No matching rows for {broad_id}.{major_id}{detailed_id}")

    @staticmethod
    def _get_id(id: Union[float, str], granularity: int):
        """Get the Detailed, Broad, or Major FOS ID from a full ID"""

        # Check if None
        if pd.isna(id):
            return None

        # Fix up issues from reading the id as a float
        digits = [x for x in str(id) if x in string.digits]

        # If the first part is preceded with a 0 re-prepend it, (01.2023)
        if len(str(id).split(".")[0]) == 1:
            digits = ['0', *digits]

        # If the number ends with a 0 re-append it, (10.2320)
        if len(digits) % 2 == 1:
            digits = [*digits, '0']

        # Return the first two digits
        if granularity == 0:
            return "".join(digits[:2])

        # If there, return the next two digits
        if granularity == 1:

            if len(digits) < 4:
                return None

            return "".join(digits[2:4])

        # If there, return the last two digits
        if granularity == 2:

            if len(digits) < 6:
                return None

            return "".join(digits[4:])

        raise ValueError(f"Granularity {granularity} is not supported")

    @staticmethod
    def get_cip_df():
        """Get the CIP data as a DataFrame, adding some columns for easier querying"""

        cip_df = pd.read_excel(SED_CIP_FILE)

        # Drop the first two rows and make the third row the column title
        cip_df.columns = cip_df.iloc[2]
        cip_df = cip_df.iloc[3:]

        cip_df["BroadFieldId"] = cip_df['SED-CIP code'].apply(lambda x: FieldOfScience._get_id(x, 0))
        cip_df["MajorFieldId"] = cip_df['SED-CIP code'].apply(lambda x: FieldOfScience._get_id(x, 1))
        cip_df["DetailedFieldId"] = cip_df['SED-CIP code'].apply(lambda x: FieldOfScience._get_id(x, 2))

        return cip_df