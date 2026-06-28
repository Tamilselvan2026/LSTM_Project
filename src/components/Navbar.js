import { Link, useNavigate } from "react-router-dom";
import { useContext } from "react";
import { AuthContext } from "../context/AuthContext";
import SearchBar from "./SearchBar";
// import logo from "../components/assets/logo.png";
const Navbar = () => {
  const { logout } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="bg-white shadow-md px-6 py-4 flex items-center justify-between">

      <h1
        className="text-xl font-bold text-blue-600 cursor-pointer"
        onClick={() => navigate("/dashboard")}
      >
        TourMate
      </h1>
      {/* LEFT : LOGO */}
{/* <img
  src={logo}
  alt="TourMate Logo"
  className="h-12 w-auto cursor-pointer"
  onClick={() => navigate("/dashboard")}
/> */}

      {/* CENTER : SEARCH BAR */}
      <div className="w-1/3">
        <SearchBar />
      </div>

      {/* RIGHT : NAV LINKS */}
      <div className="flex items-center gap-6 font-hard">
        <Link to="/dashboard" className="hover:text-blue-600">
          Dashboard
        </Link>
        <Link to="/recommend" className="hover:text-blue-600">
          Recommend
        </Link>
        <Link to="/favorites" className="hover:text-blue-600">
          Favorites
        </Link>
        <Link to="/analytics" className="hover:text-blue-600">
          Analytics
        </Link>
        <Link to="/profile" className="hover:text-blue-600">
          Profile
        </Link>

        <button
          onClick={handleLogout}
          className="text-red-500 hover:text-red-700"
        >
          Logout
        </button>
      </div>

    </nav>
  );
};

export default Navbar;