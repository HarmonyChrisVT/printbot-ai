# Shopify Custom App Setup

PrintBot AI connects to Shopify using a **Custom App** with a permanent Admin API access token (`shpat_...`).
This is the recommended approach — no OAuth dance, no expiry, no app installation required.

---

## Step 1 — Enable Custom App Development

1. Log in to your Shopify admin at `https://your-store.myshopify.com/admin`
2. Go to **Settings → Apps and sales channels**
3. Click **Develop apps** (top right)
4. Click **Allow custom app development** and confirm

---

## Step 2 — Create the Custom App

1. Click **Create an app**
2. Name it `PrintBot AI`
3. Set the App developer to your account (or leave default)
4. Click **Create app**

---

## Step 3 — Configure Admin API Scopes

1. Open the new app → **Configuration** tab
2. Under **Admin API integration**, click **Configure**
3. Enable the following scopes:

| Scope | Purpose |
|-------|---------|
| `read_products` | List existing products |
| `write_products` | Create / update products |
| `read_orders` | Check for new orders |
| `write_orders` | Update order status |
| `read_inventory` | Check stock levels |
| `write_inventory` | Adjust inventory |
| `read_fulfillments` | Track fulfillment state |
| `write_fulfillments` | Mark orders as fulfilled |
| `read_shipping` | Read shipping info |
| `write_price_rules` | Create discount / price rules |
| `read_customers` | Access customer profiles |

4. Click **Save**

---

## Step 4 — Install the App & Get the Token

1. Go to the **API credentials** tab
2. Click **Install app** → **Install**
3. Under **Admin API access token**, click **Reveal token once**
4. Copy the token — it starts with `shpat_` and **cannot be shown again**

> **Save it immediately.** If lost, you must uninstall and reinstall the app to get a new one.

---

## Step 5 — Configure PrintBot AI

Add these two lines to your `.env` file:

```
SHOPIFY_SHOP_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

- `SHOPIFY_SHOP_URL` — your store domain, no `https://`
- `SHOPIFY_ACCESS_TOKEN` — the `shpat_` token from Step 4

---

## Step 6 — Verify the Connection

Start PrintBot and watch the startup output. You should see:

```
✅ Shopify: Connected (Shop: Your Store Name)
```

If you see a warning instead, check:
- The token is copied exactly (no spaces, no line breaks)
- The store URL has no trailing slash and no `https://`
- All required scopes were selected before installing

---

## Token Security

- Store the token **only** in your `.env` file — never commit it to git
- `.env` is already in `.gitignore`
- The token has no expiry but can be revoked any time from the Custom App settings
