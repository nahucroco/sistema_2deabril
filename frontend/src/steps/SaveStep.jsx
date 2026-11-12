import { useState } from "react";
import { api } from "../api";

export default function SaveStep({ state, canvasRef, cuentas }) {
  const [guardando, setGuardando] = useState(false);
  const [publicando, setPublicando] = useState(false);
  const [mensaje, setMensaje] = useState("");
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

  async function publicarEnInstagram() {
    const canvas = canvasRef.current;
    if (!canvas || !cuenta) return;
    setPublicando(true);
    setMensaje("");
    try {
      const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
      const form = new FormData();
      form.append("cuenta", cuenta.id);
      form.append("tipo", state.tipo);
      form.append("titulo", state.titulo);
      form.append("detalle", state.detalle);
      form.append("precio", state.precio);
      form.append("imagen", blob, `historia-${state.tipo}.png`);
      const post = await api.crearHistoria(form);
      await api.publicarAhora(post.id);
      setMensaje("Enviada a publicar. En un momento aparece en la historia de Instagram.");
    } catch (err) {
      setMensaje(err.message || "No se pudo publicar. Probá de nuevo en un momento.");
    } finally {
      setPublicando(false);
    }
  }

  return (
    <section className="step">
      <div className="num">4</div>
      <div className="body">
        <h2>Guardarla</h2>
        <div className="actions">
          <button type="button" className="btn" disabled={guardando} onClick={descargarPNG}>
            Guardar imagen
          </button>
          {cuenta && (
            <button type="button" className="btn ghost" disabled={publicando} onClick={publicarEnInstagram}>
              Publicar en Instagram ahora
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
