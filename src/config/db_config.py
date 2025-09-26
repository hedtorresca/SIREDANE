import os
from dotenv import load_dotenv
from enum import Enum
from typing import Dict, Any

class DatabaseType(Enum):
    POSTGRESQL = "postgresql"
    ORACLE = "oracle"

class DbConfig:
    def __init__(self):
        load_dotenv()
        
        # Determinar el tipo de base de datos desde variables de entorno
        db_type = os.getenv("DATABASE_TYPE", "postgresql").lower()
        self.database_type = DatabaseType(db_type)
        
        # Determinar el ambiente
        environment = os.getenv("ENVIRONMENT", "dev").lower()
        
        if environment == "dev":
            self.set_dev_parameters()
        elif environment == "prod":
            self.set_prod_parameters()
        else:
            raise ValueError(f"Ambiente no soportado: {environment}")

    def set_prod_parameters(self):
        """Configuración para ambiente de producción"""
        if self.database_type == DatabaseType.ORACLE:
            self.jdbc_url = os.getenv("PROD_ORACLE_JDBC_URL")
            self.jdbc_user = os.getenv("PROD_ORACLE_JDBC_USER")
            self.jdbc_password = os.getenv("PROD_ORACLE_JDBC_PASSWORD")
            self.jdbc_driver = "oracle.jdbc.driver.OracleDriver"
            self.connection_string = os.getenv("PROD_ORACLE_CONNECTION_STRING")
        else:  # PostgreSQL
            self.jdbc_url = os.getenv("PROD_POSTGRES_JDBC_URL")
            self.jdbc_user = os.getenv("PROD_POSTGRES_JDBC_USER")
            self.jdbc_password = os.getenv("PROD_POSTGRES_JDBC_PASSWORD")
            self.jdbc_driver = "org.postgresql.Driver"
            self.connection_string = os.getenv("PROD_POSTGRES_CONNECTION_STRING")

    def set_dev_parameters(self):
        """Configuración para ambiente de desarrollo"""
        if self.database_type == DatabaseType.ORACLE:
            # Oracle como base de datos de destino
            self.jdbc_url = os.getenv("DEV_ORACLE_JDBC_URL", "jdbc:oracle:thin:@oracle-db:1521/XEPDB1")
            self.jdbc_user = os.getenv("DEV_ORACLE_JDBC_USER", "SIRE_STG")
            self.jdbc_password = os.getenv("DEV_ORACLE_JDBC_PASSWORD", "sire_password")
            self.jdbc_driver = "oracle.jdbc.driver.OracleDriver"
            self.connection_string = os.getenv("DEV_ORACLE_CONNECTION_STRING", "oracle://SIRE_STG:sire_password@oracle-db:1521/XEPDB1")
        else:  # PostgreSQL como base de datos de destino
            self.jdbc_url = os.getenv("DEV_POSTGRES_JDBC_URL", "jdbc:postgresql://sire-postgres-dw:5432/sire_dw")
            self.jdbc_user = os.getenv("DEV_POSTGRES_JDBC_USER", "sire_user")
            self.jdbc_password = os.getenv("DEV_POSTGRES_JDBC_PASSWORD", "sire_password")
            self.jdbc_driver = "org.postgresql.Driver"
            self.connection_string = os.getenv("DEV_POSTGRES_CONNECTION_STRING", "postgresql://sire_user:sire_password@sire-postgres-dw:5432/sire_dw")

    def get_params(self) -> Dict[str, Any]:
        """Retorna los parámetros de conexión para PySpark"""
        return {
            "url": self.jdbc_url,
            "user": self.jdbc_user,
            "password": self.jdbc_password,
            "driver": self.jdbc_driver
        }
    
    def get_connection_string(self) -> str:
        """Retorna la cadena de conexión para SQLAlchemy"""
        return self.connection_string
    
    def get_database_type(self) -> DatabaseType:
        """Retorna el tipo de base de datos configurado"""
        return self.database_type
    
    def is_oracle(self) -> bool:
        """Verifica si está configurado para Oracle"""
        return self.database_type == DatabaseType.ORACLE
    
    def is_postgresql(self) -> bool:
        """Verifica si está configurado para PostgreSQL"""
        return self.database_type == DatabaseType.POSTGRESQL
    
    def get_schema_prefix(self) -> str:
        """Retorna el prefijo de esquema según el tipo de base de datos"""
        if self.is_oracle():
            return "SIRE_DV"
        else:
            return "sire_dv"  # PostgreSQL usa esquemas
    
    def get_staging_schema(self) -> str:
        """Retorna el esquema de staging según el tipo de base de datos"""
        if self.is_oracle():
            return "SIRE_STA"
        else:
            return "sire_sta"
    
    def get_sqlalchemy_conn_string(self) -> str:
        """Retorna la cadena de conexión para SQLAlchemy con el tipo correcto"""
        if self.is_oracle():
            return self.connection_string
        else:
            return self.connection_string
    
    def get_oracle_connection_params(self) -> dict:
        """Retorna parámetros específicos para conexión Oracle"""
        if self.is_oracle():
            return {
                "user": self.jdbc_user,
                "password": self.jdbc_password,
                "dsn": self.jdbc_url.replace("jdbc:oracle:thin:@", ""),
                "encoding": "UTF-8",
                "nencoding": "UTF-8"
            }
        else:
            raise ValueError("Método solo disponible para Oracle")