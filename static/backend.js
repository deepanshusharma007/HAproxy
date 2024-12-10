var json = '{{ data }}';

const decodedData = decodeEntities(json);
const jsonData = JSON.parse(decodedData);
const fieldMappings = [
    { backend: 'backendname', server: 'servername', port: 'port', address: 'ip' },
    // Add more mappings for indexes 1 to 6 if needed
];

const serverLength = jsonData[1].server.data.length;
const servercontainer = document.getElementById("backendForm");
console.log("serverlength", jsonData);

var backendarray = [], servernamearray = [], IPAddress = [], portNumber = [], check = [];

var x = [
    { "backend": backendarray },
    { "servername": servernamearray },
    { "IPAddress": IPAddress },
    { "portNumber": portNumber },
    { "check": check }
]

console.log("backendArrayValues", backendarray)
const z = 0;
function saveInputValues() {
    event.preventDefault();
    const savedValues = backendarray.map(input => input);
    console.log('Saved values:', savedValues);

    var y = document.getElementById('backendid');
    console.log("y", y.value);
    // You can send the savedValues to a server or perform any other action here
}

// Attach a click event listener to the save button
const saveButton = document.getElementById('save')
saveButton.addEventListener('click', saveInputValues);

console.log("requiredDetails", x);

for (let j = 0; j < jsonData.length; j++) {

    const label = document.createElement('label');
    label.textContent = "Backend : ";
    const inputField = document.createElement('input');
    inputField.type = "text";
    inputField.value = jsonData[j].backend.name;
    inputField.classList.add("form-control");
    inputField.id = 'backendid';

    backendarray.push(inputField.value + "_" + j);

    inputField.addEventListener('blur', function () {
        backendarray[j] = inputField.value; // Update the array with the new value
    });

    servercontainer.appendChild(label);
    servercontainer.appendChild(inputField);

    for (let i = 0; i < jsonData[j].server.data.length; i++) {

        const servername = document.createElement('servername');
        servername.textContent = " Server name:";
        const inputField1 = document.createElement('input');
        inputField1.type = "text";
        inputField1.value = jsonData[j].server.data[i].name;
        inputField1.classList.add("form-control");

        servernamearray.push(inputField1.value + "_" + j)

        const ipname = document.createElement('ipname');
        ipname.textContent = " IP Address:";
        const inputField2 = document.createElement('input');
        inputField2.type = "text";
        inputField2.value = jsonData[j].server.data[i].address;
        inputField2.classList.add("form-control");

        IPAddress.push(inputField2.value + "_" + j);

        const Portname = document.createElement('Portname');
        Portname.textContent = " Port number :";
        const inputField3 = document.createElement('input');
        inputField3.type = "text";
        inputField3.value = jsonData[j].server.data[i].port;
        inputField3.classList.add("form-control");

        portNumber.push(inputField3.value + "_" + j)


        const checklabel = document.createElement("checklabel");
        checklabel.textContent = "Check:";
        checklabel.classList.add("form-label");

        const newSelect = document.createElement("newSelect");
        newSelect.name = "field";
        newSelect.classList.add("form-select");

        check.push(newSelect.value + "_" + j);


        const option1 = document.createElement("option");
        option1.value = "option1";
        option1.text = "Yes";

        const option2 = document.createElement("option");
        option2.value = "option2";
        option2.text = "No";

        newSelect.appendChild(option1);
        newSelect.appendChild(option2);

        servercontainer.appendChild(servername);
        servercontainer.appendChild(inputField1);
        servercontainer.appendChild(ipname);
        servercontainer.appendChild(inputField2);
        servercontainer.appendChild(Portname);
        servercontainer.appendChild(inputField3);
        servercontainer.appendChild(checklabel);
        servercontainer.appendChild(newSelect);
    }
}

const backendSection = document.getElementById('backendSection');
const addButton = document.getElementById('addButton');


addButton.addEventListener("click", function (event) {
    // const backendSection = document.createElement("div");
    // backendSection.classList.add("backend-section-template", "mb-3", "p-3", "border", "border-dark");

    const label = document.createElement('label');
    label.textContent = "Backend : ";
    const inputField = document.createElement('input');
    inputField.type = "text";
    inputField.placeholder = "Enter backend name";
    inputField.classList.add("form-control");

    const servername = document.createElement('servername');
    servername.textContent = " Server name:";
    const inputField1 = document.createElement('input');
    inputField1.type = "text";
    inputField1.placeholder = "Enter server name";
    inputField1.classList.add("form-control");

    const ipname = document.createElement('ipname');
    ipname.textContent = " IP Address:";
    const inputField2 = document.createElement('input');
    inputField2.type = "text";
    inputField2.placeholder = "Enter IP Address";
    inputField2.classList.add("form-control");

    const Portname = document.createElement('Portname');
    Portname.textContent = " Port number :";
    const inputField3 = document.createElement('input');
    inputField3.type = "text";
    inputField3.placeholder = "Enter Port number";
    inputField3.classList.add("form-control");

    const checklabel = document.createElement("checklabel");
    checklabel.textContent = "Check:";
    checklabel.classList.add("form-label");

    const newSelect = document.createElement("newSelect");
    newSelect.name = "field";
    newSelect.classList.add("form-select");

    const option1 = document.createElement("option");
    option1.value = "option1";
    option1.text = "Yes";

    const option2 = document.createElement("option");
    option2.value = "option2";
    option2.text = "No";

    newSelect.appendChild(option1);
    newSelect.appendChild(option2);

    backendSection.appendChild(label);
    backendSection.appendChild(inputField);
    backendSection.appendChild(servername);
    backendSection.appendChild(inputField1);
    backendSection.appendChild(ipname);
    backendSection.appendChild(inputField2);
    backendSection.appendChild(Portname);
    backendSection.appendChild(inputField3);
    backendSection.appendChild(checklabel);
    backendSection.appendChild(newSelect);

})

