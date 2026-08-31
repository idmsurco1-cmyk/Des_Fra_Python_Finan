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

## 2. Diagrama de la Arquitectura de Datos (Representación Visual)

El siguiente esquema ilustra la relación bidireccional entre la captura de datos en el sistema (3 Dimensiones) y la capacidad de renderizar dos árboles de navegación distintos en tiempo de ejecución:

```text
               ┌─────────────────────────────────────────┐
               │    REGISTRO / FACTOR DE PLANILLA        │
               │  (Tabla de Hechos - Ejecución de Caja)  │
               └────────────────────┬────────────────────┘
                                    │
    ┌───────────────────────────────┼──────────────────────────────┐
    │                               │                              │
    ▼                               ▼                              ▼
┌─────────────────────────┐   ┌──────────────────────────┐   ┌────────────────────────┐
│ DIMENSIÓN 1: CONCEPTO   │   │ DIMENSIÓN 2: NATURALEZA  │   │ DIMENSIÓN 3: PUESTO    │
│ (Grupo de Flujo / Caja) │   │ (Costo Directo/Indirecto)│   │ (Sufijo Único Identif.)│
│ Ej: 1100, 1200, 1300    │   │ Ej: MOD, CIF             │   │ Ej: .10 (Asistente)    │
└───────────┬─────────────┘   └────────────┬─────────────┘   └───────────┬────────────┘
            │                              │                             │
            └──────────────────────────────┼─────────────────────────────┘
                                           │
                                           ▼
                    ┌─────────────────────────────────────────────┐
                    │      MOTOR DE PIVOTEO Y TRANSFORMACIÓN      │
                    │         (Power BI / DAX / SQL View)         │
                    └──────────────┬──────────────┬───────────────┘
                                   │              │
                   ┌───────────────┘              └───────────────┐
                   │ Switch = Modo Financiero                     │ Switch = Modo Puesto
                   ▼                                              ▼
┌─────────────────────────────────────────────┐┌─────────────────────────────────────────────┐
│          VISTA A: ÁRBOL FINANCIERO          ││           VISTA B: ÁRBOL PIVOTEADO          │
│                                             ││                                             │
│ 1000 Presupuesto de Personal                ││ Puesto: Asistente de Operaciones (.10)      │
│ ├── 1100 Remuneración Directa (Mensual)     ││ ├── Partida 1101.10 (Sueldo Base)           │
│ │   └── 1101.00 Costo Directo (MOD)         ││ ├── Partida 1201.10 (Gratificación)        │
│ │       └── .10 Asistente de Operaciones    ││ ├── Partida 1202.10 (CTS)                  │
│ └── 1200 Beneficios de Ley (Semestral)      ││ └── Partida 1302.10 (Asignación Fam.)      │
│     └── 1201.00 Gratificación             ││                                             │
│         └── .10 Asistente de Operaciones    ││                                             │
└─────────────────────────────────────────────┘└─────────────────────────────────────────────┘