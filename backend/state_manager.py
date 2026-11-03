from backend.database import conectar


def guardar_progreso(
    pelicula_id=None,
    episodio_id=None,
    posicion=0,
    terminado=False
):
    conexion = conectar()
    cursor = conexion.cursor()

    # Buscar si ya existe un progreso para ese contenido
    if pelicula_id is not None:
        cursor.execute(
            """
            SELECT id
            FROM progreso
            WHERE pelicula_id = %s
            """,
            (pelicula_id,)
        )
    else:
        cursor.execute(
            """
            SELECT id
            FROM progreso
            WHERE episodio_id = %s
            """,
            (episodio_id,)
        )

    progreso = cursor.fetchone()

    if progreso:
        # Ya existe → actualizar
        cursor.execute(
            """
            UPDATE progreso
            SET posicion = %s,
                terminado = %s
            WHERE id = %s
            """,
            (
                posicion,
                terminado,
                progreso[0]
            )
        )

    else:
        # No existe → crear
        cursor.execute(
            """
            INSERT INTO progreso
            (
                pelicula_id,
                episodio_id,
                posicion,
                terminado
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                pelicula_id,
                episodio_id,
                posicion,
                terminado
            )
        )

    conexion.commit()

    cursor.close()
    conexion.close()


def obtener_progreso(
    pelicula_id=None,
    episodio_id=None
):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    # Buscar progreso de una película
    if pelicula_id is not None:

        cursor.execute(
            """
            SELECT posicion, terminado
            FROM progreso
            WHERE pelicula_id = %s
            """,
            (pelicula_id,)
        )

    # Buscar progreso de un episodio
    else:

        cursor.execute(
            """
            SELECT posicion, terminado
            FROM progreso
            WHERE episodio_id = %s
            """,
            (episodio_id,)
        )

    progreso = cursor.fetchone()

    cursor.close()
    conexion.close()

    # El contenido nunca se ha iniciado
    if progreso is None:
        return None

    return progreso


# Prueba temporal
if __name__ == "__main__":

    progreso = obtener_progreso(
        episodio_id=1
    )

    print("Progreso:")
    print(progreso)