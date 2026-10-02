import json
import re

from ollama import chat

from memory import (
    get_student_profile,
    get_shared_state,
    save_candidate_majors,
    save_candidate_major_reasons,
    save_university_results,
    save_final_recommendations
)

from university_tools import (
    search_programs,
    get_university_details
)

from safety import (
    validate_student_profile,
    guidance_disclaimer
)

# ==================================================
# MODELS
# ==================================================

MODEL = "qwen3:0.6b"
MAJOR_MODEL = "qwen3:4b"
RECOMMENDATION_MODEL = "qwen3:4b"


# ==================================================
# 1. STUDENT PROFILE AGENT
# ==================================================

def student_profile_agent():
    """
    Summarize the student's profile without inventing
    academic strengths or other information.
    """

    profile = get_student_profile()

    if not profile:
        return (
            "No student profile is available."
        )

    grades = profile.get(
        "grades",
        {}
    )

    strong_subjects = profile.get(
        "strong_subjects",
        []
    )

    interests = profile.get(
        "interests",
        []
    )

    skills = profile.get(
        "skills",
        []
    )

    hobbies = profile.get(
        "hobbies",
        []
    )

    preferred_work = profile.get(
        "preferred_work",
        ""
    )

    budget = profile.get(
        "budget"
    )

    location = profile.get(
        "location",
        ""
    )

    can_relocate = profile.get(
        "can_relocate",
        False
    )

    can_live_in_dorm = profile.get(
        "can_live_in_dorm",
        False
    )

    # ----------------------------------------------
    # Format grades exactly as supplied
    # ----------------------------------------------

    grade_text = ", ".join(
        f"{subject}: {grade}"
        for subject, grade
        in grades.items()
    )

    strong_subject_text = ", ".join(
        strong_subjects
    )

    interest_text = ", ".join(
        interests
    )

    skills_text = ", ".join(
        skills
    )

    hobbies_text = ", ".join(
        hobbies
    )

    # ----------------------------------------------
    # Identify missing information
    # ----------------------------------------------

    missing = []

    if not grades:
        missing.append(
            "grades"
        )

    if not strong_subjects:
        missing.append(
            "strong subjects"
        )

    if not interests:
        missing.append(
            "interests"
        )

    if not skills:
        missing.append(
            "skills"
        )

    if not hobbies:
        missing.append(
            "hobbies"
        )

    if not preferred_work:
        missing.append(
            "preferred work"
        )

    # ----------------------------------------------
    # Build grounded summary
    # ----------------------------------------------

    lines = [
        (
            "Declared strong subjects: "
            + (
                strong_subject_text
                if strong_subject_text
                else "Not provided"
            )
        ),
        (
            "Grades: "
            + (
                grade_text
                if grade_text
                else "Not provided"
            )
        ),
        (
            "Interests: "
            + (
                interest_text
                if interest_text
                else "Not provided"
            )
        ),
        (
            "Skills: "
            + (
                skills_text
                if skills_text
                else "Not provided"
            )
        ),
        (
            "Hobbies: "
            + (
                hobbies_text
                if hobbies_text
                else "Not provided"
            )
        ),
        (
            "Preferred work: "
            + (
                preferred_work
                if preferred_work
                else "Not provided"
            )
        ),
        f"Budget: {budget}",
        f"Location: {location}",
        (
            "Can relocate: "
            + (
                "Yes"
                if can_relocate
                else "No"
            )
        ),
        (
            "Can live in dorm: "
            + (
                "Yes"
                if can_live_in_dorm
                else "No"
            )
        )
    ]

    if missing:

        lines.append(
            "Missing information: "
            + ", ".join(
                missing
            )
        )

    else:

        lines.append(
            "Missing information: None"
        )

    return "\n".join(
        lines
    )

# ==================================================
# 2. MAJOR MATCHING AGENT
# ==================================================

