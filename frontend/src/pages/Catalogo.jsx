import { useCallback, useEffect, useState } from "react";
import "../css/Catalogo.css";

const API_URL = "http://127.0.0.1:5000";

// Muestra el catálogo preestablecido y permite agregar contenido a la biblioteca.
function Catalogo() {
    const [contenido, setContenido] = useState([]);
    const [miContenido, setMiContenido] = useState([]);
    const [filtro, setFiltro] = useState("todos");
    const [cargando, setCargando] = useState(true);
    const [error, setError] = useState("");
    const [mensaje, setMensaje] = useState("");
    const [agregando, setAgregando] = useState(null);

    // Consulta el catálogo y la biblioteca personal del usuario.
    const cargarDatos = useCallback(async () => {
        try {
            setCargando(true);
            setError("");

            const [respuestaCatalogo, respuestaUsuario] = await Promise.all([
                fetch(`${API_URL}/api/catalogo`),
                fetch(`${API_URL}/api/mi-contenido`)
            ]);

            if (!respuestaCatalogo.ok || !respuestaUsuario.ok) {
                throw new Error("No se pudo cargar el catálogo.");
            }

            const datosCatalogo = await respuestaCatalogo.json();
            const datosUsuario = await respuestaUsuario.json();

            setContenido(datosCatalogo);
            setMiContenido(datosUsuario);
        } catch (err) {
            setError(err.message || "No se pudo conectar con el servidor.");
        } finally {
            setCargando(false);
        }
    }, []);

    useEffect(() => {
        cargarDatos();
    }, [cargarDatos]);

    // Comprueba si un contenido ya pertenece a Mi contenido.
    function estaAgregado(item) {
        return miContenido.some(
            (elemento) =>
                elemento.tipo_contenido === item.tipo_contenido &&
                Number(elemento.contenido_id) === Number(item.contenido_id)
        );
    }

    // Agrega una película o serie del catálogo a Mi contenido.
    async function agregarContenido(item) {
        const clave = `${item.tipo_contenido}-${item.contenido_id}`;

        try {
            setAgregando(clave);
            setError("");
            setMensaje("");

            const respuesta = await fetch(`${API_URL}/api/mi-contenido`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    tipo_contenido: item.tipo_contenido,
                    contenido_id: Number(item.contenido_id)
                })
            });

            const resultado = await respuesta.json();

            if (!respuesta.ok) {
                throw new Error(
                    resultado.mensaje || "No se pudo agregar el contenido."
                );
            }

            setMensaje(`${item.titulo} se agregó a Mi contenido.`);

            await cargarDatos();
        } catch (err) {
            setError(err.message || "No se pudo conectar con el servidor.");
        } finally {
            setAgregando(null);
        }
    }

    const contenidoFiltrado = contenido.filter((item) => {
        return filtro === "todos" || item.tipo_contenido === filtro;
    });

    return (
        <section className="catalogo-page">
            <header className="catalogo-header">
                <div>
                    <span className="section-label">
                        PLAYCHANNEL / BIBLIOTECA DISPONIBLE
                    </span>
                    <h1>Catálogo</h1>
                    <p>
                        Explora el contenido disponible y agrega lo que
                        quieras incorporar a tu biblioteca.
                    </p>
                </div>

                <div className="catalogo-header-icon">▦</div>
            </header>

            <section className="catalogo-controles">
                <div>
                    <h2>Contenido disponible</h2>
                    <p>
                        {contenido.length} elementos en el catálogo
                    </p>
                </div>

                <div className="catalogo-filtros">
                    <button className={filtro === "todos" ? "activo" : ""} onClick={() => setFiltro("todos")}>
                        Todos
                    </button>

                    <button className={filtro === "pelicula" ? "activo" : ""} onClick={() => setFiltro("pelicula")}>
                        Películas
                    </button>

                    <button className={filtro === "serie" ? "activo" : ""} onClick={() => setFiltro("serie")}>
                        Series
                    </button>
                </div>
            </section>

            {error && <p className="catalogo-error">{error}</p>}
            {mensaje && <p className="catalogo-exito">{mensaje}</p>}

            {cargando ? (
                <p className="catalogo-vacio">Cargando catálogo...</p>
            ) : contenidoFiltrado.length === 0 ? (
                <div className="catalogo-vacio">
                    <span>▦</span>
                    <h3>No hay contenido disponible</h3>
                    <p>
                        {contenido.length === 0
                            ? "Todavía no se han incorporado películas o series al catálogo."
                            : "No hay elementos disponibles en esta categoría."}
                    </p>
                </div>
            ) : (
                <div className="catalogo-grid">
                    {contenidoFiltrado.map((item) => {
                        const agregado = estaAgregado(item);
                        const clave = `${item.tipo_contenido}-${item.contenido_id}`;

                        return (
                        <article className="catalogo-card" key={clave}>
                            <div className="catalogo-poster-container">
                                {item.ruta_portada ? (
                                    <img
                                        src={`${API_URL}/api/portadas/${encodeURIComponent(item.ruta_portada)}`}
                                        alt={`Portada de ${item.titulo}`}
                                        className="catalogo-card-poster"
                                    />
                                ) : (
                                    <div className="catalogo-poster-placeholder">
                                        {item.tipo_contenido === "pelicula" ? "▶" : "▤"}
                                    </div>
                                )}

                                <button
                                    className={`catalogo-agregar ${agregado ? "agregado" : ""}`} onClick={() => agregarContenido(item)} disabled={agregado || agregando === clave}>
                                    <span className="catalogo-agregar-icono">
                                        {agregado ? "✓" : agregando === clave ? "…" : "+"}
                                    </span>

                                    <span className="catalogo-agregar-texto">
                                        {agregado ? "En Mi contenido" : agregando === clave ? "Agregando..." : "Agregar contenido"}
                                    </span>
                                </button>
                            </div>

                            <div className="catalogo-card-info">
                                <span className="catalogo-tipo">
                                    {item.tipo_contenido === "pelicula" ? "PELÍCULA" : "SERIE"}
                                </span>
                                <h3>{item.titulo}</h3>
                                <p>
                                    {item.anio || "Año desconocido"} {item.duracion ? ` · ${item.duracion} min` : ""}
                                </p>
                            </div>
                        </article>
                        );
                    })}
                </div>
            )}
        </section>
    );
}

export default Catalogo;
