"""Catálogo y reglas de cuentas CONAC."""

import re
from typing import Dict

from core.models import CuentaConac


class CatalogoConac:
    """Mantiene la estructura jerárquica del estándar CONAC."""

    def __init__(self) -> None:
        self.cuentas: Dict[str, CuentaConac] = {}

    @classmethod
    def estandar(cls) -> "CatalogoConac":
        catalogo = cls()
        capitulos = {
            "1000": "Servicios personales",
            "2000": "Materiales y suministros",
            "3000": "Servicios generales",
            "4000": "Transferencias, asignaciones, subsidios y otras ayudas",
            "5000": "Bienes muebles, inmuebles e intangibles",
            "6000": "Inversión pública",
            "7000": "Inversiones financieras y otras provisiones",
            "8000": "Participaciones y aportaciones",
            "9000": "Deuda pública",
        }
        for codigo, descripcion in capitulos.items():
            catalogo.registrar_cuenta(codigo, descripcion, nivel=1)
        return catalogo

    @classmethod
    def estandar_peru(cls) -> "CatalogoConac":
        """Catálogo base empresarial con terminología del presupuesto peruano."""
        catalogo = cls()
        capitulos = {
            "1000": "Remuneraciones y obligaciones sociales",
            "2000": "Pensiones y otras prestaciones sociales",
            "3000": "Bienes y servicios",
            "4000": "Donaciones y transferencias",
            "5000": "Otros gastos",
            "6000": "Adquisición de activos no financieros",
            "7000": "Adquisición de activos financieros",
            "8000": "Servicio de la deuda pública",
        }
        for codigo, descripcion in capitulos.items():
            catalogo.registrar_cuenta(codigo, descripcion, nivel=1)
        return catalogo

    def registrar_cuenta(
        self,
        codigo: str,
        descripcion: str,
        nivel: int,
        categoria: str | None = None,
    ) -> None:
        self.cuentas[codigo] = CuentaConac(
            codigo=codigo,
            descripcion=descripcion,
            nivel=nivel,
            categoria=categoria,
        )

    def validar_codigo(self, codigo: str) -> bool:
        return bool(re.fullmatch(r"\d{4}(?:\.\d+)*", codigo))

    def capitulos(self) -> list[CuentaConac]:
        return [cuenta for cuenta in self.cuentas.values() if cuenta.nivel == 1]

    def obtener_cuenta(self, codigo: str) -> CuentaConac:
        if codigo not in self.cuentas:
            raise KeyError(f"La cuenta {codigo} no existe en el catálogo.")
        return self.cuentas[codigo]
