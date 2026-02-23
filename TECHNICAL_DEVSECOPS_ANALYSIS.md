## Technical Analysis for DevSecOps Enablement

### 1. High‑Level Architecture

- **Stack overview**  
  - **Frontend**: React (Create React App), JavaScript/TypeScript mix, Bootstrap + React-Bootstrap for UI, client-side routing via `react-router-dom`.  
  - **Backend**: Node.js + Express in TypeScript, Prisma ORM against PostgreSQL, layered architecture (`domain`, `application`, `presentation`, `routes`).  
  - **Database**: PostgreSQL, typically run via `docker-compose` with environment-driven configuration.  
  - **Infrastructure / CI-CD**:  
    - GitHub Actions workflow (`.github/workflows/ci.yml`) for backend build, test and deploy to EC2 using S3 as artifact storage and Nginx + PM2 on the instance.  
    - EC2 setup instructions and environment management documented in `README.md`.  

- **DevSecOps implications**  
  - Clear separation between frontend, backend, and database simplifies independent hardening and scanning.  
  - Existing CI pipeline focuses on **backend tests only**, leaving frontend and security checks (SAST, dependency scans, container scans) as future additions.  
  - Use of Prisma, OpenAPI spec, and centralized validation are promising foundations for enforcing security invariants at the domain and API layers.

### 2. Repositories, Modules and Boundaries

- **Backend structure** (`backend/`)  
  - `src/index.ts`: Express app bootstrap, Prisma client creation, route wiring, global error handling, basic logging.  
  - `src/domain/models/*`: Domain entities (e.g., `Candidate`, `Education`, `WorkExperience`, `Resume`, etc.), applying DDD patterns.  
  - `src/application/services/*`: Application services (e.g., `candidateService`, `positionService`, `fileUploadService`) implementing business use cases.  
  - `src/presentation/controllers/*`: Controllers that translate HTTP requests to application service calls and return HTTP responses.  
  - `src/routes/*`: Route definitions (e.g., `candidateRoutes`, `positionRoutes`).  
  - `src/application/validator.ts`: Central validation logic for candidate-related payloads using regexes and length checks.  
  - `prisma/*`: Prisma schema, migrations, and `seed.ts` for database initialization.  
  - `api-spec.yaml`: OpenAPI 3 definition for main backend endpoints.  
  - Tooling: Jest + ts-jest for unit tests, ESLint + Prettier for static analysis and formatting, `ts-node-dev` for local dev.

- **Frontend structure** (`frontend/`)  
  - `src/App.js`: Router setup for recruiter dashboard, candidate form, and position-related pages.  
  - `src/components/*`: UI components for recruiter workflows (positions listing, candidate details, drag-and-drop columns, file upload, etc.).  
  - `src/services/candidateService.js`: Centralized API client for candidate endpoints (depending on configuration of API base URL).  
  - CRA tooling provides Jest + React Testing Library (configured via `jest.config.js` referenced in scripts).

- **Root-level configuration**  
  - `package.json`: Root dev environment with TypeScript and Cypress for E2E tests, and a Prisma schema pointer.  
  - `cypress/*`: Cypress configuration, fixtures and test for positions workflow.  
  - `docker-compose.yml`: Single `db` service for PostgreSQL configured via environment variables.  
  - `.env.example`: Opinionated, security-aware template for environment variables with explicit guidance not to commit secrets.  

**DevSecOps takeaway**: The boundaries between layers are reasonably well-defined, which allows inserting security checks at specific points: input validation at controllers/services, authorization/enforcement in middleware, and secure persistence in repositories/Prisma.

### 3. Security-Relevant Backend Concerns

- **Authentication and Authorization**  
  - There is **no explicit authentication or authorization layer** in `src/index.ts` or routes: all endpoints appear publicly accessible.  
  - No usage of JWT, sessions, API keys, or role-based access control observed.  
  - For DevSecOps, this means:  
    - Security posture currently relies entirely on network-layer controls (e.g., EC2 security groups, Nginx) and implicit trust, which is insufficient for most production use cases.  
    - Introducing authentication (e.g., JWT or OAuth2) and route-level authorization will be a core hardening item.

- **Input Validation and Data Integrity**  
  - `backend/src/application/validator.ts` implements **server-side validation** for names, email, phone, dates, address, education, experience, and CV metadata using regex and length constraints.  
  - `backend/api-spec.yaml` defines complementary constraints at the API specification level (regex patterns, max lengths, required fields).  
  - Controllers and services (`candidateController`, `candidateService`) rely on these validators to prevent malformed or overly long input.  
  - Consistency between OpenAPI constraints, validator logic, and DB schema is critical; currently they are mostly aligned but must be kept in sync whenever schema evolves.

