"""Análisis de desviaciones real vs presupuestado."""


class AnalisisDesviaciones:
    """Compara valores reales con valores presupuestados."""

    def __init__(self) -> None:
        self.resultados = []

    def calcular_desviacion(self, presupuestado: float, real: float) -> float:
        return real - presupuestado

    def clasificar(self, desviacion: float) -> str:
        if desviacion > 0:
            return "Desfavorable"
        if desviacion < 0:
            return "Favorable"
        return "Sin variación"
