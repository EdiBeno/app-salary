// Function to format the input time
function formatTime(input) {
  let value = input.value.replace(/\D/g, ''); // Remove non-digit characters

  let hours, minutes;

  if (value.length === 3) {
    // Example: 234 → 2:34
    hours = parseInt(value.slice(0, 1), 10);
    minutes = parseInt(value.slice(1), 10);
  } else if (value.length === 4) {
    // Example: 1600 → 16:00
    hours = parseInt(value.slice(0, 2), 10);
    minutes = parseInt(value.slice(2), 10);
  } else {
    input.value = value; // Let user keep typing
    return;
  }

  // Only format if valid time
  if (hours >= 0 && hours <= 23 && minutes >= 0 && minutes <= 59) {
    input.value = hours + ':' + minutes.toString().padStart(2, '0');
  } else {
    input.value = value; // Keep raw input if not valid yet
  }
}



// === Table Data Update Days ===
function updateDays() {
  const employeeId = document.getElementById('employee_id')?.value;
  const month = document.getElementById('employeeMonth')?.value?.padStart(2, '0');
  const year = document.getElementById('employeeYear')?.value;
  const tableBody = document.getElementById('table-body');

  // אם אין עובד / חודש / שנה — לא בונים טבלה
  if (!employeeId || !month || !year) {
    tableBody.innerHTML = '';
    return;
  }

  tableBody.innerHTML = ''; // Clear existing table

  const daysInMonth = new Date(year, month, 0).getDate();
  const generatedDays = [];

  for (let day = 1; day <= daysInMonth; day++) {
    const date = `${day.toString().padStart(2, '0')}/${month}/${year}`;
    const dayName = new Date(year, month - 1, day)
      .toLocaleDateString('he-IL', { weekday: 'long' });

    generatedDays.push({ day: dayName, date });
  }

  generatedDays.forEach((day, index) => {
    const row = document.createElement('tr');
    row.classList.add('small-row', 'row-height');

    const isSaturdayResult = isSaturday(day.date);
    const isHolidayResult = isHoliday(day.date);
        row.innerHTML = `

        <td data-section="daily" style="font-weight: bold; width: 2.5cm; height: 0.4cm; white-space: nowrap; text-align: center;">${day.day}</td>
        <td data-section="daily" style="font-weight: bold; width: 2.0cm; height: 0.4cm; text-align: center;">${day.date}</td>
        <td data-section="daily" style="font-weight: bold; width: 2.0cm; height: 0.4cm; text-align: center;">${isSaturdayResult}</td>
        <td data-section="daily" style="font-weight: bold; width: 2.0cm; height: 0.4cm; text-align: center;">${isHolidayResult}</td>
        <td>
        <input type="text" class="start-time time-input" maxlength="5"
          data-section="daily" style="font-weight: bold; width: 2.0cm; height: 0.4cm; font-size: 14px; text-align: center;"
          oninput="formatTime(this); updateHours(this);">
        </td>
        <td>
        <input type="text" class="end-time time-input" maxlength="5"
          data-section="daily" style="font-weight: bold; width: 2.0cm; height: 0.4cm; font-size: 14px; text-align: center;"
          oninput="formatTime(this); updateHours(this);">
        </td>
        <td><input type="text" data-section="daily" style="font-weight: bold; width: 2.0cm; height: 0.4cm; font-size: 14px; text-align: center;" class="hours-calculated"></td>
        <td><input type="text" data-section="daily" style="font-weight: bold; width: 2.0cm; height: 0.4cm; text-align: center;" class="hours-calculated-regular-day"></td>
        <td><input type="text" data-section="daily" style="font-weight: bold; width: 2.0cm; height: 0.4cm; text-align: center;" class="total-extra-hours-regular-day"></td>
        <td><input type="text" data-section="daily" style="font-weight: bold; width: 2.0cm; height: 0.4cm; text-align: center;" class="extra-hours125-regular-day"></td>
        <td><input type="text" data-section="daily" style="font-weight: bold; width: 2.0cm; height: 0.4cm; text-align: center;" class="extra-hours150-regular-day"></td>
        <td><input type="text" data-section="daily" style="font-weight: bold; width: 2.0cm; height: 0.4cm; text-align: center;" class="hours-holidays-day"></td>
        <td><input type="text" data-section="daily" style="font-weight: bold; width: 2.0cm; height: 0.4cm; text-align: center;" class="extra-hours150-holidays-saturday"></td>
        <td><input type="text" data-section="daily" style="font-weight: bold; width: 2.0cm; height: 0.4cm; text-align: center;" class="extra-hours175-holidays-saturday"></td>
        <td><input type="text" data-section="daily" style="font-weight: bold; width: 2.0cm; height: 0.4cm; text-align: center;" class="extra-hours200-holidays-saturday"></td>
        <td><input type="text" data-section="daily" style="font-weight: bold; width: 2.0cm; height: 0.4cm; text-align: center;" class="sick-day"></td>
        <td><input type="text" data-section="daily" style="font-weight: bold; width: 2.0cm; height: 0.4cm; text-align: center;" class="day-off"></td>
        <td><input type="text" data-section="daily" style="font-weight: bold; width: 2.0cm; height: 0.4cm; text-align: center;" class="food-break"></td>
        <td><input type="text" data-section="daily" style="font-weight: bold; width: 2.5cm; height: 0.4cm; text-align: center;" class="final-totals-hours"></td>

        <td><input type="text" class="calc1" data-section="daily" 
             style="font-weight: bold; text-align: center; width: 2.0cm;"></td>
        <td><input type="text" class="calc2" data-section="daily" 
             style="font-weight: bold; text-align: center; width: 2.0cm;"></td>
        <td><input type="text" class="calc3" data-section="daily" 
            style="font-weight: bold; text-align: center; width: 2.0cm;"></td>

        <td><input type="text" data-section="daily" style="font-weight: bold; width: 2.0cm; height: 0.4cm; text-align: center;" class="work-day"></td>
        <td><input type="text" data-section="daily" style="font-weight: bold; width: 2.0cm; height: 0.4cm; text-align: center;" class="missing-work-day"></td>
        <td><input type="text" data-section="daily" style="font-weight: bold; width: 2.0cm; height: 0.4cm; text-align: center;" class="advance-payment"></td>
     `;

        // === ROW COLORING ===
        const dayNumber = parseInt(day.date.split("/")[0], 10);

        if (isHolidayResult) {
            row.style.backgroundColor = 'lightgreen';
        } else if (isSaturdayResult) {
            row.style.backgroundColor = 'lightblue';
        } else {
        row.style.backgroundColor = (dayNumber % 2 === 1)
            ? 'lightyellow'
            : '#f2f2f2';
        }
        tableBody.appendChild(row);
});

    //  Add Last Rows Monthly Totals 

const monthlyRow = document.createElement('tr');
monthlyRow.classList.add('small-row');
monthlyRow.innerHTML = `
    <td data-section="monthly" style="font-weight: bold; text-align: right; width: 2.5cm; white-space: nowrap; background-color: lightyellow;">סה"כ שעות</td>

    ${Array(1).fill('<td><input type="text" data-section="monthly" style="font-weight:bold;text-align:center;width:2.0cm;background-color:lightyellow;"></td>').join('')}
    ${Array(4).fill('<td><input type="text" data-section="monthly" style="font-weight:bold;text-align:center;width:2.0cm;background-color:lightyellow;"></td>').join('')}

    <td><input type="text" class="hours-calculated-monthly" data-section="monthly" style="font-weight:bold;text-align:center;width:2.0cm;background-color:lightyellow;"></td>
    <td><input type="text" class="hours-calculated-regular-day-monthly" data-section="monthly" style="font-weight:bold;text-align:center;width:2.0cm;background-color:lightyellow;"></td>
    <td><input type="text" class="total-extra-hours-regular-day-monthly" data-section="monthly" style="font-weight:bold;text-align:center;width:2.0cm;background-color:lightyellow;"></td>
    <td><input type="text" class="extra-hours125-regular-day-monthly" data-section="monthly" style="font-weight:bold;text-align:center;width:2.0cm;background-color:lightyellow;"></td>
    <td><input type="text" class="extra-hours150-regular-day-monthly" data-section="monthly" style="font-weight:bold;text-align:center;width:2.0cm;background-color:lightyellow;"></td>

    <td><input type="text" data-section="monthly" style="font-weight:bold;text-align:center;width:2.0cm;background-color:lightyellow;"></td>

    <td><input type="text" class="extra-hours150-holidays-saturday-monthly" data-section="monthly" style="font-weight:bold;text-align:center;width:2.0cm;background-color:lightyellow;"></td>
    <td><input type="text" class="extra-hours175-holidays-saturday-monthly" data-section="monthly" style="font-weight:bold;text-align:center;width:2.0cm;background-color:lightyellow;"></td>
    <td><input type="text" class="extra-hours200-holidays-saturday-monthly" data-section="monthly" style="font-weight:bold;text-align:center;width:2.0cm;background-color:lightyellow;"></td>

    <td><input type="text" class="sick-day-monthly" data-section="monthly" style="font-weight:bold;text-align:center;width:2.0cm;background-color:lightyellow;"></td>
    <td><input type="text" class="day-off-monthly" data-section="monthly" style="font-weight:bold;text-align:center;width:2.0cm;background-color:lightyellow;"></td>
    <td><input type="text" class="food-break-monthly" data-section="monthly" style="font-weight:bold;text-align:center;width:2.0cm;background-color:lightyellow;"></td>

    <td><input type="text" class="final-totals-hours-monthly" data-section="monthly" style="font-weight:bold;text-align:center;width:2.5cm;background-color:lightyellow;"></td>

    <td><input type="text" class="calc1-monthly" data-section="monthly" style="font-weight:bold;text-align:center;width:2.0cm;background-color:#F0F0F0;"></td>
    <td><input type="text" class="calc2-monthly" data-section="monthly" style="font-weight:bold;text-align:center;width:2.0cm;background-color:#F0F0F0;"></td>
    <td><input type="text" class="calc3-monthly" data-section="monthly" style="font-weight:bold;text-align:center;width:2.0cm;background-color:#F0F0F0;"></td>

    <td><input type="text" class="work-day-monthly" data-section="monthly" style="font-weight:bold;text-align:center;width:2.0cm;background-color:lightyellow;"></td>
    <td><input type="text" class="missing-work-day-monthly" data-section="monthly" style="font-weight:bold;text-align:center;width:2.0cm;background-color:lightyellow;"></td>
    <td><input type="text" data-section="monthly" style="font-weight:bold;text-align:center;width:2.0cm;background-color:lightyellow;"></td>
`;
tableBody.appendChild(monthlyRow);

//  Add Last Rows Paid Totals
const paidRow = document.createElement('tr');
paidRow.classList.add('small-row');
paidRow.innerHTML = `
    <td data-section="paid" style="font-weight: bold; text-align: right; width: 2.5cm; white-space: nowrap; background-color: #F0F0F0;">סה"כ לתשלום</td>

    ${Array(1).fill('<td><input type="text" data-section="paid" style="font-weight:bold;text-align:center;width:2.0cm;background-color:#F0F0F0;"></td>').join('')}
    ${Array(4).fill('<td><input type="text" data-section="paid" style="font-weight:bold;text-align:center;width:2.0cm;background-color:#F0F0F0;"></td>').join('')}

    <td><input type="text" data-section="paid" style="font-weight:bold;text-align:center;width:2.0cm;background-color:#F0F0F0;"></td>
    <td><input type="text" class="hours-calculated-regular-day-paid" data-section="paid" style="font-weight:bold;text-align:center;width:2.0cm;background-color:#F0F0F0;"></td>

    <td><input type="text" data-section="paid" style="font-weight:bold;text-align:center;width:2.0cm;background-color:#F0F0F0;"></td>

    <td><input type="text" class="extra-hours125-regular-day-paid" data-section="paid" style="font-weight:bold;text-align:center;width:2.0cm;background-color:#F0F0F0;"></td>
    <td><input type="text" class="extra-hours150-regular-day-paid" data-section="paid" style="font-weight:bold;text-align:center;width:2.0cm;background-color:#F0F0F0;"></td>

    <td><input type="text" data-section="paid" style="font-weight:bold;text-align:center;width:2.0cm;background-color:#F0F0F0;"></td>

    <td><input type="text" class="extra-hours150-holidays-saturday-paid" data-section="paid" style="font-weight:bold;text-align:center;width:2.0cm;background-color:#F0F0F0;"></td>
    <td><input type="text" class="extra-hours175-holidays-saturday-paid" data-section="paid" style="font-weight:bold;text-align:center;width:2.0cm;background-color:#F0F0F0;"></td>
    <td><input type="text" class="extra-hours200-holidays-saturday-paid" data-section="paid" style="font-weight:bold;text-align:center;width:2.0cm;background-color:#F0F0F0;"></td>

    <td><input type="text" class="sick-day-paid" data-section="paid" style="font-weight:bold;text-align:center;width:2.0cm;background-color:#F0F0F0;"></td>
    <td><input type="text" class="day-off-paid" data-section="paid" style="font-weight:bold;text-align:center;width:2.0cm;background-color:#F0F0F0;"></td>
    <td><input type="text" class="food-break-unpaid" data-section="paid" style="font-weight:bold;text-align:center;width:2.0cm;background-color:#F0F0F0;"></td>

    <td><input type="text" class="final-totals-hours-paid" data-section="paid" style="font-weight:bold;text-align:center;width:2.5cm;background-color:lightgreen;"></td>

    <td><input type="text" class="calc1-paid" data-section="paid" style="font-weight:bold;text-align:center;width:2.0cm;background-color:#F0F0F0;"></td>
    <td><input type="text" class="calc2-paid" data-section="paid" style="font-weight:bold;text-align:center;width:2.0cm;background-color:#F0F0F0;"></td>
    <td><input type="text" class="calc3-paid" data-section="paid" style="font-weight:bold;text-align:center;width:2.0cm;background-color:#F0F0F0;"></td>

    <td><input type="text" class="final-totals-lunch-value-paid" data-section="paid" style="font-weight:bold;text-align:center;width:2.0cm;background-color:#F0F0F0;"></td>
    <td><input type="text" class="final-total-extra-hours-weekend-monthly" data-section="paid" style="font-weight:bold;text-align:center;width:2.0cm;background-color:#F0F0F0;"></td>
    <td><input type="text" class="advance-payment-paid" data-section="paid" style="font-weight:bold;text-align:center;width:2.0cm;background-color:#F0F0F0;"></td>
`;
tableBody.appendChild(paidRow);

  // Final step: trigger calculations
  calculateHours();
}

//  Fill Section All work_day_entries, paidRow, monthlyRow (Helper)
function fillSection(sectionName, sectionData) {
  for (const [key, value] of Object.entries(sectionData)) {
    const input = document.querySelector(`.${key}[data-section="${sectionName}"]`);
    if (input) input.value = value;
  }
}


//  Monthly, Dynamic, Israeli Week Logic Alert if any Week Exceeds 40 Hours (Over)
// Convert DD/MM/YYYY to Date
function parseIsraeliDate(str) {
  const [day, month, year] = str.split('/').map(Number);
  return new Date(year, month - 1, day);
}

// Utility: Get start of week (Sunday)
function getWeekStart(date) {
  const day = date.getDay(); // 0 = Sunday
  const diff = date.getDate() - day;
  return new Date(date.getFullYear(), date.getMonth(), diff);
}

// Utility: Format date as DD/MM/YYYY
function formatDateIL(date) {
  const dd = String(date.getDate()).padStart(2, '0');
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const yyyy = date.getFullYear();
  return `${dd}/${mm}/${yyyy}`;
}

// Check weekly totals and show alert if over 42 hours
// Track which weeks have already shown alerts
function checkWeeklyHours() {
  const rows = document.querySelectorAll('#table-body tr');
  const weeklyTotals = {};
  const warnings = [];

  rows.forEach(row => {
    const dateStr = row.cells[1]?.textContent.trim();
    const hoursInput = row.querySelector('.hours-calculated');
    const breakInput = row.querySelector('.food-break');

    if (!dateStr || !hoursInput || !hoursInput.value || row.style.display === 'none') return;

    const [day, month, year] = dateStr.split('/').map(Number);
    const date = new Date(year, month - 1, day);
    const weekStart = getWeekStart(date);
    const key = formatDateIL(weekStart);

    const hours = parseFloat(hoursInput.value);
    const breakTime = parseFloat(breakInput?.value) || 0;
    if (isNaN(hours)) return;

    const adjustedHours = hours - breakTime;
    weeklyTotals[key] = (weeklyTotals[key] || 0) + adjustedHours;
  });

  for (const [weekStart, total] of Object.entries(weeklyTotals)) {
    if (total > 42) {
      warnings.push(`⚠️ השבוע שמתחיל ב־${weekStart} כולל ${total.toFixed(2)} שעות — חורג מהמותר!`);
    }
  }

  const container = document.getElementById('weekly-warning');
  container.innerHTML = ''; // Clear old warnings

  if (warnings.length > 0) {
    container.style.display = 'block';

    warnings.slice(0, 4).forEach(msg => {
      const line = document.createElement('div');
      line.className = 'warning-line';

      const text = document.createElement('span');
      text.textContent = msg;

      const confirmBtn = document.createElement('button');
      confirmBtn.textContent = 'אישור';
      confirmBtn.className = 'confirm-button';
      confirmBtn.onclick = () => {
        line.remove(); // Remove this warning line
        if (container.children.length === 0) {
          container.style.display = 'none'; // Hide container if empty
        }
      };

      line.appendChild(text);       // Message first (right side in RTL)
      line.appendChild(confirmBtn); // Button second (left side in RTL)
      container.appendChild(line);
    });
  } else {
    container.style.display = 'none';
  }
}


// Function Show Hide Windows Error.
function showWindowsSuccess(message, successKey) {
  const successDiv = document.getElementById('windows-success-box');
  successDiv.innerHTML = '';

  const messageSpan = document.createElement('span');
  messageSpan.textContent = message;
  messageSpan.style.flex = '1';

  const confirmBtn = document.createElement('button');
  confirmBtn.textContent = 'אישור';
  confirmBtn.classList.add('windows-success-btn');

  confirmBtn.onclick = function () {
    if (successKey) {
      localStorage.setItem(`successConfirmed-${successKey}`, 'true');
    }
    hideWindowsSuccess();
  };

  successDiv.appendChild(messageSpan);
  successDiv.appendChild(confirmBtn);
  successDiv.style.display = 'flex';
}

function hideWindowsSuccess() {
  const successDiv = document.getElementById('windows-success-box');
  successDiv.style.display = 'none';
  successDiv.innerHTML = '';
}



function isSaturday(date) {
    const [day, month, year] = date.split('/').map(Number);
    const dayOfWeek = new Date(year, month - 1, day).getDay();
    return dayOfWeek === 6; // 6 represents Saturday
}

