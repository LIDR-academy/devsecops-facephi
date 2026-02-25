# Auditoría de Seguridad de Código — facephi-secdevops

> **Fecha:** 2026-02-25
> **Auditor:** Análisis estático automatizado + revisión manual
> **Alcance:** Backend (Node.js/TypeScript/Prisma), Frontend (React/Nginx), Infraestructura (Terraform/AWS), Orquestación (Docker Compose), CI/CD (GitHub Actions), Monitorización (Prometheus/Loki/Grafana)

---

## Resumen Ejecutivo

| Gravedad        | Hallazgos |
|-----------------|-----------|
| 🔴 CRÍTICO      | 3         |
| 🟠 ALTO         | 7         |
| 🟡 MEDIO        | 9         |
| 🔵 BAJO         | 8         |
| ⚪ INFORMACIONAL | 4         |
| **TOTAL**       | **31**    |

La aplicación presenta **exposición activa de credenciales de base de datos en el repositorio git** y **ausencia total de autenticación en la API**, lo que permite a cualquier actor no autorizado leer, modificar y crear registros de candidatos. Estos dos factores, combinados con la apertura irrestricta de puertos de infraestructura, constituyen un riesgo de compromiso total del sistema en su estado actual.

---

## Metodología

Ficheros auditados:

- `backend/src/**` — lógica de negocio, controladores, rutas, validación, carga de ficheros
- `backend/prisma/` — esquema y seed de base de datos
- `backend/Dockerfile`
- `frontend/nginx.conf`, `frontend/Dockerfile`
- `docker-compose.yml`
- `.env`, `.env.example`, `backend/.env`
- `.gitignore`
- `.github/workflows/ci.yml`
- `tf/*.tf`, `tf/user_data_*.sh`
- `monitoring/*.yml`
- `load-tests/locustfile.py`

---

## CRÍTICO

---

### C-01 — Credenciales reales de base de datos commiteadas al repositorio

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `.env` línea 14, `backend/.env` línea 1 |
| **CWE**     | CWE-312: Almacenamiento en texto plano de información sensible |
| **CVSS v3** | 9.8 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H) |

**Evidencia:**

```
# .env — línea 14
DB_PASSWORD=D1ymf8wyQEGthFR1E9xhCq

# backend/.env — línea 1
DB_PASSWORD=D1ymf8wyQEGthFR1E9xhCq
```

**Impacto:**
Cualquier persona con acceso de lectura al repositorio (colaboradores, bots de análisis, fugas de GitHub) obtiene la contraseña real de la base de datos PostgreSQL. Combinado con la exposición del puerto de la base de datos en entornos mal configurados, el atacante puede exfiltrar, modificar o destruir todos los datos de candidatos.

**Remediación:**

1. **Rotar inmediatamente** la contraseña `D1ymf8wyQEGthFR1E9xhCq` en todos los entornos.
2. Eliminar los ficheros `.env` del historial de git:
   ```bash
   git filter-repo --path .env --invert-paths
   git filter-repo --path backend/.env --invert-paths
   git push --force --all
   ```
3. Almacenar secretos en AWS Secrets Manager o HashiCorp Vault e inyectarlos en tiempo de ejecución.
4. Añadir un pre-commit hook con `git-secrets` o `trufflehog` para prevenir futuros commits de credenciales.

---

### C-02 — `.gitignore` no excluye los ficheros `.env`

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `.gitignore` líneas 3 y 30 |
| **CWE**     | CWE-538: Inclusión de información sensible en ficheros de control de versiones |
| **CVSS v3** | 9.1 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N) |

**Evidencia:**

```gitignore
# .gitignore — línea 3 (COMENTADA — sin efecto)
#**/.env

# .gitignore — línea 30 (también es un comentario)
# .env
```

La regla `**/.env` está comentada con `#`, por lo que git **no ignora ningún fichero `.env`**. Esto explica por qué `.env` y `backend/.env` están trackeados en el repositorio.

**Impacto:**
Causa raíz del hallazgo C-01. Sin esta corrección cualquier nueva credencial volverá a commitearse.

**Remediación:**

```gitignore
# Reemplazar las líneas comentadas por:
**/.env
.env
```

