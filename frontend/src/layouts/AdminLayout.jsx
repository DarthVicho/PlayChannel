import { NavLink, Outlet } from "react-router-dom";
import '../css/AdminLayout.css'
import '../css/Admin.css'

function AdminLayout() {
    return (
        <div className="app-layout-admin">
            <aside className="sidebar-admin">
                <div className="sidebar-brand-admin">
                    <div className="brand-icon-admin">▶</div>
                    <div>
                        <h1>Play Channel</h1>
                        <span>Tu canal personal</span>
                    </div>
                </div>

                <nav className="sidebar-nav">
                    <NavLink to="/admin" end className="nav-link">
                        <span>🏠</span>
                        Inicio
                    </NavLink>

                    <NavLink to="/admin/peliculas" className="nav-link">
                        <span>🎬</span>
                        Películas
                    </NavLink>

                    <NavLink to="/admin/series" className="nav-link">
                        <span>📺</span>
                        Series
                    </NavLink>

                    <NavLink to="/admin/catalogo" className="nav-link">
                        <span>🗃️</span>
                        Catálogo
                    </NavLink>

                    <NavLink to="/admin/funcionalidades" className="nav-link">
                        <span>⚙️</span>
                        Configuración
                    </NavLink>
                </nav>

                <div className="sidebar-footer">
                    <span className="status-dot"></span>
                    Sistema local
                </div>
            </aside>

            <main className="main-content">
                <Outlet />
            </main>
        </div>
    );
    }

export default AdminLayout;