// ====== FLOATCHAT CHATBOX ======
const btn = document.getElementById("floatchat-btn");
const glassSurfaceContainer = document.getElementById("glass-surface-container");
const closeBtn = document.getElementById("close-chat");
const sendBtn = document.getElementById("send-btn");
const input = document.getElementById("chat-input");
const messages = document.getElementById("chatbox-messages");

// NEW: State variable to hold the name of the currently selected float
let selectedFloatName = null;

btn.addEventListener("click", () => {
    glassSurfaceContainer.style.display = "flex";
    setTimeout(() => {
        glassSurfaceContainer.classList.add('active');
        updateDisplacementMap();
    }, 10);
});

closeBtn.addEventListener("click", () => {
    glassSurfaceContainer.classList.remove('active');
    setTimeout(() => {
        glassSurfaceContainer.style.display = "none";
    }, 500);
});

sendBtn.addEventListener("click", (e) => {
    e.preventDefault(); 
    sendMessage();
});

input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        e.preventDefault(); 
        sendMessage();
    }
});

async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;


    const userMsg = document.createElement("div");
    userMsg.classList.add("user-message");
    userMsg.textContent = text;
    messages.appendChild(userMsg);
    input.value = "";
    messages.scrollTop = messages.scrollHeight;

    // 2. Create a placeholder for the bot's response
    const botMsg = document.createElement("div");
    botMsg.classList.add("bot-message");
    botMsg.innerHTML = '<span class="thinking"></span>'; // "Thinking" indicator
    messages.appendChild(botMsg);
    messages.scrollTop = messages.scrollHeight;

    // 3. Send the message to the backend server
    try {
        const response = await fetch('http://127.0.0.1:5000/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            // MODIFIED: Send both the message and the selected float name
            body: JSON.stringify({
                message: text,
                selected_float: selectedFloatName
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // MODIFIED: Use .innerHTML to correctly render the formatted table from the backend
        botMsg.innerHTML = data.response;

    } catch (error) {
        console.error("Error fetching from backend:", error);
        botMsg.textContent = "Sorry, I'm having trouble connecting to my brain right now. Please try again later.";
    }

    // 5. Ensure the chat is scrolled to the latest message
    messages.scrollTop = messages.scrollHeight;
}

// ====== FLOATCHAT CHATBOX ======
// ... (keep all the code before sendMessage the same)
/*
async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    const userMsg = document.createElement("div");
    userMsg.classList.add("user-message");

    const userContent = document.createElement("div");
    userContent.classList.add("message-content");
    userContent.textContent = text;
    userMsg.appendChild(userContent);

    const userTime = document.createElement("div");
    userTime.classList.add("message-time");
    const nowUser = new Date();
    userTime.textContent = nowUser.getHours().toString().padStart(2, '0') + ':' + nowUser.getMinutes().toString().padStart(2, '0');
    userMsg.appendChild(userTime);

    messages.appendChild(userMsg);
    input.value = "";
    messages.scrollTop = messages.scrollHeight;

    const botMsg = document.createElement("div");
    botMsg.classList.add("bot-message");
    const botContent = document.createElement("div");
    botContent.classList.add("message-content");
    botContent.innerHTML = '<span class="thinking"></span>';
    botMsg.appendChild(botContent);
    messages.appendChild(botMsg);
    messages.scrollTop = messages.scrollHeight;

    try {
        const response = await fetch('http://127.0.0.1:5000/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: text,
                selected_float: selectedFloatName
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        botContent.innerHTML = data.response;

        const botTime = document.createElement("div");
        botTime.classList.add("message-time");
        const nowBot = new Date();
        botTime.textContent = nowBot.getHours().toString().padStart(2, '0') + ':' + nowBot.getMinutes().toString().padStart(2, '0');
        botMsg.appendChild(botTime);


    } catch (error) {
        console.error("Error fetching from backend:", error);
        botContent.textContent = "Sorry, I'm having trouble connecting to my brain right now. Please try again later.";
    }

    messages.scrollTop = messages.scrollHeight;
}
*/
// ... (keep all the code after sendMessage the same)






// ====== MAP SETUP WITH FLOATS ======
const map = L.map("mapid", { zoomControl: false }).setView([15, 80], 5);
L.control.zoom({ position: "bottomleft" }).addTo(map);

let searchMarker;

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 18,
}).addTo(map);

const oceanFloats = [
    { name: "Gujarat Coast Float", coords: [21.0, 67.5] },
    { name: "Konkan Coast Float", coords: [16.5, 71.5] },
    { name: "Malabar Coast Float", coords: [9.0, 74.5] },
    { name: "Coromandel Coast Float", coords: [15.0, 83.5] },
    { name: "Andaman Sea Float", coords: [12.0, 94.0] },
];

