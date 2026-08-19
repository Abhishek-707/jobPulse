from typing import Optional


class JobValidator:
    """Validates normalized job data before database storage."""

    REQUIRED_FIELDS = (
        "title",
        "company",
    )

    MAX_TITLE_LENGTH = 255
    MAX_COMPANY_LENGTH = 255
    MAX_DESCRIPTION_LENGTH = 100_000

    @staticmethod
    def validate(
        job_data: dict,
    ) -> tuple[bool, Optional[str]]:
        """
        Validate job data.

        Returns:
            (True, None) when valid.
            (False, error_message) when invalid.
        """

        # ---------------------------------------------------------
        # Required fields
        # ---------------------------------------------------------

        for field in JobValidator.REQUIRED_FIELDS:
            value = job_data.get(field)

            if value is None:
                return (
                    False,
                    f"Missing required field: {field}",
                )

            if not str(value).strip():
                return (
                    False,
                    f"Missing required field: {field}",
                )

        # ---------------------------------------------------------
        # Title
        # ---------------------------------------------------------

        title = str(
            job_data["title"]
        ).strip()

        if len(title) > JobValidator.MAX_TITLE_LENGTH:
            return (
                False,
                "Title too long "
                f"(max {JobValidator.MAX_TITLE_LENGTH} characters)",
            )

        # ---------------------------------------------------------
        # Company
        # ---------------------------------------------------------

        company = str(
            job_data["company"]
        ).strip()

        if len(company) > JobValidator.MAX_COMPANY_LENGTH:
            return (
                False,
                "Company name too long "
                f"(max {JobValidator.MAX_COMPANY_LENGTH} characters)",
            )

        # ---------------------------------------------------------
        # URL
        # ---------------------------------------------------------

        url = job_data.get("url")

        if url:
            url = str(url).strip()

            if not (
                url.startswith("http://")
                or url.startswith("https://")
            ):
                return (
                    False,
                    "Invalid URL format",
                )

        # ---------------------------------------------------------
        # Description
        # ---------------------------------------------------------

        description = job_data.get("description")

        if description:
            if len(str(description)) > JobValidator.MAX_DESCRIPTION_LENGTH:
                return (
                    False,
                    "Description too long "
                    f"(max {JobValidator.MAX_DESCRIPTION_LENGTH} characters)",
                )

        return True, None