// Function to check if the date is a holiday.
function isHoliday(date) {
    const holidays = [
        '27/03/2021', '28/03/2021', '15/04/2021', '17/05/2021', '06/09/2021', '07/09/2021', '16/09/2021', '20/09/2021', '21/09/2021',
        '18/03/2022', '15/04/2022', '05/05/2022', '05/06/2022', '25/09/2022', '26/09/2022', '05/10/2022', '09/10/2022', '10/10/2022',
        '05/04/2023', '06/04/2023', '26/04/2023', '26/04/2023', '15/09/2023', '16/09/2023', '25/09/2023', '29/09/2023', '30/09/2023',
        '22/04/2024', '23/04/2024', '14/05/2024', '12/06/2024', '02/10/2024', '03/10/2024', '12/10/2024', '16/10/2024', '17/10/2024',
        '12/04/2025', '13/04/2025', '01/05/2025', '02/06/2025', '22/09/2025', '23/09/2025', '02/10/2025', '06/10/2025', '07/10/2025',
        '05/03/2026', '01/04/2026', '22/04/2026', '22/05/2026', '11/09/2026', '12/09/2026', '21/09/2026', '25/09/2026', '26/09/2026',
        '21/04/2027', '22/04/2027', '12/05/2027', '11/06/2027', '01/10/2027', '02/10/2027', '11/10/2027', '15/10/2027', '16/10/2027',
        '10/04/2028', '11/04/2028', '02/05/2028', '31/05/2028', '20/09/2028', '21/09/2028', '30/09/2028', '04/10/2028', '05/10/2028'
    ];

    // Ensure the date format is consistent
    const formattedDate = date.split('/').map(part => part.padStart(2, '0')).join('/');
    return holidays.includes(formattedDate);
}




//   === Handle Paste from Excel into Start/End Time Inputs For Excel Copy ===

//  Handle Paste from Excel into Start/End Time Inputs
document.getElementById('table-body').addEventListener('paste', function(e) {
  e.preventDefault();
  const clipboard = e.clipboardData || window.clipboardData;
  const pastedData = clipboard.getData('Text');

  const rows = pastedData.trim().split('\n');
  const startInputs = document.querySelectorAll('.start-time');
  const endInputs = document.querySelectorAll('.end-time');

  rows.forEach((row, i) => {
    const [start, end] = row.split('\t');
    if (startInputs[i]) startInputs[i].value = start.trim();
    if (endInputs[i]) endInputs[i].value = end.trim();
  });

  //  Delay recalculation to allow DOM updates
  setTimeout(() => {
      recalculateAllRows();
  }, 300);
});



//  Recalculate All Rows and Columns For Excel Copy
function recalculateAllRows() {
  const rows = document.querySelectorAll('#table-body tr');

  rows.forEach(row => {
    try {
          updateHours(row);
          updateColumn8(row);
          updateColumn9(row);
          updateColumn10(row);
          updateColumn11(row);
          updateColumn12(row);
          updateColumn13(row);
          updateColumn14(row);
          updateColumn15(row);
          updateColumn16(row);
          updateColumn17(row);
          updateColumn18(row);
          updateColumn19(row);
          updateColumn23(row);
          updateColumn24(row);
    } catch (err) {
    }
  });

    calculateTotalHoursCalculatedForMonth();
    calculateHoursCalculatedRegularDayForMonth();
    calculatetotalExtraHoursRegularDayForMonth();
    calculateExtraHours125RegularDayForMonth();
    calculateExtraHours150RegularDayForMonth();
    calculateExtraHours150HolidaysSaturdayForMonth();
    calculateExtraHours175HolidaysSaturdayForMonth();
    calculateExtraHours200HolidaysSaturdayForMonth();
    calculateSickDayForMonth();
    calculateDayOffForMonth();
    calculateFoodBreakForMonth();
    calculateFinalTotalHoursForMonth();
    calculateWorkDayForMonth();
    calculateMissingWorkDayForMonth();

    calculateTotalRegularDayPaymentForMonth();
    calculateTotalExtraHours125RegularDayPaymentForMonth();
    calculateTotalExtraHours150RegularDayPaymentForMonth();
    calculateTotalExtraHours150HolidaysSaturdayPaymentForMonth();
    calculateTotalExtraHours175HolidaysSaturdayPaymentForMonth();
    calculateTotalExtraHours200HolidaysSaturdayPaymentForMonth();
    calculateTotalFoodBreakUnpaidOffPaymentForMonth();
    calculateFinalTotalsHoursPaidForMonth();
    calculateFinalTotalsLunchValuePaidForMonth();

    preserveSickDayValue();
    preserveDayOffValue();
    updateSickDaysInSalaryForm();
    calculateSickDayYearlySummary();
    updateVacationDaysInSalaryForm();
    calculateVacationDayYearlySummary();

    updateTotalWorkDays();
    calculateFinalTotalExtraHoursWeekendForMonth();
    updateTotalsLunchValueForm();
    updateTotalMissingHours();
    updateTotalFinalExtraWeekendHours();
    updateTotalFinalExtraRegularHours();
    calculationsAdditionalPayments();
    updateIncomeTaxBeforeCredit();
    updateTaxLevelPercentage();
    calculateAboveCeilingFund();

    updateHoursFoodBreakUnpaid();
    updateHoursRegular125();
    updateHoursRegular150();
    updateHoursHolidaysSaturday150();
    updateHoursHolidaysSaturday175();
    updateHoursHolidaysSaturday200();

    updateTaxFormFields(data);
    updateBasicSalary();
    validateAndCalculateForm();
}



//   === Update Month Result ===
function updateMonthResult() {
  const month = document.getElementById('employeeMonth').value;
  const year = document.getElementById('employeeYear').value;
  const monthResult = document.getElementById('monthResult');

  const paddedMonth = String(month).padStart(2, '0');
  const monthName = new Date(year, month - 1).toLocaleString('he-IL', { month: 'long' });

  monthResult.value = `${monthName}/${year}`;

  fetch('/update_month_year', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ employeeMonth: paddedMonth, employeeYear: year })
  })
  .then(response => response.ok ? response.json() : null)
  .then(() => {
    // Response handled silently
  });

  updateDays();
}



// Function to calculate hours worked, considering overnight shifts
function calculateTimeDifference(startTime, endTime) {
  const [startH, startM] = startTime.split(':').map(Number);
  const [endH, endM] = endTime.split(':').map(Number);

  if (!isNaN(startH) && !isNaN(startM) && !isNaN(endH) && !isNaN(endM)) {
    const startMinutes = startH * 60 + startM;
    const endMinutes = endH * 60 + endM;

    let diff = endMinutes - startMinutes;
    if (diff < 0) diff += 1440; // overnight shift

    return diff / 60; // return hours as float
  }

  return 0;
}

//   === Function to Calculate Hours for Each Row ===
function calculateHours() {
  const rows = document.querySelectorAll('#table-body tr');
  rows.forEach(row => {
    const startTimeInput = row.querySelector('.start-time');
    const endTimeInput = row.querySelector('.end-time');

    if (startTimeInput && endTimeInput) {
      startTimeInput.addEventListener('input', () => updateHours(row));
      endTimeInput.addEventListener('input', () => updateHours(row));
    }
  });
}



//   === Function to Update Hours and other Columns ===
function updateHours(row) {
  const startTimeInput = row.querySelector('.start-time')?.value.trim();
  const endTimeInput = row.querySelector('.end-time')?.value.trim();
  const hoursCalculatedCell = row.querySelector('.hours-calculated');

  // Calculate hours
  if (startTimeInput && endTimeInput) {
    const hours = calculateTimeDifference(startTimeInput, endTimeInput);
    hoursCalculatedCell.value = isNaN(hours) ? '' : hours.toFixed(2);
  } else {
    hoursCalculatedCell.value = '';
}



//           === Recalculate Sick And Vacation For All Rows And Yearly Summary ===

// Input Select values 1 Columns 16 & 17 Only For Sick Days And Days Off sick/vacation
document.addEventListener('input', (e) => {
  const input = e.target;
  const col = input.closest('td');
  if (!col) return;

  const index = [...col.parentNode.children].indexOf(col);

  // Column 17 ONLY (Vacation)
  if (index === 16) {
    const value = input.value.trim();

    // Accept "1" or "1.00"
    if (value !== "1" && value !== "1.00") {
      input.value = "";
    }
  }
});



// === Run monthly summary calculations once ===

function runAllMonthlyCalculationsOnce() {
  const rows = document.querySelectorAll('#table-body tr');

  rows.forEach(row => {
    try {
          updateColumn8(row);
          updateColumn9(row);
          updateColumn10(row);
          updateColumn11(row);
          updateColumn12(row);
          updateColumn13(row);
          updateColumn14(row);
          updateColumn15(row);
          updateColumn16(row);
          updateColumn17(row);
          updateColumn18(row);
          updateColumn19(row);
          updateColumn23(row);
          updateColumn24(row);
    } catch (err) {
    }
  });

    calculateTotalHoursCalculatedForMonth();
    calculateHoursCalculatedRegularDayForMonth();
    calculatetotalExtraHoursRegularDayForMonth();
    calculateExtraHours125RegularDayForMonth();
    calculateExtraHours150RegularDayForMonth();
    calculateExtraHours150HolidaysSaturdayForMonth();
    calculateExtraHours175HolidaysSaturdayForMonth();
    calculateExtraHours200HolidaysSaturdayForMonth();
    calculateSickDayForMonth();
    calculateDayOffForMonth();
    calculateFoodBreakForMonth();
    calculateFinalTotalHoursForMonth();
    calculateWorkDayForMonth();
    calculateMissingWorkDayForMonth();

    calculateTotalRegularDayPaymentForMonth();
    calculateTotalExtraHours125RegularDayPaymentForMonth();
    calculateTotalExtraHours150RegularDayPaymentForMonth();
    calculateTotalExtraHours150HolidaysSaturdayPaymentForMonth();
    calculateTotalExtraHours175HolidaysSaturdayPaymentForMonth();
    calculateTotalExtraHours200HolidaysSaturdayPaymentForMonth();
    calculateTotalFoodBreakUnpaidOffPaymentForMonth();
    calculateFinalTotalsHoursPaidForMonth();
    calculateFinalTotalsLunchValuePaidForMonth();

    preserveSickDayValue();
    preserveDayOffValue();
    updateSickDaysInSalaryForm();
    calculateSickDayYearlySummary();
    updateVacationDaysInSalaryForm();
    calculateVacationDayYearlySummary();

    updateTotalWorkDays();
    calculateFinalTotalExtraHoursWeekendForMonth();
    updateTotalsLunchValueForm();
    updateTotalMissingHours();
    updateTotalFinalExtraWeekendHours();
    updateTotalFinalExtraRegularHours();
    calculationsAdditionalPayments();
    updateIncomeTaxBeforeCredit();
    updateTaxLevelPercentage();
    calculateAboveCeilingFund();

    updateHoursFoodBreakUnpaid();
    updateHoursRegular125();
    updateHoursRegular150();
    updateHoursHolidaysSaturday150();
    updateHoursHolidaysSaturday175();
    updateHoursHolidaysSaturday200();

    updateTaxFormFields(data);
    updateBasicSalary();
    validateAndCalculateForm();
}

 
// === Recalculate all sick days by date (for the whole month) ===
function recalcAllSickDaysByDate(allRows) {
    if (window.sickLock) return;
    window.sickLock = true;

    const sickRows = [];

    allRows.forEach(r => {
        const sickCell = r.querySelector('td:nth-child(16) input');
        if (!sickCell) return;

        const val = sickCell.value.trim();
        if (val === '') return;

        const dateStr = r.cells[1].textContent.trim();
        if (!dateStr) return;

        const [d, m, y] = dateStr.split('/').map(Number);
        if (!d || !m || !y) return;

        const rowDate = new Date(y, m - 1, d);
        sickRows.push({ row: r, date: rowDate });
    });

    sickRows.sort((a, b) => a.date - b.date);

    // Apply sick rules
    sickRows.forEach((item, i) => {
        const r = item.row;

        const sickCell           = r.querySelector('td:nth-child(16) input');
        const startTimeInput     = r.querySelector('td:nth-child(5) input');
        const endTimeInput       = r.querySelector('td:nth-child(6) input');
        const basicHoursCell     = r.querySelector('td:nth-child(8) input');      
        const finalTotal         = r.querySelector('.final-totals-hours');
        const missingWorkDayCell = r.querySelector('.missing-work-day');
        const hoursCalculatedCell = r.querySelector('.hours-calculated');         

        const index = i + 1;

        let sickPoint = 0;
        let paidHours = 0;
        let startTime = '';
        let endTime   = '';

        if (index === 1) {
            sickPoint = 0;
            paidHours = 0;
            startTime = '00:00';
            endTime   = '00:00';
        } else if (index === 2 || index === 3) {
            sickPoint = 0.5;
            paidHours = 4;
            startTime = '08:00';
            endTime   = '12:00';
        } else {
            sickPoint = 1;
            paidHours = 8;
            startTime = '08:00';
            endTime   = '16:00';
        }

        // Update row
        if (sickCell) sickCell.value = sickPoint.toFixed(2);
        if (startTimeInput) startTimeInput.value = startTime;
        if (endTimeInput) endTimeInput.value = endTime;
        if (basicHoursCell) basicHoursCell.value = paidHours.toFixed(2);
        if (finalTotal) finalTotal.value = paidHours.toFixed(2);
        if (missingWorkDayCell) missingWorkDayCell.value = paidHours.toFixed(2);
        if (hoursCalculatedCell) hoursCalculatedCell.value = paidHours.toFixed(2);

        if (basicHoursCell)
            basicHoursCell.dispatchEvent(new Event('input', { bubbles: true }));
        if (finalTotal)
            finalTotal.dispatchEvent(new Event('input', { bubbles: true }));
        if (missingWorkDayCell)
            missingWorkDayCell.dispatchEvent(new Event('input', { bubbles: true }));
    });

    window.sickLock = false;
}



// Add event listener to column 16 cells Sick and column 17 Vacation to update the DOM on change
document.querySelectorAll('#table-body tr').forEach((row, index, allRows) => {

  const sickInput          = row.querySelector('td:nth-child(16) input');
  const vacationInput      = row.querySelector('td:nth-child(17) input');
  const startTimeInput     = row.querySelector('td:nth-child(5) input');
  const endTimeInput       = row.querySelector('td:nth-child(6) input');
  const basicHoursCell     = row.querySelector('td:nth-child(8) input');
  const finalTotal         = row.querySelector('.final-totals-hours');
  const missingWorkDayCell = row.querySelector('.missing-work-day');


    let previousSickValue     = '';
    let previousVacationValue = '';
    let sickTimeout;
    let vacationTimeout;

// === Sick Day Listener ===
  if (sickInput) {
    sickInput.addEventListener('input', () => {
      clearTimeout(sickTimeout);
      sickTimeout = setTimeout(() => {

        const sickValue = sickInput.value.trim();
        if (sickValue === previousSickValue) return;
        previousSickValue = sickValue;

        // If there was vacation → clear it and recalc the row
        if (vacationInput && vacationInput.value.trim() !== '') {
          vacationInput.value = '';
          previousVacationValue = '';
        }

        if (sickValue !== '') {

          // Clear only this row's time/hour fields
          const clearCells = [
            '.start-time', '.end-time', '.hours-calculated',
            '.hours-calculated-regular-day', '.total-extra-hours-regular-day',
            '.extra-hours125-regular-day', '.extra-hours150-regular-day',
            '.hours-holidays-day', '.extra-hours150-holidays-saturday',
            '.extra-hours175-holidays-saturday', '.extra-hours200-holidays-saturday',
            '.food-break'
          ];

          clearCells.forEach(sel => {
            const cell = row.querySelector(sel);
            if (cell) cell.value = '';
          });

          // Apply sick rules for all rows
          recalcAllSickDaysByDate(allRows);

        } else {
          // Sick removed → clear only this row
          if (startTimeInput) startTimeInput.value = '';
          if (endTimeInput) endTimeInput.value = '';
          if (basicHoursCell) basicHoursCell.value = '';
          if (finalTotal) finalTotal.value = '';
          if (missingWorkDayCell) missingWorkDayCell.value = '';

          const hoursCalculated = row.querySelector('.hours-calculated');
          if (hoursCalculated) hoursCalculated.value = '';

          // Recalculate sick sequence again (maybe other days still sick)
          recalcAllSickDaysByDate(allRows);
        }

        // Monthly calculations
        runAllMonthlyCalculationsOnce();
     }, 150);
    });
  }



// === Vacation Day Listener ===
  if (vacationInput) {
    vacationInput.addEventListener('input', () => {
      clearTimeout(vacationTimeout);
      vacationTimeout = setTimeout(() => {

      const vacationValue = vacationInput.value.trim();

      if (vacationValue === previousVacationValue) return;
      previousVacationValue = vacationValue;

      if (sickInput && sickInput.value.trim() !== '') {
        sickInput.value = '';
        previousSickValue = '';
      }

      if (vacationValue !== '') {

        // Clear only this row's time/hour fields
        const clearCells = [
          '.start-time', '.end-time', '.hours-calculated',
          '.hours-calculated-regular-day', '.total-extra-hours-regular-day',
          '.extra-hours125-regular-day', '.extra-hours150-regular-day',
          '.hours-holidays-day', '.extra-hours150-holidays-saturday',
          '.extra-hours175-holidays-saturday', '.extra-hours200-holidays-saturday',
          '.food-break'
        ];

        clearCells.forEach(sel => {
          const cell = row.querySelector(sel);
          if (cell) cell.value = '';
        });

        // Vacation = 8 hours
        if (startTimeInput) startTimeInput.value = '08:00';
        if (endTimeInput) endTimeInput.value = '16:00';
        if (basicHoursCell) basicHoursCell.value = '8.00';

        const hoursCalculated = row.querySelector(".hours-calculated");
        if (hoursCalculated) hoursCalculated.value = "8.00";

        if (finalTotal) finalTotal.value = '8.00';
        if (missingWorkDayCell) missingWorkDayCell.value = '8.00';

        // DOM dynamic update
        if (basicHoursCell)
          basicHoursCell.dispatchEvent(new Event('input', { bubbles: true }));
        if (finalTotal)
          finalTotal.dispatchEvent(new Event('input', { bubbles: true }));
        if (missingWorkDayCell)
          missingWorkDayCell.dispatchEvent(new Event('input', { bubbles: true }));

        recalcAllSickDaysByDate(allRows);

      } else {

        // === Vaction Removed ===
        if (startTimeInput) startTimeInput.value = "";
        if (endTimeInput) endTimeInput.value = "";
        if (basicHoursCell) basicHoursCell.value = "";
        if (finalTotal) finalTotal.value = "";
        if (missingWorkDayCell) missingWorkDayCell.value = "";

        const hoursCalculated = row.querySelector(".hours-calculated");
        if (hoursCalculated) hoursCalculated.value = "";

        recalcAllSickDaysByDate(allRows);
      }

        // Monthly calculations
        runAllMonthlyCalculationsOnce();
      }, 150);
    });
  }
});

              // ===   calculate Sick Day Yearly Summary ===

function calculateSickDayYearlySummary() {
  const totalFieldSick = document.getElementById('sick_days_salary_yearly');
  const entitlementFieldSick = document.getElementById('sick_days_entitlement');
  const balanceFieldSick = document.getElementById('sick_days_balance_yearly');

  const sick_days_salary_yearly = parseFloatEmployee(totalFieldSick?.value);

  const sickDaysEntitlement = 18;
  const sickDaysBalance = sickDaysEntitlement - sick_days_salary_yearly;

  if (entitlementFieldSick) entitlementFieldSick.value = sickDaysEntitlement.toFixed(2);
  if (balanceFieldSick) balanceFieldSick.value = sickDaysBalance.toFixed(2);
}

// ===   calculate Vacation Day Yearly Summary ===
function calculateVacationDayYearlySummary() {
  const totalFieldVacation = document.getElementById('vacation_days_salary_yearly');
  const entitlementFieldVacation = document.getElementById('vacation_days_entitlement');
  const balanceFieldVacation = document.getElementById('vacation_balance_yearly');

  const vacation_days_salary_yearly = parseFloatEmployee(totalFieldVacation?.value);
  
  const vacationDaysEntitlement = 12;
  const vacationDaysBalance = vacationDaysEntitlement - vacation_days_salary_yearly;

  if (entitlementFieldVacation) entitlementFieldVacation.value = vacationDaysEntitlement.toFixed(2);
  if (balanceFieldVacation) balanceFieldVacation.value = vacationDaysBalance.toFixed(2);
}



// === Add event listener to column 25 cells AdvancePay to update the DOM on change ===
document.querySelectorAll('#table-body tr td:nth-child(25)').forEach(cell => {
  cell.addEventListener('input', () => {
    preserveAdvancePaymentValue(); // Save and restore value
    calculateAdvancePaymentForMonth();
    updateTotalAdvancePayment();
  });
});



       // ===   Run Update All Columns Rows Calculations ===

// Main Function for global Updates Dynamically after Cell Changes (8 to 25 columns)
    for (let i = 8; i <= 25; i++) {
        const updateColumnCell = row.querySelector(`.update-column-${i}`);
        if (updateColumnCell) {
      updateColumnCell.textContent = `Updated ${i}`;
     }
  }

// Update other columns
        updateColumn8(row);
        updateColumn9(row);
        updateColumn10(row);
        updateColumn11(row);
        updateColumn12(row);
        updateColumn13(row);
        updateColumn14(row);
        updateColumn15(row);
        updateColumn16(row);
        updateColumn17(row);
        updateColumn18(row);
        updateColumn19(row);
        updateColumn23(row);
        updateColumn24(row);

// Update employee details employee selected from combobox And Call function to calculate total payment for the month
        updateEmployeeDetails(); // employee combobox 
        calculateTotalRegularDayPaymentForMonth(); // Column 8
        calculateTotalExtraHours125RegularDayPaymentForMonth(); // Column 10
        calculateTotalExtraHours150RegularDayPaymentForMonth(); // Column 11
        calculateTotalExtraHours150HolidaysSaturdayPaymentForMonth(); // Column 13
        calculateTotalExtraHours175HolidaysSaturdayPaymentForMonth(); // Column 14
        calculateTotalExtraHours200HolidaysSaturdayPaymentForMonth(); // Column 15
        calculateTotalFoodBreakUnpaidOffPaymentForMonth(); // Column 18
        calculateFinalTotalsHoursPaidForMonth(); // Column 19
        calculateFinalTotalsLunchValuePaidForMonth(); // Column 23

// Call the functions to calculate total hours for each column
        calculateTotalHoursCalculatedForMonth();
        calculateHoursCalculatedRegularDayForMonth();
        calculatetotalExtraHoursRegularDayForMonth();
        calculateExtraHours125RegularDayForMonth();
        calculateExtraHours150RegularDayForMonth();
        calculateExtraHours150HolidaysSaturdayForMonth();
        calculateExtraHours175HolidaysSaturdayForMonth();
        calculateExtraHours200HolidaysSaturdayForMonth();
        calculateSickDayForMonth();
        calculateDayOffForMonth();
        calculateFoodBreakForMonth();
        calculateFinalTotalHoursForMonth();
        calculateWorkDayForMonth();
        calculateMissingWorkDayForMonth();

        updateSickDaysInSalaryForm();
        calculateSickDayYearlySummary(); 
        updateVacationDaysInSalaryForm();
        calculateVacationDayYearlySummary(); 

        updateTotalWorkDays();
        calculateFinalTotalExtraHoursWeekendForMonth(); 
        updateTotalsLunchValueForm();
        calculateFinalTotalsLunchValuePaidForMonth();
        updateTotalMissingHours();
        updateTotalFinalExtraWeekendHours();
        updateTotalFinalExtraRegularHours();
        calculationsAdditionalPayments();
        updateIncomeTaxBeforeCredit();
        updateTaxLevelPercentage();
        calculateAboveCeilingFund();

        updateHoursFoodBreakUnpaid();
        updateHoursRegular125();
        updateHoursRegular150();
        updateHoursHolidaysSaturday150();
        updateHoursHolidaysSaturday175();
        updateHoursHolidaysSaturday200();
        checkWeeklyHours();

        updateTaxFormFields(data);      
        updateBasicSalary();
        validateAndCalculateForm();
  }




               // Function to Calculate Employer Tax Payment All הפרשות מעביד  


