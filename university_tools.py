import re
from safety import check_untrusted_web_content
import json
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


# Path to the JSON file that contains our supported universities
DATA_FILE = Path(__file__).parent / "data" / "university_sources.json"


def load_universities():
    """
    Load the list of supported universities from the JSON file.
    """

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data["universities"]


def find_university(name):
    """
    Find a university using either its full name or short name.

    Example:
    find_university("LAU")
    find_university("Lebanese American University")
    """

    universities = load_universities()

    name = name.lower()

    for university in universities:

        if (
            university["name"].lower() == name
            or university["short_name"].lower() == name
        ):
            return university

    return None


def is_allowed_url(url):
    """
    Check that the URL belongs to one of our approved university websites.
    """

    universities = load_universities()

    allowed_domains = [
        university["domain"]
        for university in universities
    ]

    domain = urlparse(url).netloc.lower()

    # Remove www. if it exists
    if domain.startswith("www."):
        domain = domain[4:]

    return any(
        domain == allowed_domain
        or domain.endswith("." + allowed_domain)
        for allowed_domain in allowed_domains
    )


def clean_html(html):
    """
    Convert webpage HTML into readable text
    and remove common navigation elements.
    """

    soup = BeautifulSoup(html, "html.parser")

    # Remove parts that usually do not contain useful page content
    for element in soup(
        [
            "script",
            "style",
            "noscript",
            "nav",
            "header",
            "footer",
            "aside"
        ]
    ):
        element.decompose()

    text = " ".join(soup.stripped_strings)

    return text


def fetch_with_requests(url):
    """
    First attempt to download a webpage using requests.
    """

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/152.0 Safari/537.36"
        )
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=15
    )

    # If the website accepts the request
    if response.status_code == 200:
        return clean_html(response.text)

    # Return None so the browser method can be tried
    print(
        f"Requests returned status code {response.status_code}."
    )

    return None


def fetch_with_browser(url):
    """
    Use Playwright as a fallback if normal requests are blocked.
    """

    from playwright.sync_api import sync_playwright

    print("Trying browser retrieval...")

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        page = browser.new_page()

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=30000
        )

        text = page.locator("body").inner_text()

        browser.close()

    # Remove unnecessary extra spaces
    return " ".join(text.split())


def fetch_page_text(url):
    """
    Get readable text from an approved university webpage.

    The tool first tries requests.
    If the website blocks requests, it uses Playwright.
    """

    # Safety check
    if not is_allowed_url(url):
        raise ValueError(
            "This URL is not from an approved university website."
        )

    # First try normal requests
    try:

        text = fetch_with_requests(url)

        if text:
            return text

    except requests.RequestException as error:

        print(f"Requests failed: {error}")

    # If requests failed or was blocked,
    # use the browser fallback
    return fetch_with_browser(url)


def normalize_for_matching(text):
    """
    Normalize text so program names can be compared more reliably.
    """

    text = text.lower()

    # Treat "&" and "and" as the same thing.
    text = text.replace("&", " and ")

    # Replace punctuation with spaces.
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Remove repeated spaces.
    text = re.sub(r"\s+", " ", text)

    return text.strip()

def get_program_search_terms(major):
    """
    Return safe alternative names that universities may use
    for the same or closely equivalent academic field.
    """

    aliases = {
        "translation studies": [
            "translation studies",
            "translation and interpretation",
            "translation"
        ],
        "communication studies": [
            "communication studies",
            "mass communication"
        ],
        "media studies": [
            "media studies",
            "media and communication"
        ],
        "english language and literature": [
            "english language and literature",
            "english literature"
        ]
    }

    normalized_major = normalize_for_matching(
        major
    )

    return aliases.get(
        normalized_major,
        [normalized_major]
    )

def find_program_evidence(text, major):
    """
    Check whether a major or a safe program-name variation
    appears close to strong academic-program language.

    Returns a short evidence snippet if a likely academic
    program match is found. Otherwise returns None.
    """

    normalized_text = normalize_for_matching(
        text
    )

    search_terms = get_program_search_terms(
        major
    )

    academic_words = [
        "bachelor",
        "undergraduate program",
        "undergraduate programs",
        "degree",
        "major",
        "program",
        "programme",
        "ba in",
        "bs in",
        "bsc in",
        "view programs",
        "following options"
    ]

    for search_term in search_terms:

        for match in re.finditer(
            re.escape(search_term),
            normalized_text
        ):

            context_start = max(
                0,
                match.start() - 250
            )

            context_end = min(
                len(normalized_text),
                match.end() + 250
            )

            context = normalized_text[
                context_start:context_end
            ]

            if any(
                academic_word in context
                for academic_word in academic_words
            ):

                evidence_start = max(
                    0,
                    match.start() - 150
                )

                evidence_end = min(
                    len(normalized_text),
                    match.end() + 150
                )

                return normalized_text[
                    evidence_start:evidence_end
                ]

    return None

