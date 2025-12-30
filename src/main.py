from argparse import ArgumentParser, ArgumentTypeError
from datetime import datetime
from models.site import Site
from models.student import Student
from enums import Distance
import os
import pandas as pd
from pathlib import Path
import re
from typing import Dict, List, Tuple


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

    # Read the information for the students
    df_students = pd.read_csv(students_source).fillna("")
    students_data = []
    for idx, row in df_students.iterrows():
        # Skip values that do not correspond to actual student ids
        if not (id := row["Student ID"]):
            print(f"Skipping row {idx} due to missing ID")
            continue

        # Set a default name if one is not provided
        name = f"FirstName LastName {idx}"
        if "Student Name" in df_students.columns:
            name = row["Student Name"]

        # Determine the distance via regex
        distance = 0
        travel_capacity = row["Travel_capacity"]
        if re.search(r"\w*10.15\s*mile.*", travel_capacity):
            distance = Distance.UP_TO_15_MILES.value
        elif re.search(r"\w*20.30\s*mile*", travel_capacity):
            distance = Distance.UP_TO_30_MILES.value
        elif re.search(
            r".*no.*transportation.*",
            travel_capacity,
            re.IGNORECASE,
        ):
            distance = Distance.NO_TRANSPORTATION.value
        elif re.search(
            r".*need.*site.*within.*",
            travel_capacity,
            re.IGNORECASE,
        ):
            distance = Distance.WITHIN_IOWA_CITY_CORALVILLE_NORTH_LIBERTY.value
        else:
            print(f"Unable to convert record {idx} travel capacity {travel_capacity}")
            continue
        student = Student(
            id=id,
            name=name,
            workplace=row["Workplace_2_TEXT"],
            max_distance=distance,
            other_constraints=row["Constraints_2_TEXT"],
            preferred_type=row["Preference"],
        )
        students_data.append(student)

    assignments, unassigned = match_students_to_sites(students_data, sites_data)

    # output the results
    destination = os.path.join(Path(__file__).parent.parent / "output", f"assignments-{datetime.now().isoformat()}")
    df_output = pd.DataFrame(assignments)
    df_output.to_csv(destination, index=False)

    print(f"Assignments written to {destination}")
    print(f"Remaining site capacity:")
    for site in sites_data:
        print(f"Site {site.name} ({site.id}): {site.capacity} spots left")

    if unassigned:
        print("Students without feasible match (need manual review):")
        for us in unassigned:
            print(f"{us.name} (ID: {us.id})")


def rank_feasible_sites(student: Student, sites: List[Site]) -> List[Site]:
    feasible = []

    for site in sites:
        if site.capacity == 0:
            continue
        if is_employment_conflict(student, site):
            continue
        if not site_within_travel_capacity(student, site):
            continue
        feasible.append(site)

    """
     Sort the sites according to the following criteria: 
     1. Preferred type
     2. distance
     3. capacity to balance the loade
    """

    def sort_key(site: Site):
        preference = 0
        if student.preferred_type and (
            student.preferred_type.lower() == site.type.lower()
        ):
            preference = 1
        return (preference, site.distance, site.capacity)

    feasible.sort(key=sort_key)
    return feasible


def match_students_to_sites(students: List[Student], sites: List[Site]) -> Tuple[Dict]:

    # Sort the students according to max distance of travel
    students.sort(key=lambda s: s.max_distance)

    # Set a collection of assignment and unassigned
    assignments = []
    unassigned = []

    for student in students:
        feasible_sites = rank_feasible_sites(student, sites)

        if not feasible_sites:
            unassigned.append(student)
            assignments.append(
                {
                    "id": student.id,
                    "name": student.name,
                    "assigned_site_id": "",
                    "assigned_site_name": "",
                    "reason": "No feasible site found within travel capacity and capacity constraints.",
                }
            )
            continue

        # Update the capacity data store now that a student is assigned
        chosen_site = feasible_sites[0]
        chosen_site.capacity -= 1

        reason_parts = []
        reason_parts.append(
            f"Within {student.max_distance} miles and (site_distance {chosen_site.distance} miles)"
        )
        if student.preferred_type and (
            student.preferred_type.lower() == chosen_site.type.lower()
        ):
            reason_parts.append(
                f"Matches preferred setting type: {student.preferred_type}."
            )

        if is_employment_conflict(student, chosen_site):
            reason_parts.append(
                "WARNING: employment conflict detected (check manually)"
            )

        assignments.append(
            {
                "id": student.id,
                "name": student.name,
                "assigned_site_id": chosen_site.id,
                "assigned_site_name": chosen_site.name,
                "assigned_site_type": chosen_site.type,
                "reason": "".join(reason_parts),
            }
        )

    return assignments, unassigned


def is_employment_conflict(student: Student, site: Site) -> bool:
    """
    Determinines whether the students and sites are void of conflict
    """
    if not student.workplace:
        return False

    student_workplace = student.workplace.lower()
    site_name = site.name.lower()

    # Check the overlap between the two strings
    return student_workplace in site_name or site_name in student_workplace


def site_within_travel_capacity(student: Student, site: Site) -> bool:
    """
    Returns whether the site is within the student travel distance
    """
    return student.max_distance >= site.distance


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
