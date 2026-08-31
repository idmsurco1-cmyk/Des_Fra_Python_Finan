"""Utilidades generales del proyecto."""

from typing import Iterable, List


def redondear(valor: float, decimales: int = 2) -> float:
    return round(float(valor), decimales)


def sumar(valores: Iterable[float]) -> float:
    return sum(float(v) for v in valores)


def validar_positivo(valor: float, nombre: str) -> None:
    if valor < 0:
        raise ValueError(f"{nombre} no puede ser negativo.")