Verificar que no quedan ficheros `.env` trackeados:

```bash
git ls-files | grep '\.env'
git rm --cached .env backend/.env
```

---

### C-03 — Ausencia total de autenticación y autorización en la API

| Campo       | Detalle |
|-------------|---------|
| **Ficheros** | `backend/src/routes/candidateRoutes.ts`, `backend/src/routes/positionRoutes.ts`, `backend/src/index.ts` |
| **CWE**     | CWE-306: Falta de autenticación para función crítica |
| **CVSS v3** | 9.8 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H) |

**Evidencia:**

```typescript
// candidateRoutes.ts
router.post('/', async (req, res) => { ... });          // Crear candidato — sin auth
router.get('/:id', getCandidateById);                    // Leer candidato — sin auth
router.put('/:id', updateCandidateStageController);      // Modificar etapa — sin auth

// positionRoutes.ts
router.get('/', getAllPositions);                          // Listar posiciones — sin auth
router.get('/:id/candidates', getCandidatesByPosition);   // Listar candidatos — sin auth
router.get('/:id/interviewflow', getInterviewFlowByPosition); // Sin auth

// index.ts — línea 46
app.post('/upload', uploadFile); // Subida de CVs — sin auth
```

No existe ningún middleware de autenticación (JWT, sesión, API key) en ninguna ruta.

**Impacto:**
Un actor externo puede: enumerar todos los candidatos, ver datos personales (nombre, email, teléfono, dirección, historial laboral y educativo), crear candidatos falsos, modificar el estado de entrevistas, y subir ficheros arbitrarios al servidor.

**Remediación:**

```typescript
import jwt from 'jsonwebtoken';

const authMiddleware = (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'Unauthorized' });
  try {
    req.user = jwt.verify(token, process.env.JWT_SECRET!);
    next();
  } catch {
    res.status(401).json({ error: 'Invalid token' });
  }
};

app.use('/candidates', authMiddleware, candidateRoutes);
app.use('/positions', authMiddleware, positionRoutes);
app.post('/upload', authMiddleware, uploadFile);
```

Implementar además autorización basada en roles (RBAC) para operaciones de escritura.

---

## ALTO

---

### H-01 — MIME type spoofing en la carga de ficheros

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `backend/src/application/services/fileUploadService.ts` líneas 15–21 |
| **CWE**     | CWE-434: Carga sin restricción de ficheros de tipo peligroso |
| **CVSS v3** | 8.1 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N) |

**Evidencia:**

```typescript
// fileUploadService.ts — líneas 15-21
const fileFilter = (req, file, cb) => {
    if (file.mimetype === 'application/pdf' ||
        file.mimetype === 'application/vnd.openxmlformats-...') {
        cb(null, true);   // ← mimetype proviene del cliente, no del contenido real
    } else {
        cb(null, false);
    }
};
```

`file.mimetype` proviene de la cabecera `Content-Type` enviada por el cliente. Un atacante puede subir un ejecutable (`.php`, `.sh`, script Node.js) con `Content-Type: application/pdf` y pasará el filtro.

**Impacto:**
Carga de webshells o ejecutables maliciosos en el servidor. Si el directorio de uploads es accesible, puede obtenerse ejecución remota de código (RCE).

**Remediación:**

```typescript
import { fileTypeFromBuffer } from 'file-type'; // npm install file-type

// Validar por magic bytes en lugar de por cabecera HTTP
const ALLOWED_TYPES = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
];

// Leer los primeros bytes del fichero antes de aceptarlo
const detectedType = await fileTypeFromBuffer(fileBuffer);
if (!detectedType || !ALLOWED_TYPES.includes(detectedType.mime)) {
    return cb(new Error('Invalid file type'), false);
}
```

---

### H-02 — Ruta interna del servidor expuesta en la respuesta de `/upload`

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `backend/src/application/services/fileUploadService.ts` líneas 47–49 |
| **CWE**     | CWE-200: Exposición de información sensible |
| **CVSS v3** | 7.5 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N) |

**Evidencia:**

