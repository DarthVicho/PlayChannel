
import { useEffect, useRef, useState } from "react";
import "../css/Reproductor.css";

const API_URL = "http://127.0.0.1:5000";

function Reproductor({ pelicula, onTerminado }) {
  const videoRef = useRef(null);
  const [error, setError] = useState("");
  const [mensaje, setMensaje] = useState("");

  useEffect(() => {
    const video = videoRef.current;

    if (!video || !pelicula?.id) return;

    let ultimoGuardado = 0;
    let guardando = false;

    async function guardarProgreso(terminado = false) {
      if (guardando) {
        console.log("Esperando a que termine el guardado anterior...");

        while (guardando) {
          await new Promise((resolve) => setTimeout(resolve, 100));
        }
      }

      const posicion = terminado ? 0 : video.currentTime;
      guardando = true;

      try {
        const respuesta = await fetch(
          `${API_URL}/api/peliculas/${pelicula.id}/progreso`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ posicion, terminado }),
          }
        );

        if (!respuesta.ok) {
          throw new Error("No se pudo guardar el progreso.");
        }

        ultimoGuardado = Date.now();
        setMensaje("Progreso guardado");
        return true;
        } catch (error) {
          console.error("Error al guardar el progreso:", error);
          setMensaje("No se pudo guardar el progreso");
          return false;
        } finally {
        guardando = false;
      }
    }

    function alActualizarTiempo() {
      if (Date.now() - ultimoGuardado >= 10000) {
        guardarProgreso();
      }
    }

    function alPausar() {
      guardarProgreso();
    }

  async function alTerminar() {
    console.log("El video terminó.");

    const guardado = await guardarProgreso(true);

    console.log("¿Se guardó el progreso?", guardado);
    console.log("¿Existe onTerminado?", typeof onTerminado);

    if (guardado && typeof onTerminado === "function") {
      console.log("Solicitando el siguiente contenido...");
      await onTerminado();
    }
  }

    video.addEventListener("timeupdate", alActualizarTiempo);
    video.addEventListener("pause", alPausar);
    video.addEventListener("ended", alTerminar);

    return () => {
      video.removeEventListener("timeupdate", alActualizarTiempo);
      video.removeEventListener("pause", alPausar);
      video.removeEventListener("ended", alTerminar);
    };
  }, [pelicula?.id, onTerminado]);

  useEffect(() => {
    const video = videoRef.current;

    if (!video || !pelicula?.id) return;

    let cancelado = false;
    let restaurarPendiente = null;

    async function cargarProgreso() {
      try {
        const respuesta = await fetch(
          `${API_URL}/api/peliculas/${pelicula.id}/progreso`
        );

        if (!respuesta.ok) return;

        const progreso = await respuesta.json();

        if (
          cancelado ||
          progreso.terminado ||
          !Number.isFinite(Number(progreso.posicion)) ||
          Number(progreso.posicion) <= 0
        ) {
          return;
        }

        const restaurarPosicion = () => {
          if (cancelado || !Number.isFinite(video.duration)) return;

          video.currentTime = Math.min(
            Number(progreso.posicion),
            Math.max(0, video.duration - 1)
          );
        };

        if (video.readyState >= 1) {
          restaurarPosicion();
        } else {
          restaurarPendiente = restaurarPosicion;
          video.addEventListener("loadedmetadata", restaurarPosicion, {
            once: true,
          });
        }
      } catch {
        // El video puede reproducirse aunque no se recupere el progreso.
      }
    }

    cargarProgreso();

    return () => {
      cancelado = true;

      if (restaurarPendiente) {
        video.removeEventListener("loadedmetadata", restaurarPendiente);
      }
    };
  }, [pelicula?.id]);

  if (!pelicula) {
    return (
      <div className="reproductor-vacio">
        <h2>Tu canal está listo</h2>
        <p>Esperando contenido.</p>
      </div>
    );
  }

  return (
    <div className="reproductor">
      {pelicula.ruta_archivo ? (
        <video
          ref={videoRef}
          key={pelicula.id}
          className="video-player"
          controls
          autoPlay
          preload="auto"
          src={`${API_URL}/api/peliculas/${pelicula.id}/video`}
          onError={() => setError("No se pudo reproducir este video.")}
          onCanPlay={(evento) => {
            evento.currentTarget.play().catch((error) => {
              console.log(
                "El navegador bloqueó la reproducción automática:",
                error
              );
            });
          }}
        />
      ) : (
        <div className="reproductor-vacio">
          <h2>{pelicula.titulo}</h2>
          <p>Esta película no tiene un archivo de video asociado.</p>
        </div>
      )}

      {error && <p className="reproductor-error">{error}</p>}
      {mensaje && <p className="progreso-mensaje">{mensaje}</p>}

      <div className="reproductor-detalles">
        <span className="section-label">REPRODUCIENDO</span>
        <h2>{pelicula.titulo}</h2>
        <p>
          {pelicula.anio || "Año desconocido"} ·{" "}
          {pelicula.duracion
            ? `${pelicula.duracion} minutos`
            : "Duración desconocida"}
        </p>
      </div>
    </div>
  );
}

export default Reproductor;
