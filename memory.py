# Shared state used by the agents during one student session

shared_state = {
    "student_profile": {},
    "candidate_majors": [],
    "candidate_major_reasons": {},
    "university_results": [],
    "final_recommendations": []
}


def create_student_profile(
    grades,
    strong_subjects,
    interests,
    skills,
    hobbies,
    preferred_work,
    budget,
    location,
    can_relocate,
    can_live_in_dorm
):
    """
    Create a structured student profile.
    """

    profile = {
        "grades": grades,
        "strong_subjects": strong_subjects,
        "interests": interests,
        "skills": skills,
        "hobbies": hobbies,
        "preferred_work": preferred_work,
        "budget": budget,
        "location": location,
        "can_relocate": can_relocate,
        "can_live_in_dorm": can_live_in_dorm
    }

    shared_state["student_profile"] = profile

    return profile


def get_student_profile():
    """
    Return the current student profile.
    """

    return shared_state["student_profile"]


def save_candidate_majors(majors):
    """
    Save the majors suggested by the Major Matching Agent.
    """

    shared_state["candidate_majors"] = majors


def save_candidate_major_reasons(reasons):
    """
    Save the reason associated with each candidate major.

    Example:

    {
        "Translation":
            "Strong subjects in Arabic and English support this major."
    }
    """

    shared_state["candidate_major_reasons"] = reasons


def save_university_results(results):
    """
    Save university information found by
    the University Research Agent.
    """

    shared_state["university_results"] = results


def save_final_recommendations(recommendations):
    """
    Save the final recommendations.
    """

    shared_state["final_recommendations"] = recommendations


def get_shared_state():
    """
    Return all information currently stored in memory.
    """

    return shared_state


def reset_memory():
    """
    Clear the state before starting with a new student.
    """

    shared_state["student_profile"] = {}

    shared_state["candidate_majors"] = []

    shared_state["candidate_major_reasons"] = {}

    shared_state["university_results"] = []

    shared_state["final_recommendations"] = []
