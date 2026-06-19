# API Rate Limits and Quotas

To maintain platform stability, Adsparkx applies rate-limiting controls to all incoming API requests.

## 1. Rate Limits by Subscription Tier

We use a sliding-window rate-limiting algorithm evaluated per API key:

*   **Free Tier:** 100 requests per minute (RPM). Peak burst limits are capped at 5 requests per second.
*   **Pro Tier:** 1,000 requests per minute (RPM). Peak burst limits are capped at 25 requests per second.
*   **Enterprise Tier:** Configurable (defaults to 10,000 RPM). Custom peak limits are managed in your SLA agreement.

---

## 2. Rate Limit Headers

Every API response contains headers indicating your current rate limit status:

*   `X-RateLimit-Limit`: The maximum number of requests allowed per minute.
*   `X-RateLimit-Remaining`: The remaining number of requests allowed for the current window.
*   `X-RateLimit-Reset`: The Unix epoch timestamp indicating when the current window resets.

---

## 3. Handling 429 Errors

If your application exceeds the allowed rate limit, the API returns a `429 Too Many Requests` status code. 

**Recommendation:** Your API client must parse the `Retry-After` header (which lists the wait time in seconds) and wait before re-sending requests. We recommend implementing **Exponential Backoff** with jitter.
