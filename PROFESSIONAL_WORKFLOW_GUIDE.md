PROFESSIONAL WORKFLOW GUIDE
===========================

Claude Opus 4.5 + GitHub + VS Code = POWERFUL DEVELOPMENT ENVIRONMENT

This is your complete development workflow for the IRP project.

═══════════════════════════════════════════════════════════════════════════════
YOUR SETUP (PROFESSIONAL GRADE)
═════════════════════════════════════════════════════════════════════════════════

TOOLS:
  1. VS Code              (code editor)
  2. Claude Opus 4.5      (AI assistant in VS Code)
  3. GitHub               (version control & backup)
  4. Python 3.11          (runtime)
  5. Streamlit            (web framework)
  6. Git                  (local version control)

LOCATION:
  c:/Users/tskdkim/Projects/IRP_Web_App/

GIT REPOSITORY:
  https://github.com/YOUR_USERNAME/IRP_Web_App

═══════════════════════════════════════════════════════════════════════════════
STEP-BY-STEP: COMPLETE WORKFLOW
═════════════════════════════════════════════════════════════════════════════════

PHASE 1: INITIAL SETUP (One time - 15 minutes)
────────────────────────────────────────────────

1. CREATE GITHUB REPOSITORY
   └─ Go to https://github.com/new
   └─ Name: IRP_Web_App
   └─ Add Python .gitignore
   └─ Create repository

2. CLONE TO YOUR COMPUTER
   ```bash
   cd c:/Users/tskdkim/Projects
   git clone https://github.com/YOUR_USERNAME/IRP_Web_App.git
   cd IRP_Web_App
   ```

3. ADD YOUR FILES
   └─ Copy irp_web_app_enhanced.py to folder
   └─ Copy README.md to folder (replace default)
   └─ Generate requirements.txt:
   ```bash
   pip freeze > requirements.txt
   ```

4. OPEN IN VS CODE
   ```bash
   code .
   ```
   (Opens current folder in VS Code)

5. CONFIGURE GIT
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your@email.com"
   ```

6. FIRST COMMIT
   ```bash
   git add .
   git commit -m "Initial setup: IRP retirement tracker app"
   git push
   ```

VERIFY ON GITHUB:
  └─ Go to https://github.com/YOUR_USERNAME/IRP_Web_App
  └─ See your files? Perfect! ✓

═══════════════════════════════════════════════════════════════════════════════
PHASE 2: DAILY DEVELOPMENT WORKFLOW (Repeat for each change)
────────────────────────────────────────────────────────────────────────────

A. START YOUR SESSION
   ─────────────────────

   1. Open VS Code with your project
   2. Open Terminal (Ctrl+`)
   3. Activate virtual environment:
      ```bash
      venv\Scripts\activate
      ```
      (Should see (venv) in terminal)

B. DEVELOP A FEATURE
   ──────────────────

   1. DECIDE: What do you want to add/fix?
      Example: "Add error handling"

   2. WORK IN VS CODE
      └─ Edit irp_web_app_enhanced.py
      └─ Make your changes
      └─ Save (Ctrl+S)

   3. ASK CLAUDE IN VS CODE
      └─ Open Claude panel
      └─ Select your code
      └─ Ask: "Is this correct? Any improvements?"
      └─ Claude reviews and suggests
      └─ Incorporate feedback

   4. TEST LOCALLY
      ```bash
      streamlit run irp_web_app_enhanced.py
      ```
      └─ Verify it works
      └─ Check for errors
      └─ Test all features affected

   5. ITERATE IF NEEDED
      └─ Ask Claude: "How can I optimize this?"
      └─ Make improvements
      └─ Test again

C. COMMIT TO GIT
   ──────────────

   1. CHECK WHAT CHANGED
      ```bash
      git status
      ```
      └─ See modified files
      └─ See new files

   2. ADD FILES TO COMMIT
      ```bash
      git add .
      ```
      └─ Stages all changes

   3. COMMIT WITH MESSAGE
      ```bash
      git commit -m "Add error handling to dashboard"
      ```
      
      MESSAGE RULES:
      ├─ Start with verb: "Add", "Fix", "Update", "Improve"
      ├─ Be specific: "error handling" not "stuff"
      ├─ Keep under 50 characters
      └─ Clear what changed

   4. PUSH TO GITHUB
      ```bash
      git push
      ```
      └─ Uploads to GitHub
      └─ Backup created
      └─ Change is permanent

