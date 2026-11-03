import os
import math
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from backend.database import (
    obtener_peliculas,
    obtener_series,
    obtener_contenido,
    obtener_siguiente_episodio,
    conectar,
    obtener_peliculas_ciclo,
    marcar_pelicula_emitida,
    obtener_catalogo_usuario,
    agregar_catalogo_usuario,
    eliminar_catalogo_usuario,
    obtener_catalogo_preestablecido,
    agregar_pelicula_catalogo
)

from backend.random_engine import seleccionar_contenido
from backend.state_manager import obtener_progreso, guardar_progreso

app = Flask(__name__)
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",
                "http://127.0.0.1:5173"
            ],
            "methods": ["GET", "POST", "PUT","DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    }
)

# Carpeta raíz del proyecto PlayChannel
CARPETA_PROYECTO = Path(__file__).resolve().parent.parent
# Carpeta donde se almacenarán los videos importados
CARPETA_MEDIA = CARPETA_PROYECTO / "media"
CARPETA_MEDIA.mkdir(parents=True, exist_ok=True)
# Carpeta donde se almacenarán las portadas del catálogo
CARPETA_PORTADAS = CARPETA_MEDIA / "portadas"
CARPETA_PORTADAS.mkdir(parents=True, exist_ok=True)

# Tamaño máximo permitido: 2 GB por archivo.
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024 * 1024

EXTENSIONES_PERMITIDAS = {".mp4", ".mkv", ".webm", ".avi", ".mov"}
EXTENSIONES_IMAGEN = {".png", ".jpg", "jpeg"}

@app.route("/")
def inicio():
    return jsonify({
        "mensaje": "API de Play Channel funcionando"
    })


@app.route("/api/peliculas")
def listar_peliculas():
    return jsonify(obtener_peliculas())

