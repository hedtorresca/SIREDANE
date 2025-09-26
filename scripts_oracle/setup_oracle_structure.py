#!/usr/bin/env python3
"""
Script para configurar la estructura de Oracle automáticamente
Verifica la conexión y crea las tablas necesarias si no existen
"""

import os
import sys
import cx_Oracle
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def load_config():
    """Carga la configuración desde el archivo .env"""
    load_dotenv('config/prod.oracle.env')
    
    config = {
        'connection_string': os.getenv('PROD_ORACLE_CONNECTION_STRING'),
        'user': os.getenv('PROD_ORACLE_JDBC_USER'),
        'password': os.getenv('PROD_ORACLE_JDBC_PASSWORD'),
        'jdbc_url': os.getenv('PROD_ORACLE_JDBC_URL'),
        'schema_sta': os.getenv('ORACLE_SCHEMA_STA', 'SIRE_STA'),
        'schema_dv': os.getenv('ORACLE_SCHEMA_DV', 'SIRE_DV')
    }
    
    # Validar configuración
    if not config['connection_string']:
        raise ValueError("PROD_ORACLE_CONNECTION_STRING no está configurado")
    if not config['user']:
        raise ValueError("PROD_ORACLE_JDBC_USER no está configurado")
    if not config['password']:
        raise ValueError("PROD_ORACLE_JDBC_PASSWORD no está configurado")
    
    return config

def test_connection(config):
    """Prueba la conexión a Oracle"""
    try:
        print("🔍 Probando conexión a Oracle...")
        
        # Probar con SQLAlchemy
        engine = create_engine(config['connection_string'])
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 'Conexión exitosa' as mensaje FROM dual"))
            message = result.scalar()
            print(f"✅ {message}")
            return True
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def check_user_permissions(config):
    """Verifica los permisos del usuario"""
    try:
        print("🔍 Verificando permisos del usuario...")
        
        engine = create_engine(config['connection_string'])
        with engine.connect() as conn:
            # Verificar si puede crear tablas
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM user_tab_privs 
                WHERE privilege = 'CREATE TABLE' OR privilege = 'CREATE ANY TABLE'
            """))
            can_create = result.scalar() > 0
            
            if can_create:
                print("✅ Usuario tiene permisos para crear tablas")
            else:
                print("⚠️ Usuario no tiene permisos explícitos para crear tablas")
                print("   Intentando crear tabla de prueba...")
                
                # Intentar crear una tabla de prueba
                try:
                    conn.execute(text("""
                        CREATE TABLE test_permissions (
                            id NUMBER PRIMARY KEY
                        )
                    """))
                    conn.execute(text("DROP TABLE test_permissions"))
                    print("✅ Usuario puede crear tablas")
                    can_create = True
                except Exception as e:
                    print(f"❌ Usuario no puede crear tablas: {e}")
                    return False
            
            # Verificar esquema actual
            result = conn.execute(text("SELECT USER FROM dual"))
            current_user = result.scalar()
            print(f"ℹ️ Usuario actual: {current_user}")
            
            return can_create
            
    except Exception as e:
        print(f"❌ Error verificando permisos: {e}")
        return False

def create_structure(config):
    """Crea la estructura de tablas"""
    try:
        print("🔨 Creando estructura de tablas...")
        
        # Leer el script SQL
        script_path = 'scripts_sql/oracle/check_and_create_structure.sql'
        if not os.path.exists(script_path):
            print(f"❌ Script no encontrado: {script_path}")
            return False
        
        with open(script_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Reemplazar el esquema en el script
        sql_script = sql_script.replace('SIRE_STA', config['schema_sta'])
        
        engine = create_engine(config['connection_string'])
        with engine.connect() as conn:
            # Ejecutar el script
            conn.execute(text(sql_script))
            conn.commit()
        
        print("✅ Estructura creada exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error creando estructura: {e}")
        return False

def verify_structure(config):
    """Verifica que la estructura esté correcta"""
    try:
        print("🔍 Verificando estructura creada...")
        
        engine = create_engine(config['connection_string'])
        with engine.connect() as conn:
            # Verificar tablas
            tables_to_check = [
                'CONTROL_IDS_GENERADOS',
                'RAW_OBT_PERSONAS', 
                'RAW_OBT_EMPRESAS'
            ]
            
            for table in tables_to_check:
                result = conn.execute(text(f"""
                    SELECT COUNT(*) 
                    FROM user_tables 
                    WHERE table_name = '{table}'
                """))
                exists = result.scalar() > 0
                
                if exists:
                    # Contar registros
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"✅ {table}: Existe ({count} registros)")
                else:
                    print(f"❌ {table}: No existe")
            
            # Verificar índices
            result = conn.execute(text("""
                SELECT index_name, table_name 
                FROM user_indexes 
                WHERE table_name IN ('CONTROL_IDS_GENERADOS', 'RAW_OBT_PERSONAS', 'RAW_OBT_EMPRESAS')
                ORDER BY table_name, index_name
            """))
            
            indexes = result.fetchall()
            print(f"ℹ️ Índices creados: {len(indexes)}")
            for idx_name, table_name in indexes:
                print(f"   - {idx_name} en {table_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando estructura: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Configuración de Oracle para SIRE")
    print("=" * 50)
    
    try:
        # Cargar configuración
        config = load_config()
        print(f"📋 Configuración cargada para usuario: {config['user']}")
        
        # Probar conexión
        if not test_connection(config):
            print("❌ No se puede conectar a Oracle. Verificar credenciales.")
            return 1
        
        # Verificar permisos
        if not check_user_permissions(config):
            print("❌ Usuario no tiene permisos suficientes.")
            return 1
        
        # Crear estructura
        if not create_structure(config):
            print("❌ Error creando estructura.")
            return 1
        
        # Verificar estructura
        if not verify_structure(config):
            print("❌ Error verificando estructura.")
            return 1
        
        print("\n🎉 Configuración completada exitosamente!")
        print("📋 Próximos pasos:")
        print("   1. Ejecutar: docker-compose -f docker-compose.oracle.prod.yml up -d")
        print("   2. Verificar logs: docker-compose -f docker-compose.oracle.prod.yml logs sire-fastapi")
        print("   3. Probar API: curl http://localhost:5003/")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
