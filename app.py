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

import flask_excel as excel

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
        body = f"Thanks for signing up\n\nfollow this link for further steps-{url_for('confirm', token=token(data), _external=True)}"
        
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
        data=serializer.loads(token,salt=salt,max_age=180)
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
@app.route('/survey',methods=['GET','POST']) 
def survey():
    if session.get('user'):
        return render_template('survey.html')
@app.route('/create', methods=['GET', 'POST'])
def create():
    if session.get('user'):
        if request.method == 'POST':
            time = int(request.form['time'])
            sid = tokgenotp()  # Using the tokgenotp() function to generate a random token
            url = url_for('survey_start', token=token(sid), _external=True)
            cursor = mysql.connection.cursor()
            cursor.execute('insert into survey(surveyid, url, rollno) values(%s, %s, %s)', [sid, url, session.get('user')])
            mysql.connection.commit()
            return redirect(url_for('dashboard'))
        return render_template('create.html')
    else:
        return redirect(url_for('login'))


@app.route('/survey/<token>',methods=['GET','POST'])
def survey_start(token):
    try:
        s=URLSafeTimedSerializer(app.config['SECRET_KEY'])
        survey_dict=s.loads(token)
        sid=survey_dict['sid']
        if request.method=='POST':
            
            
            name=request.form['name']
            rollno=request.form['rollno']
            email=request.form['email']
            dept=request.form['dept']
            specailization=request.form['specialization']
            one=request.form['one']
            two=request.form['two']
            three=request.form['three']
            four=request.form['four']
            five=request.form['five']
            six=request.form['six']
            seven=request.form['seven']
            eight=request.form['eight']
            nine=request.form['nine']
            ten=request.form['ten']
            eleven=request.form['eleven']
            twelve=request.form['twelve']
            thirteen=request.form['thirteen']
            fourteen=request.form['fourteen']
            fifteen=request.form['fifteen']
            sixteen=request.form['sixteen']
            seventeen=request.form['seventeen']
            eighteen=request.form['eighteen']
            nineteen=request.form['nineteen']        
            cursor=mysql.connection.cursor()
            cursor.execute('insert into sur_data values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',[sid,name,rollno,email,dept,specailization,one,two,three,four,five,six,seven,eight,nine,ten,eleven,twelve,thirteen,fourteen,fifteen,sixteen,seventeen,eighteen,nineteen])
            mysql.connection.commit()
            return 'Survey submitted successfully'
        return render_template("survey.html")
    except Exception as e:
        print(e)
        abort(410,description='Survey link expired')
        
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
            confirm_link = url_for('reset', token=token(email, salt=salt), _external=True)
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

@app.route('/feedbackform/<token>')
def feedbackform(token):
    return 'success'
    

@app.route('/preview')
def preview():
    if session.get('user'):
        return render_template('survey.html')
    else:
        return redirect(url_for('login'))       

@app.route('/allsurveys')
def allsurveys():
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('SELECT * FROM survey where rollno=%s',[session.get('user')])
        data=cursor.fetchall()
        return render_template('allsurveys.html',surveys=data)
    else:
        return redirect(url_for('login'))  

@app.route('/reset/<token>',methods=['GET','POST'])
def reset(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        email=serializer.loads(token,salt=salt,max_age=180)
    except:
        abort(404,'Link Expired')
    else:
        if request.method=='POST':
            newpassword=request.form['npassword']
            confirmpassword=request.form['cpassword']
            if newpassword==confirmpassword:
                cursor=mysql.connection.cursor()
                cursor.execute('update users set password=%s where email=%s',[newpassword,email])
                mysql.connection.commit()
                flash('Reset Successful')
                return redirect(url_for('login'))
            else:
                flash('Passwords mismatched')
                return render_template('newpassword.html')
        return render_template('newpassword.html')


@app.route('/download/<sid>')
def download(sid):
    cursor=mysql.connection.cursor()
    lst=['Name','Roll no','Email','dept','1.Considering your overall experience with our college rate your ratings?',
    '2.The professors are well-trained and deliver the syllabus efficiently?',
    '3.Are you satisfied with the teaching staff and their teaching methods?',
    '4.How satisfied are you with the facilities provided by the college?',
    '5.How satisfied are you with your admission process in college?',
    '6.What are your views on the cafeteria and its hygiene and food quality?',
    '7.How satisfied are you with your admission process in college?',
    '8.Were the faculty and support staff helpful enough when you needed them?',
    '9.What are your views on the extra-curricular activities carried out in this college?',
    '10.What are your views on the cafeteria and its hygiene and food quality?',
    '11.What are the views on the sports area?',
    '12.How Professors are reliable and helpful?',
    '13.Is This college has well equipped computer access facility?',
    '14.Is it easy to gain access to the resources through the college library?',
    '15.Do you think it is a good idea for your siblings or friends to pursue their career in this college?',
    '16.Do you think college pays enough attention to the racial and ethnic biases?',
    '17.Do you think the college responds accurately to bullying cases?',
    '18.What is your overall experience with the college?',
    '19.Please feel free to give your additional inputs on your experience with this college?']
    

    cursor.execute('SELECT * from sur_data where sid=%s',[sid])
    user_data=[list(i)[1:] for i in cursor.fetchall()]
    user_data.insert(0,lst)
    print(user_data)
    return excel.make_response_from_array(user_data, "xlsx",file_name="Faculty_data")

@app.route('/update_survey', methods=['POST'])
def update_survey():
    surveyid = request.form['surveyid']
    url = request.form['url']
    
    with mysql.connection.cursor() as cursor:
        cursor.execute('UPDATE survey SET url = %s WHERE surveyid = %s', (url, surveyid))
        mysql.connection.commit()
    
    # Redirect or return a response
    return redirect(url_for('some_route'))

@app.route('/delete_sur_data', methods=['POST'])
def delete_sur_data():
    sid = request.form['sid']
    
    with mysql.connection.cursor() as cursor:
        cursor.execute('DELETE FROM sur_data WHERE sid = %s', (sid,))
        mysql.connection.commit()
    
    # Redirect or return a response
    return redirect(url_for('some_route'))


if __name__=='__main__':
    app.run()