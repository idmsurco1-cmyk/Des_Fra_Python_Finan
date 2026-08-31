"""Lógica para compras de materia prima."""

from core.utils import validar_positivo


class ModuloCompras:
    """Calcula la necesidad de compra de materiales."""

    def __init__(self) -> None:
        self.compras = {}

    def calcular_necesidad(
        self,
        unidades_producidas: float,
        estandar_uso: float,
        inventario_final: float,
        inventario_inicial: float,
    ) -> float:
        validar_positivo(unidades_producidas, "Unidades producidas")
        necesidad = (unidades_producidas * estandar_uso) + inventario_final - inventario_inicial
        return necesidad

    def calcular_costo(self, necesidad: float, precio_unitario: float) -> float:
        validar_positivo(precio_unitario, "Precio unitario")
        return necesidad * precio_unitario
