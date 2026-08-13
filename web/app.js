const form = document.querySelector("#uploadForm");
const fileInput = document.querySelector("#fileInput");
const fileLabel = document.querySelector("#fileLabel");
const dropZone = document.querySelector("#dropZone");
const selectedTranscriptionEl = document.querySelector("#selectedTranscription");
const clearSelectedTranscription = document.querySelector("#clearSelectedTranscription");
const clearTranscriptionTasks = document.querySelector("#clearTranscriptionTasks");
const jobsEl = document.querySelector("#jobs");
const transcriptionHistoryEl = document.querySelector("#transcriptionHistory");

const silenceForm = document.querySelector("#silenceForm");
const silenceFileInput = document.querySelector("#silenceFileInput");
const silenceFileLabel = document.querySelector("#silenceFileLabel");
const silenceDropZone = document.querySelector("#silenceDropZone");
const selectedSilenceEl = document.querySelector("#selectedSilence");
const clearSelectedSilence = document.querySelector("#clearSelectedSilence");
const clearSilenceTasks = document.querySelector("#clearSilenceTasks");
const silenceTasksEl = document.querySelector("#silenceTasks");
const silenceHistoryEl = document.querySelector("#silenceHistory");
const silenceResultTitle = document.querySelector("#silenceResultTitle");
const silenceResultMeta = document.querySelector("#silenceResultMeta");
const silenceResult = document.querySelector("#silenceResult");
const silenceDownload = document.querySelector("#silenceDownload");

const machineStatus = document.querySelector("#machineStatus");
const loadingOverlay = document.querySelector("#loadingOverlay");
const loadingMessage = document.querySelector("#loadingMessage");
const wakeButton = document.querySelector("#wakeButton");
const transcriptEl = document.querySelector("#transcript");
const resultTitle = document.querySelector("#resultTitle");
const resultMeta = document.querySelector("#resultMeta");
const searchBox = document.querySelector("#searchBox");
const copyButton = document.querySelector("#copyButton");
const playerDock = document.querySelector("#playerDock");
const audioPlayer = document.querySelector("#audioPlayer");
const playButton = document.querySelector("#playButton");
const seekBar = document.querySelector("#seekBar");
const currentTime = document.querySelector("#currentTime");
const durationTime = document.querySelector("#durationTime");
const volumeBar = document.querySelector("#volumeBar");
const playerTitle = document.querySelector("#playerTitle");

let selectedJobId = null;
let selectedSilenceId = null;
let currentJob = null;
let engineStatus = null;
let initialEngineReady = false;
let transcriptionFiles = [];
let silenceFiles = [];
let currentPlayerMode = "transcription";

function clock(seconds, separator = ":") {
  const total = Math.floor(seconds || 0);
  const ms = Math.round(((seconds || 0) - total) * 1000);
  const h = String(Math.floor(total / 3600)).padStart(2, "0");
  const m = String(Math.floor((total % 3600) / 60)).padStart(2, "0");
  const s = String(total % 60).padStart(2, "0");
  return `${h}:${m}:${s}${separator}${String(ms).padStart(3, "0")}`;
}

function shortClock(seconds) {
  const total = Math.floor(seconds || 0);
  const h = Math.floor(total / 3600);
  const m = String(Math.floor((total % 3600) / 60)).padStart(2, "0");
  const s = String(total % 60).padStart(2, "0");
  return h ? `${h}:${m}:${s}` : `${m}:${s}`;
}

function escapeHtml(value = "") {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  }[char]));
}

function highlight(text, query) {
  const safe = escapeHtml(text);
  if (!query) return safe;
  const needle = query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return safe.replace(new RegExp(needle, "gi"), (match) => `<mark>${match}</mark>`);
}

function activeStatuses() {
  return ["queued", "preparing", "processing"];
}

function fileKey(file) {
  return `${file.name}:${file.size}:${file.lastModified}`;
}

function addFiles(target, files) {
  const existing = new Set(target.map(fileKey));
  for (const file of Array.from(files || [])) {
    if (!existing.has(fileKey(file))) {
      target.push(file);
      existing.add(fileKey(file));
    }
  }
}

