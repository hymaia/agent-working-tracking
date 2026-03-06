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

  new Chart(ctx, {

    type: "scatter",

    data: {
      datasets: [{
        label: "Value",
        data: dataset,
        pointRadius: 8,
        backgroundColor: "rgba(220,80,80,0.7)"
      }]
    },

    options: {

      responsive: true,

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

loadMetrics()