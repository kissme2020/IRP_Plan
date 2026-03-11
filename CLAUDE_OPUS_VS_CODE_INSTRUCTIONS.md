CLAUDE OPUS 4.5 IN VS CODE - IRP PROJECT INTEGRATION GUIDE
==========================================================

Complete instructions for using Claude Opus AI agent in VS Code 
to develop, review, and maintain your IRP Retirement Tracker.

═══════════════════════════════════════════════════════════════════════════════
TABLE OF CONTENTS
═════════════════════════════════════════════════════════════════════════════════

1. Setup & Installation
2. Basic Usage (Chat Interface)
3. Code Review Workflow
4. Feature Development Workflow
5. Bug Fixing Workflow
6. ETF Configuration Workflow
7. Rebalancing Logic Workflow
8. Testing & Verification Workflow
9. Deployment Workflow
10. Advanced Tips & Tricks

═══════════════════════════════════════════════════════════════════════════════
PART 1: SETUP & INSTALLATION
═════════════════════════════════════════════════════════════════════════════════

STEP 1: INSTALL CLAUDE EXTENSION IN VS CODE
──────────────────────────────────────────────

1. Open VS Code
2. Press: Ctrl+Shift+X (Extensions panel)
3. Search: "Claude"
4. Look for: "Claude" extension by Anthropic
5. Click: "Install"
6. Wait for installation complete
7. VS Code may ask to reload - click "Reload"

VERIFY INSTALLATION:

1. Look at left sidebar
2. You should see a new icon (looks like Claude logo)
3. Click it to open Claude panel
4. You should see Claude chat interface

─────────────────────────────────────────────────────────────────────────────

STEP 2: AUTHENTICATE WITH ANTHROPIC
───────────────────────────────────────

1. Open Claude panel (click Claude icon in sidebar)
2. Click: "Sign in" or "Connect"
3. Browser opens to Anthropic login
4. Sign in with your Anthropic account
5. Grant permissions when asked
6. Return to VS Code
7. Claude panel should show: "Connected ✓"

─────────────────────────────────────────────────────────────────────────────

STEP 3: CONFIGURE CLAUDE SETTINGS
─────────────────────────────────────

1. Click: VS Code Settings (gear icon, bottom left)
2. Search: "Claude"
3. Configure:
   ├─ Model: Claude Opus 4.5 (select from dropdown)
   ├─ Auto-save: Enabled (recommended)
   ├─ Show preview: Enabled
   └─ Context size: Maximum

OPTIONAL: Set keyboard shortcuts

1. Click: Keyboard Shortcuts (Ctrl+K Ctrl+S)
2. Search: "Claude"
3. Assign shortcuts for:
   ├─ Open Claude chat: Ctrl+Shift+C (example)
   ├─ Send message: Ctrl+Enter
   └─ Insert code block: Ctrl+Shift+Insert

═══════════════════════════════════════════════════════════════════════════════
PART 2: BASIC USAGE (Chat INTERFACE)
═════════════════════════════════════════════════════════════════════════════════

OPENING CLAUDE CHAT
────────────────────

METHOD 1: Click Claude icon in sidebar
  └─ Sidebar → Claude icon (left side)
  └─ Opens Claude panel on right

METHOD 2: Keyboard shortcut
  └─ Press: Ctrl+Shift+C (if configured)
  └─ Opens Claude panel

SENDING MESSAGES
─────────────────

1. Type your question in Claude panel
2. Claude reads your current file automatically
3. Can reference the code in your question
4. Press: Ctrl+Enter or click "Send"
5. Claude responds with analysis/code

SELECTING CODE TO DISCUSS
───────────────────────────

METHOD 1: Claude sees current file
  ├─ When Claude panel is open
  ├─ Claude can see your active file
  ├─ Reference it in your message
  └─ Example: "Review this code for bugs"

METHOD 2: Select specific code
  ├─ Highlight code in editor
  ├─ Right-click → "Ask Claude"
  ├─ Opens Claude with selection
  └─ Claude references just that part

