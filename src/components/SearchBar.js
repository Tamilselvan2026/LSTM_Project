import { useState } from "react";
import { useNavigate } from "react-router-dom";

const SearchBar = () => {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  const handleSearch = (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    navigate(`/search?q=${query}`);
  };

  return (
    <form onSubmit={handleSearch} className="flex gap-2">
      <input
        type="text"
        placeholder="Search destinations..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="border px-3 py-1 rounded"
      />
      <button className="bg-blue-500 text-white px-3 rounded">
        Search
      </button>
    </form>
  );
};

export default SearchBar;