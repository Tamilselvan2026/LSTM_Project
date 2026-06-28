import { useNavigate } from "react-router-dom";

const DestinationCard = ({ dest }) => {
  const navigate = useNavigate();

  // ✅ correct public path usage
  const imageSrc = dest.image_url
    ? `/${dest.image_url}`
    : "/default.jpg";

  return (
    <div
      onClick={() => navigate(`/destination/${dest.dest_id}`)}
      className="bg-white rounded-xl shadow-md overflow-hidden cursor-pointer hover:shadow-lg transition"
    >
      <img
        src={imageSrc}
        alt={dest.name}
        className="w-full h-48 object-cover"
        loading="lazy"
        onError={(e) => {
          e.target.src = "/default.jpg";
        }}
      />
      <div className="p-4">
        <h3 className="text-lg font-semibold">{dest.name}</h3>
        <p className="text-sm text-gray-500">
          {dest.district} • {dest.category}
        </p>
        <p className="text-yellow-500 mt-2">
          ⭐ {dest.average_rating || 0}
        </p>
      </div>
    </div>
  );
};

export default DestinationCard;