```typescript
// fileUploadService.ts — líneas 47-49
res.status(200).json({
    filePath: req.file.path,   // ← ruta absoluta: /app/uploads/1716892800000-cv.pdf
    fileType: req.file.mimetype
});
```

**Impacto:**
Revela la estructura interna de directorios del contenedor. Facilita la construcción de ataques de path traversal y permite localizar ficheros subidos para accederlos directamente.

**Remediación:**

```typescript
import path from 'path';

res.status(200).json({
    fileId: path.basename(req.file.filename), // sólo el nombre del fichero
    fileType: req.file.mimetype
});
```

---

### H-03 — Puerto SSH (22) abierto a Internet en todos los Security Groups

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `tf/security_groups.tf` líneas 19–28 y 58–67 |
| **CWE**     | CWE-284: Control de acceso inadecuado |
| **CVSS v3** | 8.6 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:L/A:N) |

**Evidencia:**

```hcl
# tf/security_groups.tf — líneas 20-28 (backend SG, idéntico en frontend SG)
dynamic "ingress" {
  for_each = var.key_name != "" ? [1] : []
  content {
    description = "SSH access"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]   # ← internet completo
  }
}
```

**Impacto:**
Expone SSH a ataques de fuerza bruta, credential stuffing y exploits de OpenSSH. Si la clave privada se ve comprometida, el atacante obtiene acceso shell a las instancias EC2.

**Remediación:**

```hcl
# Restringir a la IP del equipo de operaciones
cidr_blocks = [var.admin_cidr]  # p.ej. "203.0.113.10/32"
```

Alternativa preferida: eliminar SSH completamente y usar **AWS Systems Manager Session Manager** (sin necesidad de abrir el puerto 22).

---

### H-04 — Puerto 8080 (backend) expuesto directamente a Internet

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `tf/security_groups.tf` líneas 11–17 |
| **CWE**     | CWE-284: Control de acceso inadecuado |
| **CVSS v3** | 8.2 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:L/A:N) |

**Evidencia:**

```hcl
# tf/security_groups.tf — líneas 11-17
ingress {
  description = "Backend application port"
  from_port   = var.backend_port   # 8080
  to_port     = var.backend_port
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"]   # ← internet completo
}
```

El backend sin autenticación (C-03) es accesible directamente desde internet, saltando el proxy Nginx del frontend y sus cabeceras de seguridad.

**Remediación:**

```hcl
# Restringir el puerto 8080 sólo al Security Group del frontend (o del ALB)
ingress {
  description     = "Backend port from frontend only"
  from_port       = var.backend_port
  to_port         = var.backend_port
  protocol        = "tcp"
  security_groups = [aws_security_group.frontend.id]
}
```

---

### H-05 — Credenciales AWS y de BD expuestas en comandos SSH del CI/CD

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `.github/workflows/ci.yml` líneas 245–253 |
| **CWE**     | CWE-522: Credenciales protegidas de forma insuficiente |
| **CVSS v3** | 7.8 (AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:N) |

**Evidencia:**

```yaml
# ci.yml — líneas 245-253
run: |
  ssh ec2-user@${{ secrets.EC2_INSTANCE }} \
    "AWS_ACCESS_KEY_ID='${AWS_ACCESS_KEY_ID}' \
     AWS_SECRET_ACCESS_KEY='${AWS_SECRET_ACCESS_KEY}' \
     DB_PASSWORD='${DB_PASSWORD}' \
     bash -s" << 'REMOTE'
```

Las variables se pasan inline en la línea de comandos SSH, visibles en `ps aux` durante la ejecución del proceso en la instancia EC2.

**Impacto:**
Un proceso con acceso a `ps` en el host puede capturar las credenciales de AWS y de la base de datos en el momento del despliegue.

**Remediación:**

1. Usar el **IAM Instance Profile** (ya configurado en `tf/s3.tf`) para autenticación con ECR, eliminando `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`.
2. Obtener secretos de BD desde AWS Secrets Manager dentro del script remoto, sin pasarlos como argumentos:

```bash
ssh ec2-user@$HOST 'bash -s' << 'REMOTE'
  export DB_PASSWORD=$(aws secretsmanager get-secret-value \
    --secret-id prod/db/password --query SecretString --output text)
REMOTE
```

---

