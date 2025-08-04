# AI Syllabus Planner & Study Assistant
An intelligent web application that creates personalized, human-like study schedules for students. This tool helps you organize your subjects, track your progress, and provides a suite of AI-powered tools to make studying more efficient and engaging.

## ✨ Key Features

🧠 Intelligent Scheduling: Creates dynamic, time-blocked study plans based on your subjects, topics, and exam dates. The algorithm automatically accounts for:

Urgency: Prioritizes subjects with nearer exam dates.

Real-life Balance: Schedules fewer hours on weekends and blocks out time for meals.

Exam Preparation: Automatically schedules a "Final Revision" session the day before each exam and keeps exam days free.

👤 User Authentication: Secure login and signup functionality to save and manage personal study plans, notes, and progress.

📊 Interactive Dashboard: A personalized dashboard that visualizes your progress with a 7-day achievement graph and shows your tasks for the day at a glance.

🚀 Productivity Tools:

Pomodoro Timer: A built-in timer for focused study sessions (25 min focus, 5 min break).

Integrated Notes: A pop-up editor to take and save notes for each specific study task.

Dynamic Rescheduling: A one-click button to intelligently reschedule all overdue tasks.

💡 AI Study Assistant (Powered by Google Gemini):

AI Summarizer: Paste long articles or passages to get a concise, bullet-point summary.

Concept Simplifier: Rephrase complex topics into simple, easy-to-understand explanations.

Contextual Q&A: Ask specific questions about a passage from your textbook and get a direct answer.

🎨 Customization:

Features a persistent light/dark mode.

Adapts daily schedules based on whether you have weekday classes.

🛠️ Tech Stack
Backend: Python, Flask, SQLAlchemy

Frontend: HTML, CSS, JavaScript, Chart.js

Database: SQLite

AI: Google Gemini API

🚀 Getting Started
Follow these instructions to get the project set up and running on your local machine.

Prerequisites
Python 3.8+ and Pip installed on your system.

A Google AI API Key. You can get one for free from Google AI for Developers.

Installation & Setup
Clone the repository:

Bash

git clone https://github.com/your-username/your-repository-name.git
cd your-repository-name
Create a virtual environment:
It's highly recommended to use a virtual environment to keep project dependencies isolated.

Bash

# For Windows
python -m venv venv
venv\Scripts\activate

# For macOS / Linux
python3 -m venv venv
source venv/bin/activate
Install the required packages:

Bash

pip install -r requirements.txt
Set up your environment variables:

Create a new file named .env in the root of your project folder.

Open the .env file and add your Google AI API key like this:

GOOGLE_API_KEY="your-api-key-pasted-here"
Run the application:

Bash

python run.py
The application will start, and the terminal will show that it's running on http://127.0.0.1:5000. The first time you run it, a folder named instance with a database.db file will be created automatically.

💻 How to Use
Open your web browser and navigate to http://127.0.0.1:5000.

Sign Up for a new account.

Login with your new credentials.

You will be redirected to your Dashboard.

Navigate to the Planner page to add your subjects and generate your first study plan.

Visit the AI Assistant page to use the AI-powered study tools.
