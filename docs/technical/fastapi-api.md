# API FastAPI - SIRE

## Visión General

La API FastAPI de SIRE proporciona servicios REST para la generación de IDs estadísticos únicos, que son fundamentales para la pseudonimización de datos sensibles. La API está diseñada para ser rápida, segura y fácil de usar.

## Características Principales

- ✅ **API REST moderna** con FastAPI
- ✅ **Validación automática** con Pydantic
- ✅ **Documentación interactiva** (Swagger/OpenAPI)
- ✅ **Tipado estático** con Python
- ✅ **Respuesta rápida** y eficiente
- ✅ **Manejo de errores** robusto

## Endpoints Disponibles

### 1. Generar ID para Personas

**Endpoint**: `POST /generar-id-personas`

**Descripción**: Genera un ID estadístico único para una persona. Si la persona ya existe, retorna el ID existente.

**Request Body**:
```json
{
  "tipo_documento": "CC",
  "numero_documento": "12345678",
  "primer_nombre": "Juan",
  "segundo_nombre": "Carlos",
  "primer_apellido": "Pérez",
  "segundo_apellido": "García",
  "fecha_nacimiento": "1990-05-15",
  "sexo_an": "M",
  "codigo_municipio_nacimiento": "05001",
  "codigo_pais_nacimiento": "170",
  "fecha_defuncion": null
}
```

**Response**:
```json
{
  "id_estadistico": "0100000001",
  "mensaje": "Nueva persona registrada exitosamente",
  "tipo_entidad": "01",
  "consecutivo": "00000001"
}
```

### 2. Generar ID para Empresas

**Endpoint**: `POST /generar-id-empresas`

**Descripción**: Genera un ID estadístico único para una empresa. Si la empresa ya existe, retorna el ID existente.

**Request Body**:
```json
{
  "razon_social": "EMPRESA EJEMPLO S.A.S.",
  "tipo_documento": "NIT",
  "numero_documento": "900123456",
  "digito_verificacion": "7",
  "codigo_camara": "11001",
  "camara_comercio": "BOGOTÁ",
  "matricula": "12345",
  "fecha_matricula": "2020-01-15",
  "fecha_renovacion": "2024-01-15",
  "ultimo_ano_renovado": 2024,
  "fecha_vigencia": "2025-01-15",
  "fecha_cancelacion": null,
  "codigo_tipo_sociedad": "01",
  "tipo_sociedad": "SOCIEDAD ANÓNIMA SIMPLIFICADA",
  "codigo_organizacion_juridica": "01",
  "organizacion_juridica": "SOCIEDAD ANÓNIMA SIMPLIFICADA",
  "codigo_estado_matricula": "01",
  "estado_matricula": "ACTIVA",
  "representante_legal": "Juan Pérez",
  "num_identificacion_representante_legal": "12345678",
  "clase_identificacion_rl": "CC",
  "fecha_actualizacion": "2024-01-15"
}
```

**Response**:
```json
{
  "id_estadistico": "0200000001",
  "mensaje": "Nueva empresa registrada exitosamente",
  "tipo_entidad": "02",
  "consecutivo": "00000001"
}
```

### 3. Generar ID para Empresas con CC

**Endpoint**: `POST /generar-id-empresas-cc`

**Descripción**: Genera un ID estadístico para una empresa cuyo tipo de documento es CC (Cédula de Ciudadanía). Este endpoint maneja el caso especial donde una empresa es una persona natural.

