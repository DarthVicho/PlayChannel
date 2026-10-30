import os
import math
from pathlib import Path

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

from database import (
    obtener_peliculas,
    obtener_series,
    obtener_contenido,
    obtener_siguiente_episodio,
    conectar,
    obtener_peliculas_ciclo,
    marcar_pelicula_emitida
)

from random_engine import seleccionar_contenido
from state_manager import obtener_progreso, guardar_progreso

app = Flask(__name__)

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",
                "http://127.0.0.1:5173"
            ],
            "methods": ["GET", "POST", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    }
)

# Carpeta donde se almacenarán los videos importados.
CARPETA_MEDIA = Path(__file__).resolve().parent / "media"
CARPETA_MEDIA.mkdir(parents=True, exist_ok=True)

# Tamaño máximo permitido: 2 GB por archivo.
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024 * 1024

EXTENSIONES_PERMITIDAS = {".mp4", ".mkv", ".webm", ".avi", ".mov"}

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


if __name__ == "__main__":
    app.run(debug=True, port=5000)