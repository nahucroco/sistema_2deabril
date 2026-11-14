import { COLORS, FORMATOS, TEMPLATES } from "../brand";

export default function TypeStep({ state, setState }) {
  return (
    <section className="step">
      <div className="num">2</div>
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
                  onChange={() => setState((s) => ({ ...s, formato: key }))}
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
          {Object.entries(TEMPLATES).map(([key, t]) => (
            <label className="chip" key={key}>
              <input
                type="radio"
                name="tipo"
                checked={state.tipo === key}
                onChange={() => setState((s) => ({ ...s, tipo: key }))}
              />
              <span>{t.name}</span>
            </label>
          ))}
        </div>
        </div>
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
      </div>
    </section>
  );
}