METHOD 3: Reference by file name
  ├─ Type: @filename.py
  ├─ Claude can see that file
  ├─ Example: "@irp_web_app_enhanced.py review rebalancing"

APPLYING CLAUDE'S SUGGESTIONS
──────────────────────────────

Claude provides code suggestions:

Option 1: Copy & Paste
  ├─ Click code block in Claude response
  ├─ Copy button appears
  ├─ Click to copy
  ├─ Paste in your file (Ctrl+V)
  └─ Manually apply changes

Option 2: "Insert in editor" (if available)
  ├─ Some Claude responses have "Insert" button
  ├─ Click it
  ├─ Code inserts at cursor location
  └─ Verify it looks correct

Option 3: Create new file
  ├─ Claude suggests new file
  ├─ Create file manually in VS Code
  ├─ Paste Claude's code
  ├─ Save with correct name

═══════════════════════════════════════════════════════════════════════════════
PART 3: CODE REVIEW WORKFLOW
═════════════════════════════════════════════════════════════════════════════════

WHEN: After writing code, before committing to GitHub

HOW TO USE CLAUDE FOR CODE REVIEW
──────────────────────────────────

STEP 1: Open your file in VS Code
  └─ File → Open → irp_web_app_enhanced.py

STEP 2: Open Claude panel
  └─ Click Claude icon in sidebar
  └─ Or press Ctrl+Shift+C

STEP 3: Ask Claude to review
  
  TYPE THIS IN CLAUDE:
  ```
  Please review this code for:
  1. Bugs or errors
  2. Performance issues
  3. Code quality improvements
  4. Missing error handling
  5. Readability suggestions
  ```

STEP 4: Read Claude's response
  ├─ Claude analyzes your file
  ├─ Provides detailed feedback
  ├─ Suggests specific improvements
  ├─ Explains why each matters
  └─ Shows example fixes

STEP 5: Apply improvements
  
  For each suggestion:
  1. Understand why Claude suggests it
  2. Ask Claude for clarification if needed
  3. Copy Claude's suggested code
  4. Paste into your file
  5. Test to make sure it works
  6. Save file (Ctrl+S)

STEP 6: Commit to GitHub
  
  Once all suggestions applied:
  ```bash
  git add .
  git commit -m "Code review fixes from Claude"
  git push
  ```

EXAMPLE CODE REVIEW SESSION
────────────────────────────

Claude panel:

  YOU: "Review the rebalancing function for bugs"
  
  CLAUDE: "I found 3 issues:
    1. Line 325: Missing null check
       Fix: if drift is not None
    2. Line 348: Sorting is inefficient
       Fix: Use sorted() instead of .sort()
    3. Missing error handling if pykrx fails
       Add: try-except block
    
    Here's the corrected function..."
  
  YOU: "Thanks! Can you also check for performance?"
  
  CLAUDE: "Sure! The function loops twice. 
    You can combine into single loop:
    [shows optimized code]"
  
  YOU: "Perfect! I'll apply these changes"

═══════════════════════════════════════════════════════════════════════════════
PART 4: FEATURE DEVELOPMENT WORKFLOW
═════════════════════════════════════════════════════════════════════════════════

WHEN: Adding new features to your app

EXAMPLE: Adding CSV export feature

STEP 1: Plan the feature
  
  TYPE IN CLAUDE:
  ```
  I want to add CSV export feature to my Streamlit app.
  Users should be able to:
  1. Click "Export Data" button
  2. Download current portfolio as CSV
  3. Include timestamps and values
  
  The app uses:
  - Streamlit framework
  - JSON data storage
  - Pandas for data processing
  
  How should I implement this?
  ```

STEP 2: Claude proposes approach
  
  CLAUDE RESPONDS WITH:
  ```
  Here's the recommended approach:
  
  1. Use pandas.to_csv()
  2. Add button in sidebar
  3. Use st.download_button()
  4. Format data before export
  
  Here's the code:
  [shows complete implementation]
  ```