# Registrar una película y guardar su archivo de video
@app.route("/api/peliculas", methods=["POST"])
def agregar_pelicula():
    titulo = request.form.get("titulo", "").strip()
    anio = request.form.get("anio", "").strip()
    duracion = request.form.get("duracion", "").strip()
    archivo = request.files.get("archivo")
    if not titulo or not anio or not duracion or not archivo:
        return jsonify({
            "error": "Debes completar todos los campos y seleccionar un video."
        }), 400
    try:
        anio = int(anio)
        duracion = int(duracion)
        if anio < 1888 or anio > 2100 or duracion <= 0:
            raise ValueError()
    except ValueError:
        return jsonify({
            "error": "El año o la duración no son válidos."
        }), 400
    nombre_original = secure_filename(archivo.filename or "")
    extension = Path(nombre_original).suffix.lower()
    if not nombre_original or extension not in EXTENSIONES_PERMITIDAS:
        return jsonify({
            "error": "Selecciona un archivo de video compatible."
        }), 400

    # Crear un nombre único para evitar sobrescribir otros videos.
    import uuid
    nombre_archivo = f"{uuid.uuid4().hex}{extension}"
    ruta_destino = CARPETA_MEDIA / nombre_archivo
    conexion = None
    cursor = None
    try:
        archivo.save(ruta_destino)
        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO peliculas (titulo, anio, duracion, ruta_archivo)
            VALUES (%s, %s, %s, %s)
            """,
            (titulo, anio, duracion, str(ruta_destino.resolve()))
        )
        pelicula_id = cursor.lastrowid

        # Agregar la película propia a la biblioteca del usuario.
        cursor.execute(
            """
            INSERT INTO catalogo_usuario (tipo_contenido, contenido_id)
            VALUES (%s, %s)
            """,
            ("pelicula", pelicula_id)
        )
        conexion.commit()
        return jsonify({
            "mensaje": "Película registrada correctamente.",
            "id": cursor.lastrowid,
            "titulo": titulo
        }), 201
    except Exception:
        if conexion is not None:
            conexion.rollback()
        if ruta_destino.exists():
            ruta_destino.unlink()
        app.logger.exception("Error al registrar la película.")
        return jsonify({
            "error": "No se pudo registrar la película en la base de datos."
        }), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()

@app.route("/api/peliculas/<int:pelicula_id>", methods=["DELETE", "OPTIONS"])
def eliminar_pelicula(pelicula_id):
    conexion = None
    cursor = None
    ruta_archivo = None
    try:
        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, titulo, ruta_archivo FROM peliculas WHERE id = %s",
            (pelicula_id,)
        )
        pelicula = cursor.fetchone()
        if pelicula is None:
            return jsonify({"error": "La película no existe."}), 404
        if pelicula["ruta_archivo"]:
            ruta = Path(pelicula["ruta_archivo"]).resolve()
            if not ruta.is_relative_to(CARPETA_MEDIA.resolve()):
                return jsonify({"error": "Ruta de archivo no permitida."}), 403
            ruta_archivo = ruta
        cursor.execute(
            "DELETE FROM progreso WHERE pelicula_id = %s",
            (pelicula_id,)
        )
        cursor.execute(
            "DELETE FROM peliculas WHERE id = %s",
            (pelicula_id,)
        )
        conexion.commit()
        if ruta_archivo and ruta_archivo.is_file():
            try:
                ruta_archivo.unlink()
            except OSError:
                app.logger.exception("No se pudo borrar el archivo de video.")
        return jsonify({
            "mensaje": "Película eliminada correctamente."
        }), 200
    except Exception:
        if conexion is not None:
            conexion.rollback()
        app.logger.exception("Error al eliminar la película.")
        return jsonify({"error": "No se pudo eliminar la película."}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()

# Reproducir una película registrada en MySQL
@app.route("/api/peliculas/<int:pelicula_id>/video")
def reproducir_pelicula(pelicula_id):
    conexion = None
    cursor = None
    try:
        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT ruta_archivo FROM peliculas WHERE id = %s",
            (pelicula_id,)
        )
        pelicula = cursor.fetchone()
        if not pelicula or not pelicula["ruta_archivo"]:
            return jsonify({
                "error": "La película no tiene un archivo registrado."
            }), 404
        ruta = Path(pelicula["ruta_archivo"]).resolve()

        # Permitir únicamente archivos dentro de la carpeta multimedia.
        if not ruta.is_relative_to(CARPETA_MEDIA.resolve()):
            return jsonify({
                "error": "La ruta del archivo no está permitida."
            }), 403
        if not ruta.is_file():
            return jsonify({
                "error": "No se encontró el archivo de video."
            }), 404
        return send_file(
            ruta,
            conditional=True,
            mimetype="video/mp4" if ruta.suffix.lower() == ".mp4" else None
        )
    except Exception:
        app.logger.exception("Error al reproducir la película.")
        return jsonify({
            "error": "No se pudo abrir el video."
        }), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()

#Mostrar la portada/poster
@app.route("/api/portadas/<path:nombre_archivo>", methods=["GET"])
def mostrar_portada(nombre_archivo):
    try:
        return send_from_directory(CARPETA_PORTADAS, nombre_archivo)
    except Exception:
        return jsonify({
            "error": "Portada no encontrada."
        }), 404

@app.route("/api/series")
def listar_series():
    return jsonify(obtener_series())

# Guardar el progreso de una película
@app.route("/api/peliculas/<int:pelicula_id>/progreso", methods=["POST"])
def actualizar_progreso_pelicula(pelicula_id):
    datos = request.get_json(silent=True) or {}
    try:
        posicion = float(datos.get("posicion", 0))
        terminado = datos.get("terminado", False)
        if not math.isfinite(posicion) or posicion < 0:
            raise ValueError()
        if not isinstance(terminado, bool):
            raise ValueError()
    except (TypeError, ValueError):
        return jsonify({
            "error": "La posición o el estado del video no son válidos."
        }), 400
    conexion = None
    cursor = None
    try:
        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT id FROM peliculas WHERE id = %s",
            (pelicula_id,)
        )
        if cursor.fetchone() is None:
            return jsonify({"error": "La película no existe."}), 404
        guardar_progreso(
            pelicula_id=pelicula_id,
            posicion=posicion,
            terminado=terminado
        )
        if terminado:
            marcar_pelicula_emitida(pelicula_id)
        return jsonify({
            "mensaje": "Progreso guardado correctamente."
        })
    except Exception:
        app.logger.exception("Error al guardar el progreso.")
        return jsonify({
            "error": "No se pudo guardar el progreso."
        }), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()

# Consultar el progreso de una película
@app.route("/api/peliculas/<int:pelicula_id>/progreso", methods=["GET"])
def consultar_progreso_pelicula(pelicula_id):
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            "SELECT id FROM peliculas WHERE id = %s",
            (pelicula_id,)
        )
        if cursor.fetchone() is None:
            return jsonify({"error": "La película no existe."}), 404
    finally:
        cursor.close()
        conexion.close()
    progreso = obtener_progreso(pelicula_id=pelicula_id)
    if progreso is None:
        return jsonify({
            "posicion": 0,
            "terminado": False
        })
    return jsonify({
        "posicion": float(progreso["posicion"]),
        "terminado": bool(progreso["terminado"])
    })

# Selecciona aleatoriamente una película que todavía no se ha emitido en el ciclo.
@app.route("/api/canal/siguiente")
def siguiente_contenido():
    try:
        peliculas = obtener_peliculas_ciclo()
        seleccionada = seleccionar_contenido(peliculas)
        if seleccionada is None:
            return jsonify({
                "mensaje": "No hay películas con videos disponibles."
            }), 404
        progreso = obtener_progreso(
            pelicula_id=seleccionada["id"]
        )
        return jsonify({
            "id": seleccionada["id"],
            "titulo": seleccionada["titulo"],
            "tipo": "pelicula",
            "anio": seleccionada.get("anio"),
            "duracion": seleccionada.get("duracion"),
            "ruta_archivo": seleccionada["ruta_archivo"],
            "posicion": (
                progreso["posicion"] if progreso else 0
            ),
            "terminado": (
                bool(progreso["terminado"]) if progreso else False
            )
        })
    except Exception:
        app.logger.exception("Error al seleccionar la siguiente película.")
        return jsonify({
            "mensaje": "No se pudo seleccionar la siguiente película."
        }), 500

# Obtiene el contenido que el usuario agregó a Mi contenido.
@app.route("/api/mi-contenido", methods=["GET"])
def obtener_mi_contenido():
    try:
        contenido = obtener_catalogo_usuario()
        return jsonify(contenido), 200
    except Exception:
        app.logger.exception("Error al obtener Mi contenido.")
        return jsonify({
            "mensaje": "No se pudo obtener Mi contenido."
        }), 500

# Agrega una película o serie del catálogo a Mi contenido.
@app.route("/api/mi-contenido", methods=["POST"])
def agregar_a_mi_contenido():
    datos = request.get_json(silent=True) or {}
    tipo = datos.get("tipo_contenido")
    contenido_id = datos.get("contenido_id")
    if tipo not in ("pelicula", "serie"):
        return jsonify({"mensaje": "Tipo de contenido inválido."}), 400
    if isinstance(contenido_id, bool) or not isinstance(contenido_id, int) or contenido_id <= 0:
        return jsonify({"mensaje": "ID de contenido inválido."}), 400
    try:
        agregado = agregar_catalogo_usuario(tipo, contenido_id)
        if not agregado:
            return jsonify({
                "mensaje": "El contenido no existe o ya está agregado."
            }), 409
        return jsonify({
            "mensaje": "Contenido agregado correctamente."
        }), 201
    except Exception:
        app.logger.exception("Error al agregar contenido.")
        return jsonify({
            "mensaje": "No se pudo agregar el contenido."
        }), 500

# Elimina una película o serie de Mi contenido sin borrar el original.
@app.route("/api/mi-contenido/<tipo>/<int:contenido_id>", methods=["DELETE"])
def quitar_de_mi_contenido(tipo, contenido_id):
    if tipo not in ("pelicula", "serie"):
        return jsonify({"mensaje": "Tipo de contenido inválido."}), 400
    try:
        eliminado = eliminar_catalogo_usuario(tipo, contenido_id)
        if not eliminado:
            return jsonify({
                "mensaje": "El contenido no estaba en Mi contenido."
            }), 404
        return jsonify({
            "mensaje": "Contenido eliminado de Mi contenido."
        }), 200
    except Exception:
        app.logger.exception("Error al quitar contenido.")
        return jsonify({
            "mensaje": "No se pudo quitar el contenido."
        }), 500

# Obtiene el contenido incorporado por el administrador al catálogo.
@app.route("/api/catalogo", methods=["GET"])
def listar_catalogo():
    try:
        contenido = obtener_catalogo_preestablecido()
        return jsonify(contenido), 200
    except Exception:
        app.logger.exception("Error al consultar el catálogo.")
        return jsonify({
            "mensaje": "No se pudo obtener el catálogo."
        }), 500

# Incorpora una película existente al catálogo preestablecido.
@app.route("/api/admin/catalogo/peliculas/<int:pelicula_id>", methods=["POST"])
def admin_agregar_pelicula_catalogo(pelicula_id):
    try:
        agregado = agregar_pelicula_catalogo(pelicula_id)
        if not agregado:
            return jsonify({
                "mensaje": "La película no existe o ya pertenece al catálogo."
            }), 409
        return jsonify({
            "mensaje": "Película agregada al catálogo correctamente."
        }), 201
    except Exception:
        app.logger.exception("Error al agregar película al catálogo.")
        return jsonify({
            "mensaje": "No se pudo agregar la película al catálogo."
        }), 500

# Obtener las películas del catálogo preestablecido para administración.
@app.route("/api/admin/peliculas", methods=["GET"])
def admin_listar_peliculas():
    try:
        contenido = obtener_catalogo_preestablecido()
        peliculas = [
            item for item in contenido
            if item["tipo_contenido"] == "pelicula"
        ]
        return jsonify(peliculas), 200
    except Exception:
        app.logger.exception("Error al obtener películas de administración.")
        return jsonify({
            "mensaje": "No se pudieron obtener las películas."
        }), 500

# Registra una película desde administración y la incorpora al catálogo preestablecido.
@app.route("/api/admin/peliculas", methods=["POST"])
def admin_registrar_pelicula():
    import uuid
    titulo = request.form.get("titulo", "").strip()
    anio = request.form.get("anio", "").strip()
    duracion = request.form.get("duracion", "").strip()
    archivo = request.files.get("archivo")
    portada = request.files.get("portada")

    # Validar los campos obligatorios.
    if not titulo or not anio or not duracion or not archivo:
        return jsonify({
            "mensaje": "Debes completar todos los campos y seleccionar un video."
        }), 400

    # Validar año y duración.
    try:
        anio = int(anio)
        duracion = int(duracion)
        if anio < 1888 or anio > 2100 or duracion <= 0:
            raise ValueError()
    except ValueError:
        return jsonify({
            "mensaje": "El año o la duración no son válidos."
        }), 400

    # Validar el video.
    nombre_original = secure_filename(archivo.filename or "")
    extension = Path(nombre_original).suffix.lower()
    if not nombre_original or extension not in EXTENSIONES_PERMITIDAS:
        return jsonify({
            "mensaje": "Selecciona un archivo de video compatible."
        }), 400

    # Validar la portada si se seleccionó una.
    nombre_portada = None
    ruta_portada = None
    if portada and portada.filename:
        nombre_original_portada = secure_filename(portada.filename)
        extension_portada = Path(nombre_original_portada).suffix.lower()
        if extension_portada not in EXTENSIONES_IMAGEN:
            return jsonify({
                "mensaje": "La portada debe estar en formato PNG o JPG."
            }), 400
        nombre_portada = f"{uuid.uuid4().hex}{extension_portada}"
        ruta_portada = CARPETA_PORTADAS / nombre_portada

    # Generar un nombre único para el video.
    nombre_archivo = f"{uuid.uuid4().hex}{extension}"
    ruta_destino = CARPETA_MEDIA / nombre_archivo
    conexion = None
    cursor = None
    try:
        # Guardar los archivos.
        archivo.save(ruta_destino)
        if portada and portada.filename:
            portada.save(ruta_portada)
        conexion = conectar()
        cursor = conexion.cursor()

        # Registrar la película en la tabla principal.
        cursor.execute(
            """
            INSERT INTO peliculas
            (titulo, anio, duracion, ruta_archivo, ruta_portada)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                titulo,
                anio,
                duracion,
                str(ruta_destino.resolve()),
                nombre_portada
            )
        )
        pelicula_id = cursor.lastrowid
        # Incorporar la película al catálogo preestablecido.
        cursor.execute(
            """
            INSERT INTO catalogo_preestablecido
            (tipo_contenido, contenido_id)
            VALUES (%s, %s)
            """,
            ("pelicula", pelicula_id)
        )
        conexion.commit()
        return jsonify({
            "mensaje": "Película registrada y agregada al catálogo correctamente.",
            "id": pelicula_id,
            "titulo": titulo,
            "ruta_portada": nombre_portada
        }), 201
    except Exception:
        if conexion is not None:
            conexion.rollback()
        # Eliminar archivos si el registro falla.
        if ruta_destino.exists():
            ruta_destino.unlink()
        if ruta_portada and ruta_portada.exists():
            ruta_portada.unlink()
        app.logger.exception("Error al registrar película desde administración.")
        return jsonify({
            "mensaje": "No se pudo registrar la película."
        }), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()