function formatSize(bytes) {
  if (!bytes) return "0 MB";
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function renderSelected(list, element, labelElement, emptyText) {
  labelElement.textContent = list.length ? `${list.length} arquivo(s) guardado(s) na selecao` : emptyText;
  if (!list.length) {
    element.innerHTML = '<p class="empty compact">Nenhum arquivo selecionado.</p>';
    return;
  }
  element.innerHTML = list.map((file, index) => `
    <div class="selectedFile">
      <span>${escapeHtml(file.name)}</span>
      <small>${formatSize(file.size)}</small>
      <button type="button" data-index="${index}">Remover</button>
    </div>
  `).join("");
}

function bindSelectedRemoval(element, list, render) {
  element.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-index]");
    if (!button) return;
    list.splice(Number(button.dataset.index), 1);
    render();
  });
}

function renderTranscriptionSelected() {
  renderSelected(transcriptionFiles, selectedTranscriptionEl, fileLabel, "Adicionar videos/audios de uma ou varias pastas");
}

function renderSilenceSelected() {
  renderSelected(silenceFiles, selectedSilenceEl, silenceFileLabel, "Adicionar audios/videos para cortar silencio");
}

async function loadHealth() {
  const res = await fetch("/api/health");
  const data = await res.json();
  machineStatus.textContent = data.cuda
    ? "GPU CUDA detectada. Modo acelerado ativo."
    : "CUDA nao detectada. Usando CPU local.";
}

function setTranscriptionDisabled(disabled) {
  for (const item of form.querySelectorAll("input, select, textarea, button")) {
    item.disabled = disabled;
  }
}

function renderEngineStatus(status) {
  engineStatus = status;
  const device = status.device ? status.device.toUpperCase() : "aguardando";
  const model = status.model_size || "large-v3";
  machineStatus.textContent = `${status.message} - ${model} - ${device}`;
  wakeButton.hidden = status.status !== "standby";

  const loading = status.status === "loading";
  if (!initialEngineReady || loading) {
    loadingOverlay.hidden = false;
    loadingMessage.textContent = status.message || "Carregando modelo...";
  }

  if (status.status === "ready") {
    initialEngineReady = true;
    loadingOverlay.hidden = true;
    setTranscriptionDisabled(false);
    return;
  }

  if (status.status === "standby") {
    initialEngineReady = true;
    loadingOverlay.hidden = true;
    setTranscriptionDisabled(true);
    wakeButton.disabled = false;
    return;
  }

  if (status.status === "failed") {
    initialEngineReady = true;
    loadingOverlay.hidden = true;
    setTranscriptionDisabled(true);
    machineStatus.textContent = status.last_error || "Falha no motor de transcricao";
    wakeButton.hidden = false;
    return;
  }

  setTranscriptionDisabled(true);
}

async function loadEngineStatus() {
  const res = await fetch("/api/engine");
  const status = await res.json();
  renderEngineStatus(status);
  return status;
}

