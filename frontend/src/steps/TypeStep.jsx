import { COLORS, FORMATOS, TEMPLATES } from "../brand";

export default function TypeStep({ state, setState }) {
  const esFeed = state.formato === "feed";
  // Las plantillas de varias fotos y "Solo la foto" son solo para historias.
  const plantillas = Object.entries(TEMPLATES).filter(([, t]) => !(esFeed && t.soloHistoria));
  const sinColor = TEMPLATES[state.tipo]?.mode === "raw";

  function elegirFormato(formato) {
    setState((s) => {
      const tipo = formato === "feed" && TEMPLATES[s.tipo]?.soloHistoria ? "usada" : s.tipo;
      return { ...s, formato, tipo };
    });
  }

  return (
    <section className="step">
      <div className="num">1</div>
      <div className="body">
        <h2>Qué vas a publicar</h2>
        <div>
          <span className="lbl">Dónde va</span>
          <div className="chips" role="radiogroup" aria-label="Dónde va">
            {Object.entries(FORMATOS).map(([key, f]) => (
              <label className="chip" key={key}>
                <input
                  type="radio"
                  name="formato"
                  checked={state.formato === key}
                  onChange={() => elegirFormato(key)}
                />
                <span>
                  {f.nombre} <small className="chip-nota">{f.proporcion}</small>
                </span>
              </label>
            ))}
          </div>
        </div>
        <div>
          <span className="lbl">Plantilla</span>
          <div className="chips" role="radiogroup" aria-label="Plantilla">
            {plantillas.map(([key, t]) => (
              <label className="chip" key={key}>
                <input
                  type="radio"
                  name="tipo"
                  checked={state.tipo === key}
                  onChange={() => setState((s) => ({ ...s, tipo: key, fotoActiva: 0 }))}
                />
                <span>
                  {t.name}
                  {t.fotos > 1 && <small className="chip-nota"> {t.fotos} fotos</small>}
                </span>
              </label>
            ))}
          </div>
          {!esFeed && <p className="hint">"Solo la foto" sube la foto tal cual, sin marco ni texto.</p>}
        </div>
        {!sinColor && (
          <div>
            <span className="lbl">Color principal</span>
            <div className="sws" role="radiogroup" aria-label="Color principal">
              {Object.entries(COLORS).map(([key, c]) => (
                <label className="sw" key={key}>
                  <input
                    type="radio"
                    name="color"
                    checked={state.color === key}
                    onChange={() => setState((s) => ({ ...s, color: key }))}
                  />
                  <span style={{ background: c.accent }} title={c.name} aria-label={c.name} />
                </label>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
