// Authentication State & Helper Library

const Auth = {
  getToken() {
    return localStorage.getItem("proxyqr_token");
  },

  getUser() {
    const raw = localStorage.getItem("proxyqr_user");
    try {
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },

  setSession(token, user) {
    localStorage.setItem("proxyqr_token", token);
    localStorage.setItem("proxyqr_user", JSON.stringify(user));
  },

  clearSession() {
    localStorage.removeItem("proxyqr_token");
    localStorage.removeItem("proxyqr_user");
  },

  async fetchWithAuth(url, options = {}) {
    const token = this.getToken();
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {})
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const res = await fetch(getApiUrl(url), {
      ...options,
      headers
    });

    if (res.status === 401) {
      // Session expired or invalid
      this.clearSession();
      window.location.href = "/login.html";
      throw new Error("Unauthorized session");
    }

    return res;
  },

  async checkAuth(expectedRole = null) {
    const user = this.getUser();
    const token = this.getToken();

    if (!user || !token) {
      window.location.href = "/login.html";
      return null;
    }

    if (expectedRole && user.role !== expectedRole) {
      if (user.role === "teacher") {
        window.location.href = "/teacher/dashboard.html";
      } else {
        window.location.href = "/student/dashboard.html";
      }
      return null;
    }

    return user;
  },

  async logout() {
    try {
      await fetch(getApiUrl("/api/auth/logout"), { method: "POST" });
    } catch (e) {
      console.warn("Logout error:", e);
    }
    this.clearSession();
    window.location.href = "/login.html";
  }
};
