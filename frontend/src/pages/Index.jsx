import { useCallback, useEffect, useState } from "react";
import Reproductor from "../components/Reproductor";
import AdvertenciaDerechos from "../components/AdvertenciaDerechos";
import "../css/Index.css";

const API_URL = "http://127.0.0.1:5000";

function Inicio() {
  const [contenido, setContenido] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");

  //Solicita el siguiente contenido al canal.
  const cargarSiguienteContenido = useCallback(async () => {
    try {
      setCargando(true);
      setError("");
      const respuesta = await fetch(
        `${API_URL}/api/canal/siguiente`
      );
      const resultado = await respuesta.json();
      if (!respuesta.ok) {
        throw new Error(
          resultado.mensaje || "No se pudo obtener el siguiente contenido."
        );
      }
      setContenido(resultado);
    } catch (err) {
      console.error("Error al cargar contenido:", err);
      setContenido(null);
      setError(err.message || "Error de conexión con el servidor.");
    } finally {
      setCargando(false);
    }
  }, []);

  //Carga el primer contenido al entrar en Inicio.
  useEffect(() => {
    cargarSiguienteContenido();
  }, [cargarSiguienteContenido]);

  const esPelicula = contenido?.tipo === "pelicula";
  const esEpisodio = contenido?.tipo === "episodio";

  return (
    <main>
      <AdvertenciaDerechos/>
      <section className="inicio-page">
        <header className="page-header">
          <div>
            <span className="section-label">
              TU EXPERIENCIA MULTIMEDIA
            </span>
            {/*<h1>Inicio</h1>*/}
            <p>Tu canal personal, listo para reproducir.</p>
          </div>

          <div className="channel-status">
            <span className="status-dot"></span>
            Canal automático
          </div>
        </header>

        <section className="welcome-section">
          <span className="section-label">TU CANAL, A TU MANERA</span>
          <p>
            Play Channel organiza tu biblioteca multimedia y selecciona automáticamente el contenido que se transmitirá.
          </p>
        </section>

        <section className="player-container">
          {cargando ? (
            <div className="player-placeholder">
              <h2>Preparando tu canal...</h2>
              <p>Buscando el próximo contenido.</p>
            </div>
          ) : error ? (
            <div className="player-placeholder">
              <h2>No se pudo cargar el canal</h2>
              <p>{error}</p>
              <button onClick={cargarSiguienteContenido}>
                Intentar nuevamente
              </button>
            </div>
          ) : (esPelicula || esEpisodio) && contenido.ruta_archivo ? (
            <Reproductor
              key={`${contenido.tipo}-${contenido.id}`}
              pelicula={{
                ...contenido,
                tipo: contenido.tipo
              }}
              onTerminado={cargarSiguienteContenido}
            />
          ) : (
            <div className="player-placeholder">
              <div className="play-icon">▶</div>
              <h2>{contenido?.titulo || "Tu canal está listo"}</h2>
              <p>
                {contenido?.tipo === "serie"
                  ? "La selección corresponde a una serie. La reproducción de episodios se integrará después."
                  : "Este contenido todavía no tiene un archivo de video disponible."}
              </p>
            </div>
          )}
          {/*
          <div className="player-info">
            <div>
              <span className="section-label">SELECCIÓN ACTUAL</span>
              <h3>{contenido?.titulo || "Esperando contenido"}</h3>
              <p>
                {contenido?.tipo === "pelicula"
                  ? "Película seleccionada por el canal"
                  : contenido?.tipo === "serie"
                    ? "Serie seleccionada por el canal"
                    : "Las películas y series aparecerán en este espacio."}
              </p>
            </div>

            <button
              className="boton-siguiente"
              onClick={cargarSiguienteContenido}
              disabled={cargando}
            >
              {cargando ? "Buscando..." : "Siguiente selección"}
            </button>
          </div>
          */}
        </section>
      </section>
    </main>
  );
}

export default Inicio;