# Presupuesto Modular App

Aplicación para gestionar presupuestos financieros modulares con estructura jerárquica, consolidación por niveles y vistas de reporte.

## Estado actual del proyecto

Este proyecto ya ha avanzado de un MVP básico a una base funcional para presupuestos operativos y financieros. La lógica central permite:

- crear presupuestos con estructura estándar peruana
- seleccionar un capítulo padre o estructura madre
- registrar partidas y subpartidas anidadas
- generar códigos correlativos en jerarquía
- actualizar partidas ya registradas
- consolidar importes por capítulo, nivel y categoría
- visualizar un reporte resumido por categoría y, en una segunda capa, por puesto/cargo
- mantener una vista en matriz con acumulados jerárquicos
- clasificar partidas como OPEX o CAPEX sin cambiar los códigos ni la jerarquía
- programar ingresos y egresos por mes y registrar movimientos reales de caja
- consultar un tablero anual con saldos proyectados y reales acumulados

La aplicación queda organizada en:

- app/: backend, UI y punto de entrada
- core/: modelos de dominio
- modules/: módulos de negocio y estructura financiera
- tests/: pruebas unitarias de regresión
- data/: datos y seed

## Qué ya está funcionando

### 1. Estructura jerárquica de partidas
El sistema puede crear niveles de partidas como:

- 1000
- 1001
- 1001.10
- 1001.10.10
- 1001.20
- 1001.20.10

Esto permite mantener la lógica financiera que exige crecimiento en subpartidas asociadas a una partida base, sin romper la estructura del presupuesto.

### 2. Consolidación por árbol
La matriz calcula montos acumulados en cada nivel del árbol, desde la partida hasta el capítulo principal. El acumulado se mantiene en todos los niveles superiores, lo cual es clave para la toma de decisiones y para la validación del presupuesto.

### 3. Edición de partidas existentes
Se incorporó la posibilidad de actualizar una partida ya registrada, evitando que el sistema quede bloqueado en la primera carga del registro cuando hay un error o se necesita ajustar la línea.

### 4. Reporte funcional
La pestaña de reporte permite observar un consolidado por categoría y por vista. Aunque todavía es un enfoque práctico, ya se tiene la base para proyectar la vista financiera y la vista por puesto/cargo, siguiendo la lógica documentada en los archivos de contexto.

### 5. Pruebas automáticas
La suite cubre la estructura jerárquica, los acumulados, la actualización de partidas, la programación del flujo de caja, los movimientos reales y controles HTTP de acceso por propietario.

### 6. Clasificación financiera y flujo de caja
Cada partida conserva su código y jerarquía y se clasifica como `OPEX`
(gasto operativo) o `CAPEX` (inversión de capital). El tablero anual permite
configurar el saldo inicial, distribuir importes por mes, proyectar ingresos y
registrar ingresos y egresos reales con fecha. El saldo proyectado acumula los
ingresos previstos menos los egresos programados; el saldo real acumula los
movimientos registrados. La programación mensual de una partida no puede
superar su importe anual.

La API expone `GET /api/presupuestos/{id}/flujo-caja`,
`PUT /api/presupuestos/{id}/saldo-inicial`,
`PUT /api/presupuestos/{id}/ingresos-proyectados`,
`PUT /api/presupuestos/{id}/partidas/{codigo}/programacion-mensual` y
`POST /api/presupuestos/{id}/movimientos-caja`. Las rutas HTTP aíslan cada
presupuesto por propietario; Dirección General puede consultarlos y aprobarlos.

## Limitaciones actuales

Aun así, el sistema no está listo para producción financiera completa. Hoy tiene estas restricciones principales:

1. Persistencia en memoria
   - Los datos se pierden al reiniciar el backend.
   - Falta almacenamiento real con base de datos o archivo estructurado.
   - La clasificación, la programación mensual, los saldos y movimientos de caja también se pierden al reiniciar.

2. Modelo financiero todavía parcialmente genérico
   - La lógica de asignación de puestos, salarios, beneficios y análisis del flujo de caja está bien estructurada como base, pero no está modelada con toda la profundidad del negocio real.

3. Reporte todavía funcional, pero no totalmente orientado a BI
   - La vista de reporte sirve para consolidar, pero falta una capa más refinada para pivoteo multidimensional, filtros por periodo, persona, centro de costo y estructura de caja.

4. Validación y control financiero más avanzado
   - Falta validación de reglas empresariales como:
     - centros de costo
     - responsables por línea
     - diferencia entre gasto directo e indirecto
     - integración bancaria y conciliación de caja
     - análisis detallado de variaciones reales vs presupuestadas

5. Persistencia y seguridad de negocio
   - La autenticación actual se basa en usuarios demo en memoria; no es adecuada para producción.
   - No hay control de auditoría, trazabilidad ni historial de cambios.

## Conclusión

El proyecto ya no es un prototipo vacío: tiene una base sólida de presupuesto modular, jerarquía financiera y reporte inicial. El principal valor logrado es que la estructura ya permite crecer en subpartidas, cumplir la lógica financiera y mantener el control del total acumulado en cada nivel.

Sin embargo, para convertirlo en una herramienta útil para toma de decisiones empresariales, lo siguiente es necesario:

1. Persistencia real
   - mover la información a SQLite, PostgreSQL o una capa adecuada de almacenamiento

2. Modelo de negocio más completo
   - distinguir claramente remuneraciones, beneficios, gastos de operación, gastos indirectos, materiales, inversiones y costos de estructura

3. Vista pivote de reporte
   - desarrollar completamente la vista financiera y la vista por puesto/cargo usando los documentos de contexto como referencia

4. Auditoría y aprobación de cambios
   - registrar cambios por usuario, fecha y justificación

5. Interfaz más orientada a usuarios de negocio
   - filtros, edición visual, exportación, KPI, comparativos y gráficos

6. Integración con flujo de caja y análisis de variación
   - comparar presupuesto versus ejecución, con desvíos, alertas y escenarios

## Ruta sugerida de mejora

### Fase 1: estabilizar el núcleo
- persistencia
- validación fuerte de códigos y jerarquías
- edición y eliminación segura de partidas
- pruebas de integración

### Fase 2: fortalecer el modelo financiero
- clasificación por tipo de gasto
- estructura por cargo y centro de costo
- presupuestos por periodo y por responsable

### Fase 3: BI y gestión ejecutiva
- tablero de control
- pivote financiero
- panel por persona, cargo, capítulo y subpartida
- comparación real vs presupuesto

### Fase 4: producción y administración
- usuarios reales
- roles con permisos por negocio
- exportación, historial y versionado

## Cómo ejecutar

### Aplicación web

```bash
python -m app.main
```

Abrir en el navegador:

```text
http://127.0.0.1:8000/
```

### Flujo CLI heredado

```bash
python -m app.main --cli
```

### Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Usuarios demo

```text
lider.operativo / lider2026
director.financiero / director2026
direccion.general / general2026
ingenieria.operaciones / ingenieria2026
```

## En resumen

La base funcional ya existe y es útil como motor inicial del presupuesto modular. Lo que falta no es reinventar la aplicación, sino llevarla a la siguiente etapa: convertirla en un sistema financiero con persistencia, reglas de negocio más exigentes y una capa de análisis ejecutiva sólida. Ese es el siguiente paso natural para transformar este MVP en una herramienta real para gestión financiera.