// Function To Calculate Employer Pension Fund (קופות גמל מעביד)
function employerPensionFund() {
    // Get necessary fields
    const regularHoursPaidCell = document.querySelector('.hours-calculated-regular-day-paid'); // Regular hours worked
    const employerPensionFundCell = document.getElementById('pension_fund'); // Output field

    // Constant for Employer Pension Fund percentage
    const Employer_Pension_Fund_Value = 0.065;

    // Helper to strip currency symbols or formatting
    function parseFormattedValue(value) {
        return parseFloat(value.replace(/[^0-9.-]+/g, "")) || 0;
    }

    if (regularHoursPaidCell && employerPensionFundCell) {
        const regularHoursPaid = parseFormattedValue(regularHoursPaidCell.value);
        const employerPensionFund = regularHoursPaid * Employer_Pension_Fund_Value;

        const formattedPensionFund = employerPensionFund.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });

        employerPensionFundCell.value = formattedPensionFund;
    }
}



// Function To Calculate Employer Compensation (פיצויים מעביד)

function employerCompensation() {
    const regularHoursPaidCell = document.querySelector('.hours-calculated-regular-day-paid');
    const employerCompensationCell = document.getElementById('compensation');
    const Employer_Compensation_Value = 0.0833;

    function parseFormattedValue(value) {
        return parseFloat(value.replace(/[^0-9.-]+/g, "")) || 0;
    }

    if (regularHoursPaidCell && employerCompensationCell) {
        const regularHoursPaid = parseFormattedValue(
            regularHoursPaidCell.value || regularHoursPaidCell.textContent || "0"
        );

        const employerCompensation = regularHoursPaid * Employer_Compensation_Value;

        const formattedCompensation = employerCompensation.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });

        employerCompensationCell.value = formattedCompensation;
    }
}

document.getElementById('hours-calculated-regular-day-paid')?.addEventListener('input', () => {

    employerCompensation();
});



// Function To Calculate Employer Study Fund (קרן השתלמות מעביד)
function employerStudyFund() {
    const regularHoursPaidCell = document.querySelector('.hours-calculated-regular-day-paid');
    const employerStudyFundCell = document.getElementById('study_fund');
    const Employer_Study_Fund_Value = 0.075;

    function parseFormattedValue(value) {
        return parseFloat(value.replace(/[^0-9.-]+/g, "")) || 0;
    }

    if (regularHoursPaidCell && employerStudyFundCell) {
        const regularHoursPaid = parseFormattedValue(
            regularHoursPaidCell.value || regularHoursPaidCell.textContent || "0"
        );

        const employerStudyFund = regularHoursPaid * Employer_Study_Fund_Value;

        const formattedStudyFund = employerStudyFund.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });

        employerStudyFundCell.value = formattedStudyFund;
    }
}



// Function To Calculate Employer Disability Fund (אובדן כושר מעביד)
function employerDisability() {
    const regularHoursPaidCell = document.querySelector('.hours-calculated-regular-day-paid');
    const employerDisabilityCell = document.getElementById('disability');
    const Employer_Disability_Fund_Value = 0.01;

    function parseFormattedValue(value) {
        return parseFloat(value.replace(/[^0-9.-]+/g, "")) || 0;
    }

    if (regularHoursPaidCell && employerDisabilityCell) {
        const regularHoursPaid = parseFormattedValue(
            regularHoursPaidCell.value || regularHoursPaidCell.textContent || "0"
        );

        const employerDisabilityFund = regularHoursPaid * Employer_Disability_Fund_Value;

        const formattedDisabilityFund = employerDisabilityFund.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });

        employerDisabilityCell.value = formattedDisabilityFund;
    }
}



// Function To Calculate Employer miscellaneous שונות
function updateMiscellaneousValue() {
  const miscCell = document.getElementById('miscellaneous');
  if (!miscCell) return;

  // Parse the raw input
  const rawValue = miscCell.value.replace(/[^0-9.-]+/g, "");
  const miscAmount = parseFloat(rawValue) || 0;

  // Store it in your fieldValues object
  fieldValues.miscellaneous = miscAmount;

  // Format and display the value back in the input (no currency symbol)
  miscCell.value = isNaN(miscAmount)
    ? ""
    : miscAmount.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
}



// Function To Calculate Employer National Insurance ביטוח לאומי מעביד לשנת 2025
const nationalInsuranceEmployerData = [
  { fromAmount: 0, toAmount: 7522, employerRate: 0.0451 },     // מדרגה 1
  { fromAmount: 7522, toAmount: 50695, employerRate: 0.076 }    // מדרגה 2
];

// Function to calculate Employer National Insurance with value preservation
function employerNationalInsurance() {
  const grossTaxableField = document.getElementById('gross_taxable');
  const employerNationalInsuranceField = document.getElementById('national_insurance');

  if (!grossTaxableField || !employerNationalInsuranceField) return;

  const currentValue = employerNationalInsuranceField.value || '';
  const grossTaxable = parseFloat(grossTaxableField.value.replace(/[^0-9.-]+/g, "")) || 0;

  let level1Contribution = 0;
  let level2Contribution = 0;

  // Level 1: Up to 7,522
  const level1Limit = nationalInsuranceEmployerData[0].toAmount;
  const level1Rate = nationalInsuranceEmployerData[0].employerRate;

  const level1Amount = Math.min(grossTaxable, level1Limit);
  level1Contribution = level1Amount * level1Rate;

  // Level 2: From 7,522 up to 50,695
  const level2Threshold = nationalInsuranceEmployerData[1].fromAmount;
  const level2Limit = nationalInsuranceEmployerData[1].toAmount;
  const level2Rate = nationalInsuranceEmployerData[1].employerRate;

  const level2Amount = Math.max(0, Math.min(grossTaxable, level2Limit) - level2Threshold);
  level2Contribution = level2Amount * level2Rate;

  const totalContributions = level1Contribution + level2Contribution;

  employerNationalInsuranceField.value = isNaN(totalContributions)
    ? currentValue
    : totalContributions.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
}



// Function To Calculate Employer Salary Tax Value מס שכר
function updateSalaryTaxValue() {
  const salaryTaxCell = document.getElementById('salary_tax_input');
  if (!salaryTaxCell) return;

  // Parse the raw input
  const rawValue = salaryTaxCell.value.replace(/[^0-9.-]+/g, "");
  const salaryTaxAmount = parseFloat(rawValue) || 0;

  // Store it in your fieldValues object
  fieldValues.salary_tax = salaryTaxAmount;

  // Format and display the value back in the input (no ₪ symbol)
  salaryTaxCell.value = isNaN(salaryTaxAmount)
    ? ""
    : salaryTaxAmount.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
}



// Function to calculate Additional Payments תוספות שונות שאינן מזכות בזכויות סוציאליות
  function calculationsAdditionalPayments() {
    const contractStatusField = document.getElementById('contract_status'); 
    const regularHoursPaidCell = document.querySelector('.hours-calculated-regular-day-paid'); 
    const totalPaidTotalHoursCell = document.querySelector('.final-totals-hours-paid'); 
    const totalPaidLunchValueCell = document.querySelector('.final-totals-lunch-value-paid'); 
    const thirteenthSalaryField = document.getElementById('thirteenth_salary'); 
    const mobileValueField = document.getElementById('mobile_value'); 
    const clothingValueField = document.getElementById('clothing_value'); 
    const additionalPaymentsCell = document.getElementById('additional_payments');

    if (!regularHoursPaidCell || !totalPaidTotalHoursCell || !additionalPaymentsCell || 
        !thirteenthSalaryField || !mobileValueField || !clothingValueField || !totalPaidLunchValueCell) {
      return;
    }

    const contractStatus = contractStatusField?.value.trim() || ''; 
    const regularHoursPaid = parseFloat(regularHoursPaidCell?.value.replace(/[,]/g, "").trim()) || 0;
    const totalPaidTotalHours = parseFloat(totalPaidTotalHoursCell?.value.replace(/[,]/g, "").trim()) || 0;
    const thirteenthSalary = parseFloat(thirteenthSalaryField?.value.replace(/[,]/g, "").trim()) || 0;
    const mobileValue = parseFloat(mobileValueField?.value.replace(/[,]/g, "").trim()) || 0;
    const clothingValue = parseFloat(clothingValueField?.value.replace(/[,]/g, "").trim()) || 0;
    const totalPaidLunchValue = parseFloat(totalPaidLunchValueCell?.value.replace(/[,]/g, "").trim()) || 0;

    if (!totalPaidTotalHours || isNaN(totalPaidTotalHours)) {
      additionalPaymentsCell.value = '';
      additionalPaymentsCell.dataset.rawValue = '0.00';
      return;
    }

    let additionalPayments;
    if (contractStatus === "אישי") {
      additionalPayments = thirteenthSalary + mobileValue + clothingValue + totalPaidLunchValue;
    } else {
      additionalPayments = totalPaidTotalHours - regularHoursPaid;
    }

    additionalPayments = isNaN(additionalPayments) ? 0 : additionalPayments;

    const formattedSalary = additionalPayments === 0 ? '' : additionalPayments.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });

    additionalPaymentsCell.value = formattedSalary;
    additionalPaymentsCell.dataset.rawValue = additionalPayments.toFixed(2);
  }

  // **Hide Visable Fields On Salary**
  function toggleContractFields() {
    const status = document.getElementById('contract_status')?.value.trim();
    const personalFields = document.querySelectorAll('.personal-only');
    const contractFields = document.querySelectorAll('.contract-only');

    personalFields.forEach(el => {
      el.style.display = (status === 'אישי') ? 'table-cell' : 'none';
    });

    contractFields.forEach(el => {
      el.style.display = (status === 'אישי') ? 'none' : 'table-cell';
    });
  }

  function toggleAboveCeilingFund() {
    const valueElement = document.getElementById('above_ceiling_fund_display');
    if (!valueElement) return;

    const rawValue = parseFloat(valueElement.dataset.rawValue || "0");
    const ceilingFields = document.querySelectorAll('.above-ceiling-only');

    ceilingFields.forEach(el => {
      el.style.display = rawValue > 0 ? 'table-cell' : 'none';
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    // Wait for DOM + layout to be ready
    setTimeout(() => {
      toggleContractFields();           
      toggleAboveCeilingFund();         
    }, 50);

    document.getElementById('contract_status')?.addEventListener('change', () => {
      toggleContractFields();
      toggleAboveCeilingFund();
    });

    document.addEventListener('input', () => {
      toggleAboveCeilingFund();
    });
  });



               // Function to Calculate For Update All  

// Function to Calculate National Insurance Deductions Employee All ניכוי ביטוח לאומי עובד
// Constants and data for calculations
const nationalInsuranceData = [
    { fromAmount: 0, toAmount: 7522, employerRate: 0.0104 }, // Level 1
    { fromAmount: 7522, toAmount: 50695, employerRate: 0.07 }  // Level 2
];

// Function to calculate national insurance deductions with value preservation Employee
function updateNationalInsuranceDeductions() {
  const grossTaxableCell = document.getElementById('gross_taxable');
  const deductionsCell = document.getElementById('national_insurance_deductions');
  const dobField = document.getElementById('date_of_birth');

  if (!grossTaxableCell || !deductionsCell) return;

  const currentValue = deductionsCell.value || '';
  const grossTaxable = parseFloat(grossTaxableCell.value.replace(/[^0-9.-]+/g, "")) || 0;

  // --- AGE CHECK ---
  let age = null;
  if (dobField?.value) {
    let birthDate;
    if (dobField.value.includes("-")) {
      birthDate = new Date(dobField.value);
    } else if (dobField.value.includes("/")) {
      const p = dobField.value.split("/");
      birthDate = new Date(`${p[2]}-${p[1]}-${p[0]}`);
    }
    if (!isNaN(birthDate)) {
      const today = new Date();
      age = today.getFullYear() - birthDate.getFullYear();
      const m = today.getMonth() - birthDate.getMonth();
      if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) age--;
    }
  }

  // --- REDUCED RATE CHECK ---
  const isReduced = age !== null && (age < 18 || age >= 67);

  // --- APPLY RATES ---
  const rate1 = isReduced ? 0.01 : nationalInsuranceData[0].employerRate;
  const rate2 = isReduced ? 0.01 : nationalInsuranceData[1].employerRate;

  let level1Deductions = 0;
  let level2Deductions = 0;

  if (grossTaxable <= nationalInsuranceData[0].toAmount) {
    level1Deductions = grossTaxable * rate1;
  } else {
    level1Deductions = nationalInsuranceData[0].toAmount * rate1;
  }

  if (grossTaxable > nationalInsuranceData[1].fromAmount) {
    const taxableAmount = Math.min(grossTaxable, nationalInsuranceData[1].toAmount) - nationalInsuranceData[1].fromAmount;
    level2Deductions = taxableAmount * rate2;
  }

  const totalDeductions = level1Deductions + level2Deductions;

  deductionsCell.value = isNaN(totalDeductions)
    ? currentValue
    : totalDeductions.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
}



// Function to Calculate Health Insurance Deductions Employee All ניכוי ביטוח בריאות עובד
// Constants and data for health insurance calculations
const healthInsuranceData = [
    { name: "Level 1", fromAmount: 0, toAmount: 7522, employerRate: 0.0323 }, // Level 1
    { name: "Level 2", fromAmount: 7522, toAmount: 50695, employerRate: 0.0517 }  // Level 2
];

// Function to calculate Employee health insurance deductions with value preservation
function updateHealthInsuranceDeductions() {
  const grossTaxableCell = document.getElementById('gross_taxable');
  const deductionsCell = document.getElementById('health_insurance_deductions');
  const dobField = document.getElementById('date_of_birth');

  if (!grossTaxableCell || !deductionsCell) return;

  const currentValue = deductionsCell.value || '';
  const grossTaxable = parseFloat(grossTaxableCell.value.replace(/[^0-9.-]+/g, "")) || 0;

  // --- AGE CHECK ---
  let age = null;
  if (dobField?.value) {
    let birthDate;
    if (dobField.value.includes("-")) {
      birthDate = new Date(dobField.value);
    } else if (dobField.value.includes("/")) {
      const p = dobField.value.split("/");
      birthDate = new Date(`${p[2]}-${p[1]}-${p[0]}`);
    }
    if (!isNaN(birthDate)) {
      const today = new Date();
      age = today.getFullYear() - birthDate.getFullYear();
      const m = today.getMonth() - birthDate.getMonth();
      if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) age--;
    }
  }

  // --- REDUCED RATE CHECK ---
  const isReduced = age !== null && (age < 18 || age >= 67);

  // --- APPLY RATES ---
  const rate1 = isReduced ? 0.03 : healthInsuranceData[0].employerRate;
  const rate2 = isReduced ? 0.03 : healthInsuranceData[1].employerRate;

  let level1Deductions = 0;
  let level2Deductions = 0;

  if (grossTaxable <= healthInsuranceData[0].toAmount) {
    level1Deductions = grossTaxable * rate1;
  } else {
    level1Deductions = healthInsuranceData[0].toAmount * rate1;
  }

  if (grossTaxable > healthInsuranceData[1].fromAmount) {
    const taxableAmount = Math.min(grossTaxable, healthInsuranceData[1].toAmount) - healthInsuranceData[1].fromAmount;
    level2Deductions = taxableAmount * rate2;
  }

  const totalDeductions = level1Deductions + level2Deductions;

  deductionsCell.value = isNaN(totalDeductions)
    ? currentValue
    : totalDeductions.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
}