### H-06 — Sin rate limiting en ningún endpoint

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `backend/src/index.ts` (ausencia de middleware) |
| **CWE**     | CWE-770: Asignación de recursos sin límites |
| **CVSS v3** | 7.5 (AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H) |

**Evidencia:**
No existe ningún middleware de rate limiting en `index.ts`. Los endpoints `/candidates` (POST), `/upload` (POST) y `/positions` (GET) no tienen restricciones de frecuencia.

**Impacto:**
- `/upload` puede usarse para llenar el disco del servidor.
- `POST /candidates` permite la creación masiva de registros basura.
- Cualquier endpoint es vulnerable a DoS por inundación de peticiones.

**Remediación:**

```typescript
import rateLimit from 'express-rate-limit'; // npm install express-rate-limit

const apiLimiter = rateLimit({ windowMs: 15 * 60 * 1000, max: 100 });
const uploadLimiter = rateLimit({ windowMs: 60 * 60 * 1000, max: 10 });

app.use('/candidates', apiLimiter, candidateRoutes);
app.use('/positions', apiLimiter, positionRoutes);
app.post('/upload', uploadLimiter, uploadFile);
```

---

### H-07 — Prometheus UI expuesto públicamente sin autenticación

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `docker-compose.yml` líneas 183–184 |
| **CWE**     | CWE-306: Falta de autenticación para función crítica |
| **CVSS v3** | 7.5 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N) |

**Evidencia:**

```yaml
# docker-compose.yml — líneas 183-184
prometheus:
  ports:
    - "9090:9090"   # ← expuesto en todas las interfaces del host
```

La UI de Prometheus es accesible desde internet sin credenciales. Combinado con `--web.enable-lifecycle` (ver L-01), permite operaciones administrativas remotas.

**Impacto:**
Un atacante consulta métricas internas de la aplicación, base de datos e infraestructura, y puede recargar la configuración o detener Prometheus remotamente.

**Remediación:**

```yaml
# Restringir a localhost únicamente
prometheus:
  ports:
    - "127.0.0.1:9090:9090"
```

---

## MEDIO

---

### M-01 — Grafana con credenciales por defecto `admin/admin`

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `docker-compose.yml` línea 242 |
| **CWE**     | CWE-1391: Uso de credenciales por defecto débiles |
| **CVSS v3** | 6.5 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:L/A:N) |

**Evidencia:**

```yaml
# docker-compose.yml — línea 242
GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD:-admin}
```

Si la variable de entorno no está definida, Grafana arranca con `admin/admin`.

**Remediación:**

```yaml
# El modificador :? fuerza error de arranque si la variable no está definida
GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD:?GRAFANA_ADMIN_PASSWORD must be set}
```

---

### M-02 — Content Security Policy con `unsafe-inline`

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `frontend/nginx.conf` línea 27 |
| **CWE**     | CWE-1021: Restricción inadecuada de marcos HTML (XSS) |
| **CVSS v3** | 6.1 (AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N) |

**Evidencia:**

```nginx
# nginx.conf — línea 27
add_header Content-Security-Policy "default-src 'self';
  script-src 'self' 'unsafe-inline';     # ← permite scripts inline
  connect-src 'self' http://localhost:8080;" always; # ← URL interna expuesta
```

`unsafe-inline` en `script-src` anula gran parte de la protección XSS del CSP.

**Remediación:**

```nginx
add_header Content-Security-Policy "default-src 'self';
  script-src 'self';
  style-src 'self' https://cdn.jsdelivr.net;
  font-src 'self' data:;
  img-src 'self' data:;
  connect-src 'self';" always;
```

Usar nonces CSP para scripts legítimos que requieran inline.

---

### M-03 — Sin HTTPS/TLS en toda la infraestructura

| Campo       | Detalle |
|-------------|---------|
| **Ficheros** | `frontend/nginx.conf`, `tf/security_groups.tf`, `docker-compose.yml` |
| **CWE**     | CWE-319: Transmisión en texto plano de información sensible |
| **CVSS v3** | 6.5 (AV:N/AC:H/PR:N/UI:R/S:U/C:H/I:H/A:N) |

