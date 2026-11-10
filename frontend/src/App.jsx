import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Admin from "./pages/Admin";
import MainLayout from "./layouts/MainLayout";
import AdminLayout from "./layouts/AdminLayout";
import Inicio from "./pages/Index"
import Contenido from "./pages/Contenido";
import Configuracion from "./pages/Configuracion";
import Catalogo from "./pages/Catalogo";
import AdminPeliculas from "./components/admin/AdminPeliculas";
import AdminSeries from "./components/admin/AdminSeries";
import AdminCatalogo from "./components/admin/AdminCatalogo";
import AdminFuncionalidades from "./components/admin/AdminFuncionalidades";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AdminLayout />}>
          <Route path="admin" element={<Admin />}/>
          <Route path="admin/peliculas" element={<AdminPeliculas />}/>
          <Route path="admin/series" element={<AdminSeries />}/>
          <Route path="admin/catalogo" element={<AdminCatalogo />}/>
          <Route path="admin/funcionalidades" element={<AdminFuncionalidades />}/>
        </Route>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Inicio />} />
          <Route path="contenido" element={<Contenido />} />
          <Route path="catalogo" element={<Catalogo />} />
          <Route path="configuracion" element={<Configuracion />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;