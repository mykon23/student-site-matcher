from argparse import ArgumentParser, ArgumentTypeError
from models.site import Site
from models.student import Student
import os
import pandas as pd


def csv_file(path: str) -> str:
    if not os.path.exists(path):
        raise ArgumentTypeError(f"File not found: {path}")

    if not path.lower().endswith(".csv"):
        raise ArgumentTypeError(f"Not a csv file: {path}")

    return path


def main(**kwargs):
    if not (sites_source := kwargs.get("sites")):
        print("No sites source provided.")
        exit(1)

    if not (students_source := kwargs.get("students")):
        print("No students source provided.")
        exit(1)

    # Read the information for the sites
    df_sites = pd.read_csv(sites_source)
    sites_data = [Site(**record) for record in df_sites.to_dict(orient="records")]
    print(sites_data)

    # Read the information for the students
    df_students = pd.read_csv(students_source)
    students_data = []
    for idx, row in df_students.iterrows():
        student = Student(
            id=row["Student ID"],
            name=f"student_name_{idx}",
            workplace=row["Workplace_2_TEXT"],
            max_distance=row["Travel_capacity"],
            other_constraints=row["Constraints_2_TEXT"],
            preferred_type=row["Preference"],
        )
        students_data.append(student)
    print(students_data)


if __name__ == "__main__":
    arg_parser = ArgumentParser(description="Script to match students to sites")
    arg_parser.add_argument(
        "--sites",
        help="Csv storing the sites for matching",
        type=csv_file,
        required=True,
    )
    arg_parser.add_argument(
        "--students",
        help="Csv storing the students to be matched",
        type=csv_file,
        required=True,
    )

    args = arg_parser.parse_args()

    main(sites=args.sites, students=args.students)
