import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:5000",
});

// Attach token automatically
API.interceptors.request.use((req) => {
  const token = localStorage.getItem("token");
  if (token) {
    req.headers.Authorization = `Bearer ${token}`;
  }
  return req;
});

// Auto logout if token expired
API.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export const searchDestinations = async (query) => {
  const res = await fetch(
    `http://localhost:5000/search?q=${query}`
  );
  return res.json();
};

export default API;