# Technical Explanation: REST-to-GraphQL Migration

## Decision Summary
ShopStream is migrating its public-facing API from REST to GraphQL over an 8-week period to streamline mobile and web data fetching, eliminate 15 single-purpose aggregation endpoints, and reduce frontend API traffic by 40%.

## Why We Chose This
- **Eliminating API Over-Fetching**: REST is like a fixed restaurant menu where ordering a dish forces you to take fixed sides you might not want; GraphQL is like a buffet where clients ask for and receive only the exact fields they need.
- **Reducing Sprint Bottlenecks**: Currently, frontend developers spend 30% of each sprint building custom REST aggregation endpoints. Switching to GraphQL lets frontend teams query custom data shapes without requiring backend code changes.
- **Rejected Alternatives**: We considered building a Backend-for-Frontend (BFF) layer or standardizing REST shapes. A BFF added unnecessary deployment overhead, and standardizing REST endpoints failed to solve the fundamental data mismatch between mobile and web clients.

## Risks and Mitigations
- **Learning Curve**: Two of the three dedicated engineers are new to GraphQL. We are pairing them with experienced engineers for the first two weeks.
- **Query Performance & Deep Nesting**: Uncontrolled nested queries can strain database performance. We will enforce query depth limits and query complexity analysis in middleware.
- **Caching Complexity**: Unlike REST endpoints which leverage standard URL caching, GraphQL uses POST requests with dynamic bodies. We are deploying automated response-caching middleware to handle query hashing.

## What This Means for Priya
- **Gradual Onboarding**: You will join the 3-person backend migration pod working alongside senior engineers on GraphQL schema definitions.
- **Dual-System Support**: For the next 8 weeks, both the legacy REST endpoints and the new GraphQL query engine will run concurrently in production.
- **Tooling Focus**: You will spend your first week mastering GraphQL schema design, query resolvers, and backend integration patterns.

## Next Steps
1. **Repository Access**: Clone the `shopstream-graphql-api` repository and review the initial schema definitions in `schema/root.graphql`.
2. **Setup Call**: Schedule a 30-minute walkthrough with Marcus (Migration Lead) on Tuesday at 10 AM.
3. **Environment Credentials**: Obtain local GraphQL playground tokens from the 1Password shared engineering vault.
