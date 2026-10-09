# Contexto de Desarrollo Frontend
## Presupuesto Modular MVP

## 1. Proposito

Este documento es el contexto operativo para que un analista frontend pueda actualizar o reemplazar la interfaz HTML del MVP sin alterar las reglas del dominio ni romper la comunicacion con el backend.

El objetivo de la interfaz es permitir que un usuario:

1. Ingrese al aplicativo.
2. Cree un nuevo presupuesto.
3. Seleccione un capítulo del catálogo presupuestario peruano vigente.
4. Cree partidas especificas dentro del capitulo seleccionado.
5. Consulte la matriz madre con los acumulados de partida especifica, partida generica, concepto y capitulo.

La interfaz actual es una pagina HTML servida por el backend Python. El frontend debe ser una capa de presentacion y orquestacion de solicitudes HTTP; no debe duplicar las formulas ni las reglas de validacion del dominio.

## 2. Arquitectura vigente

```text
Navegador
  |
  | HTTP / JSON
  v
app/backend.py
  |
  v
app/workspace.py
  |
  +-- core/models.py
  +-- modules/contabilidad/conac.py
```

El backend usa `http.server` de la biblioteca estandar de Python y almacenamiento en memoria. No hay base de datos en esta etapa. Todos los presupuestos se pierden cuando el proceso se detiene.

La pagina actual se encuentra en:

```text
app/static/index.html
```

La raiz del servidor entrega ese archivo:

```text
GET http://127.0.0.1:8000/
```

El servidor se inicia con:

```bash
python -m app.backend
```

## 3. Pipeline de negocio

El pipeline maestro definido en `pipeline-presupuesto.xpdl` sigue esta secuencia:

```text
Ventas
  -> Produccion
  -> Compras de materia prima
  -> Mano de obra directa
  -> Gastos indirectos / OPEX
  -> Costos de produccion
  -> Gastos de administracion y ventas
  -> Flujo de efectivo
  -> Estados financieros proyectados
  -> Analisis de desviaciones
```

El subflujo Matryoshka de partidas sigue esta secuencia:

```text
Partida especifica (XXXX)
  -> Partida generica (XXX0)
  -> Concepto (XX00)
  -> Capitulo (X000)
```

La interfaz expone la estructura presupuestaria, la matriz y un flujo de caja anual básico. Este flujo compara ingresos previstos y egresos OPEX/CAPEX programados con movimientos reales; no equivale a estados financieros completos, conciliación bancaria ni análisis de desviaciones.

## 4. Catálogo presupuestario y clasificación financiera

El aplicativo conserva el catálogo peruano vigente, con ocho capítulos:

| Codigo | Descripcion |
| --- | --- |
| 1000 | Remuneraciones y obligaciones sociales |
| 2000 | Pensiones y otras prestaciones sociales |
| 3000 | Bienes y servicios |
| 4000 | Donaciones y transferencias |
| 5000 | Otros gastos |
| 6000 | Adquisición de activos no financieros |
| 7000 | Adquisición de activos financieros |
| 8000 | Servicio de la deuda pública |

OPEX y CAPEX son una clasificación adicional de cada partida, no reemplazan el
código ni la jerarquía del catálogo. Los valores permitidos son `OPEX` (gasto
operativo) y `CAPEX` (inversión de capital); las partidas existentes sin
clasificación explícita se consideran OPEX.

Una partida especifica debe:

- Tener exactamente cuatro digitos.
- No terminar en `0`.
- Pertenecer al capitulo madre seleccionado.
- Tener un importe mayor o igual a cero.
- Tener descripcion.

Ejemplo:

```text
Partida especifica: 3111
Partida generica:  3110
Concepto:          3100
Capitulo:          3000
```

Si se registran `3111` por `S/ 1,000` y `3121` por `S/ 500`, ambos se acumulan en `3100` por `S/ 1,500` y en `3000` por `S/ 1,500`.

### Subpartidas anidadas

La estructura también permite cajas dentro de cajas a profundidad variable:

```text
1000              Capítulo madre
1000.01           Subpartida nivel 01: Personal
1000.01.01        Subpartida nivel 02: Nómina
1000.01.01.01     Subpartida nivel 03: Sueldos
```

El padre debe existir antes de crear un hijo. El frontend debe permitir elegir
cualquier nodo como contenedor y proponer el siguiente código consecutivo por
padre. La API recibe `parent_codigo` junto con `codigo`, `descripcion` e `importe`.
Los importes se acumulan en todos los padres y el frontend no debe recalcularlos.

### Personal y conceptos asociados

