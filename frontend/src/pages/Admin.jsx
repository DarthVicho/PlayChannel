import { useEffect, useState } from "react";
import "../css/Admin.css";

const API_URL = "http://127.0.0.1:5000";

function Admin() {
    const [vista, setVista] = useState("inicio");
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

    //Obtener las películas del catálogo preestablecido.
    async function cargarPeliculas() {
        try {
            setCargando(true);
            setError("");
            const respuesta = await fetch(
                `${API_URL}/api/admin/peliculas`
            );
            const resultado = await respuesta.json();
            if (!respuesta.ok) {
                throw new Error(
                    resultado.mensaje || "No se pudieron cargar las películas."
                );
            }
            setPeliculas(resultado);
        } catch (err) {
            setError(err.message || "Error de conexión con el servidor.");
        } finally {
            setCargando(false);
        }
    }

    //Cargar películas al entrar en la sección.
    useEffect(() => {
        if (vista === "peliculas") {
            cargarPeliculas();
        }
    }, [vista]);

    //Limpiar los campos del formulario.
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
    }

    //Registrar o editar una película.
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
        if (archivo) {
            datos.append("archivo", archivo);
        }
        if (portada) {
            datos.append("portada", portada);
        }
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
                throw new Error(
                    resultado.mensaje || "No se pudo guardar la película."
                );
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

    // Cargar los datos de una película en el formulario.
    function editarPelicula(pelicula) {
        setEditandoId(pelicula.contenido_id);
        setTitulo(pelicula.titulo);
        setAnio(pelicula.anio);
        setDuracion(pelicula.duracion);
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
        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });
    }

    //Eliminar una pelicula del catalogo
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
                {
                    method: "DELETE"
                }
            );
            const resultado = await respuesta.json();
            if (!respuesta.ok){
                throw new Error(
                    resultado.mensaje || "No se pudo eliminar la película"
                );
            }
            setMensaje(resultado.mensaje);
            await cargarPeliculas();
        } catch (err) {
            setError(err.mensaje || "Error al eliminar la película");
        } finally {
            setGuardando(false);
        }
    }

    return (
        <div className="admin-page">
            <header className="admin-header">
                <div>
                    <span className="admin-subtitle">PLAYCHANNEL / GESTIÓN</span>
                    <h1>Administración</h1>
                    <p>
                        Administra el contenido y las funcionalidades de tu canal personal.
                    </p>
                </div>
                <div className="admin-header-icon">⚙</div>
            </header>

            {vista === "inicio" && (
                <>
                    <section className="admin-section">
                        <h2>Gestión de contenido</h2>
                        <p className="admin-description">
                            Administra las películas y series que formarán parte del catálogo preestablecido.
                        </p>
                        <div className="admin-grid">
                            <article className="admin-card" onClick={() => {limpiarFormulario(); setMensaje(""); setError(""); setVista("peliculas");}}>
                                <div className="admin-card-icon">🎬</div>
                                <h3>Películas</h3>
                                <p>
                                    Agrega nuevas películas y modifica sus datos dentro del catálogo.
                                </p>
                                <span className="admin-card-status">
                                    Gestión de películas →
                                </span>
                            </article>

                            <article className="admin-card">
                                <div className="admin-card-icon">📺</div>
                                <h3>Series</h3>
                                <p>
                                    Registra series, administra temporadas y agrega sus episodios.
                                </p>
                                <span className="admin-card-status">
                                    Gestión de series
                                </span>
                            </article>

                            <article className="admin-card">
                                <div className="admin-card-icon">▤</div>
                                <h3>Catálogo preestablecido</h3>
                                <p>
                                    Consulta y administra el contenido incorporado al catálogo de PlayChannel.
                                </p>
                                <span className="admin-card-status">
                                    Gestión del catálogo
                                </span>
                            </article>
                        </div>
                    </section>

                    <section className="admin-section">
                        <h2>Configuración del sistema</h2>
                        <div className="admin-grid">
                            <article className="admin-card">
                                <div className="admin-card-icon">⚙</div>
                                <h3>Funcionalidades</h3>
                                <p>
                                    Gestiona las opciones y el comportamiento general de PlayChannel.
                                </p>
                                <span className="admin-card-status">
                                    Configuración del sistema
                                </span>
                            </article>
                        </div>
                    </section>
                </>
            )}

            {vista === "peliculas" && (
                <section className="admin-section">
                    <button type="button" className="admin-back-button" onClick={() => {limpiarFormulario(); setMensaje(""); setError(""); setVista("inicio");}}>
                        ← Volver a administración
                    </button>

                    <h2>
                        {editandoId ? "Editar película" : "Registro de películas"}
                    </h2>

                    <p className="admin-description">
                        {editandoId? "Modifica los datos de la película seleccionada.": "Incorpora nuevas películas al catálogo preestablecido."}
                    </p>

                    <form className="admin-form" onSubmit={guardarPelicula}>
                        <div className="admin-form-group">
                            <label htmlFor="titulo">
                                Título de la película
                            </label>
                            <input id="titulo" type="text" value={titulo} onChange={(e) => setTitulo(e.target.value)} placeholder="Ej. Volver al futuro" required/>
                        </div>

                        <div className="admin-form-row">
                            <div className="admin-form-group">
                                <label htmlFor="anio">Año de estreno</label>
                                <input id="anio" type="number" min="1888" max="2100" value={anio} onChange={(e) => setAnio(e.target.value)} placeholder="Ej. 1985" required/>
                            </div>

                            <div className="admin-form-group">
                                <label htmlFor="duracion">
                                    Duración (minutos)
                                </label>
                                <input id="duracion" type="number" min="1" value={duracion} onChange={(e) => setDuracion(e.target.value)} placeholder="Ej. 116" required/>
                            </div>
                        </div>

                        <div className="admin-form-group">
                            <label htmlFor="archivo-pelicula">
                                Archivo de video
                                {editandoId && " (opcional)"}
                            </label>
                            <input id="archivo-pelicula" type="file" accept=".mp4,.mkv,.webm,.avi,.mov,video/*" onChange={(e) => setArchivo(e.target.files[0] || null)} required={!editandoId}/>
                            {archivo && (
                                <span className="admin-file-name">
                                    Archivo seleccionado: {archivo.name}
                                </span>
                            )}
                        </div>

                        <div className="admin-form-group">
                            <label htmlFor="portada-pelicula">
                                Portada de la película (opcional)
                            </label>
                            <input id="portada-pelicula" type="file" accept=".png,.jpg,.jpeg,image/png,image/jpeg" onChange={(e) => setPortada(e.target.files[0] || null)}/>
                            {portada && (
                                <span className="admin-file-name">
                                    Portada seleccionada: {portada.name}
                                </span>
                            )}
                        </div>

                        {mensaje && (
                            <p className="admin-message success">{mensaje}</p>
                        )}

                        {error && (
                            <p className="admin-message error">{error}</p>
                        )}

                        <div className="admin-form-actions">
                            <button type="submit" className="admin-submit-button" disabled={guardando}>
                                {guardando ? "Guardando..." : editandoId ? "Guardar cambios" : "Agregar película"}
                            </button>
                            {editandoId && (
                                <button type="button" className="admin-back-button" onClick={() => {limpiarFormulario(); setMensaje(""); setError("");}}>
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
                                        <img className="admin-movie-poster" src={`${API_URL}/api/portadas/${encodeURIComponent(pelicula.ruta_portada)}`} alt={`Portada de ${pelicula.titulo}`}/>
                                    ) : (
                                        <div className="admin-movie-poster-placeholder">
                                            🎬
                                        </div>
                                    )}
                                    <div className="admin-movie-info">
                                        <h3>{pelicula.titulo}</h3>
                                        <p>
                                            {pelicula.anio} · {pelicula.duracion} min
                                        </p>
                                        <button type="button" className="admin-edit-button" onClick={() => editarPelicula(pelicula)} disabled={guardando}>
                                            Editar
                                        </button>
                                        <button type="button" className="admin-delete-button" onClick={() => eliminarPelicula(pelicula)} disabled={guardando}>
                                            Eliminar
                                        </button>
                                    </div>
                                </article>
                            ))}
                        </div>
                    </div>
                </section>
            )}
        </div>
    );
}

export default Admin;