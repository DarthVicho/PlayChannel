import { useEffect, useState } from "react";
const API_URL = "http://127.0.0.1:5000";
function AdminSeries() {
    const [series, setSeries] = useState([]);
    const [serieSeleccionada, setSerieSeleccionada] = useState(null);
    const [titulo, setTitulo] = useState("");
    const [anio, setAnio] = useState("");
    const [descripcion, setDescripcion] = useState("");
    const [portada, setPortada] = useState(null);
    const [portadaActual, setPortadaActual] = useState(null);
    const [editandoId, setEditandoId] = useState(null);
    const [numeroTemporada, setNumeroTemporada] = useState("");
    const [numeroEpisodio, setNumeroEpisodio] = useState("");
    const [tituloEpisodio, setTituloEpisodio] = useState("");
    const [duracionEpisodio, setDuracionEpisodio] = useState("");
    const [videoEpisodio, setVideoEpisodio] = useState(null);
    const [episodioEditandoId, setEpisodioEditandoId] = useState(null);
    const [temporadaSeleccionada, setTemporadaSeleccionada] = useState(null);
    const [mensaje, setMensaje] = useState("");
    const [error, setError] = useState("");
    const [cargando, setCargando] = useState(false);
    const [guardando, setGuardando] = useState(false);
    // Realizar solicitudes y manejar respuestas del backend.
    async function solicitar(url, opciones = {}) {
        const respuesta = await fetch(`${API_URL}${url}`, opciones);
        let resultado = {};
        try {
            resultado = await respuesta.json();
        } catch {
            resultado = {};
        }
        if (!respuesta.ok) {
            throw new Error(
                resultado.mensaje || "No se pudo completar la operación."
            );
        }
        return resultado;
    }
    // Cargar series registradas en el catálogo preestablecido.
    async function cargarSeries() {
        try {
            setCargando(true);
            setError("");
            const resultado = await solicitar("/api/admin/series");
            setSeries(Array.isArray(resultado) ? resultado : []);
            // Actualizar la serie seleccionada después de una modificación.
            if (serieSeleccionada) {
                const actualizada = resultado.find(
                    (serie) => serie.id === serieSeleccionada.id
                );
                setSerieSeleccionada(actualizada || null);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setCargando(false);
        }
    }
    useEffect(() => {
        cargarSeries();
    }, []);
    // Limpiar formulario de serie.
    function limpiarFormularioSerie() {
        setTitulo("");
        setAnio("");
        setDescripcion("");
        setPortada(null);
        setPortadaActual(null);
        const selectorPortada = document.getElementById("portada-serie");
        if (selectorPortada) selectorPortada.value = "";
        setEditandoId(null);
    }
    // Registrar o actualizar una serie.
    async function guardarSerie(e) {
    e.preventDefault();
    setMensaje("");
    setError("");
        try {
            setGuardando(true);
            const datos = new FormData();
            datos.append("titulo", titulo.trim());
            datos.append("anio", anio);
            datos.append("descripcion", descripcion.trim());
            if (portada) datos.append("portada", portada);
            const editando = editandoId !== null;
            const resultado = await solicitar(
                editando
                    ? `/api/admin/series/${editandoId}`
                    : "/api/admin/series",
                {
                    method: editando ? "PUT" : "POST",
                    body: datos
                }
            );
            setMensaje(
                resultado.mensaje ||
                (editando
                    ? "Serie actualizada correctamente."
                    : "Serie registrada correctamente.")
            );
            limpiarFormularioSerie();
            await cargarSeries();
        } catch (err) {
            setError(err.message);
        } finally {
            setGuardando(false);
        }
    }
    // Cargar datos de una serie en el formulario.
    function editarSerie(serie) {
        setEditandoId(serie.id);
        setTitulo(serie.titulo || "");
        setAnio(serie.anio || "");
        setDescripcion(serie.descripcion || "");
        setPortadaActual(serie.ruta_portada || null);
        setPortada(null);
        setTimeout(() => {
            const selectorPortada = document.getElementById("portada-serie");
            if (selectorPortada) selectorPortada.value = "";
        }, 0);
        setMensaje("");
        setError("");
        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });
    }
    // Obtener el nombre del archivo de portada.
    function obtenerNombreArchivo(ruta) {
        if (!ruta) return null;
        return ruta.split(/[\\/]/).pop();
    }
    // Eliminar la portada actual de la serie.
    async function eliminarPortada() {
        const confirmar = window.confirm(
            "¿Estás seguro de que deseas eliminar el archivo de portada?"
        );
        if (!confirmar) return;
        setMensaje("");
        setError("");
        try {
            setGuardando(true);
            const resultado = await solicitar(
                `/api/admin/series/${editandoId}/archivo/portada`,
                { method: "DELETE" }
            );
            setPortadaActual(null);
            setPortada(null);
            const selector = document.getElementById("portada-serie");
            if (selector) selector.value = "";
            setMensaje(resultado.mensaje || "Portada eliminada correctamente.");
            await cargarSeries();
        } catch (err) {
            setError(err.message);
        } finally {
            setGuardando(false);
        }
    }
    // Eliminar una serie completa.
    async function eliminarSerie(serie) {
        const confirmar = window.confirm(
            `¿Estás seguro de eliminar la serie "${serie.titulo}"? También se eliminarán sus temporadas, episodios y videos.`
        );
        if (!confirmar) return;
        setMensaje("");
        setError("");
        try {
            const resultado = await solicitar(
                `/api/admin/series/${serie.id}`,
                { method: "DELETE" }
            );
            setMensaje(resultado.mensaje || "Serie eliminada correctamente.");
            if (serieSeleccionada?.id === serie.id) {
                setSerieSeleccionada(null);
            }
            await cargarSeries();
        } catch (err) {
            setError(err.message);
        }
    }
    // Crear una temporada.
    async function agregarTemporada(e) {
        e.preventDefault();
        if (!serieSeleccionada) return;
        setMensaje("");
        setError("");
        try {
            setGuardando(true);
            const resultado = await solicitar(
                `/api/admin/series/${serieSeleccionada.id}/temporadas`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        numero: Number(numeroTemporada)
                    })
                }
            );
            setMensaje(resultado.mensaje || "Temporada creada correctamente.");
            setNumeroTemporada("");
            await cargarSeries();
        } catch (err) {
            setError(err.message);
        } finally {
            setGuardando(false);
        }
    }
    // Eliminar una temporada completa.
    async function eliminarTemporada(temporada) {
        const confirmar = window.confirm(
            `¿Eliminar la temporada ${temporada.numero} y todos sus episodios?`
        );
        if (!confirmar) return;
        setMensaje("");
        setError("");
        try {
            const resultado = await solicitar(
                `/api/admin/temporadas/${temporada.id}`,
                { method: "DELETE" }
            );
            setMensaje(
                resultado.mensaje || "Temporada eliminada correctamente."
            );
            if (temporadaSeleccionada?.id === temporada.id) {
                setTemporadaSeleccionada(null);
            }
            await cargarSeries();
        } catch (err) {
            setError(err.message);
        }
    }
    // Limpiar formulario de episodio.
    function limpiarFormularioEpisodio() {
        setNumeroEpisodio("");
        setTituloEpisodio("");
        setDuracionEpisodio("");
        setVideoEpisodio(null);
        setEpisodioEditandoId(null);
        const selector = document.getElementById("video-episodio");
        if (selector) selector.value = "";
    }
    // Registrar o actualizar un episodio.
    async function guardarEpisodio(e) {
        e.preventDefault();
        if (!temporadaSeleccionada) return;
        setMensaje("");
        setError("");
        const datos = new FormData();
        datos.append("numero", numeroEpisodio);
        datos.append("titulo", tituloEpisodio);
        datos.append("duracion", duracionEpisodio);
        if (videoEpisodio) {
            datos.append("archivo", videoEpisodio);
        }
        try {
            setGuardando(true);
            const editando = episodioEditandoId !== null;
            const resultado = await solicitar(
                editando
                    ? `/api/admin/episodios/${episodioEditandoId}`
                    : `/api/admin/temporadas/${temporadaSeleccionada.id}/episodios`,
                {
                    method: editando ? "PUT" : "POST",
                    body: datos
                }
            );
            setMensaje(
                resultado.mensaje ||
                (editando
                    ? "Episodio actualizado correctamente."
                    : "Episodio registrado correctamente.")
            );
            limpiarFormularioEpisodio();
            await cargarSeries();
        } catch (err) {
            setError(err.message);
        } finally {
            setGuardando(false);
        }
    }
    // Cargar episodio para editar.
    function editarEpisodio(episodio) {
        setEpisodioEditandoId(episodio.id);
        setNumeroEpisodio(episodio.numero);
        setTituloEpisodio(episodio.titulo || "");
        setDuracionEpisodio(episodio.duracion ?? "");
        setVideoEpisodio(null);
        setMensaje("");
        setError("");
        const selector = document.getElementById("video-episodio");
        if (selector) selector.value = "";
        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });
    }
    // Eliminar únicamente el video de un episodio.
    async function eliminarVideo(episodio) {
        const confirmar = window.confirm(
            `¿Eliminar el video del episodio "${episodio.titulo}"? El episodio se conservará.`
        );
        if (!confirmar) return;
        setMensaje("");
        setError("");
        try {
            const resultado = await solicitar(
                `/api/admin/episodios/${episodio.id}/archivo`,
                { method: "DELETE" }
            );
            setMensaje(resultado.mensaje || "Video eliminado correctamente.");
            await cargarSeries();
        } catch (err) {
            setError(err.message);
        }
    }
    // Eliminar un episodio completo.
    async function eliminarEpisodio(episodio) {
        const confirmar = window.confirm(
            `¿Eliminar el episodio "${episodio.titulo}"?`
        );
        if (!confirmar) return;
        setMensaje("");
        setError("");
        try {
            const resultado = await solicitar(
                `/api/admin/episodios/${episodio.id}`,
                { method: "DELETE" }
            );
            setMensaje(resultado.mensaje || "Episodio eliminado correctamente.");
            if (episodioEditandoId === episodio.id) {
                limpiarFormularioEpisodio();
            }
            await cargarSeries();
        } catch (err) {
            setError(err.message);
        }
    }
    // Obtener temporadas de la serie seleccionada.
    const temporadas = serieSeleccionada?.temporadas || [];
    // Obtener episodios de la temporada seleccionada.
    const episodios = temporadaSeleccionada?.episodios || [];
    return (
        <div className="admin-page">
            <section className="admin-section">
            <header className="admin-header">
                <div>
                    <span className="admin-subtitle">PLAYCHANNEL / SERIES</span>
                    <h1>Series</h1>
                    <p>Administra las series del catálogo de PlayChannel.</p>
                </div>
                <div className="admin-header-icon">⚙</div>
            </header>
                <h2>{serieSeleccionada ? serieSeleccionada.titulo : "Administración de series"}</h2>
                <p className="admin-description">
                    {serieSeleccionada ? "Administra las temporadas y episodios de esta serie." : "Registra y administra las series del catálogo preestablecido."}
                </p>
                {mensaje && (
                    <div className="admin-message">
                        {mensaje}
                    </div>
                )}
                {error && (
                    <div className="admin-error">
                        {error}
                    </div>
                )}
                {/* FORMULARIO DE SERIES */}
                {!serieSeleccionada && (
                    <>
                    <form className="admin-form" onSubmit={guardarSerie}>
                        <h3>
                            {editandoId
                                ? "Editar serie"
                                : "Registrar nueva serie"}
                        </h3>
                        <div className="admin-form-group">
                            <label htmlFor="titulo-serie">
                                Título de la serie
                            </label>
                            <input id="titulo-serie" type="text" value={titulo} onChange={(e) => setTitulo(e.target.value)} placeholder="Ej. Breaking Bad" required />
                        </div>
                        <div className="admin-form-group">
                            <label htmlFor="anio-serie">
                                Año de estreno
                            </label>
                            <input id="anio-serie" type="number" min="1888" max="2100" value={anio} onChange={(e) => setAnio(e.target.value)} placeholder="Ej. 2008" />
                        </div>
                        <div className="admin-form-group">
                            <label htmlFor="descripcion-serie">
                                Descripción
                            </label>
                            <textarea id="descripcion-serie" value={descripcion} onChange={(e) => setDescripcion(e.target.value)} placeholder="Descripción de la serie..." rows="4" />
                        </div>
                        <div className="admin-form-group">
                            <label htmlFor="portada-serie">Portada de la serie (opcional)</label>
                            <input id="portada-serie" type="file" accept=".png,.jpg,.jpeg,image/png,image/jpeg" onChange={(e) => setPortada(e.target.files[0] || null)} />
                            {editandoId && (
                                <div className="admin-current-file">
                                    <span>
                                        {portadaActual
                                            ? `Portada actual: ${obtenerNombreArchivo(portadaActual)}`
                                            : "No hay una portada registrada para esta serie."}
                                    </span>
                                    <button type="button" className="admin-delete-file-button" onClick={eliminarPortada} disabled={guardando || !portadaActual}>
                                        {guardando ? "Eliminando..." : "Eliminar portada"}
                                    </button>
                                </div>
                            )}
                            {portada && (
                                <span className="admin-file-name">
                                    Nueva portada seleccionada: {portada.name}
                                </span>
                            )}
                        </div>
                        <div className="admin-form-actions">
                            <button type="submit" disabled={guardando}>
                                {guardando ? "Guardando..." : editandoId ? "Guardar cambios" : "Registrar serie"}
                            </button>
                            {editandoId && (
                                <button type="button" onClick={limpiarFormularioSerie}>
                                    Cancelar edición
                                </button>
                                )}
                        </div>
                    </form>
                    <br/>
                    <div className="admin-list">
                        <h3>Series registradas</h3>
                        {cargando ? (
                            <p>Cargando series...</p>
                        ) : series.length === 0 ? (
                            <p>
                                Todavía no hay series en el catálogo preestablecido.
                            </p>
                        ) : (
                        <div className="admin-grid">
                            {series.map((serie) => (
                            <article className="admin-serie-card" key={serie.id}>
                                <div className="admin-serie-poster">
                                    {serie.ruta_portada ? (
                                        <img src={`${API_URL}/api/portadas/${encodeURIComponent(serie.ruta_portada)}`} alt={`Portada de ${serie.titulo}`} />
                                        ) : (
                                        <div className="admin-serie-poster-placeholder">
                                            📺
                                        </div>
                                    )}
                                </div>
                                <div className="admin-serie-info">
                                    <h3>{serie.titulo}</h3>
                                    <p className="admin-serie-anio">
                                        {serie.anio || "Año no indicado"}
                                    </p>
                                    <span className="admin-card-status">
                                        {serie.temporadas?.length || 0} temporadas
                                    </span>
                                    <p className="admin-serie-descripcion">
                                        {serie.descripcion || "Sin descripción"}
                                    </p>
                                </div>
                                <div className="admin-serie-actions">
                                    <button type="button" onClick={() => {
                                            setSerieSeleccionada(serie);
                                            setTemporadaSeleccionada(null);
                                            limpiarFormularioSerie();
                                            setMensaje("");
                                            setError("");}}>
                                        Administrar
                                    </button>
                                    <button type="button" onClick={() => editarSerie(serie)}>
                                        Editar
                                    </button>
                                    <button type="button" onClick={() => eliminarSerie(serie)}>
                                        Eliminar
                                    </button>
                                </div>
                            </article>
                            ))}
                        </div>
                        )}
                    </div>
                    </>
                )}
                {/* ADMINISTRACIÓN DE TEMPORADAS */}
                {serieSeleccionada && !temporadaSeleccionada && (
                    <>
                    <form className="admin-form" onSubmit={agregarTemporada}>
                        <h3>Agregar temporada</h3>
                        <div className="admin-form-group">
                            <label htmlFor="numero-temporada">
                                Número de temporada
                            </label>
                            <input id="numero-temporada" type="number" min="1" value={numeroTemporada} onChange={(e) => setNumeroTemporada(e.target.value)} placeholder="Ej. 1" required />
                        </div>
                        <button type="submit" disabled={guardando}>
                            {guardando ? "Guardando..." : "Agregar temporada"}
                        </button>
                    </form>
                    <div className="admin-list">
                        <h3>Temporadas</h3>
                        {temporadas.length === 0 ? (
                            <p>Esta serie todavía no tiene temporadas.</p>
                            ) : (
                            <div className="admin-grid">
                                {temporadas.map((temporada) => (
                                    <article className="admin-card" key={temporada.id}>
                                        <div className="admin-card-icon">
                                            🎞️
                                        </div>
                                        <h3>
                                            Temporada {temporada.numero}
                                        </h3>
                                        <p>
                                            {temporada.episodios?.length || 0} {" "}episodios
                                        </p>
                                        <div className="admin-form-actions">
                                            <button type="button" onClick={() => setTemporadaSeleccionada(temporada)}>
                                                Ver episodios
                                            </button>
                                            <button type="button" onClick={() => eliminarTemporada(temporada)}>
                                                Eliminar
                                            </button>
                                        </div>
                                    </article>
                                ))}
                            </div>
                        )}
                    </div>
                    </>
                )}
                {/* ADMINISTRACIÓN DE EPISODIOS */}
                {serieSeleccionada && temporadaSeleccionada && (
                    <>
                    <button type="button" className="admin-back-button" onClick={() => {
                            setTemporadaSeleccionada(null);
                            limpiarFormularioEpisodio();
                            setMensaje("");
                            setError("");
                        }}
                    >
                        ← Volver a temporadas
                    </button>
                    <h3>
                        Temporada {temporadaSeleccionada.numero}
                    </h3>
                    <form className="admin-form" onSubmit={guardarEpisodio}>
                        <h3>
                            {episodioEditandoId ? "Editar episodio" : "Registrar episodio"}
                        </h3>
                        <div className="admin-form-row">
                            <div className="admin-form-group">
                                <label htmlFor="numero-episodio">
                                    Número de episodio
                                </label>
                                <input id="numero-episodio" type="number" min="1" value={numeroEpisodio} onChange={(e) => setNumeroEpisodio(e.target.value)} placeholder="Ej. 1" required />
                            </div>
                            <div className="admin-form-group">
                                <label htmlFor="duracion-episodio">
                                    Duración en minutos
                                </label>
                                <input id="duracion-episodio" type="number" min="1" value={duracionEpisodio} onChange={(e) => setDuracionEpisodio(e.target.value)} placeholder="Ej. 45" />
                            </div>
                        </div>
                        <div className="admin-form-group">
                            <label htmlFor="titulo-episodio">
                                Título del episodio
                            </label>
                            <input id="titulo-episodio" type="text" value={tituloEpisodio} onChange={(e) => setTituloEpisodio(e.target.value)} placeholder="Ej. El comienzo" required />
                        </div>
                        <div className="admin-form-group">
                            <label htmlFor="video-episodio">
                                Video del episodio
                            </label>
                            <input id="video-episodio" type="file" accept="video/*" onChange={(e) => setVideoEpisodio(e.target.files?.[0] || null)} required={!episodioEditandoId} />
                            {episodioEditandoId && (
                                <small>
                                    Si seleccionas un archivo, reemplazará el video actual.
                                </small>
                            )}
                        </div>
                        <div className="admin-form-actions">
                            <button type="submit" disabled={guardando}>
                                {guardando ? "Guardando..." : episodioEditandoId ? "Guardar cambios" : "Registrar episodio"}
                            </button>
                            {episodioEditandoId && (
                                <button type="button" onClick={limpiarFormularioEpisodio}>
                                    Cancelar edición
                                </button>
                            )}
                        </div>
                    </form>
                    <div className="admin-list">
                        <h3>Episodios registrados</h3>
                        {episodios.length === 0 ? (
                            <p>
                                Esta temporada todavía no tiene episodios.
                            </p>
                            ) : (
                            <div className="admin-grid">
                                {episodios.map((episodio) => (
                                    <article className="admin-card" key={episodio.id}>
                                        <div className="admin-card-icon">
                                            ▶
                                        </div>
                                        <h3>
                                            Episodio {episodio.numero}
                                        </h3>
                                        <p>{episodio.titulo}</p>
                                        <p>
                                            Duración:{" "}{episodio.duracion? `${episodio.duracion} minutos` : "No indicada"}
                                        </p>
                                        <p>
                                            Video:{" "}{episodio.ruta_archivo ? "Cargado" : "Sin video"}
                                        </p>
                                        <div className="admin-form-actions">
                                            <button type="button" onClick={() => editarEpisodio(episodio)}>
                                                Editar
                                            </button>
                                            {episodio.ruta_archivo && (
                                                <button type="button" onClick={() => eliminarVideo(episodio)}>
                                                    Eliminar video
                                                </button>
                                            )}
                                            <button type="button" onClick={() => eliminarEpisodio(episodio)}>
                                                Eliminar episodio
                                            </button>
                                        </div>
                                    </article>
                                ))}
                            </div>
                        )}
                    </div>
                    </>
                )}
            </section>
        </div>
    );
}

export default AdminSeries;