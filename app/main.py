"""Punto de entrada principal de la aplicación."""

from datetime import date
import sys
from pathlib import Path

if __package__:
    from app.backend import run_server
    from app.workspace import EntornoPresupuestario
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from app.backend import run_server
    from app.workspace import EntornoPresupuestario


def main() -> None:
    """Inicia el backend web; usa ``--cli`` para el flujo de consola legado."""
    if "--cli" not in sys.argv[1:]:
        run_server()
        return

    print("=== Presupuesto Modular ===")
    print("Roles: 1) Líder de Área  2) Director Financiero  3) Dirección General  4) Ingeniería Industrial")
    rol = {
        "1": "Lider de Area",
        "2": "Director Financiero",
        "3": "Direccion General",
        "4": "Ingenieria Industrial",
    }.get(input("Selecciona tu rol [1]: ").strip() or "1", "Lider de Area")

    nombre = input("Nombre del nuevo presupuesto: ").strip()
    ejercicio_texto = input(f"Ejercicio [{date.today().year}]: ").strip()
    ejercicio = int(ejercicio_texto or date.today().year)
    entorno = EntornoPresupuestario.iniciar(nombre or "Presupuesto sin nombre", ejercicio, rol)

    print("\nEstructuras madre CONAC disponibles:")
    for cuenta in entorno.catalogo.capitulos():
        print(f"{cuenta.codigo} - {cuenta.descripcion}")
    entorno.seleccionar_estructura_madre(input("Selecciona el capítulo madre: ").strip())

    print("\nAgrega partidas específicas. Deja el código vacío para ver la matriz.")
    while True:
        codigo = input("Código de partida (4 dígitos): ").strip()
        if not codigo:
            break
        try:
            entorno.agregar_partida(
                codigo=codigo,
                descripcion=input("Descripción: ").strip(),
                importe=float(input("Importe presupuestado: ").strip()),
            )
            print("Partida agregada.")
        except (ValueError, PermissionError) as error:
            print(f"No se pudo agregar: {error}")

    print(f"\nMatriz madre: {entorno.model.nombre} ({entorno.model.ejercicio})")
    for fila in entorno.matriz_madre():
        print(f"{fila['codigo']} | {fila['nivel']} | {fila['descripcion']} | ${fila['importe']:,.2f}")


if __name__ == "__main__":
    main()
