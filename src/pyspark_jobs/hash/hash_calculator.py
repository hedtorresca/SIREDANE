import hashlib
import logging

class HashCalculator:

    @staticmethod
    def calculate_hash(file_path:str, spark) -> str:
        try:
            logging.info(f"Calculando hash del archivo {file_path}")
            df = spark.read.text(file_path)
            joined = "".join([row.value for row in df.collect()])
            return hashlib.sha256(joined.encode("utf-8")).hexdigest()
        except Exception as e:
            logging.error(f"Ocurrió un error al calcular el hash del archivo: {e}")
            raise e

    @staticmethod
    def get_hash(cadena_convertir:str) -> str:
        try:
            return hashlib.md5(cadena_convertir.encode("utf-8")).hexdigest()
        except Exception as e:
            logging.error(f"Ocurrió un error al calcular el hash de la cadena {cadena_convertir}: {e}")
            raise e



