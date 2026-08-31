import unittest

from app.backend import PresupuestoApi


class BackendTest(unittest.TestCase):
    def test_crea_presupuesto_y_devuelve_matriz(self) -> None:
        api = PresupuestoApi()
        creado = api.crear_presupuesto(
            {"nombre": "Presupuesto API", "ejercicio": 2026, "rol": "Lider de Area"}
        )
        presupuesto_id = creado["id"]

        api.seleccionar_madre(presupuesto_id, "2000")
        api.agregar_partida(
            presupuesto_id,
            {"codigo": "2111", "descripcion": "Papeleria", "importe": 1250},
        )
        matriz = api.matriz(presupuesto_id)

        self.assertEqual(matriz["estructura_madre"], "2000")
        self.assertEqual(matriz["filas"][0]["codigo"], "2000")
        self.assertEqual(matriz["filas"][0]["importe"], 1250)

    def test_rechaza_partida_de_otro_capitulo(self) -> None:
        api = PresupuestoApi()
        presupuesto_id = api.crear_presupuesto({"nombre": "Prueba", "ejercicio": 2026})["id"]
        api.seleccionar_madre(presupuesto_id, "2000")

        with self.assertRaises(ValueError):
            api.agregar_partida(
                presupuesto_id,
                {"codigo": "3111", "descripcion": "Servicio", "importe": 100},
            )

    def test_direccion_general_puede_aprobar_presupuesto(self) -> None:
        api = PresupuestoApi()
        presupuesto_id = api.crear_presupuesto(
            {"nombre": "Aprobación", "ejercicio": 2026}, "Lider de Area"
        )["id"]
        api.seleccionar_madre(presupuesto_id, "2000")
        api.agregar_partida(
            presupuesto_id,
            {"codigo": "2111", "descripcion": "Material", "importe": 100},
        )

        resultado = api.aprobar(presupuesto_id, "direccion.general", "Direccion General")

        self.assertTrue(resultado["aprobado"])
        self.assertEqual(resultado["aprobado_por"], "direccion.general")


if __name__ == "__main__":
    unittest.main()