D. VERIFY ON GITHUB (Optional but good practice)
   ──────────────────────────────────────────────

   1. Go to: https://github.com/YOUR_USERNAME/IRP_Web_App
   2. See your latest commit? Perfect!
   3. Can click on commits to see what changed

E. END SESSION
   ───────────

   1. Stop Streamlit: Ctrl+C in terminal
   2. Deactivate venv:
      ```bash
      deactivate
      ```
   3. Close VS Code if done
   4. All changes are backed up on GitHub! ✓

═══════════════════════════════════════════════════════════════════════════════
USING CLAUDE OPUS 4.5 IN THIS WORKFLOW
═════════════════════════════════════════════════════════════════════════════════

CLAUDE INTEGRATION POINTS:

1. CODE REVIEW
   ├─ Select your code in VS Code
   ├─ Ask Claude: "Review this function for bugs"
   ├─ Claude analyzes your code
   ├─ Apply suggestions
   └─ Commit when improved

2. FEATURE DEVELOPMENT
   ├─ Ask Claude: "How do I add CSV export?"
   ├─ Claude provides code
   ├─ Copy-paste into your file
   ├─ Test locally
   ├─ Commit

3. BUG FIXING
   ├─ Get error running app
   ├─ Copy error to Claude
   ├─ Claude suggests fix
   ├─ Apply fix
   ├─ Test
   ├─ Commit

4. CODE IMPROVEMENT
   ├─ Ask Claude: "Optimize this calculation"
   ├─ Claude refactors
   ├─ Copy improved code
   ├─ Test
   ├─ Commit

5. COMMIT MESSAGES
   ├─ Ask Claude: "Help me write a commit message"
   ├─ Claude suggests clear message
   ├─ Use it for git commit

═══════════════════════════════════════════════════════════════════════════════
EXAMPLE: ADD A FEATURE WITH THIS WORKFLOW
═════════════════════════════════════════════════════════════════════════════════

GOAL: Add CSV export functionality

STEP 1: PLAN
  "I want to add CSV export. Show me how to implement it."
  
  Claude suggests:
  - Use pandas to_csv()
  - Add a button in sidebar
  - Export current data
  - Save with timestamp

STEP 2: DEVELOP
  In VS Code:
  ```python
  import pandas as pd
  
  if st.sidebar.button("Export to CSV"):
      df = pd.DataFrame(st.session_state.data)
      csv = df.to_csv(index=False)
      st.download_button(
          label="Download CSV",
          data=csv,
          file_name="irp_data.csv"
      )
  ```

STEP 3: REVIEW WITH CLAUDE
  Select code → Ask Claude: "Is this correct?"
  
  Claude: "Good! Consider adding date formatting..."
  
  Apply suggestions

STEP 4: TEST
  ```bash
  streamlit run irp_web_app_enhanced.py
  ```
  
  Click "Export to CSV" button
  Verify CSV downloads correctly

STEP 5: COMMIT
  ```bash
  git add .
  git commit -m "Add CSV export feature to sidebar"
  git push
  ```

STEP 6: VERIFY
  Go to GitHub
  See new commit in history ✓

DONE! Feature added, tested, committed, and backed up!

═══════════════════════════════════════════════════════════════════════════════
GIT WORKFLOW SUMMARY
═════════════════════════════════════════════════════════════════════════════════

BASIC CYCLE:

1. MODIFY CODE
   └─ Edit files in VS Code
   └─ Test with Streamlit

2. STAGE CHANGES
   ```bash
   git add .
   ```

3. COMMIT
   ```bash
   git commit -m "Clear message"
   ```

4. PUSH
   ```bash
   git push
   ```

5. VERIFY
   └─ Check GitHub to confirm

REPEAT for each feature/fix!

═══════════════════════════════════════════════════════════════════════════════
COMMON GIT COMMANDS (FOR REFERENCE)
═════════════════════════════════════════════════════════════════════════════════

