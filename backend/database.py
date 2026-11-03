import os
import mysql.connector

# Establece una conexión con la base de datos de PlayChannel.
# Conecta el código a la base de datos de PlayChannel.
def conectar():
    return mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="2904vnrr",
        database="play_channel"
    )

# Obtiene todas las películas registradas.
def obtener_peliculas():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, titulo, anio, duracion, ruta_archivo, saga_id, orden
            FROM peliculas
            ORDER BY titulo
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()

#Obtiene todas las series registradas.
def obtener_series():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, titulo, anio, descripcion
            FROM series
            ORDER BY titulo
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()

# Obtiene el resumen de temporadas y episodios de una serie.
def obtener_serie_resumida(serie_id):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    try:
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
        return cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()

#Obtiene las películas y series disponibles para el sistema.
def obtener_contenido():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    try:
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
        return cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()

#Obtiene los episodios ordenados de una serie.
def obtener_episodios_serie(serie_id):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    try:
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
        return cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()

#Obtiene el siguiente episodio pendiente de una serie.
def obtener_siguiente_episodio(serie_id):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    try:
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
        return cursor.fetchone()
    finally:
        cursor.close()
        conexion.close()

#Obtiene las películas pendientes del ciclo que pertenecen a Mi contenido.
def obtener_peliculas_ciclo():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    try:
        consulta = """
            SELECT
                p.id,
                p.titulo,
                p.anio,
                p.duracion,
                p.ruta_archivo
            FROM catalogo_usuario cu
            INNER JOIN peliculas p
                ON cu.contenido_id = p.id
            LEFT JOIN historial_ciclo_peliculas h
                ON h.pelicula_id = p.id
            WHERE cu.tipo_contenido = 'pelicula'
                AND p.ruta_archivo IS NOT NULL
                AND TRIM(p.ruta_archivo) != ''
                AND h.pelicula_id IS NULL
        """
        cursor.execute(consulta)
        pendientes = cursor.fetchall()
        #Reiniciar el ciclo si todas las películas de Mi contenido ya fueron emitidas.
        if not pendientes:
            cursor.execute("""
                DELETE h
                FROM historial_ciclo_peliculas h
                INNER JOIN catalogo_usuario cu
                    ON cu.contenido_id = h.pelicula_id
                    AND cu.tipo_contenido = 'pelicula'
            """)
            conexion.commit()
            cursor.execute("""
                SELECT
                    p.id,
                    p.titulo,
                    p.anio,
                    p.duracion,
                    p.ruta_archivo
                FROM catalogo_usuario cu
                INNER JOIN peliculas p
                    ON cu.contenido_id = p.id
                WHERE cu.tipo_contenido = 'pelicula'
                    AND p.ruta_archivo IS NOT NULL
                    AND TRIM(p.ruta_archivo) != ''
            """)
            pendientes = cursor.fetchall()
        return pendientes
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()

#Marca una película como emitida durante el ciclo actual.
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

#Obtiene las películas y series que el usuario agregó a Mi contenido.
def obtener_catalogo_usuario():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    try:
        consulta = """
            SELECT
                cu.id AS registro_id,
                cu.tipo_contenido,
                p.id AS contenido_id,
                p.titulo,
                p.anio,
                p.duracion,
                p.ruta_archivo,
                p.ruta_portada,
                cu.fecha_agregado
            FROM catalogo_usuario cu
            INNER JOIN peliculas p
                ON cu.contenido_id = p.id
            WHERE cu.tipo_contenido = 'pelicula'
            UNION ALL
            SELECT
                cu.id AS registro_id,
                cu.tipo_contenido,
                s.id AS contenido_id,
                s.titulo,
                s.anio,
                NULL AS duracion,
                NULL AS ruta_archivo,
                NULL AS ruta_portada,
                cu.fecha_agregado
            FROM catalogo_usuario cu
            INNER JOIN series s
                ON cu.contenido_id = s.id
            WHERE cu.tipo_contenido = 'serie'
            ORDER BY fecha_agregado DESC
        """
        cursor.execute(consulta)
        return cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()

#Agrega a Mi contenido únicamente películas o series del catálogo preestablecido.
def agregar_catalogo_usuario(tipo_contenido, contenido_id):
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        if tipo_contenido not in ("pelicula", "serie"):
            return False
        cursor.execute(
            """
            SELECT id
            FROM catalogo_preestablecido
            WHERE tipo_contenido = %s
                AND contenido_id = %s
            """,
            (tipo_contenido, contenido_id)
        )
        if cursor.fetchone() is None:
            return False
        cursor.execute(
            """
            INSERT IGNORE INTO catalogo_usuario
                (tipo_contenido, contenido_id)
            VALUES (%s, %s)
            """,
            (tipo_contenido, contenido_id)
        )
        agregado = cursor.rowcount > 0
        conexion.commit()
        return agregado
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()

#Quita una película o serie de Mi contenido sin eliminar su registro original.
def eliminar_catalogo_usuario(tipo_contenido, contenido_id):
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            DELETE FROM catalogo_usuario
            WHERE tipo_contenido = %s
                AND contenido_id = %s
            """,
            (tipo_contenido, contenido_id)
        )
        eliminado = cursor.rowcount > 0
        conexion.commit()
        return eliminado
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()

#Obtiene exclusivamente las películas y series del catálogo preestablecido.
def obtener_catalogo_preestablecido():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    try:
        consulta = """
            SELECT
                cp.id AS registro_id,
                cp.tipo_contenido,
                p.id AS contenido_id,
                p.titulo,
                p.anio,
                p.duracion,
                p.ruta_archivo,
                p.ruta_portada,
                cp.fecha_agregado
            FROM catalogo_preestablecido cp
            INNER JOIN peliculas p
                ON cp.contenido_id = p.id
            WHERE cp.tipo_contenido = 'pelicula'
            UNION ALL
            SELECT
                cp.id AS registro_id,
                cp.tipo_contenido,
                s.id AS contenido_id,
                s.titulo,
                s.anio,
                NULL AS duracion,
                NULL AS ruta_archivo,
                NULL AS ruta_portada,
                cp.fecha_agregado
            FROM catalogo_preestablecido cp
            INNER JOIN series s
                ON cp.contenido_id = s.id
            WHERE cp.tipo_contenido = 'serie'
            ORDER BY fecha_agregado DESC
        """
        cursor.execute(consulta)
        return cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()

#Incorpora una película existente al catálogo preestablecido sin duplicarla.
def agregar_pelicula_catalogo(pelicula_id):
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            INSERT IGNORE INTO catalogo_preestablecido
                (tipo_contenido, contenido_id)
            SELECT 'pelicula', id
            FROM peliculas
            WHERE id = %s
            """,
            (pelicula_id,)
        )
        agregado = cursor.rowcount > 0
        conexion.commit()
        return agregado
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()

#Ejecuta una prueba de consulta de Mi contenido.
if __name__ == "__main__":
    contenido = obtener_catalogo_usuario()
    print("Contenido de Mi contenido:")
    for item in contenido:
        print(
            f"{item['tipo_contenido']} - "
            f"{item['titulo']}"
        )