STEP 3: Review Claude's suggestion
  
  YOU ASK:
  ```
  Is there error handling? 
  What if the JSON file is missing?
  ```
  
  CLAUDE RESPONDS:
  ```
  Good catch! Let me add error handling:
  [shows improved code with try-except]
  ```

STEP 4: Integrate into your code
  
  1. Copy Claude's code
  2. Paste into your app
  3. In correct location (sidebar section)
  4. Save file (Ctrl+S)

STEP 5: Test locally
  
  ```bash
  streamlit run src/irp_web_app_enhanced.py
  ```
  
  IN BROWSER:
  1. Click "Export Data" button
  2. Download CSV file
  3. Open CSV and verify data
  4. Check timestamps and values are correct

STEP 6: Commit to GitHub
  
  ```bash
  git add .
  git commit -m "Add CSV export feature"
  git push
  ```

═══════════════════════════════════════════════════════════════════════════════
PART 5: BUG FIXING WORKFLOW
═════════════════════════════════════════════════════════════════════════════════

WHEN: You get an error running the app

EXAMPLE: ModuleNotFoundError when running app

STEP 1: Get the error message
  
  When running app:
  ```
  ModuleNotFoundError: No module named 'pykrx'
  ```
  
  Copy the entire error (select, Ctrl+C)

STEP 2: Open Claude
  
  Click Claude icon in sidebar

STEP 3: Paste error and ask for help
  
  TYPE IN CLAUDE:
  ```
  I got this error when running my app:
  ModuleNotFoundError: No module named 'pykrx'
  
  I'm using Python 3.11 in a virtual environment.
  I installed pykrx using: pip install pykrx
  
  What could be wrong?
  ```

STEP 4: Claude diagnoses the issue
  
  CLAUDE RESPONDS:
  ```
  The issue is likely:
  1. Virtual environment not activated
  2. Package installed in wrong environment
  
  Try these steps:
  1. Check (venv) shows in terminal
  2. If not: venv\Scripts\activate
  3. Reinstall: pip install pykrx
  4. Verify: pip list | grep pykrx
  ```

STEP 5: Apply Claude's solution
  
  1. Follow Claude's steps
  2. Test if it works
  3. If still broken, report back to Claude

STEP 6: Commit fix if code change needed
  
  ```bash
  git add .
  git commit -m "Fix: install missing dependencies"
  git push
  ```

═══════════════════════════════════════════════════════════════════════════════
PART 6: ETF CONFIGURATION WORKFLOW
═════════════════════════════════════════════════════════════════════════════════

WHEN: Adding or modifying ETF configurations

STEP 1: Research new ETF on Samsung Fund
  
  Go to: https://www.samsungfund.com/
  
  Search for ETF:
  └─ Example: "KODEX US Total Market"
  
  Note down:
  ├─ Code: 102110
  ├─ Name: KODEX US Total Market (English)
  ├─ Name KR: KODEX 미국종합주식 (Korean)
  ├─ Type: Equity
  └─ Description: Entire US stock market

STEP 2: Ask Claude to format ETF config
  
  TYPE IN CLAUDE:
  ```
  I want to add a new ETF to my app.
  
  Here's the info:
  - Code: 102110
  - Name: KODEX US Total Market
  - Name KR: KODEX 미국종합주식
  - Type: Equity
  - Description: Entire US stock market
  
  Can you format this for my etf_config.json file?
  ```

STEP 3: Claude provides JSON format
  
  CLAUDE RESPONDS:
  ```json
  {
    "US Total Market": {
      "code": "102110",
      "name": "KODEX US Total Market",
      "name_kr": "KODEX 미국종합주식",
      "type": "Equity",
      "description": "Entire US stock market"
    }
  }
  ```

STEP 4: Add to etf_config.json
  
  1. Open file: data/etf_config.json
  2. Paste Claude's JSON block
  3. Make sure commas are correct
  4. Save file (Ctrl+S)

