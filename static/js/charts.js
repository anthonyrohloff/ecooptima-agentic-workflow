// charts.js
document.addEventListener("DOMContentLoaded", function () {

    // Carbon Sequestration by Tree
    const carbonChartEl = document.getElementById("carbonChart");
    if (carbonChartEl) {
        new Chart(carbonChartEl.getContext("2d"), {
            type: 'bar',
            data: {
                labels: ['Oak', 'Maple', 'Pine', 'Birch', 'Cherry'],
                datasets: [{
                    label: 'CO₂ Sequestered',
                    data: [120, 95, 130, 85, 70],
                    backgroundColor: ['#2e7d32', '#66bb6a', '#a5d6a7', '#1b5e20', '#81c784']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, ticks: { callback: value => value + ' kg CO₂' } }
                }
            }
        });
    }

// Carbon Reduction by Solution
    const carbonSolutionsChartEl = document.getElementById("carbonSolutionsChart");
    if (carbonSolutionsChartEl) {
        new Chart(carbonSolutionsChartEl.getContext("2d"), {
            type: 'pie',
            data: {
                labels: ['Renewable Energy', 'Composting', 'Green Roofs', 'Reforestation'],
                datasets: [{ 
                    data: [300, 180, 120, 250], 
                    backgroundColor: ['#4caf50','#ffb74d','#64b5f6','#81c784'] 
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }

// Cumulative CO₂ Absorption Over Years
    const carbonTimelineChartEl = document.getElementById("carbonTimelineChart");
    if (carbonTimelineChartEl) {
        new Chart(carbonTimelineChartEl.getContext("2d"), {
            type: 'line',
            data: {
                labels: ['2024','2025','2026','2027','2028'],
                datasets: [{
                    label: 'CO₂ Absorbed',
                    data: [50,180,350,560,800],
                    fill: true,
                    backgroundColor: 'rgba(33,150,243,0.2)',
                    borderColor: '#2e7d32',
                    tension: 0.3
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }

// Academic Charts

    const academicAbatementChartEl = document.getElementById("academicAbatementChart");
    if (academicAbatementChartEl) {
        new Chart(academicAbatementChartEl.getContext("2d"), {
            type: 'bar',
            data: {
                labels: [
                    'Upgrade Campus Insulation','Switch Fleets to EVs','Expand Renewable Electricity',
                    'Invest in Green Infrastructure','Optimize Logistics & Routing','Hybrid Learning & Telework',
                    'Smart Classroom & Lab Controls','Energy Efficiency Retrofits','CCS Pilot Projects','DAC Research'
                ],
                datasets: [
                    { label:'Abatement Potential (t CO₂)', data:[150,120,100,130,90,70,60,110,40,25], backgroundColor:'#4caf50' },
                    { label:'Cost Savings ($k/year)', data:[50,40,35,45,25,30,20,40,10,5], backgroundColor:'#81c784' }
                ]
            },
            options:{ indexAxis:'y', responsive:true, maintainAspectRatio:false }
        });
    }

    const academicTimelineChartEl = document.getElementById("academicTimelineChart");
    if (academicTimelineChartEl) {
        new Chart(academicTimelineChartEl.getContext("2d"), {
            type:'line',
            data:{
                labels:['2024','2025','2026','2027','2028','2029','2030'],
                datasets:[
                    { label:'Upgrade Campus Insulation', data:[30,60,90,120,150,160,170], borderColor:'#2e7d32', backgroundColor:'rgba(46,125,50,0.2)', fill:true, tension:0.3 },
                    { label:'EV Fleet Conversion', data:[20,40,60,80,100,110,120], borderColor:'#66bb6a', backgroundColor:'rgba(102,187,106,0.2)', fill:true, tension:0.3 },
                    { label:'Green Infrastructure', data:[25,50,80,110,130,140,150], borderColor:'#81c784', backgroundColor:'rgba(129,199,132,0.2)', fill:true, tension:0.3 }
                ]
            },
            options:{ responsive:true, maintainAspectRatio:false }
        });
    }

    const academicPolicyChartEl = document.getElementById("academicPolicyChart");
    if (academicPolicyChartEl) {
        new Chart(academicPolicyChartEl.getContext("2d"), {
            type:'pie',
            data:{
                labels:['Energy Efficiency','Transport & EV','Green Infrastructure','CCS/DAC Research'],
                datasets:[{ data:[5,2,2,1], backgroundColor:['#4caf50','#66bb6a','#81c784','#a5d6a7'] }]
            },
            options:{ responsive:true, maintainAspectRatio:false }
        });
    }

// Home Charts (Bar / Line / Pie)

    const homeAbatementChartEl = document.getElementById("homeAbatementChart");
    if (homeAbatementChartEl) {
        new Chart(homeAbatementChartEl.getContext("2d"), {
            type:'bar',
            data:{
                labels:[
                    'Switch to LED','Smart Thermostat','Weatherstrip','Home Insulation','Induction Cooktop','Energy Star Appliances',
                    'Electric Bike','Carpool','Plant Shade Trees','Cold Laundry','Air-dry Clothes','Low-flow Showerheads'
                ],
                datasets:[
                    { label:'Abatement Potential (kg CO₂)', data:[150,120,80,100,60,70,50,40,30,25,20,15], backgroundColor:'#4caf50' },
                    { label:'Cost Savings ($/year)', data:[40,35,25,50,20,25,15,10,5,5,5,5], backgroundColor:'#81c784' }
                ]
            },
            options:{ indexAxis:'y', responsive:true, maintainAspectRatio:false }
        });
    }

    const homeTimelineChartEl = document.getElementById("homeTimelineChart");
    if (homeTimelineChartEl) {
        new Chart(homeTimelineChartEl.getContext("2d"), {
            type:'line',
            data:{
                labels:['2024','2025','2026','2027','2028'],
                datasets:[
                    { label:'LED Bulbs', data:[20,40,60,80,100], borderColor:'#2e7d32', backgroundColor:'rgba(46,125,50,0.2)', fill:true, tension:0.3 },
                    { label:'Smart Thermostat', data:[15,35,55,75,95], borderColor:'#66bb6a', backgroundColor:'rgba(102,187,106,0.2)', fill:true, tension:0.3 },
                    { label:'Home Insulation', data:[25,50,75,100,130], borderColor:'#81c784', backgroundColor:'rgba(129,199,132,0.2)', fill:true, tension:0.3 }
                ]
            },
            options:{ responsive:true, maintainAspectRatio:false }
        });
    }

    const homePolicyChartEl = document.getElementById("homePolicyChart");
    if (homePolicyChartEl) {
        new Chart(homePolicyChartEl.getContext("2d"), {
            type:'pie',
            data:{
                labels:['Lighting','Appliances','HVAC','Transport','Trees & Landscaping','Water'],
                datasets:[{ data:[2,3,2,2,2,1], backgroundColor:['#4caf50','#66bb6a','#81c784','#aed581','#a5d6a7','#c8e6c9'] }]
            },
            options:{ responsive:true, maintainAspectRatio:false }
        });
    }

// Government Charts
const govAbatementChartEl = document.getElementById("govAbatementChart");
if (govAbatementChartEl) {
    new Chart(govAbatementChartEl.getContext("2d"), {
        type: 'bar',
        data: {
            labels: ['Policy A', 'Policy B', 'Policy C'],
            datasets: [{
                label: 'Abatement Potential (t CO₂)',
                data: [120, 100, 80],
                backgroundColor: '#4caf50'
            }]
        },
        options: { indexAxis: 'y', responsive:true, maintainAspectRatio:false }
    });
}

const govTimelineChartEl = document.getElementById("govTimelineChart");
if (govTimelineChartEl) {
    new Chart(govTimelineChartEl.getContext("2d"), {
        type: 'line',
        data: {
            labels: ['2024','2025','2026','2027','2028'],
            datasets: [{
                label: 'CO₂ Reduced',
                data: [50, 100, 150, 200, 250],
                borderColor: '#2e7d32',
                backgroundColor: 'rgba(46,125,50,0.2)',
                fill:true,
                tension:0.3
            }]
        },
        options:{ responsive:true, maintainAspectRatio:false }
    });
}

const govPolicyChartEl = document.getElementById("govPolicyChart");
if (govPolicyChartEl) {
    new Chart(govPolicyChartEl.getContext("2d"), {
        type: 'pie',
        data: {
            labels: ['Tax Incentives','Carbon Tax','Carbon Credit Model'],
            datasets:[{
                data: [5,3,2],
                backgroundColor:['#4caf50','#81c784','#a5d6a7']
            }]
        },
        options:{ responsive:true, maintainAspectRatio:false }
    });
}

// Corporate Charts
const corpAbatementChartEl = document.getElementById("corpAbatementChart");
if (corpAbatementChartEl) {
    new Chart(corpAbatementChartEl.getContext("2d"), {
        type: 'bar',
        data: {
            labels: [
                'LED Lighting', 'HVAC Upgrade', 'Energy Software', 'VFD Motors',
                'Building Insulation', 'Renewable Contracts', 'Optimize Logistics', 
                'Telework', 'Smart Manufacturing', 'EV Fleet', 'CCS', 'DAC'
            ],
            datasets: [
                { label:'Abatement Potential (t CO₂)', data:[80,120,60,70,90,100,50,40,60,70,30,20], backgroundColor:'#4caf50' },
                { label:'Cost Savings ($k/year)', data:[40,60,30,25,45,50,20,15,25,35,10,5], backgroundColor:'#81c784' }
            ]
        },
        options:{ indexAxis:'y', responsive:true, maintainAspectRatio:false }
    });
}

const corpTimelineChartEl = document.getElementById("corpTimelineChart");
if (corpTimelineChartEl) {
    new Chart(corpTimelineChartEl.getContext("2d"), {
        type:'line',
        data:{
            labels:['2024','2025','2026','2027','2028','2029','2030'],
            datasets:[
                { label:'LED Lighting', data:[10,20,30,40,50,55,60], borderColor:'#2e7d32', backgroundColor:'rgba(46,125,50,0.2)', fill:true, tension:0.3 },
                { label:'HVAC Upgrade', data:[20,45,70,95,120,130,140], borderColor:'#66bb6a', backgroundColor:'rgba(102,187,106,0.2)', fill:true, tension:0.3 },
                { label:'Renewable Contracts', data:[15,35,55,80,100,110,120], borderColor:'#81c784', backgroundColor:'rgba(129,199,132,0.2)', fill:true, tension:0.3 }
            ]
        },
        options:{ responsive:true, maintainAspectRatio:false }
    });
}

const corpPolicyChartEl = document.getElementById("corpPolicyChart");
if (corpPolicyChartEl) {
    new Chart(corpPolicyChartEl.getContext("2d"), {
        type:'pie',
        data:{
            labels:['Energy Efficiency','Transport & EV','Renewables','Smart Manufacturing','CCS/DAC'],
            datasets:[{ data:[5,2,2,2,1], backgroundColor:['#4caf50','#66bb6a','#81c784','#aed581','#a5d6a7'] }]
        },
        options:{ responsive:true, maintainAspectRatio:false }
    });
}

});