**Evidencia:**
Nginx escucha únicamente en el puerto 80 (HTTP). No existe ninguna referencia a certificados TLS en toda la infraestructura.

**Impacto:**
Datos personales de candidatos (nombre, email, teléfono, CVs) transmitidos en texto plano. Vulnerable a ataques MITM y sniffing.

**Remediación:**

```nginx
server {
  listen 443 ssl;
  ssl_certificate     /etc/nginx/ssl/cert.pem;
  ssl_certificate_key /etc/nginx/ssl/key.pem;
  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_ciphers HIGH:!aNULL:!MD5;
}
server { listen 80; return 301 https://$host$request_uri; }
```

En AWS, interponer un Application Load Balancer con terminación TLS antes de las instancias EC2.

---

### M-04 — El validador omite toda la validación si el payload contiene `id`

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `backend/src/application/validator.ts` líneas 81–84 |
| **CWE**     | CWE-20: Validación de entrada incorrecta |
| **CVSS v3** | 6.3 (AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:H/A:N) |

**Evidencia:**

```typescript
// validator.ts — líneas 81-84
export const validateCandidateData = (data: any) => {
    if (data.id) {
        return;   // ← return inmediato sin validar ningún campo
    }
    validateName(data.firstName);
    // ...
};
```

Cualquier petición `PUT /candidates/:id` que incluya un campo `id` en el body se acepta sin ninguna validación, permitiendo datos maliciosos (scripts XSS, fechas inválidas, strings excesivamente largos).

**Remediación:**

```typescript
export const validateCandidateData = (data: any, isUpdate = false) => {
    // Campos obligatorios sólo en creación
    if (!isUpdate) {
        validateName(data.firstName);
        validateName(data.lastName);
        validateEmail(data.email);
    }
    // Validar campos si están presentes (aplica en create y update)
    if (data.firstName !== undefined) validateName(data.firstName);
    if (data.lastName !== undefined) validateName(data.lastName);
    if (data.email !== undefined) validateEmail(data.email);
    if (data.phone !== undefined) validatePhone(data.phone);
    if (data.address !== undefined) validateAddress(data.address);
};
```

---

### M-05 — Nombre de fichero del cliente usado directamente en el almacenamiento

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `backend/src/application/services/fileUploadService.ts` línea 11 |
| **CWE**     | CWE-73: Control externo del nombre de fichero o ruta |
| **CVSS v3** | 6.5 (AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:H/A:N) |

**Evidencia:**

```typescript
// fileUploadService.ts — línea 11
filename: function (req, file, cb) {
    const uniqueSuffix = Date.now();
    cb(null, uniqueSuffix + '-' + file.originalname);  // ← originalname sin sanitizar
}
```

`file.originalname` puede contener `../` (path traversal), caracteres nulos o nombres extremadamente largos.

**Remediación:**

```typescript
import { v4 as uuidv4 } from 'uuid';
import path from 'path';

filename: function (req, file, cb) {
    const ext = path.extname(file.originalname).toLowerCase();
    const allowed = ['.pdf', '.docx'];
    if (!allowed.includes(ext)) return cb(new Error('Invalid extension'), '');
    cb(null, `${uuidv4()}${ext}`); // nombre completamente generado por el servidor
}
```

---

### M-06 — cAdvisor ejecutándose como contenedor privilegiado

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `docker-compose.yml` línea 124 |
| **CWE**     | CWE-250: Ejecución con privilegios innecesarios |
| **CVSS v3** | 6.7 (AV:L/AC:L/PR:H/UI:N/S:U/C:H/I:H/A:H) |

**Evidencia:**

```yaml
# docker-compose.yml — línea 124
cadvisor:
  privileged: true    # ← acceso completo al kernel del host
```

**Impacto:**
Un contenedor privilegiado tiene acceso a todos los namespaces del kernel del host. Si cAdvisor es comprometido, el atacante puede escapar del contenedor y comprometer el host.

**Remediación:**

```yaml
cadvisor:
  privileged: false
  cap_add:
    - SYS_PTRACE
  security_opt:
    - no-new-privileges:true
```

---