Un nodo como `1001 · Personal` puede contener pagos de naturaleza distinta que
forman parte del costo total de personal, aunque no sean sueldo directo:

```text
1001          Personal                         S/ 12,300
├── 1001.01   Sueldo       [Sueldo]            S/ 10,000
├── 1001.02   Pensión      [Pension]            S/  1,500
└── 1001.03   Seguro       [Seguro]            S/    800
```

El total del nodo padre y del capítulo debe ser `S/ 12,300`, mientras las tres
partidas deben permanecer visibles como desglose. Al crear una partida se puede
enviar el campo opcional `categoria` con valores como `Sueldo`, `Pension`,
`Seguro` o `Prestacion`. La interfaz debe mostrar la categoría en la fila, pero
el importe total siempre debe provenir de `GET /api/presupuestos/{id}/matriz`.

## 5. Roles vigentes

El backend reconoce estos valores:

- `Lider de Area`
- `Director Financiero`
- `Direccion General`
- `Ingenieria Industrial`

Para el MVP, solo `Lider de Area` y `Director Financiero` pueden crear presupuestos, partidas y movimientos de caja. La restriccion se aplica en backend y no debe implementarse solamente ocultando botones en HTML. Dirección General puede consultar y aprobar presupuestos, pero no editarlos. Los presupuestos de otros usuarios no deben aparecer ni ser accesibles, excepto para Dirección General en modo consulta/aprobación.

La interfaz puede mostrar controles deshabilitados para roles sin permiso, pero debe interpretar cualquier respuesta de error del backend y mostrarla al usuario.

## 6. Contrato HTTP

El frontend debe consumir preferentemente las rutas con prefijo `/api`. El backend tambien acepta las rutas sin prefijo por compatibilidad.

### Salud

```http
GET /api/health
```

Respuesta `200`:

```json
{"status":"ok"}
```

### Catalogo de capitulos

```http
GET /api/catalogo/capitulos
```

Respuesta `200`:

```json
{
  "capitulos": [
    {"codigo":"1000", "descripcion":"Remuneraciones y obligaciones sociales"},
    {"codigo":"2000", "descripcion":"Pensiones y otras prestaciones sociales"}
  ]
}
```

La API devuelve los ocho capítulos del catálogo peruano vigente.

### Inicio de sesión

```http
POST /api/login
Content-Type: application/json
```

Cuerpo: `{"usuario":"lider.operativo","contrasena":"lider2026"}`.
La respuesta entrega `token`, `usuario` y `rol`. Todas las rutas de presupuestos
deben enviar `Authorization: Bearer {token}`.

Usuarios demo: `lider.operativo / lider2026`, `director.financiero / director2026`,
`direccion.general / general2026` e `ingenieria.operaciones / ingenieria2026`.

### Presupuestos existentes y aprobación

`GET /api/presupuestos` devuelve los presupuestos disponibles para la sesión.
`POST /api/presupuestos/{id}/aprobar` está reservado a `Direccion General` y
requiere que el presupuesto tenga al menos una partida. La matriz indica
`aprobado` y `aprobado_por`.

El botón de aprobación debe mostrarse solo a Dirección General, pero la seguridad
real siempre pertenece al backend.

### Crear presupuesto

```http
POST /api/presupuestos
Content-Type: application/json
```

Cuerpo:

```json
{
  "nombre": "Presupuesto 2026",
  "ejercicio": 2026,
  "rol": "Lider de Area"
}
```

Respuesta `201`:

```json
{
  "id": "uuid",
  "nombre": "Presupuesto 2026",
  "ejercicio": 2026,
  "rol": "Lider de Area"
}
```

El frontend debe conservar el `id` en el estado de la sesion. No debe intentar fabricar un identificador.

### Seleccionar estructura madre

```http
POST /api/presupuestos/{id}/estructura-madre
Content-Type: application/json
```

Cuerpo:

```json
{"codigo":"3000"}
```

Respuesta `200`:

```json
{
  "presupuesto_id": "uuid",
  "estructura_madre": "3000"
}
```

### Agregar partida especifica

```http
POST /api/presupuestos/{id}/partidas
Content-Type: application/json
```

Cuerpo:

```json
{
  "codigo": "3111",
  "descripcion": "Servicio de mantenimiento",
  "importe": 1250,
  "clasificacion_financiera": "OPEX"
}
```

Respuesta `201`:

```json
{
  "codigo": "3111",
  "descripcion": "Servicio de mantenimiento",
  "importe": 1250.0,
  "responsable": "Lider de Area",
  "clasificacion_financiera": "OPEX"
}
```

### Consultar matriz

