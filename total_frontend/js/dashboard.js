const token = localStorage.getItem("access");

if (!token) {
    window.location.href = "index.html";
}

function loadDashboard() {

    fetch(BASE_URL + "/dashboard/live/", {
        headers: {
            "Authorization": "Bearer " + token
        }
    })
    .then(response => {

        if (!response.ok) {
            throw new Error("Unable to load dashboard");
        }

        return response.json();

    })
    .then(data => {

        // ==========================
        // Summary Cards
        // ==========================

        document.getElementById("totalEmployees").textContent =
            data.summary.total_employees;

        document.getElementById("presentToday").textContent =
            data.summary.present_today;

        document.getElementById("insideOffice").textContent =
            data.summary.employees_inside;

        document.getElementById("alertsToday").textContent =
            data.summary.alerts_today;

        document.getElementById("sensorEvents").textContent =
            data.summary.sensor_events_today;


        // ==========================
        // Recent Sensor Events
        // ==========================

        let sensorHtml = "";

        data.recent_sensor_events.forEach(event => {

            sensorHtml += `
                <tr>
                    <td>${event.employee}</td>
                    <td>${event.event}</td>
                    <td>${event.time}</td>
                </tr>
            `;

        });

        document.getElementById("sensorTable").innerHTML = sensorHtml;


        // ==========================
        // Recent Alerts
        // ==========================

        let alertHtml = "";

        data.recent_alerts.forEach(alert => {

            alertHtml += `
                <tr>
                    <td>${alert.employee}</td>
                    <td>${alert.type}</td>
                    <td>${alert.severity}</td>
                </tr>
            `;

        });

        document.getElementById("alertTable").innerHTML = alertHtml;

    })
    .catch(error => {

        console.error("Dashboard Error:", error);

    });

}

// ==========================
// Logout
// ==========================

function logout() {

    localStorage.clear();

    window.location.href = "index.html";

}

// ==========================
// Initial Load
// ==========================

loadDashboard();

// ==========================
// Auto Refresh Every 5 Seconds
// ==========================

setInterval(loadDashboard, 5000);