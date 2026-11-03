import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Admin from "./pages/Admin";
import MainLayout from "./layouts/MainLayout";
import Inicio from "./pages/Index"
import Contenido from "./pages/Contenido";
import Configuracion from "./pages/Configuracion";
import Catalogo from "./pages/Catalogo";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/admin" element={<Admin />}/>
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