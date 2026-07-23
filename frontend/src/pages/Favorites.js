import { useEffect, useState } from "react";
import API from "../services/api";
import DestinationCard from "../components/DestinationCard";

const Favorites = () => {
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFavorites();
  }, []);

  const loadFavorites = async () => {
    try {
      const res = await API.get("/favorites");
      setFavorites(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-6">Loading favorites...</div>;

  if (favorites.length === 0)
    return <div className="p-6 text-gray-500">No favorites yet.</div>;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">My Favorites</h1>

      <div className="grid md:grid-cols-3 gap-6">
        {favorites.map((dest) => (
          <DestinationCard key={dest.dest_id} dest={dest} />
        ))}
      </div>
    </div>
  );
};

export default Favorites;