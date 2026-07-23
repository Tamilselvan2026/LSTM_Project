import { useEffect, useState } from "react";
import API from "../services/api";

const Analytics = () => {
  const [districts, setDistricts] = useState([]);

  useEffect(() => {
    API.get("/analytics/top-districts")
      .then(res => setDistricts(res.data));
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Top Districts</h1>
      {districts.map(d => (
        <div key={d.district} className="bg-white p-4 shadow mb-3">
          <p className="font-bold">{d.district}</p>
          <p>Total Inflow: {d.total_inflow}</p>
        </div>
      ))}
    </div>
  );
};

export default Analytics;