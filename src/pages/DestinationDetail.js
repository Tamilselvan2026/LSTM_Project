import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import API from "../services/api";
import DemandChart from "../components/DemandChart";
import StarRating from "../components/StarRating";

const DestinationDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const [destination, setDestination] = useState(null);
  const [similar, setSimilar] = useState([]);
  const [demand, setDemand] = useState(null);
  const [rating, setRating] = useState(1);
  const [isFavorite, setIsFavorite] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAll();
  }, [id]);

  const loadAll = async () => {
    try {
      const res = await API.get(`/destination/${id}`);
      setDestination(res.data);

      const demandRes = await API.get(`/demand/${res.data.district}`);
      setDemand(demandRes.data);

      const similarRes = await API.get(`/similar/${id}`);
      setSimilar(similarRes.data);

      const favRes = await API.get("/favorites");
      const exists = favRes.data.find((f) => f.dest_id === id);
      setIsFavorite(!!exists);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const submitRating = async () => {
    try {
      await API.post("/rate", {
        dest_id: id,
        rating: parseInt(rating)
      });
      alert("Rating submitted successfully");
    } catch (err) {
      console.error(err);
    }
  };

  const toggleFavorite = async () => {
    try {
      if (isFavorite) {
        await API.delete(`/favorite/${id}`);
        setIsFavorite(false);
      } else {
        await API.post("/favorite", { dest_id: id });
        setIsFavorite(true);
      }
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) return <div className="p-6">Loading...</div>;
  if (!destination) return <div className="p-6">Destination not found</div>;

  return (
    <div className="p-6 max-w-5xl mx-auto">

      {/* Image */}
      {destination.image_url && (
        <img
          src={`/${destination.image_url}`}
          alt={destination.name}
          className="w-full h-96 object-cover rounded-xl shadow-md"
          onError={(e) => (e.target.src = "/default.jpg")}
        />
      )}

      {/* Title Section */}
      <div className="flex justify-between items-center mt-6">
        <div>
          <h1 className="text-3xl font-bold">
            {destination.name}
          </h1>
          <p className="text-gray-500 mt-1">
            {destination.district}
          </p>
          <p className="text-blue-600 text-sm mt-1">
            {destination.category}
          </p>
        </div>

        <button
          onClick={toggleFavorite}
          className="text-3xl transition transform hover:scale-110"
        >
          {isFavorite ? (
            <span className="text-red-500">❤️</span>
          ) : (
            <span className="text-gray-400">🤍</span>
          )}
        </button>
      </div>

      {/* Average Rating Display */}
      <div className="mt-4 flex items-center gap-3">
        <span className="text-yellow-500 font-semibold text-lg">
          ⭐ {destination.average_rating || 0}
        </span>
        <span className="text-gray-400 text-sm">
          Average User Rating
        </span>
      </div>

      {/* Description */}
      <p className="mt-6 text-gray-700 leading-relaxed">
        {destination.description}
      </p>

      {/* ⭐ Rate Section */}
      <div className="mt-10">
        <h2 className="font-semibold mb-3 text-lg">
          Rate this destination
        </h2>

        <StarRating rating={rating} setRating={setRating} />

        <button
          onClick={submitRating}
          className="bg-blue-600 text-white px-4 py-2 rounded mt-4 hover:bg-blue-700 transition"
        >
          Submit Rating
        </button>
      </div>

      {/* 📊 Demand Chart */}
      {demand && (
        <div className="mt-12">
          <h2 className="font-semibold mb-3 text-lg">
            Predicted Next Month Tourist Inflow
          </h2>
          <DemandChart data={demand} />
        </div>
      )}

      {/* 🔁 Similar Destinations */}
      <h2 className="text-xl font-semibold mt-14">
        Similar Destinations
      </h2>

      <div className="grid md:grid-cols-3 gap-6 mt-4">
        {similar.map((s) => (
          <div
            key={s.dest_id}
            onClick={() => navigate(`/destination/${s.dest_id}`)}
            className="bg-white rounded-xl shadow-md overflow-hidden cursor-pointer hover:shadow-xl transition"
          >
            <img
              src={s.image_url ? `/${s.image_url}` : "/default.jpg"}
              alt={s.name}
              className="w-full h-40 object-cover"
              onError={(e) => (e.target.src = "/default.jpg")}
            />
            <div className="p-4">
              <p className="font-bold">{s.name}</p>
              <p className="text-sm text-gray-500">{s.district}</p>
              <p className="text-yellow-500 text-sm mt-1">
                ⭐ {s.average_rating || 0}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default DestinationDetail;