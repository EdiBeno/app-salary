// static/hourscard.js

let localClockState = {
    isClockedIn: false,
    startTime: null,
    endTime: null,
    task: ""
};

// --- Local ISO without UTC ---
function getLocalISO() {
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    return now.toISOString().slice(0, 19); // YYYY-MM-DDTHH:MM:SS
}

// נקרא את הנתונים הנדרשים מה-HTML (hidden inputs)
const CURRENT_EMPLOYEE_ID = document.getElementById("employee_id") 
    ? document.getElementById("employee_id").value 
    : null;

const CURRENT_ID_NUMBER = document.getElementById("id_number") 
    ? document.getElementById("id_number").value 
    : null;


document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("clock-in-btn").addEventListener("click", handleClockIn);
    document.getElementById("clock-out-btn").addEventListener("click", handleClockOut);
    document.getElementById("save-btn").addEventListener("click", handleSave);

    updateButtonsUI();
});

// --- עדכון ממשק ---
function updateButtonsUI() {
    const statusText = document.getElementById("status-text");

    if (localClockState.isClockedIn) {
        statusText.textContent = "🟢 תחילת משמרת";
    } else if (localClockState.endTime && !localClockState.isClockedIn) {
        statusText.textContent = "🔴 נא לשמור דיווח";
    } else {
        statusText.textContent = "🔴 לא במשמרת";
    }

    const inBtn = document.getElementById("clock-in-btn");
    const outBtn = document.getElementById("clock-out-btn");
    const saveBtn = document.getElementById("save-btn");
    const taskInp = document.getElementById("task");

    // כניסה: פעיל רק אם לא במשמרת
    inBtn.disabled = localClockState.isClockedIn;
    inBtn.classList.toggle("disabled", localClockState.isClockedIn);

    // יציאה: פעיל רק אם במשמרת
    outBtn.disabled = !localClockState.isClockedIn;
    outBtn.classList.toggle("disabled", !localClockState.isClockedIn);

    // שדה משימה: פעיל רק אם במשמרת
    taskInp.disabled = !localClockState.isClockedIn;

    // שמירה: פעילה רק אם יצאו ויש נתוני התחלה/סיום
    const canSave = localClockState.endTime && !localClockState.isClockedIn;
    saveBtn.disabled = !canSave;
    saveBtn.classList.toggle("disabled", !canSave);

    // עדכון שעות תצוגה
    document.getElementById("start-time-display").textContent = formatTime(localClockState.startTime);
    document.getElementById("end-time-display").textContent = formatTime(localClockState.endTime);
}

// --- פעולות ---
async function handleClockIn() {
    localClockState.isClockedIn = true;
    localClockState.startTime = getLocalISO();
    localClockState.task = "";

    await fetch("/api/clockin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            employee_id: CURRENT_EMPLOYEE_ID,
            startTime: localClockState.startTime
        })
    });

    updateButtonsUI();
    alert("נכנסת למשמרת בהצלחה!");
}

async function handleClockOut() {
    const taskVal = document.getElementById("task").value.trim();
    if (!taskVal) {
        alert("עליך למלא תיאור משימה לפני יציאה");
        return;
    }

    localClockState.isClockedIn = false;
    localClockState.endTime = getLocalISO();
    localClockState.task = taskVal;

    const start = localClockState.startTime.slice(11, 16);
    const end = localClockState.endTime.slice(11, 16);
    const dateISO = localClockState.startTime.split("T")[0];

    const startDate = new Date(localClockState.startTime);
    const endDate   = new Date(localClockState.endTime);
    const diffMs = endDate - startDate;
    const diffHrs = (diffMs / (1000 * 60 * 60)).toFixed(2);

    if (typeof applyDailyToMonthlyTable === "function") {
        applyDailyToMonthlyTable(dateISO, start, end, taskVal, diffHrs);
    }

    await fetch("/api/clockout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            employee_id: CURRENT_EMPLOYEE_ID,
            endTime: localClockState.endTime,
            task: taskVal
        })
    });

    updateButtonsUI();
    alert("יציאה נרשמה. נא לשמור דיווח.");
}

// --- Load Timesheet History ---
async function loadTimesheetHistory() {
    const res = await fetch(`/api/get_timesheet?employee_id=${CURRENT_EMPLOYEE_ID}`);
    const data = await res.json();

    const tableBody = document.getElementById("timesheets-list");
    tableBody.innerHTML = "";

    if (!data.entries || data.entries.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="5" class="text-center">אין נתונים</td></tr>`;
        return;
    }

    data.entries.forEach(entry => {
        addTimesheetRow({
            date: entry.date,
            startTime: entry.startTime,
            endTime: entry.endTime,
            task: entry.task,
            totalHours: entry.totalHours
        });
    });
}

// --- Handle Save ---
async function handleSave() {
    if (!localClockState.startTime || !localClockState.endTime) {
        alert("אין דיווח מוכן לשמירה");
        return;
    }

    // use local date
    const dateStr = localClockState.startTime.split("T")[0];

    const start = new Date(localClockState.startTime);
    const end = new Date(localClockState.endTime);
    const diffHrs = ((end - start) / (1000 * 60 * 60)).toFixed(2);

    const timesheetData = {
        employee_id: CURRENT_EMPLOYEE_ID,
        id_number: CURRENT_ID_NUMBER,
        date: dateStr,  
        startTime: localClockState.startTime,
        endTime: localClockState.endTime,
        task: localClockState.task,
        totalHours: diffHrs
    };

    await fetch("/api/savetimesheet", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(timesheetData)
    });

    addTimesheetRow(timesheetData);

    localClockState = { isClockedIn: false, startTime: null, endTime: null, task: "" };
    updateButtonsUI();
    alert("הדיווח נשמר בהצלחה!");
}

// --- Helpers ---
function formatTime(isoStr) {
    if (!isoStr) return "--:--";
    const d = new Date(isoStr);
    return d.toLocaleTimeString("he-IL", { hour: "2-digit", minute: "2-digit" });
}

// --- Add Row to History ---
function addTimesheetRow(data) {
    const tableBody = document.getElementById("timesheets-list");

    const noDataRow = tableBody.querySelector("tr td.text-center");
    if (noDataRow) noDataRow.parentElement.remove();

    const newRow = document.createElement("tr");

    const displayTime = (isoStr) => {
        if (!isoStr) return "--:--";
        return isoStr.slice(11, 16);
    };

    newRow.innerHTML = `
        <td>${data.date}</td>
        <td>${displayTime(data.startTime)} - ${displayTime(data.endTime)}</td>
        <td>${data.task}</td>
        <td>${data.totalHours} שעות</td>
        <td>✔</td>
    `;

    tableBody.insertBefore(newRow, tableBody.firstChild);
}
