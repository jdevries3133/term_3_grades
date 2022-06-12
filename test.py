from dataclasses import dataclass
import unittest

from teacherhelper.sis import Sis

from main import MAX_GRADE_FIFTH, MAX_GRADE_OTHER, LiveSchoolPoint, PointRecord, StudentNotFound

sis = Sis.read_cache()


class BaseCase(unittest.TestCase):
    def setUp(self):
        # the first student (basically a random student)
        self.test_student = sis.students[list(sis.students.keys())[0]]

        self.example_rows = [
            # demerit example
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
            # merit example
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
            # name won't match example
            {
                "Date": "Wed, 12/2",
                "Time": "1:34 p.m.",
                "Teacher": "Mr. Devries",
                "Roster": "Homeroom 4 - Carrie -",
                # hopefully no one has this name, for the relevant test case to work...
                "Student": "ferageragwagrwegerbaerberabebtetabetbateaebaefadbfadbdfberbebtetafdbdfabtebtahbntabatbtabeberbeabtaebbaettbetbaet",
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
        points = [LiveSchoolPoint.from_row(row) for row in self.example_rows[0:2]]

        self.points = Points(merit=points[1], demerit=points[0])

    def test_record_point(self):

        self.rec.record_point(self.points.demerit)

        self.assertEqual(self.rec.demerits_after_merits, 1)

        # adjusted demerits does not change because we just go from 0 to 1
        # point. The demerit won't go away until we record 5 merits
        self.rec.record_point(self.points.merit)
        self.assertEqual(self.rec.demerits_after_merits, 1)

        for _ in range(1, 5):
            # more than 3 self.points on the same point don't affect the total grade,
            # so we will keep changing the date to ensure these repeated self.points
            # have an effect
            self.rec.record_point(self.points.merit)

        # now that there are 5 points, the adjusted total goes back down to zero
        self.assertEqual(self.rec.demerits_after_merits, 0)

        # but if we add another demerit, it goes back to 1
        self.rec.record_point(self.points.demerit)
        self.assertEqual(self.rec.demerits_after_merits, 1)

    def test_record_point_3_point_demerit_limit(self):
        # as stated earlier, more than 3 self.points on the same day shouldn't have
        # an effect
        for _ in range(20):
            self.rec.record_point(self.points.demerit)
        self.assertEqual(self.rec.demerits_after_merits, 3)

    def test_record_point_no_merit_limit(self):
        for _ in range(20):
            self.rec.record_point(self.points.merit)
        self.assertEqual(self.rec.cumulative_merits, 20)

    def test_extra_demerits(self):
        for _ in range(20):
            self.rec.record_point(self.points.demerit)
        self.assertEqual(self.rec.extra_demerits, 17)

    def test_adjusted_demerits_uses_lower_adjusted_value_when_many_extras_are_present(
        self,
    ):
        for _ in range(20):
            self.rec.record_point(self.points.demerit)
        for _ in range(2):
            self.rec.record_point(self.points.merit)
        self.assertEqual(self.rec.demerits_after_merits, 3)

    def test_grade_cannot_exceed_max(self):
        for _ in range(100):
            self.rec.record_point(self.points.merit)
        self.test_student.grade_level = 5
        self.assertEqual(self.rec.final_points, MAX_GRADE_FIFTH)
        self.test_student.grade_level = 6
        self.assertEqual(self.rec.final_points, MAX_GRADE_OTHER)

    def test_final_points(self):
        cases = (
            # merits, demerits (override), grade_level, expected_total
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
        self.assertEqual(self.rec.demerits, 20)

        self.rec._override_cumulative_demerits_for_testing(31)
        self.assertEqual(self.rec.demerits, 31)


class TestLiveSchoolPoint(BaseCase):
    def test_from_row(self):
        result = LiveSchoolPoint.from_row(self.example_rows[0])
        self.assertIsInstance(result, LiveSchoolPoint)

    def test_student_not_found(self):
        with self.assertRaisesRegex(StudentNotFound, "could not match student to name"):
            LiveSchoolPoint.from_row(self.example_rows[2])


if __name__ == "__main__":
    unittest.main()
