import csv
from dataclasses import dataclass
from datetime import datetime
import re
from typing import cast

from teacherhelper.sis import Sis, Student

sis = Sis.read_cache()

# liveschool doesn't include the year, so we need to hard code it.
DEFAULT_YEAR = 2022

WEEKS_IN_TERM = 12
MAX_POINTS_PER_CLASS = 3

MAX_GRADE_FIFTH = WEEKS_IN_TERM * MAX_POINTS_PER_CLASS

MAX_GRADE_OTHER = (
    MAX_GRADE_FIFTH
    * 2  # 4th, 6th, and 7th graders have 2 classes per week instead of 1 in
    # fifth
)


@dataclass
class LiveSchoolPoint:
    date: datetime
    student: Student
    value: int

    @classmethod
    def from_row(cls, row: dict[str, str]):
        date = cls.parse_date(row["Date"])
        student = sis.find_student(st_name := row["Student"])
        if student is None:
            raise Exception(f"could not match student to name {st_name}")
        value = int(row["Value"])

        return cls(
            date=date,
            student=student,
            value=value,
        )

    @staticmethod
    def parse_date(date: str) -> datetime:
        """LiveSchool dates are in the form `Mon, 3/23`, where dates are not
        zero-padded, all day strings are abbreivated with three letters, and
        there is a comma and space in-between. The year is not provided, so we
        refer to a global default year."""
        pattern = re.compile(
            r"""
                (?P<month>\d{1,2})
                /
                (?P<day>\d{1,2})
            """,
            re.VERBOSE,
        )
        mo = pattern.search(date)
        if mo is None:
            raise ValueError(f"could not parse date {date}")

        month = int(mo.group("month"))
        day = int(mo.group("day"))

        return datetime(month=month, day=day, year=DEFAULT_YEAR)


class PointRecord:
    def __init__(self, student: Student):
        self.student = student
        self.cumulative_merits = 0

        # more than 3 demerits on a single day doesn't continue to adversely
        # affect grades, so we will keep track of demerits per day to ensure
        # that limit is not exceeded
        self._day_to_demerit_mapping = {}

    @property
    def cumulative_demerits(self):
        return sum(v for v in self._day_to_demerit_mapping.values())

    @property
    def adjusted_demerits(self):
        return self.cumulative_demerits - (self.cumulative_merits // 5)

    @property
    def final_points(self):
        max_grade = (
            MAX_GRADE_FIFTH if self.student.grade_level == 5 else MAX_GRADE_OTHER
        )
        return max_grade - self.adjusted_demerits

    def record_point(self, point: LiveSchoolPoint):
        assert point.student == self.student
        # TODO: why do all that stupid parsing if I just end up turning it
        # back into a string here?...
        day_identifier = f"{point.date.month}-{point.date.day}"
        self._day_to_demerit_mapping.setdefault(day_identifier, 0)

        # when counting a demerit, assign the demerit to that day in the
        # internal mapping, and don't let demerits per day rise above three
        if point.value < 0:
            self._day_to_demerit_mapping[day_identifier] += abs(point.value)
            if self._day_to_demerit_mapping[day_identifier] > 3:
                self._day_to_demerit_mapping[day_identifier] = 3

        else:
            self.cumulative_merits += point.value

    def _override_cumulative_demerits_for_testing(self, value: int):
        self._day_to_demerit_mapping = {'override': value}


def main():
    with open("data.csv", "r") as fp:
        rd = csv.DictReader(fp)
        for row in rd:
            print(row)


if __name__ == "__main__":
    main()