// Function to calculate the above ceiling fund based on salary thresholds שווי קרן השתלמות מעל התקרה
function calculateAboveCeilingFund() {
  const grossSalaryCell = document.getElementById('gross_salary');
  const regularHoursPaidCell = document.querySelector('.hours-calculated-regular-day-paid');
  const aboveCeilingFundCell = document.getElementById('above_ceiling_fund');
  const aboveCeilingFundDisplay = document.getElementById('above_ceiling_fund_display');

  const ceilingFields = document.querySelectorAll('.above-ceiling-only');

  const Employer_Ceiling_Fund_Percent_Value = 0.075;
  const Employer_Ceiling_Fund_toAmount_Value = 15712.00;

  function parseFormattedValue(value) {
    return parseFloat(value.replace(/[^0-9.-]+/g, "")) || 0;
  }

  if (grossSalaryCell && regularHoursPaidCell && aboveCeilingFundCell && aboveCeilingFundDisplay) {
    const grossSalary = parseFormattedValue(grossSalaryCell.value);
    const regularHoursPaid = parseFormattedValue(regularHoursPaidCell.value);

    let aboveCeilingFund = 0;

    if (grossSalary >= 1 && regularHoursPaid > Employer_Ceiling_Fund_toAmount_Value) {
      aboveCeilingFund = (regularHoursPaid - Employer_Ceiling_Fund_toAmount_Value) * Employer_Ceiling_Fund_Percent_Value;
    }

    const formattedValue = aboveCeilingFund.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });

    aboveCeilingFundCell.value = formattedValue;
    aboveCeilingFundDisplay.textContent = formattedValue;
    aboveCeilingFundDisplay.dataset.rawValue = aboveCeilingFund.toString();

    //  Hide or show label + result
    ceilingFields.forEach(el => {
      el.style.display = aboveCeilingFund > 0 ? '' : 'none';
    });
  }
}



// Function To Calculate Monthly City Tax Tops סכום זיכוי ישוב חודשי
function calculateMonthlyCityTaxTops() {
    const grossTaxableElement = document.getElementById('gross_taxable');
    const cityTaxRateElement = document.getElementById('city_value_percentage');
    const cityTaxTopElement = document.getElementById('monthly_city_tax_tops');
    const finalCityTaxBenefitElement = document.getElementById('final_city_tax_benefit');

    const grossTaxable = parseFloat(grossTaxableElement?.value.replace(/[^0-9.-]+/g, "") || "0");
    const cityTaxRate = parseFloat(cityTaxRateElement?.value.replace(/[^0-9.-]+/g, "")) / 100 || 0;
    const monthlyCityTaxTop = parseFloat(cityTaxTopElement?.value.replace(/[^0-9.-]+/g, "")) || 0;

    const calculatedCityTaxBenefit = grossTaxable * cityTaxRate;
    const finalCityTaxBenefit = Math.min(calculatedCityTaxBenefit, monthlyCityTaxTop * cityTaxRate);

    if (finalCityTaxBenefitElement) {
        finalCityTaxBenefitElement.value = finalCityTaxBenefit.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    }

    return finalCityTaxBenefit;
}



//  Monthly Tax Credit
function calculateMonthlyTaxCredit() {
    const TAX_CREDIT_POINT_VALUE = 2904.0;
    const taxCreditPointsElement = document.getElementById('tax_credit_points');
    const taxCreditPoints = parseFloatEmployee(taxCreditPointsElement?.value || "0");

    const monthlyTaxCredit = (TAX_CREDIT_POINT_VALUE * taxCreditPoints) / 12;

    document.getElementById('amount_tax_credit_points_monthly').value = monthlyTaxCredit.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });
}



     // Function To Calculate and Update Income Tax מס הכנסה

// Function to Update Tax Level Percentage All Full Tax Calculation Block (Functions 1–6)
//  Constants
const Minimum_Wage_Economy_Value = 5880.02;
const Income_Tax_Credit_From_Provident_Fund_Contributions_Value = 0.35;
const Pension_Insurance_Tax_Benefit_Up_To_Amount_Yearly = 8148.00;
const Pension_Insurance_Tax_Benefit_Up_To_Amount_Monthly =
    Pension_Insurance_Tax_Benefit_Up_To_Amount_Yearly / 12;

// Updated Tax Brackets for 2025 
const taxBrackets = [
  { fromAmount: 0, toAmount: 7010, taxRate: 10.00 },
  { fromAmount: 7011, toAmount: 10060, taxRate: 14.00 },
  { fromAmount: 10061, toAmount: 16150, taxRate: 20.00 },
  { fromAmount: 16151, toAmount: 22440, taxRate: 31.00 },
  { fromAmount: 22441, toAmount: 46690, taxRate: 35.00 },
  { fromAmount: 46691, toAmount: 60130, taxRate: 47.00 },
  { fromAmount: 60131, toAmount: Infinity, taxRate: 50.00 }
];

// Number Formatter (no currency symbol)
function formatNumber(value) {
  return value.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

// 1. Total Salary Pension Funds
function totalSalaryPensionFunds() {
  const regularHoursPaid = parseFloat(
    document.querySelector('.hours-calculated-regular-day-paid')?.value.replace(/[^0-9.-]+/g, "") || "0"
  );
  const output = document.getElementById('total_salary_pension_funds');

  // Always only regular salary, no contract check, no 13th salary
  const total = regularHoursPaid;

  if (output) output.value = formatNumber(total);
}

// 2. Employee Pension Fund
function employeePensionFund() {
  const basicSalary = parseFloat(document.getElementById('basic_salary')?.value.replace(/[^0-9.-]+/g, "") || "0");
  const totalSalary = parseFloat(document.getElementById('total_salary_pension_funds')?.value.replace(/[^0-9.-]+/g, "") || "0");
  const output = document.getElementById('employee_pension_fund');

  if (!basicSalary) {
    if (output) output.value = "0.00";
    return;
  }

  const pension = totalSalary * 0.06;
  if (output) output.value = formatNumber(pension);
}

// 3. Tax Level Percentage
function updateTaxLevelPercentage() {
  const grossTaxable = parseFloat(document.getElementById('gross_taxable')?.value.replace(/[^0-9.-]+/g, "") || "0");
  const output = document.getElementById('tax_level_precente');
  const bracket = taxBrackets.find(b => grossTaxable >= b.fromAmount && grossTaxable < b.toAmount);
  if (output) output.value = bracket ? `${bracket.taxRate.toFixed(2)}%` : "";
}

// 4. Income Tax Before Credit (after deductions)
function updateIncomeTaxBeforeCredit() {
  const grossTaxableField = document.getElementById('gross_taxable');
  const selfEmployedPensionFundField = document.getElementById('self_employed_pension_fund');
  const studyFundDeductionsField = document.getElementById('study_fund_deductions');
  const output = document.getElementById('income_tax_before_credit');

  const grossTaxable = parseFloat(grossTaxableField?.value.replace(/[^0-9.-]+/g, "") || "0");
  const selfEmployedPensionFund = parseFloat(selfEmployedPensionFundField?.value.replace(/[^0-9.-]+/g, "") || "0");
  const studyFundDeductions = parseFloat(studyFundDeductionsField?.value.replace(/[^0-9.-]+/g, "") || "0");

  const SelfEmployed_Max_Monthly = 38412 / 12;
  const StudyFund_Max_Monthly = 13202 / 12;

  const selfEmployedDeductible = Math.min(selfEmployedPensionFund, SelfEmployed_Max_Monthly);
  const studyFundDeductible = Math.min(studyFundDeductions, StudyFund_Max_Monthly);

  const taxableIncome = grossTaxable - selfEmployedDeductible - studyFundDeductible;

  if (taxableIncome < 1) {
    if (output) output.value = "0.00";
    return;
  }

  let totalTax = 0;
  let remaining = taxableIncome;

  for (const bracket of taxBrackets) {
    const taxable = Math.min(remaining, bracket.toAmount - bracket.fromAmount);
    if (taxable > 0) {
      totalTax += taxable * (bracket.taxRate / 100);
      remaining -= taxable;
    }
    if (remaining <= 0) break;
  }

  if (output) {
    output.value = formatNumber(totalTax);
    output.dataset.rawValue = totalTax.toFixed(2);
  }
}

// 5. Final Income Tax Calculation
function calculateIncomeTax() {
  const grossTaxableField = document.getElementById('gross_taxable');
  const incomeTaxBeforeCreditField = document.getElementById('income_tax_before_credit');
  const creditPointsMonthlyField = document.getElementById('amount_tax_credit_points_monthly');
  const childTaxPointsField = document.getElementById('tax_point_child');
  const employeePensionFundField = document.getElementById('employee_pension_fund');
  const incomeTaxField = document.getElementById('income_tax');

  const grossTaxable = parseFloat(grossTaxableField?.value.replace(/[^0-9.-]+/g, "") || "0");
  const incomeTaxBeforeCredit = parseFloat(incomeTaxBeforeCreditField?.dataset.rawValue || "0");
  const creditPointsMonthly = parseFloat(creditPointsMonthlyField?.value.replace(/[^0-9.-]+/g, "") || "0");
  const childTaxPoints = parseFloat(childTaxPointsField?.value.replace(/[^0-9.-]+/g, "") || "0");
  const employeePension = parseFloat(employeePensionFundField?.value.replace(/[^0-9.-]+/g, "") || "0");
  const output = incomeTaxField;

  const Pension_Insurance_Tax_Benefit_Up_To_Amount_Monthly = 679;
  const Income_Tax_Credit_From_Provident_Fund_Contributions_Value = 0.35;

  let pensionRefund = 0;
  if (incomeTaxBeforeCredit > 0 && employeePension > 0) {
    const maxBySalary = grossTaxable * 0.07;
    const maxAllowed = Math.min(maxBySalary, Pension_Insurance_Tax_Benefit_Up_To_Amount_Monthly);
    const eligibleAmount = Math.min(employeePension, maxAllowed);
    pensionRefund = eligibleAmount * Income_Tax_Credit_From_Provident_Fund_Contributions_Value;
  }

  let taxAfterCredits = incomeTaxBeforeCredit
    - creditPointsMonthly
    - pensionRefund;

  const finalCityTaxBenefit = calculateMonthlyCityTaxTops();
  const finalTax = Math.max(0, taxAfterCredits - finalCityTaxBenefit - childTaxPoints);

  if (output) output.value = formatNumber(finalTax);
}



// Function To Calculate Self Employed Pension Fund קופ"ג לעצמאיים (סעיף 47)
function selfEmployedPensionFund() {
  const additionalPaymentsField = document.getElementById('additional_payments');
  const selfEmployedPensionFundField = document.getElementById('self_employed_pension_fund');
  const dateOfBirthField = document.getElementById('date_of_birth');
  const carsValueField = document.getElementById('cars_value');

  const additionalPayments = parseFloat(additionalPaymentsField?.value.replace(/[^0-9.-]+/g, "")) || 0;
  const carsValue = parseFloat(carsValueField?.value.replace(/[^0-9.-]+/g, "")) || 0;

  // --- Age calculation ---
  let age = 0;
  if (dateOfBirthField?.value) {
    let birthDate;
    if (dateOfBirthField.value.includes("-")) {
      birthDate = new Date(dateOfBirthField.value);
    } else if (dateOfBirthField.value.includes("/")) {
      const parts = dateOfBirthField.value.split("/");
      birthDate = new Date(`${parts[2]}-${parts[1]}-${parts[0]}`);
    }

    if (birthDate instanceof Date && !isNaN(birthDate)) {
      const today = new Date();
      age = today.getFullYear() - birthDate.getFullYear();
      const m = today.getMonth() - birthDate.getMonth();
      if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
        age--;
      }
    }
  }

  // --- Deduction rate depends on age ---
  const deductionRate = age >= 50 ? 0.075 : 0.05;

  // --- Base for deduction ---
  const totalForDeduction = carsValue > 0 ? additionalPayments + carsValue : additionalPayments;
  const deductionAmount = totalForDeduction * deductionRate;

  // --- Update DOM ---
  if (selfEmployedPensionFundField) {
    // keep raw numeric for calculations
    selfEmployedPensionFundField.dataset.rawValue = deductionAmount.toFixed(2);

    // show formatted number in the input (no currency symbol)
    selfEmployedPensionFundField.value = deductionAmount.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }
}



// Function To Calculate Study Fund Deductions קרן השתלמות
function studyFundDeductions() {
    const basicSalaryField = document.getElementById('basic_salary');
    const totalSalaryPensionFundsField = document.getElementById('total_salary_pension_funds');
    const studyFundDeductionsField = document.getElementById('study_fund_deductions');
    const Study_Fund_Deductions_Value = 0.025;

    const basicSalary = parseFloat(basicSalaryField?.value.replace(/[^0-9.-]+/g, "")) || 0;

    if (!basicSalary && studyFundDeductionsField) {
        studyFundDeductionsField.value = '0.00';
        return;
    }

    const totalSalaryPensionFunds = parseFloat(totalSalaryPensionFundsField?.value.replace(/[^0-9.-]+/g, "")) || 0;
    const studyFundDeductions = totalSalaryPensionFunds * Study_Fund_Deductions_Value;

    const formattedValue = studyFundDeductions.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });

    if (studyFundDeductionsField) {
        studyFundDeductionsField.value = formattedValue;
    }
}



// Function To Calculate Employee miscellaneous ניכויים שונים
function updateMiscellaneousDeductionsValue() {
  const miscCell = document.getElementById('miscellaneous_deductions');
  if (!miscCell) return;

  // Parse the raw input
  const rawValue = miscCell.value.replace(/[^0-9.-]+/g, "");
  const miscAmount = parseFloat(rawValue) || 0;

  // Store it in your fieldValues object
  fieldValues.miscellaneous = miscAmount;

  // Format and display the value back in the input (no currency symbol)
  miscCell.value = isNaN(miscAmount)
    ? ""
    : miscAmount.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
}



// Function to Update the Basic Salary based on Tax Form
function updateBasicSalary() {
    const regularHoursPaidCell = document.querySelector('.hours-calculated-regular-day-paid'); // Updated field
    const basicSalaryCell = document.getElementById('basic_salary'); // Field for basic salary

    if (regularHoursPaidCell !== null && basicSalaryCell !== null) {
        const regularHoursPaid = parseFloat(regularHoursPaidCell.value.replace(/[^0-9.-]+/g, "")) || 0;

        // Format the salary without currency symbol
        const formattedSalary = regularHoursPaid.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });

        basicSalaryCell.value = isNaN(regularHoursPaid) ? '' : formattedSalary;
    }
}



// Function to Update the Totals Lunch Value based on Tax Form
function updateTotalsLunchValueForm() {
    const lunchValuePaidCell = document.querySelector('.final-totals-lunch-value-paid'); // Updated field
    const totalsLunchValueCell = document.getElementById('totals_lunch_value'); // Field for Lunch Value

    if (lunchValuePaidCell !== null && totalsLunchValueCell !== null) {
        const lunchValuePaid = parseFloat(lunchValuePaidCell.value.replace(/[^0-9.-]+/g, "")) || 0;

        // Format the salary without currency symbol
        const formattedlunchValue = lunchValuePaid.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });

        totalsLunchValueCell.value = isNaN(lunchValuePaid) ? '' : formattedlunchValue;
    }
}



// Function to Update the Total Work Days on Tax Form
function updateTotalWorkDays() {
  const workDayCells = document.querySelectorAll('.work-day-monthly');
  const totalWorkDaysCell = document.getElementById('total_work_days'); // target cell for result

  let total = 0;
  workDayCells.forEach(cell => {
    const val = parseFloat(cell.value.replace(/[^0-9.-]+/g, "")) || 0;
    total += val;
  });

  // Always show 0.0 if empty
  totalWorkDaysCell.value = total.toFixed(1); // e.g. "0.0", "3.0"
}



// Function to Update Total Missing Hours on Tax Form
function updateTotalMissingHours() {
  const missingHoursCells = document.querySelectorAll('.missing-work-day-monthly');
  const totalMissingHoursCell = document.getElementById('total_missing_hours'); // target cell for result

  let total = 0;
  missingHoursCells.forEach(cell => {
    const val = parseFloat(cell.value.replace(/[^0-9.-]+/g, "")) || 0;
    total += val;
  });

  // Always show 0.0 if empty
  totalMissingHoursCell.value = total.toFixed(1); // e.g. "0.0", "8.0"
}



// Function to update Sick Days in Salary Form
function updateSickDaysInSalaryForm() {
    const sickDayMonthlyCell = document.querySelector('.sick-day-monthly'); // Source field
    const salaryFormSickDayCell = document.getElementById('sick_days_salary'); // Target field in salary form

    if (sickDayMonthlyCell !== null && salaryFormSickDayCell !== null) {
        const sickDays = parseFloat(sickDayMonthlyCell.value.replace(/[^0-9.-]+/g, "")) || 0;

        // Format with 2 decimals (not currency, just number)
        const formattedSickDays = sickDays === 0 ? '' : sickDays.toFixed(2);

        salaryFormSickDayCell.value = formattedSickDays;
    }
}



// Function to update Vacation Days in Salary Form
function updateVacationDaysInSalaryForm() {
    const dayOffMonthlyCell = document.querySelector('.day-off-monthly'); // Source field
    const salaryFormVacationCell = document.getElementById('vacation_days_salary'); // Target field in salary form

    if (dayOffMonthlyCell !== null && salaryFormVacationCell !== null) {
        const vacationDays = parseFloat(dayOffMonthlyCell.value.replace(/[^0-9.-]+/g, "")) || 0;

        // Format with 2 decimals (not currency, just number)
        const formattedVacationDays = vacationDays === 0 ? '' : vacationDays.toFixed(2);

        salaryFormVacationCell.value = formattedVacationDays;
    }
}



// Function to Update the Final Total Extra Hours Monthly based on Tax Form
function updateTotalFinalExtraWeekendHours() {
  const extraHoursMonthlyCell = document.querySelectorAll('.final-total-extra-hours-weekend-monthly');
  const totalFinalExtraHoursCell = document.getElementById('final_extra_hours_weekend'); // target cell for result

  let total = 0;
  extraHoursMonthlyCell.forEach(cell => {
    const val = parseFloat(cell.value.replace(/[^0-9.-]+/g, "")) || 0;
    total += val;
  });

  // Always show 0.0 if empty
  totalFinalExtraHoursCell.value = total.toFixed(1); // e.g. "0.0", "3.0"
}



// Function to Update the Final Total Extra Regular Hours Monthly based on Tax Form
function updateTotalFinalExtraRegularHours() {
  const extraRegularHoursMonthlyCell = document.querySelectorAll('.total-extra-hours-regular-day-monthly');
  const totalFinalExtraHoursRegularCell = document.getElementById('final_extra_hours_regular'); // target cell for result

  let total = 0;
  extraRegularHoursMonthlyCell.forEach(cell => {
    const val = parseFloat(cell.value.replace(/[^0-9.-]+/g, "")) || 0;
    total += val;
  });

  // Always show 0.0 if empty
  totalFinalExtraHoursRegularCell.value = total.toFixed(1); // e.g. "0.0", "3.0"
}



// Function to Update the Final Total Extra Regular Hours 125 Paid Monthly based on Tax Form
function updateHoursRegular125() {
    const extraHoursRegular125Cell = document.querySelector('.extra-hours125-regular-day-paid'); // Updated field
    const hoursRegular125Cell = document.getElementById('hours125_regular_salary'); // Field for basic salary

    if (extraHoursRegular125Cell !== null && hoursRegular125Cell !== null) {
        const extraHoursRegular125 = parseFloat(extraHoursRegular125Cell.value.replace(/[^0-9.-]+/g, "")) || 0;

        // Format the salary without currency symbol
        const formattedSalary = extraHoursRegular125.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });

        hoursRegular125Cell.value = isNaN(extraHoursRegular125) ? '' : formattedSalary;
    }
}



