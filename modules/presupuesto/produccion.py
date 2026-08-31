"""Lógica de producción."""

from core.models import BudgetModel, PresupuestoProduccion


class ModuloProduccion:
    """Calcula unidades a producir usando la fórmula base."""

    def __init__(self, model: BudgetModel) -> None:
        self.model = model

    def calcular(self, ventas: float, inventario_final: float, inventario_inicial: float) -> PresupuestoProduccion:
        produccion = PresupuestoProduccion(
            ventas=ventas,
            inventario_final=inventario_final,
            inventario_inicial=inventario_inicial,
        )
        self.model.definir_produccion(produccion)
        return produccion