- **File Upload Security**  
  - `fileUploadService.ts` uses `multer` with:  
    - Disk storage in `../uploads/` with filename prefixing using a `Date.now()` timestamp.  
    - A `fileFilter` that only allows files with MIME types `application/pdf` or `application/vnd.openxmlformats-officedocument.wordprocessingml.document`.  
    - File size limit of 10MB.  
  - Security considerations:  
    - MIME-type checks alone are not fully reliable against spoofed files; consider adding server-side extension/magic-bytes checks or an antivirus/clamav integration in a later DevSecOps phase.  
    - The upload path is relative and likely outside the backend working dir; ensure appropriate OS-level permissions and that uploads are **not directly served** without sanitization.  
    - No explicit rate limiting or abuse protection is present on the upload endpoint.

- **Error Handling and Logging**  
  - Global error middleware logs `err.stack` and returns a generic `"Something broke!"` string with status 500.  
  - `candidateController` catches application errors and maps them to 4xx/5xx responses with safe messages; it avoids leaking stack traces.  
  - There is a simple request logger that prints method/path with timestamps.  
  - For DevSecOps:  
    - Centralized structured logging (JSON logs with correlation IDs) and log shipping (e.g., to CloudWatch or ELK) can be introduced without heavy refactors.  
    - Implementing explicit audit logging (who did what, on which resource) will require adding authentication context and correlating it with requests.

- **Database and Prisma Usage**  
  - `PrismaClient` is created once in `index.ts` and injected into `req.prisma` via middleware, ensuring a shared client and avoiding accidental multiple connections.  
  - Database schema and migrations are explicit under `backend/prisma`, which is good for traceability and change management.  
  - No raw SQL strings observed in the initial scan, which reduces risk of SQL injection; Prisma parameterization further mitigates this.  
  - DevSecOps angle:  
    - Apply **least privilege** on the PostgreSQL user used in `DATABASE_URL`.  
    - Use separate DB users/DBs for dev, test, and prod, governed via infrastructure-as-code (currently missing).

### 4. Security-Relevant Frontend Concerns

- **API Consumption**  
  - The frontend talks to the backend via a service layer (`candidateService.js`), likely using a configurable base URL (e.g., environment variable `REACT_APP_API_URL`).  
  - There is no visible client-side authentication or token handling in the initial scan.  
  - For DevSecOps:  
    - Once backend auth is introduced, the frontend must handle tokens securely (in-memory or HttpOnly cookies, avoiding localStorage when possible).  
    - Implement CSRF protections if using cookies (backend + frontend coordination).

- **Input Handling and XSS Mitigation**  
  - Components mostly display candidate/position data as plain text and use React, which by default escapes values and mitigates XSS when not using `dangerouslySetInnerHTML`.  
  - No evidence of unsafe HTML injection patterns in the inspected components.  
  - Client-side validation can be added to complement server-side validation, enhancing UX but keeping the server as the security source of truth.

- **Build and Dependencies**  
  - CRA-based build with `react-scripts` and Jest/RTL for tests.  
  - No explicit linting configuration beyond default `react-app` ESLint rules.  
  - For DevSecOps, this is a good place to add:  
    - Dependency scanning (e.g., `npm audit` in CI, or external scanners like Snyk/GitHub Dependabot).  
    - Frontend linting and type-checking in CI for catching unsafe patterns early.

### 5. CI/CD and Infrastructure Considerations

- **GitHub Actions CI workflow** (`.github/workflows/ci.yml`)  
  - Trigger: `pull_request` targeting `main`.  
  - Jobs:  
    - **build**: Sets up Node.js 16, installs backend dependencies, runs `npm test` in `backend`.  
    - **deploy**: After successful build, configures AWS CLI using repo secrets, uploads `backend/` dir to an S3 bucket, then SSHs into an EC2 instance to:  
      - Ensure Nginx and Node (via nvm) are installed.  
      - Configure Nginx as a reverse proxy to `localhost:8080`.  
      - Use PM2 to run the backend app on port 8080 after `npm install` and `npm run build`.  
  - Security posture:  
    - Secrets are stored in GitHub Actions secrets, which is appropriate; however, the workflow currently `cat`s the private key to the logs, which is a **serious security issue** (must be removed).  
    - AWS credentials are exported directly in the EC2 shell; consider using instance roles/STS in the future.  
    - The workflow does not run any explicit SAST, dependency scanning, or linting steps yet.