**Request Body**:
```json
{
  "razon_social": "JUAN PÉREZ GARCÍA",
  "tipo_documento": "CC",
  "numero_documento": "12345678",
  "digito_verificacion": null,
  "codigo_camara": "11001",
  "camara_comercio": "BOGOTÁ",
  "matricula": "67890",
  "fecha_matricula": "2020-01-15",
  "fecha_renovacion": "2024-01-15",
  "ultimo_ano_renovado": 2024,
  "fecha_vigencia": "2025-01-15",
  "fecha_cancelacion": null,
  "codigo_tipo_sociedad": "01",
  "tipo_sociedad": "PERSONA NATURAL",
  "codigo_organizacion_juridica": "01",
  "organizacion_juridica": "PERSONA NATURAL",
  "codigo_estado_matricula": "01",
  "estado_matricula": "ACTIVA",
  "representante_legal": "Juan Pérez García",
  "num_identificacion_representante_legal": "12345678",
  "clase_identificacion_rl": "CC",
  "fecha_actualizacion": "2024-01-15",
  "primer_nombre": "Juan",
  "segundo_nombre": "Carlos",
  "primer_apellido": "Pérez",
  "segundo_apellido": "García",
  "fecha_nacimiento": "1990-05-15",
  "sexo_an": "M",
  "codigo_municipio_nacimiento": "05001",
  "codigo_pais_nacimiento": "170",
  "fecha_defuncion": null
}
```

**Response**:
```json
{
  "id_estadistico": "0100000001",
  "mensaje": "Empresa registrada usando ID de persona existente",
  "tipo_entidad": "01",
  "consecutivo": "00000001"
}
```

## Esquemas de Datos (Pydantic)

### PersonaRequest
```python
class PersonaRequest(BaseModel):
    tipo_documento: str
    numero_documento: str
    primer_nombre: str
    segundo_nombre: str
    primer_apellido: str
    segundo_apellido: str
    fecha_nacimiento: datetime.date
    sexo_an: str
    codigo_municipio_nacimiento: str
    codigo_pais_nacimiento: str
    fecha_defuncion: Optional[datetime.date] = None
```

### EmpresaRequest
```python
class EmpresaRequest(BaseModel):
    razon_social: str
    tipo_documento: str
    numero_documento: str
    digito_verificacion: Optional[str] = None
    codigo_camara: str
    camara_comercio: str
    matricula: str
    fecha_matricula: datetime.date
    fecha_renovacion: datetime.date
    ultimo_ano_renovado: int
    fecha_vigencia: datetime.date
    fecha_cancelacion: Optional[datetime.date] = None
    codigo_tipo_sociedad: str
    tipo_sociedad: str
    codigo_organizacion_juridica: str
    organizacion_juridica: str
    codigo_estado_matricula: str
    estado_matricula: str
    representante_legal: str
    num_identificacion_representante_legal: str
    clase_identificacion_rl: str
    fecha_actualizacion: Optional[datetime.date] = None
```

### EmpresaCCRequest
```python
class EmpresaCCRequest(BaseModel):
    # Datos de la empresa
    razon_social: str
    tipo_documento: str
    numero_documento: str
    digito_verificacion: Optional[str] = None
    codigo_camara: str
    camara_comercio: str
    matricula: str
    fecha_matricula: datetime.date
    fecha_renovacion: datetime.date
    ultimo_ano_renovado: int
    fecha_vigencia: datetime.date
    fecha_cancelacion: Optional[datetime.date] = None
    codigo_tipo_sociedad: str
    tipo_sociedad: str
    codigo_organizacion_juridica: str
    organizacion_juridica: str
    codigo_estado_matricula: str
    estado_matricula: str
    representante_legal: str
    num_identificacion_representante_legal: str
    clase_identificacion_rl: str
    fecha_actualizacion: Optional[datetime.date] = None
    
    # Datos de la persona (cuando tipo_documento es CC)
    primer_nombre: str
    segundo_nombre: str
    primer_apellido: str
    segundo_apellido: str
    fecha_nacimiento: datetime.date
    sexo_an: str
    codigo_municipio_nacimiento: str
    codigo_pais_nacimiento: str
    fecha_defuncion: Optional[datetime.date] = None
```

### IDResponse
```python
class IDResponse(BaseModel):
    id_estadistico: str
    mensaje: str
    tipo_entidad: str
    consecutivo: str
```

## Formato de IDs Estadísticos

### Personas
- **Formato**: `01` + consecutivo hexadecimal (8 dígitos)
- **Ejemplo**: `0100000001`, `0100000002`, etc.
- **Tipo de entidad**: `01`

