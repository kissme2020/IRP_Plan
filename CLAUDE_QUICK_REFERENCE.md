CLAUDE OPUS IN VS CODE - QUICK REFERENCE CARD
==============================================

Print this! Common tasks and exact prompts to use.

═══════════════════════════════════════════════════════════════════════════════
QUICK START (First Time)
═════════════════════════════════════════════════════════════════════════════════

1. Install Extension
   ├─ Ctrl+Shift+X
   ├─ Search "Claude"
   ├─ Click Install

2. Sign In
   ├─ Click Claude icon (sidebar)
   ├─ Click "Sign in"
   ├─ Complete authentication

3. Start Using
   ├─ Open your Python file
   ├─ Press Ctrl+Shift+C
   ├─ Type your question
   ├─ Press Ctrl+Enter

═══════════════════════════════════════════════════════════════════════════════
COMMON TASKS & EXACT PROMPTS
═════════════════════════════════════════════════════════════════════════════════

TASK 1: CODE REVIEW
────────────────────

PROMPT:
```
Please review this code for:
1. Bugs or errors
2. Performance issues
3. Code quality
4. Missing error handling
5. Readability improvements
```

USE WHEN: Before committing to GitHub

─────────────────────────────────────────────────────────────────────────────

TASK 2: FIX A BUG
──────────────────

PROMPT:
```
I'm getting this error:
[paste full error message]

The error happens when: [describe situation]

Here's the relevant code:
[paste code section]

What's wrong and how do I fix it?
```

USE WHEN: App crashes or behaves wrong

─────────────────────────────────────────────────────────────────────────────

TASK 3: EXPLAIN EXISTING CODE
──────────────────────────────

PROMPT:
```
Can you explain how this function works?
[paste code]

Specifically, explain:
1. What it does
2. How it does it
3. Why it matters
```

USE WHEN: Understanding what code does

─────────────────────────────────────────────────────────────────────────────

TASK 4: ADD NEW FEATURE
────────────────────────

PROMPT:
```
I want to add [feature name] to my Streamlit app.

The feature should:
1. [requirement 1]
2. [requirement 2]
3. [requirement 3]

My app uses: Streamlit, pandas, plotly, pykrx

How should I implement this?
```

USE WHEN: Building new functionality

─────────────────────────────────────────────────────────────────────────────

TASK 5: OPTIMIZE CODE
──────────────────────

PROMPT:
```
This code is slow. Can you optimize it?

Current approach:
[explain what it does]

Here's the code:
[paste code]

What's a faster way to do this?
```

USE WHEN: Code runs but takes too long

─────────────────────────────────────────────────────────────────────────────

TASK 6: ADD DOCUMENTATION
──────────────────────────

PROMPT:
```
Can you add documentation to this function?

[paste function]

Please:
1. Add a docstring
2. Add inline comments
3. Explain the algorithm
```

USE WHEN: Making code more understandable

─────────────────────────────────────────────────────────────────────────────

TASK 7: FORMAT DATA FOR CONFIG
───────────────────────────────

PROMPT:
```
Format this ETF data for my etf_config.json:

Code: 102110
Name: KODEX US Total Market
Name KR: KODEX 미국종합주식
Type: Equity
Description: Entire US stock market
```

USE WHEN: Adding new ETFs

─────────────────────────────────────────────────────────────────────────────

TASK 8: HELP WITH DEBUGGING
────────────────────────────

PROMPT:
```
I'm stuck on a problem:

What I'm trying to do: [describe goal]
What I tried: [describe approach]
What happened: [describe result]
What I expected: [describe expected result]

Can you help me debug this?
```

USE WHEN: Don't know what's wrong

─────────────────────────────────────────────────────────────────────────────

TASK 9: LEARN HOW TO USE A LIBRARY
────────────────────────────────────

PROMPT:
```
I need to understand how [library] works.

Can you explain:
1. What it does
2. Basic usage
3. Common patterns
4. Show me a simple example

Then I'll use it in my code.
```

USE WHEN: Using pykrx, pandas, Streamlit, etc.

─────────────────────────────────────────────────────────────────────────────

TASK 10: TEST PLAN
───────────────────

PROMPT:
```
I just added [feature].

Can you create a test plan?

What should I test to make sure it works correctly?
```

USE WHEN: Before marking feature complete

═══════════════════════════════════════════════════════════════════════════════
KEYBOARD SHORTCUTS
═════════════════════════════════════════════════════════════════════════════════

