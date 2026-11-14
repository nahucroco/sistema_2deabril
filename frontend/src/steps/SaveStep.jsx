import { useState } from "react";
import { api } from "../api";
import CamposRepeticion from "../components/CamposRepeticion";
import { REPETICION_INICIAL, datosRepeticion, textoFecha, textoFrecuencia } from "../repeticion";

export default function SaveStep({ state, canvasRef, cuentas, onGuardado }) {
  const [guardando, setGuardando] = useState(false);
  const [publicando, setPublicando] = useState(false);
  const [mensaje, setMensaje] = useState("");
  const [repetir, setRepetir] = useState(false);
  const [repeticion, setRepeticion] = useState(REPETICION_INICIAL);
  const cuenta = cuentas?.[0];

  function descargarPNG() {
    const canvas = canvasRef.current;
    if (!canvas) return;
    setGuardando(true);
    canvas.toBlob((blob) => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `historia-${state.tipo}.png`;
      a.click();
      URL.revokeObjectURL(url);
      setGuardando(false);
    }, "image/png");
  }

  // Sube la imagen armada y la deja guardada en el sistema (sin publicar).
  async function guardarHistoria() {
    const canvas = canvasRef.current;
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
    const form = new FormData();
    form.append("cuenta", cuenta.id);
    form.append("tipo", state.tipo);
    form.append("titulo", state.titulo);
    form.append("detalle", state.detalle);
    form.append("precio", state.precio);
    form.append("imagen", blob, `historia-${state.tipo}.png`);
    return api.crearHistoria(form);
  }

  async function publicarEnInstagram() {
    if (!canvasRef.current || !cuenta) return;
    setPublicando(true);
    setMensaje("");
    try {
      const post = await guardarHistoria();
      if (repetir) {
        const rep = await api.crearRepeticion({ historia: post.id, ...datosRepeticion(repeticion) });
        setMensaje(
          `Listo: se va a publicar sola, ${textoFrecuencia(rep.cada_dias).toLowerCase()}. La primera vez: ${textoFecha(rep.proxima)}.`
        );
      } else {
        await api.publicarAhora(post.id);
        setMensaje("Enviada a publicar. En un momento aparece en la historia de Instagram.");
      }
      onGuardado?.();
    } catch (err) {
      setMensaje(err.message || "No se pudo guardar. Probá de nuevo en un momento.");
    } finally {
      setPublicando(false);
    }
  }

  return (
    <section className="step">
      <div className="num">4</div>
      <div className="body">
        <h2>Guardarla</h2>
        {cuenta && (
          <label className="check">
            <input type="checkbox" checked={repetir} onChange={(e) => setRepetir(e.target.checked)} />
            Que se publique sola cada tanto
          </label>
        )}
        {cuenta && repetir && (
          <>
            <CamposRepeticion idBase="nueva-rep" valor={repeticion} onChange={setRepeticion} />
            <p className="hint">
              Las historias duran 24 horas: con "Todos los días" queda siempre visible. Se publica dentro de
              los 5 minutos siguientes a la hora elegida.
            </p>
          </>
        )}
        <div className="actions">
          <button type="button" className="btn" disabled={guardando} onClick={descargarPNG}>
            Guardar imagen
          </button>
          {cuenta && (
            <button
              type="button"
              className="btn ghost"
              disabled={publicando || (repetir && !repeticion.hora)}
              onClick={publicarEnInstagram}
            >
              {repetir ? "Programar repetición" : "Publicar en Instagram ahora"}
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
