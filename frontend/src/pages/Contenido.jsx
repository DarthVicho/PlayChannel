
import { useCallback, useEffect, useState } from "react";
import AgregarPelicula from "../components/AgregarPelicula";
import "../css/Contenido.css";

const API_URL = "http://127.0.0.1:5000";

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

  const cargarContenido = useCallback(async () => {
    try {
      setCargando(true);
      setError("");

      const [respuestaPeliculas, respuestaSeries] = await Promise.all([
        fetch(`${API_URL}/api/peliculas`),
        fetch(`${API_URL}/api/series`),
      ]);

      if (!respuestaPeliculas.ok || !respuestaSeries.ok) {
        throw new Error("No se pudo cargar la biblioteca.");
      }

      const datosPeliculas = await respuestaPeliculas.json();
      const datosSeries = await respuestaSeries.json();

      setPeliculas(datosPeliculas);
      setSeries(datosSeries);
    } catch (err) {
      setError(err.message || "No se pudo conectar con Flask.");
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    cargarContenido();
  }, [cargarContenido]);

  async function borrarPelicula() {
    if (!peliculaSeleccionada) {
      setError("Selecciona una película para eliminar.");
      return;
    }

    const pelicula = peliculas.find(
      (item) => String(item.id) === String(peliculaSeleccionada)
    );

    if (!pelicula) {
      setError("No se encontró la película seleccionada.");
      return;
    }

    const confirmar = window.confirm(
      `¿Seguro que quieres eliminar "${pelicula.titulo}"? Esta acción no se puede deshacer.`
    );

    if (!confirmar) return;

    try {
      setEliminando(true);
      setError("");
      setMensaje("");

      const respuesta = await fetch(
        `${API_URL}/api/peliculas/${pelicula.id}`,
        { method: "DELETE" }
      );

      const datos = await respuesta.json();

      if (!respuesta.ok) {
        throw new Error(datos.error || "No se pudo eliminar la película.");
      }

      setMensaje(datos.mensaje || "Película eliminada correctamente.");
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
            {mostrarBorrar ? "Cancelar" : "− Borrar contenido"}
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
          <h2>Borrar contenido</h2>
          <p>Selecciona la película que deseas eliminar de tu biblioteca.</p>

          {peliculas.length === 0 ? (
            <p className="mensaje-contenido">
              No hay películas disponibles para eliminar.
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
                  <option key={pelicula.id} value={pelicula.id}>
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
                  {eliminando ? "Eliminando..." : "Eliminar película"}
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
        <p className="mensaje-contenido">Cargando biblioteca...</p>
      ) : (
        <>
          <section className="biblioteca-seccion">
            <h2>Películas</h2>

            {peliculas.length === 0 ? (
              <p className="mensaje-contenido">
                Todavía no hay películas registradas.
              </p>
            ) : (
              <div className="biblioteca-grid">
                {peliculas.map((pelicula) => (
                  <article className="biblioteca-card" key={pelicula.id}>
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
                Todavía no hay series registradas.
              </p>
            ) : (
              <div className="biblioteca-grid">
                {series.map((serie) => (
                  <article className="biblioteca-card" key={serie.id}>
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
