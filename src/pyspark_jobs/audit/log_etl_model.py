from datetime import datetime

class LogEtlModel:
    def __init__(self, job_uuid: str, start_time:datetime, end_time:datetime, estado: str,
                 registros_cargados: int, tabla_destino: str, mensaje_error: str = None,
                 nombre_etl: str = None, descripcion_etl: str = None,
                 tiempo_ejecucion_segundos: int = None, nombre_archivo: str = None, hash_archivo: str = None):

        self.job_uuid = job_uuid
        self.start_time = start_time
        self.end_time = end_time
        self.estado = estado
        self.registros_cargados = registros_cargados
        self.tabla_destino = tabla_destino
        self.mensaje_error = mensaje_error
        self.nombre_etl = nombre_etl
        self.descripcion_etl = descripcion_etl
        self.tiempo_ejecucion_segundos = tiempo_ejecucion_segundos
        self.nombre_archivo = nombre_archivo
        self.hash_archivo = hash_archivo
