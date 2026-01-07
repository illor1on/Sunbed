import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";
import "./app/api/interceptors";
import "./app/owner/owner.css";


import { AuthProvider } from "./app/auth/AuthContext";

import { CityProvider } from "./app/city/CityContext";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AuthProvider>
      <CityProvider>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </CityProvider>
    </AuthProvider>
  </React.StrictMode>
);
