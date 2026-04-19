# How to Create Single Excel File with All Sheets

## Method 1: Using Excel (5 minutes)

### Step 1: Open Excel
- Open Microsoft Excel
- Create a new blank workbook

### Step 2: Import Each CSV as a Sheet
Repeat for all 8 CSV files:

1. Go to **Data** tab → **Get Data** → **From File** → **From Text/CSV**
2. Navigate to: `c:\Users\pqm847\Documents\PromptOps\tracking\`
3. Select `01_daily_work_log.csv`
4. Click **Load** (or **Load To** → **Existing worksheet** if not first sheet)
5. Right-click the sheet tab → **Rename** → Type: **"Daily Work Log"**
6. Repeat for remaining files:

| CSV File | Sheet Name |
|----------|------------|
| 01_daily_work_log.csv | Daily Work Log |
| 02_task_tracker.csv | Task Tracker |
| 03_deliverables_tracker.csv | Deliverables |
| 04_time_tracking.csv | Time Tracking |
| 05_issues_blockers.csv | Issues & Blockers |
| 06_weekly_summary.csv | Weekly Summary |
| 07_phase1_exit_criteria.csv | Exit Criteria |
| 08_team_roster.csv | Team Roster |

### Step 3: Format (Optional)
For each sheet:
- Select header row (row 1)
- **Bold** the text
- Add background color (blue recommended)
- **View** tab → **Freeze Panes** → **Freeze Top Row**

### Step 4: Save
- **File** → **Save As**
- Location: `c:\Users\pqm847\Documents\PromptOps\`
- Filename: **`PromptOps_Tracking.xlsx`**
- Format: **Excel Workbook (.xlsx)**
- Click **Save**

---

## Method 2: Power Query (Faster - 2 minutes)

1. Open Excel → New Workbook
2. **Data** → **Get Data** → **From File** → **From Folder**
3. Browse to: `c:\Users\pqm847\Documents\PromptOps\tracking\`
4. Click **OK**
5. Click **Combine** → **Combine & Load**
6. Excel will create separate sheets for each CSV
7. Rename sheets to friendly names
8. Save as: **`PromptOps_Tracking.xlsx`**

---

## Method 3: Quick Copy-Paste (3 minutes)

1. Open Excel → New Workbook
2. For each CSV file:
   - Open CSV in Excel (double-click the CSV)
   - Select all (Ctrl+A)
   - Copy (Ctrl+C)
   - Go back to your workbook
   - Create new sheet (+ icon at bottom)
   - Paste (Ctrl+V)
   - Rename sheet
   - Close CSV file
3. Save workbook as **`PromptOps_Tracking.xlsx`**

---

## Method 4: Using Python Script (If Python Installed)

```bash
# Install openpyxl
pip install openpyxl

# Run the script
python create_tracking_excel.py
```

The script `create_tracking_excel.py` is already created in the repository.

---

## Result

You'll have one Excel file: **`PromptOps_Tracking.xlsx`** with 8 sheets:

1. **Daily Work Log** - Daily task logging
2. **Task Tracker** - All Phase 1 tasks
3. **Deliverables** - Code/data/docs tracking
4. **Time Tracking** - Hourly time logs
5. **Issues & Blockers** - Risk management
6. **Weekly Summary** - Stakeholder reports
7. **Exit Criteria** - Phase 1 gates
8. **Team Roster** - Team information

---

## Recommended Method

**Use Method 1 (Excel Import)** - Most reliable and gives you formatting control.

Time: ~5 minutes

---

## After Creating

1. Add to `.gitignore`: `*.xlsx` (Excel files shouldn't be in Git)
2. Keep the CSV files for version control
3. Regenerate Excel from CSVs whenever needed
4. Share Excel file via email/OneDrive, not Git

---

## Tips

- **Format headers**: Bold, colored background, freeze panes
- **Adjust column widths**: Auto-fit or manual adjustment
- **Add filters**: Select header row → Data → Filter
- **Conditional formatting**: Highlight overdue tasks, high priority
- **Create charts**: Weekly hours, completion rates, etc.

---

Would you like me to create the Excel file or do you prefer to do it yourself?
