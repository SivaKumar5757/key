from flask import Flask, render_template, request, make_response
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
app = Flask(__name__)
user_answers = None
Qn = None
correct_anwser=None
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/omr', methods=['POST'])
def omr():
    global Qn,topic,subject,date
    subject = request.form['subject'].title()
    topic = request.form['topic'].title()
    num_questions = int(request.form['num_questions'])
    date = request.form['date']
    Qn = num_questions
    max_columns = 4
    questions_per_column = 50
    return render_template('omr.html', subject=subject, topic=topic, num_questions=num_questions, date=date, max_columns=max_columns, questions_per_column=questions_per_column)

@app.route('/answer_key', methods=['POST'])
def answer_key():
    global user_answers
    user_answers = {key: value for key, value in request.form.items() if key.startswith('user_q')}
    subject = request.form['subject']
    num_questions = int(request.form['num_questions'])
    date = request.form['date']
    topic = request.form['topic']
    print("User Answers:", user_answers)  # Debug print statement to check user answers
    
    return render_template('answer_key.html', subject=subject, topic=topic, num_questions=num_questions, date=date, user_answers=user_answers)

@app.route('/submit', methods=['POST'])
def submit():
    global user_answers,correct_answers,correct_count,wrong_count,empty_count,score,accuracy,question_analysis

    # Debug print to see all form data
    print("Form Data:", request.form)

    user_answers = {key.replace('user_q', 'q'): value for key, value in user_answers.items()}
    correct_answers = {key.replace('correct_q', 'q'): value for key, value in request.form.items() if key.startswith('correct_q')}

    # Debug print statements to check collected data
    print("User Answers:", user_answers)
    print("Correct Answers:", correct_answers)

    total = Qn
    ans = len(user_answers)
    correct_count = sum(1 for key in user_answers if user_answers[key] == correct_answers.get(key))
    wrong_count = sum(1 for key in user_answers if user_answers[key] != correct_answers.get(key))
    empty_count = total - ans
    score = correct_count * 4 - wrong_count
    accuracy = (correct_count / ans) * 100 if ans > 0 else 0

    # Prepare question-wise analysis
    question_analysis = {}
    for key in correct_answers:
        question_analysis[key] = {
            'user_answer': user_answers.get(key, 'Empty'),
            'correct_answer': correct_answers[key]
        }

    # Debug print statement to check the calculated score
    print("Score:", score)

    # Render the result template with the score and total number of questions
    return render_template('result.html', total=total, correct_count=correct_count, wrong_count=wrong_count, empty_count=empty_count, score=score, accuracy=accuracy, question_analysis=question_analysis)

@app.route('/download_pdf')
def download_pdf():
    buffer =io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Define constants for columns and rows
    num_columns = 5
    num_rows = 40
    column_width = 115  # Adjusted column width
    row_height = 15
    header_height = 20
    top_margin = 50
    bottom_margin = 50
    left_margin = 50  # Adjusted left margin
    right_margin = 50

    y_start = height - top_margin
    p.setFont("Helvetica-Bold", 12)
    p.drawString(left_margin, y_start+30, f"Subject: {subject}")
    p.setFont("Helvetica-Bold", 10)

    p.drawString(left_margin,y_start+15, f"Tittle: {topic}")
    p.drawString(508, y_start +15, f"Date: {date}")

    # Column headers
    p.setFont("Helvetica-Bold", 8)
    for i in range(num_columns):
        x = left_margin + i * column_width
        p.drawString(x, y_start, "Qn | Yr Ans | Cr Ans")

    # Questions
    p.setFont("Helvetica", 8)
    y_position = y_start - header_height

    for i in range(1, 200 + 1):
        question = str(i)
        user_answer = user_answers.get(f"q{question}", " ")
        correct_answer = correct_answers.get(f"q{question}", " ")

        column = (i - 1) // num_rows
        row = (i - 1) % num_rows

        x = left_margin + column * column_width
        y = y_position - row * row_height
        questio=int(question)
        if questio <10:
            line = f"{question}    | {user_answer}         | {correct_answer}"
        elif questio >9 and questio<100:
            line = f"{question}  | {user_answer}          | {correct_answer}"
        elif questio > 99:
            line = f"{question}| {user_answer}          | {correct_answer}"
        p.drawString(x, y,line)

        # Check if we need a new page
        if y < bottom_margin + row_height and i < Qn:
            p.showPage()
            p.setFont("Helvetica-Bold", 8)
            for j in range(num_columns):
                x = left_margin + j * column_width
                p.drawString(x, height - top_margin + 20, "Qn | Yr Ans | Cr Ans")
            p.setFont("Helvetica", 8)
            y_position = height - top_margin - header_height
            y = y_position

    # Summary (placed below the options)
    summary_y_position = y - row_height - 20
    p.setFont("Helvetica", 8)
    p.drawString(left_margin, summary_y_position, f"Total Questions: {Qn}")
    p.drawString(450, summary_y_position, f"Empty: {empty_count}")
    p.drawString(left_margin, summary_y_position -30, f"Correct: {correct_count}")
    p.drawString(450, summary_y_position -30, f"Wrong: {wrong_count}")
    p.setFont("Helvetica-Bold", 10)
    p.drawString(left_margin, summary_y_position - 60, f"Score: {score} / 720")
    p.drawString(450, summary_y_position - 60, f"Accuracy: {accuracy}%")
    p.save()

    pdf = buffer.getvalue()
    buffer.close()

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=result.pdf'

    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
