"""Backend HTTP mínimo para probar el flujo presupuestario."""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse
from uuid import uuid4

if __package__:
    from app.workspace import EntornoPresupuestario
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from app.workspace import EntornoPresupuestario


class PresupuestoApi:
    """Casos de uso del backend con almacenamiento en memoria."""

    ROLES_QUE_CAPTURAN = {"Lider de Area", "Director Financiero"}
    USUARIOS = {
        "lider.operativo": ("lider2026", "Lider de Area"),
        "director.financiero": ("director2026", "Director Financiero"),
        "direccion.general": ("general2026", "Direccion General"),
        "ingenieria.operaciones": ("ingenieria2026", "Ingenieria Industrial"),
    }

    def __init__(self) -> None:
        self.presupuestos: dict[str, EntornoPresupuestario] = {}
        self.propietarios: dict[str, str] = {}
        self.sesiones: dict[str, dict[str, str]] = {}

    def login(self, usuario: str, contrasena: str) -> dict[str, str]:
        registro = self.USUARIOS.get(usuario)
        if registro is None or registro[0] != contrasena:
            raise PermissionError("Usuario o contraseña incorrectos.")
        token = str(uuid4())
        self.sesiones[token] = {"usuario": usuario, "rol": registro[1]}
        return {"token": token, "usuario": usuario, "rol": registro[1]}

    def crear_presupuesto(
        self,
        datos: dict[str, Any],
        rol: str | None = None,
        propietario: str | None = None,
    ) -> dict[str, Any]:
        nombre = str(datos.get("nombre", "")).strip()
        if not nombre:
            raise ValueError("El nombre del presupuesto es obligatorio.")
        ejercicio = int(datos.get("ejercicio", 0))
        if ejercicio < 1:
            raise ValueError("El ejercicio debe ser un año válido.")
        rol = rol or str(datos.get("rol", "Lider de Area"))
        presupuesto_id = str(uuid4())
        self.presupuestos[presupuesto_id] = EntornoPresupuestario.iniciar_estandar_peru(nombre, ejercicio, rol)
        if propietario:
            self.propietarios[presupuesto_id] = propietario
        return {"id": presupuesto_id, "nombre": nombre, "ejercicio": ejercicio, "rol": rol}

    def capitulos(self) -> list[dict[str, Any]]:
        return [
            {"codigo": cuenta.codigo, "descripcion": cuenta.descripcion}
            for cuenta in EntornoPresupuestario.iniciar_estandar_peru("Catalogo", 0, "Lider de Area").catalogo.capitulos()
        ]

    def seleccionar_madre(self, presupuesto_id: str, codigo: str) -> dict[str, Any]:
        entorno = self._obtener(presupuesto_id)
        entorno.seleccionar_estructura_madre(codigo)
        return {"presupuesto_id": presupuesto_id, "estructura_madre": codigo}

    def agregar_partida(self, presupuesto_id: str, datos: dict[str, Any]) -> dict[str, Any]:
        entorno = self._obtener(presupuesto_id)
        partida = entorno.agregar_partida(
            codigo=str(datos.get("codigo", "")).strip(),
            descripcion=str(datos.get("descripcion", "")).strip(),
            importe=float(datos.get("importe", 0)),
            parent_codigo=str(datos.get("parent_codigo", "")).strip() or None,
            categoria=str(datos.get("categoria", "")).strip() or None,
            clasificacion_financiera=str(datos.get("clasificacion_financiera", "OPEX")),
        )
        return {
            "codigo": partida.codigo,
            "descripcion": partida.descripcion,
            "importe": partida.importe,
            "responsable": partida.responsable,
            "parent_codigo": partida.parent_codigo,
            "categoria": partida.categoria,
            "clasificacion_financiera": partida.clasificacion_financiera,
        }

    def actualizar_partida(self, presupuesto_id: str, codigo: str, datos: dict[str, Any]) -> dict[str, Any]:
        entorno = self._obtener(presupuesto_id)
        partida = entorno.actualizar_partida(
            codigo=codigo,
            descripcion=(None if "descripcion" not in datos else str(datos.get("descripcion", "")).strip() or None),
            importe=None if "importe" not in datos else float(datos.get("importe", 0)),
            parent_codigo=(None if "parent_codigo" not in datos else str(datos.get("parent_codigo", "")).strip() or None),
            categoria=(None if "categoria" not in datos else str(datos.get("categoria", "")).strip() or None),
            clasificacion_financiera=(
                None if "clasificacion_financiera" not in datos
                else str(datos.get("clasificacion_financiera", ""))
            ),
        )
        return {
            "codigo": partida.codigo,
            "descripcion": partida.descripcion,
            "importe": partida.importe,
            "responsable": partida.responsable,
            "parent_codigo": partida.parent_codigo,
            "categoria": partida.categoria,
            "clasificacion_financiera": partida.clasificacion_financiera,
        }

    def flujo_caja(self, presupuesto_id: str) -> dict[str, Any]:
        return self._obtener(presupuesto_id).flujo_caja()

    def establecer_saldo_inicial(self, presupuesto_id: str, importe: float) -> dict[str, float]:
        saldo = self._obtener(presupuesto_id).establecer_saldo_inicial(importe)
        return {"saldo_inicial": saldo}

    def programar_partida_mensual(
        self,
        presupuesto_id: str,
        codigo: str,
        mes: int,
        importe: float,
    ) -> dict[str, Any]:
        return self._obtener(presupuesto_id).programar_partida_mensual(codigo, mes, importe)

    def programar_ingreso_mensual(self, presupuesto_id: str, mes: int, importe: float) -> dict[str, Any]:
        return self._obtener(presupuesto_id).programar_ingreso_mensual(mes, importe)

    def registrar_movimiento_caja(self, presupuesto_id: str, datos: dict[str, Any]) -> dict[str, Any]:
        movimiento = self._obtener(presupuesto_id).registrar_movimiento_caja(
            fecha=str(datos.get("fecha", "")),
            tipo=str(datos.get("tipo", "")),
            descripcion=str(datos.get("descripcion", "")),
            importe=float(datos.get("importe", 0)),
            clasificacion_financiera=(
                None if datos.get("clasificacion_financiera") is None
                else str(datos.get("clasificacion_financiera"))
            ),
            partida_codigo=str(datos.get("partida_codigo", "")).strip() or None,
        )
        return {
            "id": movimiento.id,
            "fecha": movimiento.fecha,
            "tipo": movimiento.tipo,
            "descripcion": movimiento.descripcion,
            "importe": movimiento.importe,
            "clasificacion_financiera": movimiento.clasificacion_financiera,
            "partida_codigo": movimiento.partida_codigo,
        }

    def reporte(self, presupuesto_id: str, vista: str = "financiera") -> dict[str, Any]:
        entorno = self._obtener(presupuesto_id)
        vista_norm = "puesto" if vista == "puesto" else "financiera"
        datos_reporte = entorno.reporte_por_vista(vista_norm)
        return {
            "id": presupuesto_id,
            "nombre": entorno.model.nombre,
            "ejercicio": entorno.model.ejercicio,
            "vista": vista_norm,
            "reporte": datos_reporte,
        }

    def matriz(self, presupuesto_id: str) -> dict[str, Any]:
        entorno = self._obtener(presupuesto_id)
        return {
            "id": presupuesto_id,
            "nombre": entorno.model.nombre,
            "ejercicio": entorno.model.ejercicio,
            "estructura_madre": entorno.model.estructura_madre,
            "propietario_rol": entorno.rol,
            "aprobado": entorno.model.aprobado,
            "aprobado_por": entorno.model.aprobado_por,
            "filas": entorno.matriz_madre(),
        }

    def listar_presupuestos(
        self,
        propietario: str | None = None,
        incluir_todos: bool = False,
    ) -> list[dict[str, Any]]:
        return [
            {
                "id": presupuesto_id,
                "nombre": entorno.model.nombre,
                "ejercicio": entorno.model.ejercicio,
                "estructura_madre": entorno.model.estructura_madre,
                "aprobado": entorno.model.aprobado,
                "propietario_rol": entorno.rol,
            }
            for presupuesto_id, entorno in self.presupuestos.items()
            if incluir_todos or propietario is None or self.propietarios.get(presupuesto_id) == propietario
        ]

    def validar_propietario(
        self,
        presupuesto_id: str,
        propietario: str,
        permitir_direccion_general: bool = False,
    ) -> None:
        self._obtener(presupuesto_id)
        rol = next(
            (sesion["rol"] for sesion in self.sesiones.values() if sesion["usuario"] == propietario),
            None,
        )
        if self.propietarios.get(presupuesto_id) != propietario and not (
            permitir_direccion_general and rol == "Direccion General"
        ):
            raise PermissionError("No tienes acceso a este presupuesto.")

    def aprobar(self, presupuesto_id: str, usuario: str, rol: str) -> dict[str, Any]:
        entorno = self._obtener(presupuesto_id)
        entorno.aprobar(usuario, rol)
        return self.matriz(presupuesto_id)

    def _obtener(self, presupuesto_id: str) -> EntornoPresupuestario:
        try:
            return self.presupuestos[presupuesto_id]
        except KeyError as error:
            raise KeyError("El presupuesto no existe.") from error


