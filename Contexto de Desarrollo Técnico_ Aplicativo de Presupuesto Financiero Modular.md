### Informe Técnico: Arquitectura, Lógica y Reglas de Negocio del Aplicativo Presupuestario Modular

#### 1\. Introducción y Arquitectura General del Sistema

El diseño de este aplicativo presupuestario modular trasciende la mera captura de cifras; se proyecta como un ecosistema de gestión estratégica diseñado para mitigar la incertidumbre económica y reducir la probabilidad de resultados adversos. Desde una perspectiva de arquitectura de software, el sistema opera como un "mapa de camino" que normaliza la visión financiera de la organización, permitiendo que cada decisión operativa esté alineada con las metas superiores de crecimiento.

##### Pipeline de Consolidación Presupuestal y Estado de Datos

La arquitectura se basa en un flujo de datos secuencial donde el  **Presupuesto Maestro**  actúa como el orquestador principal. El proceso inicia con la captura atómica en el presupuesto de ventas, que funciona como el disparador (trigger) de todo el pipeline. Los datos fluyen hacia el presupuesto de producción para equilibrar la demanda con los niveles de inventario, activando posteriormente los sub-servicios de requerimientos de materias primas y programación de mano de obra directa. Esta trazabilidad asegura que la asignación de recursos responda exclusivamente a necesidades operativas validadas, manteniendo la integridad transacional en toda la cadena.

##### Lógica de Agregación: La Metáfora de la Matryoshka

El sistema implementa una estructura de niveles de desagregación basada en la lógica de las muñecas Matryoshka, vinculada directamente a la jerarquía de cuentas de 4 dígitos. Las  **Subpartidas (Partidas Específicas)**  representan el nivel de captura de datos más granulado. Técnicamente, estas funcionan como contenedores dinámicos que inician pipelines de cálculo, consolidando y agregando información hacia niveles superiores:  **Partida Genérica** ,  **Concepto**  y  **Capítulo** . Este modelo garantiza que cualquier modificación en el dato atómico se propague de forma consistente a través de toda la estructura jerárquica, asegurando la coherencia en los informes consolidados.

##### Integración de Bloques Operativos y Financieros

El aplicativo transforma variables operativas (unidades, horas-hombre, estándares de uso) en estados financieros proyectados mediante una capa de lógica de negocios que integra el Estado de Resultados, el Flujo de Efectivo y el Balance General.**Capa de Valor ("So What?"):**  La interdependencia técnica entre el presupuesto de operación y el financiero permite anticipar la solvencia de la empresa ante compromisos futuros. Al modelar estos escenarios, la arquitectura permite identificar desfases de liquidez antes de que ocurran, transformando el sistema de una herramienta de registro en un motor de simulación de supervivencia y crecimiento empresarial.Esta arquitectura requiere de una estructura de cuentas normalizada para garantizar que cada registro se inserte en el nodo correcto de la base de datos presupuestal.

#### 2\. Módulo de Codificación y Armonización de Cuentas (Estándar CONAC)

Para lograr un sistema de contabilidad y presupuestación robusto, es imperativo adoptar el estándar del Consejo Nacional de Armonización Contable (CONAC). Esta adopción técnica no solo facilita la fiscalización y transparencia, sino que establece principios técnicos comunes para medir la eficiencia del gasto mediante una estructura de datos estandarizada.

##### Estructura Jerárquica y Normalización

La lógica de codificación se desagrega en cuatro niveles técnicos fundamentales, asegurando la integridad referencial:

1. **Capítulo (X000):**  Máximo nivel de agregación de conjuntos homogéneos de bienes y servicios.  
2. **Concepto (XX00):**  Subconjuntos que desglosan los rubros de cada capítulo.  
3. **Partida Genérica (XXX0):**   **Nivel de armonización obligatoria**  para todos los entes, permitiendo la comparabilidad de datos.  
4. **Partida Específica (XXXX):**  Apertura dinámica que permite a la administración generar subcategorías según sus necesidades específicas de control.

