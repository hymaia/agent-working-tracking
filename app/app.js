function loadMetrics() {

  console.log("Loading metrics...")

  const data = window.metrics || []

  if (!Array.isArray(data) || !data.length) {
    console.warn("No metrics to display")
    return
  }

  console.log("Using server injected metrics:", data.length)

  // transformation des données
  const dataset = data.map(d => ({
    x: Number(d.churn) || 0,          // nombre de modifications
    y: Number(d.complexity) || 0,     // complexité
    filename: d.filename,
    loc: d.loc
  }))

  const ctx = document.getElementById("hotspotChart")

  if (!ctx) {
    console.error("Canvas hotspotChart not found")
    return
  }

  Chart.defaults.color = "#475569";
  Chart.defaults.scale.grid.color = "rgba(0, 0, 0, 0.05)";

  new Chart(ctx, {

    type: "scatter",

    data: {
      datasets: [{
        label: "Value",
        data: dataset,
        pointRadius: 6,
        hoverRadius: 8,
        backgroundColor: "rgba(59, 130, 246, 0.8)", // Blue tint
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
              const d = ctx.raw
              return [
                d.filename,
                `Churn: ${d.x}`,
                `Complexity: ${d.y}`,
                `LOC: ${d.loc}`
              ]
            }
          }
        }
      },

      scales: {

        x: {
          title: {
            display: true,
            text: "Nombre de modifications (Git Churn)"
          }
        },

        y: {
          title: {
            display: true,
            text: "Complexité cyclomatique moyenne"
          }
        }

      }

    }

  })

  console.log("Chart rendered")
}

function loadNetwork() {
  const container = document.getElementById("interactionNetwork");
  const dataRaw = window.graphData;
  
  if (!container || !dataRaw || !dataRaw.nodes || !dataRaw.edges || !dataRaw.nodes.length) {
    console.warn("No graph data to display or container missing");
    return;
  }

  console.log(`Using server injected graph data: ${dataRaw.nodes.length} nodes, ${dataRaw.edges.length} edges`);

  // Parse and color nodes for light theme readability
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
    interaction: {
      dragNodes: true,
      hideEdgesOnDrag: false,
      hideNodesOnDrag: false,
      hover: true
    },
    physics: {
      enabled: true,
      forceAtlas2Based: {
        avoidOverlap: 0.1,
        centralGravity: 0.01,
        damping: 0.4,
        gravitationalConstant: -50,
        springConstant: 0.08,
        springLength: 100
      },
      solver: "forceAtlas2Based",
      stabilization: {
        enabled: true,
        fit: true,
        iterations: 1000,
        updateInterval: 50
      }
    }
  };

  new vis.Network(container, data, options);
  console.log("Network rendered");
}

loadMetrics()
loadNetwork()