# Webhook Integration & Signature Verification Guide

Webhooks allow your application to receive real-time HTTP POST notifications when events occur in Adsparkx.

## 1. Webhook Setup Steps

To start receiving webhooks:
1. Log in to the dashboard and go to **Developer Settings** -> **Webhooks**.
2. Click **Add Endpoint**.
3. Input your destination server URL (e.g., `https://api.yourdomain.com/webhooks`).
4. Select the event triggers you want to listen to (e.g., `invoice.paid`, `account.locked`).
5. Copy the generated **Webhook signing secret key**.

---

## 2. Signature Verification

To ensure that a webhook was sent by Adsparkx and not a third party, you must verify the signature included in the request headers.
Every webhook contains a header named `X-Adsparkx-Signature`.

### Verification Logic in Python:

```python
import hmac
import hashlib

def verify_webhook(payload: bytes, header_signature: str, secret: str) -> bool:
    expected_signature = hmac.new(
        key=secret.encode('utf-8'),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, header_signature)
```

If the signature comparison fails, you should reject the payload and return a `403 Forbidden` response.
