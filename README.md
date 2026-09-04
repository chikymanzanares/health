# Health Claims Demo

Small demo: **Flask + HTML + SQLite** (front) and **gRPC** backend with **DDD / hexagonal** layout.

## High-level flow

```
Browser
  |
  | HTTP
  v
Flask front-end (:5000)
  login (SQLite) + claim form / POST /claims
  |
  | gRPC
  v
Backend (:50051)
  infrastructure/grpc  →  application use cases  →  domain
                              ↑
                    PolicyRepository (port)
                              ↑
              InMemoryPolicyRepository (adapter)
```

## Backend layers (hexagonal)

```
backend/
  domain/                         # enterprise / business
    models.py                     # Policy, result dataclasses, enums
    ports.py                      # PolicyRepository interface
    services.py                   # eligibility / auth / adjudication rules
  application/                    # use cases (transport-agnostic)
    check_eligibility.py
    request_authorization.py
    submit_claim.py
  infrastructure/                 # adapters
    persistence/
      in_memory_policy_repository.py
    grpc/
      servicer.py                 # maps protobuf ↔ use cases
      server.py
      generated/                  # *_pb2*.py (build-time)
  main.py                         # composition root
```

gRPC is only an **inbound adapter**. The same use cases could be called from FastAPI later without changing domain/application.

## Quick start

```bash
cd ~/health
make up
```

- Web UI: http://127.0.0.1:5000  
- gRPC: `localhost:50051`

### Login

| User   | Password  |
|--------|-----------|
| juanjo | juanjo01  |
| tom    | tom01     |

## Proto generation — when / how?

| Situation | What happens |
|-----------|----------------|
| `make up` / `make build` | Each **Dockerfile** runs `protoc` while building the image |
| You change a `.proto` | Rebuild images: `make up` or `make build` (Docker picks up the new proto) |
| Local IDE / host without Docker | Optional: `make proto` writes stubs under `backend/infrastructure/grpc/generated/` and `frontend/` |

You do **not** need `make proto` for Docker runs — the image build already compiles protos.  
You **do** need a rebuild after editing `.proto` files (explicit `make build` / `make up`).

## Makefile

| Target | Action |
|--------|--------|
| `make up` | Build images (incl. protoc) + start stack |
| `make down` | Stop containers |
| `make proto` | Compile protos on the host (optional) |
| `make build` | Build images only |
| `make logs` | Follow logs |

## Claim flow (MRI example)

1. **Eligibility** — policy active?  
2. **Prior authorization** — in-network provider + covered service?  
3. **Claim adjudication** — negotiated rate, deductible, coinsurance.

Demo policy **1001** (Gold PPO): patient **$360**, insurer **$640**.

### HTML

After login → **File a claim** → submit form.

### Proto enums

```protobuf
enum ClaimType { ... MEDICAL_EXPENSE | PHARMACY | DENTAL }
enum ClaimStatus { ... ADJUDICATED | DENIED }
enum EligibilityStatus { ... ACTIVE | INACTIVE | UNKNOWN }
enum AuthorizationDecision { ... APPROVED | DENIED | NOT_REQUIRED }
```

`policy_id` = insurance contract (plan).  
`member_id` = person covered by that policy.
