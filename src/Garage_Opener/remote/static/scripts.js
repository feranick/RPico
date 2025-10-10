function waitWarn(a) {
    // Send request via fetch instead of form submit to prevent full page reload
    //document.getElementById("warnLabel").innerHTML = "Please wait...";
    document.getElementById("Status").disabled = true;
    document.getElementById("Status").style.backgroundColor = "#155084";

    if (a === 0) {
        document.getElementById("Submit").disabled = true;
        document.getElementById("Submit").style.backgroundColor = "#155084";
        // Handle "Run Control" click
        fetch('./run') // Use fetch for the run command
            .then(response => {
                if (response.ok) {
                    console.log("Run control successful.");
                    // Immediately request an update after sending the command
                    // Add a small delay for the physical action to start/stop
                    setTimeout(updateStatus, 1000);
                } else {
                    throw new Error('Run command failed.');
                }
            })
            .catch(error => {
                console.error('Run Error:', error);
                document.getElementById("warnLabel").textContent = "Error during RUN.";
                updateStatus(); // Re-enable buttons
            });
    } else if (a === 1) {
        // Handle "Update Status" click
        updateStatus();
    }
}

function updateStatus() {
    document.getElementById("Submit").value = "Door Status: \n Loading...";
    document.getElementById("Status").value = "Update Status: \n Loading...";
    //document.getElementById("warnLabel").textContent = "Testing";
    fetch('/api/status')
    .then(response => response.json())
    .then(data => {
    console.log(data);

        // 1. Update Door Status and Submit Button
        //document.getElementById("door_status").textContent = data.state;
        document.getElementById("Submit").value = "Door Status: \n" + data.state;
        document.getElementById("Submit").style.backgroundColor = data.button_color;
        document.getElementById("Status").style.backgroundColor = "navy";

        // 2. Update onboard Temperature
        document.getElementById("temp_display").textContent = data.temperature;

        // 3. Update station, external temperature and relative humidity
        document.getElementById("station").textContent = data.station;
        document.getElementById("ext_temperature").textContent = data.ext_temperature;
        document.getElementById("ext_RH").textContent = data.ext_RH;
        document.getElementById("ext_aqi").textContent = data.ext_aqi;
        document.getElementById("ext_aqi").style.color = data.ext_aqi_color;
        document.getElementById("ext_next_aqi").textContent = data.ext_next_aqi;
        document.getElementById("ext_next_aqi").style.color = data.ext_next_aqi_color;
        
        document.getElementById("ext_pressure").textContent = data.ext_pressure;
        //document.getElementById("ext_dewpoint").textContent = data.ext_dewpoint;
        document.getElementById("ext_heatindex").textContent = data.ext_heatindex;
        document.getElementById("ext_visibility").textContent = data.ext_visibility;
        document.getElementById("ext_weather").textContent = data.ext_weather;

        // 4. Update Time, IP and version
        document.getElementById("datetime").textContent = data.datetime;
        document.getElementById("ip_address").textContent = data.ip;
        document.getElementById("version").textContent = data.version;

        // 5. Reset Warning and buttons
        //document.getElementById("warnLabel").textContent = "Update Status: \n Ready";
        document.getElementById("Status").value = "Update Status";
        document.getElementById("warnLabel").textContent = "";
        document.getElementById("Submit").disabled = false;
        document.getElementById("Status").disabled = false;
    })
    .catch(error => {
        console.error('Error fetching status:', error);
        document.getElementById("warnLabel").textContent = "Error: Check connection.";
        // Re-enable buttons even on error, so user can try again
        document.getElementById("Submit").disabled = false;
        document.getElementById("Status").disabled = false;
    });
}

// Start the status update when the page is fully loaded
document.addEventListener('DOMContentLoaded', updateStatus);
// Optionally, update status every 10 seconds automatically
//setInterval(updateStatus, 10000);
