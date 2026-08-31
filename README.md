# Presupuesto Modular App

Aplicación base para el sistema de presupuesto financiero modular.

## Estructura

- app/: punto de entrada de la aplicación
- core/: modelos y utilidades compartidas
- modules/: módulos funcionales por dominio
- data/: archivos de datos y seed
- tests/: pruebas del sistema

## Objetivo del MVP

- Presupuesto de ventas
- Presupuesto de producción
- Compras y MOD
- Costo indirecto flexible
- Análisis de desviaciones
- Resumen financiero básico

## Ejecutar el MVP

Desde la raíz del proyecto, inicia la aplicación web:

```bash
python -m app.main
```

Después abre `http://127.0.0.1:8000/`. El flujo de consola legado continúa
disponible con `python -m app.main --cli`.

La sesión permite seleccionar un rol, crear un presupuesto con una estructura
estándar peruana y registrar partidas específicas. La matriz muestra
los acumulados en los niveles de capítulo, concepto, partida genérica y partida
específica. Los códigos de partida específica usan cuatro dígitos; por ejemplo,
`2111` se consolida en `2110`, `2100` y `2000`.

También se pueden crear subpartidas anidadas como `1000.01`, `1000.01.01` y
`1000.01.01.01`. Cada nodo se agrega dentro del padre elegido y su importe se
acumula hasta el capítulo madre.

Los presupuestos nuevos cargan automáticamente una estructura estándar de
terminología peruana: remuneraciones, pensiones, bienes y servicios, donaciones,
activos y servicio de la deuda. Ya no es necesario seleccionar un capítulo madre;
los capítulos aparecen directamente como contenedores iniciales en la matriz.

El pipeline operativo también conserva el escenario base de ventas, producción,
compras de materia prima, mano de obra directa y gastos indirectos. Para ejecutar
las pruebas:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Ejecutar el backend

El backend HTTP no requiere dependencias externas y guarda los datos en memoria:

```bash
python -m app.backend
```

Endpoints principales:

```text
GET  /health
GET  /catalogo/capitulos
POST /login
GET  /presupuestos
POST /presupuestos
POST /presupuestos/{id}/estructura-madre
POST /presupuestos/{id}/partidas
GET  /presupuestos/{id}/matriz
POST /presupuestos/{id}/aprobar
```

Usuarios demo para el MVP:

```text
lider.operativo / lider2026
director.financiero / director2026
direccion.general / general2026
ingenieria.operaciones / ingenieria2026
```

Dirección General puede consultar presupuestos existentes y aprobarlos. La
exportación a PDF se realiza desde la interfaz mediante la impresión del navegador.

Ejemplo en PowerShell:

```powershell
$presupuesto = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/presupuestos `
	-ContentType 'application/json' `
	-Body '{"nombre":"Presupuesto 2026","ejercicio":2026,"rol":"Lider de Area"}'

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/presupuestos/$($presupuesto.id)/estructura-madre" `
	-ContentType 'application/json' -Body '{"codigo":"2000"}'

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/presupuestos/$($presupuesto.id)/partidas" `
	-ContentType 'application/json' -Body '{"codigo":"2111","descripcion":"Papeleria","importe":1250}'

Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/presupuestos/$($presupuesto.id)/matriz"
```
