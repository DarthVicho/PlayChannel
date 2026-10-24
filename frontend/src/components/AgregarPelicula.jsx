import { useState } from "react";

function AgregarPelicula({ onAgregada, onCerrar }) {
  const [titulo, setTitulo] = useState("");
  const [anio, setAnio] = useState("");
  const [duracion, setDuracion] = useState("");
  const [archivo, setArchivo] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");
  const [mensaje, setMensaje] = useState("");

  async function guardarPelicula(event) {
    event.preventDefault();
    setError("");
    setMensaje("");

    if (!archivo) {
      setError("Selecciona un archivo de video.");
      return;
    }

    const formulario = new FormData();
    formulario.append("titulo", titulo);
    formulario.append("anio", anio);
    formulario.append("duracion", duracion);
    formulario.append("archivo", archivo);

    try {
      setCargando(true);

      const respuesta = await fetch(
        "http://127.0.0.1:5000/api/peliculas",
        {
          method: "POST",
          body: formulario,
        }
      );

      const datos = await respuesta.json();

      if (!respuesta.ok) {
        throw new Error(datos.error || "No se pudo registrar la película.");
      }

      setMensaje("¡Película agregada correctamente!");
      setTitulo("");
      setAnio("");
      setDuracion("");
      setArchivo(null);

      event.target.reset();

      if (onAgregada) {
        await onAgregada();
      }
    } catch (err) {
      setError(err.message || "No se pudo conectar con Flask.");
    } finally {
      setCargando(false);
    }
  }

  return (
    <form className="formulario-pelicula" onSubmit={guardarPelicula}>
      <h2>Agregar película</h2>
      <p>Selecciona un video y completa sus datos.</p>

      <label htmlFor="titulo-pelicula">Título</label>
      <input
        id="titulo-pelicula"
        type="text"
        value={titulo}
        onChange={(e) => setTitulo(e.target.value)}
        placeholder="Ej. Big Buck Bunny"
        required
      />

      <label htmlFor="anio-pelicula">Año</label>
      <input
        id="anio-pelicula"
        type="number"
        min="1888"
        max="2100"
        value={anio}
        onChange={(e) => setAnio(e.target.value)}
        placeholder="Ej. 2008"
        required
      />

      <label htmlFor="duracion-pelicula">Duración en minutos</label>
      <input
        id="duracion-pelicula"
        type="number"
        min="1"
        value={duracion}
        onChange={(e) => setDuracion(e.target.value)}
        placeholder="Ej. 10"
        required
      />

      <label htmlFor="archivo-pelicula">Archivo de video</label>
      <input
        id="archivo-pelicula"
        type="file"
        accept=".mp4,.mkv,.webm,.avi,.mov,video/*"
        onChange={(e) => setArchivo(e.target.files?.[0] || null)}
        required
      />

      {archivo && (
        <p className="archivo-seleccionado">
          Archivo seleccionado: {archivo.name}
        </p>
      )}

      {error && <p className="formulario-error">{error}</p>}
      {mensaje && <p className="formulario-exito">{mensaje}</p>}

      <div className="formulario-acciones">
        {onCerrar && (
          <button type="button" onClick={onCerrar} disabled={cargando}>
            Cancelar
          </button>
        )}

        <button type="submit" disabled={cargando}>
          {cargando ? "Guardando video..." : "Guardar película"}
        </button>
      </div>
    </form>
  );
}

export default AgregarPelicula;