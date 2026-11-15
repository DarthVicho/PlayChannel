
import { useState } from "react";

function AgregarSerie({ onAgregada, onCerrar }) {
  const [titulo, setTitulo] = useState("");
  const [anio, setAnio] = useState("");
  const [temporadas, setTemporadas] = useState([
    { numero: 1, episodios: [{ numero: 1, titulo: "", duracion: "", archivo: null }] }
  ]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");
  const [mensaje, setMensaje] = useState("");

  function agregarTemporada() {
    setTemporadas([...temporadas, {
      numero: temporadas.length + 1,
      episodios: [{ numero: 1, titulo: "", duracion: "", archivo: null }]
    }]);
  }

  function eliminarTemporada(indice) {
    setTemporadas(temporadas.filter((_, i) => i !== indice).map((t, i) => ({ ...t, numero: i + 1 })));
  }

  function agregarEpisodio(indiceTemporada) {
    setTemporadas(temporadas.map((temporada, i) => {
      if (i !== indiceTemporada) return temporada;
      return {
        ...temporada,
        episodios: [...temporada.episodios, {
          numero: temporada.episodios.length + 1,
          titulo: "",
          duracion: "",
          archivo: null
        }]
      };
    }));
  }

  function actualizarEpisodio(indiceTemporada, indiceEpisodio, campo, valor) {
    setTemporadas(temporadas.map((temporada, i) => {
      if (i !== indiceTemporada) return temporada;
      return {
        ...temporada,
        episodios: temporada.episodios.map((episodio, j) =>
          j === indiceEpisodio ? { ...episodio, [campo]: valor } : episodio
        )
      };
    }));
  }

  function eliminarEpisodio(indiceTemporada, indiceEpisodio) {
    setTemporadas(temporadas.map((temporada, i) => {
      if (i !== indiceTemporada) return temporada;
      return {
        ...temporada,
        episodios: temporada.episodios
          .filter((_, j) => j !== indiceEpisodio)
          .map((episodio, j) => ({ ...episodio, numero: j + 1 }))
      };
    }));
  }

  async function guardarSerie(event) {
    event.preventDefault();
    setError("");
    setMensaje("");

    for (const temporada of temporadas) {
      if (temporada.episodios.length === 0) {
        setError("Cada temporada debe tener al menos un episodio.");
        return;
      }
      for (const episodio of temporada.episodios) {
        if (!episodio.titulo.trim() || !episodio.duracion || !episodio.archivo) {
          setError("Completa el título, duración y video de todos los episodios.");
          return;
        }
      }
    }

    const formulario = new FormData();
    formulario.append("titulo", titulo);
    formulario.append("anio", anio);

    const datosTemporadas = temporadas.map((temporada, i) => ({
      numero: temporada.numero,
      episodios: temporada.episodios.map((episodio, j) => {
        formulario.append(`episodio_${i}_${j}`, episodio.archivo);
        return {
          numero: episodio.numero,
          titulo: episodio.titulo,
          duracion: episodio.duracion,
          archivo: `episodio_${i}_${j}`
        };
      })
    }));

    formulario.append("temporadas", JSON.stringify(datosTemporadas));

    try {
      setCargando(true);
      const respuesta = await fetch("http://127.0.0.1:5000/api/series", {
        method: "POST",
        body: formulario
      });

      const datos = await respuesta.json();

      if (!respuesta.ok) {
        throw new Error(datos.error || "No se pudo registrar la serie.");
      }

      setMensaje("¡Serie agregada correctamente!");
      setTitulo("");
      setAnio("");
      setTemporadas([
        { numero: 1, episodios: [{ numero: 1, titulo: "", duracion: "", archivo: null }] }
      ]);

      event.target.reset();

      if (onAgregada) await onAgregada();
    } catch (err) {
      setError(err.message || "No se pudo conectar con Flask.");
    } finally {
      setCargando(false);
    }
  }

  return (
    <form className="formulario-pelicula" onSubmit={guardarSerie}>
      <h2>Agregar serie</h2>
      <p>Completa los datos de la serie y agrega sus temporadas y episodios.</p>

      <label htmlFor="titulo-serie">Título de la serie</label>
      <input id="titulo-serie" type="text" value={titulo} onChange={(e) => setTitulo(e.target.value)} placeholder="Ej. Mi serie" required />

      <label htmlFor="anio-serie">Año</label>
      <input id="anio-serie" type="number" min="1888" max="2100" value={anio} onChange={(e) => setAnio(e.target.value)} placeholder="Ej. 2020" required />

      <h3>Temporadas</h3>

      {temporadas.map((temporada, i) => (
        <section className="temporada-serie" key={i}>
          <div className="formulario-acciones">
            <h3>Temporada {temporada.numero}</h3>
            {temporadas.length > 1 && (
              <button type="button" onClick={() => eliminarTemporada(i)} disabled={cargando}>
                Eliminar temporada
              </button>
            )}
          </div>

          {temporada.episodios.map((episodio, j) => (
            <div className="episodio-serie" key={j}>
              <h4>Episodio {episodio.numero}</h4>

              <label>Título del episodio</label>
              <input type="text" value={episodio.titulo} onChange={(e) => actualizarEpisodio(i, j, "titulo", e.target.value)} placeholder="Ej. El comienzo" required />

              <label>Duración en minutos</label>
              <input type="number" min="1" value={episodio.duracion} onChange={(e) => actualizarEpisodio(i, j, "duracion", e.target.value)} placeholder="Ej. 22" required />

              <label>Archivo de video</label>
              <input type="file" accept=".mp4,.mkv,.webm,.avi,.mov,video/*" onChange={(e) => actualizarEpisodio(i, j, "archivo", e.target.files?.[0] || null)} required />

              {episodio.archivo && (
                <p className="archivo-seleccionado">
                  Archivo seleccionado: {episodio.archivo.name}
                </p>
              )}

              {temporada.episodios.length > 1 && (
                <button type="button" onClick={() => eliminarEpisodio(i, j)} disabled={cargando}>
                  Eliminar episodio
                </button>
              )}
            </div>
          ))}

          <button type="button" onClick={() => agregarEpisodio(i)} disabled={cargando}>
            + Agregar episodio
          </button>
        </section>
      ))}

      <button type="button" onClick={agregarTemporada} disabled={cargando}>
        + Agregar temporada
      </button>

      {error && <p className="formulario-error">{error}</p>}
      {mensaje && <p className="formulario-exito">{mensaje}</p>}

      <div className="formulario-acciones">
        {onCerrar && (
          <button type="button" onClick={onCerrar} disabled={cargando}>
            Cancelar
          </button>
        )}
        <button type="submit" disabled={cargando}>
          {cargando ? "Guardando serie..." : "Guardar serie"}
        </button>
      </div>
    </form>
  );
}

export default AgregarSerie;
