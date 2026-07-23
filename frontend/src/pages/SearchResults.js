import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { searchDestinations } from "../services/api";
import DestinationCard from "../components/DestinationCard";

const SearchResults = () => {
  const [results, setResults] = useState([]);
  const query = new URLSearchParams(useLocation().search).get("q");

  useEffect(() => {
    const fetchResults = async () => {
      const data = await searchDestinations(query);
      setResults(data);
    };
    if (query) fetchResults();
  }, [query]);

  return (
    <div className="p-6">
      <h2 className="text-xl font-bold mb-4">
        Search Results for "{query}"
      </h2>

      <div className="grid grid-cols-3 gap-4">
        {results.map((dest) => (
          <DestinationCard key={dest.dest_id} dest={dest} />
        ))}
      </div>
    </div>
  );
};

export default SearchResults;