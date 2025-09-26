import logging

from config.db_config import DbConfig

first_column = 0


class FileValidator:

    def __init__(self, db_config:DbConfig, spark_session):
        self.db_config = db_config
        self.spark_session = spark_session

    def validate_if_exists(self, md5_file: str) -> bool:
        try:
            query = self.__query__(md5_file)

            connection_properties = {
                "user": self.db_config.jdbc_user,
                "password": self.db_config.jdbc_password,
                "driver": self.db_config.jdbc_driver
            }

            # Read data from the database into a DataFrame
            data = self.spark_session.read.jdbc(url=self.db_config.jdbc_url, table=f"({query})  temp_table", properties=connection_properties)
            return data.first()[first_column]



        except Exception as e:
            logging.error(f"Ocurrió un error al validar si el archivo existe en la base de datos: {e}")
            return True

    def __query__(self, hash_md5) -> str:
        return """
            SELECT CASE
                     WHEN EXISTS (
                       SELECT 1
                       FROM raw_log_etl
                       WHERE hash_archivo = '{0}'
                     )
                     THEN 1
                     ELSE 0
                   END AS file_exists
            FROM dual
        """.format(hash_md5)
