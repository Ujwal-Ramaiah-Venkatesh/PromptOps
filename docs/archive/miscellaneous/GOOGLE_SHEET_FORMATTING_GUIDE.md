# Google Sheet Professional Formatting Guide

**Your Sheet:** https://docs.google.com/spreadsheets/d/143UiPMHQeeAJ5DPYYbEWnmmEC5-9VLfNKgmPtLU2do8/edit

---

## 🎨 Sheet 1: Daily Work Log

### Header Row Formatting (Row 1)
1. Select row 1
2. **Bold** (Ctrl+B)
3. **Background color:** Dark blue (#1155CC)
4. **Text color:** White
5. **Align:** Center
6. **View** → **Freeze** → **1 row**

### Add Checkboxes
**Column H (Status):** Convert to dropdown
1. Select column H (H2 onwards)
2. **Data** → **Data validation**
3. **Criteria:** List of items
4. **Items:** `Not Started, In Progress, Complete, Blocked`
5. **Show dropdown list in cell:** ✅ Check
6. Click **Save**

### Conditional Formatting
**Status Column (H):**
1. Select H2:H100
2. **Format** → **Conditional formatting**
3. **Format rules:**
   - If text contains "Complete" → Background green (#B7E1CD)
   - If text contains "Blocked" → Background red (#F4C7C3)
   - If text contains "In Progress" → Background yellow (#FFF2CC)

**Hours Column (G):**
1. Select G2:G100
2. **Format** → **Number** → **Number** → 1 decimal place

### Column Widths
- Date: 100px
- Day: 80px
- Week: 80px
- Team Member: 120px
- Task ID: 100px
- Task Description: 300px
- Hours Spent: 80px
- Status: 120px
- Deliverables: 250px
- Notes: 250px
- Blockers: 150px

---

## 🎨 Sheet 2: Task Tracker

### Header Row Formatting (Row 1)
- **Bold** + **Dark blue background** (#1155CC) + **White text** + **Center align**
- **Freeze:** Row 1

### Add Dropdowns

**Column E (Priority):**
- Validation: `Low, Medium, High, Critical`
- Colors:
  - Critical → Red background (#EA4335)
  - High → Orange (#F9AB00)
  - Medium → Yellow (#FFF2CC)
  - Low → Light gray (#F3F3F3)

**Column F (Status):**
- Validation: `Not Started, In Progress, Complete, Blocked, On Hold`
- Colors:
  - Complete → Green (#34A853)
  - In Progress → Blue (#4285F4)
  - Blocked → Red (#EA4335)
  - Not Started → Gray (#9AA0A6)
  - On Hold → Orange (#F9AB00)

### Add Checkboxes
**Column K (Completion %):**
- Change to progress bar using conditional formatting:
  1. Select K2:K100
  2. Format → Number → Percent
  3. Conditional formatting:
     - If >= 100% → Green background
     - If >= 50% → Yellow background
     - If < 50% → Red background

### Formulas
**Add in Column N (Days in Progress):**
```
=IF(F2="In Progress", TODAY()-G2, "")
```

**Add in Column O (Over Budget?):**
```
=IF(J2>I2*1.2, "⚠️ Over", "✓ OK")
```

### Conditional Formatting
**Entire row turns red if task is blocked:**
1. Select A2:O100
2. Conditional formatting → Custom formula:
   ```
   =$F2="Blocked"
   ```
3. Background color: Light red (#F4C7C3)

---

## 🎨 Sheet 3: Deliverables

### Header Row
- **Bold** + **Purple background** (#9900FF) + **White text**
- **Freeze:** Row 1

### Add Dropdowns

**Column D (Type):**
- Validation: `Code, Data, Documentation, Tests, Config`

**Column G (Status):**
- Validation: `Not Started, In Progress, Complete, Delayed`
- Conditional colors (same as Task Tracker)

**Column I (Quality Check):**
- Validation: `Pass, Fail, Needs Review, N/A`
- Colors:
  - Pass → Green
  - Fail → Red
  - Needs Review → Yellow
  - N/A → Gray

### Add Checkboxes
**Add Column K (Reviewed?):**
1. Insert column after "Quality Check"
2. Header: "Reviewed?"
3. Select K2:K100
4. **Insert** → **Checkbox**

---

## 🎨 Sheet 4: Time Tracking

### Header Row
- **Bold** + **Teal background** (#00BFA5) + **White text**
- **Freeze:** Row 1

### Add Dropdowns

**Column D (Task Category):**
- Validation: `Setup, Research, Development, Testing, Documentation, DevOps, Meeting`

**Column I (Billable):**
- Convert to checkbox:
  1. Select I2:I100
  2. Replace "Yes" with checkboxes: **Insert** → **Checkbox**

### Formulas
**Add Column K (Duration Validation):**
```
=IF((TIMEVALUE(G2)-TIMEVALUE(F2))*24<>H2, "⚠️ Check", "✓")
```

**Add Row (Total Hours per Day):**
- At bottom, sum hours per date

### Conditional Formatting
**Highlight days with >8 hours (overtime):**
1. Select H2:H100
2. Custom formula: `=$H2>8`
3. Background: Light orange

---

## 🎨 Sheet 5: Issues & Blockers

### Header Row
- **Bold** + **Red background** (#EA4335) + **White text**
- **Freeze:** Row 1

### Add Dropdowns

**Column D (Severity):**
- Validation: `Low, Medium, High, Extreme`
- Conditional colors:
  - Extreme → Dark red (#A50E0E)
  - High → Red (#EA4335)
  - Medium → Orange (#F9AB00)
  - Low → Light blue (#4285F4)

**Column E (Type):**
- Validation: `Bug, Blocker, Risk, Technical Debt, Process Issue`

**Column H (Status):**
- Validation: `Open, In Progress, Resolved, Closed, Won't Fix`
- Colors:
  - Open → Red
  - In Progress → Yellow
  - Resolved → Green
  - Closed → Gray

### Add Checkboxes
**Add Column L (Critical?):**
- Insert checkbox column
- Check for High/Extreme severity items

### Conditional Formatting
**Highlight open issues older than 7 days:**
1. Select entire data range
2. Custom formula: `=AND($H2="Open", TODAY()-$B2>7)`
3. Background: Dark red

---

## 🎨 Sheet 6: Weekly Summary

### Header Row
- **Bold** + **Green background** (#34A853) + **White text**
- **Freeze:** Row 1

### Add Formulas

**Column E (Completion Rate):**
```
=D2/C2*100
```
Format as percentage.

**Conditional Formatting:**
- If >= 90% → Green background
- If 70-89% → Yellow background
- If < 70% → Red background

### Add Checkboxes
**Add Column J (Stakeholder Reported?):**
- Checkbox to track if weekly summary was sent to stakeholders

---

## 🎨 Sheet 7: Exit Criteria

### Header Row
- **Bold** + **Orange background** (#F9AB00) + **White text**
- **Freeze:** Row 1

### Add Dropdowns

**Column D (Status):**
- Validation: `Not Started, In Progress, At Risk, Complete`
- Colors:
  - Complete → Green
  - In Progress → Blue
  - At Risk → Red
  - Not Started → Gray

### Add Progress Bar
**Column C (Current Progress):**
1. Parse percentage from text
2. Use data bars: **Format** → **Conditional formatting** → **Color scale**
   - Min: Red (0%)
   - Mid: Yellow (50%)
   - Max: Green (100%)

### Add Checkboxes
**Add Column I (Gate Passed?):**
- Checkbox for each criterion
- Check only when 100% complete

### Conditional Formatting
**Highlight overdue criteria:**
- If Status = "At Risk" → Entire row red

---

## 🎨 Sheet 8: Team Roster

### Header Row
- **Bold** + **Indigo background** (#4285F4) + **White text**
- **Freeze:** Row 1

### Add Dropdowns

**Column G (Availability):**
- Validation: `Full-time, Part-time, Contractor, On Leave, Unavailable`

### Add Checkboxes
**Add Column I (Active?):**
- Checkbox to indicate if team member is currently active on project

---

## 🎨 GLOBAL Formatting (All Sheets)

### 1. Gridlines
- **View** → **Gridlines** → ✅ Check

### 2. Alternating Colors
For each sheet:
1. Select all data (A1:Z100)
2. **Format** → **Alternating colors**
3. Choose: **Light Blue 2** style

### 3. Column Alignment
- **Text columns** (descriptions, notes): Left align
- **Numbers** (hours, dates): Right align
- **Status/dropdowns**: Center align

### 4. Freeze Panes
- Every sheet: **View** → **Freeze** → **1 row** (header)

### 5. Protect Header Rows
1. Select row 1
2. **Data** → **Protected sheets and ranges**
3. **Set permissions** → Only you can edit

---

## 📋 Step-by-Step Application

### Do This Now (30 minutes):

**For Each Sheet (Repeat 8 times):**

1. ✅ **Format header row:**
   - Bold, colored background, white text, center align
   - Freeze row 1

2. ✅ **Add dropdowns:**
   - Status columns → validation lists
   - Priority/Severity → validation lists

3. ✅ **Add checkboxes:**
   - Where "Yes/No" appears → Insert checkbox
   - Add "Reviewed?" or "Complete?" columns

4. ✅ **Add conditional formatting:**
   - Status-based colors (green/yellow/red)
   - Overdue warnings

5. ✅ **Adjust column widths:**
   - Auto-fit or manual adjustment
   - Make sure text isn't cut off

6. ✅ **Add alternating row colors:**
   - Format → Alternating colors

---

## 🎨 Color Scheme Reference

| Purpose | Color | Hex Code |
|---------|-------|----------|
| Headers | Dark Blue | #1155CC |
| Complete/Pass | Green | #34A853 |
| In Progress | Blue | #4285F4 |
| Warning/Review | Yellow | #FFF2CC |
| Blocked/Fail | Red | #EA4335 |
| Critical/Extreme | Dark Red | #A50E0E |
| Not Started | Gray | #9AA0A6 |

---

## ✅ Checklist After Formatting

- [ ] All 8 sheets have formatted headers (bold, colored, white text)
- [ ] Row 1 is frozen on all sheets
- [ ] Status columns have dropdown validation
- [ ] Priority/Severity columns have dropdown validation
- [ ] Checkboxes added where needed
- [ ] Conditional formatting applied (green/yellow/red)
- [ ] Column widths adjusted (no cut-off text)
- [ ] Alternating row colors applied
- [ ] Numbers formatted correctly (decimals, percentages)
- [ ] Protected header rows

---

## 💡 Quick Formatting Tips

**Keyboard Shortcuts:**
- Bold: `Ctrl+B`
- Center align: `Ctrl+Shift+E`
- Right align: `Ctrl+Shift+R`
- Insert checkbox: `Ctrl+Alt+Shift+X`
- Format as number: `Ctrl+Shift+1`
- Format as percentage: `Ctrl+Shift+5`

**Batch Operations:**
- Select multiple cells/rows → Apply formatting once → Applies to all
- Use "Paint format" tool (roller icon) to copy formatting

---

## 🚀 Result

After applying all formatting, your Google Sheet will have:
- ✅ Professional color-coded headers
- ✅ Dropdown validation (no typos)
- ✅ Checkboxes for binary fields
- ✅ Conditional formatting (visual status at a glance)
- ✅ Progress bars
- ✅ Data validation
- ✅ Protected headers
- ✅ Proper number formatting
- ✅ Consistent styling across all sheets

**Total time:** ~30-45 minutes to format all 8 sheets

---

## 🆘 Need Help?

Tell me:
1. Which sheet you're formatting
2. What specific issue you're facing
3. Screenshot if possible

I'll give you exact steps!
