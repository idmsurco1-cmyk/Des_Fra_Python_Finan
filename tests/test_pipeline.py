import unittest

from core.models import BudgetModel
from modules.presupuesto.pipeline import PresupuestoPipeline


class PipelineTest(unittest.TestCase):
    def test_pipeline_consolida_escenario_base(self) -> None:
        model = PresupuestoPipeline(BudgetModel()).run()

        self.assertEqual(len(model.ventas), 2)
        self.assertIsNotNone(model.produccion)
        self.assertEqual(model.produccion.unidades_a_producir, 1550)
        self.assertEqual(model.compras["Materia prima"], 57600)
        self.assertEqual(model.costos["Mano de obra directa"], 62000)
        self.assertEqual(model.costos["Gastos indirectos"], 33600)
        self.assertEqual(model.costos["Ventas presupuestadas"], 225000)


if __name__ == "__main__":
    unittest.main()