##### Catálogo de Objetos del Gasto (Estructura de Capítulos)

El sistema debe estar parametrizado con los nueve capítulos fundamentales definidos por el CONAC:

* **1000 Servicios Personales:**  (Ej. 1100 Remuneraciones Permanentes).  
* **2000 Materiales y Suministros:**  (Ej. 2100 Materiales de Administración y Artículos Oficiales).  
* **3000 Servicios Generales:**  (Servicios básicos, arrendamientos, servicios profesionales).  
* **4000 Transferencias, Asignaciones, Subsidios y Otras Ayudas.**  
* **5000 Bienes Muebles, Inmuebles e Intangibles.**  
* **6000 Inversión Pública.**  
* **7000 Inversiones Financieras y Otras Provisiones.**  
* **8000 Participaciones y Aportaciones.**  
* **9000 Deuda Pública.**

##### Reglas de Negocio: Devengo y Matriz de Conversión

El motor contable opera bajo la  **base acumulativa**  (contabilización por devengo), registrando transacciones en el momento de su realización técnica, independientemente del flujo de caja. El componente crítico para la integración es la  **Matriz de Conversión** , que permite la interrelación automática entre los clasificadores presupuestarios y las cuentas patrimoniales.**Capa de Valor ("So What?"):**  Esta estructura garantiza la generación de estados financieros en tiempo real. La Matriz de Conversión elimina los silos de información, asegurando que cada peso presupuestado tenga un reflejo automático en la contabilidad, lo que permite una rendición de cuentas transparente y una toma de decisiones basada en la situación patrimonial líquida actual.Esta estandarización de cuentas provee las variables necesarias para alimentar los algoritmos de cálculo financiero del aplicativo.

#### 3\. Programación de la Lógica y Fórmulas Financieras

La precisión del aplicativo depende de su capacidad para transformar datos históricos y supuestos de mercado en proyecciones matemáticas rigurosas, sustituyendo la intuición por modelos de cálculo validados.

##### Algoritmos de Producción y Suministros

El sistema implementa las siguientes lógicas deterministas para el cálculo de necesidades operativas:**Presupuesto de Producción:**  
Unidades a Producir \= Ventas Presupuestadas \+ Inventario Final Deseado \- Inventario Inicial Estimado

**Presupuesto de Compras de Materia Prima:**  
Necesidad de Compra \= (Volumen de Producción \* Estándar de Uso) \+ Inventario Final Deseado \- Inventario Inicial Estimado  
Costo de Compra \= Necesidad de Compra \* Precio Unitario Estimado

##### Implementación del Presupuesto Flexible

Para los Gastos Indirectos de Fabricación (GIF), el sistema programa la fórmula del presupuesto flexible para modelar el comportamiento del gasto ante variaciones en la carga de trabajo: Y \= a \+ bx

* Y: Gasto indirecto total proyectado.  
* a: Costos fijos (constantes estructurales).  
* b: Costo variable unitario (coeficiente de actividad).  
* x: Nivel de actividad (volumen de producción).

##### Lógica de Costos y Punto de Equilibrio

Es obligatoria la distinción técnica entre costos fijos y variables. Esta parametrización permite al sistema identificar la estructura de costos de cada unidad producida.**Capa de Valor ("So What?"):**  La configuración dinámica de estas variables permite el cálculo automático del punto de equilibrio (Break-Even). Esto otorga a la gerencia la capacidad de optimizar el aprovechamiento de recursos y prever la rentabilidad ante cambios en la demanda, evitando el compromiso de recursos que la operación aún no es capaz de generar.La efectividad de estas fórmulas depende de un esquema de gobernanza que valide la integridad de los datos de entrada.

#### 4\. Módulo de Gobernanza, Roles y Validación de Datos

Un aplicativo financiero es tan confiable como los procesos humanos y técnicos que lo alimentan. La descentralización de la responsabilidad presupuestal es una medida técnica para aumentar la precisión de los datos.

##### Control de Accesos y Delegación Operativa