- **Docker and Database**  
  - `docker-compose.yml` only defines the `db` service (Postgres) with env vars for credentials and DB name, exposing `${DB_PORT}` on the host.  
  - There is no containerization of the backend or frontend yet; they run directly on EC2 (Node + Nginx + PM2).  
  - For DevSecOps:  
    - Introduce containerized backend/frontend and scan images (e.g., Trivy, Grype) in CI.  
    - Lock down Postgres networking (non-public, only accessible from backend/container network).  
    - Use separate `.env` per environment, with secrets managed via AWS SSM or Secrets Manager instead of `.env` files on the instance.

### 6. Coding Standards and Best Practices

- **Manifesto of Best Practices**  
  - `backend/ManifestoBuenasPracticas.md` documents DDD, SOLID, DRY, and improvement proposals (e.g., repositories, factories, dependency inversion) with concrete examples.  
  - Some observations inside the manifesto explicitly call out remaining technical debt (e.g., domain classes that still couple to Prisma, missing repository abstractions).  
  - DevSecOps perspective: these guidelines, if fully applied, support **security by design** by reducing complexity, duplication, and tight coupling, thereby lowering the attack surface.

- **Tooling and Quality Gates**  
  - Backend has ESLint + Prettier configured via `.eslintrc.js` extending `plugin:prettier/recommended`.  
  - Jest tests exist under `backend/src/presentation` and `backend/src/application`; Cypress tests are available for E2E.  
  - However, CI only runs backend unit tests; linting, E2E tests, and type-checking are not enforced in the pipeline yet.

### 7. Current DevSecOps Maturity Snapshot

- **Strengths**  
  - Clear project structure with separation of concerns (domain, application, presentation, routes).  
  - Centralized input validation and an OpenAPI spec for the main endpoints.  
  - Prisma ORM reduces the risk of SQL injection and gives strong typing across the persistence layer.  
  - CI/CD is already in place for backend build/test and automated deployment to EC2.  
  - `.env.example` promotes good practices for secret handling, and `.env` is excluded from version control.

- **Gaps and Risks**  
  - No authentication/authorization or user identity model: all endpoints are effectively public.  
  - Secrets management is manual and potentially fragile (AWS keys and SSH private key in GitHub Actions; private key echoed in logs).  
  - No automated security checks in CI (no SAST, dependency vulnerability scans, container scanning, or secret scanning).  
  - File upload security is basic (MIME + size) but not hardened (no content-type deep validation, no antivirus).  
  - Infrastructure as code for EC2, security groups, and Nginx is missing; deployment logic is embedded in the GitHub Actions shell script.  
  - Backend listeners are hard-coded to port 8080 and CORS origin is hard-coded to `http://localhost:4000`, not environment-driven.

### 8. Recommended Next Steps for DevSecOps Implementation

- **Short term (low effort, high impact)**  
  - Remove leaking of the SSH private key from the GitHub Actions workflow (`cat private_key.pem`).  
  - Extend CI to run:  
    - `npm run lint` (or equivalent) and `npm test` in both `backend` and `frontend`.  
    - `npm audit` (or external dependency scanning) in root, backend, and frontend.  
  - Add basic secret scanning (e.g., GitHub Advanced Security or third-party) to the pipeline.  
  - Parameterize CORS origin, server port, and upload path using environment variables.  

- **Medium term**  
  - Introduce authentication and authorization:  
    - Define a user model and roles, add JWT or OAuth2-based auth, protect routes accordingly.  
    - Implement role-based checks in controllers/services.  
  - Containerize backend and frontend; use Docker images in CI/CD instead of copying source to EC2.  
  - Add SAST tools (e.g., CodeQL, Semgrep) to CI for both backend and frontend.  
  - Harden file uploads with extension checks, content inspection, and optional AV scanning.  

- **Longer term**  
  - Move infrastructure definition to IaC (Terraform/CloudFormation) including EC2, security groups, IAM roles, S3, and RDS/Postgres.  
  - Replace static AWS access keys in CI with IAM roles and short-lived tokens (e.g., GitHub OIDC + AWS role).  
  - Implement centralized logging, metrics, and alerting (e.g., CloudWatch, Prometheus, ELK) with a security-focused dashboard.  
  - Introduce formal threat modeling around core workflows (candidate management, file uploads, recruiter operations) and feed results into backlog items for continuous DevSecOps improvement.

---

This document provides the current technical baseline specifically from a DevSecOps perspective. It can be used as the foundation for a phased security roadmap, acceptance criteria for future stories, and as input into threat modeling and compliance efforts.

