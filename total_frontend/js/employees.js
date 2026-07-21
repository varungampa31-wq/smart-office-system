const token = localStorage.getItem("access");

if (!token) {
    window.location.href = "index.html";
}

function loadEmployees() {

    fetch(BASE_URL + "/employees/", {
        headers: {
            "Authorization": "Bearer " + token
        }
    })
    .then(response => response.json())
    .then(data => {

        let html = "";

        data.forEach(employee => {

            html += `
            <tr>

                <td>${employee.employee_id}</td>

                <td>${employee.first_name} ${employee.last_name}</td>

                <td>${employee.email}</td>

                <td>${employee.department}</td>

                <td>${employee.is_active ? "Active" : "Inactive"}</td>

                <td>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteEmployee(${employee.id}, '${employee.first_name} ${employee.last_name}')">
                        Delete
                    </button>
                </td>

            </tr>
            `;

        });

        document.getElementById("employeeTable").innerHTML = html;

    });

}

function deleteEmployee(id, name) {

    if (!confirm(`Delete ${name}? This cannot be undone.`)) {
        return;
    }

    fetch(BASE_URL + "/employees/" + id + "/", {
        method: "DELETE",
        headers: {
            "Authorization": "Bearer " + token
        }
    })
    .then(response => {

        if (!response.ok && response.status !== 204) {
            throw new Error("Delete failed");
        }

        loadEmployees();

    })
    .catch(error => {

        console.error("Delete employee error:", error);
        alert("Could not delete this employee. Check the console for details.");

    });

}

function logout() {

    localStorage.clear();

    window.location.href = "index.html";

}

// ==========================
// Add employee
// ==========================

document.getElementById("addEmployeeForm").addEventListener("submit", function (e) {

    e.preventDefault();

    console.log("Add employee form submitted");

    const errorBox = document.getElementById("addEmployeeError");
    errorBox.classList.add("d-none");
    errorBox.innerHTML = "";

    const payload = {
        employee_id: document.getElementById("employeeId").value.trim(),
        first_name: document.getElementById("firstName").value.trim(),
        last_name: document.getElementById("lastName").value.trim(),
        email: document.getElementById("email").value.trim(),
        department: document.getElementById("department").value,
        rfid_tag: document.getElementById("rfidTag").value.trim()
    };

    console.log("Payload:", payload);

    fetch(BASE_URL + "/employees/", {
        method: "POST",
        headers: {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    })
    .then(async response => {

        console.log("Response status:", response.status);

        const data = await response.json();

        if (!response.ok) {
            throw data;
        }

        return data;

    })
    .then(() => {

        document.getElementById("addEmployeeForm").reset();

        const modalEl = document.getElementById("addEmployeeModal");
        bootstrap.Modal.getInstance(modalEl).hide();

        loadEmployees();

    })
    .catch(errors => {

        console.error("Add employee error:", errors);

        const messages = Object.entries(errors)
            .map(([field, msgs]) => `${field}: ${Array.isArray(msgs) ? msgs.join(", ") : msgs}`)
            .join("<br>");

        errorBox.innerHTML = messages || "Something went wrong. Please check the form and try again.";
        errorBox.classList.remove("d-none");

    });

});

// ==========================
// Initial load
// ==========================

loadEmployees();