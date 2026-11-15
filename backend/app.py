import os
import math
import uuid
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
    obtener_contenido_pendiente_ciclo,
    marcar_episodio_emitido,
    obtener_catalogo_usuario,
    agregar_catalogo_usuario,
    eliminar_catalogo_usuario,
    obtener_catalogo_preestablecido,
    obtener_estadisticas_catalogo,
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
EXTENSIONES_IMAGEN = {".png", ".jpg", ".jpeg"}

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

# Reproducir un episodio registrado en MySQL.
@app.route("/api/episodios/<int:episodio_id>/video", methods=["GET"])
def reproducir_episodio(episodio_id):
    conexion = None
    cursor = None
    try:
        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT ruta_archivo FROM episodios WHERE id = %s",
            (episodio_id,)
        )
        episodio = cursor.fetchone()
        if not episodio or not episodio["ruta_archivo"]:
            return jsonify({"error": "El episodio no tiene un archivo registrado."}), 404
        ruta = Path(episodio["ruta_archivo"]).resolve()
        if not ruta.is_relative_to(CARPETA_MEDIA.resolve()):
            return jsonify({"error": "La ruta del archivo no está permitida."}), 403
        if not ruta.is_file():
            return jsonify({"error": "No se encontró el archivo de video."}), 404
        return send_file(
            ruta, conditional=True,
            mimetype="video/mp4" if ruta.suffix.lower() == ".mp4" else None
        )
    except Exception:
        app.logger.exception("Error al reproducir el episodio.")
        return jsonify({"error": "No se pudo abrir el video."}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()

# Guardar el progreso de un episodio.
@app.route("/api/episodios/<int:episodio_id>/progreso", methods=["POST"])
def actualizar_progreso_episodio(episodio_id):
    datos = request.get_json(silent=True) or {}
    try:
        posicion = float(datos.get("posicion", 0))
        terminado = datos.get("terminado", False)
        if not math.isfinite(posicion) or posicion < 0 or not isinstance(terminado, bool):
            raise ValueError()
    except (TypeError, ValueError):
        return jsonify({"error": "La posición o el estado del video no son válidos."}), 400
    conexion = None
    cursor = None
    try:
        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT id FROM episodios WHERE id = %s", (episodio_id,))
        if cursor.fetchone() is None:
            return jsonify({"error": "El episodio no existe."}), 404
        cursor.execute(
            "SELECT id FROM progreso WHERE episodio_id = %s ORDER BY id DESC LIMIT 1",
            (episodio_id,)
        )
        registro = cursor.fetchone()
        if registro:
            cursor.execute(
                "UPDATE progreso SET posicion = %s, terminado = %s WHERE id = %s",
                (posicion, terminado, registro["id"])
            )
        else:
            cursor.execute(
                "INSERT INTO progreso (episodio_id, posicion, terminado) VALUES (%s, %s, %s)",
                (episodio_id, posicion, terminado)
            )
        conexion.commit()
    except Exception:
        if conexion is not None:
            conexion.rollback()
        app.logger.exception("Error al guardar el progreso del episodio.")
        return jsonify({"error": "No se pudo guardar el progreso del episodio."}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()
    if terminado:
        try:
            marcar_episodio_emitido(episodio_id)
        except Exception:
            app.logger.exception("El progreso se guardó, pero no se pudo registrar el episodio como emitido.")
            return jsonify({"error": "El progreso se guardó, pero no se pudo actualizar el ciclo."}), 500
    return jsonify({"mensaje": "Progreso del episodio guardado correctamente."}), 200

# Consultar el progreso de un episodio.
@app.route("/api/episodios/<int:episodio_id>/progreso", methods=["GET"])
def consultar_progreso_episodio(episodio_id):
    conexion = None
    cursor = None
    try:
        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT id FROM episodios WHERE id = %s", (episodio_id,))
        if cursor.fetchone() is None:
            return jsonify({"error": "El episodio no existe."}), 404
        cursor.execute(
            "SELECT posicion, terminado FROM progreso WHERE episodio_id = %s ORDER BY id DESC LIMIT 1",
            (episodio_id,)
        )
        progreso = cursor.fetchone()
        return jsonify({
            "posicion": float(progreso["posicion"]) if progreso else 0,
            "terminado": bool(progreso["terminado"]) if progreso else False
        }), 200
    except Exception:
        app.logger.exception("Error al consultar el progreso del episodio.")
        return jsonify({"error": "No se pudo consultar el progreso del episodio."}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()

# Selecciona aleatoriamente una película o episodio pendiente del ciclo compartido.
@app.route("/api/canal/siguiente", methods=["GET"])
def siguiente_contenido():
    try:
        contenido = obtener_contenido_pendiente_ciclo()
        seleccionada = seleccionar_contenido(contenido)
        if seleccionada is None:
            return jsonify({
                "mensaje": "No hay contenido disponible para reproducir."
            }), 404
        tipo = seleccionada["tipo"]
        if tipo == "pelicula":
            progreso = obtener_progreso(pelicula_id=seleccionada["id"])
            return jsonify({
                "id": seleccionada["id"],
                "titulo": seleccionada["titulo"],
                "tipo": "pelicula",
                "anio": seleccionada.get("anio"),
                "duracion": seleccionada.get("duracion"),
                "ruta_archivo": seleccionada["ruta_archivo"],
                "posicion": progreso["posicion"] if progreso else 0,
                "terminado": bool(progreso["terminado"]) if progreso else False
            }), 200
        if tipo == "episodio":
            conexion = conectar()
            cursor = conexion.cursor(dictionary=True)
            try:
                cursor.execute(
                    "SELECT posicion, terminado FROM progreso "
                    "WHERE episodio_id = %s ORDER BY id DESC LIMIT 1",
                    (seleccionada["id"],)
                )
                progreso = cursor.fetchone()
            finally:
                cursor.close()
                conexion.close()
            return jsonify({
                "id": seleccionada["id"],
                "episodio_id": seleccionada["id"],
                "serie_id": seleccionada["serie_id"],
                "titulo": seleccionada["titulo"],
                "tipo": "episodio",
                "anio": seleccionada.get("anio"),
                "duracion": seleccionada.get("duracion"),
                "ruta_archivo": seleccionada["ruta_archivo"],
                "temporada": seleccionada["temporada"],
                "numero_episodio": seleccionada["episodio"],
                "posicion": float(progreso["posicion"]) if progreso else 0,
                "terminado": bool(progreso["terminado"]) if progreso else False
            }), 200
        return jsonify({"mensaje": "Tipo de contenido no válido."}), 500
    except Exception:
        app.logger.exception("Error al seleccionar el siguiente contenido.")
        return jsonify({
            "mensaje": "No se pudo seleccionar el siguiente contenido."
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

#Obtiene las estadísticas del catálogo para el dashboard administrativo.
@app.route("/api/admin/estadisticas", methods=["GET"])
def admin_estadisticas():
    try:
        estadisticas = obtener_estadisticas_catalogo()
        return jsonify(estadisticas), 200
    except Exception:
        app.logger.exception("Error al obtener las estadísticas del catálogo.")
        return jsonify({
            "mensaje": "No se pudieron obtener las estadísticas."
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

# Eliminar individualmente el video o la portada de una película.
@app.route(
    "/api/admin/peliculas/<int:pelicula_id>/archivo/<tipo>",
    methods=["DELETE"]
)
def admin_eliminar_archivo_pelicula(pelicula_id, tipo):
    if tipo not in ("video", "portada"):
        return jsonify({
            "mensaje": "Tipo de archivo no válido."
        }), 400
    conexion = None
    cursor = None
    ruta_archivo = None
    try:
        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.id, p.ruta_archivo, p.ruta_portada
            FROM peliculas p
            INNER JOIN catalogo_preestablecido cp
                ON cp.contenido_id = p.id
                AND cp.tipo_contenido = 'pelicula'
            WHERE p.id = %s
        """, (pelicula_id,))
        pelicula = cursor.fetchone()
        if not pelicula:
            return jsonify({
                "mensaje": "No se encontró la película."
            }), 404
        if tipo == "video":
            ruta_actual = pelicula["ruta_archivo"]
            columna = "ruta_archivo"
            if ruta_actual:
                ruta_candidata = Path(ruta_actual).resolve()
                if ruta_candidata.parent != CARPETA_MEDIA.resolve():
                    return jsonify({
                        "mensaje": "La ruta del video no está permitida."
                    }), 403
                ruta_archivo = ruta_candidata
        else:
            ruta_actual = pelicula["ruta_portada"]
            columna = "ruta_portada"
            if ruta_actual:
                ruta_candidata = (
                    CARPETA_PORTADAS / Path(ruta_actual).name
                ).resolve()
                if ruta_candidata.parent != CARPETA_PORTADAS.resolve():
                    return jsonify({
                        "mensaje": "La ruta de la portada no está permitida."
                    }), 403
                ruta_archivo = ruta_candidata
        if not ruta_actual:
            return jsonify({
                "mensaje": "La película no tiene ese archivo registrado."
            }), 404
        cursor.execute(
            f"UPDATE peliculas SET {columna} = NULL WHERE id = %s",
            (pelicula_id,)
        )
        conexion.commit()
        # Eliminar el archivo físico después de actualizar la base de datos.
        if ruta_archivo and ruta_archivo.is_file():
            try:
                ruta_archivo.unlink()
            except OSError:
                app.logger.exception(
                    "No se pudo eliminar el archivo físico."
                )
        return jsonify({
            "mensaje": (
                "Video eliminado correctamente."
                if tipo == "video"
                else "Portada eliminada correctamente."
            )
        }), 200
    except Exception:
        if conexion is not None:
            conexion.rollback()
        app.logger.exception("Error al eliminar archivo de película.")
        return jsonify({
            "mensaje": "No se pudo eliminar el archivo."
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

# ADMINISTRACIÓN DE SERIES
# Funciones auxiliares
def guardar_video_episodio(archivo):
    """Guarda un video de episodio y devuelve su ruta."""
    if not archivo or not archivo.filename:
        return None
    nombre_original = secure_filename(archivo.filename)
    extension = Path(nombre_original).suffix.lower()
    if extension not in EXTENSIONES_PERMITIDAS:
        raise ValueError("El formato del video no es compatible.")
    nombre_archivo = f"{uuid.uuid4().hex}{extension}"
    ruta_destino = CARPETA_MEDIA / nombre_archivo
    archivo.save(ruta_destino)
    return str(ruta_destino.resolve())

def eliminar_video(ruta):
    """Elimina un video si está dentro de la carpeta media."""
    if not ruta:
        return
    try:
        ruta_archivo = Path(ruta).resolve()
        carpeta_media = CARPETA_MEDIA.resolve()
        if ruta_archivo.parent == carpeta_media and ruta_archivo.is_file():
            ruta_archivo.unlink()
    except (OSError, ValueError):
        app.logger.exception("No se pudo eliminar el archivo de video.")

def obtener_serie_completa(cursor, serie_id):
    """Obtiene una serie con sus temporadas y episodios."""
    cursor.execute(
        """
        SELECT id, titulo, anio, descripcion, ruta_portada
        FROM series
        WHERE id = %s
        """,
        (serie_id,)
    )
    serie = cursor.fetchone()
    if not serie:
        return None
    cursor.execute(
        """
        SELECT id, numero
        FROM temporadas
        WHERE serie_id = %s
        ORDER BY numero
        """,
        (serie_id,)
    )
    temporadas = cursor.fetchall()
    for temporada in temporadas:
        cursor.execute(
            """
            SELECT id, numero, titulo, duracion, ruta_archivo
            FROM episodios
            WHERE temporada_id = %s
            ORDER BY numero
            """,
            (temporada["id"],)
        )
        temporada["episodios"] = cursor.fetchall()
    serie["temporadas"] = temporadas
    return serie

# LISTAR SERIES DEL CATÁLOGO PREESTABLECIDO
@app.route("/api/admin/series", methods=["GET"])
def admin_listar_series():
    conexion = None
    cursor = None
    try:
        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT s.id
            FROM series s
            INNER JOIN catalogo_preestablecido cp
                ON cp.contenido_id = s.id
                AND cp.tipo_contenido = 'serie'
            ORDER BY s.titulo
            """
        )
        registros = cursor.fetchall()
        resultado = []
        for registro in registros:
            serie = obtener_serie_completa(
                cursor,
                registro["id"]
            )
            if serie:
                resultado.append(serie)
        return jsonify(resultado), 200
    except Exception:
        app.logger.exception("Error al listar las series.")
        return jsonify({
            "mensaje": "No se pudieron obtener las series."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()
# ------------------------------------------------------------
# REGISTRAR UNA SERIE
# ------------------------------------------------------------

@app.route("/api/admin/series", methods=["POST"])
def admin_registrar_serie():
    titulo = request.form.get("titulo", "").strip()
    anio = request.form.get("anio", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    portada = request.files.get("portada")
    if not titulo:
        return jsonify({"mensaje": "Debes ingresar el título de la serie."}), 400
    if anio:
        try:
            anio = int(anio)
            if anio < 1888 or anio > 2100:
                raise ValueError()
        except ValueError:
            return jsonify({"mensaje": "El año ingresado no es válido."}), 400
    else:
        anio = None
    ruta_portada = None
    if portada and portada.filename:
        nombre_original = secure_filename(portada.filename)
        extension = Path(nombre_original).suffix.lower()
        if extension not in EXTENSIONES_IMAGEN:
            return jsonify({"mensaje": "La portada debe estar en formato PNG o JPG."}), 400
        nombre_archivo = f"{uuid.uuid4().hex}{extension}"
        ruta_destino = CARPETA_PORTADAS / nombre_archivo
        portada.save(ruta_destino)
        ruta_portada = nombre_archivo
    conexion = None
    cursor = None
    try:
        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO series (titulo, anio, descripcion, ruta_portada)
            VALUES (%s, %s, %s, %s)
            """,
            (titulo, anio, descripcion or None, ruta_portada)
        )
        serie_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO catalogo_preestablecido (tipo_contenido, contenido_id)
            VALUES ('serie', %s)
            """,
            (serie_id,)
        )
        conexion.commit()
        return jsonify({"mensaje": "Serie registrada correctamente.", "id": serie_id}), 201
    except Exception:
        if conexion:
            conexion.rollback()
        if ruta_portada:
            archivo_guardado = CARPETA_PORTADAS / ruta_portada
            if archivo_guardado.exists():
                archivo_guardado.unlink()
        app.logger.exception("Error al registrar la serie.")
        return jsonify({"mensaje": "No se pudo registrar la serie."}), 500
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

# EDITAR UNA SERIE
@app.route("/api/admin/series/<int:serie_id>", methods=["PUT"])
def admin_editar_serie(serie_id):
    titulo = request.form.get("titulo", "").strip()
    anio = request.form.get("anio", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    portada = request.files.get("portada")
    if not titulo:
        return jsonify({"mensaje": "El título de la serie es obligatorio."}), 400
    if anio:
        try:
            anio = int(anio)
            if anio < 1888 or anio > 2100:
                raise ValueError()
        except ValueError:
            return jsonify({"mensaje": "El año ingresado no es válido."}), 400
    else:
        anio = None
    conexion = None
    cursor = None
    ruta_portada_nueva = None
    try:
        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, ruta_portada FROM series WHERE id = %s",
            (serie_id,)
        )
        serie = cursor.fetchone()
        if not serie:
            return jsonify({"mensaje": "La serie no existe."}), 404
        ruta_portada_final = serie["ruta_portada"]
        if portada and portada.filename:
            nombre_original = secure_filename(portada.filename)
            extension = Path(nombre_original).suffix.lower()
            if extension not in EXTENSIONES_IMAGEN:
                return jsonify({"mensaje": "La portada debe estar en formato PNG o JPG."}), 400
            nombre_archivo = f"{uuid.uuid4().hex}{extension}"
            ruta_destino = CARPETA_PORTADAS / nombre_archivo
            portada.save(ruta_destino)
            ruta_portada_nueva = nombre_archivo
            ruta_portada_final = nombre_archivo
        cursor.execute(
            """
            UPDATE series
            SET titulo = %s, anio = %s, descripcion = %s, ruta_portada = %s
            WHERE id = %s
            """,
            (titulo, anio, descripcion or None, ruta_portada_final, serie_id)
        )
        conexion.commit()
        # Si se reemplazó la portada, eliminar la anterior después del commit.
        if ruta_portada_nueva and serie["ruta_portada"]:
            anterior = (CARPETA_PORTADAS / Path(serie["ruta_portada"]).name).resolve()
            if anterior.parent == CARPETA_PORTADAS.resolve() and anterior.is_file():
                try:
                    anterior.unlink()
                except OSError:
                    app.logger.exception("No se pudo eliminar la portada anterior de la serie.")
        return jsonify({"mensaje": "Serie actualizada correctamente."}), 200
    except Exception:
        if conexion:
            conexion.rollback()
        if ruta_portada_nueva:
            nuevo_archivo = CARPETA_PORTADAS / ruta_portada_nueva
            if nuevo_archivo.exists():
                nuevo_archivo.unlink()
        app.logger.exception("Error al editar la serie.")
        return jsonify({"mensaje": "No se pudo actualizar la serie."}), 500
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

@app.route("/api/admin/series/<int:serie_id>/archivo/portada", methods=["DELETE"])
def admin_eliminar_portada_serie(serie_id):
    conexion = None
    cursor = None
    ruta_archivo = None
    try:
        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, ruta_portada FROM series WHERE id = %s",
            (serie_id,)
        )
        serie = cursor.fetchone()
        if not serie:
            return jsonify({"mensaje": "No se encontró la serie."}), 404
        if not serie["ruta_portada"]:
            return jsonify({"mensaje": "La serie no tiene una portada registrada."}), 404
        ruta_archivo = (CARPETA_PORTADAS / Path(serie["ruta_portada"]).name).resolve()
        if ruta_archivo.parent != CARPETA_PORTADAS.resolve():
            return jsonify({"mensaje": "La ruta de la portada no está permitida."}), 403
        cursor.execute(
            "UPDATE series SET ruta_portada = NULL WHERE id = %s",
            (serie_id,)
        )
        conexion.commit()
        if ruta_archivo.is_file():
            try:
                ruta_archivo.unlink()
            except OSError:
                app.logger.exception("No se pudo eliminar el archivo físico de portada.")
        return jsonify({"mensaje": "Portada eliminada correctamente."}), 200
    except Exception:
        if conexion:
            conexion.rollback()
        app.logger.exception("Error al eliminar portada de serie.")
        return jsonify({"mensaje": "No se pudo eliminar la portada."}), 500
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

@app.route("/api/admin/series/<int:serie_id>", methods=["DELETE"])
def admin_eliminar_serie(serie_id):
    conexion = None
    cursor = None
    videos = []
    try:
        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT e.id, e.ruta_archivo
            FROM episodios e
            INNER JOIN temporadas t
                ON e.temporada_id = t.id
            WHERE t.serie_id = %s
            """,
            (serie_id,)
        )
        videos = cursor.fetchall()
        cursor.execute(
            """
            SELECT id
            FROM temporadas
            WHERE serie_id = %s
            """,
            (serie_id,)
        )
        temporadas = cursor.fetchall()
        cursor.execute(
            "SELECT id FROM series WHERE id = %s",
            (serie_id,)
        )
        if not cursor.fetchone():
            return jsonify({
                "mensaje": "La serie no existe."
            }), 404
        # Eliminar el progreso de los episodios.
        for video in videos:
            cursor.execute(
                "DELETE FROM progreso WHERE episodio_id = %s",
                (video["id"],)
            )
        # Eliminar episodios.
        for temporada in temporadas:
            cursor.execute(
                """
                DELETE FROM episodios
                WHERE temporada_id = %s
                """,
                (temporada["id"],)
            )
        # Eliminar temporadas.
        cursor.execute(
            "DELETE FROM temporadas WHERE serie_id = %s",
            (serie_id,)
        )
        # Eliminar referencias de los catálogos.
        cursor.execute(
            """
            DELETE FROM catalogo_preestablecido
            WHERE tipo_contenido = 'serie'
            AND contenido_id = %s
            """,
            (serie_id,)
        )
        cursor.execute(
            """
            DELETE FROM catalogo_usuario
            WHERE tipo_contenido = 'serie'
            AND contenido_id = %s
            """,
            (serie_id,)
        )
        # Eliminar la serie.
        cursor.execute(
            "DELETE FROM series WHERE id = %s",
            (serie_id,)
        )
        conexion.commit()
        # Eliminar los videos después de confirmar los cambios.
        for video in videos:
            eliminar_video(video["ruta_archivo"])
        return jsonify({
            "mensaje": "Serie y contenido eliminado correctamente."
        }), 200
    except Exception:
        if conexion:
            conexion.rollback()
        app.logger.exception("Error al eliminar la serie.")
        return jsonify({
            "mensaje": "No se pudo eliminar la serie."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

# CREAR UNA TEMPORADA
@app.route(
    "/api/admin/series/<int:serie_id>/temporadas",
    methods=["POST"]
)
def admin_crear_temporada(serie_id):
    datos = request.get_json(silent=True) or {}
    numero = datos.get("numero")
    try:
        numero = int(numero)
        if numero <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({
            "mensaje": "El número de temporada no es válido."
        }), 400
    conexion = None
    cursor = None
    try:
        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT id FROM series WHERE id = %s",
            (serie_id,)
        )
        if not cursor.fetchone():
            return jsonify({
                "mensaje": "La serie no existe."
            }), 404
        cursor.execute(
            """
            INSERT INTO temporadas (serie_id, numero)
            VALUES (%s, %s)
            """,
            (serie_id, numero)
        )
        temporada_id = cursor.lastrowid
        conexion.commit()
        return jsonify({
            "mensaje": "Temporada creada correctamente.",
            "id": temporada_id
        }), 201
    except Exception as error:
        if conexion:
            conexion.rollback()
        if getattr(error, "errno", None) == 1062:
            return jsonify({
                "mensaje": "Esta temporada ya existe."
            }), 409
        app.logger.exception("Error al crear la temporada.")
        return jsonify({
            "mensaje": "No se pudo crear la temporada."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()


# ELIMINAR UNA TEMPORADA
@app.route(
    "/api/admin/temporadas/<int:temporada_id>",
    methods=["DELETE"]
)
def admin_eliminar_temporada(temporada_id):
    conexion = None
    cursor = None
    videos = []
    try:
        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, ruta_archivo
            FROM episodios
            WHERE temporada_id = %s
            """,
            (temporada_id,)
        )
        videos = cursor.fetchall()
        cursor.execute(
            "SELECT id FROM temporadas WHERE id = %s",
            (temporada_id,)
        )
        if not cursor.fetchone():
            return jsonify({
                "mensaje": "La temporada no existe."
            }), 404
        for episodio in videos:
            cursor.execute(
                "DELETE FROM progreso WHERE episodio_id = %s",
                (episodio["id"],)
            )
        cursor.execute(
            "DELETE FROM episodios WHERE temporada_id = %s",
            (temporada_id,)
        )
        cursor.execute(
            "DELETE FROM temporadas WHERE id = %s",
            (temporada_id,)
        )
        conexion.commit()
        for episodio in videos:
            eliminar_video(episodio["ruta_archivo"])
        return jsonify({
            "mensaje": "Temporada eliminada correctamente."
        }), 200
    except Exception:
        if conexion:
            conexion.rollback()
        app.logger.exception("Error al eliminar la temporada.")
        return jsonify({
            "mensaje": "No se pudo eliminar la temporada."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

# REGISTRAR UN EPISODIO
@app.route(
    "/api/admin/temporadas/<int:temporada_id>/episodios",
    methods=["POST"]
)
def admin_crear_episodio(temporada_id):
    numero = request.form.get("numero", "").strip()
    titulo = request.form.get("titulo", "").strip()
    duracion = request.form.get("duracion", "").strip()
    archivo = request.files.get("archivo")
    if not numero or not titulo:
        return jsonify({
            "mensaje": "Debes ingresar el número y título del episodio."
        }), 400
    try:
        numero = int(numero)
        if numero <= 0:
            raise ValueError()
        if duracion:
            duracion = int(duracion)
            if duracion <= 0:
                raise ValueError()
        else:
            duracion = None
    except ValueError:
        return jsonify({
            "mensaje": "El número o la duración no son válidos."
        }), 400
    ruta_video = None
    conexion = None
    cursor = None
    try:
        if archivo and archivo.filename:
            ruta_video = guardar_video_episodio(archivo)
        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT id FROM temporadas WHERE id = %s",
            (temporada_id,)
        )
        if not cursor.fetchone():
            if ruta_video:
                eliminar_video(ruta_video)
            return jsonify({
                "mensaje": "La temporada no existe."
            }), 404
        cursor.execute(
            """
            INSERT INTO episodios
            (temporada_id, numero, titulo, duracion, ruta_archivo)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (temporada_id, numero, titulo, duracion, ruta_video)
        )
        episodio_id = cursor.lastrowid
        conexion.commit()
        return jsonify({
            "mensaje": "Episodio registrado correctamente.",
            "id": episodio_id
        }), 201
    except Exception as error:
        if conexion:
            conexion.rollback()
        if ruta_video:
            eliminar_video(ruta_video)
        if getattr(error, "errno", None) == 1062:
            return jsonify({
                "mensaje": "Ya existe un episodio con ese número."
            }), 409
        app.logger.exception("Error al registrar el episodio.")
        return jsonify({
            "mensaje": "No se pudo registrar el episodio."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

# EDITAR UN EPISODIO Y REEMPLAZAR SU VIDEO
@app.route(
    "/api/admin/episodios/<int:episodio_id>",
    methods=["PUT"]
)
def admin_editar_episodio(episodio_id):
    numero = request.form.get("numero", "").strip()
    titulo = request.form.get("titulo", "").strip()
    duracion = request.form.get("duracion", "").strip()
    archivo = request.files.get("archivo")
    if not numero or not titulo:
        return jsonify({
            "mensaje": "Debes ingresar el número y título del episodio."
        }), 400
    try:
        numero = int(numero)
        if numero <= 0:
            raise ValueError()
        if duracion:
            duracion = int(duracion)
            if duracion <= 0:
                raise ValueError()
        else:
            duracion = None
    except ValueError:
        return jsonify({
            "mensaje": "El número o la duración no son válidos."
        }), 400
    conexion = None
    cursor = None
    nueva_ruta = None
    ruta_anterior = None
    try:
        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT ruta_archivo
            FROM episodios
            WHERE id = %s
            """,
            (episodio_id,)
        )
        episodio = cursor.fetchone()
        if not episodio:
            return jsonify({
                "mensaje": "El episodio no existe."
            }), 404
        ruta_anterior = episodio["ruta_archivo"]
        if archivo and archivo.filename:
            nueva_ruta = guardar_video_episodio(archivo)
        cursor.execute(
            """
            UPDATE episodios
            SET numero = %s,
                titulo = %s,
                duracion = %s,
                ruta_archivo = %s
            WHERE id = %s
            """,
            (
                numero,
                titulo,
                duracion,
                nueva_ruta if nueva_ruta else ruta_anterior,
                episodio_id
            )
        )
        conexion.commit()
        if nueva_ruta and ruta_anterior:
            eliminar_video(ruta_anterior)
        return jsonify({
            "mensaje": "Episodio actualizado correctamente."
        }), 200
    except Exception as error:
        if conexion:
            conexion.rollback()
        if nueva_ruta:
            eliminar_video(nueva_ruta)
        if getattr(error, "errno", None) == 1062:
            return jsonify({
                "mensaje": "Ya existe un episodio con ese número."
            }), 409
        app.logger.exception("Error al editar el episodio.")
        return jsonify({
            "mensaje": "No se pudo actualizar el episodio."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

# ELIMINAR SOLO EL VIDEO DE UN EPISODIO
@app.route(
    "/api/admin/episodios/<int:episodio_id>/archivo",
    methods=["DELETE"]
)
def admin_eliminar_video_episodio(episodio_id):
    conexion = None
    cursor = None
    ruta_video = None
    try:
        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT ruta_archivo
            FROM episodios
            WHERE id = %s
            """,
            (episodio_id,)
        )
        episodio = cursor.fetchone()
        if not episodio:
            return jsonify({
                "mensaje": "El episodio no existe."
            }), 404
        ruta_video = episodio["ruta_archivo"]
        cursor.execute(
            """
            UPDATE episodios
            SET ruta_archivo = NULL
            WHERE id = %s
            """,
            (episodio_id,)
        )
        conexion.commit()
        eliminar_video(ruta_video)
        return jsonify({
            "mensaje": "Video eliminado correctamente."
        }), 200
    except Exception:
        if conexion:
            conexion.rollback()
        app.logger.exception("Error al eliminar el video del episodio.")
        return jsonify({
            "mensaje": "No se pudo eliminar el video."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

# ELIMINAR UN EPISODIO COMPLETO
@app.route(
    "/api/admin/episodios/<int:episodio_id>",
    methods=["DELETE"]
)
def admin_eliminar_episodio(episodio_id):
    conexion = None
    cursor = None
    ruta_video = None
    try:
        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT ruta_archivo
            FROM episodios
            WHERE id = %s
            """,
            (episodio_id,)
        )
        episodio = cursor.fetchone()
        if not episodio:
            return jsonify({
                "mensaje": "El episodio no existe."
            }), 404
        ruta_video = episodio["ruta_archivo"]
        cursor.execute(
            "DELETE FROM progreso WHERE episodio_id = %s",
            (episodio_id,)
        )
        cursor.execute(
            "DELETE FROM episodios WHERE id = %s",
            (episodio_id,)
        )
        conexion.commit()
        eliminar_video(ruta_video)
        return jsonify({
            "mensaje": "Episodio eliminado correctamente."
        }), 200
    except Exception:
        if conexion:
            conexion.rollback()
        app.logger.exception("Error al eliminar el episodio.")
        return jsonify({
            "mensaje": "No se pudo eliminar el episodio."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

# Obtiene el siguiente episodio pendiente de una serie.
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
#MAIN
if __name__ == "__main__":
    app.run(debug=True, port=5000)