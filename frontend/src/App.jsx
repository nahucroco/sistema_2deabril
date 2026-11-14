import { useEffect, useRef, useState } from "react";
import { api } from "./api";
import StoryCanvas from "./components/StoryCanvas";
import PhotoStep from "./steps/PhotoStep";
import TypeStep from "./steps/TypeStep";
import TextStep from "./steps/TextStep";
import SaveStep from "./steps/SaveStep";
import Login from "./Login";
import Registro from "./Registro";

const INITIAL_STATE = {
  formato: "historia",
  tipo: "usada",
  color: "azul",
  imagen: null,
  zoom: 1,
  ox: 0,
  oy: 0,
  titulo: "Vairo XR 3.5 R29",
  detalle: "Impecable. 21 velocidades y frenos a disco.",
  precio: "450000",
  whatsapp: "",
  caption: "",
};

export default function App() {
  // null mientras se consulta; despues {usuario, requiere_login}
  const [sesion, setSesion] = useState(null);

  useEffect(() => {
    api
      .sesion()
      .then(setSesion)
      .catch(() => setSesion({ usuario: null, requiere_login: true }));
  }, []);

  if (!sesion) return null;
  if (sesion.requiere_login && !sesion.usuario) return <Login onLogin={setSesion} />;
  return <Taller sesion={sesion} onLogout={setSesion} />;
}

function Taller({ sesion, onLogout }) {
  const [state, setState] = useState(() => {
    try {
      const guardado = JSON.parse(localStorage.getItem("taller-2deabril") || "{}");
      return { ...INITIAL_STATE, whatsapp: guardado.whatsapp || "", color: guardado.color || "azul" };
    } catch {
      return INITIAL_STATE;
    }
  });
  const [safeZones, setSafeZones] = useState(false);
  const [cuentas, setCuentas] = useState([]);
  // Sube cada vez que se guarda algo, para que el registro se recargue.
  const [version, setVersion] = useState(0);
  const canvasRef = useRef(null);

  useEffect(() => {
    try {
      localStorage.setItem(
        "taller-2deabril",
        JSON.stringify({ whatsapp: state.whatsapp, color: state.color })
      );
    } catch {
      // localStorage puede fallar (modo privado); no es critico.
    }
  }, [state.whatsapp, state.color]);

  useEffect(() => {
    api
      .cuentas()
      .then(setCuentas)
      .catch(() => setCuentas([])); // sin sesion o sin cuentas cargadas: seguimos sin publicar directo
  }, []);

  function pan(dx, dy) {
    setState((s) => ({
      ...s,
      ox: Math.max(-1, Math.min(1, s.ox + dx)),
      oy: Math.max(-1, Math.min(1, s.oy + dy)),
    }));
  }

  return (
    <div className="wrap">
      <header>
        <img src={`${import.meta.env.BASE_URL}logo.png`} alt="Bicicletería 2 de Abril, repuestos y taller" />
        <div>
          <h1>
            Taller de <span>Publicaciones</span>
          </h1>
          <p>
            Elegí una foto, contá qué es y llevate la historia o el posteo listo para Instagram. La
            foto queda tal cual: solo se le suma el marco, el precio y el contacto.
          </p>
        </div>
        <nav className="panel-links" aria-label="Panel">
          <a href="/admin/catalogo/producto/">Productos de la web</a>
          <a href="/" target="_blank" rel="noopener">Ver la web</a>
          {sesion.usuario && (
            <button type="button" className="logout" onClick={() => api.cerrarSesion().then(onLogout)}>
              Salir
            </button>
          )}
        </nav>
      </header>

      <div className="bench">
        <div className="steps">
          <PhotoStep state={state} setState={setState} />
          <TypeStep state={state} setState={setState} />
          <TextStep state={state} setState={setState} />
          <SaveStep
            state={state}
            canvasRef={canvasRef}
            cuentas={cuentas}
            onGuardado={() => setVersion((v) => v + 1)}
          />
        </div>

        <aside className="side">
          <StoryCanvas state={state} onPan={pan} showSafeZones={safeZones} canvasRef={canvasRef} />
          {state.formato === "feed" ? (
            <p className="tag">1080 × 1350 px, publicación del feed 4:5</p>
          ) : (
            <>
              <label className="check">
                <input type="checkbox" checked={safeZones} onChange={(e) => setSafeZones(e.target.checked)} />
                Mostrar lo que tapa Instagram
              </label>
              <p className="tag">1080 × 1920 px, formato historia 9:16</p>
            </>
          )}
        </aside>
      </div>

      {cuentas.length > 0 && <Registro version={version} />}
    </div>
  );
}
