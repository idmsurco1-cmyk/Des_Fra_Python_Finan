import unittest

from app.workspace import EntornoPresupuestario


class WorkspaceTest(unittest.TestCase):
    def test_matriz_acumula_partida_en_todos_los_niveles(self) -> None:
        entorno = EntornoPresupuestario.iniciar("Presupuesto 2026", 2026, "Lider de Area")
        entorno.seleccionar_estructura_madre("2000")
        entorno.agregar_partida("2111", "Papelería", 1000)
        entorno.agregar_partida("2121", "Material de limpieza", 500)

        matriz = {fila["codigo"]: fila for fila in entorno.matriz_madre()}

        self.assertEqual(matriz["2111"]["importe"], 1000)
        self.assertEqual(matriz["2100"]["importe"], 1500)
        self.assertEqual(matriz["2000"]["importe"], 1500)

    def test_partida_fuera_del_capitulo_madre_es_rechazada(self) -> None:
        entorno = EntornoPresupuestario.iniciar("Presupuesto 2026", 2026, "Lider de Area")
        entorno.seleccionar_estructura_madre("2000")

        with self.assertRaises(ValueError):
            entorno.agregar_partida("3111", "Servicio", 1000)

    def test_matriz_soporta_cajas_dentro_de_cajas(self) -> None:
        entorno = EntornoPresupuestario.iniciar("Presupuesto 2026", 2026, "Lider de Area")
        entorno.seleccionar_estructura_madre("1000")
        entorno.agregar_partida("1000.01", "Personal", 0)
        entorno.agregar_partida("1000.01.01", "Nómina", 0)
        entorno.agregar_partida("1000.01.01.01", "Sueldos", 500)

        matriz = {fila["codigo"]: fila for fila in entorno.matriz_madre()}

        self.assertEqual(matriz["1000.01"]["nivel"], "Subpartida nivel 01")
        self.assertEqual(matriz["1000.01.01"]["nivel"], "Subpartida nivel 02")
        self.assertEqual(matriz["1000.01.01.01"]["nivel"], "Subpartida nivel 03")
        self.assertEqual(matriz["1000"]["importe"], 500)

    def test_subpartida_de_partida_conac_acumula_en_capitulo(self) -> None:
        entorno = EntornoPresupuestario.iniciar("Presupuesto 2026", 2026, "Lider de Area")
        entorno.seleccionar_estructura_madre("1000")
        entorno.agregar_partida("1001", "Personal", 0)
        entorno.agregar_partida("1001.01", "Nómina", 500)

        matriz = {fila["codigo"]: fila for fila in entorno.matriz_madre()}

        self.assertEqual(matriz["1001.01"]["importe"], 500)
        self.assertEqual(matriz["1001"]["importe"], 500)
        self.assertEqual(matriz["1000"]["importe"], 500)

    def test_personal_consolida_sueldo_pension_y_seguro(self) -> None:
        entorno = EntornoPresupuestario.iniciar("Presupuesto 2026", 2026, "Lider de Area")
        entorno.seleccionar_estructura_madre("1000")
        entorno.agregar_partida("1001", "Personal", 0)
        entorno.agregar_partida("1001.01", "Sueldo", 10000, categoria="Sueldo")
        entorno.agregar_partida("1001.02", "Pensión", 1500, categoria="Pension")
        entorno.agregar_partida("1001.03", "Seguro", 800, categoria="Seguro")

        matriz = {fila["codigo"]: fila for fila in entorno.matriz_madre()}

        self.assertEqual(matriz["1001"]["importe"], 12300)
        self.assertEqual(matriz["1000"]["importe"], 12300)
        self.assertEqual(matriz["1001.02"]["categoria"], "Pension")

    def test_subpartidas_pueden_usar_formato_un_digito_y_anidado(self) -> None:
        entorno = EntornoPresupuestario.iniciar("Presupuesto 2026", 2026, "Lider de Area")
        entorno.seleccionar_estructura_madre("1000")
        entorno.agregar_partida("1001", "Personal", 0)
        entorno.agregar_partida("1001.1", "Nómina", 500)
        entorno.agregar_partida("1001.1.1", "Sueldo base", 300)
        entorno.agregar_partida("1001.2", "Gasto social", 200)

        matriz = {fila["codigo"]: fila for fila in entorno.matriz_madre()}

        self.assertEqual(matriz["1001.1"]["importe"], 800)
        self.assertEqual(matriz["1001.1.1"]["importe"], 300)
        self.assertEqual(matriz["1001.2"]["importe"], 200)
        self.assertEqual(matriz["1001"]["importe"], 1000)
        self.assertEqual(matriz["1000"]["importe"], 1000)

    def test_puede_actualizar_una_partida_existente_y_generar_reporte_por_categoria(self) -> None:
        entorno = EntornoPresupuestario.iniciar("Presupuesto 2026", 2026, "Lider de Area")
        entorno.seleccionar_estructura_madre("1000")
        entorno.agregar_partida("1001", "Personal", 0, categoria="Sueldo")
        entorno.agregar_partida("1001.1", "Nómina", 500, categoria="Sueldo")
        entorno.agregar_partida("1001.1.1", "Sueldo base", 300, categoria="Sueldo")
        entorno.agregar_partida("1001.2", "Aporte", 200, categoria="Pension")

        actualizado = entorno.actualizar_partida("1001.1", descripcion="Nómina ajustada", importe=650, categoria="Sueldo")
        self.assertEqual(actualizado.descripcion, "Nómina ajustada")
        self.assertEqual(actualizado.importe, 650)

        matriz = {fila["codigo"]: fila for fila in entorno.matriz_madre()}
        self.assertEqual(matriz["1001"]["importe"], 1150)
        self.assertEqual(matriz["1000"]["importe"], 1150)

        reporte = entorno.reporte_por_categoria()
        self.assertIn("Sueldo", reporte)
        self.assertIn("Pension", reporte)
        self.assertEqual(reporte["Sueldo"]["total"], 950)
        self.assertEqual(reporte["Pension"]["total"], 200)

    def test_generacion_con_sufijos_financieros_y_vista_puesto(self) -> None:
        entorno = EntornoPresupuestario.iniciar("Presupuesto 2026", 2026, "Lider de Area")
        entorno.seleccionar_estructura_madre("1000")

        personal = entorno.agregar_partida("1001", "Personal", 0, categoria="Sueldo")
        self.assertEqual(personal.codigo, "1001")

        asistente = entorno.agregar_partida(codigo="", descripcion="Asistente", importe=2000, parent_codigo="1001", categoria="Sueldo")
        supervisor = entorno.agregar_partida(codigo="", descripcion="Supervisor", importe=3000, parent_codigo="1001", categoria="Sueldo")

        self.assertEqual(asistente.codigo, "1001.10")
        self.assertEqual(supervisor.codigo, "1001.20")

        vista = entorno.reporte_por_vista("puesto")
        self.assertIn(".10", vista)
        self.assertIn(".20", vista)
        self.assertEqual(vista[".10"]["total"], 2000)
        self.assertEqual(vista[".20"]["total"], 3000)


if __name__ == "__main__":
    unittest.main()