```http
GET /api/presupuestos/{id}/matriz
```

Respuesta `200`:

```json
{
  "id": "uuid",
  "nombre": "Presupuesto 2026",
  "ejercicio": 2026,
  "estructura_madre": "3000",
  "filas": [
    {
      "codigo": "3000",
      "nivel": "Capitulo",
      "descripcion": "Consolidado",
      "importe": 1250.0,
      "clasificacion_financiera": null
    },
    {
      "codigo": "3100",
      "nivel": "Concepto",
      "descripcion": "Consolidado",
      "importe": 1250.0
    },
    {
      "codigo": "3110",
      "nivel": "Partida generica",
      "descripcion": "Consolidado",
      "importe": 1250.0
    },
    {
      "codigo": "3111",
      "nivel": "Partida especifica",
      "descripcion": "Servicio de mantenimiento",
      "importe": 1250.0,
      "clasificacion_financiera": "OPEX"
    }
  ]
}
```

Las filas vienen ordenadas por codigo. El frontend debe renderizar el orden recibido y no volver a calcular acumulados.

### Errores

Las validaciones de negocio responden con JSON y estado `400`:

```json
{"error":"La partida debe pertenecer al capitulo madre seleccionado."}
```

Una ruta inexistente responde con estado `404`:

```json
{"error":"Ruta no encontrada."}
```

Toda solicitud del frontend debe revisar `response.ok`, leer el JSON y mostrar un estado entendible. No debe asumir que toda respuesta es exitosa.

### Flujo de caja anual

El ejercicio se modela de enero a diciembre. Se configura un saldo inicial,
ingresos previstos por mes, importes mensuales de partidas y movimientos reales
con fecha, tipo ingreso/egreso y clasificación OPEX/CAPEX. El backend calcula
los saldos proyectados y reales acumulados.

```http
GET  /api/presupuestos/{id}/flujo-caja
PUT  /api/presupuestos/{id}/saldo-inicial
PUT  /api/presupuestos/{id}/ingresos-proyectados
PUT  /api/presupuestos/{id}/partidas/{codigo}/programacion-mensual
POST /api/presupuestos/{id}/movimientos-caja
```

Los cuerpos de los `PUT` mensuales usan `{"mes":1,"importe":250.00}`. El
movimiento real usa `fecha` (`AAAA-MM-DD`), `tipo` (`ingreso` o `egreso`),
`descripcion`, `importe` y, para egresos, `clasificacion_financiera` (`OPEX` o
`CAPEX`). `partida_codigo` es opcional para egresos. Un movimiento debe
pertenecer al ejercicio del presupuesto y la suma de programación mensual de
una partida no puede superar su presupuesto anual.

Las partidas y movimientos se conservan en memoria; el tablero no representa
datos bancarios importados ni conciliados.

## 7. Flujo de pantalla obligatorio

### Estado inicial

- Mostrar formulario de nuevo presupuesto.
- Mostrar el selector de capitulo deshabilitado.
- Mostrar el formulario de partidas deshabilitado.
- Mostrar matriz vacia con un mensaje de inicio.

### Despues de crear presupuesto

- Guardar el `id` recibido.
- Mostrar nombre, ejercicio y rol activo.
- Cargar los capitulos desde `/api/catalogo/capitulos`.
- Habilitar la seleccion de estructura madre.
- Mantener deshabilitada la captura de partidas hasta seleccionar capitulo.

### Despues de seleccionar estructura madre

- Mostrar el codigo y descripcion del capitulo.
- Mostrar el contexto en la captura, por ejemplo `1000 · Remuneraciones y obligaciones sociales`.
- Proponer automaticamente la primera partida especifica del capitulo, por ejemplo `1001`.
- Habilitar la captura de partidas si el rol tiene permiso.
- Consultar y renderizar la matriz.
- Mostrar total del capitulo seleccionado.

### Despues de agregar partida

- Limpiar el formulario solo si la respuesta fue exitosa.
- Proponer el siguiente codigo consecutivo, por ejemplo `1002` despues de guardar `1001`.
- Actualizar la matriz consultando nuevamente el backend.
- Mostrar confirmacion de alta.
- Si hay error, conservar los datos escritos para facilitar la correccion.

### Tablero de flujo de caja

- Permitir capturar el saldo inicial del ejercicio.
- Permitir programar ingresos previstos por mes.
- Permitir distribuir el presupuesto anual OPEX/CAPEX por partida y mes.
- Permitir registrar movimientos reales y asociar opcionalmente egresos con una partida.
- Mostrar comparativo mensual de egresos presupuestados y reales, flujos netos y saldos acumulados proyectados/reales.
- Mostrar el importe anual aún no distribuido por mes.
- No presentar el flujo como conciliado con banco ni como un estado financiero completo.

