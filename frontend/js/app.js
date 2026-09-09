let datosValoracionGlobal = null;
let diagnosticosSugeridosGlobal = [];
let reporteIdGenerado = null;

function mostrarCargando(mensaje) {
  document.getElementById("loader-msg").innerText = mensaje;
  document.getElementById("loader").style.display = "block";
}

function ocultarCargando() {
  document.getElementById("loader").style.display = "none";
}

function irAPaso(paso) {
  for (let p = 1; p <= 4; p++) {
    const card = document.getElementById(`step-${p}`);
    const ind = document.getElementById(`ind-${p}`);
    
    if (card) {
      card.style.display = (p === paso) ? "block" : "none";
    }
    if (ind) {
      if (p === paso) {
        ind.classList.add("active");
      } else {
        ind.classList.remove("active");
      }
    }
  }
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// 1. Extraer datos del caso clínico
async function procesarCasoClinico() {
  const fileInput = document.getElementById("archivo-pdf");
  const textoManual = document.getElementById("texto-caso").value.trim();

  if (!fileInput.files[0] && !textoManual) {
    alert("Por favor sube un archivo PDF o escribe el caso clínico.");
    return;
  }

  const formData = new FormData();
  if (fileInput.files[0]) formData.append("archivo", fileInput.files[0]);
  if (textoManual) formData.append("texto_manual", textoManual);

  try {
    mostrarCargando("Gemini está analizando el caso clínico...");
    const res = await fetch("/api/casos/extraer", { method: "POST", body: formData });
    if (!res.ok) throw new Error("Error al analizar el caso clínico.");
    
    datosValoracionGlobal = await res.json();
    
    // Rellenar formulario del Paso 2
    document.getElementById("val-nombre").value = datosValoracionGlobal.nombre_paciente || "";
    document.getElementById("val-edad").value = datosValoracionGlobal.edad || "";
    document.getElementById("val-sexo").value = datosValoracionGlobal.sexo || "";
    document.getElementById("val-cama").value = datosValoracionGlobal.cama_servicio || "";
    document.getElementById("val-motivo").value = datosValoracionGlobal.motivo_ingreso || "";
    
    const sv = datosValoracionGlobal.signos_vitales || {};
    document.getElementById("sv-pa").value = sv.presion_arterial || "";
    document.getElementById("sv-fc").value = sv.frecuencia_cardiaca || "";
    document.getElementById("sv-fr").value = sv.frecuencia_respiratoria || "";
    document.getElementById("sv-temp").value = sv.temperatura || "";
    document.getElementById("sv-sat").value = sv.saturacion_oxigeno || "";

    document.getElementById("val-antecedentes").value = datosValoracionGlobal.antecedentes || "";
    document.getElementById("val-subjetivos").value = datosValoracionGlobal.datos_subjetivos || "";
    document.getElementById("val-objetivos").value = datosValoracionGlobal.datos_objetivos || "";

    ocultarCargando();
    irAPaso(2);
  } catch (err) {
    ocultarCargando();
    alert("Error: " + err.message);
  }
}

// 2. Sugerir Diagnósticos NANDA
async function solicitarDiagnosticos() {
  // Tomar los datos editados por el usuario
  datosValoracionGlobal = {
    nombre_paciente: document.getElementById("val-nombre").value,
    edad: parseInt(document.getElementById("val-edad").value) || null,
    sexo: document.getElementById("val-sexo").value,
    cama_servicio: document.getElementById("val-cama").value,
    motivo_ingreso: document.getElementById("val-motivo").value,
    signos_vitales: {
      presion_arterial: document.getElementById("sv-pa").value,
      frecuencia_cardiaca: document.getElementById("sv-fc").value,
      frecuencia_respiratoria: document.getElementById("sv-fr").value,
      temperatura: document.getElementById("sv-temp").value,
      saturacion_oxigeno: document.getElementById("sv-sat").value
    },
    antecedentes: document.getElementById("val-antecedentes").value,
    datos_subjetivos: document.getElementById("val-subjetivos").value,
    datos_objetivos: document.getElementById("val-objetivos").value
  };

  try {
    mostrarCargando("Consultando NANDA-I para sugerir diagnósticos...");
    const res = await fetch("/api/pae/diagnosticos-sugeridos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(datosValoracionGlobal)
    });
    if (!res.ok) throw new Error("Error obteniendo sugerencias de diagnósticos.");

    const data = await res.json();
    diagnosticosSugeridosGlobal = data.diagnosticos || [];

    // Renderizar tarjetas de diagnóstico con checkboxes
    const contenedor = document.getElementById("lista-diagnosticos");
    contenedor.innerHTML = "";

    diagnosticosSugeridosGlobal.forEach((diag, index) => {
      const div = document.createElement("div");
      div.className = "diag-card selected";
      div.id = `diag-box-${index}`;
      div.innerHTML = `
        <div class="diag-header">
          <input type="checkbox" id="chk-diag-${index}" checked onchange="toggleCardSelect(${index})">
          <strong>${diag.codigo} - ${diag.etiqueta}</strong>
          <span class="badge">${diag.dominio}</span>
        </div>
        <p style="font-weight: 600; margin: 0.5rem 0; color: #2B6CB0;">${diag.formato_pes}</p>
        <p style="font-size: 0.85rem; color: #4A5568;"><em>Justificación:</em> ${diag.justificacion}</p>
      `;
      contenedor.appendChild(div);
    });

    ocultarCargando();
    irAPaso(3);
  } catch (err) {
    ocultarCargando();
    alert("Error: " + err.message);
  }
}

