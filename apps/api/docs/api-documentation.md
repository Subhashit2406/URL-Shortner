# OrderFlow External API Integration Reference

This document provides technical reference for integrating with the OrderFlow REST API (`v1`).

---

## Base URL & Authentication

- **Base URL:** `https://api.orderflow.internal.company.com/v1`
- **Authentication Header:** `Authorization: Bearer <JWT_TOKEN>`

### Obtaining a JWT Bearer Token
Request a token from the internal Auth service using your client credentials:

```bash
curl -X POST https://auth.internal.company.com/v1/oauth/token \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "grant_type": "client_credentials"
  }'
```

*Response (200 OK):*
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

---

## Rate Limits

- **Rate Limit:** 100 requests per minute per client ID.
- **Headers Returned:**
  - `X-RateLimit-Limit`: `100`
  - `X-RateLimit-Remaining`: `98`
  - `X-RateLimit-Reset`: Unix timestamp in seconds.
- **Exceeded Threshold Response:** `429 Too Many Requests`. Caller must pause until reset timestamp.

---

## Endpoint Specifications

### 1. Create Order (`POST /orders`)

Creates a new customer order and reserves inventory.

**Request:**
```bash
curl -X POST https://api.orderflow.internal.company.com/v1/orders \
  -H "Authorization: Bearer eyJhbGciOiJIUzI..." \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust_98765",
    "items": [
      {
        "sku": "PROD-101",
        "quantity": 2,
        "price_cents": 2999
      }
    ],
    "currency": "USD"
  }'
```

**Success Response (201 Created):**
```json
{
  "order_id": "ord_100294",
  "customer_id": "cust_98765",
  "status": "created",
  "total_cents": 5998,
  "created_at": "2026-10-26T14:32:00Z"
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "INVALID_PAYLOAD",
  "message": "Field 'currency' must be 3-letter ISO code (e.g. USD).",
  "action": "Correct payload schema and retry request."
}
```

---

### 2. Get Order Status (`GET /orders/{order_id}`)

Retrieves current fulfillment and payment status.

**Request:**
```bash
curl -X GET https://api.orderflow.internal.company.com/v1/orders/ord_100294 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI..."
```

**Success Response (200 OK):**
```json
{
  "order_id": "ord_100294",
  "status": "processing",
  "payment_status": "settled",
  "updated_at": "2026-10-26T14:35:12Z"
}
```

---

### 3. Initiate Refund (`POST /orders/{order_id}/refunds`)

Queues an asynchronous refund request.

**Request:**
```bash
curl -X POST https://api.orderflow.internal.company.com/v1/orders/ord_100294/refunds \
  -H "Authorization: Bearer eyJhbGciOiJIUzI..." \
  -H "Content-Type: application/json" \
  -d '{
    "amount_cents": 5998,
    "reason": "customer_return"
  }'
```

**Success Response (202 Accepted):**
```json
{
  "refund_id": "ref_88201",
  "order_id": "ord_100294",
  "status": "queued",
  "estimated_completion_seconds": 30
}
```
