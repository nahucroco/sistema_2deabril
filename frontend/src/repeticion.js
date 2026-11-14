// Opciones y textos de las historias que se repiten solas.

export const FRECUENCIAS = [
  { dias: 1, texto: "Todos los días" },
  { dias: 2, texto: "Día por medio" },
  { dias: 3, texto: "Cada 3 días" },
  { dias: 7, texto: "Una vez por semana" },
  { dias: 14, texto: "Cada 2 semanas" },
];

export const REPETICION_INICIAL = { cada_dias: 1, hora: "10:00", hasta: "" };

export function textoFrecuencia(dias) {
  return FRECUENCIAS.find((f) => f.dias === dias)?.texto || `Cada ${dias} días`;
}

// "10:00:00" -> "10:00"
export function textoHora(hora) {
  return (hora || "").slice(0, 5);
}

export function textoFecha(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleString("es-AR", {
    weekday: "short",
    day: "numeric",
    month: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// "2026-12-24" -> "24/12/2026", sin correrse de día por la zona horaria.
export function textoDia(fecha) {
  if (!fecha) return "";
  const [a, m, d] = fecha.split("-");
  return `${d}/${m}/${a}`;
}

// Lo que se manda a la API: "hasta" vacío es sin fin.
export function datosRepeticion(r) {
  return { cada_dias: Number(r.cada_dias), hora: r.hora, hasta: r.hasta || null };
}