function toggleCardSelect(index) {
  const card = document.getElementById(`diag-box-${index}`);
  const chk = document.getElementById(`chk-diag-${index}`);
  if (chk.checked) card.classList.add("selected");
  else card.classList.remove("selected");
}

// 3. Generar Plan PAE completo con NOC y NIC
async function generarPlanFinal() {
  const seleccionados = [];
  diagnosticosSugeridosGlobal.forEach((diag, i) => {
    const chk = document.getElementById(`chk-diag-${i}`);
    if (chk && chk.checked) seleccionados.push(diag);
  });

  if (seleccionados.length === 0) {
    alert("Por favor selecciona al menos un diagnóstico.");
    return;
  }

  try {
    mostrarCargando("Consultando NOC y NIC para elaborar el plan de cuidados...");
    const res = await fetch("/api/pae/generar-plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        paciente_datos: datosValoracionGlobal,
        diagnosticos_elegidos: seleccionados
      })
    });
    if (!res.ok) throw new Error("Error generando el plan PAE.");

    const planCompleto = await res.json();

    // Obtener el reporte recién guardado para tener el ID de descarga
    const resRep = await fetch("/api/reportes/");
    const lista = await resRep.json();
    if (lista.length > 0) {
      reporteIdGenerado = lista[0].reporte_id;
      document.getElementById("btn-descargar-word").href = `/api/exportar/word/${reporteIdGenerado}`;
    }

    // Renderizar tablas
    document.getElementById("res-paciente").innerText = planCompleto.paciente_nombre;
    document.getElementById("res-evaluacion").innerText = planCompleto.resumen_valoracion;

    const tablaContainer = document.getElementById("tablas-pae-resultado");
    tablaContainer.innerHTML = "";

    planCompleto.planes.forEach((p, idx) => {
      let nocsHtml = p.resultados_noc.map(n => `
        <strong>${n.codigo} ${n.nombre}</strong><br>
        ${n.indicadores.map(ind => `• ${ind.nombre} (Diana: ${ind.puntuacion_actual} ➔ ${ind.puntuacion_diana})`).join("<br>")}
      `).join("<hr style='margin: 0.5rem 0;'>");

      let nicsHtml = p.intervenciones_nic.map(nic => `
        <strong>${nic.codigo} ${nic.nombre}</strong><br>
        ${nic.actividades.map(act => `• ${act}`).join("<br>")}
      `).join("<hr style='margin: 0.5rem 0;'>");

      tablaContainer.innerHTML += `
        <h3 style="margin-top: 1.5rem; color: #1F4E79;">Diagnóstico #${idx + 1}: ${p.diagnostico_nanda.etiqueta}</h3>
        <table>
          <thead>
            <tr>
              <th style="width: 30%;">Diagnóstico NANDA</th>
              <th style="width: 35%;">Resultados NOC</th>
              <th style="width: 35%;">Intervenciones NIC</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>${p.diagnostico_nanda.codigo}</strong><br>${p.diagnostico_nanda.formato_pes}</td>
              <td>${nocsHtml}</td>
              <td>${nicsHtml}</td>
            </tr>
          </tbody>
        </table>
      `;
    });

    // Renderizar sección SOAPIE si está presente
    if (planCompleto.soapie) {
      const s = planCompleto.soapie;
      tablaContainer.innerHTML += `
        <h3 style="margin-top: 2rem; color: #1F4E79;">Registro de Enfermería (SOAPIE)</h3>
        <table>
          <thead>
            <tr>
              <th style="width: 15%;">Etapa</th>
              <th style="width: 85%;">Contenido Clínico</th>
            </tr>
          </thead>
          <tbody>
            <tr><td><strong>S</strong> (Subjetivo)</td><td>${s.s}</td></tr>
            <tr><td><strong>O</strong> (Objetivo)</td><td>${s.o}</td></tr>
            <tr><td><strong>A</strong> (Análisis)</td><td>${s.a.replace(/●/g, '<br>●')}</td></tr>
            <tr><td><strong>P</strong> (Planificación)</td><td>${s.p.replace(/➔/g, '<br>➔')}</td></tr>
            <tr><td><strong>I</strong> (Intervenciones)</td><td>${s.i.replace(/●/g, '<br>●')}</td></tr>
            <tr><td><strong>E</strong> (Evaluación)</td><td>${s.e.replace(/;/g, '<br>')}</td></tr>
          </tbody>
        </table>
      `;
    }

    ocultarCargando();
    irAPaso(4);
  } catch (err) {
    ocultarCargando();
    alert("Error: " + err.message);
  }
}