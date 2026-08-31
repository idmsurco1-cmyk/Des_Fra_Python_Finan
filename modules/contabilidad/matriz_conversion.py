"""Matriz de conversión entre cuentas presupuestarias y cuentas contables."""

from typing import Dict


class MatrizConversion:
    """Mapea partidas de presupuesto hacia cuentas del sistema financiero."""

    def __init__(self) -> None:
        self.mapeo: Dict[str, str] = {}

    def registrar_relacion(self, partida: str, cuenta_contable: str) -> None:
        self.mapeo[partida] = cuenta_contable

    def obtener_cuenta_contable(self, partida: str) -> str:
        if partida not in self.mapeo:
            raise KeyError(f"No existe relación contable para la partida {partida}.")
        return self.mapeo[partida]
