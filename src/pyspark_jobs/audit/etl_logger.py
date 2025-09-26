import datetime
import uuid
import logging
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, IntegerType, FloatType

from config.db_config import DbConfig


class EtlLogger:

    def __init__(self, spark: SparkSession, db_config: DbConfig):
        self.spark = spark
        self.db_config = db_config

    def save(self, tabla_destino: str, start_time: datetime.datetime, end_time: datetime.datetime,
             estado: str, registros_cargados: int, mensaje_error: str = None, nombre_etl: str = None,
             tiempo_ejecucion_segundos: float = None, hash_archivo: str = None, file_name: str = None):

        job_execution_id = str(uuid.uuid4())

        log_data = [(job_execution_id, start_time, end_time, estado, registros_cargados, tabla_destino,
                     mensaje_error, nombre_etl, tiempo_ejecucion_segundos, file_name, hash_archivo)]


        log_schema = StructType([
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

        df_log = self.spark.createDataFrame(log_data, schema=log_schema)

        df_log.write \
            .format("jdbc") \
            .option("url", self.db_config.jdbc_url) \
            .option("dbtable", "raw_log_etl") \
            .option("user", self.db_config.jdbc_user) \
            .option("password", self.db_config.jdbc_password) \
            .option("driver", self.db_config.jdbc_driver) \
            .mode("append") \
            .save()

        logging.info(f"Log ETL registrado en 'raw_log_etl' con job_execution_id={job_execution_id}")
