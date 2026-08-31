"""Modelos de dominio para el presupuesto modular."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CuentaConac:
    codigo: str
    descripcion: str
    nivel: int
    categoria: Optional[str] = None


@dataclass
class PresupuestoVenta:
    producto: str
    unidades: float
    precio_unitario: float
    ingreso_total: float = field(init=False)

    def __post_init__(self) -> None:
        self.ingreso_total = self.unidades * self.precio_unitario


@dataclass
class PresupuestoProduccion:
    ventas: float
    inventario_final: float
    inventario_inicial: float

    @property
    def unidades_a_producir(self) -> float:
        return self.ventas + self.inventario_final - self.inventario_inicial


@dataclass
class PartidaPresupuestal:
    codigo: str
    descripcion: str
    importe: float
    responsable: str
    parent_codigo: Optional[str] = None
    categoria: Optional[str] = None


@dataclass
class BudgetModel:
    nombre: str = ""
    ejercicio: int = 0
    estructura_madre: Optional[str] = None
    estructura_estandar: str = "CONAC"
    aprobado: bool = False
    aprobado_por: Optional[str] = None
    cuentas: Dict[str, CuentaConac] = field(default_factory=dict)
    partidas: Dict[str, PartidaPresupuestal] = field(default_factory=dict)
    ventas: List[PresupuestoVenta] = field(default_factory=list)
    produccion: Optional[PresupuestoProduccion] = None
    compras: Dict[str, float] = field(default_factory=dict)
    costos: Dict[str, float] = field(default_factory=dict)

    def agregar_cuenta(self, cuenta: CuentaConac) -> None:
        self.cuentas[cuenta.codigo] = cuenta

    def agregar_venta(self, venta: PresupuestoVenta) -> None:
        self.ventas.append(venta)

    def definir_produccion(self, produccion: PresupuestoProduccion) -> None:
        self.produccion = produccion
