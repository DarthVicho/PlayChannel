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

# Obtiene el siguiente episodio cronológico pendiente de una serie.
def obtener_siguiente_episodio(serie_id):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    try:
        consulta = """
            SELECT
                e.id,
                t.numero AS temporada,
                e.numero AS episodio,
                e.titulo,
                e.duracion,
                e.ruta_archivo
            FROM episodios e
            INNER JOIN temporadas t
                ON e.temporada_id = t.id
            LEFT JOIN historial_ciclo_episodios h
                ON h.episodio_id = e.id
            WHERE t.serie_id = %s
                AND h.episodio_id IS NULL
                AND e.ruta_archivo IS NOT NULL
                AND TRIM(e.ruta_archivo) != ''
            ORDER BY t.numero, e.numero
            LIMIT 1
        """
        cursor.execute(consulta, (serie_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conexion.close()

# Consulta películas y el siguiente episodio disponible de cada serie.
def _consultar_contenido_pendiente(cursor):
    consulta = """
        SELECT
            p.id,
            p.titulo,
            p.anio,
            p.duracion,
            p.ruta_archivo,
            'pelicula' AS tipo,
            NULL AS temporada,
            NULL AS episodio,
            NULL AS serie_id
        FROM catalogo_usuario cu
        INNER JOIN peliculas p
            ON cu.contenido_id = p.id
        LEFT JOIN historial_ciclo_peliculas hp
            ON hp.pelicula_id = p.id
        WHERE cu.tipo_contenido = 'pelicula'
            AND hp.pelicula_id IS NULL
            AND p.ruta_archivo IS NOT NULL
            AND TRIM(p.ruta_archivo) != ''
        UNION ALL
        SELECT
            e.id,
            CONCAT(s.titulo, ' - ', e.titulo) AS titulo,
            s.anio,
            e.duracion,
            e.ruta_archivo,
            'episodio' AS tipo,
            t.numero AS temporada,
            e.numero AS episodio,
            s.id AS serie_id
        FROM catalogo_usuario cu
        INNER JOIN series s
            ON cu.contenido_id = s.id
        INNER JOIN temporadas t
            ON t.serie_id = s.id
        INNER JOIN episodios e
            ON e.temporada_id = t.id
        LEFT JOIN historial_ciclo_episodios he
            ON he.episodio_id = e.id
        WHERE cu.tipo_contenido = 'serie'
            AND he.episodio_id IS NULL
            AND e.ruta_archivo IS NOT NULL
            AND TRIM(e.ruta_archivo) != ''
            -- Solo permite el primer episodio pendiente de cada serie.
            AND NOT EXISTS (
                SELECT 1
                FROM temporadas t2
                INNER JOIN episodios e2
                    ON e2.temporada_id = t2.id
                LEFT JOIN historial_ciclo_episodios he2
                    ON he2.episodio_id = e2.id
                WHERE t2.serie_id = s.id
                    AND he2.episodio_id IS NULL
                    AND e2.ruta_archivo IS NOT NULL
                    AND TRIM(e2.ruta_archivo) != ''
                    AND (
                        t2.numero < t.numero
                        OR (
                            t2.numero = t.numero
                            AND e2.numero < e.numero
                        )
                    )
            )
    """
    cursor.execute(consulta)
    return cursor.fetchall()

# Obtiene los elementos pendientes del ciclo compartido.
# Solo reinicia cuando no queda ninguna película ni episodio pendiente.
def obtener_contenido_pendiente_ciclo():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    try:
        pendientes = _consultar_contenido_pendiente(cursor)
        if not pendientes:
            cursor.execute("DELETE FROM historial_ciclo_peliculas")
            cursor.execute("DELETE FROM historial_ciclo_episodios")
            pendientes = _consultar_contenido_pendiente(cursor)
        conexion.commit()
        return pendientes
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()

# Mantiene la función anterior para no romper referencias existentes.
# Ya no reinicia el ciclo de películas por separado.
def obtener_peliculas_ciclo():
    pendientes = obtener_contenido_pendiente_ciclo()
    return [
        contenido
        for contenido in pendientes
        if contenido["tipo"] == "pelicula"
    ]

# Marca una película como emitida durante el ciclo.
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

# Marca un episodio como emitido durante el ciclo.
def marcar_episodio_emitido(episodio_id):
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            INSERT IGNORE INTO historial_ciclo_episodios (episodio_id)
            VALUES (%s)
            """,
            (episodio_id,)
        )
        conexion.commit()
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