El sistema debe implementar un control de acceso basado en roles (RBAC), donde cada líder de área es el dueño (owner) de su presupuesto individual. El diseño debe prohibir la edición centralizada de presupuestos operativos por parte de la Dirección General.**Capa de Valor ("So What?"):**  Concentrar la responsabilidad en la alta dirección es un error de diseño que genera desconexión operativa. La delegación fomenta la mejora continua, ya que los líderes de área poseen el conocimiento del "día a día" y pueden identificar eficiencias u optimizaciones en el uso de insumos que la dirección general ignora.

##### Filtros de Validación y Mitigación de Sesgos

Para evitar la sobreestimación de ingresos, el aplicativo debe integrar validadores lógicos:

* **Validadores Estadísticos:**  Comparación automática contra proyecciones basadas en promedios históricos frente a estimaciones subjetivas.  
* **Alertas de Desviación:**  Notificaciones cuando la proyección de ventas supera la desviación estándar histórica sin una justificación técnica cargada en el sistema.

##### Análisis de Desviaciones (Real vs. Presupuestado)

El sistema debe realizar comparativas mensuales de ejecución. La lógica de control debe identificar variaciones favorables y desfavorables en tiempo real, permitiendo ajustes dinámicos.**Capa de Valor ("So What?"):**  Este análisis transforma el presupuesto de una herramienta de control punitivo en un mecanismo de ajuste oportuno. Al monitorear desviaciones en tiempo real, la empresa puede reaccionar a cambios en el mercado con agilidad, convirtiendo la gestión financiera en un reto profesional para los gerentes.Estos controles se asientan sobre un modelo de datos diseñado para la integridad transaccional.

#### 5\. Modelado de Datos (Esquema Entidad-Relación Sugerido)

Para eliminar las "hemorragias operativas" y garantizar la integridad de la información, el sistema debe basarse en un modelo de datos normalizado que elimine los silos de información donde se ocultan las ineficiencias.

##### Definición de Entidades y Restricciones Técnicas

* **Tabla**  **Catálogo\_Cuentas\_CONAC**  
* ID\_Cuenta (PK): VARCHAR, con máscara obligatoria X.X.X.X (Capítulo, Concepto, Partida Genérica, Partida Específica).  
* Descripción: VARCHAR(255).  
* Nivel\_Jerárquico: SMALLINT (1-4).  
* **Tabla**  **Cédulas\_Presupuestales**  
* ID\_Cédula (PK): INT AUTO\_INCREMENT.  
* ID\_Cuenta (FK): Referencia a la cuenta CONAC para garantizar la clasificación.  
* Standard\_Uso: DECIMAL(10,4).  
* Precio\_Unitario\_Estimado: DECIMAL(19,4).  
* **Tabla**  **Transacciones\_Reales**  
* ID\_Transacción (PK): UUID o BIGINT.  
* ID\_Cuenta (FK): Vinculación forzosa para interrelación automática.  
* Monto: DECIMAL(19,4).  
* Status: ENUM ('Devengado', 'Ejercido') para soportar la base acumulativa.  
* Fecha\_Realización: DATETIME.  
* **Tabla**  **Análisis\_Desviaciones**  
* ID\_Analisis (PK).  
* Monto\_Presupuestado vs Monto\_Ejercido: Campos calculados para disparar alertas de gobernanza.

##### Integridad y Trazabilidad

La relación entre Catálogo\_Cuentas\_CONAC y las tablas de transacciones debe ser de  **1:N**  con integridad referencial estricta. Esto asegura que ningún gasto pueda ser registrado "fuera de catálogo".**Capa de Valor ("So What?"):**  Un esquema normalizado es la única defensa técnica contra la "hemorragia operativa invisible". Al forzar que cada dato operativo y financiero resida en una estructura única y vinculada, se eliminan los silos de datos que suelen ocultar duplicidades y desperdicios. Este modelo permite que la empresa transite de una gestión basada en la "intuición" hacia una arquitectura de decisiones basada en datos concretos, convirtiendo el presupuesto en un activo estratégico de alto rendimiento profesional.  
