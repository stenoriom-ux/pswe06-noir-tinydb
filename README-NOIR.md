# NOIR — Escritura atómica de JSONStorage

Trabajo PSWE-06 sobre TinyDB 4.9.0. La licencia MIT y la autoría original se conservan. Los cambios del incremento se elaboraron con asistencia de Codex para el equipo; requieren revisión y comprensión del equipo antes de la entrega.

## Copia y revisión

- Original: https://github.com/msiemens/tinydb
- Copia: https://github.com/thegabrielobo/pswe06-noir-tinydb
- Rama del trabajo: `noir/atomic-jsonstorage` (el `master` del fork sigue siendo upstream).
- Base congelada: `4aa53111d72c9cbaafcdc039211caf49f4face6f`.
- Módulo: `tinydb/storages.py`; pruebas: `tests/test_atomic_storage.py`.

## Reproducir

Desde la raíz del repositorio, con Python 3.12:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-noir.txt
python -m pytest -o addopts= tests/test_atomic_storage.py
python -m pytest -o addopts= --cov=tinydb --cov-branch --cov-report=term-missing --cov-report=json:evidence/coverage.json --cov-report=html:evidence/htmlcov tests
python -m pycodestyle --config=.pycodestyle tinydb tests
python -m pycodestyle --config=.pycodestyle tinydb/storages.py tests/test_atomic_storage.py
python -m mypy tinydb
```

En Windows, activar con `.venv\Scripts\activate`. La ejecución registrada se hizo en macOS ARM64/Python 3.12.14; otras plataformas no se han verificado. No se usa `--cov-append`: la cifra final es de esta ejecución, sin acumular runs anteriores.

## Historia verificable

| Etapa | Commit local y remoto | Resultado |
|---|---|---|
| Base | `4aa5311` | 222 pruebas aprobadas |
| Preparación | `1c0417b` | Dependencias fijadas, estilo y línea base |
| Prueba HU1, sin producción | `e2a87fb` | Un archivo de prueba, 33 líneas; un fallo real por cambio de bytes del original |
| Pruebas complementarias | `5277249` | 2 fallos y 5 aprobadas antes de producción |
| Implementación mínima | `28a45bd` | Temporal, sincronización, reemplazo y limpieza |
| Refactorización | `2e24c58` | 7 de aceptación y 229 totales aprobadas |

Para repetir el rojo sin alterar la rama principal de trabajo:

```sh
git worktree add --detach ../tinydb-red e2a87fb
cd ../tinydb-red
# Usar el intérprete del entorno previamente creado.
../pswe06-noir-tinydb/.venv/bin/python -m pytest -o addopts= tests/test_atomic_storage.py
```

El nombre local del directorio puede variar; adaptar solo la ruta al intérprete. El resultado esperado de esa comprobación es un fallo (código de salida 1). `e2a87fb` modifica exclusivamente la prueba; producción aparece después, en `28a45bd`.

## Alcance de las historias

- HU1: ante fallo de `fsync` previo al reemplazo, el error se propaga y se conserva exactamente el archivo anterior; se puede reabrir.
- HU2: escrituras mayores y menores, lectura en la misma instancia y reapertura conservan el estado nuevo.
- HU3: no quedan temporales tras éxito, fallo de sincronización ni fallo de reemplazo; un reintento posterior funciona.
- Regresiones complementarias: fallo de serialización y preservación de permisos del archivo.

HU2 ya era comportamiento válido del original; se conserva como regresión, sin inventar una fase roja. La inyección de fallo de HU1 sí demuestra una pérdida de integridad en el original. Los siete casos fueron escritos antes del cambio de producción.

## Resultados

- 229/229 pruebas aprobadas: las 222 originales y 7 casos de aceptación nuevos.
- Sentencias globales: 623/653 = 95,41%.
- Ramas globales: 163/178 = 91,57%.
- Cifra combinada de Coverage.py: 94,58% (la tabla de terminal redondea a 95%).
- `tinydb/storages.py`: 69/69 sentencias y 12/12 ramas, 100%.
- Mypy: sin errores en 10 archivos fuente.
- Pycodestyle global: 13 observaciones heredadas con límite de 99 caracteres (la base tiene 14 con el mismo criterio); salida 1. El incremento no está globalmente «limpio» por este resultado.
- Archivos del incremento: pycodestyle sin observaciones, salida 0.

El plugin de mypy no está ejercitado por la suite funcional y tiene cobertura 0% en ese reporte. Ejecutar mypy aparte comprueba tipos, pero no suma sus líneas a este porcentaje. No comparar directamente con el 98% acumulado del análisis anterior.

## Evidencias y limitaciones

`evidence/` conserva comandos, códigos de salida, revisión probada, salidas y cobertura JSON. El reporte HTML se genera localmente con el comando anterior. Los identificadores temporales y rutas de las salidas dependen del equipo de ejecución.

La garantía cubre fallos controlados previos al reemplazo en el flujo normal de texto (`r+`). El temporal se crea en el mismo directorio y se sincroniza antes de `os.replace`. Se preservan permisos, codificación y opciones de JSON; se vuelve a abrir el archivo para que nuevas lecturas/escrituras usen el destino actualizado.

No se ofrecen bloqueos multiproceso, transacciones, recuperación de archivos ya corruptos ni durabilidad certificada ante pérdida eléctrica. No se sincroniza el directorio después del reemplazo. Un cierre abrupto del proceso puede dejar un temporal: la limpieza verificada corresponde a errores capturados en el flujo, no a `kill -9`. La atomicidad requiere el comportamiento de reemplazo del sistema de archivos. Modos binarios, enlaces duros y plataformas distintas requieren validación adicional.

El incremento está implementado y verificado localmente. La revisión del equipo y los requisitos del informe final del 26 de octubre siguen siendo parte de la siguiente entrega.
