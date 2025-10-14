const station = "kbos";
const zipcode = "02139";
const country = "US";
const ow_api_key = "e11595e5e85bcf80302889e0f669b370";

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
    geo_url = "https://api.openweathermap.org/geo/1.0/zip?zip="+zipcode+","+country+"&appid="+ow_api_key;
    let data = (await getFeed(geo_url));
    return [data["lat"], data["lon"]];
    }

async function getOW(zipcode, country, ow_api_key) {
    DEFAULT_MISSING = "--";
    let coords = await getCoords(zipcode, country, ow_api_key);
    aqi_current_url = "https://api.openweathermap.org/data/2.5/air_pollution?lat="+coords[0]+"&lon="+coords[1]+"&appid="+ow_api_key;
        aqi_forecast_url = "https://api.openweathermap.org/data/2.5/air_pollution/forecast?lat="+coords[0]+"&lon="+coords[1]+"&appid="+ow_api_key;
    let r = {};
    r.now = (await getFeed(aqi_current_url))["list"][0]["main"]["aqi"];
    r.co = (await getFeed(aqi_current_url))["list"][0]["components"]["co"];
    r.no = (await getFeed(aqi_current_url))["list"][0]["components"]["no"];
    r.no2 = (await getFeed(aqi_current_url))["list"][0]["components"]["no2"];
    r.o3 = (await getFeed(aqi_current_url))["list"][0]["components"]["o3"];
    r.so2 = (await getFeed(aqi_current_url))["list"][0]["components"]["so2"];
    r.pm2_5 = (await getFeed(aqi_current_url))["list"][0]["components"]["pm2_5"];
    r.pm10 = (await getFeed(aqi_current_url))["list"][0]["components"]["pm10"];
    r.nh3 = (await getFeed(aqi_current_url))["list"][0]["components"]["bh3"];
    r.pred = (await getFeed(aqi_forecast_url))["list"][24]["main"]["aqi"];
    
    const keys = Object.keys(r);
    for (var i = 0; i < keys.length; i++) {
        if (typeof r[keys[i]] !== 'number' || r[keys[i]] === null || r[keys[i]] === undefined) {
            r[keys[i]] = DEFAULT_MISSING;
        }}
    console.log(r);
    return r;
    }

//////////////////////////////////////////////
// Utilities
//////////////////////////////////////////////
function getColor(value, ranges, defaultColor = 'white') {
    // Iterate through the array of range definitions
    for (const range of ranges) {
        // Check if the value is within the defined min and max (inclusive)
        if (value >= range.min && value <= range.max) {
            return range.color; // Return the color for the first matching range
        }
    }
    // If the loop finishes without finding a match, return the default color
    return defaultColor;
}

const aqiColorRanges = [
    { min: 1, max: 1, color: "green" },     // Your original case 1
    { min: 2, max: 2, color: "yellow" },    // Your original case 2
    { min: 3, max: 3, color: "orange" },    // Your original case 3
    { min: 4, max: 4, color: "red" },       // Your original case 4
    { min: 5, max: 5, color: "purple" }     // Your original case 5
];

const coColorRanges = [
    { min: 0, max: 4400, color: "green" },     // Your original case 1
    { min: 4400, max: 9400, color: "yellow" },    // Your original case 2
    { min: 9400, max: 12400, color: "orange" },    // Your original case 3
    { min: 12400, max: 15400, color: "red" },       // Your original case 4
    { min: 15400, max: 1e8, color: "purple" }     // Your original case 5
];

const no2ColorRanges = [
    { min: 0, max: 40, color: "green" },     // Your original case 1
    { min: 40, max: 70, color: "yellow" },    // Your original case 2
    { min: 70, max: 150, color: "orange" },    // Your original case 3
    { min: 150, max: 200, color: "red" },       // Your original case 4
    { min: 200, max: 1e8, color: "purple" }     // Your original case 5
];

const o3ColorRanges = [
    { min: 0, max: 60, color: "green" },     // Your original case 1
    { min: 60, max: 100, color: "yellow" },    // Your original case 2
    { min: 100, max: 140, color: "orange" },    // Your original case 3
    { min: 140, max: 180, color: "red" },       // Your original case 4
    { min: 180, max: 1e8, color: "purple" }     // Your original case 5
];

