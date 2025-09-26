#!/usr/bin/env python3
"""
Script para probar la conexión a Oracle desde el contenedor
"""

import sys
import os
import socket
import subprocess

def test_network_connectivity():
    """Prueba la conectividad de red a Oracle"""
    print("🔍 Probando conectividad de red...")
    
    host = "10.168.48.79"
    port = 1522
    
    try:
        # Probar conexión TCP
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Puerto {port} en {host} es accesible")
            return True
        else:
            print(f"❌ No se puede conectar a {host}:{port}")
            return False
    except Exception as e:
        print(f"❌ Error de conectividad: {e}")
        return False

def test_oracle_libraries():
    """Prueba si las librerías de Oracle están disponibles"""
    print("🔍 Probando librerías de Oracle...")
    
    try:
        import cx_Oracle
        print("✅ cx_Oracle importado correctamente")
        
        # Verificar versión del cliente
        try:
            version = cx_Oracle.clientversion()
            print(f"✅ Versión del cliente Oracle: {version}")
            return True
        except Exception as e:
            print(f"⚠️  cx_Oracle instalado pero cliente no disponible: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ cx_Oracle no está instalado: {e}")
        return False

def test_oracle_connection():
    """Prueba la conexión real a Oracle"""
    print("🔍 Probando conexión a Oracle...")
    
    try:
        import cx_Oracle
        
        # Configuración de conexión
        dsn = cx_Oracle.makedsn("10.168.48.79", 1522, service_name="dbkactus")
        
        print(f"🔗 Intentando conectar a: {dsn}")
        
        connection = cx_Oracle.connect("RRAA_DWH", "D4n3.rR3E*202S", dsn)
        
        # Probar consulta simple
        cursor = connection.cursor()
        cursor.execute("SELECT SYSDATE FROM DUAL")
        result = cursor.fetchone()
        
        print(f"✅ Conexión exitosa! Fecha del servidor: {result[0]}")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Error de conexión a Oracle: {e}")
        return False

def test_environment():
    """Prueba las variables de entorno"""
    print("🔍 Verificando variables de entorno...")
    
    env_vars = [
        "LD_LIBRARY_PATH",
        "ORACLE_HOME",
        "PATH"
    ]
    
    for var in env_vars:
        value = os.environ.get(var, "No definida")
        print(f"   {var}: {value}")
    
    return True

def main():
    """Función principal"""
    print("🚀 Prueba de Conexión Oracle desde Contenedor")
    print("=" * 60)
    
    # Pruebas
    network_ok = test_network_connectivity()
    env_ok = test_environment()
    lib_ok = test_oracle_libraries()
    conn_ok = test_oracle_connection() if lib_ok else False
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    print(f"✅ Conectividad de red: {'OK' if network_ok else 'FALLO'}")
    print(f"✅ Variables de entorno: {'OK' if env_ok else 'FALLO'}")
    print(f"✅ Librerías Oracle: {'OK' if lib_ok else 'FALLO'}")
    print(f"✅ Conexión Oracle: {'OK' if conn_ok else 'FALLO'}")
    
    if all([network_ok, env_ok, lib_ok, conn_ok]):
        print("\n🎉 ¡Todas las pruebas pasaron!")
        print("✅ El contenedor puede conectarse a Oracle")
    else:
        print("\n⚠️  Algunas pruebas fallaron")
        if not network_ok:
            print("   - Verifica que el servidor Oracle esté accesible desde la red del contenedor")
        if not lib_ok:
            print("   - Verifica que las librerías de Oracle estén instaladas en el contenedor")
        if not conn_ok:
            print("   - Verifica las credenciales y configuración de Oracle")
    
    return all([network_ok, env_ok, lib_ok, conn_ok])

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