oceanFloats.forEach((float) => {
    L.circle(float.coords, { radius: 200000, color: "#3498db", fillColor: "#3498db", fillOpacity: 0.15, weight: 1 }).addTo(map);
    const innerPoint = L.circleMarker(float.coords, { radius: 10, color: "#ffffff", weight: 2, fillColor: "#2980b9", fillOpacity: 1 }).addTo(map);
    innerPoint.bindPopup(`<b>${float.name}</b>`);

    // MODIFIED: Add logic to update the selected float name on click
    innerPoint.on("click", () => {
        map.flyTo(float.coords, 7);
        selectedFloatName = float.name; // Update the state variable

        // Optional but recommended: Give the user feedback in the chat
        const botMsg = document.createElement("div");
        botMsg.classList.add("bot-message", "system-notification"); // Add a new class for styling
        botMsg.textContent = `Now chatting about: ${float.name}. Ask me a question about it!`;
        messages.appendChild(botMsg);
        messages.scrollTop = messages.scrollHeight;
    });
});

// ====== SEARCH AUTOCOMPLETE ======
const searchInput = document.getElementById("location-search");
const suggestionsList = document.getElementById("suggestions");

searchInput.addEventListener("input", () => {
    const value = searchInput.value.toLowerCase();
    suggestionsList.innerHTML = "";
    if (!value) {
        suggestionsList.style.display = "none";
        return;
    }
    const filtered = oceanFloats.filter((ocean) => ocean.name.toLowerCase().includes(value));
    filtered.forEach((ocean) => {
        const li = document.createElement("li");
        li.textContent = ocean.name;
        li.addEventListener("click", () => {
            map.flyTo(ocean.coords, 7);
            if (searchMarker) map.removeLayer(searchMarker);
            searchMarker = L.marker(ocean.coords).addTo(map).bindPopup(ocean.name).openPopup();
            suggestionsList.style.display = "none";
            searchInput.value = ocean.name;

            // NEW: Also set the float context when selecting from search
            selectedFloatName = ocean.name;
            const botMsg = document.createElement("div");
            botMsg.classList.add("bot-message", "system-notification");
            botMsg.textContent = `Now chatting about: ${ocean.name}. Ask me a question about it!`;
            messages.appendChild(botMsg);
            messages.scrollTop = messages.scrollHeight;
        });
        suggestionsList.appendChild(li);
    });
    suggestionsList.style.display = filtered.length ? "block" : "none";
});

document.addEventListener("click", (e) => {
    if (!searchInput.contains(e.target) && !suggestionsList.contains(e.target)) {
        suggestionsList.style.display = "none";
    }
});

// ====== GLASS SURFACE EFFECT LOGIC ======
const glassEffectSettings = {
    borderRadius: 20, borderWidth: 0.07, brightness: 50, opacity: 0.93, blur: 11, displace: 15,
    distortionScale: -150, redOffset: 5, greenOffset: 15, blueOffset: 25, mixBlendMode: 'screen',
};

const feImage = document.getElementById('feImage');
const redChannel = document.getElementById('redChannel');
const greenChannel = document.getElementById('greenChannel');
const blueChannel = document.getElementById('blueChannel');
const gaussianBlur = document.getElementById('gaussianBlur');
const container = document.getElementById('glass-surface-container');

function generateDisplacementMap() {
    const rect = container.getBoundingClientRect();
    const actualWidth = rect.width, actualHeight = rect.height;
    const edgeSize = Math.min(actualWidth, actualHeight) * (glassEffectSettings.borderWidth * 0.5);
    const svgContent = `<svg viewBox="0 0 ${actualWidth} ${actualHeight}" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="red-grad-dynamic" x1="100%" y1="0%" x2="0%" y2="0%"><stop offset="0%" stop-color="#0000"/><stop offset="100%" stop-color="red"/></linearGradient><linearGradient id="blue-grad-dynamic" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#0000"/><stop offset="100%" stop-color="blue"/></linearGradient></defs><rect x="0" y="0" width="${actualWidth}" height="${actualHeight}" fill="black"></rect><rect x="0" y="0" width="${actualWidth}" height="${actualHeight}" rx="${glassEffectSettings.borderRadius}" fill="url(#red-grad-dynamic)" /><rect x="0" y="0" width="${actualWidth}" height="${actualHeight}" rx="${glassEffectSettings.borderRadius}" fill="url(#blue-grad-dynamic)" style="mix-blend-mode: ${glassEffectSettings.mixBlendMode}" /><rect x="${edgeSize}" y="${edgeSize}" width="${actualWidth - edgeSize * 2}" height="${actualHeight - edgeSize * 2}" rx="${glassEffectSettings.borderRadius}" fill="hsl(0 0% ${glassEffectSettings.brightness}% / ${glassEffectSettings.opacity})" style="filter:blur(${glassEffectSettings.blur}px)" /></svg>`;
    return `data:image/svg+xml,${encodeURIComponent(svgContent)}`;
}

