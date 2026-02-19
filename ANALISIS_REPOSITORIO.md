# Análisis Técnico del Repositorio: facephi-secdevops

> **Fecha de análisis:** 19 de febrero de 2026  
> **Versión del proyecto:** 0.0.0.001

---

## Tabla de Contenidos

1. [Descripción General](#1-descripción-general)
2. [Estructura de Directorios](#2-estructura-de-directorios)
3. [Stack Tecnológico](#3-stack-tecnológico)
4. [Arquitectura de la Aplicación](#4-arquitectura-de-la-aplicación)
5. [Modelo de Datos](#5-modelo-de-datos)
6. [API REST](#6-api-rest)
7. [Infraestructura y DevOps](#7-infraestructura-y-devops)
8. [Pipeline CI/CD](#8-pipeline-cicd)
9. [Testing](#9-testing)
10. [Configuración y Variables de Entorno](#10-configuración-y-variables-de-entorno)
11. [Guía de Ejecución Local](#11-guía-de-ejecución-local)
12. [Scripts Disponibles](#12-scripts-disponibles)
13. [Dependencias](#13-dependencias)
14. [Consideraciones de Seguridad](#14-consideraciones-de-seguridad)
15. [Áreas de Mejora](#15-áreas-de-mejora)

---

## 1. Descripción General

**LTI (Sistema de Seguimiento de Talento)** es una aplicación web full-stack de gestión de procesos de reclutamiento. Permite a los recruiters:

- Gestionar candidatos y sus datos (CV, educación, experiencia laboral)
- Gestionar posiciones abiertas
- Seguir el avance de candidatos a través de un flujo de entrevistas configurable
- Cargar y gestionar archivos adjuntos (CVs en PDF/DOCX)

La arquitectura sigue principios de **Domain-Driven Design (DDD)** con una estructura en capas.

---

## 2. Estructura de Directorios

```
facephi-secdevops/
├── .env                          # Variables de entorno raíz (DB)
├── .gitignore
├── LICENSE.md
├── README.md
├── VERSION                       # Versión del proyecto: 0.0.0.001
├── package.json                  # Dependencias raíz (Cypress + dotenv)
├── package-lock.json
├── docker-compose.yml            # Infraestructura local (PostgreSQL)
├── cypress.config.js             # Configuración tests E2E
│
├── backend/                      # Aplicación backend
│   ├── .env                      # Variables de entorno backend
│   ├── package.json
│   ├── tsconfig.json
│   ├── jest.config.js
│   ├── .eslintrc.js
│   ├── api-spec.yaml             # Especificación OpenAPI 3.0
│   ├── ManifestoBuenasPracticas.md
│   ├── ModeloDatos.md
│   ├── prisma/
│   │   ├── schema.prisma         # Esquema de base de datos
│   │   ├── seed.ts               # Script de datos iniciales
│   │   └── migrations/           # Migraciones de base de datos
│   └── src/
│       ├── index.ts              # Punto de entrada del servidor
│       ├── routes/               # Definición de rutas Express
│       │   ├── candidateRoutes.ts
│       │   └── positionRoutes.ts
│       ├── domain/
│       │   └── models/           # Entidades de dominio (DDD)
│       │       ├── Candidate.ts
│       │       ├── Education.ts
│       │       ├── WorkExperience.ts
│       │       ├── Resume.ts
│       │       ├── Company.ts
│       │       ├── Employee.ts
│       │       ├── Position.ts
│       │       ├── Application.ts
│       │       ├── Interview.ts
│       │       ├── InterviewType.ts
│       │       ├── InterviewFlow.ts
│       │       └── InterviewStep.ts
│       ├── application/
│       │   ├── validator.ts      # Validación de datos de entrada
│       │   └── services/
│       │       ├── candidateService.ts
│       │       ├── positionService.ts
│       │       └── fileUploadService.ts
│       └── presentation/
│           └── controllers/
│               ├── candidateController.ts
│               └── positionController.ts
│
├── frontend/                     # Aplicación frontend
│   ├── package.json
│   ├── tsconfig.json
│   ├── public/
│   │   └── manifest.json
│   └── src/
│       ├── index.tsx             # Punto de entrada React
│       ├── App.js                # Componente raíz + React Router
│       ├── App.css
│       ├── reportWebVitals.ts
│       ├── components/
│       │   ├── RecruiterDashboard.js
│       │   ├── AddCandidateForm.js
│       │   ├── CandidateCard.js
│       │   ├── CandidateDetails.js
│       │   ├── FileUploader.js
│       │   ├── StageColumn.js
│       │   ├── Positions.tsx
│       │   └── PositionDetails.js
│       └── services/
│           └── candidateService.js
│
├── cypress/                      # Tests end-to-end
│   ├── e2e/
│   │   └── positions.cy.ts
│   ├── fixtures/
│   │   └── example.json
│   └── support/
│       ├── commands.js
│       └── e2e.js
│
├── tf/
│   └── main.tf                   # Terraform (archivo vacío, placeholder)
│
├── prompts/
│   └── prompts.md                # Prompts de IA para el desarrollo del proyecto
│
└── .github/
    └── workflows/
        └── ci.yml                # Pipeline GitHub Actions
```

---

## 3. Stack Tecnológico

### Backend

| Tecnología | Versión | Rol |
|---|---|---|
| Node.js | v16 | Runtime |
| TypeScript | 4.9.5 | Lenguaje |
| Express.js | 4.19.2 | Framework HTTP |
| Prisma ORM | 5.13.0 | Acceso a base de datos |
| PostgreSQL | latest | Base de datos relacional |
| Multer | 1.4.5-lts.1 | Gestión de uploads |
| Swagger/OpenAPI | — | Documentación API |
| ts-node-dev | 1.1.6 | Dev server con hot reload |

### Frontend

| Tecnología | Versión | Rol |
|---|---|---|
| React | 18.3.1 | Framework UI |
| TypeScript | 4.9.5 | Lenguaje (parcial) |
| React Router DOM | 6.23.1 | Navegación SPA |
| Bootstrap | 5.3.3 | Estilos |
| React Bootstrap | 2.10.2 | Componentes UI |
| react-beautiful-dnd | 13.1.1 | Drag & drop (kanban) |
| React DatePicker | 6.9.0 | Selector de fechas |
| Axios | — | Llamadas HTTP |

### Testing

| Tecnología | Versión | Rol |
|---|---|---|
| Jest | 29.7.0 | Tests unitarios (backend) |
| ts-jest | 29.1.2 | Jest con TypeScript |
| Cypress | 13.11.0 | Tests E2E |

### DevOps e Infraestructura

| Tecnología | Rol |
|---|---|
| Docker + Docker Compose | Entorno local (base de datos) |
| GitHub Actions | Pipeline CI/CD |
| AWS EC2 | Hosting del backend en producción |
| AWS S3 | Almacenamiento de artefactos |
| Nginx | Reverse proxy (puerto 80 → 8080) |
| PM2 | Gestor de procesos Node.js en producción |
| Terraform | IaC (actualmente sin implementar) |

### Herramientas de desarrollo

| Herramienta | Versión | Rol |
|---|---|---|
| ESLint | 9.2.0 | Linting |
| Prettier | 3.2.5 | Formateo de código |

---

## 4. Arquitectura de la Aplicación

### Patrón: DDD (Domain-Driven Design) + Arquitectura en Capas

```
┌──────────────────────────────────────────────┐
│               FRONTEND (React)               │
│   RecruiterDashboard / Positions / Forms     │
└──────────────────┬───────────────────────────┘
                   │ HTTP / Axios
                   ▼
┌──────────────────────────────────────────────┐
│            BACKEND (Express)                 │
│                                              │
│  ┌─────────────────────────────────────┐     │
│  │  Presentation Layer (Controllers)   │     │
│  │  candidateController.ts             │     │
│  │  positionController.ts              │     │
│  └─────────────┬───────────────────────┘     │
│                │                             │
│  ┌─────────────▼───────────────────────┐     │
│  │  Application Layer (Services)       │     │
│  │  candidateService.ts                │     │
│  │  positionService.ts                 │     │
│  │  fileUploadService.ts               │     │
│  └─────────────┬───────────────────────┘     │
│                │                             │
│  ┌─────────────▼───────────────────────┐     │
│  │  Domain Layer (Models)              │     │
│  │  Candidate, Position, Interview...  │     │
│  └─────────────┬───────────────────────┘     │
│                │ Prisma ORM                  │
└────────────────┼─────────────────────────────┘
                 ▼
┌──────────────────────────────────────────────┐
│           PostgreSQL (Docker)                │
└──────────────────────────────────────────────┘
```

### Flujo de datos

```
React Component
  → candidateService.js (Axios)
    → Express Route (/candidates, /positions)
      → Controller (validación request/response)
        → Service (lógica de negocio)
          → Domain Model (save / findOne)
            → Prisma Client
              → PostgreSQL
```

### Rutas del frontend

| Ruta | Componente |
|---|---|
| `/` | RecruiterDashboard |
| `/add-candidate` | AddCandidateForm |
| `/positions` | Positions |
| `/positions/:id` | PositionDetails |

### Configuración del servidor backend

- Puerto: **8080**
- CORS configurado para: `http://localhost:4000`
- Rutas montadas: `/candidates`, `/positions`, `/upload`
- Middleware: JSON parser, Prisma attachment, logging, error handler

---

## 5. Modelo de Datos

El esquema de Prisma define **13 modelos** relacionados:

```
Candidate ──── Education (1:N)
           ──── WorkExperience (1:N)
           ──── Resume (1:N)
           ──── Application (1:N)

Company ──── Employee (1:N)
         ──── Position (1:N)

Position ──── Application (1:N)
          ──── InterviewFlow (1:1)

Application ──── Interview (1:N)

InterviewFlow ──── InterviewStep (1:N)

InterviewStep ──── InterviewType (N:1)
              ──── Interview (1:N)
```

### Entidades principales

| Entidad | Descripción |
|---|---|
| `Candidate` | Candidato con datos personales (email único) |
| `Position` | Oferta de trabajo de una empresa |
| `Application` | Postulación de un candidato a una posición |
| `Interview` | Entrevista realizada en un paso del flujo |
| `InterviewFlow` | Flujo de entrevistas asociado a una posición |
| `InterviewStep` | Paso individual dentro de un flujo |
| `Employee` | Empleado de una empresa (email único) |
| `Company` | Empresa que publica posiciones |

---

## 6. API REST

Especificada en `backend/api-spec.yaml` (OpenAPI 3.0):

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/candidates` | Crear nuevo candidato |
| `GET` | `/candidates/:id` | Obtener candidato por ID |
| `PUT` | `/candidates/:id` | Actualizar etapa del candidato |
| `POST` | `/upload` | Subir archivo (PDF/DOCX, máx. 10MB) |
| `GET` | `/positions` | Obtener todas las posiciones |
| `GET` | `/positions/:id/candidates` | Candidatos de una posición |
| `GET` | `/positions/:id/interviewflow` | Flujo de entrevistas de una posición |

La documentación Swagger UI está disponible en `http://localhost:8080/api-docs` cuando el servidor está en ejecución.

---

## 7. Infraestructura y DevOps

### Entorno local

La base de datos corre en Docker:

```yaml
# docker-compose.yml
services:
  db:
    image: postgres
    restart: always
    ports:
      - "${DB_PORT}:5432"
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_DB: ${DB_NAME}
```

### Entorno de producción (AWS)

```
Internet
   │
   ▼
[EC2 Instance]
   │
   ├── Nginx (puerto 80) → reverse proxy → puerto 8080
   │
   ├── PM2 → Node.js app (puerto 8080)
   │
   └── PostgreSQL (Docker)

[S3 Bucket: mi-ec2-con-github-actions]
   └── backend/ → artefactos del build
```

### Terraform

El archivo `tf/main.tf` está **vacío** actualmente. Es un placeholder para futura implementación de infraestructura como código.

---

## 8. Pipeline CI/CD

**Archivo:** `.github/workflows/ci.yml`  
**Trigger:** Pull Requests hacia `main`

### Job 1: Build & Test

```
1. Checkout del código
2. Setup Node.js v16
3. npm install (backend)
4. npm test (Jest)
```

### Job 2: Deploy (depende de Build)

```
1. Checkout del código
2. Configurar credenciales AWS
3. Subir backend a S3
4. Añadir EC2 a known_hosts
5. Desplegar en EC2 via SSH:
   ├── Instalar Nginx (si no existe)
   ├── Instalar Node.js via NVM (si no existe)
   ├── Configurar Nginx como reverse proxy
   ├── Instalar PM2
   ├── Detener procesos PM2 existentes
   ├── Descargar código desde S3
   ├── npm install
   ├── npm run build (TypeScript → dist/)
   └── PM2 start (puerto 8080)
```

### Secretos de GitHub requeridos

| Secreto | Descripción |
|---|---|
| `AWS_ACCESS_ID` | AWS Access Key ID |
| `AWS_ACCESS_KEY` | AWS Secret Access Key |
| `EC2_INSTANCE` | IP o DNS del servidor EC2 |
| `EC2_SSH_PRIVATE_KEY` | Clave SSH privada para EC2 |

---

## 9. Testing

### Tests Unitarios (Jest + ts-jest)

- Ubicación: `backend/src/**/*.test.ts`
- Cobertura esperada: servicios y controladores
- Ejecutar: `cd backend && npm test`

### Tests E2E (Cypress)

- Ubicación: `cypress/e2e/positions.cy.ts`
- Base URL: `http://localhost:3000`
- Ejecutar: `npx cypress open` o `npx cypress run`

### Configuración Jest

```js
// backend/jest.config.js
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node'
}
```

---

## 10. Configuración y Variables de Entorno

### Variables requeridas (`.env` raíz y `backend/.env`)

```env
DB_PASSWORD=<password>
DB_USER=<user>
DB_NAME=<database_name>
DB_PORT=5432
DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@localhost:${DB_PORT}/${DB_NAME}"
```

> **Nota:** Ambos archivos `.env` (raíz y `backend/`) deben contener las mismas variables de base de datos.

---

## 11. Guía de Ejecución Local

### Prerrequisitos

- Node.js v16+
- npm
- Docker y Docker Compose

### Paso 1: Clonar y configurar variables

```bash
git clone <repo-url>
cd facephi-secdevops

# Verificar que existen los .env (ya deberían estar)
cat .env
cat backend/.env
```

### Paso 2: Levantar la base de datos

```bash
docker-compose up -d
# PostgreSQL disponible en localhost:5432
```

### Paso 3: Configurar el backend

```bash
cd backend
npm install

# Generar cliente Prisma
npx prisma generate

# Ejecutar migraciones
npx prisma migrate dev

# (Opcional) Poblar con datos de ejemplo
npx ts-node prisma/seed.ts
```

### Paso 4: Iniciar el backend

```bash
# Modo desarrollo (hot reload)
npm run dev
# → Servidor en http://localhost:8080
# → Swagger UI en http://localhost:8080/api-docs
```

### Paso 5: Iniciar el frontend

```bash
cd ../frontend
npm install
npm start
# → App en http://localhost:3000
```

### Paso 6: Ejecutar tests (opcional)

```bash
# Tests unitarios
cd backend && npm test

# Tests E2E (con frontend y backend corriendo)
cd .. && npx cypress open
```

---

## 12. Scripts Disponibles

### Backend (`backend/package.json`)

| Script | Comando | Descripción |
|---|---|---|
| `dev` | `ts-node-dev --respawn --transpile-only src/index.ts` | Servidor de desarrollo con hot reload |
| `build` | `tsc` | Compilar TypeScript → `dist/` |
| `start` | `node dist/index.js` | Iniciar build de producción |
| `start:prod` | `npm run build && npm start` | Build + start en un paso |
| `test` | `jest` | Ejecutar tests unitarios |
| `prisma:generate` | `npx prisma generate` | Regenerar cliente Prisma |
| `prisma:init` | `npx prisma init` | Inicializar Prisma (ya hecho) |

### Frontend (`frontend/package.json`)

| Script | Comando | Descripción |
|---|---|---|
| `start` | `react-scripts start` | Servidor de desarrollo |
| `build` | `react-scripts build` | Build de producción |
| `test` | `jest --config jest.config.js` | Ejecutar tests |
| `eject` | `react-scripts eject` | Eject de Create React App |

### Raíz (`package.json`)

| Script | Descripción |
|---|---|
| `cypress open` | Abrir Cypress en modo interactivo |
| `cypress run` | Ejecutar Cypress en modo headless |

---

## 13. Dependencias

### Backend — Dependencias principales

```json
{
  "@prisma/client": "^5.13.0",
  "cors": "^2.8.5",
  "dotenv": "^16.4.5",
  "express": "^4.19.2",
  "multer": "^1.4.5-lts.1",
  "swagger-jsdoc": "^6.2.8",
  "swagger-ui-express": "^5.0.0"
}
```

### Frontend — Dependencias principales

```json
{
  "react": "^18.3.1",
  "react-dom": "^18.3.1",
  "react-router-dom": "^6.23.1",
  "bootstrap": "^5.3.3",
  "react-bootstrap": "^2.10.2",
  "react-beautiful-dnd": "^13.1.1",
  "react-datepicker": "^6.9.0",
  "react-scripts": "5.0.1"
}
```

---

## 14. Consideraciones de Seguridad

| Aspecto | Estado | Recomendación |
|---|---|---|
| Credenciales DB en `.env` | ⚠️ Riesgo | Usar secrets manager en producción |
| CORS solo para `localhost:4000` | ✅ Restringido | Actualizar para producción |
| Validación de entradas | ✅ Implementada | `validator.ts` en capa application |
| Subida de archivos | ✅ Controlada | Solo PDF/DOCX, límite 10MB |
| `.env` en `.gitignore` | ✅ Ignorado | Los archivos no se suben al repo |
| Secrets CI/CD en GitHub Secrets | ✅ Correcto | AWS keys y SSH key protegidas |

---

## 15. Áreas de Mejora

### Deuda técnica identificada

1. **Separación de responsabilidades en el dominio:** Los modelos de dominio acceden directamente a Prisma (`save()`, `findOne()`), mezclando lógica de dominio con persistencia. Se recomienda implementar un patrón **Repository**.

2. **Mezcla de JS y TS en el frontend:** Algunos componentes son `.js` y otros `.tsx`. Sería conveniente migrar todo a TypeScript.

3. **CORS hardcodeado a `localhost:4000`:** El frontend corre en el puerto 3000 por defecto. Revisar la coherencia de puertos.

4. **Terraform vacío:** El archivo `tf/main.tf` no tiene contenido. La infraestructura se configura manualmente en la pipeline.

5. **Node.js v16 en CI/CD:** Node.js 16 llegó al End of Life en septiembre 2023. Actualizar a v20 LTS.

### Posibles nuevas features

- Implementar autenticación y autorización (JWT/OAuth)
- Añadir notificaciones por email
- Dashboard con métricas de reclutamiento
- Completar la infraestructura Terraform
- Añadir contenedor Docker para el backend
- Internacionalización (i18n)
- Gestión de roles (recruiter, manager, candidato)

---

*Análisis generado el 19/02/2026 sobre el estado actual del repositorio.*
