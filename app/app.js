let hotspotChart = null;
let interactionNetwork = null;

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

function loadAgentTasks() {
  const container = document.getElementById("taskList");
  const data = window.agentTasks || [];

  if (!container) return;

  if (!data.length) {
    container.innerHTML = '<div class="no-tasks">No tasks tracked yet.</div>';
    return;
  }

  // Deduplication by ID (keep latest)
  const taskMap = new Map();
  data.forEach(task => {
    taskMap.set(task.id, task);
  });

  const uniqueTasks = Array.from(taskMap.values()).sort((a, b) => b.id - a.id);

  container.innerHTML = uniqueTasks.map(task => `
    <div class="task-item fade-in" onclick="selectTask(${task.id}, this)">
      <div class="task-meta">
        <span class="task-id">#${task.id}</span>
        <span class="task-date">${new Date(task.created_at).toLocaleString()}</span>
      </div>
      <div class="task-asked">${task.asked}</div>
      <pre class="task-effectuated">${task.effectuated}</pre>
    </div>
  `).join("");
}

window.onload = () => {
  loadMetrics();
  loadNetwork();
  loadAgentTasks();
};