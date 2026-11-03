from backend.database import (
    obtener_contenido,
    obtener_siguiente_episodio
)

from backend.random_engine import seleccionar_contenido
from backend.state_manager import obtener_progreso


def mostrar_estado_progreso(progreso):

    # El contenido nunca se ha iniciado
    if progreso is None:
        print("Progreso: 0 segundos")
        print("Estado: No iniciado")
        return

    # El contenido ya terminó
    if progreso["terminado"]:
        print(
            f"Progreso: {progreso['posicion']} segundos"
        )
        print("Estado: Terminado")

    # El contenido está en progreso
    else:
        print(
            f"Progreso: {progreso['posicion']} segundos"
        )
        print("Estado: En progreso")


def main():

    # Obtener contenido desde MySQL
    contenido = obtener_contenido()

    # Seleccionar contenido aleatoriamente
    seleccionado = seleccionar_contenido(contenido)

    if seleccionado is None:
        print("No hay contenido disponible.")
        return

    print("\n==============================")
    print("      PLAY CHANNEL")
    print("==============================")

    print("\nContenido seleccionado:")
    print(f"Título: {seleccionado['titulo']}")
    print(f"Tipo: {seleccionado['tipo']}")

    # --------------------------------
    # PELÍCULA
    # --------------------------------

    if seleccionado["tipo"] == "pelicula":

        progreso = obtener_progreso(
            pelicula_id=seleccionado["id"]
        )

        print("\nEstado del contenido:")

        mostrar_estado_progreso(progreso)

    # --------------------------------
    # SERIE
    # --------------------------------

    elif seleccionado["tipo"] == "serie":

        episodio = obtener_siguiente_episodio(
            seleccionado["id"]
        )

        print("\nSiguiente episodio:")

        # Todos los episodios de la serie están terminados
        if episodio is None:

            print("La serie está terminada.")

        else:

            print(
                f"T{episodio['temporada']} "
                f"E{episodio['episodio']} - "
                f"{episodio['titulo']}"
            )

            progreso = obtener_progreso(
                episodio_id=episodio["id"]
            )

            print("\nEstado del episodio:")

            mostrar_estado_progreso(progreso)


if __name__ == "__main__":
    main()