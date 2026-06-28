import { useEffect, useState } from "react";
import API from "../services/api";
import DestinationCard from "../components/DestinationCard";

const Recommend = () => {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    API.get("/recommend")
      .then((res) => setRecommendations(res.data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-6">Generating smart recommendations...</div>;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">AI Recommended For You</h1>
      <div className="grid md:grid-cols-3 gap-6">
        {recommendations.map((dest) => (
          <DestinationCard key={dest.dest_id} dest={dest} />
        ))}
      </div>
    </div>
  );
};

export default Recommend;