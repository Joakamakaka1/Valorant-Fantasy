"""
Script para ejecutar todos los tests de la API

Ejecuta los tests de professional, leagues y matches en orden.
"""

import sys
import os

# Añadir el directorio principal al path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_professional import run_all_tests as run_professional_tests
from tests.test_leagues import run_all_tests as run_leagues_tests
from tests.test_matches import run_all_tests as run_matches_tests

def main():
    print("\n" + "="*70)
    print("🎯 EJECUTANDO SUITE COMPLETA DE TESTS - Fantasy Valorant API")
    print("="*70)
    print("\n⚠️  IMPORTANTE: Asegúrate de que el servidor esté corriendo:")
    print("   uvicorn app.main:app --reload")
    print("\n" + "="*70)
    
    input("\nPresiona ENTER para comenzar los tests...")
    
    try:
        # Ejecutar tests en orden
        run_professional_tests()
        print("\n" + "⏸️ "*35)
        input("Presiona ENTER para continuar con los tests de LEAGUES...")
        
        run_leagues_tests()
        print("\n" + "⏸️ "*35)
        input("Presiona ENTER para continuar con los tests de MATCHES...")
        
        run_matches_tests()
        
        # Resumen final
        print("\n\n" + "="*70)
        print("🎉 TODOS LOS TESTS COMPLETADOS EXITOSAMENTE")
        print("="*70)
        print("\nResumen:")
        print("  ✅ Professional endpoints - OK")
        print("  ✅ Leagues endpoints - OK")
        print("  ✅ Matches endpoints - OK")
        print("\n" + "="*70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrumpidos por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error ejecutando tests: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
