import os
from datetime import datetime

from pyspark.sql.types import StructType, StructField, StringType, TimestampType, FloatType, IntegerType

from pyspark_jobs.audit.log_etl_command import LogETLCommand
from pyspark_jobs.spark.spark_session_manager import SparkSessionManager

FIRST_COLUMN = 0

class LogEtlService:

    def __init__(self, spark:SparkSessionManager):
        self.spark = spark
        self.start_command = None
        self.start_moment = None


    def start_job(self, start_command:LogETLCommand):
        self.start_command = start_command
        self.start_moment = datetime.now()


    def end_job(self, registros_cargados:int, mensaje_error:str = None)->int:
        stop_time = datetime.now()
        time_in_seconds = self.__calculate_job_time_in_seconds__(stop_time)
        estado = "SUCCESS"
        if mensaje_error is not None:
            estado = "ERROR"

        log_data = [(self.start_command.job_uuid, self.start_moment, stop_time, estado, registros_cargados,
                     self.start_command.tabla_destino, mensaje_error, self.start_command.nombre_etl,
                     time_in_seconds, self.start_command.nombre_archivo, self.start_command.hash_archivo)]

        log_schema = self.__getDfStructure__()
        sparkSessionManager = SparkSessionManager("Log ETL", os.getenv("SPARK_MASTER"))
        df_log = sparkSessionManager.get_spark_session().createDataFrame(log_data, schema=log_schema)
        sparkSessionManager.load_to_db(df_log, "raw_log_etl", mode="append")

        job_id_df = sparkSessionManager.execute_query("(select id from raw_log_etl where job_uuid = '{}' fetch first 1 rows only) job_id".format(self.start_command.job_uuid))

        return  job_id_df.first()[FIRST_COLUMN]


    def __getDfStructure__(self)-> StructType:
        return StructType([
            StructField("job_uuid", StringType(), True),
            StructField("start_time", TimestampType(), True),
            StructField("end_time", TimestampType(), True),
            StructField("estado", StringType(), True),
            StructField("registros_cargados", IntegerType(), True),
            StructField("tabla_destino", StringType(), True),
            StructField("mensaje_error", StringType(), True),
            StructField("nombre_etl", StringType(), True),
            StructField("tiempo_ejecucion_segundos", FloatType(), True),
            StructField("nombre_archivo", StringType(), True),
            StructField("hash_archivo", StringType(), True)
        ])

    def __calculate_job_time_in_seconds__(self, stop_time:datetime):
        return (stop_time - self.start_moment).total_seconds()
