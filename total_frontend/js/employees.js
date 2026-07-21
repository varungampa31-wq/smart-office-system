const token = localStorage.getItem("access");

if (!token) {
    window.location.href = "index.html";
}

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

        </tr>
        `;

    });

    document.getElementById("employeeTable").innerHTML = html;

});

function logout() {

    localStorage.clear();

    window.location.href = "index.html";

}