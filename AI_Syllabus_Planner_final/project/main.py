from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from . import db
from .models import Task
from datetime import datetime, timedelta, date, time
from sqlalchemy import func
import google.generativeai as genai
import json

main = Blueprint('main', __name__)

@main.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('home.html')

@main.route('/dashboard')
@login_required
def dashboard():
    total_tasks = Task.query.filter_by(user_id=current_user.id, task_type='study').count()
    completed_tasks_query = Task.query.filter_by(user_id=current_user.id, is_complete=True, task_type='study')
    completed_tasks = completed_tasks_query.count()
    
    completion_percentage = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    today = date.today()
    todays_tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.due_date == today,
        Task.task_type == 'study'
    ).order_by(Task.start_time).all()

    overdue_tasks_exist = Task.query.filter(Task.user_id == current_user.id, Task.is_complete == False, Task.due_date < today).first() is not None

    chart_labels = []
    chart_data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        chart_labels.append(day.strftime('%a'))
        
        completed_on_day = Task.query.filter(
            Task.user_id == current_user.id,
            Task.is_complete == True,
            Task.task_type == 'study',
            func.date(Task.due_date) == day
        ).count()
        chart_data.append(completed_on_day)

    return render_template('dashboard.html', 
                           name=current_user.name,
                           total_tasks=total_tasks,
                           completed_tasks=completed_tasks,
                           completion_percentage=completion_percentage,
                           todays_tasks=todays_tasks,
                           overdue_tasks_exist=overdue_tasks_exist,
                           chart_labels=json.dumps(chart_labels),
                           chart_data=json.dumps(chart_data))

@main.route('/planner')
@login_required
def planner():
    tasks_from_db = Task.query.filter_by(user_id=current_user.id).order_by(Task.due_date, Task.start_time).all()
    plan = {}
    for task in tasks_from_db:
        date_key = task.due_date.isoformat()
        if date_key not in plan:
            plan[date_key] = []
        plan[date_key].append(task)
    return render_template('planner.html', name=current_user.name, plan=plan)

@main.route('/tutor')
@login_required
def tutor():
    return render_template('tutor.html', name=current_user.name)

# --- API Routes ---
@main.route('/generate-plan', methods=['POST'])
@login_required
def generate_plan():
    try:
        Task.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        user_data = request.get_json()
        subjects_input = user_data.get('subjects', [])
        has_classes = user_data.get('has_classes', False)
        today = date.today()
        subjects = []
        for s in subjects_input:
            if not all(k in s for k in ['name', 'topics', 'examDate']) or not s['examDate']: continue
            exam_date = datetime.strptime(s['examDate'], "%Y-%m-%d").date()
            topics = [t.strip() for t in s['topics'].split(',') if t.strip()]
            if topics and exam_date > today: subjects.append({'name': s['name'], 'topics': topics, 'exam_date': exam_date})
        subjects.sort(key=lambda x: x['exam_date'])
        if not subjects: return jsonify({'success': True})
        latest_exam_date = max(s['exam_date'] for s in subjects)
        SCHEDULES = {
            "WEEKEND": [{'start': time(10, 0), 'end': time(13, 0), 'type': 'study'}, {'start': time(13, 0), 'end': time(14, 0), 'type': 'break', 'task': {'subject': 'Break', 'topic': 'Lunch Break'}}, {'start': time(14, 0), 'end': time(17, 0), 'type': 'study'}],
            "WEEKDAY_NO_CLASS": [{'start': time(9, 0), 'end': time(13, 0), 'type': 'study'}, {'start': time(13, 0), 'end': time(14, 0), 'type': 'break', 'task': {'subject': 'Break', 'topic': 'Lunch Break'}}, {'start': time(14, 0), 'end': time(17, 0), 'type': 'study'}, {'start': time(17, 0), 'end': time(18, 0), 'type': 'break', 'task': {'subject': 'Break', 'topic': 'Evening Break'}}, {'start': time(18, 0), 'end': time(20, 0), 'type': 'study'}],
            "WEEKDAY_WITH_CLASS": [{'start': time(6, 30), 'end': time(7, 30), 'type': 'study'}, {'start': time(9, 0), 'end': time(17, 0), 'type': 'break', 'task': {'subject': 'School', 'topic': 'Classes'}}, {'start': time(17, 0), 'end': time(18, 0), 'type': 'break', 'task': {'subject': 'Break', 'topic': 'Evening Break'}}, {'start': time(18, 0), 'end': time(20, 0), 'type': 'study'}, {'start': time(21, 0), 'end': time(22, 0), 'type': 'study'}]
        }
        calendar = {}
        for i in range((latest_exam_date - today).days + 1):
            current_date = today + timedelta(days=i)
            day_type = current_date.weekday()
            schedule_template = SCHEDULES['WEEKEND'] if day_type >= 5 else (SCHEDULES['WEEKDAY_WITH_CLASS'] if has_classes else SCHEDULES['WEEKDAY_NO_CLASS'])
            calendar[current_date] = [{'start': s['start'], 'end': s['end'], 'type': s['type'], 'task': s.get('task')} for s in schedule_template]
        for subject in subjects:
            exam_day = subject['exam_date']
            if exam_day in calendar: calendar[exam_day] = [{'start': time(0, 0), 'end': time(23, 59), 'type': 'break', 'task': {'subject': subject['name'], 'topic': 'EXAM DAY'}}]
            revision_day = exam_day - timedelta(days=1)
            if revision_day in calendar:
                for slot in reversed(calendar[revision_day]):
                    if slot['type'] == 'study' and slot['task'] is None: slot['task'] = {'subject': subject['name'], 'topic': f"Final Revision for {subject['name']}"}; break
        all_topics_flat = []
        for subject in subjects:
            for topic in subject['topics']: all_topics_flat.append({'subject': subject['name'], 'topic': topic, 'exam_date': subject['exam_date']})
        for topic_task in all_topics_flat:
            scheduled = False
            for day in sorted(calendar.keys()):
                if day < topic_task['exam_date']:
                    for slot in calendar[day]:
                        if slot['type'] == 'study' and slot['task'] is None: slot['task'] = topic_task; scheduled = True; break
                if scheduled: break
        for day, slots in calendar.items():
            for slot in slots:
                if slot['type'] == 'study' and slot['task'] is None:
                    relevant_subject = next((s['name'] for s in reversed(subjects) if day < s['exam_date']), "Overall")
                    slot['task'] = {'subject': relevant_subject, 'topic': f"Revision: {relevant_subject}"}
        for day, slots in calendar.items():
            for slot in slots:
                if slot['task']:
                    db.session.add(Task(subject=slot['task']['subject'], topic=slot['task']['topic'], due_date=day, start_time=slot['start'], end_time=slot['end'], user_id=current_user.id, task_type=slot['type']))
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback(); return jsonify({'error': 'A critical server error occurred.', 'details': str(e)}), 500