async function warmupEngine(showOverlay = true) {
  if (showOverlay) {
    loadingOverlay.hidden = false;
    loadingMessage.textContent = "Carregando tudo de uma vez...";
    setTranscriptionDisabled(true);
  }
  await fetch("/api/engine/warmup", { method: "POST" });

  for (let i = 0; i < 180; i += 1) {
    const status = await loadEngineStatus();
    if (["ready", "failed"].includes(status.status)) return status;
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  return loadEngineStatus();
}

function buildCard(item, selectedId, actions) {
  const percent = Math.round((item.progress || 0) * 100);
  const canCancel = activeStatuses().includes(item.status);
  const canRetry = item.status === "failed" || item.status === "cancelled";
  const removedSeconds = item.removed_seconds != null ? shortClock(item.removed_seconds) : "";
  const extra = item.removed_percent != null ? ` | removido: ${removedSeconds} (${item.removed_percent}%)` : "";
  const button = document.createElement("button");
  button.className = `job ${item.status} ${item.id === selectedId ? "selected" : ""}`;
  button.innerHTML = `
    <strong>${escapeHtml(item.filename)}</strong>
    <span>${escapeHtml(item.message)} - ${percent}%${extra}</span>
    <div class="bar"><i style="width:${percent}%"></i></div>
    <div class="jobActions">
      ${canCancel ? '<b data-action="cancel">Cancelar</b>' : ""}
      ${canRetry ? '<b data-action="retry">Tentar novamente</b>' : ""}
    </div>
  `;
  button.addEventListener("click", () => actions.open(item.id));
  const cancel = button.querySelector('[data-action="cancel"]');
  if (cancel) {
    cancel.addEventListener("click", async (event) => {
      event.stopPropagation();
      await actions.cancel(item.id);
    });
  }
  const retry = button.querySelector('[data-action="retry"]');
  if (retry) {
    retry.addEventListener("click", async (event) => {
      event.stopPropagation();
      await actions.retry(item.id);
    });
  }
  return button;
}

async function loadJobs() {
  const [tasksRes, historyRes] = await Promise.all([
    fetch("/api/jobs"),
    fetch("/api/history/transcriptions"),
  ]);
  const tasks = await tasksRes.json();
  const history = await historyRes.json();
  renderTaskList(jobsEl, tasks, selectedJobId, {
    empty: "Nenhuma tarefa de transcricao.",
    open: selectJob,
    cancel: cancelJob,
    retry: retryJob,
  });
  renderTaskList(transcriptionHistoryEl, history, selectedJobId, {
    empty: "Historico vazio.",
    open: selectJob,
    cancel: cancelJob,
    retry: retryJob,
  });

  if (tasks.some((job) => activeStatuses().includes(job.status))) {
    window.setTimeout(loadJobs, 1800);
  }
}

function renderTaskList(element, items, selectedId, actions) {
  element.innerHTML = "";
  if (!items.length) {
    element.innerHTML = `<p class="empty">${actions.empty}</p>`;
    return;
  }
  for (const item of items) {
    element.appendChild(buildCard(item, selectedId, actions));
  }
}

async function selectJob(jobId) {
  selectedJobId = jobId;
  currentPlayerMode = "transcription";
  const res = await fetch(`/api/jobs/${jobId}`);
  currentJob = await res.json();

  if (currentJob.audio_url) {
    setPlayer(currentJob.audio_url, currentJob.id, currentJob.filename);
  } else {
    clearPlayer();
  }

  renderTranscript();
  await loadJobs();
}

async function retryJob(jobId) {
  const res = await fetch(`/api/jobs/${jobId}/retry`, { method: "POST" });
  if (!res.ok) {
    alert(`Nao foi possivel retentar: ${await res.text()}`);
    return;
  }
  await loadJobs();
  await selectJob(jobId);
}

async function cancelJob(jobId) {
  await fetch(`/api/jobs/${jobId}/cancel`, { method: "POST" });
  await loadJobs();
  if (selectedJobId === jobId) await selectJob(jobId);
}

function renderTranscript() {
  if (!currentJob) return;
  const query = searchBox.value.trim();
  resultTitle.textContent = currentJob.filename;
  resultMeta.textContent = `${currentJob.status} - idioma: ${currentJob.detected_language || currentJob.settings.language || "pendente"} - ${currentJob.segments.length} trechos`;

  if (currentJob.error) {
    transcriptEl.innerHTML = `<p class="empty">${escapeHtml(currentJob.error)}</p>`;
    return;
  }

  if (!currentJob.segments.length) {
    transcriptEl.innerHTML = '<p class="empty">Aguardando os primeiros trechos...</p>';
    return;
  }

  transcriptEl.innerHTML = currentJob.segments.map((seg) => `
    <article class="segment" data-start="${seg.start}" data-end="${seg.end}">
      <div class="time">${clock(seg.start)} - ${clock(seg.end)}</div>
      <div>${highlight(seg.text, query)}</div>
    </article>
  `).join("");

  for (const segment of transcriptEl.querySelectorAll(".segment")) {
    segment.addEventListener("click", () => {
      currentPlayerMode = "transcription";
      audioPlayer.currentTime = Number(segment.dataset.start || 0);
      audioPlayer.play();
    });
  }
  syncActiveSegment();
}

async function loadSilenceTasks() {
  const [tasksRes, historyRes] = await Promise.all([
    fetch("/api/silence/tasks"),
    fetch("/api/silence/history"),
  ]);
  const tasks = await tasksRes.json();
  const history = await historyRes.json();
  renderTaskList(silenceTasksEl, tasks, selectedSilenceId, {
    empty: "Nenhuma tarefa de silencio.",
    open: selectSilenceTask,
    cancel: cancelSilenceTask,
    retry: retrySilenceTask,
  });
  renderTaskList(silenceHistoryEl, history, selectedSilenceId, {
    empty: "Historico vazio.",
    open: selectSilenceTask,
    cancel: cancelSilenceTask,
    retry: retrySilenceTask,
  });

  if (tasks.some((task) => activeStatuses().includes(task.status))) {
    window.setTimeout(loadSilenceTasks, 1800);
  }
}

async function selectSilenceTask(taskId) {
  selectedSilenceId = taskId;
  currentPlayerMode = "silence";
  const res = await fetch(`/api/silence/${taskId}`);
  const task = await res.json();
  silenceResultTitle.textContent = task.filename;
  const removedSeconds = task.removed_seconds != null ? shortClock(task.removed_seconds) : "";
  const removed = task.removed_percent != null ? ` - removido: ${removedSeconds} (${task.removed_percent}%)` : "";
  silenceResultMeta.textContent = `${task.status} - ${task.message}${removed}`;
  silenceResult.innerHTML = task.error
    ? `<p class="empty">${escapeHtml(task.error)}</p>`
    : `
      <p class="empty">Original: ${shortClock(task.duration_original)} | Sem silencio: ${shortClock(task.duration_output)}</p>
      <p class="empty">Motor: ${escapeHtml(task.engine || "pendente")} | Cortes: ${task.silence_cuts || 0} | Trechos mantidos: ${task.kept_segments || 0}</p>
      <p class="empty">Threshold: ${task.threshold_db_used != null ? `${task.threshold_db_used} dB` : "automatico"}</p>
    `;
  silenceDownload.hidden = !task.audio_url;

  if (task.audio_url) {
    silenceDownload.href = task.audio_url;
    setPlayer(task.audio_url, task.id, task.filename);
  }
  await loadSilenceTasks();
}

async function cancelSilenceTask(taskId) {
  await fetch(`/api/silence/${taskId}/cancel`, { method: "POST" });
  await loadSilenceTasks();
  if (selectedSilenceId === taskId) await selectSilenceTask(taskId);
}

async function retrySilenceTask(taskId) {
  const res = await fetch(`/api/silence/${taskId}/retry`, { method: "POST" });
  if (!res.ok) {
    alert(`Nao foi possivel retentar: ${await res.text()}`);
    return;
  }
  await loadSilenceTasks();
  await selectSilenceTask(taskId);
}

function setPlayer(url, id, title) {
  if (audioPlayer.dataset.itemId !== id || audioPlayer.src !== new URL(url, location.href).href) {
    audioPlayer.src = url;
    audioPlayer.dataset.itemId = id;
    seekBar.value = "0";
    currentTime.textContent = "00:00";
    durationTime.textContent = "00:00";
  }
  playerTitle.textContent = title;
  playerDock.hidden = false;
}

function clearPlayer() {
  audioPlayer.removeAttribute("src");
  audioPlayer.dataset.itemId = "";
  playerDock.hidden = true;
}

function setupDrop(zone, input, files, render) {
  input.addEventListener("change", () => {
    addFiles(files, input.files);
    input.value = "";
    render();
  });
  for (const eventName of ["dragenter", "dragover"]) {
    zone.addEventListener(eventName, (event) => {
      event.preventDefault();
      zone.classList.add("dragging");
    });
  }
  for (const eventName of ["dragleave", "drop"]) {
    zone.addEventListener(eventName, (event) => {
      event.preventDefault();
      zone.classList.remove("dragging");
    });
  }
  zone.addEventListener("drop", (event) => {
    if (!event.dataTransfer.files.length) return;
    addFiles(files, event.dataTransfer.files);
    render();
  });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!transcriptionFiles.length) {
    alert("Adicione pelo menos um arquivo para transcrever.");
    return;
  }
  if (!engineStatus || engineStatus.status !== "ready") {
    await warmupEngine(true);
    if (!engineStatus || engineStatus.status !== "ready") return;
  }
  const submit = form.querySelector("button[type=submit]");
  submit.disabled = true;
  submit.textContent = "Enviando...";

  try {
    const data = new FormData(form);
    data.delete("files");
    for (const file of transcriptionFiles) data.append("files", file, file.name);
    const res = await fetch("/api/jobs", { method: "POST", body: data });
    if (!res.ok) throw new Error(await res.text());
    const created = await res.json();
    transcriptionFiles.length = 0;
    renderTranscriptionSelected();
    await loadJobs();
    if (created[0]) await selectJob(created[0].id);
  } catch (error) {
    alert(`Falha ao iniciar transcricao: ${error.message}`);
  } finally {
    submit.disabled = false;
    submit.textContent = "Transcrever selecionados";
  }
});

silenceForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!silenceFiles.length) {
    alert("Adicione pelo menos um arquivo para remover silencio.");
    return;
  }
  const submit = silenceForm.querySelector("button[type=submit]");
  submit.disabled = true;
  submit.textContent = "Enviando...";

  try {
    const data = new FormData(silenceForm);
    data.delete("files");
    for (const file of silenceFiles) data.append("files", file, file.name);
    const res = await fetch("/api/silence", { method: "POST", body: data });
    if (!res.ok) throw new Error(await res.text());
    const created = await res.json();
    silenceFiles.length = 0;
    renderSilenceSelected();
    await loadSilenceTasks();
    if (created[0]) await selectSilenceTask(created[0].id);
  } catch (error) {
    alert(`Falha ao remover silencio: ${error.message}`);
  } finally {
    submit.disabled = false;
    submit.textContent = "Remover silencio";
  }
});

document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((item) => item.classList.remove("active"));
    document.querySelectorAll(".toolPanel").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    document.querySelector(`#${button.dataset.tab}Panel`).classList.add("active");
  });
});

wakeButton.addEventListener("click", () => {
  wakeButton.disabled = true;
  warmupEngine(true).finally(() => {
    wakeButton.disabled = false;
  });
});

searchBox.addEventListener("input", renderTranscript);

