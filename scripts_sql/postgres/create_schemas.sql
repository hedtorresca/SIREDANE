-- Crear esquemas para PostgreSQL
-- Este script se ejecuta al inicializar el contenedor PostgreSQL

-- Crear esquema para Data Vault
CREATE SCHEMA IF NOT EXISTS sire_dv;

-- Crear esquema para Staging
CREATE SCHEMA IF NOT EXISTS sire_sta;

-- Crear esquema para catálogos
CREATE SCHEMA IF NOT EXISTS catalogo;

-- Crear esquema para datos raw
CREATE SCHEMA IF NOT EXISTS raw;

-- Otorgar permisos
GRANT USAGE ON SCHEMA sire_dv TO sire_user;
GRANT USAGE ON SCHEMA sire_sta TO sire_user;
GRANT USAGE ON SCHEMA catalogo TO sire_user;
GRANT USAGE ON SCHEMA raw TO sire_user;

GRANT CREATE ON SCHEMA sire_dv TO sire_user;
GRANT CREATE ON SCHEMA sire_sta TO sire_user;
GRANT CREATE ON SCHEMA catalogo TO sire_user;
GRANT CREATE ON SCHEMA raw TO sire_user;
