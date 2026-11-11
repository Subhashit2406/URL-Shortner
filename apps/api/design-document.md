# Design Document: API Rate Limiting Infrastructure

## Problem Statement
Uncontrolled API traffic currently poses a critical threat to service availability and customer experience. Last month, a single customer accidentally generated 50,000 requests per minute, degrading API response times for all users and forcing an on-call engineer to manually block the client key at 2 AM by editing config files and redeploying. Furthermore, the product team cannot launch planned paid API tiers with guaranteed request thresholds until automated rate-limiting infrastructure is deployed.

## Proposed Approach
We propose implementing an automated API Rate Limiter at the API Gateway layer using a **Distributed Sliding Window Log** algorithm powered by **Redis**.

- **Placement**: API Gateway layer (FastAPI middleware). Intercepts incoming requests before hitting internal application services, protecting downstream resources.
- **Algorithm**: Sliding Window counter via Redis atomic commands (`INCR` and `EXPIRE`). This prevents thundering-herd spikes at fixed minute boundaries while allowing smooth bursting up to configured tier limits.
- **Header Feedback**: Returns standard HTTP headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`) and responds with `HTTP 429 Too Many Requests` when limits are exceeded.

## Alternatives Considered
- **Alternative 1: In-Memory Rate Limiting per Instance**
  - *Pros*: Zero external network calls to Redis; extremely low latency (<1ms).
  - *Cons*: Counters are isolated to individual container instances. In a multi-instance auto-scaling cluster, a client could bypass limits by spreading traffic across multiple nodes, failing our paid tier SLA guarantees.
- **Alternative 2: Fixed Window Counter in Redis**
  - *Pros*: Simple counter logic and minimal Redis memory overhead.
  - *Cons*: Vulnerable to boundary spikes (e.g. sending 100% of allowed limit in the last second of Minute 1 and first second of Minute 2, doubling effective burst traffic).

## Risks and Mitigations
- **Risk 1: Redis Instance Outage or Latency Spike**
  - *Mitigation*: Configure rate limiter middleware with a 50ms fallback timeout. If Redis is unreachable, fail open (allow request) and log a high-priority alert so an outage never blocks legitimate customer traffic.
- **Risk 2: Impact of Doing Nothing**
  - *Mitigation*: Service remains vulnerable to accidental or malicious denial-of-service, leading to unexpected cloud compute costs and customer churn due to 3 AM outages.

## Open Questions
1. **Tier Configuration**: What exact per-minute limits should be assigned to Free vs. Enterprise tiers? (Awaiting input from Product).
2. **IP vs Key Throttling**: Should unauthenticated requests be rate-limited by client IP address or blocked entirely? (Awaiting input from Security).