def major_matching_agent():
    """
    Suggest five suitable university majors/pathways using
    the student's complete profile.

    The LLM first generates 10 candidate majors.
    Python then applies deterministic preference guardrails
    and keeps the first five suitable candidates.
    """

    profile = get_student_profile()

    if not profile:
        return "No student profile is available."

    # ==================================================
    # STRUCTURED OUTPUT SCHEMA
    # ==================================================

    major_schema = {
        "type": "object",
        "properties": {
            "majors": {
                "type": "array",
                "minItems": 10,
                "maxItems": 10,
                "items": {
                    "type": "object",
                    "properties": {
                        "major": {
                            "type": "string"
                        },
                        "reason": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "major",
                        "reason"
                    ]
                }
            }
        },
        "required": [
            "majors"
        ]
    }

    # ==================================================
    # MAJOR MATCHING INSTRUCTIONS
    # ==================================================

    system_prompt = """
You are the Major Matching Agent in a university guidance
system for Grade 12 students in Lebanon.

Generate exactly 10 candidate university majors or educational
pathways, ordered from strongest fit to weakest fit.

Evaluate the student's COMPLETE profile.

PRIORITY ORDER:

1. Explicit preferred type of work and work environment.
2. Strong subjects and academic grades.
3. Interests and motivations.
4. Skills.
5. Hobbies only as supporting evidence.

IMPORTANT RULES:

- Do not simply turn a strong school subject into a major.

  Example:
  Strong Biology does not automatically mean Biology.
  Strong Physics does not automatically mean Physics.
  Strong Chemistry does not automatically mean Chemistry.

- Prefer professional or career-oriented pathways when the
  student's academic strengths, interests, skills, and work
  preferences point toward a clear profession.

- A candidate should normally be supported by at least TWO
  meaningful pieces of evidence from the student's profile.

- Explicit work preferences are extremely important.

- If the student clearly says they do not want laptop-based,
  computer-centered, screen-centered, or desk-centered work,
  avoid computer-heavy majors such as:

  Computer Science
  Data Science
  Software Engineering
  Information Technology
  Information Systems
  Artificial Intelligence
  Cybersecurity
  Health Informatics
  Computer Engineering

- If the student says they are comfortable with laptop or
  computer-based work, do not treat computer-heavy fields
  as automatically unsuitable.

- Do not recommend Communication Studies simply because the
  student lists communication as a skill.

- Do not recommend Data Science simply because the student
  lists analysis as a skill.

- Do not recommend Biology, Physics, Chemistry, or Mathematics
  merely because the student has strong grades in those
  subjects when their complete profile points toward a more
  applied professional pathway.

- For students who have strong science performance, enjoy
  helping people, have communication, analytical, or strong
  memorization skills, consider suitable health professions
  when appropriate.

  Examples may include:

  Medicine
  Physiotherapy
  Nursing
  Nutrition and Dietetics
  Pharmacy
  Medical Laboratory Sciences
  Occupational Therapy
  Dentistry
  or another suitable health profession.

- Medicine should not automatically be excluded because one
  additional subject was not provided.

- Pharmacy should be considered when the profile contains
  strong Biology and Chemistry performance together with
  analytical or memorization skills and an interest in
  helping people.

- Medicine should be considered when the profile contains
  very strong science performance together with relevant
  interests and skills such as helping people, communication,
  analysis, or strong memorization.

- Missing information should not automatically eliminate an
  otherwise strong career option.

- A low grade in one subject should be considered where
  relevant, but do not invent admission rules or automatically
  reject a major unless there is a clear reason.

- Recommend distinct, recognized university majors or
  educational pathways.

- Do not recommend universities in this step.

- Do not invent admission requirements.

For every candidate, explain briefly why it fits this specific
student using ONLY information explicitly present in the
student's profile.

Do not infer or invent preferences, motivations, personality
traits, abilities, or work environments that the student did
not provide.

If a preference was not stated, do not claim that the student
has that preference.

Every reason must be traceable to actual fields in the
student profile.

Return only the required structured output.
"""

    # ==================================================
    # CALL THE LLM
    # ==================================================

    response = chat(
        model=MAJOR_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": (
                    "Student profile:\n"
                    + json.dumps(
                        profile,
                        indent=2,
                        ensure_ascii=False
                    )
                )
            }
        ],
        think=False,
        format=major_schema,
        options={
            "temperature": 0
        }
    )

    # ==================================================
    # PARSE STRUCTURED OUTPUT
    # ==================================================

    try:
        data = json.loads(
            response.message.content
        )

    except json.JSONDecodeError:

        return (
            "The Major Matching Agent could not "
            "produce valid structured output."
        )

    major_items = data.get(
        "majors",
        []
    )

    # ==================================================
    # GUARDRAIL 1:
    # DETECT COMPUTER-WORK PREFERENCE CONFLICT
    # ==================================================

    preferred_work = str(
        profile.get(
            "preferred_work",
            ""
        )
    ).lower()

    avoids_computer_work = any(
        phrase in preferred_work
        for phrase in [
            "not being on a laptop",
            "not on a laptop",
            "avoid laptop",
            "without a laptop",
            "not computer",
            "avoid computer",
            "not being on a computer",
            "not desk",
            "avoid desk",
            "not sitting at a computer",
            "not working on a computer"
        ]
    )

    computer_heavy_majors = [
        "computer science",
        "data science",
        "software engineering",
        "information technology",
        "information systems",
        "business information systems",
        "artificial intelligence",
        "cybersecurity",
        "health informatics",
        "computer engineering"
    ]

    # ==================================================
    # GUARDRAIL 2:
    # DETECT APPLIED / PEOPLE-HELPING CAREER PREFERENCE
    # ==================================================

    profile_text = " ".join(
        [
            str(
                profile.get(
                    "interests",
                    ""
                )
            ),
            str(
                profile.get(
                    "skills",
                    ""
                )
            ),
            str(
                profile.get(
                    "preferred_work",
                    ""
                )
            )
        ]
    ).lower()

    helping_people = any(
        phrase in profile_text
        for phrase in [
            "helping people",
            "help people",
            "helping others",
            "patient care",
            "working with people",
            "care for people",
            "caring for people"
        ]
    )

    research_interest = any(
        phrase in profile_text
        for phrase in [
            "research",
            "scientist",
            "academic research",
            "professor",
            "teaching",
            "laboratory research"
        ]
    )

    prefers_applied_people_work = (
        helping_people
        and not research_interest
    )

    pure_academic_majors = [
        "biology",
        "physics",
        "chemistry",
        "mathematics",
        "math"
    ]

    # ==================================================
    # FILTER CANDIDATES
    # ==================================================

    candidate_majors = []
    candidate_reasons = {}

    for item in major_items:

        major = item.get(
            "major",
            ""
        ).strip()

        reason = item.get(
            "reason",
            ""
        ).strip()

        if not major:
            continue

        normalized_major = (
            major.lower().strip()
        )

        # ----------------------------------------------
        # Remove pure academic majors when the profile
        # clearly favors an applied helping profession
        # ----------------------------------------------

        if prefers_applied_people_work:

            if normalized_major in pure_academic_majors:

                print(
                    "Career preference guardrail removed: "
                    f"{major}"
                )

                continue

        # ----------------------------------------------
        # Remove computer-heavy majors when they
        # contradict the student's explicit preference
        # ----------------------------------------------

        if avoids_computer_work:

            computer_conflict = any(
                blocked_major
                in normalized_major
                for blocked_major
                in computer_heavy_majors
            )

            if computer_conflict:

                print(
                    "Computer-work preference guardrail "
                    f"removed: {major}"
                )

                continue

        # ----------------------------------------------
        # Save unique candidate
        # ----------------------------------------------

        if major not in candidate_majors:

            candidate_majors.append(
                major
            )

            candidate_reasons[
                major
            ] = reason

        # Keep only the final five
        if len(
            candidate_majors
        ) == 5:
            break

    # ==================================================
    # SAVE HANDOFF TO SHARED MEMORY
    # ==================================================

    save_candidate_majors(
        candidate_majors
    )

    save_candidate_major_reasons(
        candidate_reasons
    )

    if not candidate_majors:

        return (
            "No suitable majors were generated."
        )

    # ==================================================
    # HUMAN-READABLE OUTPUT
    # ==================================================

    output_lines = []

    for major in candidate_majors:

        output_lines.append(
            f"Major: {major}"
        )

        output_lines.append(
            "Reason: "
            + candidate_reasons.get(
                major,
                "No reason provided."
            )
        )

        output_lines.append(
            ""
        )

    return "\n".join(
        output_lines
    ).strip()