// Function to Update the Final Total Extra Regular Hours 150 Paid Monthly based on Tax Form
function updateHoursRegular150() {
    const extraHoursRegular150Cell = document.querySelector('.extra-hours150-regular-day-paid'); // Updated field
    const hoursRegular150Cell = document.getElementById('hours150_regular_salary'); // Field for basic salary

    if (extraHoursRegular150Cell !== null && hoursRegular150Cell !== null) {
        const extraHoursRegular150 = parseFloat(extraHoursRegular150Cell.value.replace(/[^0-9.-]+/g, "")) || 0;

        // Format the salary without currency symbol
        const formattedSalary = extraHoursRegular150.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });

        hoursRegular150Cell.value = isNaN(extraHoursRegular150) ? '' : formattedSalary;
    }
}



// Function to Update the Final Total Extra Holidays Saturday Hours 150 Paid Monthly based on Tax Form
function updateHoursHolidaysSaturday150() {
    const extraHoursHolidaysSaturday150Cell = document.querySelector('.extra-hours150-holidays-saturday-paid'); // Updated field
    const hoursHolidaysSaturday150Cell = document.getElementById('hours150_holidays_saturday_salary'); // Field for basic salary

    if (extraHoursHolidaysSaturday150Cell !== null && hoursHolidaysSaturday150Cell !== null) {
        const extraHoursHolidaysSaturday150 = parseFloat(extraHoursHolidaysSaturday150Cell.value.replace(/[^0-9.-]+/g, "")) || 0;

        // Format the salary without currency symbol
        const formattedSalary = extraHoursHolidaysSaturday150.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });

        hoursHolidaysSaturday150Cell.value = isNaN(extraHoursHolidaysSaturday150) ? '' : formattedSalary;
    }
}



// Function to Update the Final Total Extra Holidays Saturday Hours 175 Paid Monthly based on Tax Form
function updateHoursHolidaysSaturday175() {
    const extraHoursHolidaysSaturday175Cell = document.querySelector('.extra-hours175-holidays-saturday-paid'); // Updated field
    const hoursHolidaysSaturday175Cell = document.getElementById('hours175_holidays_saturday_salary'); // Field for basic salary

    if (extraHoursHolidaysSaturday175Cell !== null && hoursHolidaysSaturday175Cell !== null) {
        const extraHoursHolidaysSaturday175 = parseFloat(extraHoursHolidaysSaturday175Cell.value.replace(/[^0-9.-]+/g, "")) || 0;

        // Format the salary without currency symbol
        const formattedSalary = extraHoursHolidaysSaturday175.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });

        hoursHolidaysSaturday175Cell.value = isNaN(extraHoursHolidaysSaturday175) ? '' : formattedSalary;
    }
}



// Function to Update the Final Total Extra Holidays Saturday Hours 200 Paid Monthly based on Tax Form
function updateHoursHolidaysSaturday200() {
    const extraHoursHolidaysSaturday200Cell = document.querySelector('.extra-hours200-holidays-saturday-paid'); // Updated field
    const hoursHolidaysSaturday200Cell = document.getElementById('hours200_holidays_saturday_salary'); // Field for basic salary

    if (extraHoursHolidaysSaturday200Cell !== null && hoursHolidaysSaturday200Cell !== null) {
        const extraHoursHolidaysSaturday200 = parseFloat(extraHoursHolidaysSaturday200Cell.value.replace(/[^0-9.-]+/g, "")) || 0;

        // Format the salary without currency symbol
        const formattedSalary = extraHoursHolidaysSaturday200.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });

        hoursHolidaysSaturday200Cell.value = isNaN(extraHoursHolidaysSaturday200) ? '' : formattedSalary;
    }
}



// Function to Update the Final Total Hours Food Break Unpaid Monthly based on Tax Form
function updateHoursFoodBreakUnpaid() {
    const foodBreakUnpaidCell = document.querySelector('.food-break-unpaid'); // Updated field
    const foodBreakUnpaidSalaryCell = document.getElementById('food_break_unpaid_salary'); // Field for basic salary

    if (foodBreakUnpaidCell !== null && foodBreakUnpaidSalaryCell !== null) {
        const foodBreakUnpaid = parseFloat(foodBreakUnpaidCell.value.replace(/[^0-9.-]+/g, "")) || 0;

        // Format the salary without currency symbol
        const formattedSalary = foodBreakUnpaid.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });

        foodBreakUnpaidSalaryCell.value = isNaN(foodBreakUnpaid) ? '' : formattedSalary;
    }
}



               // Function to Calculate Advance Payment For Update All Very Importtant  


function preserveAdvancePaymentValue() {
  const advancePaymentField = document.getElementById('advance_payment_salary');
  if (!advancePaymentField) return;

  const currentValue = advancePaymentField.value;

  validateAndCalculateForm(); // עדכון חישובים

// recalculate before restoring
  calculateAdvancePaymentForMonth(); 

  advancePaymentField.value = currentValue; // שחזור הערך
}

// Function to update the Total Advance Payment On Tax Form
function updateTotalAdvancePayment() {
    const advancePaymentMonthlyCells = document.querySelectorAll('.advance-payment-paid');
    const advancePaymentCell = document.getElementById('advance_payment_salary');

    let advancePaymentTotal = 0;

    advancePaymentMonthlyCells.forEach(cell => {
        const value = parseFloat(cell.value.replace(/[^0-9.-]+/g, "")) || 0;
        advancePaymentTotal += value;
    });

    if (advancePaymentCell !== null) {
        advancePaymentCell.value = isNaN(advancePaymentTotal)
            ? ''
            : advancePaymentTotal.toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
    }
}



               // Function to Calculate Sick Day  For Update All Very Importtant  

function preserveSickDayValue() {
  const sickDayField = document.querySelector('.sick-day-monthly');
  if (!sickDayField) return;

  const currentValue = sickDayField.value;

  validateAndCalculateForm(); // עדכון חישובים

  calculateSickDayForMonth(); // recalculate before restoring

  sickDayField.value = currentValue; // שחזור הערך
}



               // Function to Calculate Day Off Vacztion For Update All Very Importtant  

function preserveDayOffValue() {
  const dayOffField = document.querySelector('.day-off-monthly');
  if (!dayOffField) return;

  const currentValue = dayOffField.value;

  validateAndCalculateForm(); // עדכון חישובים

  calculateDayOffForMonth(); // recalculate before restoring

  dayOffField.value = currentValue; // שחזור הערך
}



        // Function to Calculate Total Payment All calculated Paid monthly for the Month 


// Function to calculate total payment for the hours calculated regular day paid for Column 8
function calculateTotalRegularDayPaymentForMonth() {
    const hoursCalculatedRegularDayMonthlyCell = document.querySelector('.hours-calculated-regular-day-monthly');
    const hoursCalculatedRegularDayPaidCell = document.querySelector('.hours-calculated-regular-day-paid');
    const hourlyRateCell = document.getElementById('hourly_rate');

    // Helper function to parse formatted numbers (e.g., remove currency symbols)
    function parseFormattedValue(value) {
        return parseFloat(value.replace(/[^0-9.-]+/g, "")) || 0;
    }

    // Ensure all necessary elements exist before proceeding
    if (hoursCalculatedRegularDayMonthlyCell && hourlyRateCell && hoursCalculatedRegularDayPaidCell) {
        const totalHours = parseFormattedValue(hoursCalculatedRegularDayMonthlyCell.value);
        const hourlyRate = parseFormattedValue(hourlyRateCell.value);
        const totalPaid = totalHours * hourlyRate;

        hoursCalculatedRegularDayPaidCell.value = isNaN(totalPaid) ? '0.00' : `${totalPaid.toFixed(2)}`;
    }
}

// Function to calculate total payment for the extra hours at 125% for regular days (Column 10)
function calculateTotalExtraHours125RegularDayPaymentForMonth() {
    const extraHours125RegularDayMonthlyCell = document.querySelector('.extra-hours125-regular-day-monthly');
    const extraHours125RegularDayPaidCell = document.querySelector('.extra-hours125-regular-day-paid');
    const hourlyRateCell = document.getElementById('hourly_rate');

    // Helper function to parse formatted numbers (e.g., remove currency symbols)
    function parseFormattedValue(value) {
        return parseFloat(value.replace(/[^0-9.-]+/g, "")) || 0;
    }

    // Ensure all necessary elements exist before proceeding
    if (extraHours125RegularDayMonthlyCell && hourlyRateCell && extraHours125RegularDayPaidCell) {
        const totalExtra125 = parseFormattedValue(extraHours125RegularDayMonthlyCell.value);
        const hourlyRate = parseFormattedValue(hourlyRateCell.value);
        const totalPaidExtra125 = totalExtra125 * hourlyRate * 1.25; // Multiply by 1.25

        extraHours125RegularDayPaidCell.value = isNaN(totalPaidExtra125) ? '0.00' : `${totalPaidExtra125.toFixed(2)}`;
    }
}

// Function to calculate total payment for the extra hours at 150% for regular days (Column 11)
function calculateTotalExtraHours150RegularDayPaymentForMonth() {
    const extraHours150RegularDayMonthlyCell = document.querySelector('.extra-hours150-regular-day-monthly');
    const extraHours150RegularDayPaidCell = document.querySelector('.extra-hours150-regular-day-paid');
    const hourlyRateCell = document.getElementById('hourly_rate');

    // Helper function to parse formatted numbers (e.g., remove currency symbols)
    function parseFormattedValue(value) {
        return parseFloat(value.replace(/[^0-9.-]+/g, "")) || 0;
    }

    // Ensure all necessary elements exist before proceeding
    if (extraHours150RegularDayMonthlyCell && hourlyRateCell && extraHours150RegularDayPaidCell) {
        const totalExtra150 = parseFormattedValue(extraHours150RegularDayMonthlyCell.value);
        const hourlyRate = parseFormattedValue(hourlyRateCell.value);
        const totalPaidExtra150 = totalExtra150 * hourlyRate * 1.5; // Multiply by 1.5

        extraHours150RegularDayPaidCell.value = isNaN(totalPaidExtra150) ? '0.00' : `${totalPaidExtra150.toFixed(2)}`;
    }
}

// Function to calculate total payment for the extra hours at 150% for holidays and Saturdays (Column 13)
function calculateTotalExtraHours150HolidaysSaturdayPaymentForMonth() {
    const extraHours150HolidaysSaturdayMonthlyCell = document.querySelector('.extra-hours150-holidays-saturday-monthly');
    const extraHours150HolidaysSaturdayPaidCell = document.querySelector('.extra-hours150-holidays-saturday-paid');
    const hourlyRateCell = document.getElementById('hourly_rate');

    // Helper function to parse formatted numbers (e.g., remove currency symbols)
    function parseFormattedValue(value) {
        return parseFloat(value.replace(/[^0-9.-]+/g, "")) || 0;
    }

    // Ensure all necessary elements exist before proceeding
    if (extraHours150HolidaysSaturdayMonthlyCell && hourlyRateCell && extraHours150HolidaysSaturdayPaidCell) {
        const totalExtra150HolidaysSaturday = parseFormattedValue(extraHours150HolidaysSaturdayMonthlyCell.value);
        const hourlyRate = parseFormattedValue(hourlyRateCell.value);
        const totalPaidExtra150HolidaysSaturday = totalExtra150HolidaysSaturday * hourlyRate * 1.5; // Multiply by 1.5

        extraHours150HolidaysSaturdayPaidCell.value = isNaN(totalPaidExtra150HolidaysSaturday) ? '0.00' : `${totalPaidExtra150HolidaysSaturday.toFixed(2)}`;
    }
}

// Function to calculate total payment for the extra hours at 175% for holidays and Saturdays (Column 14)
function calculateTotalExtraHours175HolidaysSaturdayPaymentForMonth() {
    const extraHours175HolidaysSaturdayMonthlyCell = document.querySelector('.extra-hours175-holidays-saturday-monthly');
    const extraHours175HolidaysSaturdayPaidCell = document.querySelector('.extra-hours175-holidays-saturday-paid');
    const hourlyRateCell = document.getElementById('hourly_rate');

    // Helper function to parse formatted numbers (e.g., remove currency symbols)
    function parseFormattedValue(value) {
        return parseFloat(value.replace(/[^0-9.-]+/g, "")) || 0;
    }

    // Ensure all necessary elements exist before proceeding
    if (extraHours175HolidaysSaturdayMonthlyCell && hourlyRateCell && extraHours175HolidaysSaturdayPaidCell) {
        const totalExtra175HolidaysSaturday = parseFormattedValue(extraHours175HolidaysSaturdayMonthlyCell.value);
        const hourlyRate = parseFormattedValue(hourlyRateCell.value);
        const totalPaidExtra175HolidaysSaturday = totalExtra175HolidaysSaturday * hourlyRate * 1.75; // Multiply by 1.75

        extraHours175HolidaysSaturdayPaidCell.value = isNaN(totalPaidExtra175HolidaysSaturday) ? '0.00' : `${totalPaidExtra175HolidaysSaturday.toFixed(2)}`;
    }
}

// Function to calculate total payment for the extra hours at 200% for holidays and Saturdays (Column 15)
function calculateTotalExtraHours200HolidaysSaturdayPaymentForMonth() {
    const extraHours200HolidaysSaturdayMonthlyCell = document.querySelector('.extra-hours200-holidays-saturday-monthly');
    const extraHours200HolidaysSaturdayPaidCell = document.querySelector('.extra-hours200-holidays-saturday-paid');
    const hourlyRateCell = document.getElementById('hourly_rate');

    // Helper function to parse formatted numbers (e.g., remove currency symbols)
    function parseFormattedValue(value) {
        return parseFloat(value.replace(/[^0-9.-]+/g, "")) || 0;
    }

    // Ensure all necessary elements exist before proceeding
    if (extraHours200HolidaysSaturdayMonthlyCell && hourlyRateCell && extraHours200HolidaysSaturdayPaidCell) {
        const totalExtra200HolidaysSaturday = parseFormattedValue(extraHours200HolidaysSaturdayMonthlyCell.value);
        const hourlyRate = parseFormattedValue(hourlyRateCell.value);
        const totalPaidExtra200HolidaysSaturday = totalExtra200HolidaysSaturday * hourlyRate * 2; // Multiply by 2

        extraHours200HolidaysSaturdayPaidCell.value = isNaN(totalPaidExtra200HolidaysSaturday) ? '0.00' : `${totalPaidExtra200HolidaysSaturday.toFixed(2)}`;
    }
}

// Function to calculate total payment for sick days (Column 16)

// Function to calculate total payment for days off (Column 17)

// Function to calculate unpaid amount for food breaks (Column 18)
function calculateTotalFoodBreakUnpaidOffPaymentForMonth() {
    const foodBreakMonthlyCell = document.querySelector('.food-break-monthly');
    const foodBreakUnpaidCell = document.querySelector('.food-break-unpaid');
    const hourlyRateCell = document.getElementById('hourly_rate');

    // Helper function to parse formatted numbers (e.g., remove currency symbols)
    function parseFormattedValue(value) {
        return parseFloat(value.replace(/[^0-9.-]+/g, "")) || 0;
    }

    // Ensure all necessary elements exist before proceeding
    if (foodBreakMonthlyCell && hourlyRateCell && foodBreakUnpaidCell) {
        const foodBreakHours = parseFormattedValue(foodBreakMonthlyCell.value);
        const hourlyRate = parseFormattedValue(hourlyRateCell.value);
        const totalFoodBreakUnpaid = foodBreakHours * hourlyRate; // Calculation

        foodBreakUnpaidCell.value = isNaN(totalFoodBreakUnpaid) ? '0.00' : `${totalFoodBreakUnpaid.toFixed(2)}`;
        foodBreakUnpaidCell.style.color = 'red'; // Set the font color to red for the total cell
    }
}

// Function to calculate the final total hours paid for the month for Column 19
function calculateFinalTotalsHoursPaidForMonth() {
    const hoursCalculatedRegularDayMonthlyCell = document.querySelector('.hours-calculated-regular-day-monthly'); // Column 8
    const extraHours125RegularDayMonthlyCell = document.querySelector('.extra-hours125-regular-day-monthly'); // Column 10
    const extraHours150RegularDayMonthlyCell = document.querySelector('.extra-hours150-regular-day-monthly'); // Column 11
    const extraHours150HolidaysSaturdayMonthlyCell = document.querySelector('.extra-hours150-holidays-saturday-monthly'); // Column 13
    const extraHours175HolidaysSaturdayMonthlyCell = document.querySelector('.extra-hours175-holidays-saturday-monthly'); // Column 14
    const extraHours200HolidaysSaturdayMonthlyCell = document.querySelector('.extra-hours200-holidays-saturday-monthly'); // Column 15
    const foodBreakMonthlyCell = document.querySelector('.food-break-monthly'); // Column 18
    const totalPaidTotalHoursCell = document.querySelector('.final-totals-hours-paid'); // Column 19

    // Ensure all elements are found
    if (
        hoursCalculatedRegularDayMonthlyCell &&
        extraHours125RegularDayMonthlyCell &&
        extraHours150RegularDayMonthlyCell &&
        extraHours150HolidaysSaturdayMonthlyCell &&
        extraHours175HolidaysSaturdayMonthlyCell &&
        extraHours200HolidaysSaturdayMonthlyCell &&
        foodBreakMonthlyCell &&
        totalPaidTotalHoursCell
    ) {
        // Helper function to parse formatted numbers (e.g., remove currency symbols)
        function parseFormattedValue(value) {
            return parseFloat(value.replace(/[^0-9.-]+/g, "")) || 0;
        }

        // Get hourly rate and parse it correctly
        const hourlyRate = parseFormattedValue(document.getElementById('hourly_rate').value);

        // Parse all input values
        const hoursCalculatedRegularDay = parseFormattedValue(hoursCalculatedRegularDayMonthlyCell.value);
        const extraHours125RegularDay = parseFormattedValue(extraHours125RegularDayMonthlyCell.value);
        const extraHours150RegularDay = parseFormattedValue(extraHours150RegularDayMonthlyCell.value);
        const extraHours150HolidaysSaturday = parseFormattedValue(extraHours150HolidaysSaturdayMonthlyCell.value);
        const extraHours175HolidaysSaturday = parseFormattedValue(extraHours175HolidaysSaturdayMonthlyCell.value);
        const extraHours200HolidaysSaturday = parseFormattedValue(extraHours200HolidaysSaturdayMonthlyCell.value);
        const foodBreakHours = parseFormattedValue(foodBreakMonthlyCell.value);

        // Perform the calculation
        const totalPaidHours =
            (hoursCalculatedRegularDay * hourlyRate) +
            (extraHours125RegularDay * hourlyRate * 1.25) +
            (extraHours150RegularDay * hourlyRate * 1.5) +
            (extraHours150HolidaysSaturday * hourlyRate * 1.5) +
            (extraHours175HolidaysSaturday * hourlyRate * 1.75) +
            (extraHours200HolidaysSaturday * hourlyRate * 2.0) -
            (foodBreakHours * hourlyRate);

        // Format the result as plain number (no currency symbol)
        const formattedTotal = totalPaidHours.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });

        // Set the value to the calculated result or a fallback if invalid
        totalPaidTotalHoursCell.value = isNaN(totalPaidHours) ? '0.00' : formattedTotal;
    }
}


