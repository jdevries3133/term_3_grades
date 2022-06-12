import csv
from dataclasses import dataclass
from typing import Dict

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


class StudentNotFound(Exception):
    ...


@dataclass
class LiveSchoolPoint:
    date: str
    student: Student
    value: int

    @classmethod
    def from_row(cls, row: Dict[str, str]):
        student = sis.find_student(st_name := row["Student"])
        if student is None:
            raise StudentNotFound(f"could not match student to name {st_name}")
        value = int(row["Value"])

        return cls(
            date=row["Date"],
            student=student,
            value=value,
        )


class PointRecord:
    def __init__(self, student: Student):
        self.student = student
        self.cumulative_merits = 0

        # more than 3 demerits on a single day doesn't continue to adversely
        # affect grades, so we will keep track of demerits per day to ensure
        # that limit is not exceeded
        self._day_to_demerit_mapping = {}
        self._override_demerits = None

    @property
    def demerits(self):
        """Demerits that count for grade deductions: the first three demerits
        of the day."""
        if self._override_demerits is not None:
            return self._override_demerits
        return sum(v if v < 3 else 3 for v in self._day_to_demerit_mapping.values())

    @property
    def extra_demerits(self):
        """Demerits beyond the first three of the day, which don't cause grade
        deductions, but can absorb merits earned during the term and prevent
        those merits from improving the overall grade."""
        # we can't accurately calculate extra demerits when the demerit total
        # has been overriden, because demerits will be stored in a fixed value
        # and self._day_to_demerit_mapping is probably empty
        if self._override_demerits is not None:
            return 0

        return sum(v for v in self._day_to_demerit_mapping.values()) - self.demerits

    @property
    def demerits_after_merits(self):
        """Every 5 merits removes a demerit, although we also must consider
        demerits beyond three demerits per day."""
        return min(
            self.demerits,
            self.extra_demerits + self.demerits - (self.cumulative_merits // 5),
        )

    @property
    def final_points(self):
        """Each demerit deducts one point from the highest possible term grade.
        The highest possible term grade is different for fifth grade because
        they only have two music classes per week"""
        max_possible_grade = (
            MAX_GRADE_FIFTH if self.student.grade_level == 5 else MAX_GRADE_OTHER
        )
        return max_possible_grade - self.demerits_after_merits

    def record_point(self, point: LiveSchoolPoint):
        assert point.student == self.student
        # TODO: why do all that stupid parsing if I just end up turning it
        # back into a string here?...
        self._day_to_demerit_mapping.setdefault(point.date, 0)

        # when counting a demerit, assign the demerit to that day in the
        # internal mapping, and don't let demerits per day rise above three
        if point.value < 0:
            self._day_to_demerit_mapping[point.date] += abs(point.value)

        else:
            self.cumulative_merits += point.value

    def _override_cumulative_demerits_for_testing(self, value: int):
        """Set a fixed demerit value and circumvent the rule about no more than
        three demerits per day."""
        self._override_demerits = value


def get_points() -> list[LiveSchoolPoint]:
    points: list[LiveSchoolPoint] = []

    with open("data.csv", "r") as fp:
        rd = csv.DictReader(fp)
        for row in rd:
            try:
                points.append(LiveSchoolPoint.from_row(row))
            except StudentNotFound:
                print(f'warning: did not find {row["Student"]}')

    return points


def main():
    points = get_points()
    records = {n: PointRecord(s) for n, s in sis.students.items()}

    for p in points:
        record = records[p.student.name]
        record.record_point(p)

    for r in records.values():
        print(f"{r.student.name}\t{r.final_points}")


if __name__ == "__main__":
    main()