for (let i = 0; i <= 6; i++) {

    if (jsonData[i]) {
        const mapping = fieldMappings[i - 0];

        const backendName = jsonData[i].backend.name;
        document.getElementById(mapping.backend).value = backendName;

        const serverName = jsonData[i].server.data[0].name;
        document.getElementById(mapping.server).value = serverName;

        const port = jsonData[i].server.data[0].port;
        document.getElementById(mapping.port).value = port;

        const address = jsonData[i].server.data[0].address;
        document.getElementById(mapping.address).value = address;
    }
}

function decodeEntities(encodedString) {
    const textArea = document.createElement('textarea');
    textArea.innerHTML = encodedString;
    return textArea.value;
}
// console.log("jsondata", jsonData[0].backend.name);
// const backendname = jsonData[0].backend.name;
// console.log("connect timeout", backendname);
// const inputfiled = document.getElementById('backendname');
// inputfiled.value = backendname

// const servername=jsonData[0].server.data[0].name;
// const inputfiled1= document.getElementById('servername');
// inputfiled1.value=servername

// const servername1=jsonData[0].server.data[0].port;
// const inputfiled2= document.getElementById('port');
// inputfiled2.value=servername1
backend.push(document.getElementById("backend"));

// const servername2=jsonData[0].server.data[0].address;
// const inputfiled3= document.getElementById('ip');
// inputfiled3.value=servername2

// function decodeEntities(encodedString) {
//     const textArea = document.createElement('textarea');
//     textArea.innerHTML = encodedString;
//     return textArea.value;
// }
var container = document.getElementById("container");
var numberOfElements = 5;
for (var i = 0; i < numberOfElements; i++) {
    var newElement = document.createElement("p");
    newElement.textContent = "Element " + (i + 1);
    container.appendChild(newElement);
}
document.addEventListener("click", function (event) {
    if (event.target.classList.contains("add-backend")) {
        const backendSection = event.target.closest(".backend-section-template").cloneNode(true);
        backendSection.querySelector("input[name=backendname]").value = "";
        const serverSection = backendSection.querySelector(".server-section");
        serverSection.parentNode.removeChild(serverSection);
        document.getElementById("backendForm").appendChild(backendSection);
    }

    if (event.target.classList.contains("remove-backend")) {
        const backendSections = document.querySelectorAll(".backend-section-template");
        if (backendSections.length > 1) {
            backendSections[backendSections.length - 1].remove();
        }
    }

    if (event.target.classList.contains("add-server")) {
        const serverSection = event.target.closest(".backend-section-template").querySelector(".server-section").cloneNode(true);
        serverSection.querySelector("input[name=servername]").value = "";
        event.target.parentNode.insertBefore(serverSection, event.target.nextSibling);
    }

    if (event.target.classList.contains("remove-server")) {
        const serverSections = event.target.closest(".backend-section-template").querySelectorAll(".server-section");
        if (serverSections.length > 1) {
            event.target.closest(".server-section").remove();
        }
    }
});

const savebtn = document.createElement('button');
savebtn.textContent = 'Save';
savebtn.id = 'savebtn'; // Give it an ID for identification if needed
savebtn.classList.add('btn', 'btn-primary');
servercontainer.appendChild(savebtn);
savebtn.addEventListener('click', saveInputValues);

document.getElementById("submitBtn").addEventListener("click", function () {
    // Get form data
    const backendname = document.getElementById('backendname');

    // [{"type":"new","data":{}, "server":[ {"type":"new","data":{} }, {}] },{},{}]
    // backend name cannot be edited
    data = [
        {
            "type": "old",
            "data": { "name": "backendname" },
            "server": [{ "type": "new", "data": { "name": "server_new1", "address": "*", "port": 8080 } }]
        }
    ];

    data = { "server": "server_new1", "backend": "new_backend_from_python2" };

    // Display the JSON object
    //document.getElementById("jsonOutput").textContent = JSON.stringify(data, null, 2);

    // Send the JSON object via a POST request
    fetch('/delete_server', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
        .then(response => {
            // Handle the response here if needed

            if (response.ok) {
                // Parse the JSON response
                return response.json();
            } else {
                throw new Error('Request failed with status: ' + response.status);
            }
        })
        .then(data => {
            // Handle the JSON data here
            console.log(data);
            alert('Data Saved');
        })
        .catch(error => {
            // Handle errors here if the POST request fails
            alert('Fetch Error');
            console.error('Error:', error);
        });
});

function showAlertAndRedirect() {
    // Show an alert
    //alert('Do you want to Deploy config?');
    if (confirm("Confirm Changes?") == true) {
        window.location.href = '/deploy_config';
    } else {
        text = "You canceled!";
    }

    // Redirect to another page
}
