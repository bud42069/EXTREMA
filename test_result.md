#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: |
  Build a trading signal detection system for SOLUSDT with two-stage swing detection methodology.
  Target: Capture >10% swings on 5-minute timeframe
  Stage 1: Candidate detection using ATR14, volume z-score, BB width at local extrema
  Stage 2: Micro confirmation with breakout candle + volume spike
  Features: CSV upload, signal analysis, backtesting with TP/SL ladder, dashboard visualization
  User has Helius API key for future on-chain integration

backend:
  - task: "CSV Data Upload & Storage"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "Implemented POST /api/upload-data endpoint. Parses CSV, validates columns, stores in MongoDB. Tested with curl - successfully uploaded 21,484 bars."

  - task: "Technical Indicators Calculation"
    implemented: true
    working: true
    file: "indicators.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "Implemented ATR14, RSI14, Bollinger Bands, EMA, volume z-score calculations. All indicators correctly calculated on dataset."

  - task: "Local Extrema Detection"
    implemented: true
    working: true
    file: "extrema_detection.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "Implemented local minima/maxima detection using ±12 bars window. Successfully detects swing start points."

  - task: "Two-Stage Signal Detection"
    implemented: true
    working: true
    file: "signal_detection.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "Implemented candidate detection (Stage 1) and micro confirmation (Stage 2). Found 291 candidates and 98 confirmed signals on test data."

  - task: "Backtesting Engine"
    implemented: true
    working: true
    file: "backtesting.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "Implemented full backtesting with TP/SL ladder, trailing stop, position sizing. Results: 98 trades, 62.2% win rate, 41.7% total P&L, 1.66 profit factor. Fixed df reference bug in close_trade method."

  - task: "Analysis API Endpoint"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "Implemented POST /api/analyze endpoint. Runs full analysis pipeline: indicators → extrema → candidates → confirmed signals. Returns detailed summary."

  - task: "Backtest API Endpoint"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "Implemented POST /api/backtest endpoint. Fetches analysis, runs backtest engine, stores results. Returns statistics and trade history."

  - task: "Chart Data API"
    implemented: true
    working: "NA"
    file: "server.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Implemented GET /api/chart-data endpoint for OHLCV + indicators. Not tested yet."

frontend:
  - task: "Dashboard Layout & Navigation"
    implemented: true
    working: true
    file: "App.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "Implemented sidebar navigation with routes for Dashboard, Upload, Analysis, Backtest pages. UI compiled successfully and loads correctly."

  - task: "Dashboard Page"
    implemented: true
    working: true
    file: "pages/DashboardPage.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "Implemented dashboard with stats cards, getting started guide, recent datasets table, methodology info. Shows 0 datasets initially as expected."

  - task: "Upload Page"
    implemented: true
    working: "NA"
    file: "pages/UploadPage.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Implemented CSV file upload with drag-drop area, validation, upload button. UI looks good. Needs E2E testing with actual file upload."

  - task: "Analysis Page"
    implemented: true
    working: "NA"
    file: "pages/AnalysisPage.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Implemented analysis configuration form with Stage 1 & 2 parameters, dataset selection, results display. Needs E2E testing."

  - task: "Backtest Page"
    implemented: true
    working: "NA"
    file: "pages/BacktestPage.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Implemented backtest config form, TP/SL parameters, results display with trade table. Needs E2E testing."

metadata:
  created_by: "main_agent"
  version: "1.0"
  test_sequence: 0
  run_ui: true

test_plan:
  current_focus:
    - "Full E2E workflow: Upload CSV → Analyze → Backtest"
    - "Upload Page - file selection and upload"
    - "Analysis Page - run analysis and view results"
    - "Backtest Page - run backtest and view performance"
  stuck_tasks: []
  test_all: true
  test_priority: "sequential"

agent_communication:
  - agent: "main"
    message: |
      Backend implementation complete and tested with curl:
      - CSV upload: ✅ Working (21,484 bars uploaded)
      - Analysis: ✅ Working (98 confirmed signals found)
      - Backtest: ✅ Working (62.2% win rate, 41.7% P&L)
      
      Frontend pages implemented:
      - Dashboard: ✅ Loads correctly
      - Upload: ⏳ Needs E2E testing
      - Analysis: ⏳ Needs E2E testing  
      - Backtest: ⏳ Needs E2E testing
      
      Ready for full frontend testing workflow.
      User should test manually or request automated testing agent.