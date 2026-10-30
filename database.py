import mysql.connector

#Conectar el codiigo a la base de datos de PlayChannel
def conectar():
    return mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="2904vnrr",
        database="play_channel"
    )


#Función que permite detectar las peliculas
def obtener_peliculas():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM peliculas")
    peliculas = cursor.fetchall()
    cursor.close()
    conexion.close()

    return peliculas


#Función que permite detectar las series
def obtener_series():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM series")
    series = cursor.fetchall()
    cursor.close()
    conexion.close()

    return series


#Función para ver lo que cargo la serie de forma resumida
def obtener_serie_resumida(serie_id):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    consulta = """
        SELECT
            temporadas.numero AS temporada,
            COUNT(episodios.id) AS episodios
        FROM temporadas
        LEFT JOIN episodios
            ON episodios.temporada_id = temporadas.id
        WHERE temporadas.serie_id = %s
        GROUP BY temporadas.id, temporadas.numero
        ORDER BY temporadas.numero
    """
    cursor.execute(consulta, (serie_id,))
    tempordas = cursor.fetchall()
    cursor.close()
    conexion.close()

    return tempordas



def obtener_contenido():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    consulta = """
        SELECT
            id,
            titulo,
            'pelicula' AS tipo
        FROM peliculas
        WHERE ruta_archivo IS NOT NULL
            AND TRIM(ruta_archivo) != ''
        UNION ALL
        SELECT
            id,
            titulo,
            'serie' AS tipo
        FROM series
    """
    cursor.execute(consulta)
    contenido = cursor.fetchall()
    cursor.close()
    conexion.close()

    return contenido

def obtener_episodios_serie(serie_id):
    conexion = conectar()
    cursor= conexion.cursor(dictionary=True)
    consulta = """
        SELECT
            episodios.id,
            temporadas.numero AS temporada,
            episodios.numero AS episodio,
            episodios.titulo,
            episodios.duracion,
            episodios.ruta_archivo
        FROM episodios
        INNER JOIN temporadas
            ON episodios.temporada_id = temporadas.id
        WHERE temporadas.serie_id = %s
        ORDER BY temporadas.numero, episodios.numero
    """
    cursor.execute(consulta, (serie_id,))
    episodios = cursor.fetchall()
    cursor.close()
    conexion.close()

    return episodios


def obtener_siguiente_episodio(serie_id):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    consulta = """
        SELECT
            episodios.id,
            temporadas.numero AS temporada,
            episodios.numero AS episodio,
            episodios.titulo,
            episodios.duracion,
            episodios.ruta_archivo
        FROM episodios
        INNER JOIN temporadas
            ON episodios.temporada_id = temporadas.id
        LEFT JOIN progreso
            ON progreso.episodio_id = episodios.id
        WHERE temporadas.serie_id = %s
            AND (
                progreso.id IS NULL
                OR progreso.terminado = FALSE
            )
        ORDER BY temporadas.numero, episodios.numero
        LIMIT 1
    """
    cursor.execute(consulta, (serie_id,))
    episodio = cursor.fetchone()
    cursor.close()
    conexion.close()

    return episodio


#Función que permite ver las peliculas cargadas y series cargadas
if __name__ == "__main__":
    episodio = obtener_siguiente_episodio(1)
    print("Siguiente episodio:")
    if episodio:
        print(
            f"T{episodio['temporada']} "
            f"E{episodio['episodio']} - "
            f"{episodio['titulo']}"
        )
    else:
        print("La serie está terminada.")
        

# Obtiene las películas pendientes y reinicia el ciclo si todas ya terminaron.
def obtener_peliculas_ciclo():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    consulta = """
        SELECT p.id, p.titulo, p.anio, p.duracion, p.ruta_archivo
        FROM peliculas p
        LEFT JOIN historial_ciclo_peliculas h
            ON h.pelicula_id = p.id
        WHERE p.ruta_archivo IS NOT NULL
            AND TRIM(p.ruta_archivo) != ''
            AND h.pelicula_id IS NULL
    """

    try:
        cursor.execute(consulta)
        pendientes = cursor.fetchall()

        if not pendientes:
            cursor.execute("DELETE FROM historial_ciclo_peliculas")
            conexion.commit()

            cursor.execute("""
                SELECT id, titulo, anio, duracion, ruta_archivo
                FROM peliculas
                WHERE ruta_archivo IS NOT NULL
                    AND TRIM(ruta_archivo) != ''
            """)
            pendientes = cursor.fetchall()

        return pendientes

    except Exception:
        conexion.rollback()
        raise

    finally:
        cursor.close()
        conexion.close()


# Marca una película como emitida para evitar que se repita durante el ciclo.
def marcar_pelicula_emitida(pelicula_id):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        cursor.execute(
            """
            INSERT IGNORE INTO historial_ciclo_peliculas (pelicula_id)
            VALUES (%s)
            """,
            (pelicula_id,)
        )
        conexion.commit()

    except Exception:
        conexion.rollback()
        raise

    finally:
        cursor.close()
        conexion.close()