const so2ColorRanges = [
    { min: 0, max: 20, color: "green" },     // Your original case 1
    { min: 20, max: 80, color: "yellow" },    // Your original case 2
    { min: 80, max: 250, color: "orange" },    // Your original case 3
    { min: 250, max: 350, color: "red" },       // Your original case 4
    { min: 350, max: 1e8, color: "purple" }     // Your original case 5
];

const pm2_5ColorRanges = [
    { min: 0, max: 10, color: "green" },     // Your original case 1
    { min: 10, max: 25, color: "yellow" },    // Your original case 2
    { min: 25, max: 50, color: "orange" },    // Your original case 3
    { min: 50, max: 75, color: "red" },       // Your original case 4
    { min: 75, max: 1e8, color: "purple" }     // Your original case 5
];

const pm10ColorRanges = [
    { min: 0, max: 20, color: "green" },     // Your original case 1
    { min: 20, max: 50, color: "yellow" },    // Your original case 2
    { min: 50, max: 100, color: "orange" },    // Your original case 3
    { min: 100, max: 200, color: "red" },       // Your original case 4
    { min: 200, max: 1e8, color: "purple" }     // Your original case 5
];
    
//////////////////////////////////////////////
// Logic when pushing Update Status button
//////////////////////////////////////////////
async function updateStatus() {
    document.getElementById("Status").value = "Update Status: \n Loading...";
    //document.getElementById("warnLabel").textContent = "Testing";
    
    datetime = getCurrentDateTime();
    nws = await getNWS(station);
    ow = await getOW(zipcode, country, ow_api_key)

    //document.getElementById("door_status").textContent = data.state;
    
    document.getElementById("Status").style.backgroundColor = "navy";

    document.getElementById("station").textContent = nws.stationName;
    document.getElementById("ext_temperature").textContent = nws.temperature+" \u00b0C";
    document.getElementById("ext_RH").textContent = nws.relativeHumidity+" %";
    document.getElementById("ext_aqi").textContent = ow.now;
    document.getElementById("ext_aqi").style.color = getColor(ow.now, aqiColorRanges);
    document.getElementById("ext_next_aqi").textContent = ow.pred;
    document.getElementById("ext_next_aqi").style.color = getColor(ow.pred, aqiColorRanges);
    document.getElementById("ext_co").textContent = ow.co;
    document.getElementById("ext_co").style.color = getColor(ow.co, coColorRanges);
    document.getElementById("ext_no").textContent = ow.no;
    document.getElementById("ext_no2").textContent = ow.no2;
    document.getElementById("ext_no2").style.color = getColor(ow.no2, no2ColorRanges);
    document.getElementById("ext_o3").textContent = ow.o3;
    document.getElementById("ext_o3").style.color = getColor(ow.o3, o3ColorRanges);
    document.getElementById("ext_so2").textContent = ow.so2;
    document.getElementById("ext_so2").style.color = getColor(ow.so2, so2ColorRanges);
    document.getElementById("ext_pm2_5").textContent = ow.pm2_5;
    document.getElementById("ext_pm2_5").style.color = getColor(ow.pm2_5, pm2_5ColorRanges);
    document.getElementById("ext_pm10").textContent = ow.pm10;
    document.getElementById("ext_pm10").style.color = getColor(ow.pm10, pm10ColorRanges);
    document.getElementById("ext_nh3").textContent = ow.nh3;
    
    document.getElementById("ext_pressure").textContent = nws.seaLevelPressure+" mbar";
    //document.getElementById("ext_dewpoint").textContent = data.ext_dewpoint;
    document.getElementById("ext_heatindex").textContent = nws.heatIndex+" \u00b0C";
    document.getElementById("ext_visibility").textContent = nws.visibility+" m";
    document.getElementById("ext_weather").textContent = nws.presentWeather;

    document.getElementById("datetime").textContent = datetime;
    //document.getElementById("ip_address").textContent = data.ip;
    //document.getElementById("version").textContent = data.version;

    //document.getElementById("warnLabel").textContent = "Update Status: \n Ready";
    document.getElementById("Status").value = "Update Status";
    document.getElementById("warnLabel").textContent = "";
    document.getElementById("Status").disabled = false;
}

// Start the status update when the page is fully loaded
document.addEventListener('DOMContentLoaded', updateStatus);
// Optionally, update status every 30 seconds automatically
setInterval(updateStatus, 30000);