# Editar una película existente del catálogo preestablecido.
@app.route("/api/admin/peliculas/<int:pelicula_id>", methods=["PUT"])
def admin_editar_pelicula(pelicula_id):
    import uuid
    conexion = None
    cursor = None
    ruta_video_nueva = None
    ruta_portada_nueva = None
    try:
        titulo = request.form.get("titulo", "").strip()
        anio = request.form.get("anio", "").strip()
        duracion = request.form.get("duracion", "").strip()
        archivo = request.files.get("archivo")
        portada = request.files.get("portada")

        # Validar campos obligatorios.
        if not titulo or not anio or not duracion:
            return jsonify({
                "mensaje": "Debes completar todos los campos."
            }), 400

        # Validar año y duración.
        try:
            anio = int(anio)
            duracion = int(duracion)
            if anio < 1888 or anio > 2100 or duracion <= 0:
                raise ValueError()
        except ValueError:
            return jsonify({
                "mensaje": "El año o la duración no son válidos."
            }), 400
        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)

        # Verificar que la película pertenezca al catálogo preestablecido.
        cursor.execute(
            """
            SELECT p.id, p.ruta_archivo, p.ruta_portada
            FROM peliculas p
            INNER JOIN catalogo_preestablecido cp
                ON cp.contenido_id = p.id
                AND cp.tipo_contenido = 'pelicula'
            WHERE p.id = %s
            """,
            (pelicula_id,)
        )
        pelicula = cursor.fetchone()
        if not pelicula:
            return jsonify({
                "mensaje": "No se encontró la película en el catálogo."
            }), 404
        ruta_video_actual = pelicula["ruta_archivo"]
        ruta_portada_actual = pelicula["ruta_portada"]

        # Mantener los archivos actuales si no se seleccionan reemplazos.
        ruta_video_final = ruta_video_actual
        ruta_portada_final = ruta_portada_actual

        # Procesar video nuevo, si corresponde.
        if archivo and archivo.filename:
            nombre_video = secure_filename(archivo.filename)
            extension_video = Path(nombre_video).suffix.lower()
            if extension_video not in EXTENSIONES_PERMITIDAS:
                return jsonify({
                    "mensaje": "Selecciona un archivo de video compatible."
                }), 400
            nombre_video_nuevo = f"{uuid.uuid4().hex}{extension_video}"
            ruta_video_nueva = CARPETA_MEDIA / nombre_video_nuevo
            archivo.save(ruta_video_nueva)
            ruta_video_final = str(ruta_video_nueva.resolve())

        # Procesar portada nueva, si corresponde.
        if portada and portada.filename:
            nombre_portada = secure_filename(portada.filename)
            extension_portada = Path(nombre_portada).suffix.lower()
            if extension_portada not in EXTENSIONES_IMAGEN:
                return jsonify({
                    "mensaje": "La portada debe estar en formato PNG o JPG."
                }), 400
            nombre_portada_nuevo = f"{uuid.uuid4().hex}{extension_portada}"
            ruta_portada_nueva = CARPETA_PORTADAS / nombre_portada_nuevo
            portada.save(ruta_portada_nueva)
            ruta_portada_final = nombre_portada_nuevo
        # Actualizar los datos de la película.
        cursor.execute(
            """
            UPDATE peliculas
            SET titulo = %s,
                anio = %s,
                duracion = %s,
                ruta_archivo = %s,
                ruta_portada = %s
            WHERE id = %s
            """,
            (
                titulo,
                anio,
                duracion,
                ruta_video_final,
                ruta_portada_final,
                pelicula_id
            )
        )
        conexion.commit()
        # Eliminar archivos anteriores solamente después del commit.
        if ruta_video_nueva and ruta_video_actual:
            ruta_anterior = Path(ruta_video_actual)
            if ruta_anterior.parent.resolve() == CARPETA_MEDIA.resolve():
                if ruta_anterior.exists():
                    ruta_anterior.unlink()
        if ruta_portada_nueva and ruta_portada_actual:
            ruta_anterior = CARPETA_PORTADAS / Path(ruta_portada_actual).name
            if ruta_anterior.exists():
                ruta_anterior.unlink()
        return jsonify({
            "mensaje": "Película actualizada correctamente.",
            "id": pelicula_id,
            "titulo": titulo,
            "ruta_portada": ruta_portada_final
        }), 200
    except Exception:
        if conexion is not None:
            conexion.rollback()
        # Eliminar archivos nuevos si la actualización falla.
        if ruta_video_nueva and ruta_video_nueva.exists():
            ruta_video_nueva.unlink()
        if ruta_portada_nueva and ruta_portada_nueva.exists():
            ruta_portada_nueva.unlink()
        app.logger.exception("Error al editar película desde administración.")
        return jsonify({
            "mensaje": "No se pudo actualizar la película."
        }), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()

