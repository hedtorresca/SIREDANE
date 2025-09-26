#!/usr/bin/env python3
"""
Script de prueba rápida para verificar la conexión a Oracle
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def main():
    print("🔍 Prueba rápida de conexión a Oracle")
    print("=" * 40)
    
    # Cargar configuración
    load_dotenv('config/prod.oracle.env')
    
    connection_string = os.getenv('PROD_ORACLE_CONNECTION_STRING')
    if not connection_string:
        print("❌ PROD_ORACLE_CONNECTION_STRING no configurado")
        return 1
    
    print(f"📋 Conectando a: {connection_string.split('@')[1] if '@' in connection_string else 'Oracle'}")
    
    try:
        # Probar conexión
        engine = create_engine(connection_string)
        with engine.connect() as conn:
            # Consulta simple
            result = conn.execute(text("SELECT 'Conexión exitosa' as mensaje, USER as usuario, SYSDATE as fecha FROM dual"))
            row = result.fetchone()
            
            print(f"✅ {row[0]}")
            print(f"👤 Usuario: {row[1]}")
            print(f"📅 Fecha: {row[2]}")
            
            # Verificar tablas SIRE
            result = conn.execute(text("""
                SELECT table_name 
                FROM user_tables 
                WHERE table_name IN ('CONTROL_IDS_GENERADOS', 'RAW_OBT_PERSONAS', 'RAW_OBT_EMPRESAS')
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result.fetchall()]
            if tables:
                print(f"📊 Tablas SIRE encontradas: {', '.join(tables)}")
            else:
                print("⚠️ No se encontraron tablas SIRE (ejecutar setup_oracle_structure.py)")
            
            return 0
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())








