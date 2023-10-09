from flask import Flask,redirect,url_for,request,render_template,flash,session,abort
import mysql.connector
from flask_session import Session
from key import secret_key,salt
from itsdangerous import URLSafeTimedSerializer
from stoken import token
from cmail import sendmail
import os
import smtplib
from flask_excel import init_excel
import mysql.connector  # Import the MySQL library
from sotp import *
from tokenreset import token
import csv
from flask import Flask, render_template, Response
import mysql.connector
import io
from itsdangerous import URLSafeTimedSerializer

# Replace 'your-secret-key' with your actual secret key

app=Flask(__name__)
app.secret_key= b'\x011\xd3\xb9\x1a\x97{\xe6\x87\xeb{2\xbe*\xcfI\xde\x02\xe7\x89'
app.config['SESSION_TYPE']='filesystem' 
user=os.environ.get('RDS_USERNAME')
db=os.environ.get('RDS_DB_NAME')
password=os.environ.get('RDS_PASSWORD')
host=os.environ.get('RDS_HOSTNAME')
port=os.environ.get('RDS_PORT')
with mysql.connector.connect(host="Satwika",user="system",password="root",port="3306",db="spm") as conn:
    cursor=conn.cursor(buffered=True)
    cursor.execute("create table if not exists users(rollno varchar(50) primary key,password varchar(15),email varchar(60))")
    cursor.execute("create table if not exists notes(nid int not null auto_increment primary key,title tinytext,content text,date timestamp default now() on update now(),added_by varchar(50),foreign key(added_by) references users(rollno))")
    cursor.close()
#mydb=mysql.connector.connect(host=host,user=user,password=password,db=db)
mydb=mysql.connector.connect(host="Satwika",user="system",password="root",db="spm")
init_excel(app)
serializer = URLSafeTimedSerializer(b'\x011\xd3\xb9\x1a\x97{\xe6\x87\xeb{2\xbe*\xcfI\xde\x02\xe7\x89')

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/home',methods=['GET','POST'])
def home():
    return render_template('home.html')
def create_smtp_server():
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    return server

#@app.route('/register', methods=['GET', 'POST'])
#def register():
    #if request.method == 'POST':
        ## Your registration code here
       # try:
            #with create_smtp_server() as server:
                # Send email code here
       # except Exception as e:
            # Handle email sending error
    #return render_template('register.html')

# The rest of your routes...
def generate_token(data):
    return serializer.dumps(data)

def verify_token(token, max_age):
    try:
        data = serializer.loads(token, max_age=max_age)
        return data
    except Exception as e:
        # Handle token verification error here
        return None
def sendmail(to, body, subject):
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login('satwikapoluri@gmail.com', 'rpcg owoh nkij fmgm')
        message = f"Subject: {subject}\n\n{body}"
        server.sendmail('satwikapoluri@gmail.com', to, message)
        server.close()
        print("Email sent successfully.")
    except Exception as e:
        print(f"Email could not be sent. Error: {str(e)}")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        rollno = request.form['rollno']
        password = request.form['password']
        email = request.form['email']
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select count(*) from users where rollno=%s', [rollno])
        count = cursor.fetchone()[0]
        cursor.execute('select count(*) from users where email=%s', [email])
        count1 = cursor.fetchone()[0]
        cursor.close()
        
        if count == 1:
            flash('Username already in use')
            return render_template('register.html')
        elif count1 == 1:
            flash('Email already in use')
            return render_template('register.html')
        
        data = {'rollno': rollno, 'password': password, 'email': email}
        subject = 'Email Confirmation'
        body = f"Thanks for signing up\n\nfollow this link for further steps-{url_for('confirm', token=token(data, salt='f4db28e23409f84183ba442b7d607d6d'), _external=True)}"

        
        try:
            with create_smtp_server() as server:
                server.login("satwikapoluri@gmail.com", "rpcg owoh nkij fmgm")  # Replace with your Gmail credentials
                server.sendmail("satwikapoluri@gmail.com", email, body)
        except Exception as e:
            flash('Error sending confirmation email')
            return render_template('register.html')
        
        flash('Confirmation link sent to your email')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/confirm/<token>')
def confirm(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        data=serializer.loads(token,salt='f4db28e23409f84183ba442b7d607d6d',max_age=86400)
    except Exception as e:
        #print(e)
        return 'Link Expired register again'
    else:
        cursor=mydb.cursor(buffered=True)
        rollno=data['rollno']
        cursor.execute('select count(*) from users where rollno=%s',[rollno])
        count=cursor.fetchone()[0]
        if count==1:
            cursor.close()
            flash('You are already registerterd!')
            return redirect(url_for('login'))
        else:
            cursor.execute('insert into users values(%s,%s,%s)',[data['rollno'],data['password'],data['email']])
            mydb.commit()
            cursor.close()
            flash('Details registered!')
            return redirect(url_for('login'))
        
@app.route('/dashboard')
def dashboard():
    if session.get('user'):
        return render_template('dashboard.html')
    else:
        return redirect(url_for('login'))

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')    

@app.route('/contactus', methods=['GET', 'POST'])
def contactus():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        
        cursor = mydb.cursor(buffered=True)
        cursor.execute('INSERT INTO contact (name, email, message) VALUES (%s, %s, %s)', (name, email, message))
        mydb.commit()  # Commit the transaction to save the data
        
        cursor.close()
        
        return redirect(url_for('index'))
    return render_template('contactus.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user'):
        return redirect(url_for('dashboard'))  # Redirect to the dashboard if already logged in
    
    if request.method == 'POST':
        rollno = request.form['rollno']
        password = request.form['password']
        cursor = mydb.cursor(buffered=True)
        cursor.execute('SELECT count(*) from users where rollno=%s and password=%s', [rollno, password])
        count = cursor.fetchone()[0]
        cursor.close()
        
        if count == 1:
            session['user'] = rollno
            flash('Login successful')
            return redirect(url_for('dashboard'))  # Redirect to the dashboard or home page
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')

def logout():
    if session.get('user'):
        session.pop('user')
        flash('Successfully logged out')
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))
    
