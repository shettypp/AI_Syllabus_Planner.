document.addEventListener('DOMContentLoaded', () => {
    
    // --- Theme Toggler Logic (Runs on all pages) ---
    const themeToggle = document.getElementById('theme-checkbox');
    if (themeToggle) {
        const currentTheme = localStorage.getItem('theme');
        const setTheme = (theme) => {
            document.body.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);
            themeToggle.checked = theme === 'dark';
        };
        if (currentTheme) setTheme(currentTheme);
        else setTheme('light');
        themeToggle.addEventListener('change', () => {
            setTheme(themeToggle.checked ? 'dark' : 'light');
        });
    }

    const createAlert = (message) => { alert(message); };

    // --- Real-time Progress Bar Updater ---
    function updateProgressBar() {
        const completedCountEl = document.getElementById('completed-tasks-count');
        const totalCountEl = document.getElementById('total-tasks-count');
        const progressBar = document.getElementById('progress-bar');
        const progressText = document.getElementById('progress-text');
        if (!completedCountEl || !totalCountEl || !progressBar || !progressText) return; 
        const completed = parseInt(completedCountEl.textContent);
        const total = parseInt(totalCountEl.textContent);
        const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;
        progressBar.style.width = percentage + '%';
        progressText.textContent = percentage + '%';
    }

    // --- Task Status Update Logic ---
    async function updateTaskStatus(taskId, isComplete) {
        try {
            const response = await fetch(`/update-task-status/${taskId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_complete: isComplete }),
            });
            if (!response.ok) throw new Error('Failed to update task');
            
            const completedCountEl = document.getElementById('completed-tasks-count');
            if(completedCountEl){
                let currentCompleted = parseInt(completedCountEl.textContent);
                completedCountEl.textContent = isComplete ? currentCompleted + 1 : currentCompleted - 1;
                updateProgressBar();
            }
        } catch (error) {
            createAlert('Could not update task status.');
            const checkbox = document.querySelector(`input[data-task-id="${taskId}"]`);
            if (checkbox) checkbox.checked = !isComplete;
        }
    }

    // --- Planner Page Setup ---
    const plannerPageSetup = () => {
        const studyForm = document.getElementById('study-form');
        if (!studyForm) return;

        // Pomodoro Timer Logic
        const pomodoroTimerSetup = () => {
            const timerDisplay = document.getElementById('timer-display');
            if (!timerDisplay) return;

            const startPauseBtn = document.getElementById('start-pause-btn');
            const resetBtn = document.getElementById('reset-btn');
            const modeButtons = document.querySelectorAll('.mode-btn');
            
            const timers = { pomodoro: 25 * 60, shortBreak: 5 * 60, longBreak: 15 * 60 };
            let timerInterval;
            let currentMode = 'pomodoro';
            let timeRemaining = timers[currentMode];
            let isPaused = true;

            function updateDisplay() {
                const minutes = Math.floor(timeRemaining / 60).toString().padStart(2, '0');
                const seconds = (timeRemaining % 60).toString().padStart(2, '0');
                timerDisplay.textContent = `${minutes}:${seconds}`;
                document.title = `${minutes}:${seconds} - AI Planner`;
            }

            function switchMode(newMode) {
                currentMode = newMode;
                clearInterval(timerInterval);
                isPaused = true;
                startPauseBtn.textContent = 'Start';
                timeRemaining = timers[newMode];
                updateDisplay();
                modeButtons.forEach(button => button.classList.toggle('active', button.dataset.mode === newMode));
            }

            function startTimer() {
                isPaused = false;
                startPauseBtn.textContent = 'Pause';
                timerInterval = setInterval(() => {
                    timeRemaining--;
                    updateDisplay();
                    if (timeRemaining <= 0) {
                        clearInterval(timerInterval);
                        alert("Time's up!");
                        switchMode(currentMode === 'pomodoro' ? 'shortBreak' : 'pomodoro');
                    }
                }, 1000);
            }

            function pauseTimer() {
                isPaused = true;
                startPauseBtn.textContent = 'Start';
                clearInterval(timerInterval);
            }

            modeButtons.forEach(button => button.addEventListener('click', () => switchMode(button.dataset.mode)));
            startPauseBtn.addEventListener('click', () => { (isPaused) ? startTimer() : pauseTimer(); });
            resetBtn.addEventListener('click', () => switchMode(currentMode));
            updateDisplay();
        };
        pomodoroTimerSetup();
        
        const loader = document.getElementById('loader');
        const showLoader = (text) => { if(loader) { loader.querySelector('p').textContent = text; loader.classList.remove('hidden'); } };
        const hideLoader = () => { if(loader) loader.classList.add('hidden'); };

        const addSubjectBtn = document.getElementById('add-subject-btn');
        const subjectEntriesContainer = document.getElementById('subject-entries');
        const planContainer = document.getElementById('plan-container');
        const notesModal = document.getElementById('notes-modal');
        const notesTextarea = document.getElementById('notes-textarea');
        const saveNotesBtn = document.getElementById('save-notes-btn');
        const cancelNotesBtn = document.getElementById('cancel-notes-btn');
        let currentNotesTaskId = null;
        const hasClassesCheckbox = document.getElementById('has-classes-checkbox');

        function openNotesModal(taskId, currentNotes) {
            currentNotesTaskId = taskId;
            notesTextarea.value = currentNotes;
            if (notesModal) notesModal.classList.remove('hidden');
        }
        function closeNotesModal() {
            if (notesModal) notesModal.classList.add('hidden');
            currentNotesTaskId = null;
        }
        async function saveNotes() {
            if (!currentNotesTaskId) return;
            showLoader("Saving Notes...");
            try {
                const response = await fetch(`/save-notes/${currentNotesTaskId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ notes: notesTextarea.value })
                });
                if (!response.ok) throw new Error('Failed to save notes');
                const notesButton = planContainer.querySelector(`.btn-notes[data-task-id="${currentNotesTaskId}"]`);
                if (notesButton) notesButton.dataset.notes = notesTextarea.value;
                closeNotesModal();
            } catch (error) {
                createAlert('Could not save notes.');
            } finally {
                hideLoader();
            }
        }

        if (saveNotesBtn) saveNotesBtn.addEventListener('click', saveNotes);
        if (cancelNotesBtn) cancelNotesBtn.addEventListener('click', closeNotesModal);
        if (notesModal) notesModal.addEventListener('click', (e) => { if (e.target === notesModal) closeNotesModal(); });
        
        function addSubjectEntry() {
            const entryDiv = document.createElement('div');
            entryDiv.className = 'subject-entry';
            entryDiv.innerHTML = `
                <input type="text" placeholder="Subject Name" class="subject-name" required>
                <input type="text" placeholder="Topics, comma, separated" class="subject-topics" required>
                <input type="date" class="subject-exam-date" required>
                <button type="button" class="btn-danger remove-btn">X</button>
            `;
            subjectEntriesContainer.appendChild(entryDiv);
            entryDiv.querySelector('.remove-btn').addEventListener('click', () => entryDiv.remove());
        }

        function getSubjectData() {
            const subjects = [];
            document.querySelectorAll('.subject-entry').forEach(entry => {
                const name = entry.querySelector('.subject-name').value.trim();
                const topics = entry.querySelector('.subject-topics').value.trim();
                const examDate = entry.querySelector('.subject-exam-date').value;
                if (name && topics && examDate) subjects.push({ name, topics, examDate });
            });
            return subjects;
        }

        if (studyForm) {
            studyForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                showLoader("Generating New Plan...");
                try {
                    const subjects = getSubjectData();
                    const has_classes = hasClassesCheckbox.checked;
                    if (subjects.length === 0) {
                        createAlert("Please add at least one subject.");
                        hideLoader();
                        return;
                    }
                    const response = await fetch('/generate-plan', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ subjects, has_classes }),
                    });
                    if (!response.ok) throw new Error('Server error');
                    window.location.reload();
                } catch (error) {
                    createAlert("Could not generate the plan.");
                    hideLoader();
                }
            });
        }
        
        if (addSubjectBtn) { addSubjectBtn.addEventListener('click', addSubjectEntry); addSubjectEntry(); }

        if (planContainer) {
            planContainer.addEventListener('click', (e) => {
                if (e.target.matches('input[type="checkbox"]')) {
                    updateTaskStatus(e.target.dataset.taskId, e.target.checked);
                }
                if (e.target.matches('.btn-notes')) {
                    openNotesModal(e.target.dataset.taskId, e.target.dataset.notes);
                }
            });
        }
    };

    // --- Dashboard Page ---
    const dashboardPageSetup = () => {
        const dashboardGrid = document.getElementById('dashboard-grid');
        if (!dashboardGrid) return;
        
        const todayTasksContainer = document.getElementById('today-tasks');
        if (todayTasksContainer) {
            todayTasksContainer.addEventListener('click', (e) => {
                if (e.target.matches('input[type="checkbox"]')) {
                    updateTaskStatus(e.target.dataset.taskId, e.target.checked);
                }
                if (e.target.matches('.btn-notes')) {
                    openNotesModal(e.target.dataset.taskId, e.target.dataset.notes);
                }
            });
        }
        
        const rescheduleBtn = document.getElementById('reschedule-btn');
        if (rescheduleBtn) {
            rescheduleBtn.addEventListener('click', async () => {
                alert("Rescheduling overdue tasks... The page will refresh upon completion.");
                try {
                    const response = await fetch('/reschedule-tasks', { method: 'POST' });
                    if (!response.ok) throw new Error('Failed to reschedule');
                    window.location.reload();
                } catch (error) {
                    createAlert('Could not reschedule tasks.');
                }
            });
        }
    };
    
    // --- AI Assistant (Tutor) Page ---
    const tutorPageSetup = () => {
        const assistantContainer = document.getElementById('ai-assistant-container');
        if (!assistantContainer) return;
        
        const loader = document.getElementById('loader');
        const showLoader = (text) => { if(loader) { loader.querySelector('p').textContent = text; loader.classList.remove('hidden'); } };
        const hideLoader = () => { if(loader) loader.classList.add('hidden'); };

        const inputText = document.getElementById('ai-input-text');
        const summarizeBtn = document.getElementById('summarize-btn');
        const simplifyBtn = document.getElementById('simplify-btn');
        const outputContainer = document.getElementById('ai-output-container');
        const outputText = document.getElementById('ai-output-text');
        const qnaForm = document.getElementById('qna-form');
        const qnaOutputContainer = document.getElementById('qna-output-container');
        const qnaOutputText = document.getElementById('qna-output-text');

        async function performAiAction(endpoint, text, loaderText) {
            if (!text) { createAlert("Please paste some text into the text area first."); return; }
            showLoader(loaderText);
            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text }),
                });
                const data = await response.json();
                if (data.error) throw new Error(data.error);
                outputContainer.classList.remove('hidden');
                outputText.textContent = data.result;
            } catch (error) {
                createAlert(`An error occurred: ${error.message}`);
                outputContainer.classList.add('hidden');
            } finally {
                hideLoader();
            }
        }
        
        if (summarizeBtn) {
            summarizeBtn.addEventListener('click', () => {
                performAiAction('/summarize-text', inputText.value.trim(), 'Summarizing...');
            });
        }
        if (simplifyBtn) {
            simplifyBtn.addEventListener('click', () => {
                performAiAction('/simplify-text', inputText.value.trim(), 'Simplifying...');
            });
        }
        if (qnaForm) {
            qnaForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const context = document.getElementById('qna-context').value.trim();
                const question = document.getElementById('qna-question').value.trim();
                if (!context || !question) { createAlert('Please provide both a context and a question.'); return; }
                showLoader('Finding Answer...');
                try {
                    const response = await fetch('/ask-context-question', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ context, question }),
                    });
                    const data = await response.json();
                    if (data.error) throw new Error(data.error);
                    qnaOutputContainer.classList.remove('hidden');
                    qnaOutputText.textContent = data.result;
                } catch (error) {
                    createAlert(`An error occurred: ${error.message}`);
                    qnaOutputContainer.classList.add('hidden');
                } finally {
                    hideLoader();
                }
            });
        }
    };

    // Run setup for all pages
    plannerPageSetup();
    dashboardPageSetup();
    tutorPageSetup();
});