class RequestHandler(BaseHTTPRequestHandler):
    """Adaptador HTTP del API."""

    api = PresupuestoApi()

    def do_GET(self) -> None:
        ruta = self._ruta_api()
        try:
            if ruta == "/":
                self._responder_html()
            elif ruta == "/api":
                self._responder(
                    200,
                    {
                        "nombre": "Presupuesto Modular API",
                        "estado": "ok",
                        "rutas": [
                            "GET /health",
                            "GET /catalogo/capitulos",
                            "POST /presupuestos",
                            "POST /presupuestos/{id}/estructura-madre",
                            "POST /presupuestos/{id}/partidas",
                            "GET /presupuestos/{id}/matriz",
                            "GET /presupuestos/{id}/flujo-caja",
                            "PUT /presupuestos/{id}/saldo-inicial",
                            "PUT /presupuestos/{id}/ingresos-proyectados",
                            "PUT /presupuestos/{id}/partidas/{codigo}/programacion-mensual",
                            "POST /presupuestos/{id}/movimientos-caja",
                        ],
                    },
                )
            elif ruta == "/health":
                self._responder(200, {"status": "ok"})
            elif ruta == "/catalogo/capitulos":
                self._responder(200, {"capitulos": self.api.capitulos()})
            elif ruta == "/presupuestos":
                usuario = self._usuario_actual()
                incluir_todos = usuario["rol"] == "Direccion General"
                self._responder(
                    200,
                    {"presupuestos": self.api.listar_presupuestos(usuario["usuario"], incluir_todos)},
                )
            elif ruta.startswith("/presupuestos/") and ruta.endswith("/matriz"):
                presupuesto_id = ruta.split("/")[2]
                self._usuario_presupuesto(presupuesto_id)
                self._responder(200, self.api.matriz(presupuesto_id))
            elif ruta.startswith("/presupuestos/") and ruta.endswith("/reporte"):
                presupuesto_id = ruta.split("/")[2]
                self._usuario_presupuesto(presupuesto_id)
                params = parse_qs(urlparse(self.path).query)
                vista = params.get("vista", ["financiera"])[0]
                self._responder(200, self.api.reporte(presupuesto_id, vista))
            elif ruta.startswith("/presupuestos/") and ruta.endswith("/flujo-caja"):
                presupuesto_id = ruta.split("/")[2]
                self._usuario_presupuesto(presupuesto_id)
                self._responder(200, self.api.flujo_caja(presupuesto_id))
            else:
                self._responder(404, {"error": "Ruta no encontrada."})
        except (KeyError, ValueError, PermissionError) as error:
            self._responder(self._estado_error(error), {"error": str(error)})

    def do_POST(self) -> None:
        ruta = self._ruta_api()
        try:
            datos = self._leer_json()
            if ruta == "/login":
                self._responder(200, self.api.login(str(datos.get("usuario", "")), str(datos.get("contrasena", ""))))
            elif ruta == "/presupuestos":
                usuario = self._usuario_actual()
                if usuario["rol"] not in self.api.ROLES_QUE_CAPTURAN:
                    raise PermissionError("El rol actual no puede crear presupuestos.")
                self._responder(
                    201,
                    self.api.crear_presupuesto(datos, usuario["rol"], usuario["usuario"]),
                )
            elif ruta.startswith("/presupuestos/") and ruta.endswith("/estructura-madre"):
                presupuesto_id = ruta.split("/")[2]
                self._usuario_propietario(presupuesto_id)
                self._responder(200, self.api.seleccionar_madre(presupuesto_id, str(datos["codigo"])))
            elif ruta.startswith("/presupuestos/") and ruta.endswith("/partidas"):
                presupuesto_id = ruta.split("/")[2]
                self._usuario_propietario(presupuesto_id)
                self._responder(201, self.api.agregar_partida(presupuesto_id, datos))
            elif ruta.startswith("/presupuestos/") and ruta.endswith("/aprobar"):
                usuario = self._usuario_actual()
                presupuesto_id = ruta.split("/")[2]
                self.api.validar_propietario(
                    presupuesto_id,
                    usuario["usuario"],
                    permitir_direccion_general=True,
                )
                self._responder(200, self.api.aprobar(presupuesto_id, usuario["usuario"], usuario["rol"]))
            elif ruta.startswith("/presupuestos/") and ruta.endswith("/reporte"):
                presupuesto_id = ruta.split("/")[2]
                self._usuario_presupuesto(presupuesto_id)
                params = parse_qs(urlparse(self.path).query)
                vista = params.get("vista", ["financiera"])[0]
                self._responder(200, self.api.reporte(presupuesto_id, vista))
            elif ruta.startswith("/presupuestos/") and ruta.endswith("/movimientos-caja"):
                presupuesto_id = ruta.split("/")[2]
                self._usuario_propietario(presupuesto_id)
                self._responder(201, self.api.registrar_movimiento_caja(presupuesto_id, datos))
            else:
                self._responder(404, {"error": "Ruta no encontrada."})
        except (KeyError, ValueError, PermissionError, TypeError) as error:
            self._responder(self._estado_error(error), {"error": str(error)})

    def do_PUT(self) -> None:
        ruta = self._ruta_api()
        try:
            datos = self._leer_json()
            if ruta.startswith("/presupuestos/") and "/partidas/" in ruta:
                presupuesto_id = ruta.split("/")[2]
                self._usuario_propietario(presupuesto_id)
                codigo_y_accion = ruta.split("/partidas/", 1)[1]
                if codigo_y_accion.endswith("/programacion-mensual"):
                    codigo = unquote(codigo_y_accion.removesuffix("/programacion-mensual"))
                    resultado = self.api.programar_partida_mensual(
                        presupuesto_id,
                        codigo,
                        int(datos.get("mes", 0)),
                        float(datos.get("importe", 0)),
                    )
                    self._responder(200, resultado)
                    return
                codigo = unquote(codigo_y_accion)
                self._responder(200, self.api.actualizar_partida(presupuesto_id, codigo, datos))
            elif ruta.startswith("/presupuestos/") and ruta.endswith("/saldo-inicial"):
                presupuesto_id = ruta.split("/")[2]
                self._usuario_propietario(presupuesto_id)
                self._responder(
                    200,
                    self.api.establecer_saldo_inicial(presupuesto_id, float(datos.get("importe", 0))),
                )
            elif ruta.startswith("/presupuestos/") and ruta.endswith("/ingresos-proyectados"):
                presupuesto_id = ruta.split("/")[2]
                self._usuario_propietario(presupuesto_id)
                self._responder(
                    200,
                    self.api.programar_ingreso_mensual(
                        presupuesto_id,
                        int(datos.get("mes", 0)),
                        float(datos.get("importe", 0)),
                    ),
                )
            else:
                self._responder(404, {"error": "Ruta no encontrada."})
        except (KeyError, ValueError, PermissionError, TypeError) as error:
            self._responder(self._estado_error(error), {"error": str(error)})

    def _leer_json(self) -> dict[str, Any]:
        longitud = int(self.headers.get("Content-Length", "0"))
        datos = json.loads(self.rfile.read(longitud) or b"{}")
        if not isinstance(datos, dict):
            raise TypeError("El cuerpo debe ser un objeto JSON.")
        return datos

    def _ruta_api(self) -> str:
        ruta = urlparse(self.path).path.rstrip("/") or "/"
        if ruta.startswith("/api/"):
            return ruta[4:]
        return ruta

    def _usuario_actual(self) -> dict[str, str]:
        encabezado = self.headers.get("Authorization", "")
        if not encabezado.startswith("Bearer "):
            raise PermissionError("Se requiere iniciar sesión.")
        token = encabezado[7:].strip()
        if token not in self.api.sesiones:
            raise PermissionError("La sesión no es válida o expiró.")
        return self.api.sesiones[token]

    def _usuario_presupuesto(self, presupuesto_id: str) -> dict[str, str]:
        usuario = self._usuario_actual()
        self.api.validar_propietario(
            presupuesto_id,
            usuario["usuario"],
            permitir_direccion_general=True,
        )
        return usuario

    def _usuario_propietario(self, presupuesto_id: str) -> dict[str, str]:
        usuario = self._usuario_actual()
        self.api.validar_propietario(presupuesto_id, usuario["usuario"])
        return usuario

    @staticmethod
    def _estado_error(error: Exception) -> int:
        if isinstance(error, PermissionError):
            return 403 if "acceso" in str(error).lower() or "solo" in str(error).lower() or "rol" in str(error).lower() else 401
        return 400

    def _responder_html(self) -> None:
        archivo = Path(__file__).parent / "static" / "index.html"
        cuerpo = archivo.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def _responder(self, estado: int, datos: dict[str, Any]) -> None:
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(estado)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def log_message(self, formato: str, *argumentos: Any) -> None:
        return


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Inicia el servidor local del MVP."""
    servidor = ThreadingHTTPServer((host, port), RequestHandler)
    print(f"Backend disponible en http://{host}:{port}")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nBackend detenido.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    run_server()