CHECK STATUS:
  git status
  (see what changed, what's staged)

VIEW DIFFERENCES:
  git diff
  (see exact changes in files)

VIEW HISTORY:
  git log
  (see all commits)

VIEW ONE COMMIT:
  git show abc123def
  (show what changed in that commit)

UNDO LOCAL CHANGES:
  git restore filename.py
  (revert file to last commit)

UNDO LAST COMMIT:
  git reset --soft HEAD~1
  (undo commit but keep changes)

PULL LATEST FROM GITHUB:
  git pull
  (if someone else made changes)

═══════════════════════════════════════════════════════════════════════════════
PROJECT STRUCTURE FINAL
═════════════════════════════════════════════════════════════════════════════════

LOCAL FOLDER:
  c:/Users/tskdkim/Projects/IRP_Web_App/
  ├── .git/                         (hidden Git folder)
  ├── .gitignore                    (what to ignore)
  ├── README.md                     (documentation)
  ├── irp_web_app_enhanced.py       (your app - tracked)
  ├── requirements.txt              (packages - tracked)
  └── venv/                         (NOT tracked - ignored)

ON GITHUB:
  https://github.com/YOUR_USERNAME/IRP_Web_App/
  ├── .gitignore
  ├── README.md
  ├── irp_web_app_enhanced.py
  └── requirements.txt

(Only code and config are on GitHub, not venv or data!)

═══════════════════════════════════════════════════════════════════════════════
ADVANTAGES OF THIS WORKFLOW
═════════════════════════════════════════════════════════════════════════════════

WITH CLAUDE OPUS 4.5:
  ✓ Instant code review
  ✓ Better suggestions
  ✓ Error help immediately
  ✓ Stay in VS Code (no switching)
  ✓ Learn from Claude's explanations
  ✓ Faster development

WITH GITHUB:
  ✓ Cloud backup (safe)
  ✓ Version history (undo anytime)
  ✓ Share code easily
  ✓ Professional portfolio
  ✓ Scalable to team later
  ✓ Standard industry practice

COMBINED:
  ✓ Professional grade setup
  ✓ Fast development
  ✓ Safe (backups)
  ✓ Organized (Git history)
  ✓ Shareable (GitHub link)
  ✓ Scalable (ready for growth)

═══════════════════════════════════════════════════════════════════════════════
TROUBLESHOOTING
═════════════════════════════════════════════════════════════════════════════════

ISSUE: "venv folder uploaded to GitHub"
FIX:
  1. Delete venv from GitHub:
  ```bash
  git rm -r --cached venv
  git commit -m "Remove venv from tracking"
  git push
  ```
  2. Verify .gitignore has: venv/

ISSUE: "Got merge conflict"
FIX:
  1. Open file with conflict
  2. Look for <<<<<<, ======, >>>>>>
  3. Edit to keep what you want
  4. Delete conflict markers
  5. Save and commit

ISSUE: "Need to undo last commit"
FIX:
  ```bash
  git reset --soft HEAD~1
  git status (see files)
  git commit -m "Better message"
  ```

ISSUE: "Can't push - authentication error"
FIX:
  1. GitHub might need token (2FA enabled)
  2. Create token: https://github.com/settings/tokens
  3. Use token as password when pushing

═══════════════════════════════════════════════════════════════════════════════
YOUR NEXT STEPS
═════════════════════════════════════════════════════════════════════════════════

1. ✓ Create GitHub account (if needed)
2. ✓ Create GitHub repository: IRP_Web_App
3. ✓ Clone to c:/Users/tskdkim/Projects
4. ✓ Add your files
5. ✓ Configure Git (name & email)
6. ✓ Make first commit
7. ✓ Push to GitHub
8. → NOW: Copy your app code and paste here
9. → I'll review with Claude in mind
10. → You commit improvements
11. → Continue development with this workflow

═══════════════════════════════════════════════════════════════════════════════

READY FOR PROFESSIONAL DEVELOPMENT?

With Claude Opus 4.5 + GitHub + VS Code, you have a setup used by 
professional developers worldwide.

Let's build something great! 🚀

═══════════════════════════════════════════════════════════════════════════════
