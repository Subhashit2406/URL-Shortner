# TICKET-05: POST /api/auth/register — User Registration & JWT Issuance

## 1. Title
POST /api/auth/register — Create User Account & Issue JWT Token [AI-Ready Bar]

## 2. Context
Slice 2 introduces identity and authentication, allowing Learners and Providers to register accounts and authenticate for protected dashboard routes.

## 3. Scope
Implement POST `/api/auth/register` endpoint, hashing passwords with bcrypt, persisting user records, and returning signed JWT access token.

## 4. Interface Contract
- **Request Body**:
  ```json
  {
    "email": "learner@example.com",
    "password": "SecurePassword123!",
    "name": "Jane Learner",
    "role": "learner"
  }
  ```
- **Success Response (201 Created)**:
  ```json
  {
    "user_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "email": "learner@example.com",
    "role": "learner",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```
- **Error Responses**:
  - `400 Bad Request`: `{ "error": "Invalid email format or password under 8 characters" }`
  - `409 Conflict`: `{ "error": "User with this email already exists" }`

## 5. Acceptance Criteria
- **Given** valid registration details,
- **When** POST `/api/auth/register` is invoked,
- **Then** status `201 Created` is returned, password is saved hashed in DB, and a valid JWT token is returned.
- **Given** an existing email address,
- **When** POST `/api/auth/register` is called with that email,
- **Then** status `409 Conflict` is returned.

## 6. Constraints
- Password must be hashed using bcrypt (min 10 salt rounds).
- JWT payload must contain `user_id`, `email`, and `role`, signed using `JWT_SECRET`.

## 7. Anti-Scope
- No password reset via email.
- No OAuth2 / Google social sign-in.
- No MFA / SMS verification.
