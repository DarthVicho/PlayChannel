import { useEffect, useState } from "react";
import "../../css/AdminDashboard.css";

function AdminDashboard() {
    const [estadisticas, setEstadisticas] = useState({
        total_peliculas: 0,
        total_series: 0,
        total_episodios: 0
    });
    const [estadoSistema, setEstadoSistema] = useState("Conectando...");
    const [cargando, setCargando] = useState(true);

    useEffect(() => {
        async function cargarEstadisticas() {
            try {
                const respuesta = await fetch("http://127.0.0.1:5000/api/admin/estadisticas");
                if (!respuesta.ok) {
                    throw new Error("Error al consultar las estadísticas");
                }
                const datos = await respuesta.json();
                setEstadisticas(datos);
                setEstadoSistema("Sistema activo");
            } catch (error) {
                setEstadoSistema("Sin conexión");
            } finally {
                setCargando(false);
            }
        }
        cargarEstadisticas();
    }, []);

    const indicadores = [
        { titulo: "Películas", valor: estadisticas.total_peliculas, icono: "🎬" },
        { titulo: "Series", valor: estadisticas.total_series, icono: "📺" },
        { titulo: "Episodios", valor: estadisticas.total_episodios, icono: "🎞️" },
        { titulo: "Horas reproducidas", valor: "--", icono: "🕓" }
    ];

    const totalCatalogo = estadisticas.total_peliculas + estadisticas.total_series + estadisticas.total_episodios;
    const porcentaje = (valor) => totalCatalogo > 0 ? (valor / totalCatalogo) * 100 : 0;

    return (
        <main className="dashboard-admin">
            <header className="dashboard-header">
                <div>
                    <span className="dashboard-subtitle">PLAYCHANNEL / DASHBOARD</span>
                    <h1>Panel de administración</h1>
                    <p>Resumen general de tu canal personal.</p>
                </div>
                <span className={`dashboard-status ${estadoSistema === "Sistema activo" ? "activo" : "inactivo"}`}>
                    {estadoSistema}
                </span>
            </header>

            <section className="dashboard-stats-grid">
                {indicadores.map((indicador) => (
                    <article className="dashboard-stat" key={indicador.titulo}>
                        <span className="dashboard-stat-icon">{indicador.icono}</span>
                        <strong>{cargando ? "--" : indicador.valor}</strong>
                        <p>{indicador.titulo}</p>
                    </article>
                ))}
            </section>

            <section className="dashboard-panels">
                <article className="dashboard-panel">
                    <h2>Actividad del canal</h2>
                    <span className="dashboard-panel-icon">📊</span>
                    <p>Gráfico de reproducciones por día o semana.</p>
                    <div className="dashboard-empty-chart">
                        La actividad estará disponible cuando se registre el historial de reproducciones.
                    </div>
                </article>

                <article className="dashboard-panel">
                    <h2>Estado del catálogo</h2>
                    <span className="dashboard-panel-icon">🕓</span>
                    <p>Distribución de películas, series y episodios.</p>
                    {cargando ? (
                        <div className="dashboard-empty-chart">Cargando catálogo...</div>
                    ) : (
                        <div className="dashboard-catalog">
                            <div className="dashboard-catalog-row">
                                <span>Películas</span>
                                <strong>{estadisticas.total_peliculas}</strong>
                                <div className="dashboard-bar">
                                    <span style={{ width: `${porcentaje(estadisticas.total_peliculas)}%` }} />
                                </div>
                            </div>
                            <div className="dashboard-catalog-row">
                                <span>Series</span>
                                <strong>{estadisticas.total_series}</strong>
                                <div className="dashboard-bar">
                                    <span style={{ width: `${porcentaje(estadisticas.total_series)}%` }} />
                                </div>
                            </div>
                            <div className="dashboard-catalog-row">
                                <span>Episodios</span>
                                <strong>{estadisticas.total_episodios}</strong>
                                <div className="dashboard-bar">
                                    <span style={{ width: `${porcentaje(estadisticas.total_episodios)}%` }} />
                                </div>
                            </div>
                        </div>
                    )}
                </article>
            </section>
        </main>
    );
}

export default AdminDashboard;
