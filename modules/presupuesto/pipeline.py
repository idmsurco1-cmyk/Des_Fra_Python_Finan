"""Pipeline principal del presupuesto modular."""

from core.models import BudgetModel
from modules.presupuesto.compras import ModuloCompras
from modules.presupuesto.gastos_indirectos import ModuloGastosIndirectos
from modules.presupuesto.mano_obra import ModuloManoObra
from modules.presupuesto.produccion import ModuloProduccion
from modules.presupuesto.ventas import ModuloVentas


class PresupuestoPipeline:
    """Orquesta la secuencia general del presupuesto."""

    def __init__(self, model: BudgetModel) -> None:
        self.model = model

    def run(self) -> BudgetModel:
        """Ejecuta un escenario base y devuelve el modelo consolidado."""
        print("[PresupuestoPipeline] Iniciando flujo de presupuesto maestro.")

        ventas = ModuloVentas()
        ventas.agregar_venta("Producto A", unidades=1_000, precio_unitario=125)
        ventas.agregar_venta("Producto B", unidades=500, precio_unitario=200)
        self.model.ventas.extend(ventas.ventas)

        produccion = ModuloProduccion(self.model).calcular(
            ventas=sum(venta.unidades for venta in self.model.ventas),
            inventario_final=150,
            inventario_inicial=100,
        )

        compras = ModuloCompras()
        necesidad = compras.calcular_necesidad(
            unidades_producidas=produccion.unidades_a_producir,
            estandar_uso=2,
            inventario_final=300,
            inventario_inicial=200,
        )
        self.model.compras["Materia prima"] = compras.calcular_costo(
            necesidad=necesidad,
            precio_unitario=18,
        )

        self.model.costos["Mano de obra directa"] = ModuloManoObra().calcular_mod(
            horas=produccion.unidades_a_producir * 0.5,
            tarifa_hora=80,
        )
        self.model.costos["Gastos indirectos"] = ModuloGastosIndirectos(
            costo_fijo=15_000,
            costo_variable_unitario=12,
        ).calcular(produccion.unidades_a_producir)
        self.model.costos["Ventas presupuestadas"] = ventas.total_ingresos()

        print(f"[PresupuestoPipeline] Ventas: ${ventas.total_ingresos():,.2f}")
        print(f"[PresupuestoPipeline] Producción: {produccion.unidades_a_producir:,.0f} unidades")
        print(f"[PresupuestoPipeline] Compras: ${self.model.compras['Materia prima']:,.2f}")
        print("[PresupuestoPipeline] MVP consolidado correctamente.")
        return self.model
