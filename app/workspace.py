"""Entorno de trabajo para crear y analizar un presupuesto."""

from dataclasses import dataclass
import re
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.models import BudgetModel, PartidaPresupuestal
from modules.contabilidad.conac import CatalogoConac


@dataclass
class EntornoPresupuestario:
    """Gestiona la estructura madre y sus partidas del presupuesto activo."""

    model: BudgetModel
    catalogo: CatalogoConac
    rol: str

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

        if "." not in contenedor:
            prefijo = contenedor
            usados = [
                codigo for codigo in self.model.partidas
                if re.fullmatch(r"\d{4}", codigo) and codigo.startswith(prefijo)
            ]
            siguiente = 1
            while True:
                candidato = f"{prefijo}{siguiente:02d}" if False else None
                candidato = f"{prefijo}{siguiente:02d}"
                if candidato not in self.model.partidas and not candidato.endswith("0"):
                    return candidato
                siguiente += 1

        usados = [
            codigo for codigo in self.model.partidas
            if codigo.startswith(f"{contenedor}.") and len(codigo.split(".")) == len(contenedor.split(".")) + 1
        ]
        numeradores = []
        for codigo in usados:
            sufijo = codigo.split(".")[-1]
            if sufijo.isdigit():
                numeradores.append(int(sufijo))
        siguiente = max(numeradores, default=0) + 1
        return f"{contenedor}.{siguiente}"

    def agregar_partida(
        self,
        codigo: str,
        descripcion: str,
        importe: float,
        parent_codigo: str | None = None,
        categoria: str | None = None,
    ) -> PartidaPresupuestal:
        if self.rol not in {"Lider de Area", "Director Financiero"}:
            raise PermissionError("El rol actual no puede crear partidas.")
        if self.model.estructura_madre is None and parent_codigo is None:
            raise ValueError("Selecciona un contenedor de la estructura estándar.")

        codigo = str(codigo).strip() if codigo is not None else ""
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
        if importe < 0:
            raise ValueError("El importe no puede ser negativo.")

        partida = PartidaPresupuestal(codigo, descripcion, float(importe), self.rol, parent_codigo, categoria)
        self.model.partidas[codigo] = partida
        return partida

    def actualizar_partida(
        self,
        codigo: str,
        descripcion: str | None = None,
        importe: float | None = None,
        parent_codigo: str | None = None,
        categoria: str | None = None,
    ) -> PartidaPresupuestal:
        if codigo not in self.model.partidas:
            raise ValueError("La partida no existe.")
        partida = self.model.partidas[codigo]

        if descripcion is not None:
            descripcion = str(descripcion).strip()
            if not descripcion:
                raise ValueError("La descripción no puede quedar vacía.")
            partida.descripcion = descripcion
        if importe is not None:
            importe = float(importe)
            if importe < 0:
                raise ValueError("El importe no puede ser negativo.")
            partida.importe = importe
        if categoria is not None:
            partida.categoria = str(categoria).strip() or None
        if parent_codigo is not None:
            parent_codigo = str(parent_codigo).strip() or None
            if parent_codigo and parent_codigo not in self.model.partidas and parent_codigo not in self.catalogo.cuentas:
                raise ValueError("La partida padre no existe.")
            if parent_codigo and not codigo.startswith(f"{parent_codigo}.") and parent_codigo != self.model.estructura_madre:
                raise ValueError("La subpartida debe pertenecer a su partida padre.")
            partida.parent_codigo = parent_codigo
        return partida

    def reporte_por_categoria(self) -> dict[str, dict[str, object]]:
        resultado: dict[str, dict[str, object]] = {}
        for partida in self.model.partidas.values():
            categoria = partida.categoria or "Sin categoría"
            bloque = resultado.setdefault(
                categoria,
                {"total": 0.0, "partidas": [], "capitulos": {}},
            )
            bloque["total"] = float(bloque["total"]) + float(partida.importe)
            bloque["partidas"].append(
                {
                    "codigo": partida.codigo,
                    "descripcion": partida.descripcion,
                    "importe": partida.importe,
                    "parent_codigo": partida.parent_codigo,
                }
            )
            clave_capitulo = partida.codigo[:1] + "000"
            capitulos = bloque["capitulos"]
            if not isinstance(capitulos, dict):
                capitulos = {}
                bloque["capitulos"] = capitulos
            capitulos[clave_capitulo] = float(capitulos.get(clave_capitulo, 0.0)) + float(partida.importe)
        return resultado

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