def search_programs(majors):
    """
    Search approved official university program pages for
    candidate majors.

    A major is accepted only when it appears in an academic
    program context. Retrieved webpage content is also checked
    for possible prompt-injection instructions.
    """

    universities = load_universities()

    results = []

    for university in universities:

        programs_url = university.get(
            "programs_url"
        )

        if not programs_url:
            continue

        print(
            f"Checking {university['short_name']}..."
        )

        try:
            text = fetch_page_text(
                programs_url
            )

            # ------------------------------------------
            # Detect blocked webpages such as Cloudflare
            # ------------------------------------------

            if (
                "you have been blocked"
                in text.lower()
            ):

                print(
                    f"{university['short_name']} "
                    f"blocked automated access."
                )

                continue

            # ------------------------------------------
            # Treat retrieved webpage content as
            # untrusted external data.
            # ------------------------------------------

            web_safety = (
                check_untrusted_web_content(
                    text
                )
            )

            if not web_safety[
                "safe"
            ]:

                print(
                    f"{university['short_name']} "
                    f"web content failed the safety check."
                )

                continue

            # ------------------------------------------
            # Search for academic program matches
            # ------------------------------------------

            matched_majors = []
            match_evidence = {}

            for major in majors:

                evidence = (
                    find_program_evidence(
                        text,
                        major
                    )
                )

                if evidence:

                    matched_majors.append(
                        major
                    )

                    # Save evidence showing why the
                    # program was considered a match.
                    match_evidence[
                        major
                    ] = evidence[:600]

            # ------------------------------------------
            # Save university only if at least
            # one candidate major was verified
            # ------------------------------------------

            if matched_majors:

                results.append(
                    {
                        "university": university[
                            "name"
                        ],

                        "short_name": university[
                            "short_name"
                        ],

                        "matched_majors": (
                            matched_majors
                        ),

                        "source": programs_url,

                        "match_evidence": (
                            match_evidence
                        )
                    }
                )

        except Exception as error:

            print(
                f"Could not check "
                f"{university['short_name']}: "
                f"{error}"
            )

    return results


def extract_relevant_text(text, detail_type, max_chars=3500):
    """
    Extract the most relevant part of a webpage for a specific
    type of university information.
    """

    keywords = {
        "tuition": [
            "tuition",
            "fees & expenses",
            "fees",
            "cost"
        ],
        "admissions": [
            "undergraduate admission requirements",
            "admission requirements",
            "required documents",
            "lebanese baccalaureate",
            "application requirements"
        ],
        "financial_aid": [
            "financial aid",
            "scholarship",
            "financial support"
        ],
        "housing": [
            "student housing",
            "housing",
            "dormitory",
            "residence"
        ]
    }

    search_terms = keywords.get(detail_type, [])

    lower_text = text.lower()

    # Find the last occurrence because navigation menus
    # often contain the same words near the beginning.
    best_position = -1

    for term in search_terms:
        position = lower_text.rfind(term.lower())

        if position > best_position:
            best_position = position

    # If no keyword was found, return the beginning of the page.
    if best_position == -1:
        return text[:max_chars]

    # Include a little text before the keyword as context.
    start = max(0, best_position - 200)

    return text[start:start + max_chars]


def get_university_details(short_name):
    """
    Retrieve useful official information for one university.

    The function checks available official pages for:
    tuition,
    admissions,
    financial aid,
    and housing.

    Retrieved webpage content is treated as untrusted data
    and checked before being used.
    """

    university = find_university(
        short_name
    )

    if not university:

        return {
            "error": (
                f"University {short_name} "
                f"was not found."
            )
        }

    details = {
        "university": university[
            "name"
        ],

        "short_name": university[
            "short_name"
        ],

        "tuition": None,
        "admissions": None,
        "financial_aid": None,
        "housing": None
    }

    source_types = {
        "tuition": "tuition_url",
        "admissions": "admissions_url",
        "financial_aid": "financial_aid_url",
        "housing": "housing_url"
    }

    for (
        detail_name,
        url_key
    ) in source_types.items():

        url = university.get(
            url_key
        )

        if not url:
            continue

        print(
            f"Retrieving {detail_name} "
            f"information for {short_name}..."
        )

        try:
            text = fetch_page_text(
                url
            )

            # ------------------------------------------
            # Detect blocked webpages
            # ------------------------------------------

            if (
                "you have been blocked"
                in text.lower()
            ):

                details[
                    detail_name
                ] = {
                    "status": "blocked",
                    "source": url
                }

                continue

            # ------------------------------------------
            # Check retrieved webpage content
            # before using it.
            # ------------------------------------------

            web_safety = (
                check_untrusted_web_content(
                    text
                )
            )

            if not web_safety[
                "safe"
            ]:

                details[
                    detail_name
                ] = {
                    "status": "unsafe_content",
                    "source": url
                }

                continue

            # ------------------------------------------
            # Extract only the useful part of the page
            # ------------------------------------------

            details[
                detail_name
            ] = {
                "status": "available",

                "text": extract_relevant_text(
                    text,
                    detail_name
                ),

                "source": url
            }

        except Exception as error:

            details[
                detail_name
            ] = {
                "status": "error",
                "message": str(
                    error
                ),
                "source": url
            }

    return details
