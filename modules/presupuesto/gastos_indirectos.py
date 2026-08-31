"""Lógica de costos indirectos y presupuesto flexible."""


class ModuloGastosIndirectos:
    """Modelo flexible: Y = a + bx."""

    def __init__(self, costo_fijo: float, costo_variable_unitario: float) -> None:
        self.costo_fijo = costo_fijo
        self.costo_variable_unitario = costo_variable_unitario

    def calcular(self, nivel_actividad: float) -> float:
        return self.costo_fijo + (self.costo_variable_unitario * nivel_actividad)