STEP 5: Update ALLOCATION_TARGET if needed
  
  If you want to include in rebalancing:
  
  TYPE IN CLAUDE:
  ```
  I added a new ETF "US Total Market" to my config.
  I want to allocate 5% to it.
  
  How do I update ALLOCATION_TARGET in my code?
  ```
  
  CLAUDE RESPONDS:
  ```python
  ALLOCATION_TARGET = {
      'AI Core Power': 0.28,
      'AI Tech TOP10': 0.14,
      'Dividend Stocks': 0.10,
      'Consumer Staples': 0.08,
      'Treasury Bonds': 0.11,
      'Gold': 0.07,
      'Japan TOPIX': 0.02,
      'US Total Market': 0.05,  # NEW
      'Cash': 0.15,  # Adjusted
  }
  ```

STEP 6: Test the change
  
  ```bash
  streamlit run src/irp_web_app_enhanced.py
  ```
  
  Verify:
  ├─ No errors on startup
  ├─ New ETF appears in holdings input
  ├─ App shows current price for new ETF
  └─ Rebalancing includes new ETF

STEP 7: Commit to GitHub
  
  ```bash
  git add .
  git commit -m "Add US Total Market ETF to portfolio"
  git push
  ```

═══════════════════════════════════════════════════════════════════════════════
PART 7: REBALANCING LOGIC WORKFLOW
═════════════════════════════════════════════════════════════════════════════════

WHEN: Understanding or modifying rebalancing logic

STEP 1: Ask Claude to explain rebalancing
  
  TYPE IN CLAUDE:
  ```
  @irp_web_app_enhanced.py
  
  Can you explain how the rebalancing logic works?
  Specifically:
  1. How does it detect drift?
  2. How does it generate recommendations?
  3. What triggers HIGH vs MEDIUM priority?
  ```

STEP 2: Claude explains the logic
  
  CLAUDE RESPONDS:
  ```
  The rebalancing logic works in 3 steps:
  
  1. DRIFT DETECTION (line 315):
     - Compares current allocation to target
     - Calculates: drift = |current - target|
     - Flags if drift > 5%
  
  2. RECOMMENDATION GENERATION (line 325):
     - If current > target: TRIM (sell)
     - If current < target: ADD (buy)
  
  3. PRIORITY RANKING (line 334):
     - HIGH: if drift > 10%
     - MEDIUM: if drift 5-10%
  ```

STEP 3: If you want to modify
  
  TYPE IN CLAUDE:
  ```
  I want to change the drift threshold from 5% to 3%.
  Where do I make this change?
  What else might break?
  ```
  
  CLAUDE RESPONDS:
  ```
  Change line 325:
  From: if drift > 0.05:
  To:   if drift > 0.03:
  
  This will trigger more rebalancing alerts.
  Side effects:
  1. More frequent rebalancing recommendations
  2. Might increase trading costs
  3. Could reduce slippage if market moving fast
  ```

STEP 4: Make the change
  
  1. Open irp_web_app_enhanced.py
  2. Go to line 325
  3. Change threshold value
  4. Save file (Ctrl+S)

STEP 5: Test thoroughly
  
  ```bash
  streamlit run src/irp_web_app_enhanced.py
  ```
  
  Test cases:
  ├─ Add sample holdings
  ├─ Verify rebalancing alerts appear
  ├─ Check priority levels are correct
  └─ Verify math is correct

STEP 6: Commit change
  
  ```bash
  git add .
  git commit -m "Reduce rebalancing drift threshold to 3%"
  git push
  ```

═══════════════════════════════════════════════════════════════════════════════
PART 8: TESTING & VERIFICATION WORKFLOW
═════════════════════════════════════════════════════════════════════════════════

WHEN: Testing new features before committing

CHECKLIST FOR TESTING
──────────────────────

STEP 1: Create test plan
  
  TYPE IN CLAUDE:
  ```
  I just added CSV export feature.
  Can you create a test plan?
  What should I verify?
  ```
  
  CLAUDE RESPONDS:
  ```
  Test the following:
  1. Button appears in UI
  2. Click triggers download
  3. CSV file contains correct data
  4. Timestamps are formatted correctly
  5. Values match app display
  6. Works with empty data
  7. Works with large data sets
  ```