Ctrl+Shift+C          Open Claude chat
Ctrl+Enter            Send message
Ctrl+S                Save file
Ctrl+`                Open terminal
Ctrl+Shift+X          Select text → Ask Claude
Ctrl+Shift+P          Command palette

═══════════════════════════════════════════════════════════════════════════════
WORKFLOW OVERVIEW
═════════════════════════════════════════════════════════════════════════════════

STEP 1: WRITE CODE
  └─ Edit irp_web_app_enhanced.py

STEP 2: ASK CLAUDE
  └─ Open Claude (Ctrl+Shift+C)
  └─ Ask for help
  └─ Get suggestions

STEP 3: APPLY CHANGES
  └─ Copy Claude's code
  └─ Paste into file
  └─ Save (Ctrl+S)

STEP 4: TEST
  └─ Run: streamlit run src/irp_web_app_enhanced.py
  └─ Verify it works

STEP 5: COMMIT
  └─ git add .
  └─ git commit -m "message"
  └─ git push

═══════════════════════════════════════════════════════════════════════════════
PRO TIPS
═════════════════════════════════════════════════════════════════════════════════

TIP 1: Share code context
  └─ Paste the relevant code section
  └─ Claude gives better answers

TIP 2: Be specific
  └─ Instead of "Review my code"
  └─ Try "Review the rebalancing function for bugs"

TIP 3: Break into smaller tasks
  └─ Ask Claude to fix one thing at a time
  └─ Easier to apply changes

TIP 4: Use Claude as teacher
  └─ Ask "Why does this work?"
  └─ Learn while you develop

TIP 5: Reference file names
  └─ Type: @irp_web_app_enhanced.py
  └─ Claude knows which file you mean

TIP 6: Show Claude the error
  └─ Paste full error message
  └─ Claude can diagnose faster

TIP 7: Explain your thinking
  └─ "I tried X but it didn't work"
  └─ Claude understands context better

═══════════════════════════════════════════════════════════════════════════════
ASKING FOR HELP
═════════════════════════════════════════════════════════════════════════════════

IF YOU'RE STUCK:

Step 1: Describe the problem
  └─ What are you trying to do?

Step 2: Show what you have
  └─ Paste relevant code

Step 3: Show what happens
  └─ Error message? Wrong output?

Step 4: Ask Claude for help
  └─ "Can you help me fix this?"

Example:

```
I'm trying to fetch ETF prices using pykrx.

Here's my code:
[paste code]

When I run it, I get this error:
ModuleNotFoundError: No module named 'pykrx'

I've already installed it. What's wrong?
```

═══════════════════════════════════════════════════════════════════════════════
FOR YOUR IRP PROJECT
═════════════════════════════════════════════════════════════════════════════════

COMMON QUESTIONS TO ASK CLAUDE:

About Rebalancing:
  "How does the rebalancing logic work?"
  "Why is HIGH priority set at 10%?"
  "Can I change the 5% drift threshold?"

About ETFs:
  "How do I add a new ETF?"
  "What's the correct format for etf_config.json?"
  "How does pykrx fetch prices?"

About Features:
  "Can I add CSV export?"
  "How do I display the data better?"
  "Should I add more pages?"

About Performance:
  "Is my code efficient?"
  "Why is loading slow?"
  "Can I cache prices?"

About Bugs:
  "I got error [error]. What's wrong?"
  "The app crashes when I do [action]"
  "Data isn't saving. Why?"

═══════════════════════════════════════════════════════════════════════════════
EXAMPLE CONVERSATION
═════════════════════════════════════════════════════════════════════════════════

YOU:
"Review the fetch_etf_prices function for bugs"

CLAUDE:
"I found 2 issues..."

YOU:
"Can you show me the fixed version?"

CLAUDE:
"Sure! Here's the corrected code:"

YOU:
"Perfect! I'll apply this now"

[You copy code, paste into file, save]

YOU:
"I applied the changes. Should I test anything specific?"

CLAUDE:
"Yes, test these 3 cases..."

[You test, everything works]

YOU:
"Great! It works. Thanks!"

[You commit and push to GitHub]

═══════════════════════════════════════════════════════════════════════════════
REMEMBER
═════════════════════════════════════════════════════════════════════════════════

✓ Claude is your code reviewer
✓ Claude is your debugging partner
✓ Claude is your learning resource
✓ Claude is always available in VS Code
✓ Claude can help you become a better developer

Keep Claude open while you code. Ask questions!

═══════════════════════════════════════════════════════════════════════════════
