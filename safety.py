import re


# ==================================================
# PROMPT-INJECTION DETECTION
# ==================================================

INJECTION_PATTERNS = [
    r"ignore (all|any|the|your|previous) instructions",
    r"ignore previous",
    r"forget (all|your|the) instructions",
    r"reveal (the|your) system prompt",
    r"show (the|your) system prompt",
    r"developer message",
    r"system message",
    r"jailbreak",
    r"override your instructions",
    r"act as if there are no rules"
]


def contains_prompt_injection(text):
    """
    Check whether a text value contains common
    prompt-injection language.
    """

    if not isinstance(text, str):
        return False

    normalized_text = text.lower()

    for pattern in INJECTION_PATTERNS:

        if re.search(
            pattern,
            normalized_text
        ):
            return True

    return False


# ==================================================
# PROFILE VALIDATION
# ==================================================

def validate_student_profile(profile):
    """
    Validate the student's information before agents use it.

    Returns:
    {
        "is_safe": True/False,
        "errors": [...],
        "warnings": [...]
    }
    """

    errors = []
    warnings = []

    if not isinstance(profile, dict):

        return {
            "is_safe": False,
            "errors": [
                "Student profile must be a dictionary."
            ],
            "warnings": []
        }

    # --------------------------------------------------
    # Grades
    # --------------------------------------------------

    grades = profile.get(
        "grades",
        {}
    )

    if not isinstance(
        grades,
        dict
    ):
        errors.append(
            "Grades must be provided as a dictionary."
        )

    else:

        for subject, grade in grades.items():

            if not isinstance(
                grade,
                (int, float)
            ):
                errors.append(
                    f"Grade for {subject} must be numeric."
                )

                continue

            if grade < 0 or grade > 100:

                errors.append(
                    f"Grade for {subject} must be between 0 and 100."
                )

    # --------------------------------------------------
    # Budget
    # --------------------------------------------------

    budget = profile.get(
        "budget"
    )

    if not isinstance(
        budget,
        (int, float)
    ):
        errors.append(
            "Budget must be numeric."
        )

    elif budget < 0:

        errors.append(
            "Budget cannot be negative."
        )

    # --------------------------------------------------
    # Boolean values
    # --------------------------------------------------

    for field in [
        "can_relocate",
        "can_live_in_dorm"
    ]:

        if not isinstance(
            profile.get(field),
            bool
        ):
            errors.append(
                f"{field} must be True or False."
            )

    # --------------------------------------------------
    # Required text/list information
    # --------------------------------------------------

    list_fields = [
        "strong_subjects",
        "interests",
        "skills",
        "hobbies"
    ]

    for field in list_fields:

        value = profile.get(
            field,
            []
        )

        if not isinstance(
            value,
            list
        ):
            errors.append(
                f"{field} must be a list."
            )

            continue

        if len(value) == 0:

            warnings.append(
                f"{field} is empty."
            )

    # --------------------------------------------------
    # Prompt injection check
    # --------------------------------------------------

    text_values = []

    for field in list_fields:

        value = profile.get(
            field,
            []
        )

        if isinstance(
            value,
            list
        ):

            text_values.extend(
                str(item)
                for item in value
            )

    text_values.append(
        str(
            profile.get(
                "preferred_work",
                ""
            )
        )
    )

    text_values.append(
        str(
            profile.get(
                "location",
                ""
            )
        )
    )

    for text in text_values:

        if contains_prompt_injection(
            text
        ):

            errors.append(
                "Potential prompt-injection text "
                "was detected in the student profile."
            )

            break

    # --------------------------------------------------
    # Result
    # --------------------------------------------------

    return {
        "is_safe": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


# ==================================================
# UNTRUSTED WEB CONTENT
# ==================================================

def check_untrusted_web_content(text):
    """
    Check retrieved webpage text for prompt-injection language.

    University webpage content must be treated as data,
    not as instructions for the agent.
    """

    if contains_prompt_injection(
        text
    ):

        return {
            "safe": False,
            "reason": (
                "Possible prompt-injection instructions "
                "were found in retrieved webpage content."
            )
        }

    return {
        "safe": True,
        "reason": None
    }


# ==================================================
# FINAL OUTPUT SAFETY MESSAGE
# ==================================================

def guidance_disclaimer():
    """
    Standard reminder added to educational guidance.
    """

    return (
        "This system provides educational guidance only. "
        "Students should verify current program, tuition, "
        "admission, and financial-aid information directly "
        "with the university before making a final decision."
    )
