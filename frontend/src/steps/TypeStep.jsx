import { COLORS, TEMPLATES } from "../brand";

export default function TypeStep({ state, setState }) {
  return (
    <section className="step">
      <div className="num">2</div>
      <div className="body">
        <h2>Qué vas a publicar</h2>
        <div className="chips" role="radiogroup" aria-label="Tipo de historia">
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
