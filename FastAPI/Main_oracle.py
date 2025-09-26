from fastapi import FastAPI, HTTPException
from FastAPI.utils.schemas import PersonaRequest, EmpresaRequest, EmpresaCCRequest, IDResponse
from FastAPI.utils.utils_oracle import (
    buscar_persona_existente, buscar_empresa_existente,
    guardar_nueva_persona, guardar_nueva_empresa, guardar_empresa_con_id_persona
)

app = FastAPI(
    title="SIRE - Sistema de Identificación Estadística (Oracle)",
    description="API para generar IDs estadísticos para pseudonimización de datos - Versión Oracle",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {"message": "SIRE - Sistema de Identificación Estadística (Oracle)", "database": "Oracle"}

@app.post("/generar-id-personas", response_model=IDResponse)
def generar_id_personas(request: PersonaRequest):
    """
    Genera un ID estadístico para una persona.
    
    Si la persona ya existe, retorna el ID existente.
    Si no existe, genera un nuevo ID con formato: 01 + consecutivo hexadecimal.
    """
    try:
        # Buscar si la persona ya existe
        id_existente = buscar_persona_existente(request.tipo_documento, request.numero_documento)
        
        if id_existente:
            return IDResponse(
                id_estadistico=id_existente,
                mensaje="Persona ya existe en el sistema",
                tipo_entidad="01",
                consecutivo=id_existente[2:]  # Remover el prefijo "01"
            )
        
        # Si no existe, crear nueva persona
        data = request.dict()
        id_estadistico = guardar_nueva_persona(data)
        
        return IDResponse(
            id_estadistico=id_estadistico,
            mensaje="Nueva persona registrada exitosamente",
            tipo_entidad="01",
            consecutivo=id_estadistico[2:]  # Remover el prefijo "01"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la solicitud: {str(e)}")

@app.post("/generar-id-empresas", response_model=IDResponse)
def generar_id_empresas(request: EmpresaRequest):
    """
    Genera un ID estadístico para una empresa.
    
    Si la empresa ya existe, retorna el ID existente.
    Si no existe, genera un nuevo ID con formato: 02 + consecutivo hexadecimal.
    """
    try:
        # Buscar si la empresa ya existe
        id_existente = buscar_empresa_existente(request.tipo_documento, request.numero_documento)
        
        if id_existente:
            return IDResponse(
                id_estadistico=id_existente,
                mensaje="Empresa ya existe en el sistema",
                tipo_entidad="02",
                consecutivo=id_existente[2:]  # Remover el prefijo "02"
            )
        
        # Si no existe, crear nueva empresa
        data = request.dict()
        id_estadistico = guardar_nueva_empresa(data)
        
        return IDResponse(
            id_estadistico=id_estadistico,
            mensaje="Nueva empresa registrada exitosamente",
            tipo_entidad="02",
            consecutivo=id_estadistico[2:]  # Remover el prefijo "02"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la solicitud: {str(e)}")

@app.post("/generar-id-empresas-cc", response_model=IDResponse)
def generar_id_empresas_cc(request: EmpresaCCRequest):
    """
    Genera un ID estadístico para una empresa con cédula de ciudadanía.
    
    Si la persona ya existe, usa su ID existente.
    Si no existe, genera un nuevo ID de persona y lo usa para la empresa.
    """
    try:
        # Verificar si ya existe una empresa con estos datos
        id_empresa_existente = buscar_empresa_existente(request.tipo_documento, request.numero_documento)
        
        if id_empresa_existente:
            return IDResponse(
                id_estadistico=id_empresa_existente,
                mensaje="Empresa ya existe en el sistema",
                tipo_entidad="01",  # Empresas CC usan ID de persona
                consecutivo=id_empresa_existente[2:]
            )
        
        # Buscar si la persona ya existe
        id_persona_existente = buscar_persona_existente(request.tipo_documento, request.numero_documento)
        
        if id_persona_existente:
            # La persona existe, crear la empresa con el mismo ID
            data_empresa = {
                "razon_social": request.razon_social,
                "tipo_documento": request.tipo_documento,
                "numero_documento": request.numero_documento,
                "digito_verificacion": request.digito_verificacion,
                "codigo_camara": request.codigo_camara,
                "camara_comercio": request.camara_comercio,
                "matricula": request.matricula,
                "fecha_matricula": request.fecha_matricula,
                "fecha_renovacion": request.fecha_renovacion,
                "ultimo_ano_renovado": request.ultimo_ano_renovado,
                "fecha_vigencia": request.fecha_vigencia,
                "fecha_cancelacion": request.fecha_cancelacion,
                "codigo_tipo_sociedad": request.codigo_tipo_sociedad,
                "tipo_sociedad": request.tipo_sociedad,
                "codigo_organizacion_juridica": request.codigo_organizacion_juridica,
                "organizacion_juridica": request.organizacion_juridica,
                "codigo_estado_matricula": request.codigo_estado_matricula,
                "estado_matricula": request.estado_matricula,
                "representante_legal": request.representante_legal,
                "num_identificacion_representante_legal": request.num_identificacion_representante_legal,
                "clase_identificacion_rl": request.clase_identificacion_rl,
                "fecha_actualizacion": request.fecha_actualizacion
            }
            
            guardar_empresa_con_id_persona(data_empresa, id_persona_existente)
            
            return IDResponse(
                id_estadistico=id_persona_existente,
                mensaje="Empresa registrada con ID de persona existente",
                tipo_entidad="01",
                consecutivo=id_persona_existente[2:]
            )
        else:
            # La persona no existe, crear nueva persona primero
            data_persona = {
                "tipo_documento": request.tipo_documento,
                "numero_documento": request.numero_documento,
                "primer_nombre": request.primer_nombre,
                "segundo_nombre": request.segundo_nombre,
                "primer_apellido": request.primer_apellido,
                "segundo_apellido": request.segundo_apellido,
                "fecha_nacimiento": request.fecha_nacimiento,
                "sexo_an": request.sexo_an,
                "codigo_municipio_nacimiento": request.codigo_municipio_nacimiento,
                "codigo_pais_nacimiento": request.codigo_pais_nacimiento
            }

            
            id_estadistico = guardar_nueva_persona(data_persona)
            
            # Ahora crear la empresa con el mismo ID
            data_empresa = {
                "razon_social": request.razon_social,
                "tipo_documento": request.tipo_documento,
                "numero_documento": request.numero_documento,
                "digito_verificacion": request.digito_verificacion,
                "codigo_camara": request.codigo_camara,
                "camara_comercio": request.camara_comercio,
                "matricula": request.matricula,
                "fecha_matricula": request.fecha_matricula,
                "fecha_renovacion": request.fecha_renovacion,
                "ultimo_ano_renovado": request.ultimo_ano_renovado,
                "fecha_vigencia": request.fecha_vigencia,
                "fecha_cancelacion": request.fecha_cancelacion,
                "codigo_tipo_sociedad": request.codigo_tipo_sociedad,
                "tipo_sociedad": request.tipo_sociedad,
                "codigo_organizacion_juridica": request.codigo_organizacion_juridica,
                "organizacion_juridica": request.organizacion_juridica,
                "codigo_estado_matricula": request.codigo_estado_matricula,
                "estado_matricula": request.estado_matricula,
                "representante_legal": request.representante_legal,
                "num_identificacion_representante_legal": request.num_identificacion_representante_legal,
                "clase_identificacion_rl": request.clase_identificacion_rl,
                "fecha_actualizacion": request.fecha_actualizacion
            }
            
            guardar_empresa_con_id_persona(data_empresa, id_estadistico)
            
            return IDResponse(
                id_estadistico=id_estadistico,
                mensaje="Nueva persona y empresa registradas exitosamente",
                tipo_entidad="01",
                consecutivo=id_estadistico[2:]
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la solicitud: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5003)
