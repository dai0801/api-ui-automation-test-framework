import os


# ==================================================
# Public/demo environment configuration
# ==================================================
#
# Do not hard-code real company domains or internal API paths
# in the public repository. Values can be overridden through
# environment variables.
#
# Safe defaults below intentionally point to non-production,
# non-company example addresses.
# ==================================================

BASE_URL = os.getenv(
    "TEST_BASE_URL",
    "https://example.invalid",
).rstrip("/")

DWELLER_API = os.getenv(
    "TEST_DWELLER_API",
    "/api/v1/residents",
)


def get_headers():
    """
    Build API request headers.

    Sensitive values are read from environment variables
    instead of being hard-coded in source code.
    """
    token = os.getenv("TEST_AUTH_TOKEN")
    app_code = os.getenv("TEST_APP_CODE")

    assert token, "TEST_AUTH_TOKEN is not configured"
    assert app_code, "TEST_APP_CODE is not configured"

    return {
        "Authorization": token,
        "X-AppCode": app_code,
        "Accept": "application/json, text/plain, */*",
    }
