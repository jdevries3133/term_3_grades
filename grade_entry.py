"""Script for grade entry into oncourse"""

from time import sleep

import pyautogui as pg
from teacherhelper.sis import Sis, Student

from main import get_grade_records, get_points


sis = Sis.read_cache()


CODE_TO_TEACHER = {
    "7A": "Espiritu, Melissa",
    "6E": "Shuzman, Adam",
    "7B": "Davis, Shondell",
    "7E": "Baurkot, Juliana",
    "7C": "Zhu, Zhu",
    "7D": "Regan, Katelyn",
    "6C": "Zou, Jiying",
    "6D": "Chung, Soyoun",
    "5D": "Silvestri, Melissa",
    "6A": "Irizarry, Gina",
    "6B": "Saadeh, Salwa",
    "5C": "Armstead, Joseph",
    "5B": "Geltzeiler, Katelyn",
    "5A": "Kassalow, Anne",
    "4B": "DuVal, Dina",
    "5E": "Ruffee, Michele",
    "4E": "Carrie, Jannine",
    "4C": "Morrow, Lisa",
    "4E": "Chartier, Jessica",
    "4D": "Rodriguez, Joseph",
    "4A": "McNeill, Kaity",
}


NAME_TO_RECORD_MAPPING = get_grade_records(get_points())


def get_sorted_homeroom_students(homeroom_code: str):
    hr = sis.homerooms[CODE_TO_TEACHER[homeroom_code]]

    return sorted(hr.students, key=lambda s: s.last_name)



def get_grade_value(s: Student) -> str | None:
    """Return the literal value to be typed into the OnCourse text box"""
    record = NAME_TO_RECORD_MAPPING.get(s.name)

    if record is None:
        return None

    return str(record.final_points)


def main():
    while True:
        homeroom_code = input("enter current homeroom: ").upper()
        if homeroom_code not in CODE_TO_TEACHER:
            print("error: unacceptable homeroom code")
            continue

        students = get_sorted_homeroom_students(homeroom_code)

        print("focus first text box now!!")
        for i in range(5, 0, -1):
            print(i)
            sleep(0.5)
        for s in students:
            if (grade := get_grade_value(s)) is not None:
                pg.typewrite(grade)
            pg.press("down")


if __name__ == '__main__':
    main()