# ==================================================
# 3. UNIVERSITY RESEARCH AGENT
# ==================================================

def university_research_agent():
    """
    Search approved official university sources for programs
    that match the suggested majors.

    Then collect available tuition, admissions,
    financial-aid, and housing information.
    """

    state = get_shared_state()

    majors = state[
        "candidate_majors"
    ]

    if not majors:
        return "No candidate majors have been created."

    print(
        "\nUniversity Research Agent "
        "is searching official sources...\n"
    )

    matches = search_programs(
        majors
    )

    if not matches:
        return "No matching university programs were found."

    full_results = []

    for match in matches:

        short_name = match[
            "short_name"
        ]

        print(
            f"\nGetting details for {short_name}..."
        )

        details = get_university_details(
            short_name
        )

        full_results.append(
            {
                "university": match[
                    "university"
                ],

                "short_name": short_name,

                "matched_majors": match[
                    "matched_majors"
                ],

                "program_source": match[
                    "source"
                ],

                # Evidence showing why the program
                # was considered a match.
                "match_evidence": match.get(
                    "match_evidence",
                    {}
                ),

                "details": details
            }
        )

    save_university_results(
        full_results
    )

    summary = []

    for result in full_results:

        majors_text = ", ".join(
            result[
                "matched_majors"
            ]
        )

        summary.append(
            f"{result['short_name']}: "
            f"{majors_text}"
        )

    return "\n".join(
        summary
    )


