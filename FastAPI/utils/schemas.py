from pydantic import BaseModel, validator, Field
from typing import Optional, Union, Literal
import datetime

# PENMDIENTE - ACTUALIZACIÓN DE DATOS EN LA BASE DE DATOS CUANDO CAMBIAN. AGREGAR PARAMETRO DE ES_FUENTE_CONFIABLE QUE PERMITA SABER A LA API SI REQUIERE O NO
# ACTUALIZARLA

# Schema para el servicio /generar-id-personas
class PersonaRequest(BaseModel):
    tipo_documento: str = Field(min_length=1, example="CC", description="Tipo de documento: CC, TI, CE, etc.")
    numero_documento: str = Field(min_length=1, example="1234567890")
    primer_nombre: str = Field(min_length=1, example="JUAN")
    segundo_nombre: Optional[str] = ""
    primer_apellido: str = Field(min_length=1, example="PEREZ")
    segundo_apellido: Optional[str] = ""
    fecha_nacimiento: datetime.date = Field(example="1990-01-15")
    sexo_an: str = Field(min_length=1, example="M", description="Sexo: M o F")
    codigo_municipio_nacimiento: str = Field(pattern=r'^\d+$', example="11001", description="DIVIPOLA de 5 dígitos")
    codigo_pais_nacimiento: str = Field(pattern=r'^\d+$', example="170", description="Código M49 de 3 dígitos")
    fecha_defuncion: Optional[datetime.date] = None

    class Config:
        schema_extra = {
            "example": {
                "tipo_documento": "CC",
                "numero_documento": "1234567890",
                "primer_nombre": "JUAN",
                "segundo_nombre": "",
                "primer_apellido": "PEREZ",
                "segundo_apellido": "",
                "fecha_nacimiento": "1990-01-15",
                "sexo_an": "M",
                "codigo_municipio_nacimiento": "11001",
                "codigo_pais_nacimiento": "170",
                "fecha_defuncion": None
            }
        }

## PENDIENTE - Validaciones de fechas, defuncion no puede ser anterior a la fecha de nacimiento
    @validator('fecha_nacimiento', 'fecha_defuncion', pre=True, always=True)
    def parse_date(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            return datetime.datetime.strptime(v, '%Y-%m-%d').date()
        return v

    @validator('segundo_nombre', 'segundo_apellido', pre=True, always=True)
    def optional_strings_to_empty(cls, v):
        # Normaliza None a cadena vacía para campos opcionales
        return "" if v is None else v

    @validator('tipo_documento', 'numero_documento', 'primer_nombre', 'primer_apellido', pre=True)
    def must_not_be_placeholder(cls, v):
        # Rechazar valores de autollenado comunes
        placeholders = {"string", "autodiligenciado", "auto", "null", "none"}
        if isinstance(v, str) and v.strip().lower() in placeholders:
            raise ValueError('valor inválido')
        return v

    @validator('sexo_an')
    def validate_sexo(cls, v):
        allowed = {"M", "F"}
        if v.upper() not in allowed:
            raise ValueError('sexo_an debe ser M o F')
        return v.upper()

    @validator('fecha_defuncion')
    def validate_dates_order(cls, v, values):
        # Si hay fecha de defunción, debe ser posterior o igual a fecha de nacimiento
        if v is not None:
            fnac = values.get('fecha_nacimiento')
            if fnac is not None and v < fnac:
                raise ValueError('fecha_defuncion no puede ser anterior a fecha_nacimiento')
        return v

    @validator('fecha_nacimiento')
    def validate_birth_not_future(cls, v):
        if v is not None:
            today = datetime.date.today()
            if v > today:
                raise ValueError('fecha_nacimiento no puede ser futura')
        return v

    @validator('codigo_municipio_nacimiento')
    def validate_codigo_municipio(cls, v):
        s = v.strip()
        if not s.isdigit():
            raise ValueError('codigo_municipio_nacimiento debe ser numérico')
        if len(s) != 5:
            raise ValueError('codigo_municipio_nacimiento debe tener exactamente 5 dígitos (DIVIPOLA)')
        return s

    @validator('codigo_pais_nacimiento')
    def validate_codigo_pais(cls, v):
        s = v.strip()
        if not s.isdigit():
            raise ValueError('codigo_pais_nacimiento debe ser numérico')
        if len(s) != 3:
            raise ValueError('codigo_pais_nacimiento debe tener exactamente 3 dígitos (M49)')
        return s

# Schema para el servicio /generar-id-empresas
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

    @validator('fecha_matricula', 'fecha_renovacion', 'fecha_vigencia', 'fecha_cancelacion', 'fecha_actualizacion', pre=True, always=True)
    def parse_date(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            return datetime.datetime.strptime(v, '%Y-%m-%d').date()
        return v

# Schema para el servicio /generar-id-empresas-cc
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

    @validator('fecha_matricula', 'fecha_renovacion', 'fecha_vigencia', 'fecha_cancelacion', 'fecha_actualizacion', 'fecha_nacimiento', 'fecha_defuncion', pre=True, always=True)
    def parse_date(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            return datetime.datetime.strptime(v, '%Y-%m-%d').date()
        return v

    @validator('fecha_defuncion')
    def validate_dates_order(cls, v, values):
        # Si hay fecha de defunción, debe ser posterior o igual a fecha de nacimiento
        if v is not None:
            fnac = values.get('fecha_nacimiento')
            if fnac is not None and v < fnac:
                raise ValueError('fecha_defuncion no puede ser anterior a fecha_nacimiento')
        return v

    @validator('fecha_nacimiento')
    def validate_birth_not_future(cls, v):
        if v is not None:
            today = datetime.date.today()
            if v > today:
                raise ValueError('fecha_nacimiento no puede ser futura')
        return v

# Schema de respuesta común para todos los servicios
class IDResponse(BaseModel):
    id_estadistico: str
    mensaje: str
    tipo_entidad: str
    consecutivo: str
    coincidencia: Optional["CoincidenciaResponse"] = None


class EvidenciaDocExacto(BaseModel):
    tipo_documento: str
    numero_documento: str


class EvidenciaDoc1DigNombre(BaseModel):
    doc_diff_1dig: bool
    sim_nombre: float = Field(ge=0.0, le=1.0)


class CoincidenciaResponse(BaseModel):
    criterio: Literal["C1_DOC_EXACTO", "C2_DOC_1DIG_NOMBRE_SIM"]
    puntaje: float = Field(ge=0.0, le=1.0)
    evidencia: Union[EvidenciaDocExacto, EvidenciaDoc1DigNombre]

    @validator("puntaje")
    def validar_puntaje_por_criterio(cls, puntaje: float, values):
        criterio = values.get("criterio")
        if criterio == "C1_DOC_EXACTO" and puntaje != 1.0:
            raise ValueError("El criterio C1_DOC_EXACTO debe tener puntaje 1.0")
        if criterio == "C2_DOC_1DIG_NOMBRE_SIM" and not (0.90 <= puntaje <= 1.0):
            raise ValueError("El criterio C2_DOC_1DIG_NOMBRE_SIM debe tener puntaje entre 0.90 y 1.0")
        return puntaje


IDResponse.update_forward_refs()
