import { useState } from "react";
import AdminPeliculas from "../components/admin/AdminPeliculas";
import AdminSeries from "../components/admin/AdminSeries";
import AdminCatalogo from "../components/admin/AdminCatalogo";
import AdminFuncionalidades from "../components/admin/AdminFuncionalidades";
import "../css/Admin.css";

function Admin() {
    const [vista, setVista] = useState("inicio");
    function volverInicio() {
        setVista("inicio");
    }

    return (
        <div className="admin-page">
            <header className="admin-header">
                <div>
                    <span className="admin-subtitle">PLAYCHANNEL / GESTIÓN</span>
                    <h1>Administración</h1>
                    <p>Administra el contenido y las funcionalidades de tu canal personal.</p>
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
                            <article className="admin-card" onClick={() => setVista("peliculas")}>
                                <div className="admin-card-icon">🎬</div>
                                <h3>Películas</h3>
                                <p>Agrega nuevas películas y modifica sus datos dentro del catálogo.</p>
                                <span className="admin-card-status">Gestión de películas →</span>
                            </article>

                            <article className="admin-card" onClick={() => setVista("series")}>
                                <div className="admin-card-icon">📺</div>
                                <h3>Series</h3>
                                <p>Registra series, administra temporadas y agrega sus episodios.</p>
                                <span className="admin-card-status">Gestión de series</span>
                            </article>

                            <article className="admin-card" onClick={() => setVista("catalogo")}>
                                <div className="admin-card-icon">▤</div>
                                <h3>Catálogo preestablecido</h3>
                                <p>Consulta y administra el contenido incorporado al catálogo de PlayChannel.</p>
                                <span className="admin-card-status">Gestión del catálogo</span>
                            </article>
                        </div>
                    </section>

                    <section className="admin-section">
                        <h2>Configuración del sistema</h2>
                        <div className="admin-grid">
                            <article className="admin-card" onClick={() => setVista("funcionalidades")}>
                                <div className="admin-card-icon">⚙</div>
                                <h3>Funcionalidades</h3>
                                <p>Gestiona las opciones y el comportamiento general de PlayChannel.</p>
                                <span className="admin-card-status">Configuración del sistema</span>
                            </article>
                        </div>
                    </section>
                </>
            )}

            {vista === "peliculas" && <AdminPeliculas volverInicio={volverInicio} />}
            {vista === "series" && (<AdminSeries />)}
            {vista === "catalogo" && <AdminCatalogo volverInicio={volverInicio} />}
            {vista === "funcionalidades" && <AdminFuncionalidades volverInicio={volverInicio} />}
        </div>
    );
}

export default Admin;
