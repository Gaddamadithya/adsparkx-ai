# SDK Integration & Quickstart

Get started quickly using the official Adsparkx SDKs for Python and Node.js.

## 1. Python SDK Integration

### Installation:
```bash
pip install adsparkx-sdk
```

### Quickstart Example:
```python
from adsparkx import AdsparkxClient

# Initialize the client with your bearer token
client = AdsparkxClient(api_key="your_api_token_here")

# Fetch current account metadata
account_info = client.accounts.get_current()
print(f"Connected to account: {account_info.name}")

# Publish an event to the stream
response = client.events.publish(
    topic="system.status",
    data={"status": "active", "load": 0.42}
)
print(f"Event ID: {response.event_id}")
```

---

## 2. Node.js SDK Integration

### Installation:
```bash
npm install adsparkx-node-sdk
```

### Quickstart Example:
```javascript
const { AdsparkxClient } = require('adsparkx');

const client = new AdsparkxClient({
  apiKey: 'your_api_token_here'
});

async function main() {
  const account = await client.accounts.getCurrent();
  console.log(`Connected to account: ${account.name}`);
}

main().catch(console.error);
```
