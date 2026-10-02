from memory import (
    reset_memory,
    create_student_profile
)

from agents import supervisor_agent


# ==================================================
# INPUT HELPERS
# ==================================================

def ask_list(prompt):
    """
    Read comma-separated values and return a clean list.
    """

    value = input(prompt).strip()

    if not value:
        return []

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


def ask_grades():
    """
    Ask the student to enter grades using:

    Math=85, English=90, Physics=78
    """

    while True:

        value = input(
            "\nEnter your grades "
            "(example: Math=85, English=90): "
        ).strip()

        if not value:
            return {}

        grades = {}

        try:

            entries = value.split(",")

            for entry in entries:

                subject, grade = entry.split(
                    "=",
                    1
                )

                subject = subject.strip()

                grade = float(
                    grade.strip()
                )

                # Store whole numbers as integers
                if grade.is_integer():
                    grade = int(
                        grade
                    )

                grades[
                    subject
                ] = grade

            return grades

        except ValueError:

            print(
                "\nInvalid format."
            )

            print(
                "Please use something like:"
            )

            print(
                "Math=85, English=90, Physics=78"
            )


def ask_budget():
    """
    Ask for the yearly university budget.
    """

    while True:

        value = input(
            "\nApproximate yearly university "
            "budget in USD: "
        ).strip()

        try:

            budget = float(
                value
            )

            if budget.is_integer():
                budget = int(
                    budget
                )

            return budget

        except ValueError:

            print(
                "Please enter a number, "
                "for example: 8000"
            )


def ask_yes_no(prompt):
    """
    Convert yes/no input into True/False.
    """

    while True:

        value = input(
            prompt
        ).strip().lower()

        if value in [
            "yes",
            "y"
        ]:
            return True

        if value in [
            "no",
            "n"
        ]:
            return False

        print(
            "Please enter yes or no."
        )


# ==================================================
# MAIN PROGRAM
# ==================================================

def main():

    print(
        "\n=========================================="
    )

    print(
        "AI UNIVERSITY GUIDANCE AGENT"
    )

    print(
        "Grade 12 Students in Lebanon"
    )

    print(
        "=========================================="
    )

    print(
        "\nPlease answer the following questions."
    )

    # Clear any previous student session
    reset_memory()

    # --------------------------------------------------
    # Student information
    # --------------------------------------------------

    grades = ask_grades()

    strong_subjects = ask_list(
        "\nStrong subjects "
        "(comma separated): "
    )

    interests = ask_list(
        "\nInterests "
        "(comma separated): "
    )

    skills = ask_list(
        "\nSkills "
        "(comma separated): "
    )

    hobbies = ask_list(
        "\nHobbies "
        "(comma separated): "
    )

    preferred_work = input(
        "\nWhat type of work would you "
        "prefer in the future? "
    ).strip()

    budget = ask_budget()

    location = input(
        "\nWhere do you currently live "
        "in Lebanon? "
    ).strip()

    can_relocate = ask_yes_no(
        "\nAre you willing to relocate "
        "to another area? (yes/no): "
    )

    can_live_in_dorm = ask_yes_no(
        "\nAre you willing to live in "
        "a university dorm? (yes/no): "
    )

    # --------------------------------------------------
    # Create shared student profile
    # --------------------------------------------------

    create_student_profile(
        grades=grades,
        strong_subjects=strong_subjects,
        interests=interests,
        skills=skills,
        hobbies=hobbies,
        preferred_work=preferred_work,
        budget=budget,
        location=location,
        can_relocate=can_relocate,
        can_live_in_dorm=can_live_in_dorm
    )

    # --------------------------------------------------
    # Start multi-agent workflow
    # --------------------------------------------------

    print(
        "\n\nStarting university guidance analysis..."
    )

    print(
        "This may take several minutes because "
        "official university sources are checked."
    )

    result = supervisor_agent()

    # --------------------------------------------------
    # Final result
    # --------------------------------------------------

    print(
        "\n\n=========================================="
    )

    print(
        "FINAL GUIDANCE"
    )

    print(
        "==========================================\n"
    )

    print(
        result
    )


# ==================================================
# PROGRAM ENTRY POINT
# ==================================================

if __name__ == "__main__":
    main()
