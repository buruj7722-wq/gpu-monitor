async function loadGPU(){

    const res = await fetch("/api/gpu");
    const gpu = await res.json();

    document.getElementById("gpu-name").innerText = gpu.name;

    document.getElementById("temp").innerText =
        gpu.temperature + "°C";

    document.getElementById("gpu-util").innerText =
        gpu.gpu_util + "%";

    document.getElementById("memory").innerText =
        gpu.memory_used + " / " + gpu.memory_total + " MB";

    document.getElementById("power").innerText =
        gpu.power + " / " + gpu.power_limit + " W";

    document.getElementById("fan").innerText =
        gpu.fan + "%";

    document.getElementById("gpu-bar").style.width =
        gpu.gpu_util + "%";

    const mem =
        (gpu.memory_used / gpu.memory_total) * 100;

    document.getElementById("mem-bar").style.width =
        mem + "%";

    document.getElementById("updated").innerText =
        new Date().toLocaleTimeString();

}


async function loadProcesses(){

    const res = await fetch("/api/processes");

    const data = await res.json();

    let html = "";

    data.forEach(function(p){

        html += `
        <tr>

        <td>${p.pid}</td>

        <td>${p.name}</td>

        <td>${p.memory} MB</td>

        </tr>
        `;

    });

    document.getElementById("processes").innerHTML = html;

}


async function refresh(){

    await loadGPU();

    await loadProcesses();

}

refresh();

setInterval(refresh,1000);
