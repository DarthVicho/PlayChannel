import { useState } from "react";
import "../css/AdvertenciaDerechos.css"

function AdvertenciaDerechos() {
    const [visible, setVisible] = useState(true);

    if (!visible){
        return null;
    }
    return(
        <>
            <div className="advertencia-overlay">
                <section className="advertencia-modal" role="dialog" aria-modal="true" aria-labelledby="advertencia-titulo">
                    <div className="advertencia-icono">
                        <span aria-hidden="true">!</span>
                    </div>
                    <h2 id="advertencia-titulo">
                        Aviso sobre derechos de autor
                    </h2>
                    <p>
                        PlayChannel no se hace responsable del contenido incorporado por los usuarios. Cada usuario es reponsable de respetar los derechos de autor y utilizar contenido obtenido legalmente.
                    </p>
                    <p className="advertencia-nota">
                        Este aviso es informativo y no sustituye las autorizaciones que correspondan.
                    </p>
                    <button className="advertencia-boton" onClick={() => setVisible(false)} autoFocus>
                        Aceptar
                    </button>
                </section>
            </div>
        </>
    );
}
export default AdvertenciaDerechos
