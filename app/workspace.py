"""Entorno de trabajo para crear y analizar un presupuesto."""

from dataclasses import dataclass, field
from datetime import date
import math
import re
import sys
from pathlib import Path
from typing import TypedDict
from uuid import uuid4

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.models import BudgetModel, MovimientoCaja, PartidaPresupuestal
from modules.contabilidad.conac import CatalogoConac


class PartidaReporte(TypedDict):
    codigo: str
    descripcion: str
    importe: float
    parent_codigo: str | None
    clasificacion_financiera: str


class BloqueCategoria(TypedDict):
    total: float
    partidas: list[PartidaReporte]
    capitulos: dict[str, float]


class BloquePuesto(TypedDict):
    total: float
    partidas: list[PartidaReporte]
    puesto: str


@dataclass
class EntornoPresupuestario:
    """Gestiona la estructura madre y sus partidas del presupuesto activo."""

    model: BudgetModel
    catalogo: CatalogoConac
    rol: str
    saldo_inicial: float = 0.0
    presupuestos_mensuales: dict[str, dict[int, float]] = field(default_factory=dict)
    ingresos_proyectados: dict[int, float] = field(default_factory=dict)
    movimientos_caja: list[MovimientoCaja] = field(default_factory=list)

    @classmethod
    def iniciar(cls, nombre: str, ejercicio: int, rol: str) -> "EntornoPresupuestario":
        return cls(
            model=BudgetModel(nombre=nombre, ejercicio=ejercicio),
            catalogo=CatalogoConac.estandar(),
            rol=rol,
        )

    @classmethod
    def iniciar_estandar_peru(cls, nombre: str, ejercicio: int, rol: str) -> "EntornoPresupuestario":
        entorno = cls(
            model=BudgetModel(nombre=nombre, ejercicio=ejercicio, estructura_estandar="Perú"),
            catalogo=CatalogoConac.estandar_peru(),
            rol=rol,
        )
        return entorno

    def seleccionar_estructura_madre(self, codigo: str) -> None:
        cuenta = self.catalogo.obtener_cuenta(codigo)
        if cuenta.nivel != 1:
            raise ValueError("La estructura madre debe ser un capítulo CONAC.")
        self.model.estructura_madre = codigo

    def _generar_codigo_correlativo(self, parent_codigo: str | None = None) -> str:
        contenedor = parent_codigo or self.model.estructura_madre
        if contenedor is None:
            raise ValueError("Selecciona un contenedor de la estructura estándar.")

        cuenta_contenedora = self.catalogo.cuentas.get(contenedor)
        if cuenta_contenedora is not None and cuenta_contenedora.nivel == 1:
            siguiente = 1
            while True:
                candidato = f"{contenedor[:1]}{siguiente:03d}"
                if candidato not in self.model.partidas and not candidato.endswith("0"):
                    return candidato
                siguiente += 1

        usados = [
            codigo for codigo in self.model.partidas
            if codigo.startswith(f"{contenedor}.") and len(codigo.split(".")) == len(contenedor.split(".")) + 1
        ]
        numeradores: list[int] = []
        for codigo in usados:
            sufijo = codigo.split(".")[-1]
            if sufijo.isdigit():
                numeradores.append(int(sufijo))

        siguiente = 10 if not numeradores else max(numeradores) + 10
        while True:
            candidato = f"{contenedor}.{siguiente}"
            if candidato not in self.model.partidas:
                return candidato
            siguiente += 10

    def agregar_partida(
        self,
        codigo: str,
        descripcion: str,
        importe: float,
        parent_codigo: str | None = None,
        categoria: str | None = None,
        clasificacion_financiera: str = "OPEX",
    ) -> PartidaPresupuestal:
        if self.rol not in {"Lider de Area", "Director Financiero"}:
            raise PermissionError("El rol actual no puede crear partidas.")
        if self.model.estructura_madre is None and parent_codigo is None:
            raise ValueError("Selecciona un contenedor de la estructura estándar.")

        codigo = str(codigo).strip() if codigo is not None else ""
        descripcion = str(descripcion).strip()
        if not descripcion:
            raise ValueError("La descripción no puede quedar vacía.")
        importe = self._validar_importe(importe, "El importe")
        clasificacion_financiera = self._validar_clasificacion(clasificacion_financiera)
        if not codigo:
            codigo = self._generar_codigo_correlativo(parent_codigo or self.model.estructura_madre)

        if not re.fullmatch(r"\d{4}(?:\.\d+)*", codigo):
            raise ValueError("El código debe usar cuatro dígitos y niveles opcionales con numeración decimal, por ejemplo 1001.1 o 1001.1.1.")
        raiz = (parent_codigo or self.model.estructura_madre or codigo)[:4]
        if self.model.estructura_madre and codigo[:1] != self.model.estructura_madre[:1]:
            raise ValueError("La partida debe pertenecer al capítulo madre seleccionado.")
        if raiz[:1] not in {cuenta.codigo[:1] for cuenta in self.catalogo.capitulos()}:
            raise ValueError("La partida debe pertenecer al capítulo madre seleccionado.")
        if codigo in self.model.partidas:
            raise ValueError("El código de partida ya existe.")
        if "." in codigo:
            inferred_parent = codigo.rsplit(".", 1)[0]
            parent_codigo = parent_codigo or inferred_parent
            if parent_codigo not in self.model.partidas and parent_codigo not in self.catalogo.cuentas:
                raise ValueError("La partida padre debe existir antes de crear una subpartida.")
        elif codigo.endswith("0"):
            raise ValueError("La partida específica no puede terminar en 0.")
        elif parent_codigo is None:
            parent_codigo = self.model.estructura_madre
        if parent_codigo and parent_codigo != self.model.estructura_madre and parent_codigo not in self.catalogo.cuentas:
            if parent_codigo not in self.model.partidas:
                raise ValueError("La partida padre no existe.")
            if not codigo.startswith(f"{parent_codigo}."):
                raise ValueError("La subpartida debe pertenecer a su partida padre.")
        partida = PartidaPresupuestal(
            codigo, descripcion, importe, self.rol, parent_codigo, categoria, clasificacion_financiera
        )
        self.model.partidas[codigo] = partida
        return partida

    def actualizar_partida(
        self,
        codigo: str,
        descripcion: str | None = None,
        importe: float | None = None,
        parent_codigo: str | None = None,
        categoria: str | None = None,
        clasificacion_financiera: str | None = None,
    ) -> PartidaPresupuestal:
        if codigo not in self.model.partidas:
            raise ValueError("La partida no existe.")
        partida = self.model.partidas[codigo]

        nueva_descripcion = partida.descripcion
        if descripcion is not None:
            descripcion = str(descripcion).strip()
            if not descripcion:
                raise ValueError("La descripción no puede quedar vacía.")
            nueva_descripcion = descripcion

        nuevo_importe = partida.importe
        if importe is not None:
            importe = self._validar_importe(importe, "El importe")
            asignado = sum(self.presupuestos_mensuales.get(codigo, {}).values())
            if asignado > importe:
                raise ValueError("El presupuesto anual no puede ser menor que lo programado por mes.")
            nuevo_importe = importe

        nueva_categoria = partida.categoria
        if categoria is not None:
            nueva_categoria = str(categoria).strip() or None

        nuevo_padre = partida.parent_codigo
        if parent_codigo is not None:
            parent_codigo = str(parent_codigo).strip() or None
            if parent_codigo and parent_codigo not in self.model.partidas and parent_codigo not in self.catalogo.cuentas:
                raise ValueError("La partida padre no existe.")
            if parent_codigo and not codigo.startswith(f"{parent_codigo}.") and parent_codigo != self.model.estructura_madre:
                raise ValueError("La subpartida debe pertenecer a su partida padre.")
            nuevo_padre = parent_codigo

        nueva_clasificacion = partida.clasificacion_financiera
        if clasificacion_financiera is not None:
            nueva_clasificacion = self._validar_clasificacion(clasificacion_financiera)
            if any(
                movimiento.partida_codigo == codigo
                and movimiento.clasificacion_financiera != nueva_clasificacion
                for movimiento in self.movimientos_caja
            ):
                raise ValueError("No se puede cambiar la clasificación de una partida con movimientos asociados.")

        partida.descripcion = nueva_descripcion
        partida.importe = nuevo_importe
        partida.categoria = nueva_categoria
        partida.parent_codigo = nuevo_padre
        partida.clasificacion_financiera = nueva_clasificacion
        return partida

    @staticmethod
    def _validar_importe(importe: float, nombre: str) -> float:
        valor = float(importe)
        if not math.isfinite(valor) or valor < 0:
            raise ValueError(f"{nombre} debe ser un importe finito mayor o igual a cero.")
        return valor

    @staticmethod
    def _validar_clasificacion(clasificacion: str) -> str:
        valor = str(clasificacion).strip().upper()
        if valor not in {"OPEX", "CAPEX"}:
            raise ValueError("La clasificación financiera debe ser OPEX o CAPEX.")
        return valor

    def establecer_saldo_inicial(self, importe: float) -> float:
        self.saldo_inicial = self._validar_importe(importe, "El saldo inicial")
        return self.saldo_inicial

    def programar_partida_mensual(self, codigo: str, mes: int, importe: float) -> dict[str, object]:
        if codigo not in self.model.partidas:
            raise ValueError("La partida presupuestaria no existe.")
        mes = int(mes)
        if mes < 1 or mes > 12:
            raise ValueError("El mes debe estar entre 1 y 12.")
        importe = self._validar_importe(importe, "El importe mensual")
        asignaciones = self.presupuestos_mensuales.setdefault(codigo, {})
        total_nuevo = sum(asignaciones.values()) - asignaciones.get(mes, 0.0) + importe
        if total_nuevo > self.model.partidas[codigo].importe:
            raise ValueError("La programación mensual supera el importe anual de la partida.")
        asignaciones[mes] = importe
        return {"codigo": codigo, "mes": mes, "importe": importe}

    def programar_ingreso_mensual(self, mes: int, importe: float) -> dict[str, object]:
        mes = int(mes)
        if mes < 1 or mes > 12:
            raise ValueError("El mes debe estar entre 1 y 12.")
        importe = self._validar_importe(importe, "El ingreso proyectado")
        self.ingresos_proyectados[mes] = importe
        return {"mes": mes, "importe": importe}

    def registrar_movimiento_caja(
        self,
        fecha: str,
        tipo: str,
        descripcion: str,
        importe: float,
        clasificacion_financiera: str | None = None,
        partida_codigo: str | None = None,
    ) -> MovimientoCaja:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(fecha)):
            raise ValueError("La fecha debe tener formato AAAA-MM-DD.")
        try:
            fecha_movimiento = date.fromisoformat(str(fecha))
        except ValueError as error:
            raise ValueError("La fecha debe tener formato AAAA-MM-DD.") from error
        if fecha_movimiento.year != self.model.ejercicio:
            raise ValueError("El movimiento debe pertenecer al ejercicio del presupuesto.")
        tipo = str(tipo).strip().lower()
        if tipo not in {"ingreso", "egreso"}:
            raise ValueError("El tipo de movimiento debe ser ingreso o egreso.")
        descripcion = str(descripcion).strip()
        if not descripcion:
            raise ValueError("La descripción del movimiento es obligatoria.")
        importe = self._validar_importe(importe, "El importe del movimiento")
        if importe == 0:
            raise ValueError("El importe del movimiento debe ser mayor que cero.")

        if tipo == "ingreso":
            clasificacion = "INGRESO"
            if partida_codigo:
                raise ValueError("Un ingreso no puede asociarse a una partida de gasto.")
        else:
            clasificacion = self._validar_clasificacion(clasificacion_financiera or "")
            if partida_codigo:
                partida = self.model.partidas.get(partida_codigo)
                if partida is None:
                    raise ValueError("La partida asociada no existe.")
                if partida.clasificacion_financiera != clasificacion:
                    raise ValueError("La clasificación del movimiento debe coincidir con la partida.")

        movimiento = MovimientoCaja(
            id=str(uuid4()),
            fecha=fecha_movimiento.isoformat(),
            tipo=tipo,
            descripcion=descripcion,
            importe=importe,
            clasificacion_financiera=clasificacion,
            partida_codigo=partida_codigo or None,
        )
        self.movimientos_caja.append(movimiento)
        return movimiento

    def flujo_caja(self) -> dict[str, object]:
        filas: list[dict[str, object]] = []
        saldo_proyectado = self.saldo_inicial
        saldo_real = self.saldo_inicial
        total_ingreso_proyectado = 0.0
        total_opex_programado = 0.0
        total_capex_programado = 0.0
        total_ingreso_real = 0.0
        total_egreso_real = 0.0
        for mes in range(1, 13):
            egresos = {"OPEX": 0.0, "CAPEX": 0.0}
            for codigo, importes in self.presupuestos_mensuales.items():
                partida = self.model.partidas[codigo]
                egresos[partida.clasificacion_financiera] += importes.get(mes, 0.0)
            ingreso_proyectado = self.ingresos_proyectados.get(mes, 0.0)
            ingresos_reales = 0.0
            egresos_reales = {"OPEX": 0.0, "CAPEX": 0.0}
            for movimiento in self.movimientos_caja:
                fecha_movimiento = date.fromisoformat(movimiento.fecha)
                if fecha_movimiento.month != mes:
                    continue
                if movimiento.tipo == "ingreso":
                    ingresos_reales += movimiento.importe
                else:
                    egresos_reales[movimiento.clasificacion_financiera] += movimiento.importe

            egreso_proyectado = egresos["OPEX"] + egresos["CAPEX"]
            egreso_real = egresos_reales["OPEX"] + egresos_reales["CAPEX"]
            flujo_neto_proyectado = ingreso_proyectado - egreso_proyectado
            flujo_neto_real = ingresos_reales - egreso_real
            total_ingreso_proyectado += ingreso_proyectado
            total_opex_programado += egresos["OPEX"]
            total_capex_programado += egresos["CAPEX"]
            total_ingreso_real += ingresos_reales
            total_egreso_real += egreso_real
            saldo_proyectado += flujo_neto_proyectado
            saldo_real += flujo_neto_real
            filas.append({
                "mes": mes,
                "ingresos_proyectados": ingreso_proyectado,
                "presupuesto_opex": egresos["OPEX"],
                "presupuesto_capex": egresos["CAPEX"],
                "egresos_presupuestados": egreso_proyectado,
                "flujo_neto_proyectado": flujo_neto_proyectado,
                "saldo_proyectado": saldo_proyectado,
                "ingresos_reales": ingresos_reales,
                "egresos_opex_reales": egresos_reales["OPEX"],
                "egresos_capex_reales": egresos_reales["CAPEX"],
                "egresos_reales": egreso_real,
                "flujo_neto_real": flujo_neto_real,
                "saldo_real": saldo_real,
            })

        presupuesto_anual = {"OPEX": 0.0, "CAPEX": 0.0}
        sin_programar = 0.0
        for partida in self.model.partidas.values():
            presupuesto_anual[partida.clasificacion_financiera] += partida.importe
            programado = sum(self.presupuestos_mensuales.get(partida.codigo, {}).values())
            sin_programar += max(partida.importe - programado, 0.0)

        return {
            "ejercicio": self.model.ejercicio,
            "saldo_inicial": self.saldo_inicial,
            "resumen": {
                "ingresos_proyectados": total_ingreso_proyectado,
                "opex_presupuestado": total_opex_programado,
                "capex_presupuestado": total_capex_programado,
                "opex_anual": presupuesto_anual["OPEX"],
                "capex_anual": presupuesto_anual["CAPEX"],
                "presupuesto_sin_programar": sin_programar,
                "saldo_proyectado_final": saldo_proyectado,
                "ingresos_reales": total_ingreso_real,
                "egresos_reales": total_egreso_real,
                "saldo_real_actual": saldo_real,
            },
            "partidas": [
                {
                    "codigo": partida.codigo,
                    "descripcion": partida.descripcion,
                    "importe_anual": partida.importe,
                    "clasificacion_financiera": partida.clasificacion_financiera,
                    "programacion": self.presupuestos_mensuales.get(partida.codigo, {}),
                }
                for partida in self.model.partidas.values()
            ],
            "meses": filas,
            "movimientos": [
                {
                    "id": movimiento.id,
                    "fecha": movimiento.fecha,
                    "tipo": movimiento.tipo,
                    "descripcion": movimiento.descripcion,
                    "importe": movimiento.importe,
                    "clasificacion_financiera": movimiento.clasificacion_financiera,
                    "partida_codigo": movimiento.partida_codigo,
                }
                for movimiento in self.movimientos_caja
            ],
        }

    def reporte_por_categoria(self) -> dict[str, BloqueCategoria]:
        resultado: dict[str, BloqueCategoria] = {}
        for partida in self.model.partidas.values():
            categoria = str(partida.categoria or "Sin categoría")
            bloque = resultado.setdefault(
                categoria,
                {"total": 0.0, "partidas": [], "capitulos": {}},
            )
            importe = float(partida.importe)
            bloque["total"] = float(bloque["total"]) + importe
            bloque["partidas"].append(
                {
                    "codigo": str(partida.codigo),
                    "descripcion": str(partida.descripcion),
                    "importe": importe,
                    "parent_codigo": partida.parent_codigo,
                    "clasificacion_financiera": partida.clasificacion_financiera,
                }
            )
            clave_capitulo = partida.codigo[:1] + "000"
            bloque["capitulos"][clave_capitulo] = float(bloque["capitulos"].get(clave_capitulo, 0.0)) + importe
        return resultado

    def reporte_por_vista(
        self,
        vista: str = "financiera",
    ) -> dict[str, BloqueCategoria] | dict[str, BloquePuesto]:
        if vista == "puesto":
            resultado: dict[str, BloquePuesto] = {}
            for partida in self.model.partidas.values():
                if "." not in partida.codigo:
                    continue
                clave = f".{partida.codigo.split('.')[-1]}"
                bloque = resultado.setdefault(
                    clave,
                    {"total": 0.0, "partidas": [], "puesto": partida.descripcion},
                )
                importe = float(partida.importe)
                bloque["total"] = float(bloque["total"]) + importe
                bloque["partidas"].append(
                    {
                        "codigo": str(partida.codigo),
                        "descripcion": str(partida.descripcion),
                        "importe": importe,
                        "parent_codigo": partida.parent_codigo,
                        "clasificacion_financiera": partida.clasificacion_financiera,
                    }
                )
            return resultado
        return self.reporte_por_categoria()

    def aprobar(self, usuario: str, rol: str | None = None) -> None:
        if (rol or self.rol) != "Direccion General":
            raise PermissionError("Solo Dirección General puede aprobar presupuestos.")
        if not self.model.partidas:
            raise ValueError("No se puede aprobar un presupuesto sin partidas.")
        self.model.aprobado = True
        self.model.aprobado_por = usuario

    def matriz_madre(self) -> list[dict[str, object]]:
        """Devuelve la estructura CONAC y las subpartidas anidadas con acumulados."""
        acumulados: dict[str, float] = {}
        descripciones: dict[str, str] = {}
        categorias: dict[str, str | None] = {}
        clasificaciones: dict[str, str | None] = {}
        niveles = {1: "Capítulo", 2: "Concepto", 3: "Partida genérica", 4: "Partida específica"}

        for cuenta in self.catalogo.capitulos():
            acumulados.setdefault(cuenta.codigo, 0)
            descripciones.setdefault(cuenta.codigo, cuenta.descripcion)

        for partida in self.model.partidas.values():
            if "." in partida.codigo:
                segmentos = partida.codigo.split(".")
                codigos = [".".join(segmentos[:indice]) for indice in range(1, len(segmentos) + 1)]
                base = segmentos[0]
                if re.fullmatch(r"\d{4}", base):
                    codigos.extend(
                        [
                            base[:3] + "0",
                            base[:2] + "00",
                            base[:1] + "000",
                        ]
                    )
                codigos = list(dict.fromkeys(codigos))
            else:
                codigos = [
                    partida.codigo,
                    partida.codigo[:3] + "0",
                    partida.codigo[:2] + "00",
                    partida.codigo[:1] + "000",
                ]
                codigos = list(dict.fromkeys(codigos))
            for codigo in codigos:
                acumulados[codigo] = acumulados.get(codigo, 0) + partida.importe
                descripciones.setdefault(codigo, partida.descripcion if codigo == partida.codigo else "Consolidado")
                if codigo == partida.codigo:
                    categorias[codigo] = partida.categoria
                    clasificaciones[codigo] = partida.clasificacion_financiera

        def nivel(codigo: str) -> str:
            if "." in codigo:
                return f"Subpartida nivel {len(codigo.split('.')) - 1:02d}"
            return niveles[4 - (len(codigo) - len(codigo.rstrip("0")))]

        filas = [
            {
                "codigo": codigo,
                "nivel": nivel(codigo),
                "descripcion": descripciones[codigo],
                "importe": importe,
                "parent_codigo": self._padre_de_matriz(codigo),
                "categoria": categorias.get(codigo),
                "clasificacion_financiera": clasificaciones.get(codigo),
            }
            for codigo, importe in sorted(acumulados.items())
        ]
        if self.model.estructura_madre:
            filas.sort(key=lambda fila: (fila["codigo"] != self.model.estructura_madre, fila["codigo"]))
        return filas

    def _padre_de_matriz(self, codigo: str) -> str | None:
        partida = self.model.partidas.get(codigo)
        if partida and partida.parent_codigo:
            return partida.parent_codigo
        if "." in codigo:
            return codigo.rsplit(".", 1)[0]
        if codigo in self.catalogo.cuentas:
            return None
        return codigo[:1] + "000" if len(codigo) == 4 else None