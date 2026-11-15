import { useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:5000";

function AdminCatalogo() {
    const [peliculas, setPeliculas] = useState([]);
    const [series, setSeries] = useState([]);
    const [filtro, setFiltro] = useState("todos");
    const [cargando, setCargando] = useState(true);
    const [error, setError] = useState("");

    async function cargarCatalogo() {
        try {
            setCargando(true);
            setError("");

            const [respuestaPeliculas, respuestaSeries] = await Promise.all([
                fetch(`${API_URL}/api/admin/peliculas`),
                fetch(`${API_URL}/api/admin/series`)
            ]);

            if (!respuestaPeliculas.ok || !respuestaSeries.ok) {
                throw new Error("No se pudo cargar el catálogo.");
            }

            const datosPeliculas = await respuestaPeliculas.json();
            const datosSeries = await respuestaSeries.json();

            setPeliculas(Array.isArray(datosPeliculas) ? datosPeliculas : []);
            setSeries(Array.isArray(datosSeries) ? datosSeries : []);
        } catch (err) {
            setError(err.message || "Error al conectar con el servidor.");
        } finally {
            setCargando(false);
        }
    }

    useEffect(() => {
        cargarCatalogo();
    }, []);

    const contenido = [
        ...peliculas.map((pelicula) => ({
            ...pelicula,
            tipo_contenido: "pelicula",
            identificador: `pelicula-${pelicula.contenido_id}`
        })),
        ...series.map((serie) => ({
            ...serie,
            tipo_contenido: "serie",
            identificador: `serie-${serie.id}`
        }))
    ];

    const contenidoFiltrado = contenido.filter((item) =>
        filtro === "todos" || item.tipo_contenido === filtro
    );

    return (
        <div className="admin-page">
            <header className="admin-header">
                <div>
                    <span className="admin-subtitle">PLAYCHANNEL / CATÁLOGO</span>
                    <h1>Catálogo</h1>
                    <p>Revisa el catálogo de PlayChannel.</p>
                </div>
                <div className="admin-header-icon">⚙</div>
            </header>

            <section className="admin-section">
                <h2>Catálogo preestablecido</h2>
                <p className="admin-description">
                    Visualiza todas las películas y series registradas en PlayChannel.
                </p>

                <div className="admin-catalogo-resumen">
                    <div className="admin-card">
                        <h3>{contenido.length}</h3>
                        <p>Contenido total</p>
                    </div>
                    <div className="admin-card">
                        <h3>{peliculas.length}</h3>
                        <p>Películas</p>
                    </div>
                    <div className="admin-card">
                        <h3>{series.length}</h3>
                        <p>Series</p>
                    </div>
                </div>

                <div className="admin-catalogo-controles">
                    <h3>Contenido disponible</h3>

                    <div className="admin-catalogo-filtros">
                        <button type="button" className={filtro === "todos" ? "activo" : ""} onClick={() => setFiltro("todos")}>
                            Todos
                        </button>
                        <button type="button" className={filtro === "pelicula" ? "activo" : ""} onClick={() => setFiltro("pelicula")}>
                            Películas
                        </button>
                        <button type="button" className={filtro === "serie" ? "activo" : ""} onClick={() => setFiltro("serie")}>
                            Series
                        </button>
                    </div>
                </div>

                {error && (
                    <div className="admin-message error">{error}</div>
                )}

                {cargando ? (
                    <p className="admin-description">Cargando catálogo...</p>
                ) : contenidoFiltrado.length === 0 ? (
                    <div className="admin-catalogo-vacio">
                        <h3>No hay contenido disponible</h3>
                        <p>
                            No se encontraron elementos en esta categoría.
                        </p>
                    </div>
                ) : (
                    <div className="admin-catalogo-grid">
                        {contenidoFiltrado.map((item) => (
                            <article className="admin-movie-card" key={item.identificador}>
                                <div className="admin-catalogo-poster">
                                    {item.ruta_portada ? (
                                        <img
                                            src={`${API_URL}/api/portadas/${encodeURIComponent(item.ruta_portada)}`}
                                            alt={`Portada de ${item.titulo}`}
                                        />
                                    ) : (
                                        <div className="admin-movie-poster-placeholder">
                                            {item.tipo_contenido === "pelicula" ? "🎬" : "📺"}
                                        </div>
                                    )}
                                </div>

                                <div className="admin-movie-info">
                                    <span className="admin-catalogo-tipo">
                                        {item.tipo_contenido === "pelicula" ? "PELÍCULA" : "SERIE"}
                                    </span>
                                    <h3>{item.titulo}</h3>
                                    <p>{item.anio || "Año no indicado"}</p>
                                    {item.tipo_contenido === "pelicula" ? (
                                        <p>
                                            {item.duracion
                                                ? `${item.duracion} min`
                                                : "Duración no indicada"}
                                        </p>
                                    ) : (
                                        <p>
                                            {item.temporadas?.length || 0} temporadas
                                        </p>
                                    )}
                                </div>
                            </article>
                        ))}
                    </div>
                )}
            </section>
        </div>
    );
}

export default AdminCatalogo;