// Function to calculate the final total hours lunch value paid for the month for Column 23
function calculateFinalTotalsLunchValuePaidForMonth() {
    const workDayMonthlyCell = document.querySelector('.work-day-monthly');
    const totalPaidLunchValueCell = document.querySelector('.final-totals-lunch-value-paid'); // Column 23
    const lunchValueCell = document.getElementById('lunch_value');

    // Helper function to parse formatted numbers (e.g., remove currency symbols)
    function parseFormattedValue(value) {
        return parseFloat(value.replace(/[^0-9.-]+/g, "")) || 0;
    }

         // Ensure all necessary elements exist before proceeding
    if (workDayMonthlyCell && lunchValueCell && totalPaidLunchValueCell) {
        const totalworkDay = parseFormattedValue(workDayMonthlyCell.value);
        const lunchValue = parseFormattedValue(lunchValueCell.value);
        const totalPaidworkDay = totalworkDay * lunchValue; // Calculation

        totalPaidLunchValueCell.value = isNaN(totalPaidworkDay) ? '0.00' : `${totalPaidworkDay.toFixed(2)}`;
        totalPaidLunchValueCell.style.color = 'red'; // Set the font color to red for the total cell
    }
}

        // Function to Calculate Total Hours All calculated monthly for the Month 


// Function to calculate total hours calculated monthly for the month for Column 7
function calculateTotalHoursCalculatedForMonth() {
    var totalHours = 0;
    const rows = document.querySelectorAll('#table-body tr');

    rows.forEach(row => {
        const hoursCalculatedCell = row.querySelector('.hours-calculated');
        if (hoursCalculatedCell && hoursCalculatedCell.value) {
            totalHours += parseFloat(hoursCalculatedCell.value) || 0;
        }
    });

    // Display total hours in the specific cell with class 'hours-calculated-monthly'
    const hoursCalculatedMonthlyCell = document.querySelector('.hours-calculated-monthly');
    if (hoursCalculatedMonthlyCell !== null) {
        hoursCalculatedMonthlyCell.value = totalHours === 0 ? '' : totalHours.toFixed(2);
    }
}

// Function to calculate hours calculated regular day for the month for Column 8
function calculateHoursCalculatedRegularDayForMonth() {
    var totalHours = 0;
    const rows = document.querySelectorAll('#table-body tr');

    rows.forEach(row => {
        const hoursCalculatedRegularDayCell = row.querySelector('.hours-calculated-regular-day');
        if (hoursCalculatedRegularDayCell && hoursCalculatedRegularDayCell.value) {
            totalHours += parseFloat(hoursCalculatedRegularDayCell.value) || 0;
        }
    });

    // Display total hours in the specific cell with class 'hours-calculated-regular-day-monthly'
    const hoursCalculatedRegularDayMonthlyCell = document.querySelector('.hours-calculated-regular-day-monthly');
    if (hoursCalculatedRegularDayMonthlyCell !== null) {
        hoursCalculatedRegularDayMonthlyCell.value = totalHours === 0 ? '' : totalHours.toFixed(2);
    }
}

// Function to calculate hours calculated total extra hours regular day for the month for Column 9
function calculatetotalExtraHoursRegularDayForMonth() {
  let totalHours = 0;
  const rows = document.querySelectorAll('#table-body tr');

  rows.forEach(row => {
    const extraHoursCell = row.querySelector('.total-extra-hours-regular-day');
    if (extraHoursCell && extraHoursCell.value) {
      totalHours += parseFloat(extraHoursCell.value) || 0;
    }
  });

  // Display total in the monthly summary cell
  const monthlyTotalCell = document.querySelector('.total-extra-hours-regular-day-monthly');
  if (monthlyTotalCell !== null) {
    monthlyTotalCell.value = totalHours === 0 ? '' : totalHours.toFixed(2);
  }
}

// Function to calculate extra hours125 regular day for the month for Column 10
function calculateExtraHours125RegularDayForMonth() {
    let totalHours = 0;
    const rows = document.querySelectorAll('#table-body tr');

    rows.forEach(row => {
        const extraHours125RegularDay = row.querySelector('.extra-hours125-regular-day');
        if (extraHours125RegularDay && extraHours125RegularDay.value) {
            totalHours += parseFloat(extraHours125RegularDay.value) || 0;
        }
    });

    // Display total hours in the specific cell with class 'extra-hours125-regular-day-monthly'
    const extraHours125RegularDayMonthlyCell = document.querySelector('.extra-hours125-regular-day-monthly');
    if (extraHours125RegularDayMonthlyCell !== null) {
        extraHours125RegularDayMonthlyCell.value = totalHours === 0 ? '' : totalHours.toFixed(2);
    }
}

// Function to calculate extra hours150 regular day for the month for Column 11
function calculateExtraHours150RegularDayForMonth() {
    let totalHours = 0;
    const rows = document.querySelectorAll('#table-body tr');

    rows.forEach(row => {
        const extraHours150RegularDay = row.querySelector('.extra-hours150-regular-day');
        if (extraHours150RegularDay && extraHours150RegularDay.value) {
            totalHours += parseFloat(extraHours150RegularDay.value) || 0;
        }
    });

    // Display total hours in the specific cell with class 'extra-hours150-regular-day-monthly'
    const extraHours150RegularDayMonthlyCell = document.querySelector('.extra-hours150-regular-day-monthly');
    if (extraHours150RegularDayMonthlyCell !== null) {
        extraHours150RegularDayMonthlyCell.value = totalHours === 0 ? '' : totalHours.toFixed(2);
    }
}

// Function to calculate extra hours150 holidays saturday for the month for Column 13
function calculateExtraHours150HolidaysSaturdayForMonth() {
    let totalHours = 0;
    const rows = document.querySelectorAll('#table-body tr');

    rows.forEach(row => {
        const extraHours150HolidaysSaturday = row.querySelector('.extra-hours150-holidays-saturday');
        if (extraHours150HolidaysSaturday && extraHours150HolidaysSaturday.value) {
            totalHours += parseFloat(extraHours150HolidaysSaturday.value) || 0;
        }
    });

    // Display total hours in the specific cell with class 'extra-hours150-holidays-saturday-monthly'
    const extraHours150HolidaysSaturdayMonthlyCell = document.querySelector('.extra-hours150-holidays-saturday-monthly');
    if (extraHours150HolidaysSaturdayMonthlyCell !== null) {
        extraHours150HolidaysSaturdayMonthlyCell.value = totalHours === 0 ? '' : totalHours.toFixed(2);
    }
}

// Function to calculate extra hours175 holidays saturday for the month for Column 14
function calculateExtraHours175HolidaysSaturdayForMonth() {
    let totalHours = 0;
    const rows = document.querySelectorAll('#table-body tr');

    rows.forEach(row => {
        const extraHours175HolidaysSaturday = row.querySelector('.extra-hours175-holidays-saturday');
        if (extraHours175HolidaysSaturday && extraHours175HolidaysSaturday.value) {
            totalHours += parseFloat(extraHours175HolidaysSaturday.value) || 0;
        }
    });

    // Display total hours in the specific cell with class 'extra-hours175-holidays-saturday-monthly'
    const extraHours175HolidaysSaturdayMonthlyCell = document.querySelector('.extra-hours175-holidays-saturday-monthly');
    if (extraHours175HolidaysSaturdayMonthlyCell !== null) {
        extraHours175HolidaysSaturdayMonthlyCell.value = totalHours === 0 ? '' : totalHours.toFixed(2);
    }
}

// Function to calculate extra hours200 holidays saturday for the month for Column 15
function calculateExtraHours200HolidaysSaturdayForMonth() {
    let totalHours = 0;
    const rows = document.querySelectorAll('#table-body tr');

    rows.forEach(row => {
        const extraHours200HolidaysSaturday = row.querySelector('.extra-hours200-holidays-saturday');
        if (extraHours200HolidaysSaturday && extraHours200HolidaysSaturday.value) {
            totalHours += parseFloat(extraHours200HolidaysSaturday.value) || 0;
        }
    });

    // Display total hours in the specific cell with class 'extra-hours200-holidays-saturday-monthly'
    const extraHours200HolidaysSaturdayMonthlyCell = document.querySelector('.extra-hours200-holidays-saturday-monthly');
    if (extraHours200HolidaysSaturdayMonthlyCell !== null) {
        extraHours200HolidaysSaturdayMonthlyCell.value = totalHours === 0 ? '' : totalHours.toFixed(2);
    }
}

// Function to calculate sick day for the month for Column 16
function calculateSickDayForMonth() {
    let totalHours = 0;
    const rows = document.querySelectorAll('#table-body tr');

    rows.forEach(row => {
        const sickDay = row.querySelector('.sick-day');
        if (sickDay && sickDay.value) {
            totalHours += parseFloat(sickDay.value) || 0;
        }
    });

    // Display total hours in the specific cell with class 'sick-day-monthly'
    const sickDayMonthlyCell = document.querySelector('.sick-day-monthly');
    if (sickDayMonthlyCell !== null) {
        sickDayMonthlyCell.value = totalHours === 0 ? '' : totalHours.toFixed(2);
    }
}

// Function to calculate day off Vacation for the month for Column 17
function calculateDayOffForMonth() {
    let totalHours = 0;
    const rows = document.querySelectorAll('#table-body tr');

    rows.forEach(row => {
        const dayOff = row.querySelector('.day-off');
        if (dayOff && dayOff.value) {
            totalHours += parseFloat(dayOff.value) || 0;
        }
    });

    // Display total hours in the specific cell with class 'day-off-monthly'
    const dayOffMonthlyCell = document.querySelector('.day-off-monthly');
    if (dayOffMonthlyCell !== null) {
        dayOffMonthlyCell.value = totalHours === 0 ? '' : totalHours.toFixed(2);
    }
}

// Function to calculate food break for the month for Column 18
function calculateFoodBreakForMonth() {
    let totalHours = 0;
    const rows = document.querySelectorAll('#table-body tr');

    rows.forEach(row => {
        const foodBreak = row.querySelector('.food-break');
        if (foodBreak && foodBreak.value) {
            totalHours += parseFloat(foodBreak.value) || 0;
        }
    });

    // Display total hours in the specific cell with class 'food-break-monthly'
    const foodBreakMonthlyCell = document.querySelector('.food-break-monthly');
    if (foodBreakMonthlyCell !== null) {
        foodBreakMonthlyCell.value = totalHours === 0 ? '' : totalHours.toFixed(2);
    }
}

// Function to calculate final total hours for the month for Column 19
function calculateFinalTotalHoursForMonth() {
  let totalHours = 0;
  const rows = document.querySelectorAll('#table-body tr');

  rows.forEach(row => {
    const finalTotalHoursCell = row.querySelector('.final-totals-hours');
    if (finalTotalHoursCell && finalTotalHoursCell.value) {
      const value = parseFloat(finalTotalHoursCell.value);
      if (!isNaN(value)) {
        totalHours += value;
      }
    }
  });

  // Display total hours in the specific cell with class 'final-totals-hours-monthly'
  const finalTotalHoursMonthlyCell = document.querySelector('.final-totals-hours-monthly');
  if (finalTotalHoursMonthlyCell !== null) {
    if ('value' in finalTotalHoursMonthlyCell) {
      // If it's an <input>
      finalTotalHoursMonthlyCell.value = totalHours === 0 ? '' : totalHours.toFixed(2);
    } else {
      // If it's a <td>, <span>, <div>, etc.
      finalTotalHoursMonthlyCell.textContent = totalHours === 0 ? '' : totalHours.toFixed(2);
    }
  }
}

// Function to calculate work day for the month for Column 23
function calculateWorkDayForMonth() {
    let totalHours = 0;
    const rows = document.querySelectorAll('#table-body tr');

    rows.forEach(row => {
        const workDayCell = row.querySelector('.work-day');
        if (workDayCell && workDayCell.value) {
            totalHours += parseFloat(workDayCell.value) || 0;
        }
    });

    // Display total hours in the specific cell with class 'work-day-monthly'
    const workDayMonthlyCell = document.querySelector('.work-day-monthly');
    if (workDayMonthlyCell !== null) {
        workDayMonthlyCell.value = totalHours === 0 ? '' : totalHours.toFixed(2);
    }
}

// Function to calculate missing work day for the month for Column 24
function calculateMissingWorkDayForMonth() {
    let totalHours = 0;
    const rows = document.querySelectorAll('#table-body tr');

    rows.forEach(row => {
        const missingWorkDayCell = row.querySelector('.missing-work-day');
        if (missingWorkDayCell && missingWorkDayCell.value) {
            totalHours += parseFloat(missingWorkDayCell.value) || 0;
        }
    });

    // Display total hours in the specific cell with class 'missing-work-day-monthly'
    const missingWorkDayMonthlyCell = document.querySelector('.missing-work-day-monthly');
    if (missingWorkDayMonthlyCell !== null) {
        missingWorkDayMonthlyCell.value = totalHours === 0 ? '' : totalHours.toFixed(2);
    }
}

// Function to calculate the advance payment for the month for Column 25
function calculateAdvancePaymentForMonth() {
    let totalAdvancePayment = 0;
    const cells = document.querySelectorAll('#table-body tr .advance-payment');

    cells.forEach(cell => {
        const raw = cell?.value?.replace(/[^0-9.-]+/g, "") || "0";
        const num = parseFloat(raw);
        totalAdvancePayment += isNaN(num) ? 0 : num;
        cell.style.color = 'red';
    });

    const advancePaymentMonthlyCell = document.querySelector('.advance-payment-paid');
    if (advancePaymentMonthlyCell !== null) {
        advancePaymentMonthlyCell.value = totalAdvancePayment.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
        advancePaymentMonthlyCell.style.color = 'red';
    }
}



// Function to calculate Final Toatal ExtraHours Monthly On Last Row Column 24
function calculateFinalTotalExtraHoursWeekendForMonth() {
  const totalPaidCell = document.querySelector('.final-totals-hours-monthly');     
  const totalRegularCell = document.querySelector('.missing-work-day-monthly');    
  const extraHoursRegularCell = document.querySelector('.total-extra-hours-regular-day-monthly');
  const extraHoursMonthlyCell = document.querySelector('.final-total-extra-hours-weekend-monthly'); 

  const totalPaid = parseFloat(totalPaidCell?.value || totalPaidCell?.textContent) || 0;
  const totalRegular = parseFloat(totalRegularCell?.value || totalRegularCell?.textContent) || 0;
  const extraHoursRegular = parseFloat(extraHoursRegularCell?.value || extraHoursRegularCell?.textContent) || 0;

  const extraHours = totalPaid - totalRegular - extraHoursRegular;

  if (extraHoursMonthlyCell !== null) {
    if ('value' in extraHoursMonthlyCell) {
      extraHoursMonthlyCell.value = extraHours === 0 ? '' : extraHours.toFixed(2);
    } else {
      extraHoursMonthlyCell.textContent = extraHours === 0 ? '' : extraHours.toFixed(2);
    }
  }
}



        // Function to Calculate Total Hours calculated Dayly for Each Column 

function updateColumn8(row) {
  const column8Cell = row.querySelector('.hours-calculated-regular-day');
  const sickInput = row.querySelector('td:nth-child(16) input');
  const vacationInput = row.querySelector('td:nth-child(17) input');

  // SICK OVERRIDE 
  if (sickInput && sickInput.value.trim() !== '') {
    const sickValue = parseFloat(sickInput.value) || 0;
    let sickHours = 0;

    // Count sick days BEFORE this row
    const allRows = Array.from(document.querySelectorAll('#table-body tr'));
    const currentIndex = allRows.indexOf(row);

    let sickCountBefore = 0;
    for (let i = 0; i < currentIndex; i++) {
      const prev = allRows[i].querySelector('td:nth-child(16) input');
      if (prev && prev.value.trim() !== '') sickCountBefore++;
    }

    const sickDayNumber = sickCountBefore + 1;

    if (sickDayNumber === 1) {
      sickValue = 0;
      sickHours = 0;
    } else if (sickDayNumber === 2) {
      sickValue = 0.5;
      sickHours = 4;
    } else if (sickDayNumber === 3) {
      sickValue = 0.5;
      sickHours = 4;
    } else {
      sickValue = 1;
      sickHours = 8;
    }

    column8Cell.value = sickHours.toFixed(2);
    return;
  }

  // VACATION OVERRIDE
  if (vacationInput && vacationInput.value.trim() !== '') {
    const vacationDays = parseFloat(vacationInput.value) || 0;
    const vacationHours = vacationDays * 8;
    column8Cell.value = vacationHours.toFixed(2);
    return;
  }

  // NORMAL LOGIC
  const hoursCalculatedCell = row.querySelector('.hours-calculated');
  const calculatedHours = parseFloat(hoursCalculatedCell?.value);

  const startTime = row.querySelector('.start-time')?.value?.trim();
  const endTime = row.querySelector('.end-time')?.value?.trim();
  const dateStr = row.cells[1]?.textContent.trim();

  if (!startTime || !endTime || isNaN(calculatedHours) || !dateStr) {
    column8Cell.value = '';
    return;
  }

  const [startH] = startTime.split(':').map(Number);
  const startsInNightShift = (startH >= 22 || startH < 6);
  const shiftCap = startsInNightShift ? 7 : 8;
  const cappedHours = Math.min(calculatedHours, shiftCap);

  const [day, month, year] = dateStr.split('/').map(Number);
  const date = new Date(year, month - 1, day);
  const dayOfWeek = date.getDay();

  const isSaturday = row.querySelector('td:nth-child(3)')?.textContent === 'true';
  const isHoliday = row.querySelector('td:nth-child(4)')?.textContent === 'true';

  if (isSaturday || isHoliday) {
    column8Cell.value = '';
    return;
  }

  // FRIDAY LOGIC
  if (dayOfWeek === 5) {
    const weekKey = formatDateIL(getWeekStart(date));
    const rows = document.querySelectorAll('#table-body tr');
    const weekdayTotals = {};

    rows.forEach(r => {
      if (r.style.display === 'none') return;

      const dStr = r.cells[1]?.textContent.trim();
      const hInput = r.querySelector('.hours-calculated');
      const sTime = r.querySelector('.start-time')?.value?.trim();

      if (!dStr || !hInput || !sTime) return;

      const [d, m, y] = dStr.split('/').map(Number);
      const dObj = new Date(y, m - 1, d);
      const key = formatDateIL(getWeekStart(dObj));
      const dow = dObj.getDay();
      const hrs = parseFloat(hInput.value);
      if (isNaN(hrs)) return;

      const sH = parseInt(sTime.split(':')[0]);
      const isNight = sH >= 22 || sH < 6;
      const cap = isNight ? Math.min(hrs, 7) : Math.min(hrs, 8);

      if (dow >= 0 && dow <= 4) {
        weekdayTotals[key] = (weekdayTotals[key] || 0) + cap;
      }
    });

    const weekdayTotal = weekdayTotals[weekKey] || 0;
    const maxAllowed = 42 - weekdayTotal;
    const finalFridayHours = Math.min(cappedHours, maxAllowed);

    column8Cell.value = finalFridayHours.toFixed(2);
    return;
  }

  // NORMAL DAY
  column8Cell.value = cappedHours.toFixed(2);
}



// Function to calculate Column 9
function updateColumn9(row) {
    const column7Value = parseFloat(row.querySelector('.hours-calculated').value);
    const column8Value = parseFloat(row.querySelector('.hours-calculated-regular-day').value);
    const column9Cell = row.querySelector('.total-extra-hours-regular-day');

    // Only update Column 9 if both start and end hours are present
    if (!isNaN(column7Value) && !isNaN(column8Value)) {
        if (column7Value > column8Value) {
            const diff = column7Value - column8Value; // Difference in hours
            column9Cell.value = diff.toFixed(2); // Display result in decimal format
        } else {
            column9Cell.value = '';
        }
    } else {
        column9Cell.value = '';
    }
}

