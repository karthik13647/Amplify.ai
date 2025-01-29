from flask import Flask, render_template, request, session,redirect,flash,url_for
import google.generativeai as genai
import os
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
# from werkzeug.security import generate_password_hash, check_password_hash 
from datetime import timedelta
from functools import wraps

app = Flask(__name__)


#Configure Gemini API
api_key = os.getenv('gemini_api_abhi')
if api_key: 
    genai.configure(api_key=api_key)
# print(my_api_key_gemini)
 # Ensure this is set in your environment
if not api_key:
    raise ValueError("API Key for Gemini is not set.")
app.secret_key = os.getenv('gemini_api_abhi')
# print(app.secret_key)
if not app.secret_key:
    raise ValueError("No secret key set. Make sure FLASK_SECRET_KEY is set in the environment.")
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///Users.db';
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Session expires after 30 minutes
db=SQLAlchemy(app)
bcrypt = Bcrypt(app)



class Users(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    first_name=db.Column(db.String(100),nullable=False)
    last_name=db.Column(db.String(100),nullable=False)
    email=db.Column(db.String(100),nullable=False,unique=True)
    password=db.Column(db.String(50),nullable=False)

    # def __init__(self,email,password,first_name,last_name):
    #     self.first_name=first_name
    #     self.last_name=last_name
    #     self.email=email
    #     self.password=bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt()).decode('utf-8')

    # def check_password(self,password):
    #     return bcrypt.checkpw(password.encode('utf-8'),self.password.encode('utf-8'))
    

# with app.app_context():
#     db.create_all()  RUN THE CODE WHEN YOU WANT TO CREATE THE DATABASE

@app.after_request
def add_cache_control(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "-1"
    return response

@app.route('/')
def home():
    return render_template('home_page.html')


# Custom decorator to require login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = Users.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            flash("Login Successful", "success")
            next_page = request.args.get('next')
            session['email'] = user.email
            return redirect(next_page) if next_page else redirect('/main_page')
        else:
            flash("Invalid credentials or user does not exist. Register now.", "danger")
            return render_template('login.html', error='Invalid User')

    return render_template("login.html")    
# @app.route('/login')
# def login():
#     if request.method=='POST':
#         email=request.form['email']
#         password=request.form['password']
#         user=Users.query.filter_by(email=email).first()
#         if user and user.check_password(password):
#             flash("Login Successfully")
#             session['email']= user.email
#             return redirect('/main_page')
#         else:
#             flash("User Not Exist, Register Now")
#             return render_template('login.html',error='Invalid User')

#     return render_template("login.html")

@app.route('/main_page', methods=['GET'])
@login_required
def main_page():
    if 'email' in session:
        return render_template("main_page.html")
    else:
        flash("Please log in first.", "warning")
        return redirect('/login')
    
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = Users(first_name=first_name, last_name=last_name, email=email, password=hashed_password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect('/login')
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
            return render_template("register.html")

    return render_template("register.html")

# @app.route('/register', methods=['POST','GET'])
# def register():
#     if request.method=='POST':
#         first_name=request.form['first_name']
#         last_name=request.form['last_name']
#         email=request.form['email']
#         password=request.form['password']
#         new_user=Users(first_name=first_name,last_name=last_name,email=email,password=password)
#         db.session.add(new_user)
#         db.session.commit()
#         return redirect('/login')

#     return render_template("register.html")

@app.route('/logout')
def logout():
    session.pop('email',None)
    return redirect('/login')


@app.route('/cold_mail', methods=['POST', 'GET'])
@login_required
def cold_mail():
    # input_text1= request.form.get('job_description')
    input_text2=request.form.get('resume_text')
    if not input_text2:
        return render_template('cold_mail.html',error="please provide inputs for both inputs")
    
    try:
    # Combine inputs into a single prompt
        combined_prompt = (
        f"Here is the input that contains the resume text:\n"
        f"Input 2: {input_text2}\n"
        f"give me the effective cold mail to recruiter that have to contains matter in input2 are present in it and make it in professional format"
        # f"Subject: Inquiry About Potential Job Opportunities\n\n"
        # f"Dear [Recruiter’s Name],\n\n"
        # f"I hope this message finds you well. I am writing to inquire about potential job openings at [Company Name]. "
        # f"I am highly interested in contributing to the impactful work being done by your team and would be grateful for "
        # f"any information regarding current or upcoming opportunities that align with my skill set.\n\n"
        # f"I have attached my resume for your reference. Please let me know if there are any roles available that fit my "
        # f"profile or if there are specific steps I should follow to apply successfully.\n\n"
        # f"Thank you for your time and assistance. I appreciate your consideration and look forward to hearing from you.\n\n"
        # f"Best regards,\n"
        # f"[Your Full Name]\n"
        # f"[Your Contact Information]\n"
        # f"[Your LinkedIn Profile (optional)]\n"
    )
        # Send the combined prompt to Gemini
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(combined_prompt)
        # Render the combined response in final.html
        # print("API Response:", response.text)
        return render_template(
            'final.html',
            combined_prompt=response.text
        )
    except Exception as e:
        return render_template('cold_mail.html', error=f"Error: {str(e)}")
    
@app.route('/keywords', methods=['POST', 'GET'])
@login_required
def keywords():
    input_text1= request.form.get('job_description')
    if not input_text1:
        return render_template('keywords.html',error="please provide inputs for both inputs")
    
    try:
        # Combine inputs into a single prompt
        combined_prompt = (
            f"Here are input that contains the job description:\n"
            f"Input 1: {input_text1}\n"
            f"give me the keywords that are present in the input1 those ATS will scanned during the selection"
        )

        # Send the combined prompt to Gemini
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(combined_prompt)
        # Render the combined response in final.html
        # print("API Response:", response.text)
        return render_template(
            'final.html',
            combined_prompt=response.text
        )
    except Exception as e:
        return render_template('keywords.html', error=f"Error: {str(e)}")
    

@app.route("/referral_message", methods=['POST', 'GET'])
@login_required
def referral_message():
    input1=request.form.get('job_id')
    input2=request.form.get('job_description')
    input3=request.form.get('resume_text')
    if not input1 or not input2 or not input3:
        return render_template('ref_msg.html' ,error="please provide inputs for all inputs")
    
    try:
        combined_prompt = (
        f"Here are three inputs that contain the job ID, job description, and resume text:\n"
        f"Input1: {input1}\n"
        f"Input2: {input2}\n"
        f"Input3: {input3}\n"
        f"give me the effective referral mail to recruiter that have to contains input1, input3 are present in it and make it in professional format according to the input2"
        # f"I hope this message finds you well. I am reaching out to seek your assistance and advice regarding a job opportunity at [Company Name]. I recently came across an open position for [Job Title] and its [Job ID] and believe that my skills and experience make me a strong candidate for the role.\n\n"
        # f"Having worked together at [Previous Company/Project], I greatly value your insight and professional opinion. I was wondering if you would be willing to refer me for this position. I truly believe that your endorsement would make a significant difference in my application.\n\n"
        # f"I have attached my updated resume for your reference. Please let me know if there is any additional information you need from me. I would be extremely grateful for any help you can provide.\n\n"
        # f"Thank you for considering my request. I appreciate your time and support.\n\n"
        # f"Best regards,\n\n"
        # f"[Your Full Name]\n\n"
        # f"[Your LinkedIn Profile (optional)]\n\n"
        # f"[Your Contact Information]"
        # f"like this generate the response according to the input2 and input3 that gave to you and important thing maintain the professionality in text"
    )
        model =genai.GenerativeModel('gemini-pro')
        response =model.generate_content(combined_prompt)

        return render_template(
            "final.html",
            combined_prompt=response.text
        )
    except Exception as e:
        return render_template("ref_msg.html", error=f"Error: {str(e)}")

@app.route('/cover_letter', methods=['POST', 'GET'])
@login_required
def cover_letter():
    input_text1= request.form.get('job_description')
    input_text2=request.form.get('resume_text')
    if not input_text1 or not input_text2:
        return render_template('cover_letter.html',error="please provide inputs for both inputs")
    
    try:
    # Combine inputs into a single prompt
        combined_prompt = (
        f"Here are two inputs that contain the job description and resume text:\n"
        f"Input 1: {input_text1}\n"
        f"Input 2: {input_text2}\n"
        f"give me the effective cover letter to recruiter that have to contains input2 skill set are present in it and make it in professional format according to the input1"
        # f"[Your Address]\n"
        # f"[City, State, ZIP Code]\n"
        # f"[Your Email Address]\n"
        # f"[Your Phone Number]\n"
        # f"[Date]\n\n"
        # f"[Recruiter’s Name]\n"
        # f"[Recruiter’s Title]\n"
        # f"[Company Name]\n"
        # f"[Company Address]\n"
        # f"[City, State, ZIP Code]\n\n"
        # f"Subject: Application for [Specific Role/Field]\n\n"
        # f"Dear [Recruiter’s Name],\n\n"
        # f"I hope this message finds you well. I am writing to express my interest in exploring career opportunities within [Company Name]. With a background in [Your Field/Industry] and extensive experience in [mention key skills or accomplishments relevant to the company], I believe I would be a valuable addition to your team.\n\n"
        # f"In my current/previous role as a [Your Current/Previous Position] at [Current/Previous Company], I successfully [mention one or two specific achievements or responsibilities, e.g., “led a team to complete a project ahead of schedule,” or “optimized processes to improve efficiency by 20%”]. My expertise lies in [mention key skills or areas of expertise relevant to the job you're applying for], and I am confident these skills align with the requirements of [Company Name].\n\n"
        # f"What excites me most about [Company Name] is your commitment to [mention something specific about the company, e.g., “innovative solutions in technology,” “building sustainable practices,” or “your culture of fostering growth”]. I am particularly interested in contributing to [specific project, initiative, or department] and believe that my skills in [relevant skill/area] would be a strong match for your needs.\n\n"
        # f"I have attached my resume for your review and would greatly appreciate the opportunity to discuss how my background, skills, and experiences align with the goals of [Company Name]. Please let me know if there are any current or upcoming roles that fit my profile, or if there is an opportunity to connect further.\n\n"
        # f"Thank you for your time and consideration. I look forward to the possibility of contributing to [Company Name]'s success and hope to hear from you soon.\n\n"
        # f"Best regards,\n"
        # f"[Your Full Name]\n"
        # f"[Your LinkedIn Profile (optional)]\n"
        # f"[Your Contact Information]\n"
    )
        #Send the combined prompt to Gemini
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(combined_prompt)
        # Render the combined response in final.html
        # print("API Response:", response.text)
        return render_template(
            'final.html',
            combined_prompt=response.text
        )
    except Exception as e:
        return render_template('cover_letter.html', error=f"Error: {str(e)}")
    


@app.route('/professional_summary', methods=['POST', 'GET'])
@login_required
def professional_summary():
    # Get input texts from the textareas
    input_text1 = request.form.get('job_description')
    input_text2 = request.form.get('resume_text')

    if not input_text1 or not input_text2:
        return render_template('professional_summary.html', error="Please provide input for both text areas.")

    try:
        # Combine inputs into a single prompt
        combined_prompt = (
            f"Here are two inputs that contains the job description and resume text:\n"
            f"Input 1: {input_text1}\n"
            f"Input 2: {input_text2}\n\n"
            f"So, you need to analyse the both input 1 and input2 then give me the professional summary to placed in resume like paragraph which contains 50 to 100 words and implant the keywords in professional summary that are present in the input1 ."
        )

        # Send the combined prompt to Gemini
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(combined_prompt)
        # Render the combined response in final.html
        # print("API Response:", response.text)
        return render_template(
            'final.html',
            combined_prompt=response.text
        )
    except Exception as e:
        return render_template('professional_summary.html', error=f"Error: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)
