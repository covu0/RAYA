const API = "http://localhost:8000";

const state = {
  caregiverId: null,
  patientId: null,
};

async function loadDrugs() {
  try {
    const res = await fetch(`${API}/drugs`);
    const data = await res.json();
    const datalist = document.getElementById("drug-list");
    const seen = new Set();
    Object.values(data).flat().forEach((alias) => {
      if (seen.has(alias)) return;
      seen.add(alias);
      const opt = document.createElement("option");
      opt.value = alias;
      datalist.appendChild(opt);
    });
  } catch (e) {
    console.error("Failed to load drug list:", e);
  }
}

async function createPatient() {
  const name = document.getElementById("patient-name").value.trim();
  const age = parseInt(document.getElementById("patient-age").value) || null;
  if (!name) return alert("الرجاء إدخال اسم المريض");

  // Auto-create caregiver for MVP (no auth yet)
  const cgRes = await fetch(`${API}/caregivers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: "المستخدم" }),
  });
  const cg = await cgRes.json();
  state.caregiverId = cg.id;

  const pRes = await fetch(`${API}/patients`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ caregiver_id: cg.id, name, age }),
  });
  const p = await pRes.json();
  state.patientId = p.id;

  document.getElementById("patient-info").textContent =
    `المريض: ${p.name}${age ? ` (${age} سنة)` : ""}`;
  document.getElementById("setup-card").classList.add("hidden");
  document.getElementById("add-card").classList.remove("hidden");
  document.getElementById("meds-card").classList.remove("hidden");
  refreshMeds();
}

async function addMedication() {
  const name = document.getElementById("med-name").value.trim();
  const dose = document.getElementById("med-dose").value.trim();
  const freq = document.getElementById("med-freq").value.trim();
  const errEl = document.getElementById("add-error");
  errEl.classList.add("hidden");

  if (!name) return alert("الرجاء إدخال اسم الدواء");
  if (!state.patientId) return alert("لم يتم إنشاء ملف المريض بعد");

  const res = await fetch(`${API}/patients/${state.patientId}/medications`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, dose: dose || null, frequency: freq || null }),
  });
  const data = await res.json();
  if (!res.ok) {
    errEl.textContent = "الدواء غير معروف. جرب اسمًا آخر مثل بانادول أو Aspirin.";
    errEl.classList.remove("hidden");
    return;
  }
  document.getElementById("med-name").value = "";
  document.getElementById("med-dose").value = "";
  document.getElementById("med-freq").value = "";
  refreshMeds();
}

function renderWarnings(warnings) {
  const card = document.getElementById("warnings-card");
  if (!warnings.length) {
    card.classList.add("hidden");
    card.innerHTML = "";
    return;
  }
  card.classList.remove("hidden");
  card.innerHTML = warnings.map((w) => {
    const isSevere = w.severity === "severe";
    const bg = isSevere ? "bg-red-50 border-red-300" : "bg-amber-50 border-amber-300";
    const text = isSevere ? "text-red-800" : "text-amber-800";
    const label = isSevere ? "تحذير شديد" : "تحذير متوسط";
    return `
      <div class="${bg} border rounded-xl p-4">
        <div class="flex items-center gap-2 mb-1">
          <span class="text-lg">${isSevere ? "⚠️" : "⚡"}</span>
          <span class="font-bold ${text}">${label}: ${w.drug_a} + ${w.drug_b}</span>
        </div>
        <p class="${text} text-sm leading-relaxed">${w.message_ar}</p>
        <p class="${text} text-xs mt-1 opacity-75" dir="ltr">${w.message_en}</p>
      </div>
    `;
  }).join("");
}

async function refreshMeds() {
  if (!state.patientId) return;
  const res = await fetch(`${API}/patients/${state.patientId}/medications`);
  const meds = await res.json();
  const list = document.getElementById("meds-list");
  if (!meds.length) {
    list.innerHTML = `<li class="text-sm text-slate-500">لم يتم إضافة أدوية بعد.</li>`;
  } else {
    list.innerHTML = meds.map((m) => `
      <li class="flex justify-between items-start border border-slate-200 rounded-lg p-3">
        <div>
          <div class="font-medium">${m.name_input}
            <span class="text-xs text-slate-400">(${m.active_ingredient})</span>
          </div>
          <div class="text-sm text-slate-500">
            ${[m.dose, m.frequency].filter(Boolean).join(" — ") || ""}
          </div>
        </div>
        <button onclick="deleteMed(${m.id})" class="text-red-600 text-sm hover:underline">حذف</button>
      </li>
    `).join("");
  }

  const checkRes = await fetch(`${API}/patients/${state.patientId}/check`);
  const checkData = await checkRes.json();
  renderWarnings(checkData.warnings || []);
}

async function deleteMed(id) {
  await fetch(`${API}/medications/${id}`, { method: "DELETE" });
  refreshMeds();
}
window.deleteMed = deleteMed;

document.getElementById("create-patient").addEventListener("click", createPatient);
document.getElementById("add-med").addEventListener("click", addMedication);
loadDrugs();