function updateDisplacementMap() {
    if (feImage) feImage.setAttribute('href', generateDisplacementMap());
}

function applyFilterSettings() {
    if (!redChannel || !greenChannel || !blueChannel || !gaussianBlur) return;
    [{ ref: redChannel, offset: glassEffectSettings.redOffset }, { ref: greenChannel, offset: glassEffectSettings.greenOffset }, { ref: blueChannel, offset: glassEffectSettings.blueOffset }].forEach(({ ref, offset }) => {
        ref.setAttribute('scale', (glassEffectSettings.distortionScale + offset).toString());
        ref.setAttribute('xChannelSelector', 'R'); ref.setAttribute('yChannelSelector', 'G');
    });
    gaussianBlur.setAttribute('stdDeviation', glassEffectSettings.displace.toString());
}

document.addEventListener('DOMContentLoaded', () => {
    applyFilterSettings();
    const supportsSVGFilters = () => {
        const isWebkit = /Safari/.test(navigator.userAgent) && !/Chrome/.test(navigator.userAgent);
        if (isWebkit || /Firefox/.test(navigator.userAgent)) return false;
        const div = document.createElement('div');
        div.style.backdropFilter = 'url(#glass-filter)';
        return div.style.backdropFilter !== '';
    };

    if (supportsSVGFilters()) {
        container.classList.add('glass-surface--svg');
    } else {
        container.classList.add('glass-surface--fallback');
    }
    const resizeObserver = new ResizeObserver(() => setTimeout(updateDisplacementMap, 0));
    resizeObserver.observe(container);
});

// ====== HEADER WAVE MOUSE EFFECT ======
const header = document.querySelector("header");
const spotlight = document.getElementById("wave-spotlight");

header.addEventListener("mousemove", (e) => {
    const rect = header.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    spotlight.style.background = `radial-gradient(circle at ${x}px ${y}px, rgba(56, 189, 248, 0.2), transparent 250px)`;
    spotlight.style.opacity = '1';
});

header.addEventListener("mouseleave", () => {
    spotlight.style.opacity = '0';
});









// ====== JOURNEY SECTION CANVAS WAVES ======
const journeyCanvas = document.getElementById('oceanCanvas');
const journeyCtx = journeyCanvas.getContext('2d');

const journeyWaves = [
    /* Layer 1 (Back): Lightest dark blue */
    { color: 'rgba(1, 90, 132, 1)',  offset: 0,   amplitude: 40, frequency: 0.010, phaseShift: 1, speed: 0.0010 },
    /* Layer 2 */
    { color: 'rgba(1, 42, 108, 1)',  offset: 40,  amplitude: 35, frequency: 0.012, phaseShift: 2, speed: -0.0012 },
    /* Layer 3 */
    { color: 'rgba(0, 32, 83, 1)',  offset: 80,  amplitude: 50, frequency: 0.011, phaseShift: 3, speed: 0.0011 },
    /* Layer 4 */
    { color: 'rgba(0, 24, 63, 1)',   offset: 120,  amplitude: 25, frequency: 0.013, phaseShift: 4, speed: -0.0013 },
    /* Layer 5 */
    { color: 'rgba(0, 13, 44, 1)',    offset: 160,  amplitude: 30, frequency: 0.009, phaseShift: 5, speed: 0.0010 },
    /* Layer 6 (Front): Deepest, darkest blue */
    { color: 'rgba(0, 7, 24, 1)',    offset: 200, amplitude: 45, frequency: 0.008, phaseShift: 6, speed: -0.0011 }
];

let journeyFrame = 0;

function resizeJourneyCanvas() {
    const container = document.querySelector('.visual-content-animated');
    if (container) {
        journeyCanvas.width = container.offsetWidth;
        journeyCanvas.height = container.offsetHeight;
    }
}

window.addEventListener('resize', resizeJourneyCanvas);
resizeJourneyCanvas();

function drawJourneyWaves(time) {
    journeyCtx.clearRect(0, 0, journeyCanvas.width, journeyCanvas.height);
    
    journeyWaves.forEach((wave) => {
        journeyCtx.beginPath();
        journeyCtx.fillStyle = wave.color;

        const startY = journeyCanvas.height * 0.2 + wave.offset;
        const phase = time * wave.speed + wave.phaseShift;

        journeyCtx.moveTo(0, startY);

        for (let x = 0; x <= journeyCanvas.width; x++) {
            const y = startY + Math.sin(x * wave.frequency + phase) * wave.amplitude;
            journeyCtx.lineTo(x, y);
        }

        journeyCtx.lineTo(journeyCanvas.width, journeyCanvas.height);
        journeyCtx.lineTo(0, journeyCanvas.height);
        journeyCtx.closePath();
        journeyCtx.fill();
    });
}

function animateJourneyWaves() {
    const time = Date.now();
    drawJourneyWaves(time);
    requestAnimationFrame(animateJourneyWaves);
}

animateJourneyWaves();