@main.route('/update-task-status/<int:task_id>', methods=['POST'])
@login_required
def update_task_status(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id: return jsonify({'error': 'Unauthorized'}), 403
    task.is_complete = request.get_json().get('is_complete', False)
    db.session.commit()
    return jsonify({'success': True})

@main.route('/save-notes/<int:task_id>', methods=['POST'])
@login_required
def save_notes(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id: return jsonify({'error': 'Unauthorized'}), 403
    task.notes = request.get_json().get('notes', '')
    db.session.commit()
    return jsonify({'success': True, 'message': 'Notes saved.'})

@main.route('/reschedule-tasks', methods=['POST'])
@login_required
def reschedule_tasks():
    try:
        today = date.today()
        overdue_tasks = Task.query.filter(Task.user_id == current_user.id, Task.is_complete == False, Task.due_date < today).all()
        if not overdue_tasks: return jsonify({'message': 'No overdue tasks to reschedule.'})
        future_tasks_count = db.session.query(Task.due_date, func.count(Task.id)).filter(Task.user_id == current_user.id, Task.due_date > today).group_by(Task.due_date).all()
        tasks_per_day = {day: count for day, count in future_tasks_count}
        last_day = max(tasks_per_day.keys()) if tasks_per_day else today
        for task in overdue_tasks:
            potential_date = today + timedelta(days=1)
            while potential_date <= last_day:
                if tasks_per_day.get(potential_date, 0) < 2:
                    task.due_date = potential_date; tasks_per_day[potential_date] = tasks_per_day.get(potential_date, 0) + 1; break
                potential_date += timedelta(days=1)
            else:
                last_day += timedelta(days=1); task.due_date = last_day; tasks_per_day[last_day] = 1
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback(); return jsonify({'error': 'Failed to reschedule tasks.', 'details': str(e)}), 500

def call_gemini_api(prompt):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: The AI service could not be reached. Details: {str(e)}"

@main.route('/summarize-text', methods=['POST'])
@login_required
def summarize_text():
    prompt = f"Summarize the following text into key bullet points:\n\n{request.get_json().get('text')}"
    summary = call_gemini_api(prompt)
    if summary.startswith("Error:"): return jsonify({'error': summary}), 500
    return jsonify({'result': summary})

@main.route('/simplify-text', methods=['POST'])
@login_required
def simplify_text():
    prompt = f"Explain the following concept in simple terms:\n\n{request.get_json().get('text')}"
    simplified_text = call_gemini_api(prompt)
    if simplified_text.startswith("Error:"): return jsonify({'error': simplified_text}), 500
    return jsonify({'result': simplified_text})

@main.route('/ask-context-question', methods=['POST'])
@login_required
def ask_context_question():
    data = request.get_json()
    context = data.get('context')
    question = data.get('question')
    if not context or not question:
        return jsonify({'error': 'Context and question are required.'}), 400
    prompt = f"Based ONLY on the following context, answer the question.\n\nCONTEXT: '''{context}'''\n\nQUESTION: {question}\n\nANSWER:"
    answer = call_gemini_api(prompt)
    if answer.startswith("Error:"):
        return jsonify({'error': answer}), 500
    return jsonify({'result': answer})