class LogETLCommand:

    def __init__(self, nombre_job:str, tabla_destino:str,
                 job_uuid:str, nombre_etl:str, descripcion_etl:str,
                 nombre_archivo:str, hash_archivo:str):
        self.nombre_job = nombre_job
        self.tabla_destino = tabla_destino
        self.job_uuid = job_uuid
        self.nombre_etl = nombre_etl
        self.descripcion_etl = descripcion_etl
        self.nombre_archivo = nombre_archivo
        self.hash_archivo = hash_archivo