### Empresas
- **Formato**: `02` + consecutivo hexadecimal (8 dígitos)
- **Ejemplo**: `0200000001`, `0200000002`, etc.
- **Tipo de entidad**: `02`

### Empresas con CC
- **Formato**: Usa el ID de la persona asociada (formato `01`)
- **Ejemplo**: `0100000001` (mismo ID que la persona)
- **Tipo de entidad**: `01`

## Validaciones

### Validación de Fechas
```python
@validator('fecha_nacimiento', 'fecha_defuncion', pre=True, always=True)
def parse_date(cls, v):
    if v is None:
        return v
    if isinstance(v, str):
        return datetime.datetime.strptime(v, '%Y-%m-%d').date()
    return v
```

### Validación de Tipo de Documento
```python
# Para empresas CC, validar que el tipo sea CC
if request.tipo_documento.upper() != "CC":
    raise HTTPException(
        status_code=400, 
        detail="Este servicio solo es válido para empresas con tipo de documento 'CC'"
    )
```

## Manejo de Errores

### Códigos de Estado HTTP
- **200 OK**: Operación exitosa
- **400 Bad Request**: Datos de entrada inválidos
- **500 Internal Server Error**: Error interno del servidor

### Respuestas de Error
```json
{
  "detail": "Error al procesar la solicitud: [descripción del error]"
}
```

### Ejemplos de Errores Comunes
```json
// Tipo de documento inválido para empresas CC
{
  "detail": "Este servicio solo es válido para empresas con tipo de documento 'CC'"
}

// Error de conexión a base de datos
{
  "detail": "Error al procesar la solicitud: connection timeout"
}
```

## Configuración

### Variables de Entorno
```bash
# Selector de backend
DATABASE_TYPE=postgresql   # o oracle
ENVIRONMENT=dev            # o prod

# Base de datos PostgreSQL (dev)
DEV_POSTGRES_JDBC_URL=jdbc:postgresql://sire-postgres-dw:5432/sire_dw
DEV_POSTGRES_JDBC_USER=sire_user
DEV_POSTGRES_JDBC_PASSWORD=sire_password
DEV_POSTGRES_CONNECTION_STRING=postgresql://sire_user:sire_password@sire-postgres-dw:5432/sire_dw

# Base de datos Oracle (prod o dev-oracle)
PROD_ORACLE_JDBC_URL=jdbc:oracle:thin:@oracle-server:1521/XEPDB1
PROD_ORACLE_JDBC_USER=SIRE_STG
PROD_ORACLE_JDBC_PASSWORD=sire_password
PROD_ORACLE_CONNECTION_STRING=oracle://SIRE_STG:sire_password@oracle-server:1521/XEPDB1

# API
API_HOST=0.0.0.0
API_PORT=8001
```

### Docker
```yaml
# Desarrollo (PostgreSQL)
services:
  sire-fastapi:
    build:
      context: .
      dockerfile: Dockerfile.fastapi
    environment:
      - ENVIRONMENT=dev
      - DATABASE_TYPE=postgresql
      - DEV_POSTGRES_CONNECTION_STRING=${DEV_POSTGRES_CONNECTION_STRING}
    ports:
      - "8001:8001"

# Producción (Oracle externo)
services:
  sire-fastapi:
    build:
      context: .
      dockerfile: Dockerfile.fastapi.oracle
    environment:
      - ENVIRONMENT=prod
      - DATABASE_TYPE=oracle
      - PROD_ORACLE_CONNECTION_STRING=${PROD_ORACLE_CONNECTION_STRING}
    ports:
      - "8001:8001"
```

## Entrypoints por variante
- PostgreSQL: `FastAPI/Main.py` (usa `FastAPI/utils/utils.py`)
- Oracle: `FastAPI/Main_oracle.py` (usa `FastAPI/utils/utils_oracle.py`)

## Documentación Interactiva

### Swagger UI
- **URL**: http://localhost:8001/docs
- **Descripción**: Interfaz interactiva para probar la API

### ReDoc
- **URL**: http://localhost:8001/redoc
- **Descripción**: Documentación alternativa con mejor formato

