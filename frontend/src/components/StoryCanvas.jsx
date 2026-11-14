import { useEffect, useRef } from "react";
import { FORMATOS } from "../brand";
import { drawStory } from "../drawStory";
import { makeSampleImage } from "../sampleImage";

const sample = typeof document !== "undefined" ? makeSampleImage() : null;

export default function StoryCanvas({ state, onPan, showSafeZones, canvasRef: externalRef }) {
  const internalRef = useRef(null);
  const canvasRef = externalRef || internalRef;
  const logoRef = useRef(null);
  const dragRef = useRef(null);
  const esFeed = state.formato === "feed";
  const { ancho, alto } = FORMATOS[esFeed ? "feed" : "historia"];

  useEffect(() => {
    const img = new Image();
    img.onload = () => {
      logoRef.current = img;
      redraw();
    };
    img.src = `${import.meta.env.BASE_URL}logo.png`;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function redraw() {
    if (canvasRef.current) drawStory(canvasRef.current, state, logoRef.current, sample);
  }

  useEffect(redraw);

  function handlePointerDown(e) {
    dragRef.current = { x: e.clientX, y: e.clientY };
    e.target.setPointerCapture(e.pointerId);
  }
  function handlePointerMove(e) {
    if (!dragRef.current || !onPan) return;
    const k = (canvasRef.current?.clientWidth || 200) * 0.6;
    const dx = (e.clientX - dragRef.current.x) / k;
    const dy = (e.clientY - dragRef.current.y) / k;
    onPan(dx, dy);
    dragRef.current = { x: e.clientX, y: e.clientY };
  }
  function handlePointerUp() {
    dragRef.current = null;
  }

  return (
    <div className={esFeed ? "phone feed" : "phone"}>
      <canvas
        ref={canvasRef}
        width={ancho}
        height={alto}
        aria-label={esFeed ? "Vista previa de la publicación del feed" : "Vista previa de la historia"}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerUp}
      />
      {showSafeZones && !esFeed && (
        <>
          <div className="zone t">Acá Instagram pone el nombre de la cuenta</div>
          <div className="zone b">Acá va la barra para responder</div>
        </>
      )}
    </div>
  );
}
