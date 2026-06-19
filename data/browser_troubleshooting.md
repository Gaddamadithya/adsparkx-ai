# Browser Troubleshooting: Clearing Cookies and Cache

This guide describes how to clear cookies and browser cache to resolve interface loading issues, expired session errors, and rendering bugs on the Adsparkx platform.

## 1. Why Clear Cookies and Cache?
Sometimes, our interface may fail to load, or show a spinning loading wheel indefinitely. This is usually caused by:
*   **Outdated Assets:** Caching outdated Javascript or CSS files from previous deployments.
*   **Expired Sessions:** Expired oauth/bearer cookies that block your browser from fetching fresh user data.
*   **Corrupted Storage:** Corrupt local storage states causing scripting errors in your dashboard.

---

## 2. Steps to Clear Cookies & Cache

### Google Chrome
1. Click the **three dots** in the top-right corner of the browser.
2. Select **Clear Browsing Data** (or press `Ctrl + Shift + Delete` on Windows, `Cmd + Shift + Delete` on Mac).
3. Set the Time Range to **All time**.
4. Check the boxes next to **"Cookies and other site data"** and **"Cached images and files"**.
5. Click **Clear data** and restart Chrome.

### Mozilla Firefox
1. Click the **menu button** (three horizontal lines) in the top-right corner.
2. Select **Settings** -> **Privacy & Security**.
3. Under the **Cookies and Site Data** section, click **Clear Data...**.
4. Check both options and click **Clear**.

### Safari (macOS)
1. Click **Safari** in the top menu bar, then select **Settings**.
2. Go to the **Privacy** tab and click **Manage Website Data...**.
3. Search for `adsparkx` or select **Remove All**, then click **Remove Now**.