@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset(token):
    try:
        serializer = URLSafeTimedSerializer(secret_key)
        email = serializer.loads(token, salt='f4db28e23409f84183ba442b7d607d6d', max_age=86400)
    except:
        abort(404, 'Link Expired')

    if request.method == 'POST':
        newpassword = request.form['npassword']
        confirmpassword = request.form['cpassword']
        print("Email:", email)
        print("New Password:", newpassword)
        print("Confirm Password:", confirmpassword)

        if newpassword == confirmpassword:
            cursor = mydb.cursor(buffered=True)
            cursor.execute('UPDATE users SET password=%s WHERE email=%s', [newpassword, email])

            # Check if any rows were affected (updated)
            row_count = cursor.rowcount
            cursor.close()
            print("Row Count:", row_count)
            mydb.commit()

            if row_count > 0:
                flash('Reset Successful')
                return redirect(url_for('login'))
            else:
                flash('No rows updated in the database.')
        else:
            flash('Passwords mismatched')
            return render_template('newpassword.html')

    return render_template('newpassword.html')

@app.route('/forget', methods=['GET', 'POST'])
def forget():
    if request.method == 'POST':
        email = request.form['email']
        cursor = mydb.cursor(buffered=True)
        cursor.execute('SELECT count(*) FROM users WHERE email = %s', [email])
        count = cursor.fetchone()[0]
        
        if count == 1:
            cursor.execute('SELECT email FROM users WHERE email = %s', [email])
            email_result = cursor.fetchone()[0]
            
            subject = 'Forget Password'
            confirm_link = url_for('reset', token=token(email, salt='f4db28e23409f84183ba442b7d607d6d'), _external=True)
            body = f"Use this link to reset your password:\n\n{confirm_link}"
            
            sendmail(to=email_result, body=body, subject=subject)
            flash('Reset link sent, check your email')
            cursor.close()
            return redirect(url_for('login'))
        else:
            flash('Invalid email id')
            cursor.close()
            return render_template('forgot.html')
    
    return render_template('forgot.html')


@app.route('/survey', methods=['GET','POST'])
def survey_start():
        
        if request.method == 'POST':
            name = request.form['name']
            rollno = request.form['rollno']
            email = request.form['email']
            dept = request.form['dept']
            specialization = request.form['specialization']
            one = request.form['one']
            two = request.form['two']
            three = request.form['three']
            four = request.form['four']
            five = request.form['five']
            six = request.form['six']
            seven = request.form['seven']
            eight = request.form['eight']
            nine = request.form['nine']
            ten = request.form['ten']
            eleven = request.form['eleven']
            twelve = request.form['twelve']
            thirteen = request.form['thirteen']
            fourteen = request.form['fourteen']
            fifteen = request.form['fifteen']
            sixteen = request.form['sixteen']
            seventeen = request.form['seventeen']
            eighteen = request.form['eighteen']
            nineteen = request.form['nineteen']        
            
            cursor = mydb.cursor(buffered=True)
            cursor.execute('INSERT INTO sur_data VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [name, rollno, email, dept, specialization, one, two, three, four, five, six, seven, eight, nine, ten, eleven, twelve, thirteen, fourteen, fifteen, sixteen, seventeen, eighteen, nineteen])
            mydb.commit()

            flash('Survey submitted successfully', 'success')
            return redirect(url_for('thank_you'))  # Redirect to thank-you page
        return render_template("survey.html")

def fetch_survey_data():
    try:
        cursor = mydb.cursor(dictionary=True)  # This cursor returns rows as dictionaries
        cursor.execute('SELECT * FROM sur_data')  # Replace with your actual SQL query

        # Fetch all rows of survey data
        survey_data = cursor.fetchall()

        return survey_data
    except Exception as e:
        print(f"Error fetching survey data: {e}")
        return None
    finally:
        cursor.close()

@app.route('/download_survey_data', methods=['GET'])
def download_survey_data():
    # Fetch survey data from the database
    survey_data = fetch_survey_data()

    if not survey_data:
        return "No survey data found."

    # Create a buffer to hold the CSV data
    buffer = io.StringIO()

    # Use the CSV module to write the survey data to the buffer
    csv_writer = csv.writer(buffer)
    header = ["name", "rollno", "email", "dept", "specialization", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
    csv_writer.writerow(header)
    for row in survey_data:
        csv_writer.writerow(row.values())

    # Set the appropriate headers for CSV download
    buffer.seek(0)
    return Response(
        buffer.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=survey_data.csv'}
    )

@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

  
if __name__=='__main__':
    app.run()
