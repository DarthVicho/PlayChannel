import { useEffect, useRef, useState, useCallback } from "react";
import "../css/Reproductor.css";

const API_URL = "http://127.0.0.1:5000";

function Reproductor({ pelicula, onTerminado }) {
  const tipoContenido = pelicula?.tipo === "episodio" ? "episodios" : "peliculas";
  const urlVideo = pelicula?.tipo === "episodio"
    ? `${API_URL}/api/episodios/${pelicula.id}/video`
    : `${API_URL}/api/peliculas/${pelicula.id}/video`;
  const urlProgreso = pelicula?.tipo === "episodio"
    ? `${API_URL}/api/episodios/${pelicula.id}/progreso`
    : `${API_URL}/api/peliculas/${pelicula.id}/progreso`;
  const videoRef = useRef(null);
  const contenedorRef = useRef(null);
  const guardandoRef = useRef(false);
  const ultimoGuardadoRef = useRef(0);
  const cambioEnCursoRef = useRef(false);
  const [error, setError] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [reproduciendo, setReproduciendo] = useState(false);
  const [tiempo, setTiempo] = useState(0);
  const [duracion, setDuracion] = useState(0);
  const [volumen, setVolumen] = useState(1);
  const [silenciado, setSilenciado] = useState(false);
  const [pantallaCompleta, setPantallaCompleta] = useState(false);

  //Convierte los segundos en un formato de tiempo legible para los controles.
  const formatearTiempo = (segundos) => {
    if (!Number.isFinite(segundos) || segundos < 0) return "00:00";
    const horas = Math.floor(segundos / 3600);
    const minutos = Math.floor((segundos % 3600) / 60);
    const segundosRestantes = Math.floor(segundos % 60);
    const formato = (numero) => String(numero).padStart(2, "0");
    return horas > 0
      ? `${horas}:${formato(minutos)}:${formato(segundosRestantes)}`
      : `${formato(minutos)}:${formato(segundosRestantes)}`;
  };

  //Guarda el progreso de películas o episodios.
  const guardarProgreso = useCallback(async (terminado = false) => {
    const video = videoRef.current;
    if (!video || !pelicula?.id || guardandoRef.current) return false;
    guardandoRef.current = true;
    try {
      const respuesta = await fetch(urlProgreso, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          posicion: terminado ? 0 : video.currentTime,
          terminado
        })
      });
      if (!respuesta.ok) {
        throw new Error("No se pudo guardar el progreso.");
      }
      ultimoGuardadoRef.current = Date.now();
      setMensaje("Progreso guardado");
      return true;
    } catch (err) {
      console.error("Error al guardar el progreso:", err);
      setMensaje("No se pudo guardar el progreso");
      return false;
    } finally {
      guardandoRef.current = false;
    }
  }, [pelicula?.id, urlProgreso]);

  //Guarda el contenido y solicita el siguiente elemento del canal.
  const avanzarContenido = useCallback(async () => {
    if (cambioEnCursoRef.current || typeof onTerminado !== "function") return;
    cambioEnCursoRef.current = true;
    const guardado = await guardarProgreso(true);
    if (!guardado) {
      cambioEnCursoRef.current = false;
      return;
    }
    try {
      await onTerminado();
    } catch (err) {
      console.error("No se pudo cargar el siguiente contenido:", err);
      setMensaje("No se pudo cargar el siguiente contenido");
      cambioEnCursoRef.current = false;
    }
  }, [guardarProgreso, onTerminado]);

  //Registra los eventos del video, recupera el progreso y gestiona el cambio automático.
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !pelicula?.id) return;
    let cancelado = false;
    let restaurarPendiente = null;
    cambioEnCursoRef.current = false;
    setError("");
    setMensaje("");
    setTiempo(0);
    setDuracion(0);
    setReproduciendo(false);
    ultimoGuardadoRef.current = 0;

    //Actualiza el tiempo transcurrido.
    const actualizarTiempo = () => {
      setTiempo(video.currentTime || 0);
    };

    //Actualiza la duración del video.
    const actualizarDuracion = () => {
      if (Number.isFinite(video.duration) && video.duration > 0) {
        setDuracion(video.duration);
      }
    };

    //Actualiza el estado de reproducción.
    const alReproducir = () => setReproduciendo(true);
    const alPausar = () => setReproduciendo(false);

    //Guarda el progreso cada diez segundos.
    const guardarAlActualizar = () => {
      if (Date.now() - ultimoGuardadoRef.current >= 10000) {
        guardarProgreso();
      }
    };

    //Guarda el progreso cuando se pausa manualmente.
    const guardarAlPausar = () => {
      if (!video.ended && !cambioEnCursoRef.current) {
        guardarProgreso();
      }
    };

    //Solicita el siguiente contenido cuando termina el video.
    const alTerminar = () => {
      if (!cancelado) {
        avanzarContenido();
      }
    };

    //Recupera la posición guardada anteriormente.
    const recuperarProgreso = async () => {
      try {
        const respuesta = await fetch(urlProgreso);
        if (!respuesta.ok || cancelado) return;
        const progreso = await respuesta.json();
        const posicion = Number(progreso.posicion);
        if (
          progreso.terminado ||
          !Number.isFinite(posicion) ||
          posicion <= 0
        ) {
          return;
        }
        const restaurar = () => {
          if (cancelado || !Number.isFinite(video.duration)) return;
          video.currentTime = Math.min(
            posicion,
            Math.max(0, video.duration - 1)
          );
        };
        if (video.readyState >= 1) {
          restaurar();
        } else {
          restaurarPendiente = restaurar;
          video.addEventListener("loadedmetadata", restaurar, { once: true });
        }
      } catch (err) {
        console.error("No se pudo recuperar el progreso:", err);
      }
    };

    video.addEventListener("timeupdate", actualizarTiempo);
    video.addEventListener("loadedmetadata", actualizarDuracion);
    video.addEventListener("durationchange", actualizarDuracion);
    video.addEventListener("play", alReproducir);
    video.addEventListener("pause", alPausar);
    video.addEventListener("timeupdate", guardarAlActualizar);
    video.addEventListener("pause", guardarAlPausar);
    video.addEventListener("ended", alTerminar);

    recuperarProgreso();

    return () => {
      cancelado = true;
      video.removeEventListener("timeupdate", actualizarTiempo);
      video.removeEventListener("loadedmetadata", actualizarDuracion);
      video.removeEventListener("durationchange", actualizarDuracion);
      video.removeEventListener("play", alReproducir);
      video.removeEventListener("pause", alPausar);
      video.removeEventListener("timeupdate", guardarAlActualizar);
      video.removeEventListener("pause", guardarAlPausar);
      video.removeEventListener("ended", alTerminar);
      if (restaurarPendiente) {
        video.removeEventListener("loadedmetadata", restaurarPendiente);
      }
    };
  }, [pelicula?.id, guardarProgreso, avanzarContenido, urlProgreso]);

  //Detecta cuándo el reproductor entra o sale de pantalla completa.
  useEffect(() => {
    const actualizarPantalla = () => {
      setPantallaCompleta(Boolean(document.fullscreenElement));
    };
    document.addEventListener("fullscreenchange", actualizarPantalla);
    return () => {
      document.removeEventListener("fullscreenchange", actualizarPantalla);
    };
  }, []);

  //Inicia o pausa el video.
  const alternarReproduccion = () => {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused) {
      video.play().catch((err) => {
        console.error("No se pudo iniciar el video:", err);
        setMensaje("Pulsa reproducir para iniciar el video");
      });
    } else {
      video.pause();
    }
  };

  //Cambia la posición del video.
  const cambiarTiempo = (evento) => {
    const video = videoRef.current;
    if (!video || !Number.isFinite(video.duration)) return;
    const nuevoTiempo = Number(evento.target.value);
    video.currentTime = nuevoTiempo;
    setTiempo(nuevoTiempo);
  };

  //Cambia el volumen.
  const cambiarVolumen = (evento) => {
    const nuevoVolumen = Number(evento.target.value);
    setVolumen(nuevoVolumen);
    setSilenciado(nuevoVolumen === 0);
    if (videoRef.current) {
      videoRef.current.volume = nuevoVolumen;
      videoRef.current.muted = nuevoVolumen === 0;
    }
  };

  //Activa o desactiva el sonido.
  const alternarSilencio = () => {
    const video = videoRef.current;
    if (!video) return;
    video.muted = !video.muted;
    setSilenciado(video.muted);
  };

  //Activa o desactiva la pantalla completa.
  const alternarPantallaCompleta = async () => {
    const contenedor = contenedorRef.current;
    if (!contenedor) return;
    try {
      if (!document.fullscreenElement) {
        await contenedor.requestFullscreen();
      } else {
        await document.exitFullscreen();
      }
    } catch (err) {
      console.error("No se pudo cambiar a pantalla completa:", err);
    }
  };

  //Guarda el contenido actual como terminado y avanza.
  const cambiarContenido = async () => {
    await avanzarContenido();
  };

  //Muestra un mensaje cuando todavía no hay contenido seleccionado.
  if (!pelicula) {
    return (
      <div className="reproductor-vacio">
        <div className="reproductor-icono">▶</div>
        <h2>Tu canal está listo</h2>
        <p>Esperando contenido para comenzar la transmisión.</p>
      </div>
    );
  }

  return (
    <section className="reproductor" ref={contenedorRef}>
      {pelicula.ruta_archivo ? (
        <div className="reproductor-pantalla">
          <video ref={videoRef} key={`${tipoContenido}-${pelicula.id}`} className="video-player" autoPlay preload="auto"
            playsInline src={urlVideo} onError={() => setError("No se pudo reproducir este video.")} onClick={alternarReproduccion}
            onCanPlay={(evento) => {
              evento.currentTarget.play().catch(() => {
                setMensaje("Pulsa reproducir para iniciar el video");
              });
            }}
          />

          <div className="marca-transmision">
            <span className="marca-punto" />
            PLAYCHANNEL <span>·</span> CANAL PERSONAL
          </div>

          {!reproduciendo && (
            <button type="button" className="boton-central" onClick={alternarReproduccion} aria-label="Reproducir video">
              ▶
            </button>
          )}

          <div className="controles-video">
            <div className="barra-tiempo">
              <input type="range" min="0" max={duracion || 0} step="0.1" value={Math.min(tiempo, duracion || 0)}
                onChange={cambiarTiempo} aria-label="Posición del video" style={{ "--progreso": `${duracion > 0 ? (tiempo / duracion) * 100 : 0}%`
                }}
              />
            </div>

            <div className="controles-fila">
              <button type="button" className="control-boton control-play" onClick={alternarReproduccion} aria-label={reproduciendo ? "Pausar" : "Reproducir"}>
                {reproduciendo ? "Ⅱ" : "▶"}
              </button>

              <span className="tiempo-video">
                {formatearTiempo(tiempo)} / {formatearTiempo(duracion)}
              </span>

              <div className="controles-derecha">
                <button type="button" className="control-boton boton-siguiente" onClick={cambiarContenido} aria-label="Cambiar al siguiente contenido" title="Siguiente contenido">
                  »|
                </button>

                <button type="button" className="control-boton" onClick={alternarSilencio} aria-label={silenciado ? "Activar sonido" : "Silenciar"}>
                  {silenciado || volumen === 0 ? "×" : "◖"}
                </button>

                <input className="control-volumen" type="range" min="0" max="1"
                  step="0.05" value={silenciado ? 0 : volumen} onChange={cambiarVolumen} aria-label="Volumen"/>

                <button type="button" className="control-boton" onClick={alternarPantallaCompleta}
                  aria-label={pantallaCompleta ? "Salir de pantalla completa" : "Pantalla completa"}>
                  {pantallaCompleta ? "⤢" : "⛶"}
                </button>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="reproductor-vacio">
          <div className="reproductor-icono">▶</div>
          <h2>{pelicula.titulo}</h2>
          <p>Este contenido no tiene un archivo de video asociado.</p>
        </div>
      )}

      {error && <p className="reproductor-error">{error}</p>}
      {mensaje && <p className="progreso-mensaje">{mensaje}</p>}

      <div className="reproductor-detalles">
        <span className="section-label">EN EMISIÓN</span>
        {pelicula.tipo === "episodio" ? (
          <h2>
            {pelicula.titulo.split(" - ")[0]} -  T{pelicula.temporada}:E{pelicula.numero_episodio}  {pelicula.titulo.split(" - ").slice(1).join(" - ")}
          </h2>
        ) : (
          <h2>{pelicula.titulo}</h2>
        )}
        <p>
          {pelicula.anio || "Año desconocido"} ·{" "}
          {pelicula.duracion ? `${pelicula.duracion} minutos` : "Duración desconocida"}
        </p>
      </div>
    </section>
  );
}

export default Reproductor;