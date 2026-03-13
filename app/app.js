let hotspotChart = null;
let interactionNetwork = null;

// Log active config on load
if (window.envConfig) {
  console.info(`[agent-tracking] ENV_IDE=${window.envConfig.env_ide} | AGENT_CONV_ID=${window.envConfig.conv_id}`);
}

function loadMetrics(providedData = null) {
  console.log("Loading metrics...");
  const data = providedData || window.metrics || [];
  let ctx = document.getElementById("hotspotChart");
  const card = ctx ? ctx.closest(".card") : null;

  if (!Array.isArray(data) || !data.length) {
    console.warn("No metrics to display");
    if (card) card.classList.add("hidden");
    if (hotspotChart) {
      hotspotChart.destroy();
      hotspotChart = null;
    }
    return;
  }

  if (card) card.classList.remove("hidden");

  const dataset = data.map(d => ({
    x: Number(d.churn) || 0,
    y: Number(d.complexity) || 0,
    filename: d.filename,
    loc: d.loc
  }));

  if (!ctx) { console.error("Canvas hotspotChart not found"); return; }

  Chart.defaults.color = "#475569";
  Chart.defaults.scale.grid.color = "rgba(0, 0, 0, 0.05)";

  if (hotspotChart) {
    hotspotChart.data.datasets[0].data = dataset;
    hotspotChart.update();
  } else {
    hotspotChart = new Chart(ctx, {
      type: "scatter",
      data: {
        datasets: [{
          label: "Value",
          data: dataset,
          pointRadius: 6,
          hoverRadius: 8,
          backgroundColor: "rgba(59, 130, 246, 0.8)",
          borderColor: "#2563eb",
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          tooltip: {
            callbacks: {
              label: (ctx) => {
                const d = ctx.raw;
                return [d.filename, `Churn: ${d.x}`, `Complexity: ${d.y}`, `LOC: ${d.loc}`];
              }
            }
          }
        },
        scales: {
          x: { title: { display: true, text: "Nombre de modifications (Git Churn)" } },
          y: { title: { display: true, text: "Complexité cyclomatique moyenne" } }
        }
      }
    });
  }
}

function loadNetwork(providedData = null) {
  const container = document.getElementById("interactionNetwork");
  const dataRaw = providedData || window.graphData;

  const card = container ? container.closest(".card") : null;

  if (!container || !dataRaw || !dataRaw.nodes || !dataRaw.edges || !dataRaw.nodes.length) {
    console.warn("No graph data to display or container missing");
    if (card) card.classList.add("hidden");
    if (interactionNetwork) {
      interactionNetwork.destroy();
      interactionNetwork = null;
    }
    return;
  }

  if (card) card.classList.remove("hidden");

  const nodesArr = dataRaw.nodes.map(n => ({
    ...n,
    font: { color: "#1e293b", face: "Outfit" },
    shadow: { enabled: true, color: "rgba(0,0,0,0.1)", size: 5, x: 2, y: 2 }
  }));

  const edgesArr = dataRaw.edges.map(e => ({
    ...e,
    color: { color: "#cbd5e1", highlight: "#3b82f6" }
  }));

  const data = {
    nodes: new vis.DataSet(nodesArr),
    edges: new vis.DataSet(edgesArr)
  };

  const options = {
    interaction: { dragNodes: true, hover: true },
    physics: {
      enabled: true,
      forceAtlas2Based: {
        avoidOverlap: 0.1,
        centralGravity: 0.01,
        damping: 0.4,
        gravitationalConstant: -50,
        strokeWidth: 2,
        springConstant: 0.08,
        springLength: 100
      },
      solver: "forceAtlas2Based",
      stabilization: { enabled: true, fit: true, iterations: 1000, updateInterval: 50 }
    }
  };

  if (interactionNetwork) {
    interactionNetwork.setData(data);
  } else {
    interactionNetwork = new vis.Network(container, data, options);
  }
}

async function selectTask(taskId, element) {
  console.log(`Selecting task: ${taskId}`);

  // UI Feedback
  document.querySelectorAll('.task-item').forEach(el => el.classList.remove('active'));
  if (element) element.classList.add('active');

  // Sync header select
  const select = document.getElementById("taskSelect");
  if (select) select.value = taskId;

  try {
    const [metricsRes, graphRes] = await Promise.all([
      fetch(`/api/metrics/${taskId}`),
      fetch(`/api/graph/${taskId}`)
    ]);

    const metricsData = await metricsRes.json();
    const graphData = await graphRes.json();

    loadMetrics(metricsData);
    loadNetwork(graphData);
  } catch (e) {
    console.error("Error fetching versioned data:", e);
  }
}

function buildTaskEl(task) {
  const item = document.createElement("div");
  item.className = "task-item fade-in";
  item.dataset.taskId = task.id;
  item.onclick = () => selectTask(task.id, item);

  const meta = document.createElement("div");
  meta.className = "task-meta";

  const taskId = document.createElement("span");
  taskId.className = "task-id";
  taskId.textContent = `#${task.id}`;

  const taskDate = document.createElement("span");
  taskDate.className = "task-date";
  taskDate.textContent = new Date(task.created_at).toLocaleString();

  meta.appendChild(taskId);
  meta.appendChild(taskDate);
  item.appendChild(meta);

  if (task.conversation_id) {
    const convId = document.createElement("div");
    convId.className = "task-conv-id";
    convId.title = task.conversation_id;
    convId.textContent = task.conversation_id.slice(0, 8) + "…";
    item.appendChild(convId);
  }

  const asked = document.createElement("div");
  asked.className = "task-asked";
  asked.textContent = task.asked || "";
  item.appendChild(asked);

  const effectuated = document.createElement("pre");
  effectuated.className = "task-effectuated";
  effectuated.textContent = task.effectuated || "";
  item.appendChild(effectuated);

  return item;
}

function loadAgentTasks() {
  const container = document.getElementById("taskList");
  const select = document.getElementById("taskSelect");
  const data = window.agentTasks || [];

  if (!container) return;

  if (!data.length) {
    container.innerHTML = '<div class="no-tasks">No tasks tracked yet.</div>';
    if (select) select.innerHTML = '<option disabled selected>No tasks</option>';
    return;
  }

  // Deduplication by ID (keep latest)
  const taskMap = new Map();
  data.forEach(task => taskMap.set(task.id, task));
  const uniqueTasks = Array.from(taskMap.values()).sort((a, b) => b.id - a.id);

  // Populate header select
  if (select) {
    const buildOptions = (tasks) => {
      select.innerHTML = tasks.map(task => {
        const raw = task.asked || `Task #${task.id}`;
        const label = raw.replace(/<[^>]*>/g, '').slice(0, 36);
        const suffix = raw.replace(/<[^>]*>/g, '').length > 36 ? '…' : '';
        return `<option value="${task.id}">#${task.id} · ${label}${suffix}</option>`;
      }).join("");
    };

    const buildDatalist = (tasks) => {
      const datalist = document.getElementById("taskSearchList");
      if (!datalist) return;
      datalist.innerHTML = tasks.map(task => {
        const raw = (task.asked || `Task #${task.id}`).replace(/<[^>]*>/g, '').slice(0, 60);
        return `<option value="#${task.id} · ${raw}"></option>`;
      }).join("");
    };

    buildOptions(uniqueTasks);
    buildDatalist(uniqueTasks);

    if (!select._changeListenerAdded) {
      select.addEventListener("change", () => {
        const id = Number(select.value);
        const el = document.querySelector(`.task-item[data-task-id="${id}"]`);
        selectTask(id, el);
      });
      select._changeListenerAdded = true;
    }

    const search = document.getElementById("taskSearch");
    if (search && !search._inputListenerAdded) {
      search.addEventListener("input", () => {
        const q = search.value.toLowerCase();
        const filtered = uniqueTasks.filter(task => {
          const raw = (task.asked || `Task #${task.id}`).replace(/<[^>]*>/g, '').toLowerCase();
          return `#${task.id}`.includes(q) || raw.includes(q);
        });
        buildOptions(filtered.length ? filtered : uniqueTasks);
      });

      search.addEventListener("change", () => {
        const match = uniqueTasks.find(task => {
          const raw = (task.asked || `Task #${task.id}`).replace(/<[^>]*>/g, '').slice(0, 60);
          return search.value === `#${task.id} · ${raw}`;
        });
        if (match) {
          select.value = match.id;
          const el = document.querySelector(`.task-item[data-task-id="${match.id}"]`);
          selectTask(match.id, el);
          search.value = "";
          buildOptions(uniqueTasks);
        }
      });

      search._inputListenerAdded = true;
    }
  }

  container.replaceChildren(...uniqueTasks.map(buildTaskEl));
}

// ------------------------------------
// AUTO-RELOAD: poll for new tasks
// ------------------------------------
let _lastTaskCount = 0;
let _lastMaxId = -1;

async function pollTasks() {
  try {
    const [tasksRes, configRes] = await Promise.all([
      fetch("/api/tasks"),
      fetch("/api/config")
    ]);

    if (configRes.ok) {
      const config = await configRes.json();
      const badge = document.getElementById("convIdBadge");
      if (badge && config.conv_id) {
        badge.textContent = config.conv_id;
        badge.title = config.conv_id;
      }
    }

    if (!tasksRes.ok) return;
    const data = await tasksRes.json();

    const maxId = data.reduce((m, t) => Math.max(m, t.id ?? -1), -1);

    if (data.length !== _lastTaskCount || maxId !== _lastMaxId) {
      _lastTaskCount = data.length;
      _lastMaxId = maxId;
      window.agentTasks = data;
      const currentId = Number(document.getElementById("taskSelect")?.value);
      loadAgentTasks();
      // restore previous selection if still valid
      if (currentId && data.some(t => t.id === currentId)) {
        const select = document.getElementById("taskSelect");
        if (select) select.value = currentId;
      }
    }
  } catch (e) {
    // silent — server may be temporarily unavailable
  }
}

window.onload = () => {
  loadMetrics();
  loadNetwork();
  loadAgentTasks();
  setInterval(pollTasks, 5000);
};