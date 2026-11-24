# ProxyQR - Real-Time Dynamic Attendance Management System

A web-based application for automated, real-time, and secure classroom attendance tracking using 15-second dynamic, rotating QR codes to completely eliminate proxy attendance.

---

## 🚀 Key Features

* **Anti-Proxy Dynamic QR Generation:** Refreshes automatically every 15 seconds with a new cryptographic security token and a 5-second grace window, making screenshots and remote sharing useless.
* **Role-Based Portals:**
  * **Student Portal:** In-browser smartphone camera scanner (`html5-qrcode`), subject-wise attendance percentage tracking, defaulter (< 75%) warning badges, and attendance log history.
  * **Faculty Portal:** Course management, lecture session launcher, dedicated full-screen Projector Mode with live countdown ring and real-time student check-in feed, manual override, and CSV report export.
* **Security & Constraints:**
  * JWT (JSON Web Tokens) with secure HTTP-only cookies and bcrypt password hashing.
  * Enforces unique constraint on `(session_id, student_id)` to prevent double submissions.
  * Strict enrollment checks to prevent unauthorized scanning.

---

## 🔑 Demo Credentials (Pre-seeded)

### Faculty Accounts (Password: `Faculty@123`)
* **Prof. Abhijeet Kushawah:** `abhijeet@college.edu` (Teaches Operating Systems & DBMS)
* **Dr. Priya Sharma:** `priya@college.edu` (Teaches Computer Networks)

### Student Accounts (Password: `Student@123`)
* **Rajpreet Singh:** Roll `251620101035` (`rajpreet@college.edu`)
* **Arvind Verma:** Roll `251620101008` (`arvind@college.edu`)
* **Sneha Kapoor:** Roll `251620101012` (`sneha@college.edu`)
* **Rohan Mehta:** Roll `251620101020` (`rohan@college.edu`)
* **Ananya Gupta:** Roll `251620101044` (`ananya@college.edu`)

*(Quick Demo buttons on the login page will automatically autofill any of these credentials with one click).*

---

## 💻 Local Setup & Running

1. **Activate Virtual Environment:**
   ```powershell
   .\venv\Scripts\activate
   ```
2. **Run Server:**
   ```powershell
   python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```
   *Or simply double-click `run.bat`.*
3. **Open in Browser:**
   Visit `http://localhost:8000` to access the login page.

---

## 🌐 Netlify Deployment Guide

The frontend is completely decoupled in the `frontend/` directory and pre-configured for Netlify:

1. **Frontend on Netlify:**
   * Publish directory: `frontend`
   * In `frontend/js/config.js`, set `CONFIG.API_BASE` to your deployed backend URL.
   * Netlify automatically provisions free HTTPS, allowing smartphone browsers to use the camera without security blocks.
2. **Backend on Render / Railway / Fly.io:**
   * Deploy the Python backend with `uvicorn backend.main:app --host 0.0.0.0 --port 10000`.