copyButton.addEventListener("click", async () => {
  if (!currentJob || !currentJob.text) return;
  await navigator.clipboard.writeText(currentJob.text);
  copyButton.textContent = "Copiado";
  window.setTimeout(() => {
    copyButton.textContent = "Copiar tudo";
  }, 1200);
});

clearSelectedTranscription.addEventListener("click", () => {
  transcriptionFiles.length = 0;
  renderTranscriptionSelected();
});

clearSelectedSilence.addEventListener("click", () => {
  silenceFiles.length = 0;
  renderSilenceSelected();
});

clearTranscriptionTasks.addEventListener("click", async () => {
  await fetch("/api/jobs/clear", { method: "POST" });
  await loadJobs();
});

clearSilenceTasks.addEventListener("click", async () => {
  await fetch("/api/silence/clear", { method: "POST" });
  await loadSilenceTasks();
});

playButton.addEventListener("click", () => {
  if (!audioPlayer.src) return;
  if (audioPlayer.paused) {
    audioPlayer.play();
  } else {
    audioPlayer.pause();
  }
});

seekBar.addEventListener("input", () => {
  if (!audioPlayer.duration) return;
  audioPlayer.currentTime = (Number(seekBar.value) / 1000) * audioPlayer.duration;
});

volumeBar.addEventListener("input", () => {
  audioPlayer.volume = Number(volumeBar.value);
});

audioPlayer.addEventListener("play", () => {
  playButton.textContent = "Pausar";
});

audioPlayer.addEventListener("pause", () => {
  playButton.textContent = "Play";
});

audioPlayer.addEventListener("loadedmetadata", () => {
  durationTime.textContent = shortClock(audioPlayer.duration);
});

audioPlayer.addEventListener("timeupdate", () => {
  currentTime.textContent = shortClock(audioPlayer.currentTime);
  if (audioPlayer.duration) {
    seekBar.value = String(Math.round((audioPlayer.currentTime / audioPlayer.duration) * 1000));
  }
  if (currentPlayerMode === "transcription") syncActiveSegment();
});

function syncActiveSegment() {
  const now = audioPlayer.currentTime || 0;
  let active = null;
  for (const segment of transcriptEl.querySelectorAll(".segment")) {
    const start = Number(segment.dataset.start || 0);
    const end = Number(segment.dataset.end || 0);
    const isActive = now >= start && now <= end;
    segment.classList.toggle("active", isActive);
    if (isActive) active = segment;
  }
  if (active && !audioPlayer.paused) {
    active.scrollIntoView({ block: "center", behavior: "smooth" });
  }
}

bindSelectedRemoval(selectedTranscriptionEl, transcriptionFiles, renderTranscriptionSelected);
bindSelectedRemoval(selectedSilenceEl, silenceFiles, renderSilenceSelected);
setupDrop(dropZone, fileInput, transcriptionFiles, renderTranscriptionSelected);
setupDrop(silenceDropZone, silenceFileInput, silenceFiles, renderSilenceSelected);
renderTranscriptionSelected();
renderSilenceSelected();
setTranscriptionDisabled(true);
loadHealth().catch(() => {
  machineStatus.textContent = "Nao foi possivel ler o status da maquina.";
});
warmupEngine(true).catch(() => {
  loadingMessage.textContent = "Nao foi possivel preparar o motor.";
});
loadJobs();
loadSilenceTasks();
window.setInterval(async () => {
  await loadEngineStatus();
  await loadJobs();
  await loadSilenceTasks();
  if (selectedJobId) await selectJob(selectedJobId);
  if (selectedSilenceId) await selectSilenceTask(selectedSilenceId);
}, 3500);
