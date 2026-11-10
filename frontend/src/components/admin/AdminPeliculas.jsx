import { useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:5000";

function AdminPeliculas({ volverInicio }) {
    const [titulo, setTitulo] = useState("");
    const [anio, setAnio] = useState("");
    const [duracion, setDuracion] = useState("");
    const [archivo, setArchivo] = useState(null);
    const [portada, setPortada] = useState(null);
    const [peliculas, setPeliculas] = useState([]);
    const [editandoId, setEditandoId] = useState(null);
    const [mensaje, setMensaje] = useState("");
    const [error, setError] = useState("");
    const [guardando, setGuardando] = useState(false);
    const [cargando, setCargando] = useState(false);
    const [videoActual, setVideoActual] = useState(null);
    const [portadaActual, setPortadaActual] = useState(null);

    async function cargarPeliculas() {
        try {
            setCargando(true);
            setError("");
            const respuesta = await fetch(`${API_URL}/api/admin/peliculas`);
            const resultado = await respuesta.json();

            if (!respuesta.ok) {
                throw new Error(resultado.mensaje || "No se pudieron cargar las películas.");
            }

            setPeliculas(resultado);
        } catch (err) {
            setError(err.message || "Error de conexión con el servidor.");
        } finally {
            setCargando(false);
        }
    }

    useEffect(() => {
        cargarPeliculas();
    }, []);

    function limpiarFormulario() {
        setTitulo("");
        setAnio("");
        setDuracion("");
        setArchivo(null);
        setPortada(null);
        setEditandoId(null);

        const selectorVideo = document.getElementById("archivo-pelicula");
        const selectorPortada = document.getElementById("portada-pelicula");

        if (selectorVideo) selectorVideo.value = "";
        if (selectorPortada) selectorPortada.value = "";

        setVideoActual(null);
        setPortadaActual(null);
    }

    async function guardarPelicula(e) {
        e.preventDefault();
        setMensaje("");
        setError("");

        if (!editandoId && !archivo) {
            setError("Debes seleccionar un archivo de video.");
            return;
        }

        const datos = new FormData();
        datos.append("titulo", titulo);
        datos.append("anio", anio);
        datos.append("duracion", duracion);

        if (archivo) datos.append("archivo", archivo);
        if (portada) datos.append("portada", portada);

        const editando = editandoId !== null;

        try {
            setGuardando(true);
            const respuesta = await fetch(
                editando
                    ? `${API_URL}/api/admin/peliculas/${editandoId}`
                    : `${API_URL}/api/admin/peliculas`,
                {
                    method: editando ? "PUT" : "POST",
                    body: datos
                }
            );

            const resultado = await respuesta.json();

            if (!respuesta.ok) {
                throw new Error(resultado.mensaje || "No se pudo guardar la película.");
            }

            setMensaje(resultado.mensaje);
            limpiarFormulario();
            await cargarPeliculas();
        } catch (err) {
            setError(err.message || "Error de conexión con el servidor.");
        } finally {
            setGuardando(false);
        }
    }

    function obtenerNombreArchivo(ruta) {
        if (!ruta) return null;
        return ruta.split(/[\\/]/).pop();
    }

    function editarPelicula(pelicula) {
        setEditandoId(pelicula.contenido_id);
        setTitulo(pelicula.titulo);
        setAnio(pelicula.anio);
        setDuracion(pelicula.duracion);
        setVideoActual(pelicula.ruta_archivo || null);
        setPortadaActual(pelicula.ruta_portada || null);
        setArchivo(null);
        setPortada(null);
        setMensaje("");
        setError("");

        setTimeout(() => {
            const selectorVideo = document.getElementById("archivo-pelicula");
            const selectorPortada = document.getElementById("portada-pelicula");
            if (selectorVideo) selectorVideo.value = "";
            if (selectorPortada) selectorPortada.value = "";
        }, 0);

        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    async function eliminarPelicula(pelicula) {
        const confirmar = window.confirm(
            `¿Estás seguro de que deseas eliminar "${pelicula.titulo}"? Esta acción no se puede deshacer.`
        );

        if (!confirmar) return;

        setMensaje("");
        setError("");

        try {
            setGuardando(true);
            const respuesta = await fetch(
                `${API_URL}/api/admin/peliculas/${pelicula.contenido_id}`,
                { method: "DELETE" }
            );

            const resultado = await respuesta.json();

            if (!respuesta.ok) {
                throw new Error(resultado.mensaje || "No se pudo eliminar la película.");
            }

            setMensaje(resultado.mensaje);
            await cargarPeliculas();
        } catch (err) {
            setError(err.message || "Error al eliminar la película.");
        } finally {
            setGuardando(false);
        }
    }

    async function eliminarArchivo(tipo) {
        const nombre = tipo === "video" ? "video" : "portada";
        const confirmar = window.confirm(
            `¿Estás seguro de que deseas eliminar el archivo de ${nombre}?`
        );

        if (!confirmar) return;

        setMensaje("");
        setError("");

        try {
            setGuardando(true);
            const respuesta = await fetch(
                `${API_URL}/api/admin/peliculas/${editandoId}/archivo/${tipo}`,
                { method: "DELETE" }
            );

            const resultado = await respuesta.json();

            if (!respuesta.ok) {
                throw new Error(resultado.mensaje || "No se pudo eliminar el archivo.");
            }

            if (tipo === "video") {
                setVideoActual(null);
                setArchivo(null);
                const selector = document.getElementById("archivo-pelicula");
                if (selector) selector.value = "";
            } else {
                setPortadaActual(null);
                setPortada(null);
                const selector = document.getElementById("portada-pelicula");
                if (selector) selector.value = "";
            }

            setMensaje(resultado.mensaje);
            await cargarPeliculas();
        } catch (err) {
            setError(err.message || "Error al eliminar el archivo.");
        } finally {
            setGuardando(false);
        }
    }

    return (
        <section className="admin-section">
            <h2>{editandoId ? "Editar película" : "Registro de películas"}</h2>
            <p className="admin-description">
                {editandoId
                    ? "Modifica los datos de la película seleccionada."
                    : "Incorpora nuevas películas al catálogo preestablecido."}
            </p>

            <form className="admin-form" onSubmit={guardarPelicula}>
                <div className="admin-form-group">
                    <label htmlFor="titulo">Título de la película</label>
                    <input
                        id="titulo"
                        type="text"
                        value={titulo}
                        onChange={(e) => setTitulo(e.target.value)}
                        placeholder="Ej. Volver al futuro"
                        required
                    />
                </div>

                <div className="admin-form-row">
                    <div className="admin-form-group">
                        <label htmlFor="anio">Año de estreno</label>
                        <input
                            id="anio"
                            type="number"
                            min="1888"
                            max="2100"
                            value={anio}
                            onChange={(e) => setAnio(e.target.value)}
                            placeholder="Ej. 1985"
                            required
                        />
                    </div>

                    <div className="admin-form-group">
                        <label htmlFor="duracion">Duración (minutos)</label>
                        <input
                            id="duracion"
                            type="number"
                            min="1"
                            value={duracion}
                            onChange={(e) => setDuracion(e.target.value)}
                            placeholder="Ej. 116"
                            required
                        />
                    </div>
                </div>

                <div className="admin-form-group">
                    <label htmlFor="archivo-pelicula">
                        Archivo de video {editandoId && "(opcional)"}
                    </label>
                    <input
                        id="archivo-pelicula"
                        type="file"
                        accept=".mp4,.mkv,.webm,.avi,.mov,video/*"
                        onChange={(e) => setArchivo(e.target.files[0] || null)}
                        required={!editandoId && !videoActual}
                    />

                    {editandoId && videoActual && (
                        <div className="admin-current-file">
                            <span>Archivo actual: {obtenerNombreArchivo(videoActual)}</span>
                            <button
                                type="button"
                                className="admin-delete-file-button"
                                onClick={() => eliminarArchivo("video")}
                                disabled={guardando}
                            >
                                Eliminar archivo
                            </button>
                        </div>
                    )}

                    {archivo && (
                        <span className="admin-file-name">
                            Nuevo archivo seleccionado: {archivo.name}
                        </span>
                    )}
                </div>

                <div className="admin-form-group">
                    <label htmlFor="portada-pelicula">Portada de la película (opcional)</label>
                    <input
                        id="portada-pelicula"
                        type="file"
                        accept=".png,.jpg,.jpeg,image/png,image/jpeg"
                        onChange={(e) => setPortada(e.target.files[0] || null)}
                    />

                    {editandoId && portadaActual && (
                        <div className="admin-current-file">
                            <span>Archivo actual: {obtenerNombreArchivo(portadaActual)}</span>
                            <button
                                type="button"
                                className="admin-delete-file-button"
                                onClick={() => eliminarArchivo("portada")}
                                disabled={guardando}
                            >
                                Eliminar archivo
                            </button>
                        </div>
                    )}

                    {portada && (
                        <span className="admin-file-name">
                            Nueva portada seleccionada: {portada.name}
                        </span>
                    )}
                </div>

                {mensaje && <p className="admin-message success">{mensaje}</p>}
                {error && <p className="admin-message error">{error}</p>}

                <div className="admin-form-actions">
                    <button
                        type="submit"
                        className="admin-submit-button"
                        disabled={guardando}
                    >
                        {guardando
                            ? "Guardando..."
                            : editandoId
                                ? "Guardar cambios"
                                : "Agregar película"}
                    </button>

                    {editandoId && (
                        <button
                            type="button"
                            className="admin-back-button"
                            onClick={() => {
                                limpiarFormulario();
                                setMensaje("");
                                setError("");
                            }}
                        >
                            Cancelar edición
                        </button>
                    )}
                </div>
            </form>

            <div className="admin-list-section">
                <h2>Películas registradas</h2>

                {cargando && <p>Cargando películas...</p>}

                {!cargando && peliculas.length === 0 && (
                    <p className="admin-description">
                        No hay películas registradas en el catálogo.
                    </p>
                )}

                <div className="admin-movies-grid">
                    {peliculas.map((pelicula) => (
                        <article className="admin-movie-card" key={pelicula.contenido_id}>
                            {pelicula.ruta_portada ? (
                                <img
                                    className="admin-movie-poster"
                                    src={`${API_URL}/api/portadas/${encodeURIComponent(pelicula.ruta_portada)}`}
                                    alt={`Portada de ${pelicula.titulo}`}
                                />
                            ) : (
                                <div className="admin-movie-poster-placeholder">🎬</div>
                            )}

                            <div className="admin-movie-info">
                                <h3>{pelicula.titulo}</h3>
                                <p>{pelicula.anio} · {pelicula.duracion} min</p>

                                <button
                                    type="button"
                                    className="admin-edit-button"
                                    onClick={() => editarPelicula(pelicula)}
                                    disabled={guardando}
                                >
                                    Editar
                                </button>

                                <button
                                    type="button"
                                    className="admin-delete-button"
                                    onClick={() => eliminarPelicula(pelicula)}
                                    disabled={guardando}
                                >
                                    Eliminar
                                </button>
                            </div>
                        </article>
                    ))}
                </div>
            </div>
        </section>
    );
}

export default AdminPeliculas;
