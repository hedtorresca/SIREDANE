from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp

def load_file(path_file: str):
    # Variables internas (no usa .env)
    SPARK_MASTER = "spark://sire-spark-master:7077"
    ORACLE_JDBC_URL = "jdbc:oracle:thin:@sire-oracle:1521/XEPDB1"
    ORACLE_USER = "sire_user"
    ORACLE_PASSWORD = "sire_pass"
    ORACLE_DRIVER = "oracle.jdbc.OracleDriver"
    SPARK_JARS = (
        "org.postgresql:postgresql:42.6.0,"
        "com.oracle.database.jdbc:ojdbc8:21.9.0.0"
    )

    # Inicializar SparkSession
    spark = SparkSession.builder \
        .appName("carga archivos raw_bdua") \
        .master(SPARK_MASTER) \
        .config("spark.jars.packages", SPARK_JARS) \
        .getOrCreate()

    # Leer el archivo CSV
    df = spark.read.option("header", True).option("inferSchema", "true").csv(path_file)


    # Escribir en Oracle
    df.write \
        .format("jdbc") \
        .option("url", ORACLE_JDBC_URL) \
        .option("dbtable", "raw_bdua_airflow_test") \
        .option("user", ORACLE_USER) \
        .option("password", ORACLE_PASSWORD) \
        .option("driver", ORACLE_DRIVER) \
        .mode("overwrite") \
        .save()