### M-07 — Docker socket montado en el contenedor Promtail

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `docker-compose.yml` línea 222 |
| **CWE**     | CWE-269: Gestión inadecuada de privilegios |
| **CVSS v3** | 6.7 (AV:L/AC:L/PR:H/UI:N/S:U/C:H/I:H/A:H) |

**Evidencia:**

```yaml
# docker-compose.yml — línea 222
promtail:
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro
```

**Impacto:**
Montar el socket Docker permite listar todos los contenedores, imágenes y metadatos. Un atacante que comprometa Promtail obtiene visibilidad total de la infraestructura Docker.

**Remediación:**
Leer logs directamente desde el sistema de ficheros sin el socket:

```yaml
promtail:
  volumes:
    - /var/lib/docker/containers:/var/lib/docker/containers:ro
    # eliminar la línea del docker.sock
```

---

### M-08 — Servicios systemd en EC2 corren como `root`

| Campo       | Detalle |
|-------------|---------|
| **Ficheros** | `tf/user_data_backend.sh` líneas 27–43, `tf/user_data_frontend.sh` líneas 23–38 |
| **CWE**     | CWE-250: Ejecución con privilegios innecesarios |
| **CVSS v3** | 6.3 (AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H) |

**Evidencia:**

```bash
# user_data_backend.sh — unidad systemd sin directiva User=
[Service]
Type=simple
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/node index.js
# ← NO hay User= ni Group=, el proceso corre como root
```

**Impacto:**
Si la aplicación Node.js es comprometida (RCE), el atacante obtiene privilegios `root` en el sistema operativo de la instancia EC2.

**Remediación:**

```bash
useradd --system --no-create-home --shell /usr/sbin/nologin nodeapp

cat > /etc/systemd/system/backend.service <<EOF
[Service]
User=nodeapp
Group=nodeapp
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/node index.js
EOF

chown -R nodeapp:nodeapp "$APP_DIR"
```

---

### M-09 — Sin paginación en endpoints de listado

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `backend/src/application/services/positionService.ts` líneas 12–33 y 69–77 |
| **CWE**     | CWE-770: Asignación de recursos sin límites |
| **CVSS v3** | 5.3 (AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:L) |

**Evidencia:**

```typescript
// positionService.ts — líneas 12-22
const applications = await prisma.application.findMany({
    where: { positionId },
    include: { candidate: true, interviews: true, interviewStep: true }
    // ← sin take/skip (sin paginación)
});
```

**Impacto:**
Con suficientes registros, una sola petición puede devolver megabytes de datos personales, consumir toda la memoria del proceso Node.js y degradar el servicio.

**Remediación:**

```typescript
export const getCandidatesByPositionService = async (
    positionId: number, page = 1, pageSize = 20
) => {
    const skip = (page - 1) * pageSize;
    const [applications, total] = await prisma.$transaction([
        prisma.application.findMany({
            where: { positionId }, skip, take: pageSize,
            include: { candidate: true, interviews: true, interviewStep: true }
        }),
        prisma.application.count({ where: { positionId } })
    ]);
    return { data: applications.map(/* ... */), total, page, pageSize };
};
```

---

## BAJO

---

### L-01 — `--web.enable-lifecycle` activa la API de administración de Prometheus

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `docker-compose.yml` línea 191 |
| **CWE**     | CWE-284: Control de acceso inadecuado |

**Evidencia:**

```yaml
command:
  - "--web.enable-lifecycle"   # habilita POST /-/reload y /-/quit
```

Combinado con el puerto 9090 expuesto públicamente (H-07), permite recargar la configuración de Prometheus o detenerlo sin autenticación.

**Remediación:** Eliminar `--web.enable-lifecycle` si no se usa, o asegurar el puerto antes de habilitarlo.

---

### L-02 — Loki con autenticación desactivada

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `monitoring/loki-config.yml` línea 5 |
| **CWE**     | CWE-306: Falta de autenticación |

**Evidencia:**

```yaml
# loki-config.yml — línea 5
auth_enabled: false
```

Cualquier servicio en la red Docker puede escribir y leer logs sin credenciales.

**Remediación:** `auth_enabled: true` y configurar tokens de acceso para Promtail.

---

