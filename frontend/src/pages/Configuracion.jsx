import "../css/Configuracion.css";

function Configuracion() {
  return (
    <section className="configuracion-page">
      <header className="page-header">
        <div>
          <span className="section-label">PERSONALIZA TU EXPERIENCIA</span>
          <h1>Configuración</h1>
          <p>Administra las preferencias de Play Channel.</p>
        </div>
      </header>

      <section className="settings-card">
        <h2>Preferencias del canal</h2>

        <div className="setting-row">
          <div>
            <h3>Modo de reproducción</h3>
            <p>El canal seleccionará el contenido automáticamente.</p>
          </div>
          <span className="setting-value">Automático</span>
        </div>

        <div className="setting-row">
          <div>
            <h3>Almacenamiento</h3>
            <p>Los archivos multimedia se guardarán en tu equipo.</p>
          </div>
          <span className="setting-value">Local</span>
        </div>

        <div className="setting-row">
          <div>
            <h3>Base de datos</h3>
            <p>Conexión con la base de datos de Play Channel.</p>
          </div>
          <span className="setting-value">MySQL</span>
        </div>
      </section>
    </section>
  );
}

export default Configuracion;