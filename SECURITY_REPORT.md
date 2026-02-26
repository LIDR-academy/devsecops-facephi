# Informe de Seguridad — facephi-secdevops

**Fecha de análisis:** 26 de febrero de 2026
**Analista:** Revisión estática de código (SAST manual)
**Rama analizada:** `main-b`
**Alcance:** Revisión completa del repositorio (backend, frontend, CI/CD, infraestructura, monitoring)

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Metodología y Alcance](#2-metodología-y-alcance)
3. [Resumen de Hallazgos](#3-resumen-de-hallazgos)
4. [Hallazgos Detallados](#4-hallazgos-detallados)
   - [Críticos](#41-críticos)
   - [Altos](#42-altos)
   - [Medios](#43-medios)
   - [Bajos](#44-bajos)
5. [Análisis de Pipeline CI/CD](#5-análisis-de-pipeline-cicd)
6. [Análisis de Infraestructura y Contenedores](#6-análisis-de-infraestructura-y-contenedores)
7. [Fortalezas Identificadas](#7-fortalezas-identificadas)
8. [Recomendaciones Priorizadas](#8-recomendaciones-priorizadas)
9. [Métricas Consolidadas](#9-métricas-consolidadas)

---

## 1. Resumen Ejecutivo

El repositorio `facephi-secdevops` implementa una aplicación de gestión de candidatos (ATS — _Applicant Tracking System_) compuesta por un backend Node.js/Express con TypeScript, un frontend React y una base de datos PostgreSQL. El análisis ha identificado **21 hallazgos de seguridad**, de los cuales **3 son críticos** y **6 son de severidad alta**.

El problema más urgente es que los archivos `.env` con credenciales reales están potencialmente siendo rastreados por git, ya que la regla de exclusión en `.gitignore` está comentada. Combinado con la ausencia total de autenticación y autorización en la API, la aplicación presenta una superficie de ataque significativa antes de cualquier consideración de despliegue en producción.

La madurez DevSecOps actual es **nivel 1 de 5**: existe una pipeline CI/CD básica y herramientas de lint/test, pero no hay controles de seguridad automatizados activos (SAST, SCA, secret scanning, container scanning). El stack de monitorización es funcional pero expone puntos de información sensible sin protección.

**Puntuación de riesgo global estimada: CRÍTICO**

---

## 2. Metodología y Alcance

### Técnica de análisis

| Técnica | Descripción |
|---|---|
| Revisión estática de código (SAST manual) | Análisis de todos los ficheros fuente TypeScript, JavaScript, YAML y configuración |
| Revisión de configuración de infraestructura | `docker-compose.yml`, Dockerfiles, configs de monitoring |
| Revisión de pipeline CI/CD | Todos los workflows de GitHub Actions |
| Revisión de gestión de secretos | `.env`, `.env.example`, `.gitignore` |
| Revisión de control de acceso | Rutas Express, middlewares, validadores |

### Archivos analizados

```
backend/src/index.ts
backend/src/application/validator.ts
backend/src/application/services/fileUploadService.ts
backend/src/application/services/candidateService.ts
backend/src/presentation/controllers/candidateController.ts
backend/src/presentation/controllers/positionController.ts
backend/src/routes/candidateRoutes.ts
backend/src/routes/positionRoutes.ts
backend/prisma/schema.prisma
backend/package.json
backend/Dockerfile.dev
frontend/package.json
frontend/Dockerfile.dev
docker-compose.yml
.env
.env.example
backend/.env
.gitignore
.github/workflows/ci.yml
.github/workflows/cd.yml
.github/workflows/legacy-ec2-deploy.yml
.github/workflows/sast-template.yml
monitoring/prometheus/prometheus.yml
monitoring/loki/loki-config.yml
monitoring/promtail/promtail-config.yml
```

### Framework de clasificación

Los hallazgos se clasifican según **OWASP Top 10 2021** y **CVSS v3.1**:

| Severidad | Puntuación CVSS | Acción requerida |
|---|---|---|
| **Crítico** | 9.0 – 10.0 | Bloquea producción. Requiere remediación inmediata |
| **Alto** | 7.0 – 8.9 | Remediación en el sprint actual |
| **Medio** | 4.0 – 6.9 | Remediación planificada en próximo sprint |
| **Bajo** | 0.1 – 3.9 | Backlog de mejora continua |

---

## 3. Resumen de Hallazgos

| ID | Severidad | Categoría OWASP | Título | Archivo |
|---|---|---|---|---|
| SEC-001 | **CRÍTICO** | A02 – Cryptographic Failures | Credenciales reales en git (`.gitignore` comentado) | `.gitignore`, `.env`, `backend/.env` |
| SEC-002 | **CRÍTICO** | A01 – Broken Access Control | Sin autenticación ni autorización en ningún endpoint | `backend/src/index.ts` |
| SEC-003 | **CRÍTICO** | A01 – Broken Access Control | Endpoint `/metrics` de Prometheus expuesto públicamente | `backend/src/index.ts` |
| SEC-004 | **ALTO** | A03 – Injection | Path traversal via `file.originalname` en subida de ficheros | `fileUploadService.ts` |
| SEC-005 | **ALTO** | A05 – Security Misconfiguration | Ruta absoluta del servidor expuesta en respuesta de `/upload` | `fileUploadService.ts` |
| SEC-006 | **ALTO** | A03 – Injection | Bypass completo de validación en edición de candidatos | `validator.ts` |
| SEC-007 | **ALTO** | A05 – Security Misconfiguration | CORS hardcodeado, origin incorrecto y no parametrizable | `backend/src/index.ts` |
| SEC-008 | **ALTO** | A02 – Cryptographic Failures | Credenciales AWS expuestas en sesión SSH remota (workflow legacy) | `legacy-ec2-deploy.yml` |
| SEC-009 | **ALTO** | A05 – Security Misconfiguration | cAdvisor con `privileged: true` y acceso completo al host | `docker-compose.yml` |
| SEC-010 | **MEDIO** | A04 – Insecure Design | Sin rate limiting en ningún endpoint | `backend/src/index.ts` |
| SEC-011 | **MEDIO** | A05 – Security Misconfiguration | Sin headers de seguridad HTTP | `backend/src/index.ts` |
| SEC-012 | **MEDIO** | A07 – Identification and Auth. Failures | Grafana con credenciales por defecto en `.env` | `.env` |
| SEC-013 | **MEDIO** | A05 – Security Misconfiguration | Prometheus config con puerto de backend incorrecto | `prometheus.yml` |
| SEC-014 | **MEDIO** | A05 – Security Misconfiguration | Promtail monta Docker socket — riesgo de escape de contenedor | `docker-compose.yml` |
| SEC-015 | **MEDIO** | A06 – Vulnerable Components | `npm audit` no bloquea el pipeline (`continue-on-error: true`) | `ci.yml` |
| SEC-016 | **MEDIO** | A09 – Security Logging Failures | Stack traces en logs de producción | `backend/src/index.ts` |
| SEC-017 | **MEDIO** | A08 – Software and Data Integrity | SAST workflow vacío — sin análisis de código activo | `sast-template.yml` |
| SEC-018 | **BAJO** | A05 – Security Misconfiguration | Puerto del servidor hardcodeado en código fuente | `backend/src/index.ts` |
| SEC-019 | **BAJO** | A06 – Vulnerable Components | `npm install` en lugar de `npm ci` en Dockerfile | `Dockerfile.dev` |
| SEC-020 | **BAJO** | A05 – Security Misconfiguration | node-exporter con `pid: host` expone procesos del host | `docker-compose.yml` |
| SEC-021 | **BAJO** | A05 – Security Misconfiguration | Imagen de desarrollo usada en despliegue de producción | `cd.yml`, `Dockerfile.dev` |

---

## 4. Hallazgos Detallados

### 4.1 Críticos

---

#### SEC-001 — Credenciales reales en git: regla `.gitignore` comentada

**Severidad:** CRÍTICO | **CVSS v3.1:** 9.1 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N)
**Categoría OWASP:** A02:2021 – Cryptographic Failures

**Descripción:**

La regla de exclusión de archivos `.env` en `.gitignore` está comentada, lo que significa que los ficheros `.env` con credenciales reales no están excluidos del control de versiones y pueden haber sido o ser rastreados por git.

**Evidencia:**

Archivo `.gitignore`, línea 3:
```
#**/.env
```

El fichero `.env` en la raíz del proyecto contiene una contraseña de base de datos real:
```
DB_PASSWORD=D1ymf8wyQEGthFR1E9xhCq
DB_USER=LTIdbUser
DB_NAME=LTIdb
DB_PORT=5432
DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@localhost:${DB_PORT}/${DB_NAME}"
GRAFANA_ADMIN_PASSWORD=change_me_in_production
```

Igualmente, `backend/.env` contiene las mismas credenciales de base de datos. Si alguno de estos ficheros fue rastreado en cualquier commit pasado, la contraseña debe considerarse comprometida, incluso si se corrige el `.gitignore` ahora.

**Impacto:**

Cualquier persona con acceso al repositorio (o a su historial) puede obtener las credenciales de la base de datos PostgreSQL y de Grafana. Esto permite acceso directo y sin restricciones a todos los datos de candidatos.

**Remediación:**

1. Corregir inmediatamente `.gitignore` — descomentar la regla:
   ```
   **/.env
   ```
2. Ejecutar `git log --all --full-history -- .env` para verificar si los ficheros fueron comprometidos en el historial.
3. Si fueron rastreados: rotar **todas** las credenciales expuestas (DB, Grafana), limpiar el historial de git con `git filter-repo` o BFG Repo-Cleaner y forzar push (previa coordinación del equipo).
4. Implementar secret scanning automatizado (GitHub Advanced Security / Gitleaks) en la pipeline para prevenir futuros compromisos.

---

#### SEC-002 — Sin autenticación ni autorización en ningún endpoint

**Severidad:** CRÍTICO | **CVSS v3.1:** 9.8 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H)
**Categoría OWASP:** A01:2021 – Broken Access Control

**Descripción:**

Ningún endpoint de la API tiene protección de autenticación o autorización. Cualquier cliente con acceso de red puede leer, crear, modificar y eliminar candidatos, consultar posiciones y subir ficheros sin presentar ninguna credencial.

**Evidencia:**

Archivo `backend/src/index.ts` — registro de rutas sin ningún middleware de autenticación:
```typescript
app.use('/candidates', candidateRoutes);
app.post('/upload', uploadFile);
app.use('/positions', positionRoutes);
```

No existe ningún middleware de tipo `authenticate`, `authorize`, `verifyToken`, `requireAuth` o equivalente en ningún archivo del directorio `backend/src/`. No hay ningún modelo de usuario, sesión, JWT ni API key en el código fuente.

**Impacto:**

- Exposición total de datos PII de candidatos (nombre, email, teléfono, experiencia, CV) a cualquier actor no autenticado.
- Posibilidad de crear, modificar o eliminar candidatos y sus aplicaciones sin restricción.
- Capacidad de subir ficheros arbitrarios al servidor sin control de identidad.
- Incumplimiento directo del GDPR (Reglamento General de Protección de Datos) por falta de control de acceso sobre datos personales.

**Remediación:**

1. Implementar autenticación JWT o integración OAuth2/OIDC.
2. Crear un modelo de usuario con roles (recruiter, admin).
3. Añadir middleware `authenticate` que valide el token en cada petición.
4. Aplicar autorización basada en roles en controladores y servicios.
5. Proteger el endpoint `/upload` con autenticación y vincular el fichero subido al usuario autenticado.

---

#### SEC-003 — Endpoint `/metrics` de Prometheus expuesto sin autenticación

**Severidad:** CRÍTICO | **CVSS v3.1:** 9.1 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N)
**Categoría OWASP:** A01:2021 – Broken Access Control

**Descripción:**

El endpoint `/metrics` de Prometheus está registrado directamente en la aplicación Express y es públicamente accesible sin ningún tipo de autenticación. Este endpoint expone métricas detalladas del sistema operativo, proceso Node.js, memoria, uso de CPU y, lo más relevante, metadatos de todas las rutas HTTP con sus métodos, paths y códigos de estado.

**Evidencia:**

Archivo `backend/src/index.ts`, líneas 74–77:
```typescript
app.get('/metrics', async (_req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});
```

Este endpoint no tiene ningún middleware de autenticación previo. La información que expone incluye:

- Todas las rutas de la API con métodos HTTP y patrones exactos (`http_requests_total`, `http_request_duration_seconds`)
- Información de memoria heap de Node.js
- Número de descriptores de fichero activos
- Estadísticas del event loop

**Impacto:**

Un atacante puede usar esta información para mapear la superficie de ataque completa de la API, identificar endpoints de alto tráfico e inferir comportamiento interno del sistema sin necesidad de hacer ningún request exploratorio visible.

**Remediación:**

1. Mover el scraping de Prometheus a un puerto separado no expuesto públicamente, o añadir autenticación básica/token al endpoint.
2. Opción recomendada para Docker: exponer `/metrics` solo en la red interna de Docker, no publicar el puerto del backend directamente al host para scraping.
3. Opción alternativa: middleware de IP whitelist que solo permita el acceso desde la IP del contenedor Prometheus.

```typescript
app.get('/metrics', authenticateMetrics, async (_req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});
```

---

### 4.2 Altos

---

#### SEC-004 — Path traversal via `file.originalname` en subida de ficheros

**Severidad:** ALTO | **CVSS v3.1:** 8.1 (AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N)
**Categoría OWASP:** A03:2021 – Injection

**Descripción:**

El nombre de fichero generado en el almacenamiento en disco incorpora directamente `file.originalname`, que es el nombre del fichero tal como lo envía el cliente HTTP. Un atacante puede manipular este valor para incluir secuencias de path traversal como `../../etc/passwd` o para sobrescribir ficheros de configuración en el sistema de archivos del servidor.

**Evidencia:**

Archivo `backend/src/application/services/fileUploadService.ts`, líneas 7–11:
```typescript
filename: function (req, file, cb) {
    const uniqueSuffix = Date.now();
    cb(null, uniqueSuffix + '-' + file.originalname);  // VULNERABLE
}
```

Un cliente malicioso puede enviar un fichero con el nombre `../../config/app.conf` y el sistema construirá la ruta `../uploads/1700000000000-../../config/app.conf`.

**Impacto:**

Escritura de ficheros arbitrarios en el servidor, potencialmente fuera del directorio `uploads/`. Dependiendo de los permisos del proceso Node.js, esto puede permitir sobrescribir código de la aplicación, ficheros de configuración o crear ficheros ejecutables en rutas de sistema.

**Remediación:**

```typescript
import path from 'path';

filename: function (req, file, cb) {
    const uniqueSuffix = Date.now();
    const sanitizedName = path.basename(file.originalname).replace(/[^a-zA-Z0-9._-]/g, '_');
    cb(null, `${uniqueSuffix}-${sanitizedName}`);
}
```

Adicionalmente, verificar que el destino final de almacenamiento esté siempre dentro del directorio `uploads/` usando `path.resolve` y validando que el path resultante comienza con la ruta base esperada.

---

#### SEC-005 — Ruta absoluta del servidor expuesta en respuesta de `/upload`

**Severidad:** ALTO | **CVSS v3.1:** 7.5 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N)
**Categoría OWASP:** A05:2021 – Security Misconfiguration

**Descripción:**

El endpoint `/upload` devuelve directamente `req.file.path`, que es la ruta absoluta del fichero en el sistema de archivos del servidor. Esto expone la estructura interna de directorios del servidor al cliente.

**Evidencia:**

Archivo `backend/src/application/services/fileUploadService.ts`, líneas 46–49:
```typescript
res.status(200).json({
    filePath: req.file.path,  // e.g. "/usr/src/app/../uploads/1700000000000-cv.pdf"
    fileType: req.file.mimetype
});
```

**Impacto:**

Un atacante obtiene información sobre la estructura del sistema de archivos del servidor (rutas absolutas, nombres de directorio, organización del proyecto). Esta información facilita ataques de path traversal, inclusión de ficheros locales (LFI) y la explotación de otras vulnerabilidades que requieren conocer rutas del sistema.

**Remediación:**

Devolver únicamente un identificador opaco o una URL relativa en lugar de la ruta del sistema de archivos:

```typescript
res.status(200).json({
    filePath: req.file.filename,  // solo el nombre del fichero
    fileType: req.file.mimetype
});
```

---

#### SEC-006 — Bypass completo de validación en edición de candidatos

**Severidad:** ALTO | **CVSS v3.1:** 8.2 (AV:N/AC:L/PR:L/UI:N/S:U/C:N/I:H/A:N)
**Categoría OWASP:** A03:2021 – Injection

**Descripción:**

La función `validateCandidateData` en el validador central omite **toda** la validación de datos cuando el campo `id` está presente en el payload de la petición. Esto significa que cualquier operación de edición de candidato puede enviar datos maliciosos (payloads extremadamente largos, caracteres especiales, datos malformados) sin que sean validados.

**Evidencia:**

Archivo `backend/src/application/validator.ts`, líneas 80–84:
```typescript
export const validateCandidateData = (data: any) => {
    if (data.id) {
        // If id is provided, we are editing an existing candidate, so fields are not mandatory
        return;  // TODA la validación se omite aquí
    }
    // ... resto de validaciones solo ejecutadas en creación
```

**Impacto:**

Un atacante autenticado (o, dado SEC-002, cualquier usuario anónimo) puede:
- Inyectar strings extremadamente largos en campos de texto para causar errores de base de datos o consumo excesivo de memoria.
- Introducir caracteres especiales que podrían ser procesados por otras capas del sistema.
- Modificar el `email` de un candidato existente a un valor no válido, rompiendo la integridad referencial.
- Inyectar contenido en campos que luego son renderizados en el frontend (stored XSS).

**Remediación:**

Separar la validación de presencia obligatoria de la validación de formato/integridad. Los campos opcionales en edición deben seguir siendo validados en formato cuando están presentes:

```typescript
export const validateCandidateData = (data: any) => {
    const isEdit = !!data.id;

    if (!isEdit) {
        validateName(data.firstName);
        validateName(data.lastName);
        validateEmail(data.email);
    }

    // Validar formato siempre, independientemente de si es creación o edición
    if (data.firstName !== undefined) validateName(data.firstName);
    if (data.lastName !== undefined) validateName(data.lastName);
    if (data.email !== undefined) validateEmail(data.email);
    if (data.phone !== undefined) validatePhone(data.phone);
    if (data.address !== undefined) validateAddress(data.address);
    // ...
};
```

---

#### SEC-007 — CORS hardcodeado con origin incorrecto y no parametrizable

**Severidad:** ALTO | **CVSS v3.1:** 7.2 (AV:N/AC:L/PR:N/UI:N/S:C/C:L/I:L/A:N)
**Categoría OWASP:** A05:2021 – Security Misconfiguration

**Descripción:**

La configuración CORS está hardcodeada en el código fuente con un origin incorrecto (`http://localhost:4000`), mientras que el frontend real corre en el puerto `3000`. Esto indica que la protección CORS no está funcionando como se espera. Adicionalmente, al estar en el código fuente, no puede ser modificada por entorno sin un recompilado.

**Evidencia:**

Archivo `backend/src/index.ts`, líneas 55–59:
```typescript
app.use(cors({
  origin: 'http://localhost:4000',  // frontend corre en :3000
  credentials: true
}));
```

`docker-compose.yml` confirma que el frontend está mapeado al puerto `3000`:
```yaml
ports:
  - "3000:3000"
```

**Impacto:**

- El origin configurado es incorrecto, por lo que las peticiones con credenciales desde el frontend legítimo son bloqueadas (defecto funcional).
- La inconsistencia sugiere que la protección CORS fue desactivada o ignorada durante el desarrollo, potencialmente dejando el flag `credentials: true` con un origen wildcard en algún momento.
- Al no ser parametrizable, no es posible configurar dominios de producción sin modificar el código.

**Remediación:**

```typescript
const allowedOrigins = (process.env.CORS_ORIGIN ?? 'http://localhost:3000').split(',');

app.use(cors({
  origin: (origin, callback) => {
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error(`CORS policy: origin ${origin} not allowed`));
    }
  },
  credentials: true,
}));
```

Añadir `CORS_ORIGIN=http://localhost:3000` al `.env.example` y documentar el formato multi-origen para producción.

---

#### SEC-008 — Credenciales AWS expuestas en sesión SSH remota (workflow legacy)

**Severidad:** ALTO | **CVSS v3.1:** 8.8 (AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H)
**Categoría OWASP:** A02:2021 – Cryptographic Failures

**Descripción:**

El workflow de despliegue legacy (`legacy-ec2-deploy.yml`) inyecta las credenciales de AWS (`AWS_ACCESS_KEY_ID` y `AWS_SECRET_ACCESS_KEY`) directamente dentro de un heredoc SSH ejecutado en la instancia EC2. Estas credenciales quedan expuestas como variables de entorno del proceso remoto, visibles en `/proc/<pid>/environ` para cualquier proceso con los permisos adecuados en la instancia.

**Evidencia:**

Archivo `.github/workflows/legacy-ec2-deploy.yml`, líneas 51–53:
```yaml
ssh -o StrictHostKeyChecking=no -i private_key.pem ec2-user@"$EC2_INSTANCE" << 'EOF'
  export AWS_ACCESS_KEY_ID=${{ secrets.AWS_ACCESS_ID }}
  export AWS_SECRET_ACCESS_KEY=${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

Adicionalmente, la opción `-o StrictHostKeyChecking=no` deshabilita la verificación de la huella digital del host, lo que expone la conexión SSH a ataques de man-in-the-middle.

**Impacto:**

Comprometimiento de credenciales AWS de larga duración con potencial acceso a todos los recursos de la cuenta AWS. Cualquier proceso malicioso en la instancia EC2 podría extraer estas credenciales.

**Remediación:**

1. Este workflow está marcado como legacy (`workflow_dispatch` only). Considerar eliminarlo completamente.
2. Si se mantiene, reemplazar las credenciales estáticas por roles IAM de instancia EC2 con permisos mínimos.
3. Para la pipeline de CI/CD, usar GitHub OIDC para asumir roles IAM temporales sin necesidad de credenciales de larga duración.
4. Eliminar `-o StrictHostKeyChecking=no` y gestionar `known_hosts` de forma controlada.

---

#### SEC-009 — cAdvisor con modo `privileged` y montajes del host

**Severidad:** ALTO | **CVSS v3.1:** 7.8 (AV:L/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:H)
**Categoría OWASP:** A05:2021 – Security Misconfiguration

**Descripción:**

El servicio cAdvisor en `docker-compose.yml` se ejecuta con `privileged: true` y monta directorios críticos del sistema operativo del host (`/`, `/sys`, `/proc`, `/var/lib/docker`). Un contenedor privilegiado tiene acceso casi completo al kernel del host y puede ser usado para escapar del aislamiento de Docker.

**Evidencia:**

Archivo `docker-compose.yml`, líneas 122–138:
```yaml
cadvisor:
  image: gcr.io/cadvisor/cadvisor:v0.49.1
  privileged: true
  devices:
    - /dev/kmsg
  volumes:
    - /:/rootfs:ro
    - /var/run:/var/run:ro
    - /sys:/sys:ro
    - /var/lib/docker:/var/lib/docker:ro
    - /dev/disk:/dev/disk:ro
  ports:
    - "8081:8080"
```

El puerto `8081` está publicado en el host sin autenticación.

**Impacto:**

Si el contenedor cAdvisor es comprometido (por ejemplo, mediante una vulnerabilidad en su interfaz web expuesta en el puerto 8081), el atacante tiene acceso privilegiado al host completo. El volumen `/:/rootfs:ro` proporciona acceso de lectura a todo el sistema de archivos del host.

**Remediación:**

1. Incluir cAdvisor solo en el perfil `monitoring` (ya está), y nunca desplegar el perfil de monitoring en entornos de producción con acceso público.
2. Añadir autenticación básica al proxy inverso frente a cAdvisor.
3. Evaluar si `privileged: true` es estrictamente necesario para el caso de uso; en muchos entornos es posible usar solo las capacidades específicas requeridas (`CAP_SYS_ADMIN` para algunos casos).
4. Asegurarse de que el puerto `8081` nunca es accesible desde Internet en producción.

---

### 4.3 Medios

---

#### SEC-010 — Sin rate limiting en ningún endpoint

**Severidad:** MEDIO | **CVSS v3.1:** 6.5 (AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H)
**Categoría OWASP:** A04:2021 – Insecure Design

**Descripción:**

No existe ningún mecanismo de rate limiting en la aplicación Express. Todos los endpoints, incluyendo `/upload`, `/candidates` y `/positions`, aceptan un número ilimitado de peticiones por cliente por unidad de tiempo.

**Impacto:**

- Ataques de denegación de servicio (DoS) por saturación de peticiones.
- Ataques de fuerza bruta una vez que se implemente autenticación.
- Abuso del endpoint `/upload` para llenar el disco del servidor con ficheros.
- Enumeración de recursos (candidatos, posiciones) mediante peticiones masivas automatizadas.

**Remediación:**

Añadir `express-rate-limit` como middleware global y con configuraciones más estrictas en endpoints sensibles:

```typescript
import rateLimit from 'express-rate-limit';

const globalLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,  // 15 minutos
  max: 200,
  standardHeaders: true,
  legacyHeaders: false,
});

const uploadLimiter = rateLimit({
  windowMs: 60 * 1000,  // 1 minuto
  max: 5,
});

app.use(globalLimiter);
app.post('/upload', uploadLimiter, uploadFile);
```

---

#### SEC-011 — Sin headers de seguridad HTTP

**Severidad:** MEDIO | **CVSS v3.1:** 5.3 (AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N)
**Categoría OWASP:** A05:2021 – Security Misconfiguration

**Descripción:**

La aplicación Express no configura ningún header de seguridad HTTP. Ninguna respuesta incluye `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, `Strict-Transport-Security`, `Referrer-Policy` ni `Permissions-Policy`.

**Impacto:**

- Sin `X-Frame-Options` o `CSP frame-ancestors`: la aplicación es vulnerable a clickjacking.
- Sin `X-Content-Type-Options: nosniff`: el navegador puede interpretar tipos MIME de manera incorrecta (MIME sniffing attacks).
- Sin `Content-Security-Policy`: sin mitigación adicional para XSS en el frontend servido.
- Sin `Strict-Transport-Security`: el navegador no fuerza HTTPS en visitas futuras.

**Remediación:**

Añadir el paquete `helmet` que configura estos headers automáticamente siguiendo las mejores prácticas:

```typescript
import helmet from 'helmet';
app.use(helmet());
```

Para un CSP más específico, configurar las directivas según los recursos cargados por el frontend.

---

#### SEC-012 — Grafana con credenciales por defecto en `.env`

**Severidad:** MEDIO | **CVSS v3.1:** 6.8 (AV:N/AC:L/PR:H/UI:N/S:U/C:H/I:H/A:H)
**Categoría OWASP:** A07:2021 – Identification and Authentication Failures

**Descripción:**

El fichero `.env` en producción contiene `GRAFANA_ADMIN_PASSWORD=change_me_in_production`, que es una contraseña por defecto no cambiada. Grafana con estas credenciales expone dashboards de métricas y logs y permite la creación de plugins o data sources con acceso a recursos de red internos (SSRF via data sources).

**Evidencia:**

Archivo `.env`, línea 9:
```
GRAFANA_ADMIN_PASSWORD=change_me_in_production
```

**Impacto:**

Acceso de administrador a Grafana permite al atacante ver todos los logs de la aplicación (Loki), métricas internas (Prometheus) y potencialmente configurar data sources que realicen peticiones a recursos internos del entorno de red.

**Remediación:**

1. Cambiar inmediatamente la contraseña de Grafana a un valor fuerte y único.
2. Añadir la contraseña real como secreto en GitHub Actions o en el gestor de secretos de la plataforma de despliegue.
3. Nunca usar valores literales descriptivos como `change_me_in_production` en ficheros que son rastreados o distribuidos.

---

#### SEC-013 — Prometheus apunta al puerto incorrecto del backend

**Severidad:** MEDIO | **CVSS v3.1:** 4.3 (AV:N/AC:L/PR:L/UI:N/S:U/C:N/I:N/A:L)
**Categoría OWASP:** A05:2021 – Security Misconfiguration

**Descripción:**

La configuración de scraping de Prometheus apunta a `backend:8080`, pero el backend Express escucha en el puerto `3010`. Como consecuencia, Prometheus no puede recopilar métricas del backend y el sistema de monitorización está parcialmente no operativo.

**Evidencia:**

Archivo `monitoring/prometheus/prometheus.yml`, línea 19:
```yaml
- job_name: 'backend'
  static_configs:
    - targets: ['backend:8080']  # INCORRECTO: el backend corre en :3010
```

`backend/src/index.ts`, línea 93–104:
```typescript
const port = 3010;
app.listen(port, () => { ... });
```

**Impacto:**

El sistema de alertas basado en métricas del backend no funciona, reduciendo la capacidad de detección de incidentes de disponibilidad y rendimiento.

**Remediación:**

Corregir el target en `prometheus.yml`:
```yaml
targets: ['backend:3010']
```

---

#### SEC-014 — Promtail monta el Docker socket

**Severidad:** MEDIO | **CVSS v3.1:** 6.7 (AV:L/AC:L/PR:H/UI:N/S:U/C:H/I:H/A:H)
**Categoría OWASP:** A05:2021 – Security Misconfiguration

**Descripción:**

El contenedor Promtail monta `/var/run/docker.sock` con permisos de lectura/escritura. El Docker socket es equivalente a acceso root al host: cualquier proceso o atacante que comprometa el contenedor Promtail puede usarlo para crear nuevos contenedores privilegiados, montar el sistema de archivos del host y escalar privilegios.

**Evidencia:**

Archivo `docker-compose.yml`, línea 115:
```yaml
- /var/run/docker.sock:/var/run/docker.sock:ro
```

**Impacto:**

Aunque está montado como `:ro` (read-only), el Docker socket en modo lectura sigue permitiendo listar todos los contenedores, imágenes y secretos de entorno de todos los contenedores en ejecución.

**Remediación:**

1. Evaluar si el acceso al Docker socket es estrictamente necesario para la recolección de logs o si puede reemplazarse por el montaje directo de `/var/lib/docker/containers`.
2. Si es necesario, usar un proxy de Docker socket como `docker-socket-proxy` que limita los endpoints accesibles.
3. Asegurarse de que este perfil (`monitoring`) nunca se despliega en entornos de producción con acceso público.

---

#### SEC-015 — `npm audit` no bloquea el pipeline

**Severidad:** MEDIO | **CVSS v3.1:** 5.9 (AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N)
**Categoría OWASP:** A06:2021 – Vulnerable and Outdated Components

**Descripción:**

En el workflow de CI, los pasos de auditoría de dependencias tienen `continue-on-error: true`, lo que significa que si se detectan vulnerabilidades de severidad alta o crítica en las dependencias, el pipeline continúa y el código puede ser desplegado.

**Evidencia:**

Archivo `.github/workflows/ci.yml`, línea 43–44:
```yaml
- name: Dependency audit (backend)
  run: npm audit --production --audit-level=high
  continue-on-error: true  # vulnerabilidades altas no bloquean el despliegue
```

Idéntico patrón en el job `frontend_ci` (línea 77–78).

**Remediación:**

Eliminar `continue-on-error: true` para que las vulnerabilidades de nivel alto o crítico bloqueen el pipeline. Como alternativa gradual, usar Dependabot o Snyk para gestión de vulnerabilidades con alertas y PRs automáticos de actualización.

---

#### SEC-016 — Stack traces de errores en logs de producción

**Severidad:** MEDIO | **CVSS v3.1:** 5.3 (AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N)
**Categoría OWASP:** A09:2021 – Security Logging and Monitoring Failures

**Descripción:**

El manejador global de errores imprime el stack trace completo mediante `console.error(err.stack)`. En un entorno de producción, estos logs son recolectados por Promtail y enviados a Loki. Si los logs son accesibles (como se describe en SEC-012 y SEC-003), los stack traces revelan rutas de ficheros del servidor, nombres de módulos internos y flujos de ejecución.

**Evidencia:**

Archivo `backend/src/index.ts`, líneas 99–103:
```typescript
app.use((err: any, req: Request, res: Response, next: NextFunction) => {
  console.error(err.stack);  // stack trace expuesto en logs
  res.type('text/plain');
  res.status(500).send('Something broke!');
});
```

**Remediación:**

Implementar logging estructurado con niveles diferenciados por entorno:

```typescript
app.use((err: any, req: Request, res: Response, next: NextFunction) => {
  const isDev = process.env.NODE_ENV !== 'production';
  logger.error({
    message: err.message,
    stack: isDev ? err.stack : undefined,
    requestId: req.headers['x-request-id'],
  });
  res.status(500).json({ error: 'Internal server error' });
});
```

---

#### SEC-017 — Workflow SAST vacío (solo placeholder)

**Severidad:** MEDIO | **CVSS v3.1:** 5.3 (AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N)
**Categoría OWASP:** A08:2021 – Software and Data Integrity Failures

**Descripción:**

El workflow `sast-template.yml` existe en el repositorio pero no realiza ningún análisis de seguridad real. Solo imprime mensajes de texto y no está conectado a la pipeline principal de CI (no es llamado por `ci.yml`).

**Evidencia:**

Archivo `.github/workflows/sast-template.yml`:
```yaml
- name: Placeholder for SAST tool
  run: |
    echo "Add your SAST tool here (e.g., CodeQL, Semgrep)."
```

**Impacto:**

La apariencia de tener un workflow SAST puede dar una falsa sensación de seguridad. No se realizan análisis de código estático, por lo que vulnerabilidades como las identificadas en SEC-004, SEC-006 no serían detectadas automáticamente.

**Remediación:**

Implementar CodeQL (disponible gratuitamente para repositorios públicos de GitHub) o Semgrep en la pipeline CI. Conectarlo como job dependiente en `ci.yml` o como workflow separado disparado en cada pull request.

---

### 4.4 Bajos

---

#### SEC-018 — Puerto del servidor hardcodeado en código fuente

**Severidad:** BAJO | **CVSS v3.1:** 3.1 (AV:N/AC:H/PR:N/UI:R/S:U/C:N/I:L/A:N)
**Categoría OWASP:** A05:2021 – Security Misconfiguration

**Descripción:**

El puerto de escucha del servidor Express está hardcodeado como `3010` en el código fuente en lugar de leerse desde una variable de entorno.

**Evidencia:**

Archivo `backend/src/index.ts`, línea 93:
```typescript
const port = 3010;
```

**Remediación:**

```typescript
const port = parseInt(process.env.PORT ?? '3010', 10);
```

---

#### SEC-019 — `npm install` en lugar de `npm ci` en Dockerfile

**Severidad:** BAJO | **CVSS v3.1:** 3.7 (AV:N/AC:H/PR:N/UI:N/S:U/C:N/I:L/A:N)
**Categoría OWASP:** A06:2021 – Vulnerable and Outdated Components

**Descripción:**

El `Dockerfile.dev` usa `npm install` en lugar de `npm ci`. `npm install` puede actualizar el `package-lock.json` y resolver dependencias a versiones no exactas, mientras que `npm ci` garantiza instalaciones reproducibles y deterministas a partir del lockfile.

**Evidencia:**

Archivo `backend/Dockerfile.dev`, línea 10:
```dockerfile
RUN npm install
```

**Remediación:**

```dockerfile
RUN npm ci --omit=dev
```

Usar `--omit=dev` para no incluir devDependencies en la imagen de producción.

---

#### SEC-020 — node-exporter con `pid: host`

**Severidad:** BAJO | **CVSS v3.1:** 3.8 (AV:L/AC:L/PR:L/UI:N/S:C/C:L/I:N/A:N)
**Categoría OWASP:** A05:2021 – Security Misconfiguration

**Descripción:**

El contenedor `node-exporter` usa `pid: host`, compartiendo el namespace de PIDs con el host. Esto permite que el contenedor vea y, con los permisos adecuados, envíe señales a todos los procesos del host.

**Evidencia:**

Archivo `docker-compose.yml`, línea 144:
```yaml
node-exporter:
  pid: host
```

**Remediación:**

Evaluar si `pid: host` es necesario para las métricas que se desean recopilar. En muchos casos, el montaje de `/proc:/host/proc:ro` es suficiente y `pid: host` puede eliminarse. Asegurar que este servicio solo se despliega en el perfil `monitoring` controlado (ya está correctamente configurado con `profiles: [monitoring]`).

---

#### SEC-021 — Imagen de desarrollo usada en despliegue (Dockerfile.dev en CD)

**Severidad:** BAJO | **CVSS v3.1:** 3.1 (AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:N/A:N)
**Categoría OWASP:** A05:2021 – Security Misconfiguration

**Descripción:**

El pipeline de CD (`cd.yml`) construye las imágenes Docker usando `Dockerfile.dev`, que está diseñado para desarrollo con recarga en caliente (`ts-node-dev`). Esta imagen incluye todas las devDependencies, herramientas de desarrollo y ejecuta TypeScript sin compilar. Una imagen de producción debería compilar el código TypeScript y ejecutar solo el JavaScript resultante con un proceso Node.js sin herramientas de desarrollo.

**Evidencia:**

Archivo `.github/workflows/cd.yml`, líneas 30–35:
```yaml
- name: Build backend image
  run: |
    docker build \
      -f backend/Dockerfile.dev \  # imagen de desarrollo en pipeline CD
      -t "${IMAGE_NAME}:${{ github.sha }}" \
      backend
```

**Remediación:**

Crear un `Dockerfile.prod` multi-stage:
```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine AS runtime
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/prisma ./prisma
RUN npx prisma generate
CMD ["node", "dist/index.js"]
```

---

## 5. Análisis de Pipeline CI/CD

```
.github/workflows/
├── ci.yml              — Build, lint, test y audit (backend + frontend)
├── cd.yml              — Build y push de imágenes Docker a GHCR + stub de deploy
├── legacy-ec2-deploy.yml — Despliegue manual a EC2 (workflow_dispatch)
└── sast-template.yml   — Placeholder SAST (sin implementación real)
```

### Estado actual de seguridad en CI/CD

| Control | Estado | Workflow | Observación |
|---|---|---|---|
| Unit tests backend | Activo | `ci.yml` | Correcto |
| Unit tests frontend | Activo | `ci.yml` | Correcto |
| Lint backend (ESLint) | Activo | `ci.yml` | Correcto |
| Lint frontend | Activo | `ci.yml` | Correcto |
| `npm audit` backend | Activo pero no bloquea | `ci.yml` | `continue-on-error: true` |
| `npm audit` frontend | Activo pero no bloquea | `ci.yml` | `continue-on-error: true` |
| SAST (análisis estático de seguridad) | No activo | `sast-template.yml` | Solo placeholder |
| Secret scanning | No activo | — | No configurado |
| Container scanning (Trivy/Grype) | No activo | `cd.yml` | No hay pasos de scanning |
| Revisión de imagen base | No activo | — | No hay policy de versiones |
| DAST (pruebas dinámicas) | No activo | — | No configurado |
| Firma de imágenes (cosign) | No activo | `cd.yml` | Imágenes no firmadas |

### Diagrama de la pipeline actual vs. pipeline objetivo

```mermaid
flowchart TD
    PR[Pull Request] --> CI[ci.yml]
    CI --> backend_ci[Backend CI]
    CI --> frontend_ci[Frontend CI]
    backend_ci --> lint_b[Lint]
    backend_ci --> build_b[Build]
    backend_ci --> test_b[Unit Tests]
    backend_ci --> audit_b["npm audit (no bloquea)"]
    frontend_ci --> build_f[Build]
    frontend_ci --> test_f[Unit Tests]
    frontend_ci --> lint_f[Lint]
    frontend_ci --> audit_f["npm audit (no bloquea)"]

    PUSH[Push main] --> CD[cd.yml]
    CD --> build_images[Build Docker Images]
    build_images --> push_ghcr[Push GHCR]
    push_ghcr --> deploy_stub["Deploy Stub (TODO)"]

    MANUAL[workflow_dispatch] --> legacy[legacy-ec2-deploy.yml]
    MANUAL2[workflow_dispatch] --> sast_empty["sast-template.yml (vacío)"]

    style audit_b fill:#f9a,stroke:#c00
    style audit_f fill:#f9a,stroke:#c00
    style sast_empty fill:#f9a,stroke:#c00
    style legacy fill:#f9a,stroke:#c00
    style deploy_stub fill:#ff9,stroke:#aa0
```

---

## 6. Análisis de Infraestructura y Contenedores

### Superficie de red expuesta (docker-compose.yml)

| Servicio | Puerto expuesto en host | Autenticación | Perfiles |
|---|---|---|---|
| backend | `3010` | Ninguna (SEC-002) | siempre activo |
| frontend | `3000` | N/A (app React) | siempre activo |
| db (PostgreSQL) | `${DB_PORT}` (5432) | Credenciales DB | siempre activo |
| prometheus | `9090` | Ninguna | monitoring |
| grafana | `3001` | admin/change_me (SEC-012) | monitoring |
| loki | `3100` | Ninguna | monitoring |
| cadvisor | `8081` | Ninguna (SEC-009) | monitoring |
| node-exporter | `9100` | Ninguna (SEC-020) | monitoring |
| locust | `8089` | Ninguna | loadtest |

**Observaciones críticas:**
- La base de datos PostgreSQL expone su puerto directamente al host. En producción, este puerto nunca debería ser accesible desde fuera de la red Docker interna.
- El perfil `monitoring` expone múltiples servicios sin autenticación. Si el host es accesible desde Internet, toda la infraestructura de monitoring es pública.
- Loki no tiene autenticación y expone el puerto `3100` al host, permitiendo acceso directo a los logs de la aplicación.

### Riesgos del stack de monitoring

El stack de monitoring completo (Prometheus + Grafana + Loki + Promtail + cAdvisor + node-exporter) tiene acceso a información altamente sensible:

- **Promtail**: lee logs de todos los contenedores, incluyendo potenciales tokens, credenciales y datos PII en logs de aplicación.
- **cAdvisor**: acceso privilegiado al sistema de ficheros del host.
- **Prometheus**: almacena historial de métricas que puede revelar patrones de uso.
- **Grafana**: punto de entrada único sin autenticación fuerte que agrega toda esta información.

---

## 7. Fortalezas Identificadas

A pesar de los hallazgos anteriores, el repositorio presenta varias prácticas positivas:

| Fortaleza | Descripción |
|---|---|
| Arquitectura en capas (DDD) | Separación clara entre domain, application, presentation y routes facilita la inserción de controles de seguridad |
| Prisma ORM | Elimina el riesgo de SQL injection mediante queries parametrizadas y tipado estático |
| Validación centralizada | `validator.ts` proporciona un punto único para extender las validaciones de seguridad |
| OpenAPI spec | `api-spec.yaml` define contratos que pueden usarse para validación automática y testing de seguridad |
| `.env.example` documentado | El fichero de ejemplo incluye advertencias explícitas sobre no commitear secrets |
| Pipeline CI con lint y tests | ESLint configurado con `--max-warnings=0` previene degradación de calidad |
| `npm ci` en CI (no en Docker) | Los workflows de CI usan `npm ci` para builds reproducibles |
| Stack de monitoring funcional | Prometheus + Grafana + Loki proporciona la base para observabilidad y detección de incidentes |
| Separación por perfiles Docker | Monitoring y loadtest en perfiles separados evita su activación accidental |
| `GF_USERS_ALLOW_SIGN_UP: "false"` | Grafana no permite auto-registro de usuarios |

---

## 8. Recomendaciones Priorizadas

### Fase 1 — Inmediata (bloquea producción)

| Prioridad | Acción | Hallazgo | Esfuerzo |
|---|---|---|---|
| 1 | Corregir `.gitignore` y rotar credenciales comprometidas | SEC-001 | Bajo |
| 2 | Implementar autenticación JWT en todos los endpoints | SEC-002 | Alto |
| 3 | Proteger endpoint `/metrics` con autenticación o red interna | SEC-003 | Bajo |
| 4 | Sanitizar `file.originalname` y usar solo `path.basename` | SEC-004 | Bajo |
| 5 | No devolver `filePath` absoluto en respuesta de `/upload` | SEC-005 | Bajo |
| 6 | Corregir lógica de bypass de validación en edición | SEC-006 | Bajo |

### Fase 2 — Corto plazo (sprint actual)

| Prioridad | Acción | Hallazgo | Esfuerzo |
|---|---|---|---|
| 7 | Parametrizar CORS desde variable de entorno y corregir el puerto | SEC-007 | Bajo |
| 8 | Añadir `helmet` para headers de seguridad HTTP | SEC-011 | Bajo |
| 9 | Implementar rate limiting con `express-rate-limit` | SEC-010 | Bajo |
| 10 | Eliminar `continue-on-error: true` en `npm audit` | SEC-015 | Bajo |
| 11 | Implementar SAST real (CodeQL o Semgrep) en CI | SEC-017 | Medio |
| 12 | Cambiar contraseña de Grafana a valor seguro | SEC-012 | Bajo |
| 13 | Corregir puerto del backend en `prometheus.yml` | SEC-013 | Mínimo |

### Fase 3 — Medio plazo (próximo sprint)

| Prioridad | Acción | Hallazgo | Esfuerzo |
|---|---|---|---|
| 14 | Revisar montaje del Docker socket en Promtail | SEC-014 | Medio |
| 15 | Evaluar y reducir privilegios de cAdvisor | SEC-009 | Medio |
| 16 | Añadir logging estructurado, eliminar stack traces en prod | SEC-016 | Medio |
| 17 | Crear `Dockerfile.prod` multi-stage y actualizar CD | SEC-021 | Medio |
| 18 | Parametrizar puerto del servidor desde env | SEC-018 | Mínimo |
| 19 | Cambiar `npm install` a `npm ci` en Dockerfile | SEC-019 | Mínimo |

### Fase 4 — Largo plazo (roadmap)

- Implementar secret scanning automatizado (Gitleaks, GitHub Advanced Security) integrado en la pipeline.
- Añadir container scanning (Trivy) en el workflow CD antes del push de imágenes.
- Migrar credenciales AWS a GitHub OIDC con roles IAM de corta duración.
- Implementar Infrastructure as Code (Terraform) para EC2, RDS, IAM y security groups.
- Introducir DAST (OWASP ZAP) como parte del ciclo de testing de integración.
- Realizar threat modeling formal sobre los flujos de gestión de candidatos y subida de ficheros.
- Establecer política de rotación de secretos y uso de AWS Secrets Manager o HashiCorp Vault.

---

## 9. Métricas Consolidadas

### Distribución de hallazgos por severidad

| Severidad | Cantidad | % del total |
|---|---|---|
| Crítico | 3 | 14.3% |
| Alto | 6 | 28.6% |
| Medio | 8 | 38.1% |
| Bajo | 4 | 19.0% |
| **Total** | **21** | **100%** |

### Distribución por categoría OWASP Top 10

| Categoría OWASP | Hallazgos | IDs |
|---|---|---|
| A01 – Broken Access Control | 3 | SEC-002, SEC-003, SEC-009 |
| A02 – Cryptographic Failures | 2 | SEC-001, SEC-008 |
| A03 – Injection | 2 | SEC-004, SEC-006 |
| A04 – Insecure Design | 1 | SEC-010 |
| A05 – Security Misconfiguration | 10 | SEC-005, SEC-007, SEC-009, SEC-011, SEC-013, SEC-014, SEC-018, SEC-019, SEC-020, SEC-021 |
| A06 – Vulnerable Components | 2 | SEC-015, SEC-019 |
| A07 – Auth. Failures | 1 | SEC-012 |
| A08 – Software Integrity | 1 | SEC-017 |
| A09 – Logging Failures | 1 | SEC-016 |

### Distribución por componente

| Componente | Hallazgos |
|---|---|
| Backend (Express/Node.js) | SEC-002, SEC-003, SEC-006, SEC-007, SEC-010, SEC-011, SEC-016, SEC-018 |
| Ficheros de configuración (.env, .gitignore) | SEC-001, SEC-012 |
| Servicio de subida de ficheros | SEC-004, SEC-005 |
| CI/CD (GitHub Actions) | SEC-008, SEC-015, SEC-017, SEC-021 |
| Infraestructura (docker-compose) | SEC-009, SEC-013, SEC-014, SEC-019, SEC-020 |

### Madurez DevSecOps actual vs. objetivo

| Dimensión | Estado actual | Estado objetivo |
|---|---|---|
| Control de acceso a API | Sin autenticación | JWT/OAuth2 + RBAC |
| Gestión de secretos | `.env` en riesgo de git | Vault / AWS Secrets Manager |
| SAST en CI | Placeholder vacío | CodeQL + Semgrep activos |
| SCA (dependencias) | Audit no bloqueante | Dependabot + audit bloqueante |
| Container scanning | No existe | Trivy en CD pipeline |
| Secret scanning | No existe | Gitleaks en pre-commit y CI |
| Logging y auditoría | Console.log sin estructura | Logging estructurado + audit trail |
| Headers de seguridad | Sin configurar | Helmet configurado |
| Rate limiting | Sin implementar | express-rate-limit por endpoint |
| Infraestructura como código | Ausente | Terraform para toda la infra |

---

*Informe generado mediante revisión estática de código y análisis de configuración. Para un análisis completo se recomienda complementar con pruebas dinámicas (DAST), análisis de dependencias con CVE lookup actualizado y threat modeling formal.*
