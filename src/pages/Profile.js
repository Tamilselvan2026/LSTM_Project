import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../services/api";
import DestinationCard from "../components/DestinationCard";

const Profile = () => {
  const [profile, setProfile] = useState(null);
  const [history, setHistory] = useState([]);
  const [editMode, setEditMode] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadProfile();
    loadHistory();
  }, []);

  const loadProfile = async () => {
    try {
      const res = await API.get("/profile");
      setProfile(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadHistory = async () => {
    try {
      const res = await API.get("/history");
      setHistory(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const updateProfile = async () => {
    try {
      await API.put("/profile/update", profile);
      alert("Profile updated");
      setEditMode(false);
    } catch (err) {
      console.error(err);
    }
  };

  const deleteAccount = async () => {
    if (!window.confirm("Are you sure? This action cannot be undone."))
      return;

    try {
      await API.delete("/profile/delete");
      localStorage.clear();
      navigate("/login");
    } catch (err) {
      console.error(err);
    }
  };

  const removeHistory = async (dest_id) => {
    try {
      await API.delete(`/history/${dest_id}`);
      setHistory(history.filter((h) => h.dest_id !== dest_id));
    } catch (err) {
      console.error(err);
    }
  };

  if (!profile) return <div className="p-6">Loading profile...</div>;

  return (
    <div className="p-6 max-w-5xl mx-auto">

      {/* PROFILE INFO */}
      <div className="bg-white shadow rounded-xl p-6 mb-8">
        <h1 className="text-2xl font-bold mb-4">My Profile</h1>

        {editMode ? (
          <>
            <input
              className="border p-2 w-full mb-3"
              value={profile.username}
              onChange={(e) =>
                setProfile({ ...profile, username: e.target.value })
              }
            />
            <input
              className="border p-2 w-full mb-3"
              value={profile.email}
              onChange={(e) =>
                setProfile({ ...profile, email: e.target.value })
              }
            />
            <button
              onClick={updateProfile}
              className="bg-blue-600 text-white px-4 py-2 rounded mr-3"
            >
              Save
            </button>
            <button
              onClick={() => setEditMode(false)}
              className="text-gray-500"
            >
              Cancel
            </button>
          </>
        ) : (
          <>
            <p><strong>User ID:</strong> {profile.user_id}</p>
            <p><strong>Username:</strong> {profile.username}</p>
            <p><strong>Email:</strong> {profile.email}</p>

            <button
              onClick={() => setEditMode(true)}
              className="mt-4 bg-gray-800 text-white px-4 py-2 rounded mr-3"
            >
              Edit Profile
            </button>

            <button
              onClick={deleteAccount}
              className="mt-4 bg-red-600 text-white px-4 py-2 rounded"
            >
              Delete Account
            </button>
          </>
        )}
      </div>

      {/* HISTORY SECTION */}
      <div>
        <h2 className="text-xl font-semibold mb-4">
          Visited / Rated Destinations
        </h2>

        {history.length === 0 ? (
          <p className="text-gray-500">No activity yet.</p>
        ) : (
          <div className="grid md:grid-cols-3 gap-6">
            {history.map((item) => (
              <div key={item.dest_id} className="relative">
                
                <DestinationCard dest={item} />

                <button
                  onClick={() => removeHistory(item.dest_id)}
                  className="absolute top-3 right-3 bg-red-500 text-white px-2 py-1 text-xs rounded"
                >
                  Remove
                </button>

                {item.user_rating && (
                  <p className="text-sm text-blue-600 mt-2">
                    Your Rating: ⭐ {item.user_rating}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
};

export default Profile;