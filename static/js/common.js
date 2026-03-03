// static/js/common.js
function sendToFlask(mode, workflow) {
    var inputField = document.getElementById("userInput");
    var input = inputField.value;
    var selectedMode = mode || "analyze";
    var selectedWorkflow = workflow;

    if (input.trim() === "") {
        inputField.focus();
        return;
    }
    inputField.value = "";

    spinner.style.display = "block";
    inputField.disabled = true;

    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/response", true);
    xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");

    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            spinner.style.display = "none";
            inputField.disabled = false;

            if (xhr.status === 200) {
                var data = JSON.parse(xhr.responseText);
                document.getElementById("assistant-output").style.display = "block";
                document.getElementById("response").innerText = data.result;
                var charts = document.getElementById("charts");
                charts.innerHTML = "";

                (data.img_urls || []).forEach(function(src, idx) {
                    var img = document.createElement("img");
                    img.src = src;
                    img.alt = "chart " + (idx + 1);
                    img.style.maxWidth = "100%";
                    img.style.height = "auto";
                    charts.appendChild(img);
                });

                setTimeout(function() {
                    inputField.focus();
                }, 50);
            }
        }
    }

    xhr.send(
        "userInput=" +
            encodeURIComponent(input) +
            "&mode=" +
            encodeURIComponent(selectedMode) +
            "&workflow=" +
            encodeURIComponent(selectedWorkflow)
    );
}

function resetConversation() {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/reset", true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4 && xhr.status === 200) {
            var data = JSON.parse(xhr.responseText);
            document.getElementById("response").innerText = data.message;
            document.getElementById("charts").innerHTML = "";
            document.getElementById("assistant-output").style.display = "none";
        }
    };
    xhr.send();
}
  