// Function to calculate Column 10
function updateColumn10(row) {
    const column7Value = parseFloat(row.querySelector('.hours-calculated').value);
    const column8Value = parseFloat(row.querySelector('.hours-calculated-regular-day').value);
    const column9Value = parseFloat(row.querySelector('.total-extra-hours-regular-day').value);
    const column10Cell = row.querySelector('.extra-hours125-regular-day');
    const isSaturdayResult = row.querySelector('td:nth-child(3)').textContent === 'true';
    const isHolidayResult = row.querySelector('td:nth-child(4)').textContent === 'true';

    if (isNaN(column7Value) || column7Value === 0 || isSaturdayResult || isHolidayResult || isNaN(column9Value)) {
        column10Cell.value = '';
    } else if (column9Value > 2) {
        column10Cell.value = '2.00';
    } else {
        column10Cell.value = column9Value.toFixed(2);
    }

    // Ensure the value is updated even if the cell is hidden
    column10Cell.dispatchEvent(new Event('input', { bubbles: true }));
}

// Function to calculate Column 11
function updateColumn11(row) {
    const column7Value = parseFloat(row.querySelector('.hours-calculated').value);
    const isSaturdayResult = row.querySelector('td:nth-child(3)').textContent === 'true';
    const isHolidayResult = row.querySelector('td:nth-child(4)').textContent === 'true';
    const column9Value = parseFloat(row.querySelector('.total-extra-hours-regular-day').value);
    const column10Value = parseFloat(row.querySelector('.extra-hours125-regular-day').value);
    const column11Cell = row.querySelector('.extra-hours150-regular-day');

    if (isNaN(column7Value) || column7Value === 0 || isSaturdayResult || isHolidayResult || isNaN(column9Value) || isNaN(column10Value)) {
        column11Cell.value = '';
    } else {
        const result = (column9Value - column10Value).toFixed(2);
        column11Cell.value = result === '0.00' ? '' : result;
    }

    // Ensure the value is updated even if the cell is hidden
    column11Cell.dispatchEvent(new Event('input', { bubbles: true }));
}

// Column 12: Extra hours beyond 8
function updateColumn12(row) {
  const column12Cell = row.querySelector('.hours-holidays-day');
  const column7Value = parseFloat(row.querySelector('.hours-calculated')?.value);
  const isSaturday = row.querySelector('td:nth-child(3)')?.textContent === 'true';
  const isHoliday = row.querySelector('td:nth-child(4)')?.textContent === 'true';
  const startTime = row.querySelector('.start-time')?.value?.trim();

  if (!startTime || isNaN(column7Value) || (!isSaturday && !isHoliday)) {
    column12Cell.value = '';
    column12Cell.dispatchEvent(new Event('input', { bubbles: true }));
    return;
  }

  const startHour = parseInt(startTime.split(':')[0]);
  const isNightShift = startHour >= 22 || startHour < 6;
  const shiftCap = isNightShift ? 7 : 8;
  const extraHours = column7Value > shiftCap ? column7Value - shiftCap : 0;

  column12Cell.value = extraHours > 0 ? extraHours.toFixed(2) : '';
  column12Cell.dispatchEvent(new Event('input', { bubbles: true }));
}

// Column 13: First 8 hours at 150%
function updateColumn13(row) {
  const column13Cell = row.querySelector('.extra-hours150-holidays-saturday');
  const column7Value = parseFloat(row.querySelector('.hours-calculated')?.value);
  const isSaturday = row.querySelector('td:nth-child(3)')?.textContent === 'true';
  const isHoliday = row.querySelector('td:nth-child(4)')?.textContent === 'true';
  const startTime = row.querySelector('.start-time')?.value?.trim();

  if (!startTime || isNaN(column7Value) || (!isSaturday && !isHoliday)) {
    column13Cell.value = '';
    column13Cell.dispatchEvent(new Event('input', { bubbles: true }));
    return;
  }

  const startHour = parseInt(startTime.split(':')[0]);
  const isNightShift = startHour >= 22 || startHour < 6;
  const cappedHours = isNightShift ? Math.min(column7Value, 7) : Math.min(column7Value, 8);

  column13Cell.value = cappedHours.toFixed(2);
  column13Cell.dispatchEvent(new Event('input', { bubbles: true }));
}

// Column 14: First 2 extra hours at 175%
function updateColumn14(row) {
    const column12Value = parseFloat(row.querySelector('.hours-holidays-day')?.value);
    const column14Cell = row.querySelector('.extra-hours175-holidays-saturday');

    if (!isNaN(column12Value)) {
        column14Cell.value = Math.min(column12Value, 2).toFixed(2);
    } else {
        column14Cell.value = '';
    }

    column14Cell.dispatchEvent(new Event('input', { bubbles: true }));
}

// Column 15: Remaining extra hours at 200%
function updateColumn15(row) {
    const column12Value = parseFloat(row.querySelector('.hours-holidays-day')?.value);
    const column14Value = parseFloat(row.querySelector('.extra-hours175-holidays-saturday')?.value);
    const column15Cell = row.querySelector('.extra-hours200-holidays-saturday');

    if (!isNaN(column12Value) && !isNaN(column14Value)) {
        const remaining = column12Value - column14Value;
        column15Cell.value = remaining > 0 ? remaining.toFixed(2) : '';
    } else {
        column15Cell.value = '';
    }

    column15Cell.dispatchEvent(new Event('input', { bubbles: true }));
}

// Function to calculate Sick Day Column 16
function updateColumn16(row) {
    const column7Value = parseFloat(row.querySelector('.hours-calculated').value);
    const column16Value = parseFloat(row.querySelector('.sick-day').value) || 0;
    const column16Cell = row.querySelector('.sick-day');

    if (isNaN(column7Value) || column7Value === 0) {
        column16Cell.value = '';
    } else {
        column16Cell.value = column16Value === 0 ? '' : column16Value.toFixed(2);
    }

    // Display cell as empty if value is 0
    if (column16Cell.value === '0.00') {
        column16Cell.value = '';
    }

    // Ensure the value is updated even if the cell is hidden
    column16Cell.dispatchEvent(new Event('input', { bubbles: true }));
}

// Function to calculate Vacation Column 17 (day-off)
function updateColumn17(row) {
    const column7Value = parseFloat(row.querySelector('.hours-calculated').value);
    const column17Value = parseFloat(row.querySelector('.day-off').value) || 0;
    const column17Cell = row.querySelector('.day-off');

    if (isNaN(column7Value) || column7Value === 0) {
        column17Cell.value = '';
    } else {
        column17Cell.value = column17Value === 0 ? '' : column17Value.toFixed(2);
    }

    // Display cell as empty if value is 0
    if (column17Cell.value === '0.00') {
        column17Cell.value = '';
    }

    // Ensure the value is updated even if the cell is hidden
    column17Cell.dispatchEvent(new Event('input', { bubbles: true }));
}

// Function to calculate Column 18 (Food Break)
function updateColumn18(row) {
    const column7Value = parseFloat(row.querySelector('.hours-calculated').value);
    const column18Cell = row.querySelector('.food-break');

    const AE30 = 11.5; 
    const AE29 = 8.5;  
    const AF30 = 0.5;  

    // NEW RULE: If hours < 8 → NO BREAK
    if (column7Value < 8) {
        column18Cell.value = '';
    }
    else if (column7Value > AE30) {
        column18Cell.value = (AF30 + AF30).toFixed(2); 
    }
    else if (column7Value > AE29) {
        column18Cell.value = AF30.toFixed(2); 
    }
    else {
        column18Cell.value = '';
    }

    column18Cell.dispatchEvent(new Event('input', { bubbles: true }));
}



// Function to calculate final total hours Column 19
function updateColumn19(row) {
    const column7Value  = parseFloat(row.querySelector('.hours-calculated')?.value) || 0;
    const column8Value  = parseFloat(row.querySelector('.hours-calculated-regular-day')?.value) || 0;
    const column10Value = parseFloat(row.querySelector('.extra-hours125-regular-day')?.value) || 0;
    const column11Value = parseFloat(row.querySelector('.extra-hours150-regular-day')?.value) || 0;
    const column13Value = parseFloat(row.querySelector('.extra-hours150-holidays-saturday')?.value) || 0;
    const column14Value = parseFloat(row.querySelector('.extra-hours175-holidays-saturday')?.value) || 0;
    const column15Value = parseFloat(row.querySelector('.extra-hours200-holidays-saturday')?.value) || 0;
    const column16Value = parseFloat(row.querySelector('.sick-day')?.value) || 0;
    const column17Value = parseFloat(row.querySelector('.day-off')?.value) || 0;
    const column18Value = parseFloat(row.querySelector('.food-break')?.value) || 0;

    const column19Cell = row.querySelector('.final-totals-hours');
    if (!column19Cell) return;

    // === Sick overrides everything ===
    if (column16Value > 0) {
        column19Cell.value = column16Value.toFixed(2);
        column19Cell.dispatchEvent(new Event('input', { bubbles: true }));
        return;
    }

    // === Vacation overrides everything → ALWAYS 8 hours ===
    if (column17Value > 0) {
        column19Cell.value = '8.00';
        column19Cell.dispatchEvent(new Event('input', { bubbles: true }));
        return;
    }

    // === If no hours → empty ===
    if (column7Value === 0) {
        column19Cell.value = '';
        column19Cell.dispatchEvent(new Event('input', { bubbles: true }));
        return;
    }

    // === Normal calculation ===
    const regularDaysTotal = column8Value + column10Value + column11Value;
    const holidaysTotal    = column13Value + column14Value + column15Value;
    const total            = regularDaysTotal + holidaysTotal - column18Value;

    column19Cell.value = total === 0 ? '' : total.toFixed(2);
    column19Cell.dispatchEvent(new Event('input', { bubbles: true }));
}



// Function to calculate Column 23 (Daily Work Days)
function updateColumn23(row) {
  const startTimeInput = row.querySelector('.start-time')?.value.trim();
  const endTimeInput   = row.querySelector('.end-time')?.value.trim();
  const workDayCell    = row.querySelector('.work-day');

  if (startTimeInput && endTimeInput) {
    // Both start and end exist → worked day
    workDayCell.value = (1.0).toFixed(2);   // "1.00"
  } else {
    // Either missing or both empty → not a work day
    workDayCell.value = (0.0).toFixed(2);   // "0.00"
  }

  // Fire event so bindings notice the change
  workDayCell.dispatchEvent(new Event('input', { bubbles: true }));
}

// Function to calculate Column 24
function updateColumn24(row) {
  const basicHoursCell = row.querySelector('.hours-calculated-regular-day'); // Column 8
  const missingWorkDayCell = row.querySelector('.missing-work-day');        // Column 24

  const actualHours = parseFloat(basicHoursCell?.value);

  if (!isNaN(actualHours)) {
    missingWorkDayCell.value = actualHours.toFixed(2);
  } else {
    missingWorkDayCell.value = '';
  }

  missingWorkDayCell.dispatchEvent(new Event('input', { bubbles: true }));
}




// Function to calculate Form 102 Summary All Employees 68<Age<17 (עובד מתחת לגיל 18 או מעל 67 → שכר מופחת)

function isReducedRate(dateOfBirth) {
    const age = calculateAge(dateOfBirth);
    return age < 18 || age >= 67;
}

function calculate102Summary(employees) {
    let regularCount = 0;
    let reducedCount = 0;

    let regularSalary = 0;
    let reducedSalary = 0;

    employees.forEach(emp => {
        const salary = parseFloat(emp.gross_taxable) || 0;
        const age = calculateAge(emp.dateOfBirth);
        const isReduced = isReducedRate(emp.dateOfBirth);

        if (isReduced) {
            reducedCount++;
            reducedSalary += salary;
        } else {
            regularCount++;
            regularSalary += salary;
        }
    });

    return {
        regularCount,
        reducedCount,
        regularSalary: parseFloat(regularSalary.toFixed(2)),
        reducedSalary: parseFloat(reducedSalary.toFixed(2)),
        totalSalary: parseFloat((regularSalary + reducedSalary).toFixed(2))
    };
}



               // Function to Update All Very Importtant  

// Function to update all tax form fields dynamically
function updateTaxFormFields(data) {
    const fields = [
      'address', 'city', 'postal_code', 'phone', 'id_number', 'date_of_birth', 'start_date', 'hourly_rate',
      'thirteenth_salary', 'lunch_value', 'mobile_value', 'clothing_value', 'work_percent', 'contract_status',
      'tax_point_child', 'monthly_city_tax_tops', 'tax_credit_points', 'city_value_percentage', 'cars_value', 
      'sick_days_salary', 'vacation_days_salary', 'final_extra_hours_regular', 'final_extra_hours_weekend',
      'sick_days_entitlement', 'vacation_days_entitlement',
      'total_work_days', 'total_missing_hours',
      'basic_salary', 'totals_lunch_value', 'additional_payments',
      'net_value', 'gross_salary', 'above_ceiling_value', 'above_ceiling_fund',
      'above_ceiling_compensation', 'gross_taxable', 'pension_fund', 'compensation',
      'study_fund', 'disability', 'miscellaneous', 'national_insurance', 'salary_tax',
      'total_employer_contributions', 'employee_pension_fund', 'self_employed_pension_fund',
      'study_fund_deductions', 'miscellaneous_deductions', 'national_insurance_deductions',
      'health_insurance_deductions', 'income_tax', 'advance_payment_salary',
      'total_deductions', 'net_payment', 'tax_level_precente', 'income_tax_before_credit',
      'amount_tax_credit_points_monthly', 'food_break_unpaid_salary',
      'hours125_regular_salary', 'hours150_regular_salary',
      'hours150_holidays_saturday_salary', 'hours175_holidays_saturday_salary', 'hours200_holidays_saturday_salary',
      'final_city_tax_benefit', 'total_salary_cost', 'total_salary_pension_funds',
    ];

    fields.forEach(field => {
        const fieldElement = document.getElementById(field);
        if (fieldElement) {
            const newValue = data[field] !== undefined ? data[field] : fieldElement.value;
            fieldElement.value = newValue;
        }
    });

    // ---- UPDATE EMPLOYEE BASIC INFO ----
    if (data.employee_name) {
        const nameField = document.getElementById('employee_name');
        if (nameField) nameField.value = data.employee_name;
    }

    if (data.employee_id) {
        const idField = document.getElementById('employee_id');
        if (idField) idField.value = data.employee_id;
    }

    if (data.employeeMonth) {
        const monthField = document.getElementById('employeeMonth');
        if (monthField) monthField.value = data.employeeMonth;
    }

    if (data.employeeYear) {
        const yearField = document.getElementById('employeeYear');
        if (yearField) yearField.value = data.employeeYear;
    }
}


// Clear all salary/tax fields WITHOUT clearing employee selection
function clearAllFields() {
    const fields = [
      'address', 'city', 'postal_code', 'phone', 'id_number', 'date_of_birth', 'start_date', 'hourly_rate',
      'thirteenth_salary', 'lunch_value', 'mobile_value', 'clothing_value', 'work_percent', 'contract_status',
      'tax_point_child', 'monthly_city_tax_tops', 'tax_credit_points', 'city_value_percentage', 'cars_value', 
      'sick_days_salary', 'vacation_days_salary', 'final_extra_hours_regular', 'final_extra_hours_weekend',
      'sick_days_entitlement', 'vacation_days_entitlement',
      'total_work_days', 'total_missing_hours',
      'basic_salary', 'totals_lunch_value', 'additional_payments',
      'net_value', 'gross_salary', 'above_ceiling_value', 'above_ceiling_fund',
      'above_ceiling_compensation', 'gross_taxable', 'pension_fund', 'compensation',
      'study_fund', 'disability', 'miscellaneous', 'national_insurance', 'salary_tax',
      'total_employer_contributions', 'employee_pension_fund', 'self_employed_pension_fund',
      'study_fund_deductions', 'miscellaneous_deductions', 'national_insurance_deductions',
      'health_insurance_deductions', 'income_tax', 'advance_payment_salary',
      'total_deductions', 'net_payment', 'tax_level_precente', 'income_tax_before_credit',
      'amount_tax_credit_points_monthly', 'food_break_unpaid_salary',
      'hours125_regular_salary', 'hours150_regular_salary',
      'hours150_holidays_saturday_salary', 'hours175_holidays_saturday_salary', 'hours200_holidays_saturday_salary',
      'final_city_tax_benefit', 'total_salary_cost', 'total_salary_pension_funds',
    ];

    fields.forEach(field => {
        const fieldElement = document.getElementById(field);
        if (fieldElement) {
            fieldElement.value = ''; 
        }
    });
}


               // Function to  Update All Employee  


// Update employee details when a new employee is selected from the combobox Fetch and store employee data
function updateEmployeeDetails() {
  const employeeId = document.getElementById('employee_id')?.value;
  const month = document.getElementById('employeeMonth')?.value?.padStart(2, '0');
  const year = document.getElementById('employeeYear')?.value;

  // אם חסר משהו — מנקה את הטופס ולא עושה fetch
  if (!employeeId || !month || !year) {
    clearAllFields();
    return;
  }

  const url = `/get_employee_details/${employeeId}/${month}/${year}`;

  fetch(url)
    .then(response => response.json())
    .then(data => {

      sessionStorage.setItem('employee_data_full', JSON.stringify(data));

      if (data.existing_record_found) {
        alert("⚠️ שכר כבר קיים לתאריך הזה עבור העובד");
        document.querySelectorAll('#hours-table input').forEach(input => input.disabled = true);
      } else {
        document.querySelectorAll('#hours-table input').forEach(input => input.disabled = false);
      }

      updateTaxFormFields(data);
    })
    .catch(err => {
      clearAllFields();
    });
}



        // Update Function Validate And Calculate Tax Form

function parseFloatEmployee(value) {
  if (!value) return 0;
  return parseFloat(value.toString().replace(/[^0-9.-]+/g, '').trim()) || 0;
}