STEP 2: Manual testing
  
  Run app:
  ```bash
  streamlit run src/irp_web_app_enhanced.py
  ```
  
  Go through each test case:
  ├─ Does button appear?
  ├─ Can you click it?
  ├─ Does download happen?
  ├─ Is CSV content correct?
  └─ No errors in terminal?

STEP 3: Report results to Claude
  
  TYPE IN CLAUDE:
  ```
  I tested the CSV export:
  ✓ Button appears
  ✓ Download works
  ✗ Timestamps are missing
  ✗ Column headers are wrong
  
  Can you fix these issues?
  ```
  
  CLAUDE RESPONDS:
  ```
  Here's the corrected code:
  [shows fix]
  ```

STEP 4: Apply fixes and retest
  
  1. Apply Claude's code
  2. Run app again
  3. Retest failed cases
  4. Verify fixes work

STEP 5: Performance testing
  
  TYPE IN CLAUDE:
  ```
  Is my code efficient enough?
  Any performance concerns?
  Will it work with 10 years of data?
  ```

STEP 6: Commit when all tests pass
  
  ```bash
  git add .
  git commit -m "CSV export feature - all tests passing"
  git push
  ```

═══════════════════════════════════════════════════════════════════════════════
PART 9: DEPLOYMENT WORKFLOW
═════════════════════════════════════════════════════════════════════════════════

WHEN: Ready to push to GitHub and use in production

BEFORE DEPLOYMENT CHECKLIST
────────────────────────────

STEP 1: Final code review
  
  TYPE IN CLAUDE:
  ```
  I'm about to deploy my app to GitHub.
  Can you do a final security review?
  
  Check for:
  1. Hardcoded credentials
  2. SQL injection risks
  3. File path issues
  4. Missing error handling
  5. Data validation
  ```
  
  CLAUDE RESPONDS:
  ```
  I found 2 issues:
  1. Line 450: Missing validation on user input
  2. Line 200: Hardcoded path won't work on Mac
  
  Here's how to fix:
  [shows fixes]
  ```

STEP 2: Update README
  
  TYPE IN CLAUDE:
  ```
  I'm deploying version 1.1 with CSV export feature.
  Can you update the README to document this?
  ```
  
  CLAUDE RESPONDS:
  ```
  Here's the updated README section:
  [shows updated docs]
  ```

STEP 3: Create requirements.txt
  
  TYPE IN CLAUDE:
  ```
  Can you help me create requirements.txt?
  My project uses: streamlit, pandas, plotly, 
  numpy, requests, pykrx
  ```
  
  CLAUDE RESPONDS:
  ```
  Create requirements.txt with:
  streamlit==1.28.1
  pandas==2.0.3
  plotly==5.14.0
  numpy==1.24.3
  requests==2.31.0
  pykrx==0.3.5
  ```

STEP 4: Final test
  
  ```bash
  streamlit run src/irp_web_app_enhanced.py
  ```
  
  Quick smoke test:
  ├─ App starts without errors
  ├─ All pages load
  ├─ No debug messages
  └─ Data persists

STEP 5: Commit and push
  
  ```bash
  git add .
  git commit -m "Version 1.1: Add CSV export and minor fixes"
  git push
  ```

STEP 6: Verify on GitHub
  
  1. Go to GitHub repo
  2. Verify latest commit is there
  3. Check all files uploaded
  4. README displays correctly

═══════════════════════════════════════════════════════════════════════════════
PART 10: ADVANCED TIPS & TRICKS
═════════════════════════════════════════════════════════════════════════════════

TIP 1: CONTEXT WINDOW MANAGEMENT
─────────────────────────────────

Your file is 1,918 lines. Claude might not see all at once.

SOLUTION 1: Ask Claude about specific functions

Instead of: "Review my entire code"
Use: "Review the fetch_etf_prices function (lines 93-130)"

SOLUTION 2: Share key functions

