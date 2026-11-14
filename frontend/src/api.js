// Cliente minimo contra la API del backend. En desarrollo, Vite proxea
// /api a http://localhost:8000 (ver vite.config.js); en produccion hay
// que servir el front detras del mismo dominio o configurar la URL base.

function getCookie(name) {
  const match = document.cookie.match(new RegExp(`(^| )${name}=([^;]+)`));
  return match ? decodeURIComponent(match[2]) : null;
}

async function request(path, options = {}) {
  const res = await fetch(`/api${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken") || "",
      ...(options.headers || {}),
    },
    ...options,
  });
  if (!res.ok) {
    let detail = `Error ${res.status}`;
    try {
      const data = await res.json();
      detail = data.detail || JSON.stringify(data);
    } catch {
      // sin cuerpo JSON, nos quedamos con el status
    }
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  sesion: () => request("/sesion/"),
  iniciarSesion: (usuario, clave) =>
    request("/sesion/iniciar/", { method: "POST", body: JSON.stringify({ usuario, clave }) }),
  cerrarSesion: () => request("/sesion/cerrar/", { method: "POST" }),
  cuentas: () => request("/cuentas/"),
  historias: () => request("/historias/"),
  crearHistoria: (formData) =>
    fetch("/api/historias/", {
      method: "POST",
      credentials: "include",
      headers: { "X-CSRFToken": getCookie("csrftoken") || "" },
      body: formData,
    }).then(async (res) => {
      if (!res.ok) throw new Error(`Error ${res.status} al crear la historia`);
      return res.json();
    }),
  publicarAhora: (id) => request(`/historias/${id}/publicar_ahora/`, { method: "POST" }),
  registro: () => request("/historias/registro/"),
  cancelarProgramada: (id) => request(`/historias/${id}/cancelar/`, { method: "POST" }),
  repeticiones: () => request("/repeticiones/"),
  crearRepeticion: (datos) => request("/repeticiones/", { method: "POST", body: JSON.stringify(datos) }),
  cambiarRepeticion: (id, datos) =>
    request(`/repeticiones/${id}/`, { method: "PATCH", body: JSON.stringify(datos) }),
  borrarRepeticion: (id) => request(`/repeticiones/${id}/`, { method: "DELETE" }),
  sugerirTexto: (idea, tipo) =>
    request("/historias/sugerir_texto/", { method: "POST", body: JSON.stringify({ idea, tipo }) }),
};
