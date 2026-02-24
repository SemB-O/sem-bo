#!/bin/bash

# Script de instalação rápida da Automação SIGTAP

echo "🚀 Instalando Automação SIGTAP..."
echo ""

# 1. Instalar APScheduler
echo "📦 Instalando APScheduler..."
pip install APScheduler==3.10.4

echo ""
echo "✅ Instalação concluída!"
echo ""
echo "📋 Próximos passos:"
echo ""
echo "1. Reinicie o servidor Django:"
echo "   python manage.py runserver"
echo ""
echo "2. Acesse o Dashboard Admin:"
echo "   http://localhost:8000/admin/"
echo ""
echo "3. Clique em 'Atualizar SIGTAP Agora' para testar!"
echo ""
echo "🎉 Sincronização automática configurada para toda segunda às 3h!"