```
Here are the key functions in my app:
1. fetch_etf_prices() - Gets prices
2. get_rebalancing_recommendations() - Makes alerts
3. calculate_progress() - Tracks goal progress

Can you review function #2 for bugs?
```

TIP 2: ASKING CLAUDE TO FIX CODE
─────────────────────────────────

NOT EFFECTIVE:
"This code is slow. Fix it."

EFFECTIVE:
"This function calculates drift for 100 assets.
It uses a loop. Can you optimize it?
Here's the current code: [paste]"

TIP 3: USING CLAUDE FOR DOCUMENTATION
──────────────────────────────────────

```
Here's my calculate_progress function.
Can you:
1. Add docstring
2. Add inline comments
3. Explain the algorithm

[paste code]
```

TIP 4: DEBUGGING WITH CLAUDE
─────────────────────────────

When stuck:

```
I'm trying to do X but getting error Y.
Here's what I tried: [explain]
Here's the error: [paste full error]

What am I missing?
```

Claude is great at:
├─ Explaining error messages
├─ Suggesting debugging steps
├─ Catching typos
└─ Finding edge cases

TIP 5: LEARNING FROM CLAUDE
────────────────────────────

```
I don't understand how pykrx works.
Can you explain:
1. What it does
2. How to use it
3. Show me an example

Then I'll use it in my code.
```

Claude can teach you as you develop!

TIP 6: REFACTORING WITH CLAUDE
────────────────────────────────

```
My rebalancing logic is getting complex.
Here's the current approach:
[explain current code]

Should I refactor? If yes:
- What's a better approach?
- How would you restructure it?
- Show the refactored code
```

TIP 7: CLAUDE AS CODE MENTOR
──────────────────────────────

```
I'm learning Python and Streamlit.
Is there a more Pythonic way to write this?

[paste code]

Can you also explain the better approach?
```

Claude is patient and explains thoroughly!

═══════════════════════════════════════════════════════════════════════════════
SUMMARY: YOUR WORKFLOW
═════════════════════════════════════════════════════════════════════════════════

DAILY DEVELOPMENT:

1. WRITE CODE
   └─ Edit your app in VS Code

2. ASK CLAUDE
   └─ Press Ctrl+Shift+C
   └─ Ask for review/help
   └─ Copy Claude's suggestions

3. APPLY CHANGES
   └─ Integrate code
   └─ Save file (Ctrl+S)

4. TEST
   └─ Run: streamlit run...
   └─ Verify it works

5. COMMIT
   └─ git add .
   └─ git commit -m "message"
   └─ git push

WEEKLY:

- Ask Claude for performance review
- Refactor complex functions
- Add documentation
- Plan next features

MONTHLY:

- Full code review with Claude
- Update README
- Test all features
- Plan improvements

═══════════════════════════════════════════════════════════════════════════════
KEYBOARD SHORTCUTS
═════════════════════════════════════════════════════════════════════════════════

Ctrl+Shift+C         Open Claude chat
Ctrl+Enter           Send message to Claude
Ctrl+Shift+X         Select code → Ask Claude
Ctrl+S               Save file
Ctrl+`               Toggle terminal
Ctrl+Shift+P         Command palette

═══════════════════════════════════════════════════════════════════════════════
QUICK REFERENCE
═════════════════════════════════════════════════════════════════════════════════

Need code review?
→ "Review [filename] for [specific issues]"

Need bug fix?
→ Paste error + code + what you tried

Need feature help?
→ Explain feature + ask for implementation

Need explanation?
→ "Can you explain how [function] works?"

Need optimization?
→ Explain current approach + paste code

Need documentation?
→ "Add docstrings and comments to this function"

═══════════════════════════════════════════════════════════════════════════════
NEXT STEPS
═════════════════════════════════════════════════════════════════════════════════

1. Install Claude extension in VS Code
2. Sign in to your Anthropic account
3. Open your IRP project
4. Open Claude panel
5. Start asking questions!

You're now ready to develop your IRP app with Claude Opus 4.5! 🚀

═══════════════════════════════════════════════════════════════════════════════
