import { NavLink, Outlet } from "react-router-dom";
import "../css/MainLayout.css";

function MainLayout() {
  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-icon">▶</div>
          <div>
            <h1>Play Channel</h1>
            <span>Tu canal personal</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <NavLink to="/" end className="nav-link">
            <span>🏠</span>
            Inicio
          </NavLink>

          <NavLink to="/contenido" className="nav-link">
            <span>🎞️</span>
            Mi Contenido
          </NavLink>

          <NavLink to="/catalogo" className="nav-link">
            <span>🗃️</span>
            Catálogo
          </NavLink>

          <NavLink to="/configuracion" className="nav-link">
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

export default MainLayout;