### L-03 — Credenciales de test hardcodeadas en el workflow de CI

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `.github/workflows/ci.yml` líneas 77–79 |
| **CWE**     | CWE-798: Uso de credenciales hardcodeadas |

**Evidencia:**

```yaml
# ci.yml — líneas 77-79
POSTGRES_USER: ltiuser
POSTGRES_PASSWORD: ltipassword   # ← hardcodeado en el workflow
POSTGRES_DB: ltidb_test
```

**Remediación:** Usar `${{ secrets.TEST_DB_PASSWORD }}` o generar una contraseña aleatoria en cada ejecución:

```bash
TEST_DB_PASSWORD=$(openssl rand -hex 16)
```

---

### L-04 — Mensajes de error internos retornados directamente al cliente

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `backend/src/presentation/controllers/candidateController.ts` líneas 11–13 |
| **CWE**     | CWE-209: Generación de mensaje de error con información sensible |

**Evidencia:**

```typescript
// candidateController.ts — líneas 11-13
res.status(400).json({ message: 'Error adding candidate', error: error.message });
// error.message puede ser: "Unique constraint failed on field: email"
// revelando el esquema interno de la base de datos
```

**Remediación:**

```typescript
console.error('Candidate creation error:', error); // log interno
res.status(400).json({ message: 'Error processing request' }); // mensaje genérico al cliente
```

---

### L-05 — Fichero `app.env` escrito en disco EC2 sin permisos restrictivos

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `.github/workflows/ci.yml` líneas 261–267 |
| **CWE**     | CWE-732: Asignación incorrecta de permisos de fichero |

**Evidencia:**

```bash
# ci.yml — líneas 261-267
cat > ~/app.env << EOF
DB_PASSWORD=${DB_PASSWORD}
...
EOF
```

El fichero se crea con permisos por defecto del umask (normalmente `644`), legible por cualquier usuario del sistema.

**Remediación:**

```bash
touch ~/app.env
chmod 600 ~/app.env
cat > ~/app.env << EOF
...
EOF
```

---

### L-06 — Header `X-Powered-By: Express` expuesto

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `backend/src/index.ts` (ausencia de `helmet`) |
| **CWE**     | CWE-200: Exposición de información sensible |

Express añade por defecto el header `X-Powered-By: Express` en todas las respuestas, revelando el framework utilizado y facilitando la selección de exploits específicos.

**Remediación:**

```typescript
import helmet from 'helmet'; // npm install helmet
app.use(helmet()); // deshabilita X-Powered-By y añade cabeceras de seguridad
```

---

### L-07 — Header HSTS ausente en la configuración Nginx

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `frontend/nginx.conf` líneas 23–27 |
| **CWE**     | CWE-319: Transmisión en texto plano de información sensible |

Los headers de seguridad en nginx no incluyen `Strict-Transport-Security`. Sin HSTS un navegador no fuerza HTTPS aunque esté disponible.

**Remediación** (aplicar junto a M-03):

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
```

---

### L-08 — Stress test de Locust apunta directamente a la instancia EC2 de producción

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `.github/workflows/ci.yml` líneas 322–324 |
| **CWE**     | CWE-400: Consumo de recursos sin control |

**Evidencia:**

```yaml
# ci.yml — líneas 322-324
--host "http://${{ secrets.EC2_INSTANCE }}:8080"
--users 50
--run-time 60s
```

El test de carga se ejecuta contra el entorno de producción inmediatamente después del despliegue.

**Remediación:** Desplegar a un entorno de staging separado y ejecutar los tests de carga allí. Si se mantiene en producción, usar ventanas de mantenimiento y un ALB para desviar tráfico durante las pruebas.

---

## INFORMACIONAL

---

### I-01 — Sin SAST en el pipeline de CI

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `.github/workflows/ci.yml` |
| **CWE**     | CWE-1006: Proceso de desarrollo de software débil |

El pipeline incluye `npm audit` para dependencias pero no hay análisis estático de seguridad del código fuente. Herramientas como Semgrep, CodeQL o SonarQube detectarían automáticamente muchos de los hallazgos de este informe.

**Remediación:** Añadir CodeQL (gratuito para GitHub):

```yaml
- name: Initialize CodeQL
  uses: github/codeql-action/init@v3
  with:
    languages: javascript-typescript

