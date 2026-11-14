import { useState } from "react";
import { api } from "../api";
import CamposRepeticion from "../components/CamposRepeticion";
import { REPETICION_INICIAL, datosRepeticion, textoFecha, textoFrecuencia } from "../repeticion";

// "2026-11-14T18:30" (lo que da <input type="datetime-local">) para dentro de una hora.
function enUnaHora() {
  const d = new Date(Date.now() + 60 * 60 * 1000);
  d.setMinutes(0, 0, 0);
  const dos = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${dos(d.getMonth() + 1)}-${dos(d.getDate())}T${dos(d.getHours())}:00`;
}

export default function SaveStep({ state, canvasRef, cuentas, onGuardado }) {
  const [guardando, setGuardando] = useState(false);
  const [publicando, setPublicando] = useState(false);
  const [mensaje, setMensaje] = useState("");
  // "ahora", "programar" o "repetir" (solo historias)
  const [cuando, setCuando] = useState("ahora");
  const [fechaHora, setFechaHora] = useState(enUnaHora);
  const [repeticion, setRepeticion] = useState(REPETICION_INICIAL);
  const cuenta = cuentas?.[0];
  const esFeed = state.formato === "feed";
  const modo = esFeed && cuando === "repetir" ? "ahora" : cuando;
  // Instagram pide JPEG para el feed; la historia sale en PNG como siempre.
  const tipoImagen = esFeed ? "image/jpeg" : "image/png";
  const extension = esFeed ? "jpg" : "png";
  const nombrePieza = esFeed ? "publicación" : "historia";

  function aBlob() {
    return new Promise((resolve) => canvasRef.current.toBlob(resolve, tipoImagen, 0.92));
  }

  async function descargar() {
    if (!canvasRef.current) return;
    setGuardando(true);
    const blob = await aBlob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${esFeed ? "post" : "historia"}-${state.tipo}.${extension}`;
    a.click();
    URL.revokeObjectURL(url);
    setGuardando(false);
  }

  // Sube la imagen armada y la deja guardada en el sistema.
  async function guardarPieza(extra = {}) {
    const form = new FormData();
    form.append("cuenta", cuenta.id);
    form.append("formato", state.formato);
    form.append("tipo", state.tipo);
    form.append("titulo", state.titulo);
    form.append("detalle", state.detalle);
    form.append("precio", state.precio);
    if (esFeed) form.append("caption", state.caption);
    for (const [k, v] of Object.entries(extra)) form.append(k, v);
    form.append("imagen", await aBlob(), `${esFeed ? "post" : "historia"}-${state.tipo}.${extension}`);
    return api.crearHistoria(form);
  }

  async function publicar() {
    if (!canvasRef.current || !cuenta) return;
    setPublicando(true);
    setMensaje("");
    try {
      if (modo === "repetir") {
        const post = await guardarPieza();
        const rep = await api.crearRepeticion({ historia: post.id, ...datosRepeticion(repeticion) });
        setMensaje(
          `Listo: se va a publicar sola, ${textoFrecuencia(rep.cada_dias).toLowerCase()}. La primera vez: ${textoFecha(rep.proxima)}.`
        );
      } else if (modo === "programar") {
        const post = await guardarPieza({ programada_para: new Date(fechaHora).toISOString() });
        setMensaje(`Listo: la ${nombrePieza} sale el ${textoFecha(post.programada_para)}.`);
      } else {
        const post = await guardarPieza();
        await api.publicarAhora(post.id);
        setMensaje(`Enviada a publicar. En un momento aparece en ${esFeed ? "el feed" : "la historia"} de Instagram.`);
      }
      onGuardado?.();
    } catch (err) {
      setMensaje(err.message || "No se pudo guardar. Probá de nuevo en un momento.");
    } finally {
      setPublicando(false);
    }
  }

  const opciones = [
    { valor: "ahora", texto: "Ahora" },
    { valor: "programar", texto: "En una fecha y hora" },
    ...(esFeed ? [] : [{ valor: "repetir", texto: "Que se repita sola" }]),
  ];
  const textoBoton = {
    ahora: "Publicar en Instagram ahora",
    programar: "Programar publicación",
    repetir: "Programar repetición",
  }[modo];
  const faltaDato = (modo === "programar" && !fechaHora) || (modo === "repetir" && !repeticion.hora);

  return (
    <section className="step">
      <div className="num">4</div>
      <div className="body">
        <h2>Guardarla</h2>
        {cuenta && (
          <div>
            <span className="lbl">Cuándo se publica</span>
            <div className="chips" role="radiogroup" aria-label="Cuándo se publica">
              {opciones.map((o) => (
                <label className="chip" key={o.valor}>
                  <input type="radio" name="cuando" checked={modo === o.valor} onChange={() => setCuando(o.valor)} />
                  <span>{o.texto}</span>
                </label>
              ))}
            </div>
          </div>
        )}
        {cuenta && modo === "programar" && (
          <div>
            <label htmlFor="fecha-hora">Día y hora</label>
            <input
              id="fecha-hora"
              type="datetime-local"
              required
              value={fechaHora}
              onChange={(e) => setFechaHora(e.target.value)}
            />
            <p className="hint">Sale dentro de los 5 minutos siguientes a la hora elegida.</p>
          </div>
        )}
        {cuenta && modo === "repetir" && (
          <>
            <CamposRepeticion idBase="nueva-rep" valor={repeticion} onChange={setRepeticion} />
            <p className="hint">
              Las historias duran 24 horas: con "Todos los días" queda siempre visible. Se publica dentro de
              los 5 minutos siguientes a la hora elegida.
            </p>
          </>
        )}
        <div className="actions">
          <button type="button" className="btn" disabled={guardando} onClick={descargar}>
            Guardar imagen
          </button>
          {cuenta && (
            <button type="button" className="btn ghost" disabled={publicando || faltaDato} onClick={publicar}>
              {textoBoton}
            </button>
          )}
        </div>
        {mensaje && <p className="msg">{mensaje}</p>}
        {!cuenta && (
          <div className="next">
            <b>Publicar directo en Instagram</b> todavía no está disponible: falta conectar la cuenta
            profesional del local (ver docs/instagram_setup.md). Mientras tanto, guardá la imagen y
            subila desde el celular o desde Meta Business Suite.
          </div>
        )}
      </div>
    </section>
  );
}
