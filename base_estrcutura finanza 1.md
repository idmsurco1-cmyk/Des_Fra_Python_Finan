# Contexto de Desarrollo: Estructura Financiera Presupuestal y Especificación de Pivoteo (BI / ERP)

## 1. Propósito y Filosofía del Diseño

El objetivo de este documento es definir la especificación técnica y funcional para la construcción del catálogo de partidas presupuestales de personal y la lógica de renderizado dinámico en reportes (Business Intelligence / ERP).

### Principios Fundamentales:
1. **Enfoque Presupuestal y de Flujo de Caja:** La estructura prioriza la disponibilidad financiera, la liquidez y la separación entre costos directos/indirectos sobre las reglas contables impositivas.
2. **Independencia del Plan Contable:** Se evitan códigos o nomenclaturas del Plan Contable General Empresarial (PCGE - Elemento 6) para evitar rigidez financiera.
3. **Pivoteo Multidimensional:** La codificación sigue un estándar jerárquico simétrico que permite al sistema colapsar, expandir y reordenar las ramas en dos vistas principales:
   * **Vista A (Estructura Base / Financiera):** Concepto de Gasto ➔ Clasificación Operativa ➔ Puesto / Cargo.
   * **Vista B (Vista Pivote / Gestión de Personas):** Puesto / Cargo ➔ Conceptos de Gasto Asociados.

---

## 2. Estructura Financiera de Partidas (Modelo Base)

### 2.1 Jerarquía de Codificación
La codificación presupuestal utiliza un esquema jerárquico de 4 niveles:
* **Nivel 1 (Capítulo Presupuestal - 4 dígitos):** Tipo de flujo o naturaleza financiera (`1000`).
* **Nivel 2 (Grupo de Flujo - 4 dígitos):** Periodicidad y comportamiento de caja (`1100`, `1200`, `1300`).
* **Nivel 3 (Clasificación Operativa - 6 dígitos):** Agrupación por Directo (MOD) / Indirecto (CIF) (`1101.00`, `1102.00`).
* **Nivel 4 (Partida Analítica - Sufijo Único):** Puesto o posición específica (`.10`, `.11`, `.20`).

---

### 2.2 Catálogo Maestro de Partidas

#### 1000 PRESUPUESTO DE REMUNERACIONES Y BENEFICIOS

##### 1100 REMUNERACIÓN DIRECTA Y PERMANENTE (Flujo Mensual Fijo)
*Monitorea las salidas operativas fijas de cada cierre de mes.*

* **1101.00 Costo Directo - Operaciones (Mano de Obra Directa - MOD)**
  * `1101.10` Asistente de Operaciones
  * `1101.11` Operador de Campo
* **1102.00 Costo Indirecto - Supervisión / Soporte (CIF)**
  * `1102.10` Supervisor de Operaciones
  * `1102.11` Inspector de Calidad

##### 1200 BENEFICIOS DE LEY Y OBLIGACIONES SEMESTRALES (Picos de Liquidez)
*Aísla los desembolsos no mensuales para proyectar picos de demanda de caja (Mayo, Julio, Noviembre, Diciembre).*

* **1201.00 Gratificaciones y Bonificación Extraordinaria (Julio / Diciembre)**
  * `1201.10.10` Asistente de Operaciones (MOD)
  * `1201.10.20` Supervisor de Operaciones (CIF)
* **1202.00 Depósitos de CTS (Mayo / Noviembre)**
  * `1202.10.10` Asistente de Operaciones (MOD)
  * `1202.10.20` Supervisor de Operaciones (CIF)

##### 1300 REMUNERACIÓN VARIABLE Y EVENTUAL (Flujo Contingente)
*Presupuesto asignado a consumo condicionado o variable.*

* **1301.00 Bonos por Desempeño y Horas Extras**
  * `1301.10` Asistente de Operaciones
  * `1301.11` Supervisor de Operaciones
* **1302.00 Asignación Familiar y Movilidad**
  * `1302.10` Asistente de Operaciones
  * `1302.11` Supervisor de Operaciones

---

## 3. Especificación Técnica para Reportes: Lógica de Pivoteo (BI / ERP)

Para lograr que el sistema reordene el árbol de información en tiempo de ejecución sin alterar la base de datos, el motor de reportes o la base de datos (SQL / DAX / Python) debe manejar la dimensión del **Puesto / Cargo** mediante el **Sufijo Único Identificador**.

### 3.1 Mapeo de Identificadores (Sufijos de Puesto)
* Sufijo **`.10`**: Asistente de Operaciones
* Sufijo **`.11`**: Operador de Campo / Inspector de Calidad (según rama)
* Sufijo **`.20`**: Supervisor de Operaciones

---

### 3.2 Lógica de Transformación (Query / Algoritmo de Pivoteo)

Al registrar una línea de ejecución presupuestal, la tabla de hechos almacena las siguientes llaves dimensionales:

```json
{
  "id_transaccion": "TX-90821",
  "codigo_partida": "1101.10",
  "monto": 2500.00,
  "periodo": "2026-08",
  "dim_concepto": "Sueldo Base Mensual",
  "dim_puesto_sufijo": ".10",
  "dim_puesto_nombre": "Asistente de Operaciones",
  "dim_clasificacion": "MOD - Costo Directo"
}