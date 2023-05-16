class Headers:
    OBJECTIVE_HEADER_KEYWORDS: tuple[str] = ("objective", "summary", "career goals")

    EMPLOYMENT_HEADER_KEYWORDS: tuple[str] = (
        "work history",
        "work experience",
        "experience",
        "professional experience",
        "related experience",
        "relevant experience",
        "programming experience",
        "freelance",
        "military experience",
        "career summary",
    )

    EDUCATION_HEADER_KEYWORDS: tuple[str] = (
        "education",
        "training",
        "academic qualifications",
        "professional training",
        "course projects",
        "internships",
        "apprenticeships",
        "college activities",
        "certifications",
        "special training",
    )

    SKILLS_HEADER_KEYWORDS: tuple[str] = (
        "skills",
        "areas of expertise",
        "technical skills",
        "computer skills",
        "personal skills",
        "technologies",
        "languages",
        "programming languages",
        "competencies",
    )

    MISCELLANEOUS_HEADER_KEYWORDS: tuple[str] = (
        "interests",
        "activities",
        "affiliations",
        "associations",
        "sports",
        "memberships",
        "community involvement",
        "volunteer work",
        "additional information",
    )

    ACCOMPLISHMENTS_HEADER_KEYWORDS: tuple[str] = (
        "achievements",
        "awards",
        "licenses",
        "presentations",
        "dissertations",
        "publications",
        "research experience",
        "grants",
        "projects",
        "thesis",
    )

    HEADERS: dict[str, tuple[str]] = {
        "experience": EMPLOYMENT_HEADER_KEYWORDS,
        "education": EDUCATION_HEADER_KEYWORDS,
        "skills": SKILLS_HEADER_KEYWORDS,
        "objective": OBJECTIVE_HEADER_KEYWORDS,
        "misc": MISCELLANEOUS_HEADER_KEYWORDS,
        "accomplishments": ACCOMPLISHMENTS_HEADER_KEYWORDS,
        "headline": (),
    }

    TOP_SEGMENTS: tuple[str] = (
        "headline",
        "objective",
    )

    BOTTOM_SEGMENTS: tuple[str] = (
        "misc",
        "accomplishments",
    )

    DEFAULT_SEGMENT: str = "misc"
