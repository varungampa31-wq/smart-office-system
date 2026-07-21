const token = localStorage.getItem("access");

if (!token) {
    window.location.href = "index.html";
}

let employeeNamesById = {};

function severityBadgeClass(severity) {
    if (severity === "HIGH") return "bg-danger";
    if (severity === "MEDIUM") return "bg-warning text-dark";
    return "bg-secondary";
}

function formatAlertType(type) {
    return (type || "").replaceAll("_", " ");
}

function loadEmployeeNames() {
    return fetch(BASE_URL + "/employees/", {
        headers: {
            "Authorization": "Bearer " + token
        }
    })
    .then(response => response.json())
    .then(data => {
        employeeNamesById = {};
        data.forEach(employee => {
            employeeNamesById[employee.id] = `${employee.first_name} ${employee.last_name}`;
        });
    })
    .catch(error => {
        console.error("Failed to load employees for alert lookup:", error);
    });
}

function loadAlerts() {

    fetch(BASE_URL + "/alerts/", {
        headers: {
            "Authorization": "Bearer " + token
        }
    })
    .then(response => {

        if (!response.ok) {
            throw new Error("Unable to load alerts");
        }

        return response.json();

    })
    .then(data => {

        const severityFilter = document.getElementById("severityFilter").value;
        const resolvedFilter = document.getElementById("resolvedFilter").value;

        let alerts = data.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

        if (severityFilter) {
            alerts = alerts.filter(alert => alert.severity === severityFilter);
        }

        if (resolvedFilter) {
            const wantResolved = resolvedFilter === "true";
            alerts = alerts.filter(alert => alert.resolved === wantResolved);
        }

        const tableBody = document.getElementById("alertsTable");
        const emptyMessage = document.getElementById("emptyMessage");

        if (alerts.length === 0) {
            tableBody.innerHTML = "";
            emptyMessage.classList.remove("d-none");
            return;
        }

        emptyMessage.classList.add("d-none");

        let html = "";

        alerts.forEach(alert => {

            const employeeName = alert.employee
                ? (employeeNamesById[alert.employee] || `Employee #${alert.employee}`)
                : "System";

            const time = new Date(alert.timestamp).toLocaleString();

            const statusBadge = alert.resolved
                ? `<span class="badge bg-success">Resolved</span>`
                : `<span class="badge bg-secondary">Open</span>`;

            const actionButton = alert.resolved
                ? ""
                : `<button class="btn btn-sm btn-outline-success" onclick="resolveAlert(${alert.id})">Mark Resolved</button>`;

            html += `
            <tr>
                <td>${time}</td>
                <td>${employeeName}</td>
                <td>${formatAlertType(alert.alert_type)}</td>
                <td><span class="badge ${severityBadgeClass(alert.severity)}">${alert.severity}</span></td>
                <td>${alert.description || ""}</td>
                <td>${statusBadge}</td>
                <td>${actionButton}</td>
            </tr>
            `;

        });

        tableBody.innerHTML = html;

    })
    .catch(error => {

        console.error("Alerts Error:", error);

    });

}

function resolveAlert(alertId) {

    fetch(BASE_URL + "/alerts/" + alertId + "/", {
        method: "PATCH",
        headers: {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ resolved: true })
    })
    .then(response => {

        if (!response.ok) {
            throw new Error("Unable to resolve alert");
        }

        return loadAlerts();

    })
    .catch(error => {

        console.error("Resolve Alert Error:", error);

    });

}

function logout() {

    localStorage.clear();

    window.location.href = "index.html";

}

// ==========================
// Initial Load
// ==========================

loadEmployeeNames().then(loadAlerts);

document.getElementById("severityFilter").addEventListener("change", loadAlerts);
document.getElementById("resolvedFilter").addEventListener("change", loadAlerts);

// ==========================
// Auto Refresh Every 5 Seconds
// ==========================

setInterval(loadAlerts, 5000);