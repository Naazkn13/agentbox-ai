---
id: openapi-design
name: OpenAPI Design Expert
category: api-work
level1: "For designing OpenAPI 3.x specs — paths, schemas, auth, status codes, and client generation"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**OpenAPI Design Expert** — Activate for: OpenAPI 3.x spec authoring, paths/components/schemas, request/response models, authentication schemes (bearer/apiKey/oauth2), HTTP status codes, and generating clients with openapi-generator.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## OpenAPI Design — Core Instructions

1. **Use OpenAPI 3.x (not Swagger 2.0):** declare `openapi: "3.1.0"` and use `components/schemas` for all reusable models — never inline complex schemas twice.
2. **Define all reusable types in components:** schemas, parameters, responses, request bodies, and security schemes all belong under `components`, then referenced with `$ref`.
3. **Every response must have a schema:** document 2xx, 4xx, and 5xx responses for every operation — do not leave responses undocumented.
4. **Use `required` arrays and `nullable` explicitly:** be exact about which fields are required and which can be null; never leave it ambiguous.
5. **Apply security at the global level, override per-operation:** set a global `security` block, then override individual operations (e.g., login endpoint has empty `security: []`).
6. **Use `operationId` on every endpoint:** name it `verbNoun` (e.g., `createUser`, `listOrders`) — this drives generated SDK method names.
7. **Validate the spec before committing:** run `npx @redocly/cli lint openapi.yaml` or `npx swagger-parser validate` in CI to catch broken `$ref`s and schema errors early.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## OpenAPI Design — Full Reference

### Minimal Valid OpenAPI 3.1 File
```yaml
openapi: "3.1.0"
info:
  title: Payments API
  version: "1.0.0"
  description: API for processing payments

servers:
  - url: https://api.example.com/v1
    description: Production
  - url: https://staging-api.example.com/v1
    description: Staging

security:
  - BearerAuth: []   # applies to all operations by default

paths:
  /payments:
    get:
      operationId: listPayments
      summary: List payments
      tags: [payments]
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/LimitParam'
      responses:
        '200':
          description: Paginated list of payments
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaymentListResponse'
        '401':
          $ref: '#/components/responses/Unauthorized'
    post:
      operationId: createPayment
      summary: Create a payment
      tags: [payments]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreatePaymentRequest'
      responses:
        '201':
          description: Payment created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Payment'
        '422':
          $ref: '#/components/responses/ValidationError'

  /payments/{paymentId}:
    get:
      operationId: getPayment
      summary: Get a payment by ID
      tags: [payments]
      parameters:
        - $ref: '#/components/parameters/PaymentIdParam'
      responses:
        '200':
          description: Payment found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Payment'
        '404':
          $ref: '#/components/responses/NotFound'

  /auth/token:
    post:
      operationId: issueToken
      summary: Issue an access token
      tags: [auth]
      security: []   # override: this endpoint is public
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TokenRequest'
      responses:
        '200':
          description: Token issued
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TokenResponse'
```

### Components: Schemas
```yaml
components:
  schemas:
    Payment:
      type: object
      required: [id, amountCents, currency, status, createdAt]
      properties:
        id:
          type: string
          format: uuid
          example: "3fa85f64-5717-4562-b3fc-2c963f66afa6"
        amountCents:
          type: integer
          minimum: 1
          example: 1000
        currency:
          type: string
          pattern: '^[A-Z]{3}$'
          example: "USD"
        status:
          type: string
          enum: [pending, completed, failed]
        createdAt:
          type: string
          format: date-time

    CreatePaymentRequest:
      type: object
      required: [amountCents, currency]
      properties:
        amountCents:
          type: integer
          minimum: 1
        currency:
          type: string
          pattern: '^[A-Z]{3}$'
        idempotencyKey:
          type: string
          maxLength: 64

    PaymentListResponse:
      type: object
      required: [data, pagination]
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/Payment'
        pagination:
          $ref: '#/components/schemas/Pagination'

    Pagination:
      type: object
      required: [total, page, limit, pages]
      properties:
        total:  { type: integer }
        page:   { type: integer }
        limit:  { type: integer }
        pages:  { type: integer }

    ErrorResponse:
      type: object
      required: [error, code]
      properties:
        error: { type: string }
        code:  { type: string }
        field: { type: string, nullable: true }

    ValidationErrorResponse:
      type: object
      required: [error, code, errors]
      properties:
        error:  { type: string }
        code:   { type: string }
        errors:
          type: array
          items:
            type: object
            required: [field, message]
            properties:
              field:   { type: string }
              message: { type: string }
```

### Components: Parameters, Responses, Security
```yaml
  parameters:
    PaymentIdParam:
      name: paymentId
      in: path
      required: true
      schema:
        type: string
        format: uuid
    PageParam:
      name: page
      in: query
      schema:
        type: integer
        default: 1
        minimum: 1
    LimitParam:
      name: limit
      in: query
      schema:
        type: integer
        default: 20
        minimum: 1
        maximum: 100

  responses:
    Unauthorized:
      description: Authentication required
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    NotFound:
      description: Resource not found
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    ValidationError:
      description: Validation failed
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ValidationErrorResponse'

  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
    OAuth2:
      type: oauth2
      flows:
        authorizationCode:
          authorizationUrl: https://auth.example.com/oauth/authorize
          tokenUrl: https://auth.example.com/oauth/token
          scopes:
            payments:read: Read payment data
            payments:write: Create and modify payments
```

### Generating Clients with openapi-generator
```bash
# Install
npm install -g @openapitools/openapi-generator-cli

# Generate TypeScript/Axios client
openapi-generator-cli generate \
  -i openapi.yaml \
  -g typescript-axios \
  -o ./src/generated/api \
  --additional-properties=supportsES6=true,npmName=my-api-client

# Generate Python client
openapi-generator-cli generate \
  -i openapi.yaml \
  -g python \
  -o ./clients/python \
  --additional-properties=packageName=my_api_client

# Generate Go client
openapi-generator-cli generate \
  -i openapi.yaml \
  -g go \
  -o ./clients/go \
  --additional-properties=packageName=apiclient
```

### Linting in CI
```bash
# Redocly (recommended)
npx @redocly/cli lint openapi.yaml

# swagger-parser for $ref validation
npx swagger-parser validate openapi.yaml
```

### Anti-patterns to Avoid
- Never use `additionalProperties: true` on response schemas — it makes generated clients useless.
- Never inline the same schema in multiple places — always use `$ref`.
- Never omit `operationId` — generated clients will get auto-named methods that are unreadable.
- Never document only the happy path — 4xx and 5xx responses must be specified.
- Never mix Swagger 2.0 and OpenAPI 3.x syntax in the same file.
- Never put secrets or example tokens in the spec — they will be committed to source control.
<!-- LEVEL 3 END -->
