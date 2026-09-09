let listaReportes = [];

async function cargarHistorial() {
  try {
    const res = await fetch("/api/reportes/");
    listaReportes = await res.json();
    renderizarTabla(listaReportes);
  } catch (err) {
    alert("Error cargando el historial: " + err.message);
  }
}

function renderizarTabla(datos) {
  const tbody = document.getElementById("tabla-cuerpo");
  tbody.innerHTML = "";

  if (datos.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #718096;">No hay reportes registrados aún.</td></tr>`;
    return;
  }

  datos.forEach(r => {
    tbody.innerHTML += `
      <tr>
        <td><strong>#${r.reporte_id}</strong></td>
        <td>${r.paciente_nombre}</td>
        <td>${r.edad || 'N/E'} años</td>
        <td>${r.cama || 'N/E'}</td>
        <td>${r.fecha}</td>
        <td>
          <a class="btn btn-success" style="padding: 0.4rem 0.8rem; font-size: 0.85rem;" href="/api/exportar/word/${r.reporte_id}" target="_blank">📥 Word</a>
          <button class="btn btn-secondary" style="padding: 0.4rem 0.8rem; font-size: 0.85rem; background: #E53E3E;" onclick="eliminarReporte(${r.reporte_id})">🗑 Eliminar</button>
        </td>
      </tr>
    `;
  });
}

function filtrarReportes() {
  const busqueda = document.getElementById("buscador").value.toLowerCase();
  const filtrados = listaReportes.filter(r => r.paciente_nombre.toLowerCase().includes(busqueda));
  renderizarTabla(filtrados);
}

async function eliminarReporte(id) {
  if (!confirm(`¿Estás seguro de eliminar el reporte #${id}?`)) return;
  try {
    await fetch(`/api/reportes/${id}`, { method: "DELETE" });
    cargarHistorial();
  } catch (err) {
    alert("Error eliminando: " + err.message);
  }
}

document.addEventListener("DOMContentLoaded", cargarHistorial);