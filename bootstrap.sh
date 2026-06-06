#!/bin/bash
# Asegura que ctx7 esté listo
if ! command -v npx &> /dev/null; then
    echo "❌ Node.js/npx no instalado."
    exit 1
fi
npx ctx7 setup
echo "✅ Context7 MCP configurado correctamente."