# ==================================================
# 4. RECOMMENDATION AGENT
# ==================================================

def recommendation_agent():
    """
    Create grounded university-major recommendations.

    The LLM is allowed to select only from numbered options.
    Python validates the selections and builds the final answer.
    """

    state = get_shared_state()

    profile = state[
        "student_profile"
    ]

    university_results = state[
        "university_results"
    ]

    candidate_majors = state[
        "candidate_majors"
    ]

    candidate_major_reasons = state[
        "candidate_major_reasons"
    ]

    if not profile:
        return "No student profile has been created."

    if not university_results:
        return "No university research results are available."

    # --------------------------------------------------
    # Build allowed university-major options
    # --------------------------------------------------

    options = []
    option_id = 1

    for result in university_results:

        for major in result[
            "matched_majors"
        ]:

            options.append(
                {
                    "id": option_id,

                    "university": result[
                        "university"
                    ],

                    "short_name": result[
                        "short_name"
                    ],

                    "major": major,

                    # Original reason produced by
                    # the Major Matching Agent.
                    "major_reason": (
                        candidate_major_reasons.get(
                            major,
                            ""
                        )
                    ),

                    "program_source": result[
                        "program_source"
                    ],

                    "program_evidence": result.get(
                        "match_evidence",
                        {}
                    ).get(
                        major,
                        ""
                    ),

                    "details": result[
                        "details"
                    ]
                }
            )

            option_id += 1

    if not options:
        return (
            "No verified university-major "
            "options are available."
        )

    option_text = "\n".join(
        f"{option['id']}. "
        f"{option['university']} "
        f"({option['short_name']}) "
        f"- {option['major']}"
        for option in options
    )

    # --------------------------------------------------
    # Let the LLM choose ONLY option numbers
    # --------------------------------------------------

    system_prompt = """
You are the Recommendation Agent.

You will receive:
1. A student profile.
2. A numbered list of allowed university-major options.

Choose up to 3 suitable options.

STRICT RULES:

- Choose ONLY option numbers from the provided list.
- Do not write university names.
- Do not write major names.
- Do not invent information.
- Prefer different universities when possible.
- Prefer different majors when possible.
- Do not assume that tuition fits the budget.
- Do not assume housing or relocation is possible.
- Return ONLY the option numbers.

Example:

1, 4, 7
"""

    user_prompt = f"""
STUDENT PROFILE:

{json.dumps(profile, indent=2)}

CANDIDATE MAJORS:

{json.dumps(candidate_majors, indent=2)}

ALLOWED OPTIONS:

{option_text}

Return up to 3 option numbers only.
"""

    response = chat(
        model=RECOMMENDATION_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        think=False,
        options={
            "temperature": 0
        }
    )

    # --------------------------------------------------
    # Validate the LLM selection
    # --------------------------------------------------

    numbers = re.findall(
        r"\d+",
        response.message.content
    )

    selected_options = []
    selected_universities = set()
    selected_majors = set()

    for number in numbers:

        selected_id = int(
            number
        )

        matching_option = next(
            (
                option
                for option in options
                if option[
                    "id"
                ] == selected_id
            ),
            None
        )

        if not matching_option:
            continue

        university = matching_option[
            "short_name"
        ]

        major = matching_option[
            "major"
        ]

        # Prefer different universities.
        if university in selected_universities:
            continue

        # Prefer different academic directions.
        if major in selected_majors:
            continue

        selected_options.append(
            matching_option
        )

        selected_universities.add(
            university
        )

        selected_majors.add(
            major
        )

        if len(
            selected_options
        ) == 3:
            break

    # --------------------------------------------------
    # First fallback:
    # new university + new major
    # --------------------------------------------------

    if len(
        selected_options
    ) < 3:

        for option in options:

            if (
                option[
                    "short_name"
                ]
                in selected_universities
            ):
                continue

            if (
                option[
                    "major"
                ]
                in selected_majors
            ):
                continue

            selected_options.append(
                option
            )

            selected_universities.add(
                option[
                    "short_name"
                ]
            )

            selected_majors.add(
                option[
                    "major"
                ]
            )

            if len(
                selected_options
            ) == 3:
                break

    # --------------------------------------------------
    # Second fallback:
    # repeated major allowed only if necessary,
    # but still prefer another university.
    # --------------------------------------------------

    if len(
        selected_options
    ) < 3:

        for option in options:

            if (
                option[
                    "short_name"
                ]
                in selected_universities
            ):
                continue

            selected_options.append(
                option
            )

            selected_universities.add(
                option[
                    "short_name"
                ]
            )

            selected_majors.add(
                option[
                    "major"
                ]
            )

            if len(
                selected_options
            ) == 3:
                break

    # --------------------------------------------------
    # Build final answer using verified information
    # --------------------------------------------------

    recommendations = []

    for index, option in enumerate(
        selected_options,
        start=1
    ):

        details = option[
            "details"
        ]

        admissions = details.get(
            "admissions"
        )

        financial_aid = details.get(
            "financial_aid"
        )

        # ----------------------------------------------
        # Admissions
        # ----------------------------------------------

        if (
            admissions
            and admissions.get(
                "status"
            ) == "available"
        ):
            admission_text = (
                "Official admission information was retrieved. "
                "The student should verify the current requirements "
                "using the official university source."
            )

        else:
            admission_text = (
                "Admission requirements should be verified "
                "using the official source."
            )

        # ----------------------------------------------
        # Financial Aid
        # ----------------------------------------------

        if (
            financial_aid
            and financial_aid.get(
                "status"
            ) == "available"
        ):
            aid_text = (
                "Official financial-aid information was found. "
                "Eligibility should be verified with the university."
            )

        else:
            aid_text = (
                "Financial aid information was not verified."
            )

        # ----------------------------------------------
        # Use the original reason produced by
        # the Major Matching Agent
        # ----------------------------------------------

        if option[
            "major_reason"
        ]:

            why_text = option[
                "major_reason"
            ]

        else:
            why_text = (
                f"{option['major']} was identified by the "
                f"Major Matching Agent based on the "
                f"student's profile."
            )

        # ----------------------------------------------
        # Location / relocation / housing
        # ----------------------------------------------

        if (
            profile.get(
                "can_relocate"
            ) is False
        ):
            location_text = (
                "The student cannot relocate. "
                "Campus location and travel feasibility must "
                "therefore be checked before making a final decision."
            )

        else:
            location_text = (
                "Campus location should be checked "
                "before making a final decision."
            )

        if (
            profile.get(
                "can_live_in_dorm"
            ) is False
        ):
            location_text += (
                " Dormitory housing was not treated as an option."
            )

        # ----------------------------------------------
        # Final recommendation
        # ----------------------------------------------

        recommendation = f"""
Recommendation {index}

University: {option["university"]}

Candidate Major: {option["major"]}

Official Program Match:
A related official program match was found for the candidate field
"{option["major"]}". The university may use a different program,
degree, or concentration title, so the exact title should be
confirmed using the official source.

Why it fits:
{why_text}

Budget:
Budget fit could not be fully verified from the retrieved official source.

Admissions:
{admission_text}

Financial Aid:
{aid_text}

Location/Housing:
{location_text}

Important note:
This recommendation is guidance only. The student should verify
current information before making a final decision.

Official program source:
{option["program_source"]}
"""

        recommendations.append(
            recommendation.strip()
        )

    result = "\n\n".join(
        recommendations
    )

    save_final_recommendations(
        result
    )

    return result