### OpenAPI Schema
- **URL**: http://localhost:8001/openapi.json
- **Descripción**: Esquema OpenAPI en formato JSON

## Ejemplos de Uso

### Python (requests)
```python
import requests

# Generar ID para persona
url = "http://localhost:8001/generar-id-personas"
data = {
    "tipo_documento": "CC",
    "numero_documento": "12345678",
    "primer_nombre": "Juan",
    "segundo_nombre": "Carlos",
    "primer_apellido": "Pérez",
    "segundo_apellido": "García",
    "fecha_nacimiento": "1990-05-15",
    "sexo_an": "M",
    "codigo_municipio_nacimiento": "05001",
    "codigo_pais_nacimiento": "170"
}

response = requests.post(url, json=data)
result = response.json()
print(f"ID Estadístico: {result['id_estadistico']}")
```

### cURL
```bash
# Generar ID para empresa
curl -X POST "http://localhost:8001/generar-id-empresas" \
  -H "Content-Type: application/json" \
  -d '{
    "razon_social": "EMPRESA EJEMPLO S.A.S.",
    "tipo_documento": "NIT",
    "numero_documento": "900123456",
    "digito_verificacion": "7",
    "codigo_camara": "11001",
    "camara_comercio": "BOGOTÁ",
    "matricula": "12345",
    "fecha_matricula": "2020-01-15",
    "fecha_renovacion": "2024-01-15",
    "ultimo_ano_renovado": 2024,
    "fecha_vigencia": "2025-01-15",
    "fecha_cancelacion": null,
    "codigo_tipo_sociedad": "01",
    "tipo_sociedad": "SOCIEDAD ANÓNIMA SIMPLIFICADA",
    "codigo_organizacion_juridica": "01",
    "organizacion_juridica": "SOCIEDAD ANÓNIMA SIMPLIFICADA",
    "codigo_estado_matricula": "01",
    "estado_matricula": "ACTIVA",
    "representante_legal": "Juan Pérez",
    "num_identificacion_representante_legal": "12345678",
    "clase_identificacion_rl": "CC",
    "fecha_actualizacion": "2024-01-15"
  }'
```

### JavaScript (fetch)
```javascript
// Generar ID para empresa CC
const url = 'http://localhost:8001/generar-id-empresas-cc';
const data = {
  razon_social: 'JUAN PÉREZ GARCÍA',
  tipo_documento: 'CC',
  numero_documento: '12345678',
  // ... otros campos
};

fetch(url, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(data)
})
.then(response => response.json())
.then(result => {
  console.log('ID Estadístico:', result.id_estadistico);
});
```

## Monitoreo y Logs

### Logs de Aplicación
```python
# Los logs se escriben en la consola del contenedor
# Para ver logs en tiempo real:
docker logs -f sire-fastapi
```

### Métricas de Performance
- Tiempo de respuesta promedio
- Número de requests por segundo
- Tasa de errores
- Uso de memoria y CPU

### Health Check
```python
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}
```

## Seguridad

### Validación de Entrada
- Validación automática con Pydantic
- Sanitización de datos de entrada
- Validación de tipos de datos

### Control de Acceso
- Autenticación básica (configurable)
- Rate limiting (configurable)
- CORS configurado

### Logs de Seguridad
- Registro de todas las operaciones
- Logs de errores de validación
- Monitoreo de accesos

## Troubleshooting

### Problemas Comunes

#### Error de Conexión a Base de Datos
```
Error: connection timeout
```
**Solución**: Verificar que la base de datos esté ejecutándose y accesible.

#### Error de Validación
```
Error: validation error for PersonaRequest
```
**Solución**: Verificar que todos los campos requeridos estén presentes y en el formato correcto.

#### Error de Puerto en Uso
```
Error: Address already in use
```
**Solución**: Cambiar el puerto en la configuración o detener el proceso que lo está usando.

### Logs de Debug
```bash
# Habilitar logs detallados
export LOG_LEVEL=DEBUG
docker-compose up fastapi
```
