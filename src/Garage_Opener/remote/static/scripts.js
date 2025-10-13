////////////////////////////////////
// Get feed from DB - generic
////////////////////////////////////
async function getFeed(url) {
    const res = await fetch(url);
    const obj = await res.json();
    return obj;
    }

////////////////////////////////////
// Get and format Date and Time
////////////////////////////////////
function getCurrentDateTime() {
    function get_dig(a) {
        if (a<10) {
            secs = "0"+a;}
        else {
            secs = a;}
        return secs;}
        
    let now = new Date();
    month = now.getMonth()+1
    day = now.getDate()
    year = now.getFullYear()
    hours = get_dig(now.getHours())
    minutes = get_dig(now.getMinutes())
    
    if (now.getSeconds()<10) {
        secs = "0"+now.getSeconds();}
    else {
        secs = now.getSeconds();}
        
    formattedTime = hours +":"+minutes+":"+secs;
    formattedDate = month+"/"+day+"/"+year;
    console.log(formattedDate);
    return formattedDate+"      "+formattedTime;
    }

////////////////////////////////////
// Get NWS data
////////////////////////////////////
async function getNWS(station) {
    nws_url = "https://api.weather.gov/stations/"+station+"/observations/latest/";
    let data = (await getFeed(nws_url));
    let r = {};
    
    let keys = [
            'temperature',
            'heatIndex',
            'relativeHumidity',
            'seaLevelPressure',
            'dewpoint',
            'visibility',
        ];
        
    DEFAULT_MISSING = "--";
    let full_defaults_list = [DEFAULT_MISSING] * keys.length;
        
    let formats_map = {
            'temperature': 1,
            'heatIndex': 1,
            'relativeHumidity': 0,
            'seaLevelPressure': 0,
            'dewpoint': 1,
            'visibility': 0,
        };
    
    let units_map = {
            'temperature': 1,
            'heatIndex': 1,
            'relativeHumidity': 1,
            'seaLevelPressure': 100,
            'dewpoint': 1,
            'visibility': 1,
        };
    
    for (var i = 0; i < keys.length; i++) {
        var format_str = formats_map[keys[i]];
        var units_str = units_map[keys[i]];
        var d = data['properties'][keys[i]]['value'];
        if (typeof d === 'number' && d !== null && d !== undefined) {
            r[keys[i]] = (d/units_str).toFixed(format_str);}
        else{
            r[keys[i]] = DEFAULT_MISSING;
        }}
        
    r['stationName'] = data['properties']['stationName'];
    let weather_list = data['properties']['presentWeather'];

    if (weather_list && weather_list.length > 0) {
        weather_value = weather_list[0]['weather'];
            if (weather_value != null) {
                r['weather'] = weather_value;
                }
            else {
                r['weather'] = DEFAULT_MISSING;
                }
        }
    return r;
    }

//////////////////////////////////////////////
// Ger OpenWeather location and weather data
//////////////////////////////////////////////
async function getCoords(zipcode, country, ow_api_key) {
    geo_url = "http://api.openweathermap.org/geo/1.0/zip?zip="+zipcode+","+country+"&appid="+ow_api_key;
    let data = (await getFeed(geo_url));
    return [data["lat"], data["lon"]];
    }

async function getOW(zipcode, country, ow_api_key) {
    let coords = await getCoords(zipcode, country, ow_api_key);
    aqi_current_url = "http://api.openweathermap.org/data/2.5/air_pollution?lat="+coords[0]+"&lon="+coords[1]+"&appid="+ow_api_key;
        aqi_forecast_url = "http://api.openweathermap.org/data/2.5/air_pollution/forecast?lat="+coords[0]+"&lon="+coords[1]+"&appid="+ow_api_key;
    let r = {};
    r.now = (await getFeed(aqi_current_url))["list"][0]["main"]["aqi"];
    r.pred = (await getFeed(aqi_forecast_url))["list"][24]["main"]["aqi"];
    
    return r;
    }

//////////////////////////////////////////////
// Ger Local Data from Pico
//////////////////////////////////////////////
async function fetchLocalData() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        //console.log("Using data inside the async function:", data);
        return data;
        
    } catch (error) {
        console.error('Error fetching status:', error);
        document.getElementById("warnLabel").textContent = "Error: Check connection.";
        // Re-enable buttons even on error, so user can try again
        document.getElementById("Submit").disabled = false;
        document.getElementById("Status").disabled = false;
    }
}

//////////////////////////////////////////////
// Utilities
//////////////////////////////////////////////
//Determine color of font for AQI text
function colAqi(aqi) {
    let col;
    
    switch (aqi) {
        case 1:
            col = "green";
            break;
        case 2:
            col = "yellow";
            break;
        case 3:
            col = "orange";
            break;
        case 4:
            col = "red";
            break;
        case 5:
            col = "purple";
            break;
        default:
            col = "white";
            break;
    }
    return col;
}
    
//////////////////////////////////////////////
// Logic when pushing Update Status button
//////////////////////////////////////////////
async function updateStatus() {
    document.getElementById("Submit").value = "Door Status: \n Loading...";
    document.getElementById("Status").value = "Update Status: \n Loading...";
    //document.getElementById("warnLabel").textContent = "Testing";
    
    datetime = getCurrentDateTime();
    data = await fetchLocalData();
    nws = await getNWS(data.station);
    ow = await getOW(data.zipcode, data.country, data.ow_api_key)

    //document.getElementById("door_status").textContent = data.state;
    document.getElementById("Submit").value = "Door Status: \n" + data.state;
    document.getElementById("Submit").style.backgroundColor = data.button_color;
    document.getElementById("Status").style.backgroundColor = "navy";

    document.getElementById("temp_display").textContent = data.temperature;

    document.getElementById("station").textContent = nws.stationName;
    document.getElementById("ext_temperature").textContent = nws.temperature+" \u00b0C";
    document.getElementById("ext_RH").textContent = nws.relativeHumidity+" %";
    document.getElementById("ext_aqi").textContent = ow.now;
    document.getElementById("ext_aqi").style.color = colAqi(ow.now);
    document.getElementById("ext_next_aqi").textContent = ow.pred;
    document.getElementById("ext_next_aqi").style.color = colAqi(ow.pred);
        
    document.getElementById("ext_pressure").textContent = nws.seaLevelPressure+" mbar";
    //document.getElementById("ext_dewpoint").textContent = data.ext_dewpoint;
    document.getElementById("ext_heatindex").textContent = nws.heatIndex+" \u00b0C";
    document.getElementById("ext_visibility").textContent = nws.visibility+" m";
    document.getElementById("ext_weather").textContent = nws.presentWeather;

    document.getElementById("datetime").textContent = datetime;
    document.getElementById("ip_address").textContent = data.ip;
    document.getElementById("version").textContent = data.version;

    //document.getElementById("warnLabel").textContent = "Update Status: \n Ready";
    document.getElementById("Status").value = "Update Status";
    document.getElementById("warnLabel").textContent = "";
    document.getElementById("Submit").disabled = false;
    document.getElementById("Status").disabled = false;
}

//////////////////////////////////////////////
// Logic when pushing Door Status
//////////////////////////////////////////////
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

// Start the status update when the page is fully loaded
document.addEventListener('DOMContentLoaded', updateStatus);
// Optionally, update status every 30 seconds automatically
setInterval(updateStatus, 30000);