# ==================================================
# 5. SUPERVISOR AGENT
# ==================================================

def supervisor_agent():
    """
    Coordinate the specialist agents in the correct order.

    Workflow:
    1. Safety validation
    2. Student Profile Agent
    3. Major Matching Agent
    4. University Research Agent
    5. Recommendation Agent
    """

    state = get_shared_state()

    profile = state[
        "student_profile"
    ]

    if not profile:
        return "No student profile has been created."

    # --------------------------------------------------
    # Safety check before any agent processes the profile
    # --------------------------------------------------

    safety_result = validate_student_profile(
        profile
    )

    if not safety_result[
        "is_safe"
    ]:

        errors = "\n".join(
            f"- {error}"
            for error in safety_result[
                "errors"
            ]
        )

        return (
            "The student profile failed the safety check:\n"
            f"{errors}"
        )

    if safety_result[
        "warnings"
    ]:

        print(
            "\nPROFILE WARNINGS:"
        )

        for warning in safety_result[
            "warnings"
        ]:
            print(
                "-",
                warning
            )

    print("\n================================")
    print("SUPERVISOR AGENT STARTED")
    print("================================")

    # --------------------------------------------------
    # Step 1: Student Profile Agent
    # --------------------------------------------------

    print(
        "\n[1/4] Student Profile Agent"
    )

    profile_analysis = (
        student_profile_agent()
    )

    print(
        profile_analysis
    )

    # --------------------------------------------------
    # Step 2: Major Matching Agent
    # --------------------------------------------------

    print(
        "\n[2/4] Major Matching Agent"
    )

    major_result = (
        major_matching_agent()
    )

    print(
        major_result
    )

    state = get_shared_state()

    if not state[
        "candidate_majors"
    ]:
        return (
            "The workflow stopped because no suitable "
            "candidate majors were produced."
        )

    # --------------------------------------------------
    # Step 3: University Research Agent
    # --------------------------------------------------

    print(
        "\n[3/4] University Research Agent"
    )

    university_result = (
        university_research_agent()
    )

    print(
        university_result
    )

    state = get_shared_state()

    if not state[
        "university_results"
    ]:
        return (
            "The workflow stopped because no matching "
            "university programs were found."
        )

    # --------------------------------------------------
    # Step 4: Recommendation Agent
    # --------------------------------------------------

    print(
        "\n[4/4] Recommendation Agent"
    )

    final_result = (
        recommendation_agent()
    )

    print("\n================================")
    print("SUPERVISOR AGENT FINISHED")
    print("================================\n")

    # Add the standard guidance disclaimer
    return (
        final_result
        + "\n\n"
        + guidance_disclaimer()
    )
