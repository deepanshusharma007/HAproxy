/*!
* Start Bootstrap - Simple Sidebar v6.0.6 (https://startbootstrap.com/template/simple-sidebar)
* Copyright 2013-2023 Start Bootstrap
* Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-simple-sidebar/blob/master/LICENSE)
*/
// 
// Scripts
// 

// Function to handle the button click

// {
//     event.preventDefault();
//     document.body.classList.toggle('sb-sidenav-toggled');
//     // localStorage.setItem('sb|sidebar-wrapper', document.body.classList.contains('sb-sidenav-toggled'));
//     if (document.body.classList.contains('sb-sidenav-toggled')) {
//         chevronIcon.src = "/static/chevron-right.svg";

//     } else {
//         chevronIcon.src = "/static/chevron-left.svg";
//     }
   

document.getElementById('startButton').addEventListener('click', function () {
    if (confirm('Are you sure you want to start HA Proxy?')) {
        // If the user clicks "OK" in the confirmation dialog:
        console.log('OK');
        window.location.href = '/stop_ha_proxy?action=start';
    } else {
        // If the user clicks "Cancel" in the confirmation dialog:
        console.log('Cancled');
    }
});


document.getElementById('restartButton').addEventListener('click', function () {
    if (confirm('Are you sure you want to restart HA Proxy?')) {
        // If the user clicks "OK" in the confirmation dialog:
        console.log('OK');
        window.location.href = '/stop_ha_proxy?action=restart';
    } else {
        // If the user clicks "Cancel" in the confirmation dialog:
        console.log('Cancled');
    }
});

document.getElementById('stopButton').addEventListener('click', function () {
    if (confirm('Are you sure you want to stop HA Proxy?')) {
        // If the user clicks "OK" in the confirmation dialog:
        console.log('OK');
        window.location.href = '/stop_ha_proxy?action=stop';
    } else {
        // If the user clicks "Cancel" in the confirmation dialog:
        console.log('Cancled');
    }
});

window.addEventListener('DOMContentLoaded', event => {

    // Toggle the side navigation
    const sidebarToggle = document.body.querySelector('#sidebarToggle');
    const chevronIcon = document.getElementById("chevronIcon");

    // const chevronLeftIcon = document.getElementById("chevronLeftIcon");
    // const chevronRightIcon = document.getElementById("chevronRightIcon");

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', event => {
            event.preventDefault();
            document.body.classList.toggle('sb-sidenav-toggled');
            // localStorage.setItem('sb|sidebar-wrapper', document.body.classList.contains('sb-sidenav-toggled'));
            if (document.body.classList.contains('sb-sidenav-toggled')) {
                chevronIcon.src = "/static/chevron-right.svg";
            
            } else {
                chevronIcon.src = "/static/chevron-left.svg";
            }
            
        });
    }
});
