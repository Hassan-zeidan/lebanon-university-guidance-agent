from mcp.server import MCPServer

from university_tools import (
    load_universities,
    search_programs,
    get_university_details
)


# ==================================================
# MCP SERVER
# ==================================================

mcp = MCPServer(
    "Lebanon University Guidance Tools"
)


# ==================================================
# MCP TOOL 1
# ==================================================

@mcp.tool()
def list_supported_universities() -> dict:
    """
    Return the universities supported by the guidance system.
    """

    universities = load_universities()

    results = []

    for university in universities:

        results.append(
            {
                "name": university["name"],
                "short_name": university["short_name"]
            }
        )

    return {
        "universities": results
    }


# ==================================================
# MCP TOOL 2
# ==================================================

@mcp.tool()
def search_official_programs(
    majors: list[str]
) -> dict:
    """
    Search approved official Lebanese university program pages
    for academic programs related to the provided candidate majors.

    The underlying retrieval system checks official university
    sources and returns supporting program evidence.
    """

    results = search_programs(
        majors
    )

    return {
        "results": results
    }


# ==================================================
# MCP TOOL 3
# ==================================================

@mcp.tool()
def get_official_university_details(
    short_name: str
) -> dict:
    """
    Retrieve available official university information.

    Information may include:
    tuition,
    admissions,
    financial aid,
    and housing.
    """

    return get_university_details(
        short_name
    )


# ==================================================
# RUN SERVER
# ==================================================

if __name__ == "__main__":
    mcp.run()
