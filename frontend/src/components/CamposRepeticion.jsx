import { FRECUENCIAS } from "../repeticion";

// Cada cuánto, a qué hora y hasta cuándo se publica sola una historia.
export default function CamposRepeticion({ valor, onChange, idBase }) {
  const cambiar = (campo) => (e) => onChange({ ...valor, [campo]: e.target.value });
  return (
    <div className="row">
      <div>
        <label htmlFor={`${idBase}-cada`}>Cada cuánto</label>
        <select id={`${idBase}-cada`} value={valor.cada_dias} onChange={cambiar("cada_dias")}>
          {FRECUENCIAS.map((f) => (
            <option key={f.dias} value={f.dias}>
              {f.texto}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor={`${idBase}-hora`}>A qué hora</label>
        <input id={`${idBase}-hora`} type="time" required value={valor.hora} onChange={cambiar("hora")} />
      </div>
      <div>
        <label htmlFor={`${idBase}-hasta`}>Hasta (opcional)</label>
        <input id={`${idBase}-hasta`} type="date" value={valor.hasta} onChange={cambiar("hasta")} />
      </div>
    </div>
  );
}
