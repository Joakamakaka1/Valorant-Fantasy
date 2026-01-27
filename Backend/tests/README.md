# API Integration Tests

Esta carpeta contiene tests de integración para los endpoints de la API de Fantasy Valorant.

## Estructura

- `test_professional.py` - Tests de equipos y jugadores profesionales
- `test_leagues.py` - Tests de ligas, miembros y rosters
- `test_matches.py` - Tests de partidos y estadísticas
- `run_tests.py` - Script principal para ejecutar todos los tests

## Requisitos

```bash
pip install requests
```

## Uso

### Ejecutar todos los tests

```bash
# Asegúrate de que el servidor esté corriendo
uvicorn app.main:app --reload

# En otra terminal, ejecuta los tests
python tests/run_tests.py
```

### Ejecutar tests individuales

```bash
python tests/test_professional.py
python tests/test_leagues.py
python tests/test_matches.py
```

## Qué se testea

### Professional Endpoints

- ✅ Crear equipos y jugadores
- ✅ Filtrar por región, rol, precio
- ✅ Actualizar precios
- ✅ Historial de precios

### Leagues Endpoints

- ✅ Crear ligas con código de invitación
- ✅ Unirse a ligas
- ✅ Añadir jugadores al roster
- ✅ Validación de límites (8 titulares, 3 suplentes)
- ✅ Validación de presupuesto
- ✅ Rankings por puntos

### Matches Endpoints

- ✅ Crear partidos
- ✅ Actualizar resultados
- ✅ Crear estadísticas de jugadores
- ✅ Cálculo automático de fantasy points
- ✅ Marcar partidos como procesados

## Notas

- Los tests crean datos reales en la base de datos
- Algunos tests dependen de autenticación (se crea usuario automáticamente)
- Los fantasy points se calculan automáticamente en el servicio
