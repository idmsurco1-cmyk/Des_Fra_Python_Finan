"""Lógica de presupuesto de ventas."""

from typing import List

from core.models import PresupuestoVenta


class ModuloVentas:
    """Calcula el presupuesto base de ventas."""

    def __init__(self) -> None:
        self.ventas: List[PresupuestoVenta] = []

    def agregar_venta(self, producto: str, unidades: float, precio_unitario: float) -> PresupuestoVenta:
        venta = PresupuestoVenta(
            producto=producto,
            unidades=unidades,
            precio_unitario=precio_unitario,
        )
        self.ventas.append(venta)
        return venta

    def total_ingresos(self) -> float:
        return sum(v.ingreso_total for v in self.ventas)
