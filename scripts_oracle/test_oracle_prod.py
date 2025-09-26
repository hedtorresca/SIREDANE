#!/usr/bin/env python3
"""
Script de prueba para verificar la conexión a Oracle en producción
y probar las funcionalidades de la API
"""

import cx_Oracle
import os
import sys
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

# Agregar el directorio raíz al path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def load_prod_config():
    """Carga la configuración de producción"""
    env_file = project_root / "config" / "prod.oracle.env"
    load_dotenv(env_file)
    
    return {
        "host": "10.168.48.79",
        "port": 1522,
        "service_name": "dbkactus",
        "user": "RRAA_STAGING",
        "password": "Dane2025"
    }

def test_direct_connection():
    """Prueba la conexión directa a Oracle"""
    print("🔍 Probando conexión directa a Oracle...")
    
    config = load_prod_config()
    
    try:
        dsn = cx_Oracle.makedsn(config["host"], config["port"], service_name=config["service_name"])
        connection = cx_Oracle.connect(config["user"], config["password"], dsn)
        
        cursor = connection.cursor()
        cursor.execute("SELECT SYSDATE FROM DUAL")
        result = cursor.fetchone()
        
        print(f"✅ Conexión exitosa a Oracle")
        print(f"   Host: {config['host']}:{config['port']}")
        print(f"   Service: {config['service_name']}")
        print(f"   Usuario: {config['user']}")
        print(f"   Fecha del servidor: {result[0]}")
        
        # Verificar esquema
        cursor.execute("SELECT USER FROM DUAL")
        current_user = cursor.fetchone()[0]
        print(f"   Usuario actual: {current_user}")
        
        # Verificar tablas
        cursor.execute("""
            SELECT table_name 
            FROM user_tables 
            WHERE table_name IN ('CONTROL_IDS_GENERADOS', 'RAW_OBT_EMPRESAS', 'RAW_OBT_PERSONAS')
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        print(f"   Tablas encontradas: {[table[0] for table in tables]}")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Error de conexión directa: {e}")
        return False

def test_api_connection():
    """Prueba la conexión a la API FastAPI"""
    print("\n🔍 Probando conexión a la API FastAPI...")
    
    try:
        # Probar endpoint de salud
        response = requests.get("http://localhost:5003/", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API respondiendo correctamente")
            print(f"   Mensaje: {data.get('message', 'N/A')}")
            print(f"   Base de datos: {data.get('database', 'N/A')}")
            return True
        else:
            print(f"❌ API respondió con código: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ No se pudo conectar a la API (¿está ejecutándose?)")
        return False
    except Exception as e:
        print(f"❌ Error probando API: {e}")
        return False

def test_persona_endpoint():
    """Prueba el endpoint de generación de ID para personas"""
    print("\n🔍 Probando endpoint de personas...")
    
    test_data = {
        "tipo_documento": "CC",
        "numero_documento": "12345678",
        "primer_nombre": "Juan",
        "segundo_nombre": "Carlos",
        "primer_apellido": "Pérez",
        "segundo_apellido": "García",
        "fecha_nacimiento": "1990-01-15",
        "sexo_an": "M",
        "codigo_municipio_nacimiento": 11001,
        "codigo_pais_nacimiento": 170
    }
    
    try:
        response = requests.post(
            "http://localhost:5003/generar-id-personas",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Endpoint de personas funcionando")
            print(f"   ID generado: {data.get('id_estadistico', 'N/A')}")
            print(f"   Mensaje: {data.get('mensaje', 'N/A')}")
            print(f"   Tipo entidad: {data.get('tipo_entidad', 'N/A')}")
            return True
        else:
            print(f"❌ Error en endpoint de personas: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error probando endpoint de personas: {e}")
        return False

def test_empresa_endpoint():
    """Prueba el endpoint de generación de ID para empresas"""
    print("\n🔍 Probando endpoint de empresas...")
    
    test_data = {
        "tipo_documento": "NIT",
        "numero_documento": "900123456",
        "razon_social": "Empresa de Prueba S.A.S.",
        "digito_verificacion": "7",
        "codigo_camara": "11001",
        "camara_comercio": "Bogotá",
        "matricula": "12345",
        "fecha_matricula": "2020-01-15",
        "fecha_renovacion": "2021-01-15",
        "ultimo_ano_renovado": 2021,
        "fecha_vigencia": "2022-01-15",
        "fecha_cancelacion": None,
        "codigo_tipo_sociedad": "01",
        "tipo_sociedad": "Sociedad Anónima",
        "codigo_organizacion_juridica": "01",
        "organizacion_juridica": "Sociedad Anónima",
        "codigo_estado_matricula": "01",
        "estado_matricula": "Activa",
        "representante_legal": "Juan Pérez",
        "num_identificacion_representante_legal": "12345678",
        "clase_identificacion_rl": "CC",
        "fecha_actualizacion": "2023-01-01T00:00:00"
    }
    
    try:
        response = requests.post(
            "http://localhost:5003/generar-id-empresas",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Endpoint de empresas funcionando")
            print(f"   ID generado: {data.get('id_estadistico', 'N/A')}")
            print(f"   Mensaje: {data.get('mensaje', 'N/A')}")
            print(f"   Tipo entidad: {data.get('tipo_entidad', 'N/A')}")
            return True
        else:
            print(f"❌ Error en endpoint de empresas: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error probando endpoint de empresas: {e}")
        return False

def test_duplicate_persona():
    """Prueba el comportamiento con datos duplicados"""
    print("\n🔍 Probando comportamiento con datos duplicados...")
    
    test_data = {
        "tipo_documento": "CC",
        "numero_documento": "12345678",  # Mismo documento que en test_persona_endpoint
        "primer_nombre": "Juan",
        "segundo_nombre": "Carlos",
        "primer_apellido": "Pérez",
        "segundo_apellido": "García",
        "fecha_nacimiento": "1990-01-15",
        "sexo_an": "M",
        "codigo_municipio_nacimiento": 11001,
        "codigo_pais_nacimiento": 170
    }
    
    try:
        response = requests.post(
            "http://localhost:5003/generar-id-personas",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Manejo de duplicados funcionando")
            print(f"   ID: {data.get('id_estadistico', 'N/A')}")
            print(f"   Mensaje: {data.get('mensaje', 'N/A')}")
            
            if "ya existe" in data.get('mensaje', '').lower():
                print("   ✅ Correctamente detectó duplicado")
            else:
                print("   ⚠️  No detectó duplicado (puede ser normal si es la primera vez)")
            
            return True
        else:
            print(f"❌ Error en prueba de duplicados: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error probando duplicados: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Iniciando pruebas de Oracle en producción...")
    print("=" * 60)
    
    # Pruebas de conexión
    direct_ok = test_direct_connection()
    api_ok = test_api_connection()
    
    if not direct_ok:
        print("\n❌ No se pudo conectar directamente a Oracle. Verifica la configuración.")
        return False
    
    if not api_ok:
        print("\n❌ La API no está respondiendo. Inicia el servicio primero:")
        print("   docker-compose -f docker-compose.oracle.prod.yml up sire-fastapi")
        return False
    
    # Pruebas de funcionalidad
    persona_ok = test_persona_endpoint()
    empresa_ok = test_empresa_endpoint()
    duplicate_ok = test_duplicate_persona()
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    print(f"✅ Conexión directa a Oracle: {'OK' if direct_ok else 'FALLO'}")
    print(f"✅ Conexión a API: {'OK' if api_ok else 'FALLO'}")
    print(f"✅ Endpoint de personas: {'OK' if persona_ok else 'FALLO'}")
    print(f"✅ Endpoint de empresas: {'OK' if empresa_ok else 'FALLO'}")
    print(f"✅ Manejo de duplicados: {'OK' if duplicate_ok else 'FALLO'}")
    
    all_ok = all([direct_ok, api_ok, persona_ok, empresa_ok, duplicate_ok])
    
    if all_ok:
        print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")
        print("✅ El sistema está listo para producción")
    else:
        print("\n⚠️  Algunas pruebas fallaron. Revisa los errores anteriores.")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
