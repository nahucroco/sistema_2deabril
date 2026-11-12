import { useState } from "react";
import { api } from "../api";

export default function TextStep({ state, setState }) {
  const [idea, setIdea] = useState("Vairo XR 3.5 rodado 29, usada, impecable, $450.000");
  const [cargando, setCargando] = useState(false);
  const [nota, setNota] = useState("Proponé 2 o 3 líneas y tocá \"Sugerir textos\".");
  const [opciones, setOpciones] = useState([]);
  const [caption, setCaption] = useState("");

  async function pedirSugerencias() {
    if (!idea.trim()) {
      setNota("Escribí primero qué querés publicar.");
      return;
    }
    setCargando(true);
    setNota("Pensando los textos…");
    try {
      const data = await api.sugerirTexto(idea.trim(), state.tipo);
      setOpciones(data.opciones || []);
      setCaption(data.caption || "");
      if (data.precio) setState((s) => ({ ...s, precio: data.precio }));
      setNota("Tocá la opción que más te guste. Después la podés corregir abajo.");
    } catch (err) {
      setNota(err.message || "No salió esta vez. Probá de nuevo.");
    } finally {
      setCargando(false);
    }
  }

  function elegir(o) {
    setState((s) => ({ ...s, titulo: o.titulo, detalle: o.detalle || "" }));
  }

  return (
    <section className="step">
      <div className="num">3</div>
      <div className="body">
        <h2>El texto</h2>
        <div className="ai">
          <div>
            <label htmlFor="idea">Contalo como se lo dirías a un cliente</label>
            <textarea id="idea" value={idea} onChange={(e) => setIdea(e.target.value)} />
          </div>
          <div className="actions">
            <button type="button" className="btn ghost" disabled={cargando} onClick={pedirSugerencias}>
              Sugerir textos
            </button>
            <p className="hint">{nota}</p>
          </div>
          {opciones.length > 0 && (
            <div className="opts">
              {opciones.map((o, i) => (
                <button type="button" className="opt" key={i} onClick={() => elegir(o)}>
                  <b>{o.titulo}</b>
                  <small>{o.detalle}</small>
                </button>
              ))}
            </div>
          )}
          {caption && (
            <div className="cap">
              <span className="lbl">Texto para acompañar en el feed</span>
              <p>{caption}</p>
              <button
                type="button"
                className="btn ghost small"
                onClick={() => navigator.clipboard?.writeText(caption).catch(() => {})}
              >
                Copiar
              </button>
            </div>
          )}
        </div>
        <div>
          <label htmlFor="titulo">Título</label>
          <input
            id="titulo"
            type="text"
            maxLength={60}
            value={state.titulo}
            onChange={(e) => setState((s) => ({ ...s, titulo: e.target.value }))}
          />
        </div>
        <div className="row">
          <div>
            <label htmlFor="precio">Precio</label>
            <input
              id="precio"
              type="text"
              inputMode="numeric"
              placeholder="Sin precio"
              value={state.precio}
              onChange={(e) => setState((s) => ({ ...s, precio: e.target.value }))}
            />
          </div>
          <div>
            <label htmlFor="detalle">Detalle</label>
            <input
              id="detalle"
              type="text"
              maxLength={90}
              value={state.detalle}
              onChange={(e) => setState((s) => ({ ...s, detalle: e.target.value }))}
            />
          </div>
        </div>
        <div className="row">
          <div>
            <label htmlFor="whatsapp">WhatsApp del local</label>
            <input
              id="whatsapp"
              type="text"
              inputMode="tel"
              maxLength={24}
              value={state.whatsapp}
              onChange={(e) => setState((s) => ({ ...s, whatsapp: e.target.value }))}
            />
          </div>
          <p className="hint" style={{ alignSelf: "end" }}>
            El logo de 2 de Abril va siempre arriba a la izquierda.
          </p>
        </div>
      </div>
    </section>
  );
}
