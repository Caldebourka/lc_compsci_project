// Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyDczW3d0RbphdiXQHzjS8rAQrUGNku0iYc",
  authDomain: "birds-2b89b.firebaseapp.com",
  databaseURL: "https://birds-2b89b-default-rtdb.europe-west1.firebasedatabase.app",
  projectId: "birds-2b89b",
  storageBucket: "birds-2b89b.firebasestorage.app",
  messagingSenderId: "179072348631",
  appId: "1:179072348631:web:64e6bc3e5ca763cf98db92",
  measurementId: "G-6NGMSSL7PP"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const dbcon = firebase.database().ref('/userBird/');

let birdStrikesData = [];

fetch('https://cors-anywhere.herokuapp.com/file:///path/to/your/bird_strikes.json')
    .then(response => response.json())
    .then(data => {
        birdStrikesData = data;
        console.log("Bird strike data loaded:", birdStrikesData);
        showTable2();
    })
    .catch(error => console.error("Error loading bird strike data:", error));
	
// Function to save data to Firebase
document.getElementById("sendToFb").addEventListener("click", saveData);

function saveData() {
    let nameValue = document.getElementById("name").value.trim();
    let breedFieldVal = document.getElementById("breed").value.trim();
    let sizeFieldVal = document.getElementById("size").value.trim();
    let cloudFieldVal = document.getElementById("cloud").value.trim();
    
    let airlines = [];
    for (let i = 1; i <= 5; i++) {
        let checkbox = document.getElementById(`al${i}`);
        if (checkbox.checked) {
            airlines.push(checkbox.value);
            checkbox.checked = false;
        }
    }

    if (!nameValue || !breedFieldVal || !sizeFieldVal) {
        alert("Please fill in all required fields.");
        return;
    }

    let data = { Name: nameValue, Breed: breedFieldVal, Size: sizeFieldVal, Airlines: airlines, Clouds: cloudFieldVal };

    dbcon.push(data).then(() => {
        showTable1();
        showTable2(); // Display updated tables after saving
    }).catch(error => console.error("Error saving data: ", error));
}

// Function to display data in Table 1
function showTable1() {
    dbcon.once("value", function (snapshot) {
        const data = snapshot.val();
        const tbody = document.getElementById("ar2data");
        tbody.innerHTML = "";
        
        if (!data) {
            console.log("No data found in Firebase.");
            return;
        }

        for (let key in data) {
            const row = data[key];
            const tr = document.createElement("tr");

            const name = document.createElement("td");
            const breed = document.createElement("td");
            const size = document.createElement("td");
            const airlines = document.createElement("td");
            const clouds = document.createElement("td");

            name.textContent = row.Name;
            breed.textContent = row.Breed;
            size.textContent = row.Size;
            airlines.textContent = Array.isArray(row.Airlines) ? row.Airlines.join(", ") : "None";
            clouds.textContent = row.Clouds;

            tr.appendChild(name);
            tr.appendChild(breed);
            tr.appendChild(size);
            tr.appendChild(airlines);
            tr.appendChild(clouds);

            tbody.appendChild(tr);
        }
    });
}

// Function to display recommendations in Table 2
function showTable2() {
    if (birdStrikesData.length === 0) {
        console.warn("Bird strike data not loaded yet. Retrying...");
        return;
    }

    dbcon.once("value", function (snapshot) {
        const data = snapshot.val();
        const tbody = document.getElementById("ar3data");
        tbody.innerHTML = "";
        
        if (!data) {
            console.log("No data found in Firebase.");
            return;
        }

        for (let key in data) {
            const row = data[key];
            const tr = document.createElement("tr");

            const name = document.createElement("td");
            const recommendations = document.createElement("td");

            name.textContent = row.Name;
            recommendations.textContent = generateRecommendation(row.Breed, row.Size, row.Airlines, row.Clouds);

            tr.appendChild(name);
            tr.appendChild(recommendations);

            tbody.appendChild(tr);
        }
    });
}

// Function to generate safety recommendations
function generateRecommendation(breed, size, airlines, clouds) {
    if (!birdStrikesData || birdStrikesData.length === 0) {
        return "Data not available";
    }

    let relevantStrikes = birdStrikesData.filter(entry =>
        entry.species.toLowerCase() === breed.toLowerCase()
    );

    if (relevantStrikes.length === 0) {
        return "No known risk for this breed.";
    }

    relevantStrikes.sort((a, b) => b.strikes - a.strikes);
    let highRiskAirports = relevantStrikes.slice(0, 3).map(entry => entry.airport);
    let saferAirports = relevantStrikes.slice(-3).map(entry => entry.airport);

    return `Avoid: ${highRiskAirports.join(", ")} | Prefer: ${saferAirports.join(", ")}`;
}

// Use a single event listener for DOMContentLoaded
document.addEventListener("DOMContentLoaded", () => {
    showTable1();
    showTable2(); // Ensure both tables are displayed once the page is ready
});






