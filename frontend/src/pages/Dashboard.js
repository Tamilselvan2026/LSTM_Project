import { useEffect, useState } from "react";
import API from "../services/api";
import DestinationCard from "../components/DestinationCard";

const Dashboard = () => {
  const [destinations, setDestinations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    API.get("/destinations")
      .then((res) => setDestinations(res.data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-6">Loading destinations...</div>;

  return (
    <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
      {destinations.map((dest) => (
        <DestinationCard key={dest.dest_id} dest={dest} />
      ))}
    </div>
  );
};

export default Dashboard;