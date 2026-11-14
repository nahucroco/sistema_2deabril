import { useState } from "react";
import { api } from "./api";

export default function Login({ onLogin }) {
  const [usuario, setUsuario] = useState("");
  const [clave, setClave] = useState("");
  const [error, setError] = useState("");
  const [entrando, setEntrando] = useState(false);

  async function entrar(e) {
    e.preventDefault();
    setEntrando(true);
    setError("");
    try {
      onLogin(await api.iniciarSesion(usuario, clave));
    } catch (err) {
      setError(err.message || "No se pudo entrar. Probá de nuevo.");
    } finally {
      setEntrando(false);
    }
  }

  return (
    <div className="wrap login">
      <header>
        <img src={`${import.meta.env.BASE_URL}logo.png`} alt="Bicicletería 2 de Abril, repuestos y taller" />
        <div>
          <h1>
            Taller de <span>Publicaciones</span>
          </h1>
          <p>Entrá con tu usuario para armar y publicar historias.</p>
        </div>
      </header>

      <form className="login-form" onSubmit={entrar}>
        <div>
          <label htmlFor="usuario">Usuario</label>
          <input
            id="usuario"
            type="text"
            autoComplete="username"
            autoCapitalize="none"
            value={usuario}
            onChange={(e) => setUsuario(e.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="clave">Contraseña</label>
          <input
            id="clave"
            type="password"
            autoComplete="current-password"
            value={clave}
            onChange={(e) => setClave(e.target.value)}
            required
          />
        </div>
        {error && <p className="msg">{error}</p>}
        <button type="submit" className="btn" disabled={entrando}>
          {entrando ? "Entrando…" : "Entrar"}
        </button>
      </form>
    </div>
  );
}
