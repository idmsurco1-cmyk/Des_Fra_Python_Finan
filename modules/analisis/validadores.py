"""Validadores y reglas de negocio del presupuesto."""


class ValidadorPresupuesto:
    """Valida inconsistencias básicas en la proyección."""

    @staticmethod
    def validar_inventario(inventario_final: float, inventario_inicial: float) -> bool:
        return inventario_final >= 0 and inventario_inicial >= 0

    @staticmethod
    def validar_ventas(ventas: float) -> bool:
        return ventas >= 0
