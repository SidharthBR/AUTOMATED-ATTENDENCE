// dashboard.js
document.addEventListener("DOMContentLoaded", () => {
  const trainBtn = document.getElementById("trainBtn");
  const trainProgress = document.getElementById("trainProgress");
  const trainMsg = document.getElementById("trainMsg");

  async function pollStatus() {
    try {
      const res = await fetch("/train_status");
      const data = await res.json();
      trainProgress.style.width = data.progress + "%";
      trainProgress.innerText = data.progress + "%";
      trainMsg.innerText = data.message || "";
      return data;
    } catch (e) {
      console.error(e);
      return null;
    }
  }

  trainBtn.addEventListener("click", async () => {
    trainBtn.disabled = true;
    const start = await fetch("/train_model");
    if (!start.ok && start.status !== 202) {
      alert("❌ Neural network initialization failed");
      trainBtn.disabled = false;
      return;
    }
    trainMsg.innerText = "🧠 Neural network training initiated...";
    // poll until progress==100 or not running
    const t = setInterval(async () => {
      const s = await pollStatus();
      if (s && s.progress >= 100) {
        clearInterval(t);
        trainBtn.disabled = false;
        alert("✅ Neural network training completed successfully");
      }
    }, 1500);
  });

  // Chart initial render & update every 10s
  let chart = null;
  async function updateChart() {
    const res = await fetch("/attendance_stats");
    const data = await res.json();
    const ctx = document.getElementById("attendanceChart").getContext("2d");
    if (!chart) {
      chart = new Chart(ctx, {
        type: "bar",
        data: {
          labels: data.dates,
          datasets: [{ 
            label: "Verified Identities", 
            data: data.counts, 
            backgroundColor: "rgba(0, 255, 255, 0.7)",
            borderColor: "rgba(0, 255, 255, 1)",
            borderWidth: 2
          }]
        },
        options: { 
          responsive: true, 
          maintainAspectRatio: false,
          plugins: {
            legend: {
              labels: {
                color: '#00ffff',
                font: {
                  family: 'Orbitron'
                }
              }
            }
          },
          scales: {
            x: {
              ticks: { color: '#e0e6ed' },
              grid: { color: 'rgba(0, 255, 255, 0.1)' }
            },
            y: {
              ticks: { color: '#e0e6ed' },
              grid: { color: 'rgba(0, 255, 255, 0.1)' }
            }
          }
        }
      });
    } else {
      chart.data.labels = data.dates;
      chart.data.datasets[0].data = data.counts;
      chart.update();
    }
  }
  updateChart();
  setInterval(updateChart, 10000);
});
