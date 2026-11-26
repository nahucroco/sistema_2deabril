import { useRef, useState } from "react";
import { FOTO_VACIA, TEMPLATES, fotosDe } from "../brand";

function abrir(file) {
  return new Promise((resolve, reject) => {
    if (!file || !file.type.startsWith("image/")) {
      reject(new Error("Ese archivo no es una imagen. Probá con un JPG o PNG."));
      return;
    }
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error("No se pudo abrir esa foto. Probá con un JPG o PNG."));
    img.src = URL.createObjectURL(file);
  });
}

export default function PhotoStep({ state, setState }) {
  const fileRef = useRef(null);
  // A partir de que lugar se cargan las fotos que se eligen en el selector.
  const destinoRef = useRef(0);
  const [nota, setNota] = useState("Ahora se ve una bici dibujada de ejemplo.");
  const [over, setOver] = useState(false);
  const n = fotosDe(state.tipo);
  const soloFoto = TEMPLATES[state.tipo]?.mode === "raw";
  const activa = Math.min(state.fotoActiva, n - 1);
  const cargadas = state.fotos.slice(0, n).filter((f) => f.img).length;

  // Pone las fotos elegidas en los lugares libres, empezando por "desde".
  async function cargar(files, desde) {
    const lista = Array.from(files || []).slice(0, n);
    if (!lista.length) return;
    try {
      const imgs = await Promise.all(lista.map(abrir));
      setState((s) => {
        const fotos = [...s.fotos];
        // Con una sola foto elegida se reemplaza el lugar indicado; con varias, se llenan en orden.
        let lugar = desde;
        for (const img of imgs) {
          fotos[lugar] = { ...FOTO_VACIA, img };
          lugar = (lugar + 1) % n;
        }
        return { ...s, fotos, fotoActiva: desde };
      });
      setNota(imgs.length === 1 ? `Foto cargada: ${lista[0].name}` : `${imgs.length} fotos cargadas.`);
    } catch (err) {
      setNota(err.message);
    }
  }

  function elegir(desde) {
    destinoRef.current = desde;
    fileRef.current?.click();
  }

  function primerLibre() {
    const i = state.fotos.slice(0, n).findIndex((f) => !f.img);
    return i === -1 ? activa : i;
  }

  function cambiarZoom(valor) {
    setState((s) => ({
      ...s,
      fotos: s.fotos.map((f, i) => (i === activa ? { ...f, zoom: valor } : f)),
    }));
  }

  return (
    <section className="step">
      <div className="num">2</div>
      <div className="body">
        <h2>{n > 1 ? "Las fotos" : "La foto"}</h2>
        <div
          className={`drop${over ? " over" : ""}`}
          onDragOver={(e) => {
            e.preventDefault();
            setOver(true);
          }}
          onDragLeave={() => setOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setOver(false);
            cargar(e.dataTransfer.files, n > 1 ? primerLibre() : 0);
          }}
        >
          <button type="button" className="btn" onClick={() => elegir(n > 1 ? primerLibre() : 0)}>
            {n > 1 ? "Elegir fotos" : "Elegir foto"}
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            multiple={n > 1}
            hidden
            onChange={(e) => {
              cargar(e.target.files, destinoRef.current);
              e.target.value = ""; // permite volver a elegir el mismo archivo
            }}
          />
          <p className="hint">
            o {n > 1 ? "arrastralas" : "arrastrala"} acá. {nota}
          </p>
        </div>

        {n > 1 && (
          <>
            <p className="hint">
              Esta plantilla lleva {n} fotos ({cargadas} de {n} elegidas). Podés elegirlas todas juntas.
            </p>
            <div className="lugares" role="group" aria-label="Fotos de la plantilla">
              {state.fotos.slice(0, n).map((f, i) => (
                <button
                  type="button"
                  key={i}
                  className={`lugar${i === activa ? " activo" : ""}`}
                  aria-pressed={i === activa}
                  aria-label={`Foto ${i + 1}${f.img ? "" : " (sin elegir)"}`}
                  onClick={() => setState((s) => ({ ...s, fotoActiva: i }))}
                >
                  {f.img ? <img src={f.img.src} alt="" /> : <span>Foto {i + 1}</span>}
                </button>
              ))}
            </div>
            <div className="actions">
              <button type="button" className="btn ghost small" onClick={() => elegir(activa)}>
                Cambiar la foto {activa + 1}
              </button>
            </div>
          </>
        )}

        {soloFoto && (
          <div>
            <span className="lbl">Cómo entra la foto</span>
            <div className="chips" role="radiogroup" aria-label="Cómo entra la foto">
              {[
                { valor: "llenar", texto: "Llenar la pantalla" },
                { valor: "entera", texto: "Foto entera, con fondo" },
              ].map((o) => (
                <label className="chip" key={o.valor}>
                  <input
                    type="radio"
                    name="ajuste"
                    checked={state.ajuste === o.valor}
                    onChange={() => setState((s) => ({ ...s, ajuste: o.valor }))}
                  />
                  <span>{o.texto}</span>
                </label>
              ))}
            </div>
            <p className="hint">
              "Llenar la pantalla" recorta lo que sobra; "Foto entera" la muestra completa, sin cortar, con la
              misma foto desenfocada de fondo.
            </p>
          </div>
        )}

        <div className="zoom">
          <label htmlFor="zoom">{n > 1 ? `Acercar la foto ${activa + 1}` : "Acercar"}</label>
          <input
            id="zoom"
            type="range"
            min={soloFoto && state.ajuste === "entera" ? "0.5" : "1"}
            max="3"
            step="0.01"
            value={state.fotos[activa].zoom}
            onChange={(e) => cambiarZoom(Number(e.target.value))}
          />
        </div>
        <p className="hint">
          {n > 1
            ? "Para acomodar cada foto, arrastrala sobre la vista previa."
            : "Para acomodarla, arrastrá la foto sobre la vista previa."}
        </p>
      </div>
    </section>
  );
}