function validateAndCalculateForm() {
  function performCalculations() {
    const fields = [
      'address', 'city', 'postal_code', 'phone', 'id_number', 'date_of_birth', 'start_date', 'hourly_rate',
      'thirteenth_salary', 'lunch_value', 'mobile_value', 'clothing_value', 'work_percent', 'contract_status',
      'tax_point_child', 'monthly_city_tax_tops', 'tax_credit_points', 'city_value_percentage', 'cars_value', 
      'sick_days_salary', 'vacation_days_salary', 'final_extra_hours_regular', 'final_extra_hours_weekend',
      'sick_days_entitlement', 'vacation_days_entitlement',
      'total_work_days', 'total_missing_hours',
      'basic_salary', 'totals_lunch_value', 'additional_payments',
      'net_value', 'gross_salary', 'above_ceiling_value', 'above_ceiling_fund',
      'above_ceiling_compensation', 'gross_taxable', 'pension_fund', 'compensation',
      'study_fund', 'disability', 'miscellaneous', 'national_insurance', 'salary_tax',
      'total_employer_contributions', 'employee_pension_fund', 'self_employed_pension_fund',
      'study_fund_deductions', 'miscellaneous_deductions', 'national_insurance_deductions',
      'health_insurance_deductions', 'income_tax', 'advance_payment_salary',
      'total_deductions', 'net_payment', 'tax_level_precente', 'income_tax_before_credit',
      'amount_tax_credit_points_monthly', 'food_break_unpaid_salary',
      'hours125_regular_salary', 'hours150_regular_salary',
      'hours150_holidays_saturday_salary', 'hours175_holidays_saturday_salary', 'hours200_holidays_saturday_salary',
      'final_city_tax_benefit', 'total_salary_cost', 'total_salary_pension_funds',
    ];

    const fieldValues = {};
    fields.forEach(fieldId => {
      const element = document.getElementById(fieldId);
      fieldValues[fieldId] = element && element.value ? parseFloatEmployee(element.value) : 0;
    });

    // === Trigger dependent calculations ===
    updateTotalsLunchValueForm();
    calculateFinalTotalsLunchValuePaidForMonth();
    calculateSickDayForMonth();
    calculateDayOffForMonth();
    updateSickDaysInSalaryForm();
    updateVacationDaysInSalaryForm();
    updateTotalWorkDays();
    calculateFinalTotalExtraHoursWeekendForMonth();
    updateTotalMissingHours();
    updateTotalFinalExtraWeekendHours();
    updateTotalFinalExtraRegularHours();
    calculationsAdditionalPayments();
    updateIncomeTaxBeforeCredit();
    updateTaxLevelPercentage();
    calculateAboveCeilingFund();

    updateHoursFoodBreakUnpaid();
    updateHoursRegular125();
    updateHoursRegular150();
    updateHoursHolidaysSaturday150();
    updateHoursHolidaysSaturday175();
    updateHoursHolidaysSaturday200();

    updateBasicSalary();
    updateTotalAdvancePayment();

    employerPensionFund();
    employerCompensation();
    employerStudyFund();
    employerDisability();
    employerNationalInsurance();

    studyFundDeductions();
    updateNationalInsuranceDeductions();
    updateHealthInsuranceDeductions();
    calculateMonthlyCityTaxTops();
    totalSalaryPensionFunds();
    employeePensionFund();
    calculateMonthlyTaxCredit();
    selfEmployedPensionFund();
    calculateIncomeTax();

    // === Basic salary calculations ===
    const basic = parseFloatEmployee(document.getElementById('basic_salary')?.value);
    const additional = parseFloatEmployee(document.getElementById('additional_payments')?.value);
    const car = parseFloatEmployee(document.getElementById('cars_value')?.value);
    const ceiling = parseFloatEmployee(document.getElementById('above_ceiling_fund')?.value);

    const netValue = basic + additional + car;
    const grossSalary = basic + additional;
    const grossTaxable = netValue + ceiling;

    fieldValues.grossTaxable = grossTaxable;

    document.getElementById('net_value').value = formatCurrency(netValue);
    document.getElementById('gross_salary').value = formatCurrency(grossSalary);
    document.getElementById('above_ceiling_fund').value = formatCurrency(ceiling);
    document.getElementById('gross_taxable').value = formatCurrency(grossTaxable);
    document.getElementById('gross_taxable').dataset.rawValue = grossTaxable.toFixed(2);

    // === Employer contributions ===
    const employerFields = [
      'pension_fund', 'compensation', 'study_fund',
      'disability', 'miscellaneous', 'national_insurance', 'salary_tax'
    ];

    let totalEmployerContributions = 0;
    employerFields.forEach(id => {
      const value = parseFloatEmployee(document.getElementById(id)?.value || fieldValues[id]);
      document.getElementById(id).value = formatCurrency(value);
      totalEmployerContributions += value;
    });

    const totalSalaryCost = grossSalary + totalEmployerContributions;
    document.getElementById('total_employer_contributions').value = formatCurrency(totalEmployerContributions);
    document.getElementById('total_salary_cost').value = formatCurrency(totalSalaryCost);

    // === Update Income Tax And Add Field study Fund Deduction ===
    const incomeTaxRaw = parseFloatEmployee(document.getElementById('income_tax')?.value);
    const studyFundDeductionRaw = parseFloatEmployee(document.getElementById('study_fund_deductions')?.value);
    document.getElementById('income_tax').value = formatCurrency(incomeTaxRaw);

    // === Final deductions and net payment ===
    const totalDeductions =
      parseFloatEmployee(document.getElementById('employee_pension_fund')?.value) +
      parseFloatEmployee(document.getElementById('self_employed_pension_fund')?.value) +
      studyFundDeductionRaw +
      parseFloatEmployee(document.getElementById('miscellaneous_deductions')?.value) +
      parseFloatEmployee(document.getElementById('national_insurance_deductions')?.value) +
      parseFloatEmployee(document.getElementById('health_insurance_deductions')?.value) +
      incomeTaxRaw +
      parseFloatEmployee(document.getElementById('advance_payment_salary')?.value);

    document.getElementById('total_deductions').value = formatCurrency(totalDeductions);

    const netPayment = grossSalary - totalDeductions;
    document.getElementById('net_payment').value = formatCurrency(netPayment);

    // === Preserve advance payment value ===
    setTimeout(() => {
        preserveAdvancePaymentValue();

    }, 150);
  }

  function formatCurrency(value) {
    return value.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  performCalculations();
}




// ===  Daily and Monthly Field Definitions (all kebab-case to match your HTML) ===
const dailyFields = [
  'date', 'day', 'saturday', 'holiday', 'start-time', 'end-time',
  'hours-calculated', 'hours-calculated-regular-day', 'total-extra-hours-regular-day',
  'extra-hours125-regular-day', 'extra-hours150-regular-day', 'hours-holidays-day',
  'extra-hours150-holidays-saturday', 'extra-hours175-holidays-saturday', 'extra-hours200-holidays-saturday',
  'sick-day', 'day-off', 'food-break', 'final-totals-hours', 'calc1', 'calc2', 'calc3',
  'work-day', 'missing-work-day', 'advance-payment'
];

const monthlyFields = [
  "hours-calculated-monthly", "hours-calculated-regular-day-monthly", "total-extra-hours-regular-day-monthly",
  "extra-hours125-regular-day-monthly", "extra-hours150-regular-day-monthly", "hours-holidays-day-monthly",
  "extra-hours150-holidays-saturday-monthly", "extra-hours175-holidays-saturday-monthly",
  "extra-hours200-holidays-saturday-monthly", "sick-day-monthly", "day-off-monthly",
  "food-break-monthly", "final-totals-hours-monthly", "calc1-monthly", "calc2-monthly",
  "calc3-monthly", "work-day-monthly", "missing-work-day-monthly", "advance-payment-monthly"
];

const paidFields = [
  "hours-calculated-paid", "hours-calculated-regular-day-paid", "total-extra-hours-regular-day-paid",
  "extra-hours125-regular-day-paid", "extra-hours150-regular-day-paid", "hours-holidays-day-paid",
  "extra-hours150-holidays-saturday-paid", "extra-hours175-holidays-saturday-paid",
  "extra-hours200-holidays-saturday-paid", "sick-day-paid", "day-off-paid",
  "food-break-unpaid", "final-totals-hours-paid", "calc1-paid", "calc2-paid", "calc3-paid",
  "final-totals-lunch-value-paid", "final-total-extra-hours-weekend-monthly", "advance-payment-paid"
];


// Convert snake_case → kebab-case
function snakeToKebab(str) {
  return str.replace(/_/g, '-');
}


// === Populate Table from Server Data ===
function populateExistingHours(data) {
  const rows = document.querySelectorAll("#table-body tr");

  // === Daily rows ===
  const entries = data.work_day_entries || [];
  entries.forEach(entry => {
    const entryDate = entry.date;

    rows.forEach(row => {
      const rowDate = row.children[1]?.textContent.trim();
      if (rowDate === entryDate) {

        Object.entries(entry).forEach(([key, value]) => {
          if (["day", "date", "saturday", "holiday"].includes(key)) return;

          const input = row.querySelector(`input.${key}`);
          if (input) input.value = value;
        });
      }
    });
  });

  // === Monthly totals ===
  const monthlyRow = rows[rows.length - 2];
  Object.entries(data.monthly_totals || {}).forEach(([key, value]) => {
    const input = monthlyRow.querySelector(`input.${key}`);
    if (input) input.value = value;
  });

  // === Paid totals ===
  const paidRow = rows[rows.length - 1];
  Object.entries(data.paid_totals || {}).forEach(([key, value]) => {
    const input = paidRow.querySelector(`input.${key}`);
    if (input) input.value = value;
  });

  // === TAX fields ===
  if (data.tax) {
    Object.entries(data.tax).forEach(([key, value]) => {
      const input = document.getElementById(key);
      if (input) input.value = value;
    });
  }
}



// Convert kebab-case → snake_case
function kebabToSnake(str) {
  return str.replace(/-/g, '_');
}

// === Collect Table Data for Saving ===
function collectHoursTable() {
  const tableBody = document.getElementById("table-body");
  const rows = Array.from(tableBody.querySelectorAll("tr"));

  const work_day_entries = [];
  const monthly_totals = {};
  const paid_totals = {};

  // === Skip header row if present ===
  const hasHeader = rows[0]?.querySelectorAll("th").length > 0;
  const startIndex = hasHeader ? 1 : 0;

  // === Daily Rows ===
  // last two rows are monthly + paid
  const dailyRowCount = rows.length - 2;
  for (let i = startIndex; i < dailyRowCount; i++) {
    const row = rows[i];
    const rowData = {};

    const cells = row.querySelectorAll("td");

    rowData["day"] = cells[0]?.textContent.trim() || "";
    rowData["date"] = cells[1]?.textContent.trim() || "";
    rowData["saturday"] = cells[2]?.textContent.trim() || "";
    rowData["holiday"] = cells[3]?.textContent.trim() || "";

    dailyFields.forEach(field => {
      if (!["day", "date", "saturday", "holiday"].includes(field)) {
        const input = row.querySelector(`input.${field}`);
        const snake = kebabToSnake(field);
        rowData[snake] = input?.value?.trim() || "";
      }
    });

    work_day_entries.push(rowData);
  }

  // === Monthly Totals Row ===
  const monthlyRow = rows[rows.length - 2];
  monthlyFields.forEach(field => {
    const input = monthlyRow.querySelector(`input.${field}`);
    const snake = kebabToSnake(field);
    monthly_totals[snake] = input?.value?.trim() || "";
  });

  // === Paid Totals Row ===
  const paidRow = rows[rows.length - 1];
  paidFields.forEach(field => {
    const input = paidRow.querySelector(`input.${field}`);
    const snake = kebabToSnake(field);
    paid_totals[snake] = input?.value?.trim() || "";
  });

  return { work_day_entries, monthly_totals, paid_totals };
}



// === Collect Tax Form Fields ===
function collectTaxFormFields() {
   const fieldNames = [
      'address', 'city', 'postal_code', 'phone', 'id_number', 'date_of_birth', 'start_date', 'hourly_rate',
      'thirteenth_salary', 'lunch_value', 'mobile_value', 'clothing_value', 'work_percent', 'contract_status',
      'tax_point_child', 'monthly_city_tax_tops', 'tax_credit_points', 'city_value_percentage', 'cars_value', 
      'sick_days_salary', 'vacation_days_salary', 'final_extra_hours_regular', 'final_extra_hours_weekend',
      'sick_days_entitlement', 'vacation_days_entitlement',
      'total_work_days', 'total_missing_hours',
      'basic_salary', 'totals_lunch_value', 'additional_payments',
      'net_value', 'gross_salary', 'above_ceiling_value', 'above_ceiling_fund',
      'above_ceiling_compensation', 'gross_taxable', 'pension_fund', 'compensation',
      'study_fund', 'disability', 'miscellaneous', 'national_insurance', 'salary_tax',
      'total_employer_contributions', 'employee_pension_fund', 'self_employed_pension_fund',
      'study_fund_deductions', 'miscellaneous_deductions', 'national_insurance_deductions',
      'health_insurance_deductions', 'income_tax', 'advance_payment_salary',
      'total_deductions', 'net_payment', 'tax_level_precente', 'income_tax_before_credit',
      'amount_tax_credit_points_monthly', 'food_break_unpaid_salary',
      'hours125_regular_salary', 'hours150_regular_salary',
      'hours150_holidays_saturday_salary', 'hours175_holidays_saturday_salary', 'hours200_holidays_saturday_salary',
      'final_city_tax_benefit', 'total_salary_cost', 'total_salary_pension_funds',
    ];

  const taxData = {};
  fieldNames.forEach(name => {
    const input = document.getElementById(name);
    taxData[name] = input ? input.value.trim() : '';
  });

  return taxData;
}


               // Function to Update Yearly All Monthly Paid Employee & Employer Tax  

function integrateYearlyTotals(payload, all_hours) {
  const yearlyFields = [
    "sick_days_salary",
    "vacation_days_salary",
    "sick_days_balance",
    "vacation_balance",
    "sick_days_balance",
    "vacation_balance",
    "gross_taxable",
    "employee_pension_fund",
    "self_employed_pension_fund",
    "study_fund_deductions",
    "miscellaneous_deductions",
    "national_insurance_deductions",
    "health_insurance_deductions",
    "income_tax",
    "amount_tax_credit_points_monthly",
    "final_city_tax_benefit",
    "pension_fund",
    "compensation",
    "study_fund",
    "disability",
    "miscellaneous",
    "national_insurance",
    "salary_tax",
    "total_employer_contributions",
    "total_salary_cost"
  ];

  const sick_days_entitlement = 18;
  const vacation_days_entitlement = 12;

  const employeeId = String(payload.employee_id);
  const year = String(payload.year);
  const month = parseInt(payload.month, 10);

  const employeeData = all_hours?.[employeeId] || {};

  let totals = {};

  yearlyFields.forEach(field => {
    let sum = 0;

    // 1. Sum previous months
    Object.entries(employeeData).forEach(([monthKey, monthData]) => {
      if (!monthKey.startsWith(year)) return;

      const monthNum = parseInt(monthKey.split("-")[1], 10);
      if (monthNum >= month) return;

      const rawVal = monthData?.hours_table?.tax?.[field] || 0;
      const parsed = parseFloat(String(rawVal).replace(/[^0-9.-]+/g, ""));
      if (!isNaN(parsed)) sum += parsed;
    });

    // 2. Add current month
    const currentVal = parseFloat(
      String(payload.hours_table.tax[field] || 0).replace(/[^0-9.-]+/g, "")
    );
    if (!isNaN(currentVal)) sum += currentVal;

    totals[field + "_yearly"] = sum;
  });

  // === 3. Compute balances ===
  const sick_used = totals["sick_days_salary_yearly"] || 0;
  const vacation_used = totals["vacation_days_salary_yearly"] || 0;

  totals["sick_days_balance_yearly"] = sick_days_entitlement - sick_used;
  totals["vacation_balance_yearly"] = vacation_days_entitlement - vacation_used;

  // === 4. Format + update payload + DOM ===
  Object.entries(totals).forEach(([key, val]) => {
    const formatted = Number(val).toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });

    payload.hours_table.tax[key] = formatted;

    const el = document.getElementById(key);
    if (el) {
      el.dataset.rawValue = val.toFixed(2);
      el.value = formatted;
    }
  });

  return payload;
}



// ===  Save Table All Fields ===
function saveTable(event) {
  event.preventDefault();

    // === Get employee info ===
    const employeeSelect = document.getElementById('employee_id');
    const employeeId = employeeSelect?.value?.trim();
    const employeeName = employeeSelect?.selectedOptions[0]?.text?.trim();

    // === Get selected month and year ===
    const selectedMonth = document.getElementById('employeeMonth')?.value?.trim();
    const selectedYear = document.getElementById('employeeYear')?.value?.trim();

    // === Collect all table data AFTER recalculation ===
    const { work_day_entries, monthly_totals, paid_totals } = collectHoursTable();
    const taxData = collectTaxFormFields();

    // === Build payload ===
    let payload = {
      employee_id: employeeId,
      employee_name: employeeName,
      month: selectedMonth,
      year: selectedYear,
      hours_table: {
        work_day_entries,
        monthly_totals,
        paid_totals,
        tax: taxData
      }
    };

    // === Integrate yearly totals (updates DOM + payload)===
    payload = integrateYearlyTotals(payload, all_hours);

  // === Send to Flask ===
  fetch('/save_hours', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  .then(res => res.json())
  .then(data => {
       showWindowsSuccess(`✅ ${data.message || 'הנתונים נשמרו בהצלחה'}`);

  //  Refresh the page after save
    setTimeout(() => {
      location.reload();
    }, 300); 
  });
}



// ===============================
// CLEAR TABLE INPUTS
// ===============================

function clearTableInputs() {
  document.querySelectorAll("#table-body input").forEach(input => {
    input.value = "";
  });
}


// ===============================
// LOAD SAVED HOURS FROM JSON
// ===============================
function loadHoursFromJson() {
    const empEl = document.getElementById("employee_id");
    const monthEl = document.getElementById("employeeMonth");
    const yearEl = document.getElementById("employeeYear");

    const employeeId = empEl?.value?.trim();
    const selectedMonth = monthEl?.value?.trim();
    const selectedYear = yearEl?.value?.trim();

    if (!employeeId || !selectedMonth || !selectedYear) {
        return; 
    }

    fetch(`/get_hours_data?employee_id=${employeeId}&month=${selectedMonth}&year=${selectedYear}`)
    .then(res => res.json())
    .then(data => {
            if (!data || data.empty || (!data.work_day_entries && !data.hours_table)) {
                clearTableInputs();
                return;
            }

            // חילוץ הנתונים הנכון (לפעמים זה בתוך hours_table)
            const entries = data.work_day_entries || data.hours_table?.work_day_entries;
            
            if (entries) {
                clearTableInputs();
                populateExistingHours(data.hours_table || data);
                setTimeout(() => recalculateAllRows(), 150);
            }
        })
}


document.addEventListener("DOMContentLoaded", () => {
  loadHoursFromJson();   
});

// ===============================
// WHEN EMPLOYEE CHANGES
// ===============================

document.getElementById("employee_id").addEventListener("change", () => {
  const employeeId = document.getElementById("employee_id").value.trim();

  if (!employeeId) {
    clearTableInputs();   
    return;
  }

  loadHoursFromJson();    
});


// ===============================
//  Clock in out Page Fill CLOCK START/END
// ===============================
function fillStartEndFromClock(clockData) {
  const rows = document.querySelectorAll("#table-body tr");

  const entries = clockData.entries || [];

  entries.forEach(entry => {
    const entryDate = entry.date; // DD/MM/YYYY

    rows.forEach(row => {
      const rowDate = row.children[1]?.textContent.trim();

      if (rowDate === entryDate) {
        const startInput = row.querySelector("input.start-time");
        const endInput = row.querySelector("input.end-time");

        if (startInput) startInput.value = entry.start_time || "";
        if (endInput) endInput.value = entry.end_time || "";
      }
    });
  });
}


// ===============================
// LOAD CLOCK DATA (ONLY WHEN CLICKED)
// ===============================

function loadClockIntoIndex() {
  const employeeId = document.getElementById('employee_id')?.value?.trim();
  const month = document.getElementById('employeeMonth')?.value?.trim();
  const year = document.getElementById('employeeYear')?.value?.trim();

  if (!employeeId) {
    clearTableInputs();
    alert("בחר עובד קודם");
    return;
  }

  fetch(`/get_clock_hours?employee_id=${employeeId}&month=${month}&year=${year}`)
    .then(async res => {
      const data = await res.json();

      fillStartEndFromClock(data);

      setTimeout(() => {
          recalculateAllRows();
      }, 150);
  });
}



//  Main Index Display Start Todays As Month Year
document.addEventListener('DOMContentLoaded', function () {
  updateMonthResult(); 
});
