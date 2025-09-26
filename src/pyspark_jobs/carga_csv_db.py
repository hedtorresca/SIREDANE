import logging
import os
import uuid
from datetime import datetime

from dotenv import load_dotenv
from pyspark.sql.functions import lit, current_timestamp
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType

from config.db_config import DbConfig
from config.logging_config import basic_config
from pyspark_jobs.audit.etl_logger import EtlLogger
from pyspark_jobs.hash.hash_calculator import HashCalculator
from pyspark_jobs.spark.spark_session_manager import SparkSessionManager
from pyspark_jobs.validations.file_validator import FileValidator

basic_config()

class CsvFileLoader:

    def __init__(self, db_config: DbConfig):
        self.db_config = db_config

    def load(self, csv_path: str, tabla_destino: str, mode: str = "append")-> str | None:

        load_dotenv()
        spark_manager = SparkSessionManager(app_name="CsvFileLoader.load", spark_master=os.getenv("SPARK_MASTER"))

        start_time = datetime.now()

        file_validator = FileValidator(db_config=self.db_config, spark_session=spark_manager.get_spark_session())
        etl_logger = EtlLogger(spark=spark_manager.get_spark_session(), db_config=self.db_config)

        try:

            hash_file = HashCalculator.calculate_hash(csv_path, spark_manager.get_spark_session())
            if file_validator.validate_if_exists(hash_file):
                logging.warning(f"El archivo {csv_path} ya se encuentra cargado en el sistema")
                return None

            self.__load_to_db_and_log__(csv_path, etl_logger, hash_file, mode, spark_manager, start_time, tabla_destino)
            return hash_file

        except Exception as e:
            logging.error(f"Ocurrio un error al cargar el archivo {csv_path}: {e}")
            self.__register_error_to_log_table__(csv_path, e, etl_logger, start_time, tabla_destino)
            return None
        finally:
            logging.info("Sesión de Spark cerrada")
            spark_manager.stop_spark_session()


    def __register_error_to_log_table__(self, csv_path, e, etl_logger, start_time, tabla_destino):
        stop_time = datetime.now()
        etl_logger.save(tabla_destino=tabla_destino, start_time=start_time, end_time=stop_time, estado="ERROR",
                        registros_cargados=0,
                        nombre_etl='bdua.raw', mensaje_error=str(e),
                        tiempo_ejecucion_segundos=self.__calculate_job_time_in_seconds__(start_time, stop_time),
                        hash_archivo=None, file_name=csv_path)

    def __load_to_db_and_log__(self, csv_path, etl_logger, hash_file, mode, sparkManager, start_time, tabla_destino):
        df = self.__read_csv_file__(csv_path, sparkManager)
        sparkManager.load_to_db(df=df, table_name=tabla_destino, mode=mode)

        stop_time = datetime.now()
        etl_logger.save(tabla_destino=tabla_destino, start_time=start_time, end_time=stop_time, estado="SUCCESS",
                        registros_cargados=df.count(),
                        nombre_etl='bdua.raw', mensaje_error=None,
                        tiempo_ejecucion_segundos=self.__calculate_job_time_in_seconds__(start_time, stop_time),
                        hash_archivo=hash_file, file_name=csv_path)

    def __calculate_job_time_in_seconds__(self, start_time, stop_time):
        return (stop_time - start_time).total_seconds()

    def __generar_id_estadistico__(self):
        return str(uuid.uuid4())

    def __read_csv_file__(self, csv_path, spark_session_manager: SparkSessionManager):
        df = spark_session_manager.read_csv(header=True, csv_path=csv_path)
        df = df.withColumn("load_date", lit(current_timestamp()))
        df = df.withColumn("file_name", lit(csv_path))
        uuid_udf = udf(self.__generar_id_estadistico__, StringType())
        df = df.withColumn("id_estadistico_persona", uuid_udf())
        return df


# corre directamente este archivo
if __name__ == "__main__":
    load_dotenv()
    csv_file_loader = CsvFileLoader(db_config=DbConfig())
    csv_file_loader.load(
        csv_path="C:/Users/ASUS/Documents/SIRE/sire/src/data/bdua.csv",
        tabla_destino="raw_bdua"
    )
