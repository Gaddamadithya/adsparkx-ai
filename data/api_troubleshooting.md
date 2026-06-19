# API Authentication & Error Troubleshooting Guide

This guide describes how to authenticate requests to the Adsparkx API and troubleshoot common HTTP response error codes.

## 1. Authentication

All requests to the Adsparkx API must be authenticated using a bearer token in the HTTP `Authorization` header. You can generate API tokens in the Developer Settings section of your dashboard.

### Header Format

You must include the header as follows in all requests:

```http
Authorization: Bearer YOUR_API_KEY
```

If the header is missing, incorrectly formatted, or if the token is expired, the API will return a `401 Unauthorized` response.

---

## 2. Troubleshooting Common API Error Codes

### 401 Unauthorized
*   **Description:** The request is missing credentials or uses an invalid/expired token.
*   **Resolution:** Check that your token is correctly configured in the headers. Verify that the token has not expired or been deleted in your dashboard settings.

### 403 Forbidden
*   **Description:** The authenticated user or token does not have permission to access the requested resource.
*   **Resolution:** Verify that your API token has the appropriate scopes enabled (e.g., `read:users`, `write:billing`). If you are trying to access team features, check that your team has active billing.

### 429 Too Many Requests
*   **Description:** You have exceeded the rate limit threshold for your account tier.
*   **Resolution:** Check the response headers for rate limit details. Reduce request volume or upgrade to a higher tier. (See `rate_limits.md` for exact limits).

### 500 Internal Server Error
*   **Description:** An unexpected error occurred on the Adsparkx servers.
*   **Resolution:** This is an infrastructure issue. Please check the status page or retry your request using exponential backoff.
