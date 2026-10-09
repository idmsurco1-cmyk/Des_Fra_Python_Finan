import json
from http.server import ThreadingHTTPServer
import threading
import unittest
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app.backend import PresupuestoApi, RequestHandler


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

    def test_codigo_automatico_en_capitulo_y_clasificacion_opex_capex(self) -> None:
        api = PresupuestoApi()
        presupuesto_id = api.crear_presupuesto(
            {"nombre": "Clasificación", "ejercicio": 2026}, "Lider de Area"
        )["id"]
        api.seleccionar_madre(presupuesto_id, "2000")

        creada = api.agregar_partida(
            presupuesto_id,
            {
                "codigo": "",
                "descripcion": "Equipo productivo",
                "importe": 500,
                "parent_codigo": "2000",
                "clasificacion_financiera": "CAPEX",
            },
        )

        self.assertEqual(creada["codigo"], "2001")
        self.assertEqual(creada["clasificacion_financiera"], "CAPEX")
        self.assertEqual(
            next(f for f in api.matriz(presupuesto_id)["filas"] if f["codigo"] == "2001")[
                "clasificacion_financiera"
            ],
            "CAPEX",
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

    def test_clasificacion_programacion_y_flujo_de_caja(self) -> None:
        api = PresupuestoApi()
        presupuesto_id = api.crear_presupuesto(
            {"nombre": "Caja 2026", "ejercicio": 2026}, "Lider de Area"
        )["id"]
        api.seleccionar_madre(presupuesto_id, "2000")
        api.agregar_partida(
            presupuesto_id,
            {
                "codigo": "2111",
                "descripcion": "Equipo",
                "importe": 300,
                "clasificacion_financiera": "CAPEX",
            },
        )
        api.establecer_saldo_inicial(presupuesto_id, 1000)
        api.programar_partida_mensual(presupuesto_id, "2111", 1, 100)
        api.programar_partida_mensual(presupuesto_id, "2111", 2, 200)
        api.programar_ingreso_mensual(presupuesto_id, 1, 500)
        api.programar_ingreso_mensual(presupuesto_id, 2, 100)
        api.registrar_movimiento_caja(
            presupuesto_id,
            {
                "fecha": "2026-01-15",
                "tipo": "ingreso",
                "descripcion": "Cobro de cliente",
                "importe": 400,
            },
        )
        api.registrar_movimiento_caja(
            presupuesto_id,
            {
                "fecha": "2026-01-20",
                "tipo": "egreso",
                "descripcion": "Compra de equipo",
                "importe": 80,
                "clasificacion_financiera": "CAPEX",
                "partida_codigo": "2111",
            },
        )

        flujo = api.flujo_caja(presupuesto_id)
        enero, febrero = flujo["meses"][:2]

        self.assertEqual(enero["presupuesto_capex"], 100)
        self.assertEqual(enero["saldo_proyectado"], 1400)
        self.assertEqual(enero["saldo_real"], 1320)
        self.assertEqual(febrero["saldo_proyectado"], 1300)
        self.assertEqual(febrero["saldo_real"], 1320)
        self.assertEqual(flujo["resumen"]["presupuesto_sin_programar"], 0)
        self.assertEqual(len(flujo["movimientos"]), 2)

    def test_rechaza_programacion_mayor_al_presupuesto_y_movimientos_fuera_del_ejercicio(self) -> None:
        api = PresupuestoApi()
        presupuesto_id = api.crear_presupuesto(
            {"nombre": "Validación caja", "ejercicio": 2026}, "Lider de Area"
        )["id"]
        api.seleccionar_madre(presupuesto_id, "2000")
        api.agregar_partida(
            presupuesto_id,
            {"codigo": "2111", "descripcion": "Material", "importe": 100},
        )

        with self.assertRaisesRegex(ValueError, "supera el importe anual"):
            api.programar_partida_mensual(presupuesto_id, "2111", 1, 101)
        with self.assertRaisesRegex(ValueError, "pertenecer al ejercicio"):
            api.registrar_movimiento_caja(
                presupuesto_id,
                {
                    "fecha": "2027-01-01",
                    "tipo": "ingreso",
                    "descripcion": "Fuera del año",
                    "importe": 10,
                },
            )
        with self.assertRaisesRegex(ValueError, "finito"):
            api.establecer_saldo_inicial(presupuesto_id, float("nan"))

    def test_presupuestos_se_filtran_por_propietario(self) -> None:
        api = PresupuestoApi()
        de_ana = api.crear_presupuesto(
            {"nombre": "Privado A", "ejercicio": 2026}, "Lider de Area", "ana"
        )["id"]
        api.crear_presupuesto(
            {"nombre": "Privado B", "ejercicio": 2026}, "Lider de Area", "bea"
        )

        self.assertEqual([p["id"] for p in api.listar_presupuestos("ana")], [de_ana])
        with self.assertRaisesRegex(PermissionError, "No tienes acceso"):
            api.validar_propietario(de_ana, "bea")

    def test_actualizar_partida_no_deja_cambios_parciales_si_falla_validacion(self) -> None:
        api = PresupuestoApi()
        presupuesto_id = api.crear_presupuesto(
            {"nombre": "Actualización atómica", "ejercicio": 2026}, "Lider de Area"
        )["id"]
        api.seleccionar_madre(presupuesto_id, "2000")
        api.agregar_partida(
            presupuesto_id,
            {"codigo": "2111", "descripcion": "Material", "importe": 100},
        )
        api.programar_partida_mensual(presupuesto_id, "2111", 1, 20)

        with self.assertRaisesRegex(ValueError, "OPEX o CAPEX"):
            api.actualizar_partida(
                presupuesto_id,
                "2111",
                {
                    "descripcion": "Descripción que no debe guardarse",
                    "importe": 50,
                    "clasificacion_financiera": "INVERSION",
                },
            )

        partida = api.actualizar_partida(presupuesto_id, "2111", {})
        self.assertEqual(partida["descripcion"], "Material")
        self.assertEqual(partida["importe"], 100)


class BackendHttpTest(unittest.TestCase):
    def setUp(self) -> None:
        self.api_original = RequestHandler.api
        RequestHandler.api = PresupuestoApi()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), RequestHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        RequestHandler.api = self.api_original

    def request(
        self,
        method: str,
        path: str,
        body: dict[str, object] | None = None,
        token: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        headers = {}
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode("utf-8")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = Request(self.base_url + path, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=3) as response:
                return response.status, json.loads(response.read())
        except HTTPError as error:
            try:
                return error.code, json.loads(error.read())
            finally:
                error.close()

    def login(self, usuario: str, contrasena: str) -> str:
        status, respuesta = self.request(
            "POST",
            "/api/login",
            {"usuario": usuario, "contrasena": contrasena},
        )
        self.assertEqual(status, 200)
        return str(respuesta["token"])

    def test_entrega_dashboard_con_vista_de_caja(self) -> None:
        with urlopen(self.base_url + "/", timeout=3) as respuesta:
            contenido = respuesta.read().decode("utf-8")
        self.assertIn('id="tab-caja"', contenido)
        self.assertIn('id="caja-grafico"', contenido)
        self.assertIn('id="in-clasificacion-financiera"', contenido)

    def test_caja_por_http_y_acceso_por_propietario_con_aprobacion(self) -> None:
        lider = self.login("lider.operativo", "lider2026")
        status, presupuesto = self.request(
            "POST",
            "/api/presupuestos",
            {"nombre": "Flujo HTTP", "ejercicio": 2026},
            lider,
        )
        self.assertEqual(status, 201)
        presupuesto_id = str(presupuesto["id"])
        base = f"/api/presupuestos/{presupuesto_id}"

        self.assertEqual(
            self.request("POST", base + "/estructura-madre", {"codigo": "2000"}, lider)[0],
            200,
        )
        self.assertEqual(
            self.request(
                "POST",
                base + "/partidas",
                {
                    "codigo": "2111",
                    "descripcion": "Compra de equipo",
                    "importe": 250,
                    "clasificacion_financiera": "CAPEX",
                },
                lider,
            )[0],
            201,
        )
        self.assertEqual(
            self.request("PUT", base + "/saldo-inicial", {"importe": 1000}, lider)[0],
            200,
        )
        self.assertEqual(
            self.request(
                "PUT",
                base + "/ingresos-proyectados",
                {"mes": 1, "importe": 500},
                lider,
            )[0],
            200,
        )
        self.assertEqual(
            self.request(
                "PUT",
                base + "/partidas/2111/programacion-mensual",
                {"mes": 1, "importe": 100},
                lider,
            )[0],
            200,
        )
        self.assertEqual(
            self.request(
                "POST",
                base + "/movimientos-caja",
                {
                    "fecha": "2026-01-10",
                    "tipo": "egreso",
                    "descripcion": "Equipo recibido",
                    "importe": 75,
                    "clasificacion_financiera": "CAPEX",
                    "partida_codigo": "2111",
                },
                lider,
            )[0],
            201,
        )
        status, flujo = self.request("GET", base + "/flujo-caja", token=lider)
        self.assertEqual(status, 200)
        self.assertEqual(flujo["meses"][0]["saldo_proyectado"], 1400)
        self.assertEqual(flujo["meses"][0]["saldo_real"], 925)

        ingenieria = self.login("ingenieria.operaciones", "ingenieria2026")
        self.assertEqual(
            self.request(
                "POST",
                "/api/presupuestos",
                {"nombre": "Sin permisos", "ejercicio": 2026},
                ingenieria,
            )[0],
            403,
        )
        self.assertEqual(self.request("GET", base + "/flujo-caja", token=ingenieria)[0], 403)
        direccion = self.login("direccion.general", "general2026")
        self.assertEqual(self.request("GET", base + "/matriz", token=direccion)[0], 200)
        self.assertEqual(self.request("POST", base + "/aprobar", {}, direccion)[0], 200)


if __name__ == "__main__":
    unittest.main()
