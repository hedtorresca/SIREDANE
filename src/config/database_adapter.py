"""
Adaptador de base de datos para manejar diferencias entre Oracle y PostgreSQL
"""
from typing import Dict, Any, Optional
from src.config.db_config import DbConfig, DatabaseType

class DatabaseAdapter:
    """Adaptador para manejar diferencias entre bases de datos"""
    
    def __init__(self, db_config: DbConfig):
        self.db_config = db_config
    
    def get_jdbc_properties(self) -> Dict[str, str]:
        """Retorna las propiedades JDBC específicas para cada base de datos"""
        if self.db_config.is_oracle():
            return {
                "driver": "oracle.jdbc.driver.OracleDriver",
                "url": self.db_config.jdbc_url,
                "user": self.db_config.jdbc_user,
                "password": self.db_config.jdbc_password,
                "oracle.jdbc.timezoneAsRegion": "false",
                "oracle.net.CONNECT_TIMEOUT": "10000",
                "oracle.jdbc.ReadTimeout": "30000"
            }
        else:  # PostgreSQL
            return {
                "driver": "org.postgresql.Driver",
                "url": self.db_config.jdbc_url,
                "user": self.db_config.jdbc_user,
                "password": self.db_config.jdbc_password,
                "ssl": "false",
                "sslmode": "disable"
            }
    
    def get_table_name(self, base_name: str) -> str:
        """Retorna el nombre de tabla con el esquema apropiado"""
        if self.db_config.is_oracle():
            return f"{self.db_config.get_schema_prefix()}.{base_name}"
        else:
            # PostgreSQL usa esquemas, no prefijos
            return base_name
    
    def get_schema_name(self) -> str:
        """Retorna el nombre del esquema según el tipo de BD"""
        if self.db_config.is_oracle():
            return self.db_config.get_schema_prefix()
        else:
            return "public"
    
    def get_create_table_sql(self, table_name: str, columns: Dict[str, str]) -> str:
        """Genera SQL CREATE TABLE específico para cada base de datos"""
        if self.db_config.is_oracle():
            return self._get_oracle_create_table_sql(table_name, columns)
        else:
            return self._get_postgresql_create_table_sql(table_name, columns)
    
    def _get_oracle_create_table_sql(self, table_name: str, columns: Dict[str, str]) -> str:
        """Genera SQL CREATE TABLE para Oracle"""
        column_definitions = []
        for col_name, col_type in columns.items():
            # Mapear tipos de datos a Oracle
            oracle_type = self._map_to_oracle_type(col_type)
            column_definitions.append(f"    {col_name} {oracle_type}")
        
        columns_sql = ",\n".join(column_definitions)
        return f"""CREATE TABLE {self.get_table_name(table_name)} (
{columns_sql}
)"""
    
    def _get_postgresql_create_table_sql(self, table_name: str, columns: Dict[str, str]) -> str:
        """Genera SQL CREATE TABLE para PostgreSQL"""
        column_definitions = []
        for col_name, col_type in columns.items():
            # Mapear tipos de datos a PostgreSQL
            postgres_type = self._map_to_postgresql_type(col_type)
            column_definitions.append(f"    {col_name} {postgres_type}")
        
        columns_sql = ",\n".join(column_definitions)
        return f"""CREATE TABLE {self.get_table_name(table_name)} (
{columns_sql}
)"""
    
    def _map_to_oracle_type(self, generic_type: str) -> str:
        """Mapea tipos genéricos a tipos específicos de Oracle"""
        type_mapping = {
            "string": "VARCHAR2(4000)",
            "varchar": "VARCHAR2(4000)",
            "text": "CLOB",
            "int": "NUMBER(10)",
            "bigint": "NUMBER(19)",
            "float": "NUMBER(10,2)",
            "double": "NUMBER(19,4)",
            "boolean": "NUMBER(1)",
            "date": "DATE",
            "timestamp": "TIMESTAMP",
            "decimal": "NUMBER(19,4)"
        }
        return type_mapping.get(generic_type.lower(), "VARCHAR2(4000)")
    
    def _map_to_postgresql_type(self, generic_type: str) -> str:
        """Mapea tipos genéricos a tipos específicos de PostgreSQL"""
        type_mapping = {
            "string": "VARCHAR(255)",
            "varchar": "VARCHAR(255)",
            "text": "TEXT",
            "int": "INTEGER",
            "bigint": "BIGINT",
            "float": "REAL",
            "double": "DOUBLE PRECISION",
            "boolean": "BOOLEAN",
            "date": "DATE",
            "timestamp": "TIMESTAMP",
            "decimal": "DECIMAL(19,4)"
        }
        return type_mapping.get(generic_type.lower(), "VARCHAR(255)")
    
    def get_insert_sql(self, table_name: str, columns: list) -> str:
        """Genera SQL INSERT específico para cada base de datos"""
        if self.db_config.is_oracle():
            placeholders = ":" + ", :".join(columns)
        else:
            placeholders = ", ".join(["%s"] * len(columns))
        
        columns_str = ", ".join(columns)
        return f"INSERT INTO {self.get_table_name(table_name)} ({columns_str}) VALUES ({placeholders})"
    
    def get_upsert_sql(self, table_name: str, columns: list, key_columns: list) -> str:
        """Genera SQL UPSERT específico para cada base de datos"""
        if self.db_config.is_oracle():
            return self._get_oracle_upsert_sql(table_name, columns, key_columns)
        else:
            return self._get_postgresql_upsert_sql(table_name, columns, key_columns)
    
    def _get_oracle_upsert_sql(self, table_name: str, columns: list, key_columns: list) -> str:
        """Genera SQL MERGE para Oracle"""
        # Implementar MERGE para Oracle
        set_clause = ", ".join([f"{col} = :{col}" for col in columns if col not in key_columns])
        values_clause = ", ".join([f":{col}" for col in columns])
        key_condition = " AND ".join([f"target.{col} = :{col}" for col in key_columns])
        
        return f"""
        MERGE INTO {self.get_table_name(table_name)} target
        USING (SELECT {values_clause} FROM dual) source
        ON ({key_condition})
        WHEN MATCHED THEN UPDATE SET {set_clause}
        WHEN NOT MATCHED THEN INSERT ({", ".join(columns)}) VALUES ({values_clause})
        """
    
    def _get_postgresql_upsert_sql(self, table_name: str, columns: list, key_columns: list) -> str:
        """Genera SQL ON CONFLICT para PostgreSQL"""
        columns_str = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        update_clause = ", ".join([f"{col} = EXCLUDED.{col}" for col in columns if col not in key_columns])
        conflict_columns = ", ".join(key_columns)
        
        return f"""
        INSERT INTO {self.get_table_name(table_name)} ({columns_str})
        VALUES ({placeholders})
        ON CONFLICT ({conflict_columns})
        DO UPDATE SET {update_clause}
        """