- name: Perform CodeQL Analysis
  uses: github/codeql-action/analyze@v3
```

---

### I-02 — Sin escaneo de imágenes Docker en CI

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `.github/workflows/ci.yml` (job `docker-build-push`) |

Las imágenes Docker se publican en ECR sin ser escaneadas en busca de CVEs en el sistema operativo base (Alpine) ni en las dependencias npm.

**Remediación:** Añadir Trivy después del build:

```yaml
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ secrets.ECR_REGISTRY }}/lti-backend:${{ github.sha }}
    format: sarif
    exit-code: '1'
    severity: 'CRITICAL,HIGH'
```

---

### I-03 — `multer ^1.4.5-lts.1` con vulnerabilidades conocidas

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `backend/package.json` línea 25 |
| **CWE**     | CWE-1395: Dependencia con vulnerabilidades conocidas |

Multer 1.x tiene vulnerabilidades conocidas de ReDoS y está en modo de mantenimiento a largo plazo sin recibir parches de seguridad activos.

**Remediación:** Monitorizar `npm audit` para nuevas CVEs en multer. Evaluar migración a Multer 2.x o usar `busboy` directamente.

---

### I-04 — Locust UI expuesto sin autenticación en docker-compose

| Campo       | Detalle |
|-------------|---------|
| **Fichero** | `docker-compose.yml` línea 106 |

```yaml
locust:
  ports:
    - "8089:8089"   # UI de control de Locust, sin auth
```

La interfaz web de Locust (que permite iniciar/detener tests de carga) está expuesta sin autenticación. Mitigado parcialmente por el perfil `load-test`.

**Remediación:** Restringir el puerto a `127.0.0.1:8089:8089`.

---

## Plan de Remediación Priorizado

| Prioridad | ID   | Acción                                                              | Esfuerzo |
|-----------|------|---------------------------------------------------------------------|----------|
| P0        | C-01 | Rotar credenciales de BD comprometidas + purgar historial git       | 1 h      |
| P0        | C-02 | Corregir `.gitignore` y ejecutar `git rm --cached` de `.env`        | 15 min   |
| P0        | C-03 | Implementar autenticación JWT en todos los endpoints                | 2 días   |
| P1        | H-01 | Validar tipo de fichero por magic bytes, no por cabecera MIME       | 2 h      |
| P1        | H-02 | No retornar ruta absoluta en respuesta de `/upload`                 | 30 min   |
| P1        | H-03 | Restringir SSH a IP de administración o usar AWS SSM Session Mgr    | 1 h      |
| P1        | H-04 | Restringir puerto 8080 al SG del frontend/ALB                       | 1 h      |
| P1        | H-05 | Usar IAM Instance Profile para ECR; eliminar credenciales inline    | 2 h      |
| P1        | H-06 | Añadir `express-rate-limit` a todos los endpoints                   | 2 h      |
| P1        | H-07 | Restringir Prometheus a `127.0.0.1:9090`                            | 15 min   |
| P2        | M-03 | Configurar TLS en nginx + ALB en AWS                                | 4 h      |
| P2        | M-04 | Corregir validador para no omitir validación en updates             | 1 h      |
| P2        | M-05 | Usar UUID para nombres de fichero, ignorar `originalname`           | 30 min   |
| P2        | M-08 | Crear usuario dedicado sin privilegios para los servicios systemd   | 1 h      |
| P3        | M-01 | Forzar contraseña de Grafana con `:?` en docker-compose             | 5 min    |
| P3        | L-01 | Eliminar `--web.enable-lifecycle` de Prometheus                     | 5 min    |
| P3        | L-06 | Añadir `helmet` al servidor Express                                 | 15 min   |
| P4        | I-01 | Integrar CodeQL en el pipeline de CI                                | 2 h      |
| P4        | I-02 | Integrar Trivy (escaneo de imágenes Docker) en el pipeline de CI    | 1 h      |

---

*Informe generado mediante análisis estático manual de todos los ficheros del repositorio.*
*Para reauditoría tras aplicar las remediaciones, contactar con el equipo de seguridad.*
