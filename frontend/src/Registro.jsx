import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import CamposRepeticion from "./components/CamposRepeticion";
import {
  REPETICION_INICIAL,
  datosRepeticion,
  textoDia,
  textoFecha,
  textoFrecuencia,
  textoHora,
} from "./repeticion";

const ESTADOS = {
  programada: "Programada",
  publicando: "Publicando…",
  publicada: "Publicada",
  error: "Error",
};

// Registro de historias: lo que se ve hoy en Instagram, las que se repiten
// solas y las últimas publicaciones (con sus errores).
export default function Registro({ version }) {
  const [registro, setRegistro] = useState(null);
  const [repeticiones, setRepeticiones] = useState([]);
  const [error, setError] = useState("");

  const cargar = useCallback(() => {
    Promise.all([api.registro(), api.repeticiones()])
      .then(([r, reps]) => {
        setRegistro(r);
        setRepeticiones(reps);
        setError("");
      })
      .catch((err) => setError(err.message || "No se pudo cargar el registro."));
  }, []);

  useEffect(() => {
    cargar();
    // Se refresca solo, para ver pasar las publicaciones de "Publicando…" a "Publicada".
    const id = setInterval(cargar, 60000);
    return () => clearInterval(id);
  }, [cargar, version]);

  async function accion(promesa) {
    try {
      await promesa;
      cargar();
    } catch (err) {
      setError(err.message || "No se pudo hacer el cambio.");
    }
  }

  if (!registro) {
    return error ? <p className="msg">{error}</p> : null;
  }

  return (
    <section className="registro" aria-labelledby="registro-titulo">
      <div className="registro-cabecera">
        <h2 id="registro-titulo">Registro de historias</h2>
        <button type="button" className="btn ghost small" onClick={cargar}>
          Actualizar
        </button>
      </div>
      {error && <p className="msg">{error}</p>}

      <h3>En Instagram ahora</h3>
      {registro.en_instagram.length ? (
        <ul className="tiras">
          {registro.en_instagram.map((p) => (
            <li key={p.id} className="tira">
              <img src={p.imagen} alt="" />
              <span className="tira-titulo">{p.titulo || "Sin título"}</span>
              <span className="tira-dato">Se ve hasta {textoFecha(p.vence_en)}</span>
              {p.repeticion && <span className="marca-auto">Automática</span>}
            </li>
          ))}
        </ul>
      ) : (
        <p className="hint">No hay historias visibles en este momento.</p>
      )}

      <h3>Se publican solas</h3>
      {repeticiones.length ? (
        <ul className="repeticiones">
          {repeticiones.map((r) => (
            <FilaRepeticion
              key={r.id}
              rep={r}
              onCambiar={(datos) => accion(api.cambiarRepeticion(r.id, datos))}
              onBorrar={() => {
                if (window.confirm(`¿Dejar de publicar "${r.nombre || "esta historia"}"? No se borra lo ya publicado.`)) {
                  accion(api.borrarRepeticion(r.id));
                }
              }}
            />
          ))}
        </ul>
      ) : (
        <p className="hint">
          Ninguna todavía. Al guardar una historia, marcá "Que se publique sola cada tanto", o usá "Repetir" en
          una de las últimas publicaciones.
        </p>
      )}

      <h3>Últimas publicaciones</h3>
      {registro.recientes.length ? (
        <ul className="recientes">
          {registro.recientes.map((p) => (
            <FilaReciente
              key={p.id}
              post={p}
              onReintentar={() => accion(api.publicarAhora(p.id))}
              onRepetir={(datos) => accion(api.crearRepeticion({ historia: p.id, ...datosRepeticion(datos) }))}
            />
          ))}
        </ul>
      ) : (
        <p className="hint">Todavía no se publicó ninguna historia desde el Taller.</p>
      )}
    </section>
  );
}

function FilaRepeticion({ rep, onCambiar, onBorrar }) {
  const [editando, setEditando] = useState(false);
  const [valor, setValor] = useState({
    cada_dias: rep.cada_dias,
    hora: textoHora(rep.hora),
    hasta: rep.hasta || "",
  });

  return (
    <li className={`repeticion${rep.activa ? "" : " pausada"}`}>
      <img src={rep.imagen} alt="" />
      <div className="repeticion-datos">
        <span className="tira-titulo">{rep.nombre || "Sin título"}</span>
        <span className="tira-dato">
          {textoFrecuencia(rep.cada_dias)} a las {textoHora(rep.hora)}
          {rep.hasta && `, hasta el ${textoDia(rep.hasta)}`}
        </span>
        <span className="tira-dato">
          {rep.activa ? `Próxima: ${textoFecha(rep.proxima)}` : "En pausa"}
          {rep.ultima && ` · Última: ${textoFecha(rep.ultima)}`}
        </span>
        {editando && (
          <form
            className="repeticion-form"
            onSubmit={(e) => {
              e.preventDefault();
              onCambiar(datosRepeticion(valor));
              setEditando(false);
            }}
          >
            <CamposRepeticion idBase={`rep-${rep.id}`} valor={valor} onChange={setValor} />
            <div className="actions">
              <button type="submit" className="btn small">
                Guardar cambios
              </button>
              <button type="button" className="btn ghost small" onClick={() => setEditando(false)}>
                Cancelar
              </button>
            </div>
          </form>
        )}
        {!editando && (
          <div className="actions">
            <button type="button" className="btn ghost small" onClick={() => onCambiar({ activa: !rep.activa })}>
              {rep.activa ? "Pausar" : "Reanudar"}
            </button>
            <button type="button" className="btn ghost small" onClick={() => setEditando(true)}>
              Cambiar horario
            </button>
            <button type="button" className="btn ghost small peligro" onClick={onBorrar}>
              Quitar
            </button>
          </div>
        )}
      </div>
    </li>
  );
}

function FilaReciente({ post, onReintentar, onRepetir }) {
  const [repitiendo, setRepitiendo] = useState(false);
  const [valor, setValor] = useState(REPETICION_INICIAL);
  const cuando = post.publicado_en || post.programada_para || post.actualizado;

  return (
    <li className="reciente">
      <img src={post.imagen} alt="" />
      <div className="repeticion-datos">
        <span className="tira-titulo">{post.titulo || "Sin título"}</span>
        <span className="tira-dato">
          <span className={`estado estado-${post.estado}`}>{ESTADOS[post.estado] || post.estado}</span>{" "}
          {textoFecha(cuando)}
          {post.repeticion && " · automática"}
        </span>
        {post.estado === "error" && post.error_mensaje && <span className="msg">{post.error_mensaje}</span>}
        {repitiendo ? (
          <form
            className="repeticion-form"
            onSubmit={(e) => {
              e.preventDefault();
              onRepetir(valor);
              setRepitiendo(false);
            }}
          >
            <CamposRepeticion idBase={`rec-${post.id}`} valor={valor} onChange={setValor} />
            <div className="actions">
              <button type="submit" className="btn small">
                Programar repetición
              </button>
              <button type="button" className="btn ghost small" onClick={() => setRepitiendo(false)}>
                Cancelar
              </button>
            </div>
          </form>
        ) : (
          <div className="actions">
            {post.estado === "error" && (
              <button type="button" className="btn ghost small" onClick={onReintentar}>
                Reintentar
              </button>
            )}
            <button type="button" className="btn ghost small" onClick={() => setRepitiendo(true)}>
              Repetir
            </button>
          </div>
        )}
      </div>
    </li>
  );
}
