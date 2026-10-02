# AI University Guidance Agent for Grade 12 Students in Lebanon

This project is a multi-agent AI system designed to help Grade 12 students in Lebanon explore suitable university majors and universities based on their academic profile, interests, skills, work preferences, budget, and location.

The system provides guidance only and does not make final decisions for the student.

---

## Project Goal

Many students are unsure which university major fits them and may change majors after beginning university.

This project aims to provide structured guidance by combining:

- Student grades
- Strong subjects
- Interests
- Skills
- Hobbies
- Preferred type of work
- Budget
- Location
- Ability to relocate
- Dorm preferences

The system then researches official university sources and provides grounded recommendations.

---

## Multi-Agent Architecture

The system uses four main agents:

### 1. Student Profile Agent

Organizes the student's information into a structured profile without inventing additional strengths or preferences.

### 2. Major Matching Agent

Uses the student's complete profile to generate suitable university majors.

The agent first generates multiple candidate majors and applies deterministic guardrails to remove options that clearly conflict with the student's stated preferences.

### 3. University Research Agent

Searches official Lebanese university websites to identify programs related to the candidate majors.

It also retrieves available information about:

- Admissions
- Tuition
- Financial aid
- Housing

### 4. Recommendation Agent

Combines the student profile, candidate majors, and verified university research.

The LLM selects only from allowed university-major combinations, while Python constructs the final grounded recommendation.

---

## Supervisor Agent

A Supervisor Agent coordinates the workflow:

Student Profile  
→ Safety Validation  
→ Student Profile Agent  
→ Major Matching Agent  
→ University Research Agent  
→ Recommendation Agent

Shared memory is used to pass structured information between agents.

---

## Memory

The project uses shared session memory stored in `memory.py`.

It stores:

- Student profile
- Candidate majors
- Reasons for each major
- University research results
- Final recommendations

The memory is reset before starting a new student session.

---

## Tools and Official University Sources

University research is performed using tools defined in:

`university_tools.py`

The system retrieves information from approved official university domains.

The project currently supports multiple Lebanese universities including:

- Lebanese American University
- American University of Beirut
- Université Saint-Joseph de Beyrouth
- Lebanese University
- Beirut Arab University
- Holy Spirit University of Kaslik
- Notre Dame University-Louaize
- University of Balamand
- Lebanese International University
- American University of Science and Technology
- Haigazian University
- Antonine University
- Rafik Hariri University
- Phoenicia University
- Modern University for Business and Science

University source configuration is stored in:

`data/university_sources.json`

Some university websites may block automated retrieval. The system does not attempt to bypass website security restrictions.

---

## MCP

The project uses the Model Context Protocol (MCP) to expose university research tools.

The MCP server is implemented in:

`mcp_server.py`

It exposes tools such as:

- `list_supported_universities`
- `search_official_programs`
- `get_official_university_details`

The MCP client is implemented in:

`mcp_client.py`

The client allows an LLM to select an appropriate function using tool calling and execute the selected tool through MCP.

Example workflow:

User Request  
→ Qwen LLM  
→ Function Calling  
→ MCP Client  
→ MCP Server  
→ University Tool  
→ Official University Source

---

## Safety

Safety controls are implemented in:

`safety.py`

The system includes:

- Student input validation
- Grade validation
- Budget validation
- Prompt-injection detection
- Web-content prompt-injection detection
- Official-domain restrictions
- Grounded recommendation constraints
- Educational guidance disclaimer

Potentially malicious student input is blocked before specialist agents process it.

Retrieved webpage content is treated as untrusted external data.

---

## Evaluation

Evaluation is implemented in:

`evaluate.py`

The system includes:

### End-to-End Evaluation

Checks include:

- Major generation
- Major reasoning
- Grounded university recommendations
- Program evidence
- Student constraint handling
- Official sources
- Guidance disclaimer

### Red-Team Tests

The project tests:

- Prompt injection in student input
- Invalid grades
- Negative budget
- Prompt injection in webpage content

Two end-to-end student profiles were evaluated successfully, with all automated checks passing during testing.

Evaluation results can be generated with:

```bash
python3 evaluate.py