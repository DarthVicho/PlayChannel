
import { useCallback, useEffect, useState } from "react";
import AgregarPelicula from "../components/AgregarPelicula";
import "../css/Contenido.css";

const API_URL = "http://127.0.0.1:5000";

// Muestra y administra el contenido que el usuario tiene en su biblioteca.
function Contenido() {
  const [peliculas, setPeliculas] = useState([]);
  const [series, setSeries] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [mostrarBorrar, setMostrarBorrar] = useState(false);
  const [peliculaSeleccionada, setPeliculaSeleccionada] = useState("");
  const [eliminando, setEliminando] = useState(false);

  // Obtiene únicamente los registros que pertenecen a Mi contenido.
  const cargarContenido = useCallback(async () => {
    try {
      setCargando(true);
      setError("");

      const respuesta = await fetch(`${API_URL}/api/mi-contenido`);

      if (!respuesta.ok) {
        throw new Error("No se pudo cargar Mi contenido.");
      }

      const datos = await respuesta.json();

      setPeliculas(
        datos.filter((item) => item.tipo_contenido === "pelicula")
      );

      setSeries(
        datos.filter((item) => item.tipo_contenido === "serie")
      );
    } catch (err) {
      setError(err.message || "No se pudo conectar con Flask.");
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    cargarContenido();
  }, [cargarContenido]);

  // Quita una película de Mi contenido sin eliminar su registro original.
  async function borrarPelicula() {
    if (!peliculaSeleccionada) {
      setError("Selecciona una película para eliminar.");
      return;
    }

    const pelicula = peliculas.find(
      (item) => String(item.contenido_id) === String(peliculaSeleccionada)
    );

    if (!pelicula) {
      setError("No se encontró la película seleccionada.");
      return;
    }

    const confirmar = window.confirm(
      `¿Quieres quitar "${pelicula.titulo}" de Mi contenido? El archivo original se conservará.`
    );

    if (!confirmar) return;

    try {
      setEliminando(true);
      setError("");
      setMensaje("");

      const respuesta = await fetch(
        `${API_URL}/api/mi-contenido/pelicula/${pelicula.contenido_id}`,
        { method: "DELETE" }
      );

      const datos = await respuesta.json();

      if (!respuesta.ok) {
        throw new Error(
          datos.mensaje || "No se pudo quitar la película de Mi contenido."
        );
      }

      setMensaje(datos.mensaje || "Película quitada de Mi contenido.");
      setPeliculaSeleccionada("");
      setMostrarBorrar(false);

      await cargarContenido();
    } catch (err) {
      setError(err.message || "No se pudo conectar con Flask.");
    } finally {
      setEliminando(false);
    }
  }

  return (
    <section className="contenido-page">
      <header className="page-header">
        <div>
          <span className="section-label">TU BIBLIOTECA MULTIMEDIA</span>
          <h1>Contenido</h1>
          <p>Administra las películas y series de tu canal.</p>
        </div>

        <div className="contenido-acciones">
          <button
            className="boton-agregar"
            onClick={() => {
              setMostrarFormulario(!mostrarFormulario);
              setMostrarBorrar(false);
              setError("");
              setMensaje("");
            }}
          >
            {mostrarFormulario ? "Cerrar formulario" : "+ Agregar película"}
          </button>

          <button
            type="button"
            className="boton-borrar"
            onClick={() => {
              setMostrarBorrar(!mostrarBorrar);
              setMostrarFormulario(false);
              setError("");
              setMensaje("");
              setPeliculaSeleccionada("");
            }}
          >
            {mostrarBorrar ? "Cancelar" : "− Quitar contenido"}
          </button>
        </div>
      </header>

      {mostrarFormulario && (
        <section className="formulario-contenedor">
          <AgregarPelicula
            onAgregada={async () => {
              await cargarContenido();
              setMostrarFormulario(false);
            }}
            onCerrar={() => setMostrarFormulario(false)}
          />
        </section>
      )}

      {mostrarBorrar && (
        <section className="formulario-contenedor">
          <h2>Quitar contenido</h2>
          <p>
            Selecciona la película que deseas quitar de tu biblioteca.
            El registro original y su video se conservarán.
          </p>

          {peliculas.length === 0 ? (
            <p className="mensaje-contenido">
              No hay películas disponibles para quitar.
            </p>
          ) : (
            <>
              <label htmlFor="pelicula-eliminar">Película</label>
              <select
                id="pelicula-eliminar"
                value={peliculaSeleccionada}
                onChange={(e) => setPeliculaSeleccionada(e.target.value)}
                disabled={eliminando}
              >
                <option value="">Selecciona una película</option>
                {peliculas.map((pelicula) => (
                  <option
                    key={pelicula.contenido_id}
                    value={pelicula.contenido_id}
                  >
                    {pelicula.titulo} ({pelicula.anio || "Año desconocido"})
                  </option>
                ))}
              </select>

              <div className="formulario-acciones">
                <button
                  type="button"
                  onClick={() => setMostrarBorrar(false)}
                  disabled={eliminando}
                >
                  Cancelar
                </button>

                <button
                  type="button"
                  className="boton-borrar"
                  onClick={borrarPelicula}
                  disabled={eliminando || !peliculaSeleccionada}
                >
                  {eliminando ? "Quitando..." : "Quitar de Mi contenido"}
                </button>
              </div>
            </>
          )}
        </section>
      )}

      {error && <p className="error-contenido">{error}</p>}
      {mensaje && <p className="formulario-exito">{mensaje}</p>}

      <section className="biblioteca-resumen">
        <article className="resumen-card">
          <span>Películas</span>
          <strong>{peliculas.length}</strong>
        </article>

        <article className="resumen-card">
          <span>Series</span>
          <strong>{series.length}</strong>
        </article>
      </section>

      {cargando ? (
        <p className="mensaje-contenido">Cargando Mi contenido...</p>
      ) : (
        <>
          <section className="biblioteca-seccion">
            <h2>Películas</h2>

            {peliculas.length === 0 ? (
              <p className="mensaje-contenido">
                Todavía no tienes películas en Mi contenido.
              </p>
            ) : (
              <div className="biblioteca-grid">
                {peliculas.map((pelicula) => (
                  <article
                    className="biblioteca-card"
                    key={pelicula.contenido_id}
                  >
                    <div className="biblioteca-card-icon">▶</div>
                    <div className="biblioteca-card-info">
                      <h3>{pelicula.titulo}</h3>
                      <p>{pelicula.anio || "Año desconocido"}</p>
                      <span>Película</span>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>

          <section className="biblioteca-seccion">
            <h2>Series</h2>

            {series.length === 0 ? (
              <p className="mensaje-contenido">
                Todavía no tienes series en Mi contenido.
              </p>
            ) : (
              <div className="biblioteca-grid">
                {series.map((serie) => (
                  <article
                    className="biblioteca-card"
                    key={serie.contenido_id}
                  >
                    <div className="biblioteca-card-icon serie-icon">▤</div>
                    <div className="biblioteca-card-info">
                      <h3>{serie.titulo}</h3>
                      <p>{serie.anio || "Año desconocido"}</p>
                      <span>Serie</span>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </section>
  );
}

export default Contenido;