## 8. Reglas para reemplazar `index.html` sin bugs

Un nuevo HTML puede reemplazar directamente:

```text
app/static/index.html
```

Debe cumplir todas estas condiciones:

1. Ser un archivo autonomo servido por `GET /`.
2. Usar rutas relativas `/api/...`; no fijar `localhost` o un puerto en JavaScript.
3. Mantener los seis contratos HTTP descritos en este documento.
4. No cambiar nombres de propiedades JSON como `id`, `estructura_madre`, `filas`, `codigo` o `importe`.
5. No calcular en frontend los acumulados de la matriz.
6. Permitir seleccionar cualquier nodo existente como padre de una nueva subpartida.
7. Mantener visible la relación padre-hijo y proponer códigos consecutivos por padre.
8. No permitir que una seleccion de capitulo habilite partidas sin haber creado presupuesto.
9. No permitir que una partida se presente como guardada antes de recibir `201`.
10. Manejar errores `400`, `404` y fallos de red sin dejar la pantalla bloqueada.
11. Escapar o insertar como texto los valores recibidos del backend; no interpolar descripciones sin sanitizacion en `innerHTML`.
12. Funcionar en escritorio y movil.
13. No requerir un proceso de compilacion, npm, bundler ni dependencias externas para ser reemplazable en este MVP.
14. Conservar `lang="es"`, viewport responsive y controles accesibles con etiquetas.
15. No depender de archivos estaticos adicionales, porque el backend actual solo sirve `index.html`.
16. Si se agrega una hoja de estilos o script externo, se debe actualizar tambien el servidor para servirlo y probar la ruta.

## 9. Criterios de aceptacion

El reemplazo frontend se considera compatible cuando:

- `python -m app.backend` inicia sin errores.
- `GET http://127.0.0.1:8000/` entrega HTML con estado `200`.
- La pantalla carga los ocho capítulos peruanos vigentes desde la API.
- Se puede crear un presupuesto con rol `Lider de Area`.
- Se puede seleccionar `3000` como estructura madre.
- Se puede guardar `3111` con importe `1250`.
- La matriz muestra `3111`, `3110`, `3100` y `3000`.
- El total de `3000` aparece como `S/ 1,250.00` o equivalente local.
- Una partida `2111` bajo madre `3000` muestra el error del backend y no aparece en la matriz.
- Un importe negativo no se presenta como guardado.
- Un rol sin permiso no puede registrar partidas aunque intente llamar la API.
- OPEX/CAPEX se conserva al consultar la matriz y programar partidas por mes.
- El saldo proyectado y el real se calculan con movimientos mensuales distintos.
- Un usuario no puede consultar ni modificar presupuestos de otro propietario; Dirección General puede consultarlos y aprobarlos.
- La suite existente sigue pasando:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## 10. Limitaciones conocidas del MVP

- El almacenamiento es temporal y en memoria.
- La autenticación usa usuarios demo y sesiones en memoria; no es autenticación de producción.
- No hay edicion ni eliminacion de partidas.
- No hay persistencia. Las rutas web aíslan presupuestos por propietario y Dirección General puede consultarlos/aprobarlos, pero no existe gestión productiva de usuarios.
- La matriz actualmente representa importes de partidas; aun no integra todo el pipeline financiero.
- El servidor actual no sirve archivos estaticos adicionales.
- El flujo de caja es una proyección básica; no hay integración/conciliación bancaria, estados financieros ni análisis de desviaciones.

## 11. Comprobacion manual recomendada

1. Iniciar el backend.
2. Abrir `http://127.0.0.1:8000/`.
3. Crear `Presupuesto 2026`, ejercicio `2026`, rol `Lider de Area`.
4. Seleccionar `3000 - Bienes y servicios`.
5. Agregar `3111 - Servicio de mantenimiento - 1250`.
6. Agregar `3121 - Material de limpieza - 500`.
7. Confirmar que `3100` suma `S/ 1,500` y `3000` suma `S/ 1,500`.
8. Intentar agregar `2111` y confirmar que el backend rechaza la partida.
9. Detener y reiniciar el backend para verificar que la interfaz tolera una nueva sesion sin datos previos.
10. Configurar saldo inicial, ingreso previsto y egresos OPEX/CAPEX para dos meses; verificar saldos proyectados.
11. Registrar un ingreso y un egreso real y confirmar que el saldo real evoluciona independientemente del proyectado.
