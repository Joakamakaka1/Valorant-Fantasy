#!/bin/bash
#
# Entrypoint Script for Valorant Fantasy API
# 
# Este script se ejecuta al iniciar el contenedor/servidor y asegura que:
# 1. Las migraciones de base de datos estén aplicadas
# 2. El servidor FastAPI se inicie correctamente
#
# Uso:
#   bash entrypoint.sh
#   O en Docker: CMD ["bash", "entrypoint.sh"]
#

set -e  # Salir inmediatamente si algún comando falla

echo "==============================================="
echo "  Valorant Fantasy API - Starting Server"
echo "==============================================="
echo ""

# ============================================================================
# PASO 1: Aplicar migraciones de base de datos
# ============================================================================
echo "🔄 Running database migrations..."
echo "Command: alembic upgrade head"
echo ""

alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Database migrations completed successfully"
else
    echo "❌ Database migrations failed"
    exit 1
fi

echo ""
echo "==============================================="

# ============================================================================
# PASO 2: Iniciar servidor FastAPI
# ============================================================================
echo "🚀 Starting FastAPI server..."
echo "Host: 0.0.0.0"
echo "Port: 8000"
echo ""

# Ejecutar Uvicorn
# --host 0.0.0.0: Permite conexiones desde fuera del contenedor
# --port 8000: Puerto estándar para la API
# Nota: No usar --reload en producción
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Si el servidor se detiene, mostrar mensaje
echo ""
echo "Server stopped."
