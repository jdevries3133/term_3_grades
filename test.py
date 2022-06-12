from dataclasses import dataclass
from datetime import datetime
import unittest

from teacherhelper.sis import Sis

from main import DEFAULT_YEAR, LiveSchoolPoint, PointRecord

sis = Sis.read_cache()


class BaseCase(unittest.TestCase):
    def setUp(self):
        # the first student (basically a random student)
        self.test_student = sis.students[list(sis.students.keys())[0]]

        self.example_rows = [
            {
                "Date": "Tue, 2/22",
                "Time": "12:57 p.m.",
                "Teacher": "Mr. Devries",
                "Roster": "Homeroom 7",
                "Student": self.test_student.name,
                "Item": "Classroom Misconduct",
                "Category": "2. S.T.A.R. Behaviors",
                "Value": "-1",
                "Location": "Classroom",
                "Comment": "repeatedly having conversations and derailing the lesson",
            },
            {
                "Date": "Wed, 12/2",
                "Time": "1:34 p.m.",
                "Teacher": "Mr. Devries",
                "Roster": "Homeroom 4 - Carrie -",
                "Student": self.test_student.name,
                "Item": "Respectful to Staff and Students",
                "Category": "S.T.A.R. Behaviors",
                "Value": "1",
                "Location": "Classroom",
                "Comment": "",
            },
        ]


class TestPointRecord(BaseCase):
    def setUp(self):
        super().setUp()

        @dataclass
        class Points:
            merit: LiveSchoolPoint
            demerit: LiveSchoolPoint

        self.rec = PointRecord(self.test_student)
        points = [LiveSchoolPoint.from_row(row) for row in self.example_rows]

        self.points = Points(merit=points[1], demerit=points[0])

    def test_record_point(self):

        self.rec.record_point(self.points.demerit)

        self.assertEqual(self.rec.adjusted_demerits, 1)

        # adjusted demerits does not change because we just go from 0 to 1
        # point. The demerit won't go away until we record 5 merits
        self.rec.record_point(self.points.merit)
        self.assertEqual(self.rec.adjusted_demerits, 1)

        for _ in range(1, 5):
            # more than 3 self.points on the same point don't affect the total grade,
            # so we will keep changing the date to ensure these repeated self.points
            # have an effect
            self.rec.record_point(self.points.merit)

        # now that there are 5 points, the adjusted total goes back down to zero
        self.assertEqual(self.rec.adjusted_demerits, 0)

        # but if we add another demerit, it goes back to 1
        self.rec.record_point(self.points.demerit)
        self.assertEqual(self.rec.adjusted_demerits, 1)

    def test_record_point_3_point_demerit_limit(self):
        # as stated earlier, more than 3 self.points on the same day shouldn't have
        # an effect
        for _ in range(20):
            self.rec.record_point(self.points.demerit)
        self.assertEqual(self.rec.adjusted_demerits, 3)

    def test_record_point_no_merit_limit(self):
        for _ in range(20):
            self.rec.record_point(self.points.merit)
        self.assertEqual(self.rec.cumulative_merits, 20)

    def test_final_points(self):
        cases = (
            # merits, demerits, grade_level, expected_total
            (7, 4, 6, 69),
            (8, 5, 7, 68),
            (3, 9, 5, 27),
        )

        for merits, demerits, grade_level, expected_total in cases:
            self.rec.cumulative_merits = merits
            self.rec._override_cumulative_demerits_for_testing(demerits)
            self.test_student.grade_level = grade_level
            self.assertEqual(self.rec.final_points, expected_total)

    def test_demerit_overrider(self):
        self.rec._override_cumulative_demerits_for_testing(20)
        self.assertEqual(self.rec.cumulative_demerits, 20)

        self.rec._override_cumulative_demerits_for_testing(31)
        self.assertEqual(self.rec.cumulative_demerits, 31)


class TestLiveSchoolPoint(BaseCase):
    def test_from_row(self):
        result = LiveSchoolPoint.from_row(self.example_rows[0])
        self.assertIsInstance(result, LiveSchoolPoint)

    def test_parse_date(self):
        cases = (
            ("Tuesday, 3/23", datetime(DEFAULT_YEAR, 3, 23)),
            ("Wed, 12/2", datetime(DEFAULT_YEAR, 12, 2)),
            ("Wed, 10/05", datetime(DEFAULT_YEAR, 10, 5)),
        )
        for input, output in cases:
            self.assertEqual(LiveSchoolPoint.parse_date(input), output)

        with self.assertRaisesRegex(ValueError, "could not parse date"):
            LiveSchoolPoint.parse_date("Monday 2/")


if __name__ == "__main__":
    unittest.main()
