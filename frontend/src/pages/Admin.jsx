import { useState } from "react";
import AdminDashboard from "../components/admin/AdminDashboard";


function Admin() {
    return (
        <div className="admin-page">
            <header className="admin-header">
                <div>
                    <span className="admin-subtitle">PLAYCHANNEL / GESTIÓN</span>
                    <h1>Administración</h1>
                    <p>Administra el contenido y las funcionalidades de PlayChannel.</p>
                </div>
                <div className="admin-header-icon">⚙</div>
            </header>
            <div className="admin-page">
                <AdminDashboard/>
            </div>
        </div>
    );
}

export default Admin;
