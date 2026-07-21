const token = localStorage.getItem("access");

if (!token) {
    window.location.href = "index.html";
}

const rfidInput = document.getElementById("rfidTag");

// Focus the textbox when page loads
window.onload = function () {
    rfidInput.focus();
};

// Scan when Enter key is pressed
rfidInput.addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
        scanRFID();
    }
});

function scanRFID() {

    const rfid = rfidInput.value.trim();

    if (rfid === "") {
        showMessage(
            "warning",
            "Please enter an RFID tag."
        );
        return;
    }

    fetch(BASE_URL + "/scan/rfid/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        },
        body: JSON.stringify({
            rfid_tag: rfid
        })
    })
    .then(response => response.json())
    .then(data => {

        const now = new Date().toLocaleString();

        let color = "secondary";

        if (data.status === "success") {
            color = "success";
        }
        else if (data.status === "warning") {
            color = "warning";
        }
        else if (data.status === "error") {
            color = "danger";
        }

        // The backend only sends "message" for warning/error responses.
        // Successful check-in/check-out replies carry "action" instead,
        // so build a message from that when "message" is missing.
        let message = data.message;
        if (!message) {
            if (data.action === "CHECK_IN") {
                message = "Checked in successfully";
            } else if (data.action === "CHECK_OUT") {
                message = "Checked out successfully";
            } else {
                message = "Scan processed";
            }
        }

        document.getElementById("result").innerHTML = `
            <div class="alert alert-${color}">

                <h4>${icon} ${message}</h4>

                ${data.employee ? `
                <hr>

                <p><strong>Employee ID:</strong> ${data.employee.employee_id}</p>

                <p><strong>Name:</strong> ${data.employee.name}</p>

                <p><strong>Scan Time:</strong> ${now}</p>
                ` : ""}

            </div>
        `;

        // Clear textbox
        rfidInput.value = "";

        // Ready for next scan
        rfidInput.focus();

    })
    .catch(error => {

        console.error(error);

        showMessage(
            "danger",
            "Unable to connect to the server."
        );

        rfidInput.focus();

    });

}

function showMessage(type, message) {

    document.getElementById("result").innerHTML = `
        <div class="alert alert-${type}">
            <h4>${message}</h4>
        </div>
    `;
}

function logout() {

    localStorage.clear();

    window.location.href = "index.html";

}