"""Lógica de mano de obra directa."""


class ModuloManoObra:
    """Calcula costos de mano de obra directa (MOd)."""

    def __init__(self) -> None:
        self.costos = {}

    def calcular_mod(self, horas: float, tarifa_hora: float) -> float:
        return horas * tarifa_hora