# Elimina definitivamente una película del catálogo preestablecido.
@app.route("/api/admin/peliculas/<int:pelicula_id>", methods=["DELETE"])
def admin_eliminar_pelicula(pelicula_id):
    conexion = None
    cursor = None
    ruta_video = None
    ruta_portada = None
    try:
        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)
        # Buscar la película y comprobar que pertenezca al catálogo.
        cursor.execute(
            """
            SELECT p.id, p.ruta_archivo, p.ruta_portada
            FROM peliculas p
            INNER JOIN catalogo_preestablecido cp
                ON cp.contenido_id = p.id
                AND cp.tipo_contenido = 'pelicula'
            WHERE p.id = %s
            """,
            (pelicula_id,)
        )
        pelicula = cursor.fetchone()
        if not pelicula:
            return jsonify({
                "mensaje": "No se encontró la película en el catálogo."
            }), 404
        # Preparar las rutas de los archivos que se eliminarán.
        if pelicula["ruta_archivo"]:
            ruta_candidata = Path(pelicula["ruta_archivo"]).resolve()
            if ruta_candidata.parent == CARPETA_MEDIA.resolve():
                ruta_video = ruta_candidata
        if pelicula["ruta_portada"]:
            ruta_candidata = (
                CARPETA_PORTADAS / Path(pelicula["ruta_portada"]).name
            ).resolve()
            if ruta_candidata.parent == CARPETA_PORTADAS.resolve():
                ruta_portada = ruta_candidata
        # Eliminar registros relacionados con la película.
        cursor.execute(
            "DELETE FROM progreso WHERE pelicula_id = %s",
            (pelicula_id,)
        )
        cursor.execute(
            """
            DELETE FROM catalogo_usuario
            WHERE tipo_contenido = 'pelicula'
                AND contenido_id = %s
            """,
            (pelicula_id,)
        )
        cursor.execute(
            """
            DELETE FROM catalogo_preestablecido
            WHERE tipo_contenido = 'pelicula'
                AND contenido_id = %s
            """,
            (pelicula_id,)
        )
        # El historial se elimina automáticamente por ON DELETE CASCADE.
        cursor.execute(
            "DELETE FROM peliculas WHERE id = %s",
            (pelicula_id,)
        )
        conexion.commit()
        # Eliminar los archivos físicos después de confirmar la transacción.
        for ruta in (ruta_video, ruta_portada):
            if ruta and ruta.is_file():
                try:
                    ruta.unlink()
                except OSError:
                    app.logger.exception(
                        "No se pudo eliminar el archivo: %s", ruta
                    )
        return jsonify({
            "mensaje": "Película eliminada correctamente.",
            "id": pelicula_id
        }), 200
    except Exception:
        if conexion is not None:
            conexion.rollback()
        app.logger.exception(
            "Error al eliminar película desde administración."
        )
        return jsonify({
            "mensaje": "No se pudo eliminar la película."
        }), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()

if __name__ == "__main__":
    app.run(debug=True, port=5000)