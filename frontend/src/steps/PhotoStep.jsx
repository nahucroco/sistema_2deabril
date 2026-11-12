import { useRef, useState } from "react";

export default function PhotoStep({ state, setState }) {
  const fileRef = useRef(null);
  const [nota, setNota] = useState("Ahora se ve una bici dibujada de ejemplo.");
  const [over, setOver] = useState(false);

  function cargar(file) {
    if (!file || !file.type.startsWith("image/")) {
      setNota("Ese archivo no es una imagen. Probá con un JPG o PNG.");
      return;
    }
    const img = new Image();
    img.onload = () => {
      setState((s) => ({ ...s, imagen: img, zoom: 1, ox: 0, oy: 0 }));
      setNota(`Foto cargada: ${file.name}`);
    };
    img.onerror = () => setNota("No se pudo abrir esa foto. Probá con un JPG o PNG.");
    img.src = URL.createObjectURL(file);
  }

  return (
    <section className="step">
      <div className="num">1</div>
      <div className="body">
        <h2>La foto</h2>
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
            cargar(e.dataTransfer.files[0]);
          }}
        >
          <button type="button" className="btn" onClick={() => fileRef.current?.click()}>
            Elegir foto
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            hidden
            onChange={(e) => cargar(e.target.files[0])}
          />
          <p className="hint">o arrastrala acá. {nota}</p>
        </div>
        <div className="zoom">
          <label htmlFor="zoom">Acercar</label>
          <input
            id="zoom"
            type="range"
            min="1"
            max="3"
            step="0.01"
            value={state.zoom}
            onChange={(e) => setState((s) => ({ ...s, zoom: Number(e.target.value) }))}
          />
        </div>
        <p className="hint">Para acomodarla, arrastrá la foto sobre la vista previa.</p>
      </div>
    </section>
  );
}
