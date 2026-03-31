// static/js/common.js
var hasAnalyzed = false; // make sure this is global

function sendToFlask(mode, workflow) {
    var inputField = document.getElementById("userInput");
    var spinner = document.getElementById("spinner");
    var input = inputField.value.trim();
    var selectedMode = mode || "analyze";
    var selectedWorkflow = workflow;

    if (!input) {
        inputField.focus();
        return;
    }

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

                var responseDiv = document.getElementById("response");

                // User message
                var userMsg = document.createElement("div");
                userMsg.className = "message user";
                userMsg.innerText = input;
                responseDiv.appendChild(userMsg);

                // Assistant wrapper
                var assistantWrapper = document.createElement("div");
                assistantWrapper.className = "message assistant-wrapper";

                // Charts first
                (data.img_urls || []).forEach(function(src, idx) {
                    var img = document.createElement("img");
                    img.src = src;
                    img.alt = "chart " + (idx + 1);
                    img.style.maxWidth = "400px";   // smaller default size
                    img.style.height = "auto";
                    img.style.cursor = "pointer";
                    img.style.marginBottom = "10px";
                    img.style.borderRadius = "8px";
                    img.style.boxShadow = "0 2px 6px rgba(0,0,0,0.1)";

                    // Click to open modal
                    img.onclick = function() {
                        var modal = document.getElementById("imgModal");
                        var modalImg = document.getElementById("modalImg");
                        modal.style.display = "block";
                        modalImg.src = src;
                    };

                    assistantWrapper.appendChild(img);
                });

                // Bot text
                var botMsg = document.createElement("div");
                botMsg.className = "message assistant";
                botMsg.innerText = data.result;
                assistantWrapper.appendChild(botMsg);

                responseDiv.appendChild(assistantWrapper);

                // Scroll to bottom
                responseDiv.scrollTop = responseDiv.scrollHeight;

                // Hide Run Analysis button after first analyze
                if (selectedMode === "analyze" && !hasAnalyzed) {
                    document.getElementById("analyzeBtn").style.display = "none";
                    hasAnalyzed = true;
                }

                inputField.value = "";
                setTimeout(() => inputField.focus(), 50);
            }
        }
    };

    xhr.send(
        "userInput=" + encodeURIComponent(input) +
        "&mode=" + encodeURIComponent(selectedMode) +
        "&workflow=" + encodeURIComponent(selectedWorkflow)
    );
}

// Modal close functionality
var closeBtn = document.getElementById("closeModal");
var modal = document.getElementById("imgModal");

if (closeBtn && modal) {
    closeBtn.onclick = function() {
        modal.style.display = "none";
    };

    modal.onclick = function(e) {
        if (e.target.id === "imgModal") {
            modal.style.display = "none";
        }
    };
}

// Reset conversation function remains unchanged
function resetConversation() {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/reset", true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4 && xhr.status === 200) {
            var data = JSON.parse(xhr.responseText);
            document.getElementById("response").innerText = "";

            var chartsDiv = document.getElementById("charts");
            if (chartsDiv) chartsDiv.innerHTML = "";

            document.getElementById("assistant-output").style.display = "none";
            document.getElementById("analyzeBtn").style.display = "inline-block";
            hasAnalyzed = false;
        }
    };
    xhr.send();
}

// ============================
// Sidebar & Main Content Setup
// ============================
const sidebar = document.querySelector('.sidebar');
const toggleBtn = document.querySelector('.sidebar-toggle');
const mainContent = document.querySelector('.main');

let sidebarPinned = false; // sidebar starts collapsed

// INITIAL STATE: collapsed
sidebar.classList.add('collapsed');
document.body.classList.remove('sidebar-open');
mainContent.style.marginLeft = '0';

// ============================
// FUNCTION: Open sidebar
// ============================
function openSidebar() {
    sidebar.classList.remove('collapsed');
    document.body.classList.add('sidebar-open');
    mainContent.style.transition = 'margin-left 0.3s ease';
    mainContent.style.marginLeft = '240px';
}

// ============================
// FUNCTION: Collapse sidebar
// ============================
function collapseSidebar() {
    sidebar.classList.add('collapsed');
    document.body.classList.remove('sidebar-open');
    mainContent.style.transition = 'margin-left 0.3s ease';
    mainContent.style.marginLeft = '0';
}

// ============================
// TOGGLE: Hamburger click
// ============================
toggleBtn.addEventListener('click', function () {
    sidebarPinned = !sidebarPinned;

    if (sidebarPinned) {
        openSidebar(); // permanently pinned open
    } else {
        collapseSidebar(); // collapses when unpinned
    }
});

// ============================
// HOVER: Temporary open
// ============================
sidebar.addEventListener('mouseenter', function () {
    if (!sidebarPinned) {
        openSidebar(); // temporarily expand
    }
});

sidebar.addEventListener('mouseleave', function () {
    if (!sidebarPinned) {
        collapseSidebar(); // collapse back
    }
});

// ===== Mobile Dropdown Fix =====
window.addEventListener('DOMContentLoaded', () => {
    const arrows = document.querySelectorAll('.dropdown-arrow');

    arrows.forEach(arrow => {
        const dropdown = arrow.closest('.dropdown');
        const menu = dropdown.querySelector('.dropdown-menu');

        arrow.addEventListener('click', e => {
            e.stopPropagation(); // prevent bubbling
            // toggle menu
            if (menu.style.display === 'flex') {
                menu.style.display = 'none';
            } else {
                // close other dropdowns
                document.querySelectorAll('.dropdown-menu').forEach(m => {
                    if (m !== menu) m.style.display = 'none';
                });
                menu.style.display = 'flex';
            }
        });
    });

    // click outside closes dropdowns
    document.addEventListener('click', e => {
        if (!e.target.closest('.dropdown')) {
            document.querySelectorAll('.dropdown-menu').forEach(menu => {
                menu.style.display = 'none';
            });
        }
    });

    // reset on resize
    window.addEventListener('resize', () => {
        if (window.innerWidth >= 768) {
            document.querySelectorAll('.dropdown-menu').forEach(menu => {
                menu.style.display = '';
            });
        } else {
            document.querySelectorAll('.dropdown-menu').forEach(menu => {
                menu.style.display = 'none';
            });
        }
    });
});