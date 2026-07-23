import {
  Chart as ChartJS,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
} from "chart.js";
import { Line } from "react-chartjs-2";

ChartJS.register(
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend
);

const DemandChart = ({ data }) => {
  if (!data) return null;

  const chartData = {
    labels: data.months, // Jan–Dec only
    datasets: [
      {
        label: "Historical (Last Year)",
        data: data.historical_inflow,
        borderColor: "#2563eb",
        backgroundColor: "rgba(37, 99, 235, 0.2)",
        borderWidth: 3,
        tension: 0.4,
        pointRadius: 5,
      },
      {
        label: "Forecast (Next Year)",
        data: data.forecast_inflow,
        borderColor: "#16a34a",
        backgroundColor: "rgba(22, 163, 74, 0.2)",
        borderDash: [6, 6],
        borderWidth: 3,
        tension: 0.4,
        pointRadius: 5,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: { display: true },
    },
    scales: {
      y: {
        beginAtZero: false,
      },
    },
  };

  return (
    <div className="bg-white p-6 shadow rounded-lg">
      <Line data={chartData} options={options} />
    </div>
  );
};

export default DemandChart;