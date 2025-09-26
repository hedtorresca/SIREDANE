from pydantic import BaseModel, validator
from typing import Optional
import datetime

# PENMDIENTE - ACTUALIZACIÓN DE DATOS EN LA BASE DE DATOS CUANDO CAMBIAN. AGREGAR PARAMETRO DE ES_FUENTE_CONFIABLE QUE PERMITA SABER A LA API SI REQUIERE O NO
# ACTUALIZARLA

# Schema para el servicio /generar-id-personas
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

## PENDIENTE - Validaciones de fechas, defuncion no puede ser anterior a la fecha de nacimiento
    @validator('fecha_nacimiento', 'fecha_defuncion', pre=True, always=True)
    def parse_date(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            return datetime.datetime.strptime(v, '%Y-%m-%d').date()
        return v

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

# Schema de respuesta común para todos los servicios
class IDResponse(BaseModel):
    id_estadistico: str
    mensaje: str
    tipo_entidad: str
    consecutivo: str
