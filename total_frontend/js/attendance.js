const token = localStorage.getItem("access");

if (!token) {
    window.location.href = "index.html";
}

let attendanceData = [];

function loadAttendance() {

    fetch(BASE_URL + "/attendance/", {
        headers: {
            Authorization: "Bearer " + token
        }
    })
    .then(response => response.json())
    .then(data => {

        attendanceData = data;
        renderTable(data);

    })
    .catch(error => {

        console.error(error);

        alert("Unable to load attendance.");

    });

}

function renderTable(data) {

    let html = "";

    data.forEach(record => {

        const checkIn = record.check_in
            ? new Date(record.check_in).toLocaleString()
            : "-";

        const checkOut = record.check_out
            ? new Date(record.check_out).toLocaleString()
            : "-";

        let badge = "success";

        if (record.status === "Late")
            badge = "warning";

        if (record.status === "Absent")
            badge = "danger";

        html += `

        <tr>

            <td>${record.employee_id}</td>

            <td>${record.employee_name} ${record.employee_last_name}</td>

            <td>${record.date}</td>

            <td>${checkIn}</td>

            <td>${checkOut}</td>

            <td>${record.working_hours}</td>

            <td>

                <span class="badge bg-${badge}">

                    ${record.status}

                </span>

            </td>

        </tr>

        `;

    });

    document.getElementById("attendanceTable").innerHTML = html;

}

document.getElementById("searchBox").addEventListener("keyup", function () {

    const value = this.value.toLowerCase();

    const filtered = attendanceData.filter(record =>

        record.employee_name.toLowerCase().includes(value) ||

        record.employee_last_name.toLowerCase().includes(value) ||

        record.employee_id.toLowerCase().includes(value)

    );

    renderTable(filtered);

});

function logout() {

    localStorage.clear();

    window.location.href = "index.html";

}

loadAttendance();

// Refresh every 10 seconds
setInterval(loadAttendance, 10000);