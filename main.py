from flask import Flask, render_template, request, redirect, url_for, session
import bcrypt
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import os, uuid
from werkzeug.utils import secure_filename
from datetime import date, timedelta, datetime

app = Flask(__name__)
app.secret_key='h+\xe1GZ]\x9egB\xcf\xf4\x88_z\x01>'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'property_management'

mysql = MySQL(app)

@app.route("/", methods=['GET', 'POST'])
def home():
    if 'loggedin' in session:
        return render_template('home.html', username=session['username'],
                               email1=session['email1'])
    return render_template('home.html',username="",email1="")

@app.route("/login/", methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if len(username) > 0 and len(password) > 0:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM accounts WHERE username = %s', (username, ))
            account = cursor.fetchone()
            mysql.connection.commit()
            cursor.close()
            if account and bcrypt.checkpw(password.encode('utf-8'), account['password'].encode('utf-8')):
                if username == 'admin':
                    session['loggedin'] = True
                    session['id'] = account['id']
                    session['username'] = account['username']
                    session['email1'] = account['email']
                    session['mobile'] = account['mobile']
                    return redirect(url_for('admindashboard'))
                else:
                    session['loggedin'] = True
                    session['id'] = account['id']
                    session['username'] = account['username']
                    session['email1'] = account['email']
                    session['mobile'] = account['mobile']
                    return redirect(url_for('dashboard'))
            else:
                msg = 'Incorrect username/password!'
        else:
            msg = ' Please fill the entries !'
    return render_template('login.html', msg=msg)


@app.route('/login/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('email1', None)
    session.pop('mobile', None)
    return redirect(url_for('login'))


@app.route("/register/", methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        fullname = request.form['fullname']
        password = request.form['password']
        email = request.form['email']
        mobile = request.form['mobile']
        cpassword = request.form['cpassword']
        if len(username) > 0 and len(password) > 0 and len(email) > 0 and len(mobile) > 0 and len(fullname) > 0 and len(
                cpassword) > 0:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM accounts WHERE username = % s', (username,))
            account = cursor.fetchone()
            cursor.execute('SELECT * FROM accounts WHERE email = % s', (email,))
            account1 = cursor.fetchone()
            cursor.execute('SELECT * FROM accounts WHERE mobile = % s', (mobile,))
            account2 = cursor.fetchone()
            if account:
                msg = 'Account already exists with this username!'
            elif account1:
                msg = 'Account already exists with this email !'
            elif account2:
                msg = 'Account already exists with this mobile number !'
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                msg = 'Invalid email address !'
            elif not re.match(r'[A-Za-z0-9]+', username):
                msg = 'Username must contain only characters and numbers !'
            elif not username or not password or not email or not mobile or not cpassword or not fullname:
                msg = 'Please fill out the form !'
            elif len(mobile) != 10:
                msg = 'Enter 10 digit number !'
            elif cpassword != password:
                msg = 'Confirm password does not match with password !'
            else:
                hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                cursor.execute('INSERT INTO accounts VALUES (NULL, % s, % s, % s,% s,% s,% s)',
                               (username, fullname, email, mobile, hashed, hashed,))
                mysql.connection.commit()
                cursor.close()
                msg = 'You have successfully registered !'
        else:
            msg = 'Please fill out the form !'

    return render_template('register.html', msg=msg)


@app.route("/admindashboard", methods=['GET', 'POST'])
def admindashboard():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts')
        count = cursor.fetchall()
        cursor.execute('SELECT * FROM apartmentdetail')
        counta = cursor.fetchall()
        cursor.execute('SELECT * FROM roomdetail')
        countr = cursor.fetchall()
        cursor.execute('SELECT * FROM projectdetail')
        countp = cursor.fetchall()
        mysql.connection.commit()
        cursor.close()
        return render_template('admindashboard.html', count=len(count)-1, counta= len(counta), countr= len(countr), countp= len(countp), username='admin', email1=session['email1'])
    return redirect(url_for('login'))


@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM book_meet_apt where A_ID in (select A_ID from apartmentdetail where id=%s)',
                       [session['id']])
        result = cursor.fetchall()
        r = list(result)
        cursor.execute(
            'SELECT A_ID, Aname FROM apartmentdetail where id= %s and A_ID in (select A_ID from book_meet_apt)',
            [session['id']])
        result1 = cursor.fetchall()
        r1 = list(result1)
        ans = []
        for i in r:
            for j in r1:
                if i['A_ID'] == j['A_ID']:
                    k = []
                    k.append(i['A_ID'])
                    k.append(i['id'])
                    k.append(i['Occupation'])
                    k.append(i['Slot'])
                    k.append(i['booking_date'])
                    k.append(j['Aname'])
                    cursor.execute('select fullname from accounts where id=%s', [i['id']])
                    result2 = cursor.fetchall()
                    r2 = list(result2)
                    k.append(r2[0]['fullname'])
                    ans.append(k)

        cursor.execute('SELECT * FROM accept_meet_apt where buyer_id =%s',
                       [session['id']])
        result9 = cursor.fetchall()
        r9 = list(result9)
        cursor.execute(
            'SELECT A_ID, Aname FROM apartmentdetail where A_ID in (select A_ID from accept_meet_apt where buyer_id=%s)',
            [session['id']])
        result8 = cursor.fetchall()
        r8 = list(result8)
        ans1 = []
        for i in r9:
            for j in r8:
                if i['A_ID'] == j['A_ID']:
                    k = []
                    k.append(i['Address'])
                    k.append(i['Landmark'])
                    k.append(i['City'])
                    k.append(i['Pincode'])
                    k.append(i['State'])
                    k.append(i['Country'])
                    k.append(i['booking_date'])
                    k.append(i['starttime'])
                    k.append(i['endtime'])
                    k.append(j['Aname'])
                    cursor.execute('select fullname, email, mobile from accounts where id=%s', [i['id']])
                    result2 = cursor.fetchall()
                    r2 = list(result2)
                    k.append(r2[0]['fullname'])
                    k.append(r2[0]['email'])
                    k.append(r2[0]['mobile'])
                    ans1.append(k)
        print(ans1)

        cursor.execute('SELECT * FROM book_meet_project where P_ID in (select P_ID from projectdetail where id=%s)',
                       [session['id']])
        resultp = cursor.fetchall()
        rp = list(resultp)
        cursor.execute(
            'SELECT P_ID, Pname, Flattype FROM projectdetail where id= %s and P_ID in (select P_ID from book_meet_project)',
            [session['id']])
        resultp1 = cursor.fetchall()
        rp1 = list(resultp1)
        ansp = []
        for i in rp:
            for j in rp1:
                if i['P_ID'] == j['P_ID']:
                    k = []
                    k.append(i['P_ID'])
                    k.append(i['id'])
                    k.append(i['Occupation'])
                    k.append(i['Slot'])
                    k.append(i['booking_date'])
                    k.append(j['Pname'])
                    cursor.execute('select fullname from accounts where id=%s', [i['id']])
                    result2 = cursor.fetchall()
                    r2 = list(result2)
                    k.append(r2[0]['fullname'])
                    k.append(j['Flattype'])
                    ansp.append(k)

        cursor.execute('SELECT * FROM accept_meet_project where buyer_id =%s',
                       [session['id']])
        resultp9 = cursor.fetchall()
        rp9 = list(resultp9)
        cursor.execute(
            'SELECT P_ID, Pname, Flattype FROM projectdetail where P_ID in (select P_ID from accept_meet_project where buyer_id=%s)',
            [session['id']])
        resultp8 = cursor.fetchall()
        rp8 = list(resultp8)
        ansp1 = []
        for i in rp9:
            for j in rp8:
                if i['P_ID'] == j['P_ID']:
                    k = []
                    k.append(i['Address'])
                    k.append(i['Landmark'])
                    k.append(i['City'])
                    k.append(i['Pincode'])
                    k.append(i['State'])
                    k.append(i['Country'])
                    k.append(i['booking_date'])
                    k.append(i['starttime'])
                    k.append(i['endtime'])
                    k.append(j['Pname'])
                    cursor.execute('select fullname, email, mobile from accounts where id=%s', [i['id']])
                    result2 = cursor.fetchall()
                    r2 = list(result2)
                    k.append(r2[0]['fullname'])
                    k.append(r2[0]['email'])
                    k.append(r2[0]['mobile'])
                    k.append(j['Flattype'])
                    ansp1.append(k)

        cursor.execute('SELECT * FROM book_meet_room where R_ID in (select R_ID from roomdetail where id=%s)',
                       [session['id']])
        resultr = cursor.fetchall()
        rr = list(resultr)
        cursor.execute(
            'SELECT R_ID, Bname, Room_no FROM roomdetail where id= %s and R_ID in (select R_ID from book_meet_room)',
            [session['id']])
        resultr1 = cursor.fetchall()
        rr1 = list(resultr1)
        ansr = []
        for i in rr:
            for j in rr1:
                if i['R_ID'] == j['R_ID']:
                    k = []
                    k.append(i['R_ID'])
                    k.append(i['id'])
                    k.append(i['Occupation'])
                    k.append(i['Slot'])
                    k.append(i['booking_date'])
                    k.append(j['Bname'])
                    cursor.execute('select fullname from accounts where id=%s', [i['id']])
                    result2 = cursor.fetchall()
                    r2 = list(result2)
                    k.append(r2[0]['fullname'])
                    k.append(j['Room_no'])
                    ansr.append(k)

        cursor.execute('SELECT * FROM accept_meet_room where buyer_id =%s',
                       [session['id']])
        resultr9 = cursor.fetchall()
        rr9 = list(resultr9)
        cursor.execute(
            'SELECT R_ID, Bname , Room_no FROM roomdetail where R_ID in (select R_ID from accept_meet_room where buyer_id=%s)',
            [session['id']])
        resultr8 = cursor.fetchall()
        rr8 = list(resultr8)
        ansr1 = []
        for i in rr9:
            for j in rr8:
                if i['R_ID'] == j['R_ID']:
                    k = []
                    k.append(i['Address'])
                    k.append(i['Landmark'])
                    k.append(i['City'])
                    k.append(i['Pincode'])
                    k.append(i['State'])
                    k.append(i['Country'])
                    k.append(i['booking_date'])
                    k.append(i['starttime'])
                    k.append(i['endtime'])
                    k.append(j['Bname'])
                    cursor.execute('select fullname, email, mobile from accounts where id=%s', [i['id']])
                    result2 = cursor.fetchall()
                    r2 = list(result2)
                    k.append(r2[0]['fullname'])
                    k.append(r2[0]['email'])
                    k.append(r2[0]['mobile'])
                    k.append(j['Room_no'])
                    ansr1.append(k)

        cursor.close()
        return render_template('userdashboard.html', ans=ans, ans1=ans1, ansp=ansp, ansp1=ansp1, ansr=ansr, ansr1=ansr1, username=session['username'],
                               email1=session['email1'])
    return redirect(url_for('login'))


@app.route("/apmt_reg/", methods=['GET', 'POST'])
def apmt_reg():
    msg = ''
    if request.method == 'POST':
        # fetch data
        details = request.form
        apmtname = details['name']
        plot_no = details['Plot']
        area = details['Area']
        address = details['Address']
        landmark = details['Landmark']
        city = details['City']
        pin = details['Pincode']
        state = details['State']
        country = details['Country']
        atype = details['Atype']
        rs = details['Rent/Sale']
        availability = details['Availability']
        Price = details['Price']
        facilities = details['Facilities']
        description = details['Description']
        file = request.files['file']
        filename = secure_filename(file.filename)
        extension = os.path.splitext(filename)
        allowed_extensions = {'.jpg', '.png', '.jpeg'}
        if extension[1] in allowed_extensions:
            f_name = str(uuid.uuid4()) + str(extension[1])
            app.config['UPLOAD_FOLDER'] = 'static/Uploads'
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], f_name))
            if len(apmtname) > 0 and len(plot_no) > 0 and len(address) > 0 and len(landmark) > 0 and len(availability) and len(
                city) > 0 and len(pin) > 0 and len(state) > 0 and len(country) > 0 and len(rs)>0 and len(
                atype) > 0 and len(area)>0 and len(facilities) > 0 and len(description) > 0 and len(Price)>0:

                if len(pin) != 6:
                    msg = 'Enter 6 digit Pincode !'
                elif not apmtname or not plot_no or not area or not address or not landmark or not city or not pin or not state or not country or not atype or not rs or not availability or not Price or not facilities or not description or not file:
                    msg = 'Please fill out the form !'
                else:
                    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    cursor.execute(
                        "INSERT INTO apartmentdetail VALUES(NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (
                            session['id'] , apmtname, plot_no, area, address, landmark, city, pin, state, country, atype, rs, availability,
                            Price, facilities, description, f_name,'0'))
                    mysql.connection.commit()
                    cursor.close()
                    msg = 'Registration Successful! Thank You !'
            else:
                msg = 'Please fill out the form !'
        else:
            msg = 'Upload image in jpg/png/jpeg format only!'
    if 'loggedin' in session:
        return render_template('Apmt_reg.html', msg=msg, username=session['username'], email1=session['email1'])
    else:
        return redirect(url_for('login'))


@app.route("/roomreg/", methods=['GET', 'POST'])
def roomreg():
    msg = ''
    if request.method == 'POST':
        # fetch data
        details = request.form
        bname = details['name']
        room_no = details['room']
        area = details['Area']
        address = details['Address']
        landmark = details['Landmark']
        city = details['City']
        pin = details['Pincode']
        state = details['State']
        country = details['Country']
        availability = details['Availability']
        Rent = details['Price']
        facilities = details['Facilities']
        description = details['Description']
        file = request.files['file']
        filename = secure_filename(file.filename)
        extension = os.path.splitext(filename)
        allowed_extensions = {'.jpg', '.png', '.jpeg'}
        if extension[1] in allowed_extensions:
            f_name = str(uuid.uuid4()) + str(extension[1])
            app.config['UPLOAD_FOLDER'] = 'static/Uploads'
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], f_name))
            if len(bname) > 0 and len(room_no) > 0 and len(area) and len(address) > 0 and len(landmark) > 0 and len(
                city) > 0 and len(pin) > 0 and len(state) > 0 and len(country) > 0 and len(availability) and len(
                Rent)>0 and len(facilities) > 0 and len(description) > 0:

                if len(pin) != 6:
                    msg = 'Enter 6 digit Pincode !'
                elif not bname or not room_no or not area or not address or not landmark or not city or not pin or not state or not country or not availability or not Rent or not facilities or not description or not file:
                    msg = 'Please fill out the form !'
                else:
                    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    cursor.execute(
                        "INSERT INTO roomdetail VALUES(NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (
                            session['id'], bname, room_no, area, address, landmark, city, pin, state, country, availability,
                            Rent, facilities, description, f_name,'0'))
                    mysql.connection.commit()
                    cursor.close()
                    msg = 'Registration Successful! Thank You !'
            else:
                msg = 'Please fill out the form !'
        else:
            msg = 'Upload image in jpg/png/jpeg format only!'
    if 'loggedin' in session:
        return render_template('roomreg.html', msg=msg, username=session['username'], email1=session['email1'])
    else:
        return redirect(url_for('login'))



@app.route("/projectreg/", methods=['GET', 'POST'])
def projectreg():
    msg = ''
    if request.method == 'POST':
        # fetch data
        details = request.form
        pname = details['name']
        flat = details.getlist('flattype')
        print(flat)
        flattype = ', '.join(flat)
        address = details['Address']
        city = details['City']
        pin = details['Pincode']
        state = details['State']
        country = details['Country']
        facility = details.getlist('Facilities')
        facilities = ', '.join(facility)
        feature = details.getlist('features')
        features = ', '.join(feature)
        availability = details['Availability']
        description = details['Description']
        file = request.files['file']
        filename = secure_filename(file.filename)
        extension = os.path.splitext(filename)
        allowed_extensions = {'.jpg', '.png', '.jpeg'}
        if extension[1] in allowed_extensions:
            f_name = str(uuid.uuid4()) + str(extension[1])
            app.config['UPLOAD_FOLDER'] = 'static/Uploads'
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], f_name))
            if len(pname) > 0 and len(flattype) > 0 and len(address) > 0 and len(features) > 0 and len(
                city) > 0 and len(pin) > 0 and len(state) > 0 and len(country) > 0 and len(
                availability) > 0 and len(facilities) > 0 and len(description) > 0:

                if len(pin) != 6:
                    msg = 'Enter 6 digit Pincode !'
                elif not pname or not flattype or not features or not address or not city or not pin or not state or not country or not availability or not facilities or not description or not file:
                    msg = 'Please fill out the form !'
                else:
                    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    cursor.execute(
                        "INSERT INTO projectdetail VALUES(NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (
                            session['id'], pname, flattype, address, features, city, pin, state, country, availability,
                            facilities, description, f_name,'0'))
                    mysql.connection.commit()
                    cursor.close()
                    msg = 'Registration Successful! Thank You !'
            else:
                msg = 'Please fill out the form !'
        else:
            msg = 'Upload image in jpg/png/jpeg format only!'
    if 'loggedin' in session:
        return render_template('projectreg.html', msg=msg, username=session['username'], email1=session['email1'])
    else:
        return redirect(url_for('login'))




@app.route("/registeredusers/")
def registeredusers():
    if 'loggedin' in session:
        if session['username']=='admin':
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM accounts where username <> 'admin' ")
            userDetails = cur.fetchall()
            mysql.connection.commit()
            cur.close()
            return render_template('registeredusers.html', userDetails=userDetails, username=session['username'],
                                   email1=session['email1'])
        else:
            return render_template('home.html')
    else:
        return render_template('login.html')

@app.route("/deleteuser/<string:id>")
def deleteuser(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM accounts where ID=%s", [id, ])
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('registeredusers'))

@app.route("/search/", methods=['GET', 'POST'])
def search():
    op = ""
    result=[]
    result1=[]
    result2=[]
    if request.method == 'POST':
        loc = request.form['location']
        city = request.form['city']
        option = request.form.get('opt')
        minprice = request.form['minprice']
        maxprice = request.form['maxprice']
        area = request.form['area']
        atype= request.form.get('atypeo')
        flattype = request.form.getlist('flattype')
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if option == "choose" :
            op="n"
            #apartments
            if loc == "" and city == "" :
                cur.execute(
                    'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id')
                result = cur.fetchall()
            elif loc != "":
                if city == "" :
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s',
                        [loc])
                    result = cur.fetchall()
                elif city != "" :
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and City = %s',
                        ([loc], [city]))
                    result = cur.fetchall()
            elif city != "" and loc == "":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where City = % s',
                        [city])
                    result = cur.fetchall()

            #rooms
            
            if loc == "" and city == "" :
                cur.execute(
                    'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id')
                result1 = cur.fetchall()
            elif loc != "":
                if city == "" :
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where State = % s',
                        [loc])
                    result1 = cur.fetchall()
                elif city != "" :
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where State = % s and City = %s',
                        ([loc], [city]))
                    result1 = cur.fetchall()
            elif city != "" and loc == "":
                if minprice == "" and maxprice == "":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where City = % s',
                        [city])
                    result1 = cur.fetchall()

            #projects
            if loc == "" and city == "":
                cur.execute(
                    'SELECT P_ID,username,Pname,Flattype,Features,Address,City,Pincode,State,Country,Availability,Facilities,Descr,image,rating FROM projectdetail INNER JOIN accounts on projectdetail.id=accounts.id')
                result2 = cur.fetchall()
            elif loc != "":
                if city == "":
                    cur.execute(
                        'SELECT P_ID,username,Pname,Flattype,Features,Address,City,Pincode,State,Country,Availability,Facilities,Descr,image,rating FROM projectdetail INNER JOIN accounts on projectdetail.id=accounts.id where State = % s',
                        [loc])
                    result2 = cur.fetchall()
                elif city != "":
                    cur.execute(
                        'SELECT P_ID,username,Pname,Flattype,Features,Address,City,Pincode,State,Country,Availability,Facilities,Descr,image,rating FROM projectdetail INNER JOIN accounts on projectdetail.id=accounts.id where State = % s and City = %s',
                        ([loc], [city]))
                    result2 = cur.fetchall()
            elif city != "" and loc == "" :
                cur.execute(
                    'SELECT P_ID,username,Pname,Flattype,Features,Address,City,Pincode,State,Country,Availability,Facilities,Descr,image,rating FROM projectdetail INNER JOIN accounts on projectdetail.id=accounts.id where City = % s',
                    [city])
                result2 = cur.fetchall()


        if option == "apartments":
            op = "a"
            if loc == "" and city == "" and minprice == "" and maxprice == "" and area== "" and atype=="" :
                cur.execute(
                    'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id')
                result = cur.fetchall()
                print(1)
            elif loc == "" and city == "" and minprice == "" and maxprice == "" and area!= "" and atype=="" :
                cur.execute(
                    'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where Area=%s',[area])
                result = cur.fetchall()
            elif loc == "" and city == "" and minprice == "" and maxprice == "" and area== "" and atype!="" :
                cur.execute(
                    'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where Atype=%s',[atype])
                result = cur.fetchall()
            elif loc == "" and city == "" and minprice == "" and maxprice == "" and area!= "" and atype!="" :
                cur.execute(
                    'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where Area=%s and Atype=%s',([area], [atype]))
                result = cur.fetchall()

            elif loc != "":
                if city == "" and minprice == "" and maxprice == "" and area=="" and atype=="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s',
                        [loc])
                    result = cur.fetchall()
                elif city == "" and minprice == "" and maxprice == "" and area!="" and atype=="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and Area=%s',
                        ([loc],[area]))
                    result = cur.fetchall()
                elif city == "" and minprice == "" and maxprice == "" and area=="" and atype!="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and Atype=%s',
                        ([loc],[atype]))
                    result = cur.fetchall()
                elif city == "" and minprice == "" and maxprice == "" and area!="" and atype!="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and Atype=%s and Area=%s',
                        ([loc],[atype],[area]))
                    result = cur.fetchall()

                elif city != "" and minprice == "" and maxprice == "" and area=="" and atype=="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and City = %s',
                        ([loc], [city]))
                    result = cur.fetchall()
                elif city != "" and minprice == "" and maxprice == "" and area!="" and atype=="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and City = %s and Area=%s',
                        ([loc], [city], [area]))
                    result = cur.fetchall()
                elif city != "" and minprice == "" and maxprice == "" and area=="" and atype!="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and City = %s and Atype=%s',
                        ([loc], [city], [atype]))
                    result = cur.fetchall()
                elif city != "" and minprice == "" and maxprice == "" and area!="" and atype!="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and City = %s and Atype=%s and Area=%s' ,
                        ([loc], [city], [atype], [area]))
                    result = cur.fetchall()


                elif city != "" and minprice != "" and maxprice == "" and area=="" and atype=="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and City = %s and Price>=%s',
                        ([loc], [city], [minprice]))
                    result = cur.fetchall()
                elif city != "" and minprice != "" and maxprice == "" and area!="" and atype=="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and City = %s and Price>=%s and Area=%s',
                        ([loc], [city], [minprice],[area]))
                    result = cur.fetchall()
                elif city != "" and minprice != "" and maxprice == "" and area!="" and atype!="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and City = %s and Price>=%s and Area=%s and Atype=%s',
                        ([loc], [city], [minprice],[area],[atype]))
                    result = cur.fetchall()
                elif city != "" and minprice != "" and maxprice == "" and area=="" and atype!="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and City = %s and Price>=%s and Atype=%s',
                        ([loc], [city], [minprice],[atype]))
                    result = cur.fetchall()


                elif city != "" and minprice == "" and maxprice != "" and area=="" and atype=="":
                    cur.execute(
                        'A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and City = %s and Price<=%s',
                        ([loc], [city], [maxprice]))
                    result = cur.fetchall()
                elif city != "" and minprice == "" and maxprice != "" and area!="" and atype=="":
                    cur.execute(
                        'A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and City = %s and Price<=%s and Area=%s',
                        ([loc], [city], [maxprice],[area]))
                    result = cur.fetchall()
                elif city != "" and minprice == "" and maxprice != "" and area=="" and atype!="":
                    cur.execute(
                        'A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and City = %s and Price<=%s and atype=%s',
                        ([loc], [city], [maxprice],[atype]))
                    result = cur.fetchall()
                elif city != "" and minprice == "" and maxprice != "" and area!="" and atype!="":
                    cur.execute(
                        'A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and City = %s and Price<=%s and Area=%s and Atype=%s',
                        ([loc], [city], [maxprice],[area],[atype]))
                    result = cur.fetchall()


                elif city == "" and minprice == "" and maxprice != "" and area=="" and atype=="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and Price<=%s',
                        ([loc], [maxprice]))
                    result = cur.fetchall()
                elif city == "" and minprice == "" and maxprice != "" and area!="" and atype=="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and Price<=%s and Area=%s',
                        ([loc], [maxprice],[area]))
                    result = cur.fetchall()
                elif city == "" and minprice == "" and maxprice != "" and area=="" and atype!="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and Price<=%s and Atype=%s',
                        ([loc], [maxprice],[atype]))
                    result = cur.fetchall()
                elif city == "" and minprice == "" and maxprice != "" and area!="" and atype!="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and Price<=%s and Area=%s and Atype=%s',
                        ([loc], [maxprice],[area],[atype]))
                    result = cur.fetchall()


                elif city == "" and minprice != "" and maxprice == "" and area=="" and atype=="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and Price<=%s',
                        ([loc], [maxprice]))
                    result = cur.fetchall()
                elif city == "" and minprice != "" and maxprice == "" and area!="" and atype=="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and Price<=%s and Area=%s',
                        ([loc], [maxprice],[area]))
                    result = cur.fetchall()
                elif city == "" and minprice != "" and maxprice == "" and area=="" and atype!="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and Price<=%s and Atype="%s',
                        ([loc], [maxprice],[atype]))
                    result = cur.fetchall()
                elif city == "" and minprice != "" and maxprice == "" and area!="" and atype!="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and Price<=%s ans Area=%s and Atype=%s',
                        ([loc], [maxprice],[area],[atype]))
                    result = cur.fetchall()


                elif city == "" and minprice != "" and maxprice != "" and area=="" and atype=="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and Price>=%s and Price<=%s',
                        ([loc], [minprice], [maxprice]))
                    result = cur.fetchall()
                elif city == "" and minprice != "" and maxprice != "" and area!="" and atype=="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and Price>=%s and Price<=%s and Area=%s',
                        ([loc], [minprice], [maxprice],[area]))
                    result = cur.fetchall()
                elif city == "" and minprice != "" and maxprice != "" and area=="" and atype!="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and Price>=%s and Price<=%s and Atype=%s',
                        ([loc], [minprice], [maxprice],[atype]))
                    result = cur.fetchall()
                elif city == "" and minprice != "" and maxprice != "" and area!="" and atype!="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and Price>=%s and Price<=%s and Area=%s and Atype=%s',
                        ([loc], [minprice], [maxprice],[area],[atype]))
                    result = cur.fetchall()


                elif city != "" and minprice != "" and maxprice != "" and area=="" and atype=="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and City=%s and Price>=%s and Price<=%s',
                        ([loc], [city], [minprice], [maxprice]))
                    result = cur.fetchall()
                elif city != "" and minprice != "" and maxprice != "" and area != "" and atype == "":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and City=%s and Price>=%s and Price<=%s and Area=%s',
                        ([loc], [city], [minprice], [maxprice],[area]))
                    result = cur.fetchall()
                elif city != "" and minprice != "" and maxprice != "" and area=="" and atype!="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and City=%s and Price>=%s and Price<=%s and Atype=%s',
                        ([loc], [city], [minprice], [maxprice],[atype]))
                    result = cur.fetchall()
                elif city != "" and minprice != "" and maxprice != "" and area!="" and atype!="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where State = % s and City=%s and Price>=%s and Price<=%s and Area=%s and Atype=%s',
                        ([loc], [city], [minprice], [maxprice],[area],[atype]))
                    result = cur.fetchall()


            elif city != "" and loc == "":
                if minprice == "" and maxprice == "" and area=="" and atype=="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where City = % s',
                        [city])
                    result = cur.fetchall()
                elif minprice == "" and maxprice == "" and area!="" and atype=="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where City = % s and Area=%s',
                        ([city],[area]))
                    result = cur.fetchall()
                elif minprice == "" and maxprice == "" and area=="" and atype!="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where City = % s and Atype=%s',
                        ([city],[atype]))
                    result = cur.fetchall()
                elif minprice == "" and maxprice == "" and area!="" and atype!="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where City = % s and Area=%s and Atype=%s',
                        ([city],[area],[atype]))
                    result = cur.fetchall()


                elif minprice == "" and maxprice != "" and area=="" and atype=="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where City = % s and Price<=%s',
                        ([city], [maxprice]))
                    result = cur.fetchall()
                elif minprice == "" and maxprice != "" and area!="" and atype=="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where City = % s and Price<=%s and Area=%s',
                        ([city], [maxprice],[area]))
                    result = cur.fetchall()
                elif minprice == "" and maxprice != "" and area=="" and atype!="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where City = % s and Price<=%s and Atype=%s',
                        ([city], [maxprice],[atype]))
                    result = cur.fetchall()
                elif minprice == "" and maxprice != "" and area!="" and atype!="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where City = % s and Price<=%s and Area=%s and Atype=%s',
                        ([city], [maxprice],[area],[atype]))
                    result = cur.fetchall()


                elif minprice != "" and maxprice == "" and area=="" and atype=="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where City = % s and Price<=%s',
                        ([city], [maxprice]))
                    result = cur.fetchall()
                elif minprice != "" and maxprice == "" and area!="" and atype=="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where City = % s and Price<=%s and Area=%s',
                        ([city], [maxprice],[area]))
                    result = cur.fetchall()
                elif minprice != "" and maxprice == "" and area=="" and atype!="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where City = % s and Price<=%s and Atype=%s',
                        ([city], [maxprice],[atype]))
                    result = cur.fetchall()
                elif minprice != "" and maxprice == "" and area!="" and atype!="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where City = % s and Price<=%s and Area=%s andAtype=%s',
                        ([city], [maxprice],[area],[atype]))
                    result = cur.fetchall()


                elif minprice != "" and maxprice != "" and area=="" and atype=="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where City = % s and Price>=%s and Price<=%s',
                        ([city], [minprice], [maxprice]))
                    result = cur.fetchall()
                elif minprice != "" and maxprice != "" and area!="" and atype=="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where City = % s and Price>=%s and Price<=%s and Area=%s',
                        ([city], [minprice], [maxprice],[area]))
                    result = cur.fetchall()
                elif minprice != "" and maxprice != "" and area=="" and atype!="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where City = % s and Price>=%s and Price<=%s and Atype=%s',
                        ([city], [minprice], [maxprice],[atype]))
                    result = cur.fetchall()
                elif minprice != "" and maxprice != "" and area!="" and atype!="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where City = % s and Price>=%s and Price<=%s and Area=%s and Atype=%s',
                        ([city], [minprice], [maxprice],[area],[atype]))
                    result = cur.fetchall()


            elif city == "" and loc == "":
                if minprice == "" and maxprice != "" and area=="" and atype=="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where Price<=%s',
                        ([maxprice]))
                    result = cur.fetchall()
                elif minprice == "" and maxprice != "" and area!="" and atype=="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where Price<=%s and Area=%s',
                        ([maxprice],[area]))
                    result = cur.fetchall()
                elif minprice == "" and maxprice != "" and area=="" and atype!="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where Price<=%s and Atype=%s',
                        ([maxprice],[atype]))
                    result = cur.fetchall()
                elif minprice == "" and maxprice != "" and area!="" and atype!="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where Price<=%s and Area=%s and Atype=%s',
                        ([maxprice],[area],[atype]))
                    result = cur.fetchall()


                elif minprice != "" and maxprice == "" and area=="" and atype=="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where Price>=%s',
                        ([minprice]))
                    result = cur.fetchall()
                elif minprice != "" and maxprice == "" and area!="" and atype=="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where Price>=%s and Area=%s',
                        ([minprice],[area]))
                    result = cur.fetchall()
                elif minprice != "" and maxprice == "" and area=="" and atype!="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where Price>=%s and Atype=%s',
                        ([minprice],[atype]))
                    result = cur.fetchall()
                elif minprice != "" and maxprice == "" and area!="" and atype!="":
                    cur.execute(
                        'SELECT A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where Price>=%s and Area=%s and Atype=%s',
                        ([minprice],[area],[atype]))
                    result = cur.fetchall()


                elif minprice != "" and maxprice != "" and area=="" and atype=="":
                    cur.execute(
                        'A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where Price>=%s and Price<=%s',
                        ([minprice], [maxprice]))
                    result = cur.fetchall()
                elif minprice != "" and maxprice != "" and area!="" and atype=="":
                    cur.execute(
                        'A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where Price>=%s and Price<=%s and Area=%s',
                        ([minprice], [maxprice],[area]))
                    result = cur.fetchall()
                elif minprice != "" and maxprice != "" and area=="" and atype!="":
                    cur.execute(
                        'A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where Price>=%s and Price<=%s and Atype=%s',
                        ([minprice], [maxprice],[atype]))
                    result = cur.fetchall()
                elif minprice != "" and maxprice != "" and area!="" and atype!="":
                    cur.execute(
                        'A_ID,username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where Price>=%s and Price<=%s and Area=%s and Atype=%s',
                        ([minprice], [maxprice],[area],[atype]))
                    result = cur.fetchall()


        elif option == "rooms":
            op = "r"
            if loc == "" and city == "" and minprice == "" and maxprice == "" and area=="":
                cur.execute(
                    'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id')
                result1 = cur.fetchall()
            elif loc == "" and city == "" and minprice == "" and maxprice == "" and area!="":
                cur.execute(
                    'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where Area=%s',([area]))
                result1 = cur.fetchall()

            elif loc != "":
                if city == "" and minprice == "" and maxprice == "" and area=="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where State = % s',
                        [loc])
                    result1 = cur.fetchall()
                elif city == "" and minprice == "" and maxprice == "" and area!="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where State = % s and Area=%s',
                        ([loc],[area]))
                    result1 = cur.fetchall()

                elif city != "" and minprice == "" and maxprice == "" and area=="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where State = % s and City = %s',
                        ([loc], [city]))
                    result1 = cur.fetchall()
                elif city != "" and minprice == "" and maxprice == "" and area!="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where State = % s and City = %s and Area=%s',
                        ([loc], [city],[area]))
                    result1 = cur.fetchall()

                elif city != "" and minprice != "" and maxprice == "" and area=="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where State = % s and City = %s and Rent>=%s',
                        ([loc], [city], [minprice]))
                    result1 = cur.fetchall()
                elif city != "" and minprice != "" and maxprice == "" and area!="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where State = % s and City = %s and Rent>=%s and Area=%s',
                        ([loc], [city], [minprice],[area]))
                    result1 = cur.fetchall()

                elif city != "" and minprice == "" and maxprice != "" and area=="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where State = % s and City = %s and Rent<=%s',
                        ([loc], [city], [maxprice]))
                    result1 = cur.fetchall()
                elif city != "" and minprice == "" and maxprice != "" and area!="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where State = % s and City = %s and Rent<=%s and Area=%s',
                        ([loc], [city], [maxprice],[area]))
                    result1 = cur.fetchall()

                elif city == "" and minprice == "" and maxprice != "" and area=="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where State = % s and Rent<=%s',
                        ([loc], [maxprice]))
                    result1 = cur.fetchall()
                elif city == "" and minprice == "" and maxprice != "" and area!="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where State = % s and Rent<=%s and Area=%s',
                        ([loc], [maxprice],[area]))
                    result1 = cur.fetchall()

                elif city == "" and minprice != "" and maxprice == "" and area=="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where State = % s and Rent<=%s',
                        ([loc], [maxprice]))
                    result1 = cur.fetchall()
                elif city == "" and minprice != "" and maxprice == "" and area!="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where State = % s and Rent<=%s and Area=%s',
                        ([loc], [maxprice],[area]))
                    result1 = cur.fetchall()

                elif city == "" and minprice != "" and maxprice != "" and area=="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where State = % s and Rent>=%s and Rent<=%s',
                        ([loc], [minprice], [maxprice]))
                    result1 = cur.fetchall()
                elif city == "" and minprice != "" and maxprice != "" and area!="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where State = % s and Rent>=%s and Rent<=%s and Area=%s',
                        ([loc], [minprice], [maxprice],[area]))
                    result1 = cur.fetchall()

                elif city != "" and minprice != "" and maxprice != "" and area=="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where State = % s and City=%s and Rent>=%s and Rent<=%s',
                        ([loc], [city], [minprice], [maxprice]))
                    result1 = cur.fetchall()
                elif city != "" and minprice != "" and maxprice != "" and area!="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where State = % s and City=%s and Rent>=%s and Rent<=%s and Area=%s',
                        ([loc], [city], [minprice], [maxprice],[area]))
                    result1 = cur.fetchall()

            elif city != "" and loc == "":
                if minprice == "" and maxprice == "" and area=="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where City = % s',
                        [city])
                    result1 = cur.fetchall()
                elif minprice == "" and maxprice == "" and area!="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where City = % s and Area=%s',
                        ([city],[area]))
                    result1 = cur.fetchall()

                elif minprice == "" and maxprice != "" and area=="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where City = % s and Rent<=%s',
                        ([city], [maxprice]))
                    result1 = cur.fetchall()
                elif minprice == "" and maxprice != "" and area!="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where City = % s and Rent<=%s and Area=%s',
                        ([city], [maxprice],[area]))
                    result1 = cur.fetchall()

                elif minprice != "" and maxprice == "" and area=="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where City = % s and Rent<=%s',
                        ([city], [maxprice]))
                    result1 = cur.fetchall()
                elif minprice != "" and maxprice == "" and area!="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where City = % s and Rent<=%s and Area=%s',
                        ([city], [maxprice],[area]))
                    result1 = cur.fetchall()

                elif minprice != "" and maxprice != "" and area=="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where City = % s and Rent>=%s and Price<=%s',
                        ([city], [minprice], [maxprice]))
                    result1 = cur.fetchall()
                elif minprice != "" and maxprice != "" and area!="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where City = % s and Rent>=%s and Price<=%s and Area=%s',
                        ([city], [minprice], [maxprice],[area]))
                    result1 = cur.fetchall()

            elif city == "" and loc == "":
                if minprice == "" and maxprice != "" and area=="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where Rent<=%s',
                        ([maxprice]))
                    result1 = cur.fetchall()
                elif minprice == "" and maxprice != "" and area!="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where Rent<=%s and Area=%s',
                        ([maxprice],[area]))
                    result1 = cur.fetchall()

                elif minprice != "" and maxprice == "" and area=="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where Rent>=%s',
                        ([minprice]))
                    result1 = cur.fetchall()
                elif minprice != "" and maxprice == "" and area!="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where Rent>=%s and Area=%s',
                        ([minprice],[area]))
                    result1 = cur.fetchall()

                elif minprice != "" and maxprice != "" and area=="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where Rent>=%s and Rent<=%s',
                        ([minprice], [maxprice]))
                    result1 = cur.fetchall()
                elif minprice != "" and maxprice != "" and area!="":
                    cur.execute(
                        'SELECT R_ID,username,Bname,Room_no,Area,Address,Landmark,City,Pincode,State,Country,Availability,Facilities,Descr,image,Rent,rating FROM roomdetail INNER JOIN accounts on roomdetail.id=accounts.id where Rent>=%s and Rent<=%s and Area=%s',
                        ([minprice], [maxprice],[area]))
                    result1 = cur.fetchall()


        elif option=='projects':
            if loc == "" and city == "" and (not flattype):
                cur.execute(
                    'SELECT P_ID,username,Pname,Flattype,Features,Address,City,Pincode,State,Country,Availability,Facilities,Descr,image,rating FROM projectdetail INNER JOIN accounts on projectdetail.id=accounts.id')
                result2 = cur.fetchall()
            elif loc == "" and city == "" and flattype:
                cur.execute(
                    'SELECT P_ID,username,Pname,Flattype,Features,Address,City,Pincode,State,Country,Availability,Facilities,Descr,image,rating FROM projectdetail INNER JOIN accounts on projectdetail.id=accounts.id',)
                r = cur.fetchall()
                for i in r:
                    l=i['Flattype'].split(', ')
                    for j in l:
                        if j in flattype:
                            result2.append(i)
                            break
            elif loc != "":
                if city == "" and (not flattype) :
                    cur.execute(
                        'SELECT P_ID,username,Pname,Flattype,Features,Address,City,Pincode,State,Country,Availability,Facilities,Descr,image,rating FROM projectdetail INNER JOIN accounts on projectdetail.id=accounts.id where State = % s',
                        [loc])
                    result2 = cur.fetchall()
                elif city == "" and flattype:
                    cur.execute(
                        'SELECT P_ID,username,Pname,Flattype,Features,Address,City,Pincode,State,Country,Availability,Facilities,Descr,image,rating FROM projectdetail INNER JOIN accounts on projectdetail.id=accounts.id where State = % s',
                        [loc])
                    r = cur.fetchall()
                    for i in r:
                        l = i['Flattype'].split(', ')
                        for j in l:
                            if j in flattype:
                                result2.append(i)
                                break
                elif city != "" and (not flattype):
                    cur.execute(
                        'SELECT P_ID,username,Pname,Flattype,Features,Address,City,Pincode,State,Country,Availability,Facilities,Descr,image,rating FROM projectdetail INNER JOIN accounts on projectdetail.id=accounts.id where State = % s and City = %s',
                        ([loc], [city]))
                    result2 = cur.fetchall()
                elif city != "" and flattype:
                    cur.execute(
                        'SELECT P_ID,username,Pname,Flattype,Features,Address,City,Pincode,State,Country,Availability,Facilities,Descr,image,rating FROM projectdetail INNER JOIN accounts on projectdetail.id=accounts.id where State = % s and City = %s',
                        ([loc], [city]))
                    r = cur.fetchall()
                    for i in r:
                        l = i['Flattype'].split(', ')
                        for j in l:
                            if j in flattype:
                                result2.append(i)
                                break
            elif city != "" and loc == "" and (not flattype):
                    cur.execute(
                        'SELECT P_ID,username,Pname,Flattype,Features,Address,City,Pincode,State,Country,Availability,Facilities,Descr,image,rating FROM projectdetail INNER JOIN accounts on projectdetail.id=accounts.id where City = % s',
                        [city])
                    result2 = cur.fetchall()
            elif city != "" and loc == "" and flattype:
                cur.execute(
                    'SELECT P_ID,username,Pname,Flattype,Features,Address,City,Pincode,State,Country,Availability,Facilities,Descr,image,rating FROM projectdetail INNER JOIN accounts on projectdetail.id=accounts.id where City = % s',
                    [city])
                r = cur.fetchall()
                for i in r:
                    l = i['Flattype'].split(', ')
                    for j in l:
                        if j in flattype:
                            result2.append(i)
                            break
        mysql.connection.commit()
        cur.close()
        if result or result1 or result2:
            if 'loggedin' in session:
                return render_template('search.html', detail=result,detail1=result1,detail2=result2, msg="Result for the search", op=op,
                                       username=session['username'],email1=session['email1'])
            else:
                return render_template('search.html', detail=result,detail1=result1,detail2=result2, msg="Result for the search", op=op, username="",email1="")
        else:
            if 'loggedin' in session:
                return render_template('search.html', msg="No records found", username=session['username'],email1=session['email1'])
            else:
                return render_template('search.html', msg="No records found", username="",email1="")
    else:
        if 'loggedin' in session:
            return render_template('search.html', username=session['username'],email1=session['email1'])
        else:
            return render_template('search.html', username="",email1="")
    return render_template('search.html')


@app.route("/ownerapartments/")
def ownerapartments():
    msg = ''
    if 'loggedin' in session:
        cur = mysql.connection.cursor()
        resultValue = cur.execute("SELECT * FROM apartmentdetail where id = %s", (session['id'],))
        print(resultValue)
        if resultValue > 0:
            apartDetails = cur.fetchall()
            return render_template('ownerapartments.html', msg=msg, apartDetails=apartDetails, username=session['username'],email1=session['email1'])
        else:
            msg = 'No Apartments registered by you as of now'
            return render_template('ownerapartments.html', msg=msg, username=session['username'], email1=session['email1'])
    else:
        return redirect(url_for('login'))

@app.route("/ownerrooms/")
def ownerrooms():
    msg = ''
    if 'loggedin' in session:
        cur = mysql.connection.cursor()
        resultValue = cur.execute("SELECT * FROM roomdetail where id=%s", (session['id'],))
        if resultValue > 0:
            roomDetails = cur.fetchall()
            return render_template('ownerrooms.html', msg=msg, roomDetails=roomDetails, username=session['username'],
                                   email1=session['email1'])
        else:
            msg = 'No Room Registered by you as of now'
            return render_template('ownerrooms.html', msg=msg, username=session['username'], email1=session['email1'])


@app.route("/ownerprojects/")
def ownerprojects():
    msg = ''
    if 'loggedin' in session:
        cur = mysql.connection.cursor()
        resultValue = cur.execute("SELECT * FROM projectdetail where id=%s", (session['id'],))
        if resultValue > 0:
            projectDetails = cur.fetchall()
            return render_template('ownerprojects.html', msg=msg, projectDetails=projectDetails, username=session['username'],
                                   email1=session['email1'])
        else:
            msg = 'No Projects added by you as of now'
            return render_template('ownerprojects.html', msg=msg, username=session['username'], email1=session['email1'])

@app.route("/applied_apt/", methods=['GET', 'POST'])
def applied_apt():
    if 'loggedin' in session and session['username'] != 'admin':
      cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
      cursor.execute('SELECT username,Aname,Plot_no,Area,Address,Landmark,City,Pincode,State,Country,Price,Atype,RS,Availability,Facilities,Descr,image,rating FROM apartmentdetail INNER JOIN accounts on apartmentdetail.id=accounts.id where A_ID in (select A_ID from Buy_propertyapt where id=%s) ',[session['id']])
      result = cursor.fetchall()
      mysql.connection.commit()
      cursor.close()
      return render_template('applied_aptdetails.html',details=result,username=session['username'],email1=session['email1'])
    elif 'loggedin' in session and session['username'] == 'admin':
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))

@app.route("/Buy_propertyapt/<string:id>", methods=['GET', 'POST'])
def Buy_propertyapt(id):
    if 'loggedin' in session and session['username'] != 'admin':
        msg = ''
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * from Buy_propertyapt where A_ID=%s and id=%s', ([id], [session['id']]))
        res = cursor.fetchall()
        # 1-------
        if res:
            msg = 'You have already applied for this apartment!'
            return render_template('search.html', username=session['username'], msg=msg,email1=session['email1'])
        elif request.method == 'POST':
                Age = request.form['Age']
                Occupation = request.form['Occupation']
                Address = request.form['Address']
                Landmark = request.form['Landmark']
                City = request.form['City']
                Pincode = request.form['Pincode']
                State = request.form['State']
                Status = 'Not Approved'
                if len(City) > 0 and len(Age) > 0 and len(Occupation) > 0 and len(Address) > 0 and len(Landmark) > 0 and len(Pincode) > 0 and len(State) > 0:
                    cursor.execute('INSERT INTO Buy_propertyapt VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(id,session['id'],Age,Address,Landmark,City,Pincode,State,Occupation,Status))
                    mysql.connection.commit()
                    cursor.close()
                    msg = 'Your application for an apartment is registered successfully :)'
                    return redirect(url_for('applied_apt'))
                else:
                    msg = 'Please fill out the form !'
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute('SELECT Aname from apartmentdetail where A_ID=%s', [id, ])
        data = cur.fetchall()
        cur.execute('SELECT fullname,email,mobile from accounts where id=%s', [session['id'], ])
        data1 = cur.fetchall()
        data = data + data1
        cur.close()
        return render_template("Buy_propertyapt.html", datas=data, msg=msg, id=id, username=session['username'],
                               email1=session['email1'])
    elif 'loggedin' in session and session['username'] == 'admin':
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))

@app.route('/complaintsapartment/<string:id>', methods=['GET', 'POST'])
def complaintsapartment(id):
    msg = ''
    if request.method == 'POST':
        data = request.form
        apmtname = data['name']
        complaint = data['complaint']
        if len(apmtname) > 0 and len(complaint) > 0:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO complaintsapartment VALUES(NULL, %s, %s, %s,0)", (id, apmtname, complaint))
            mysql.connection.commit()
            cur.close()
            msg = '   A complaint has been successfully registered'
        else:
            msg = '   Please fill out the form !'
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT Aname from apartmentdetail where A_ID=%s",(id) )
    aptn = cur.fetchall()
    cur.close()
    if 'loggedin' in session:
        return render_template("complaintsapartment.html", msg=msg, datas=aptn, id=id, username=session['username'],
                               email1=session['email1'])
    else:
        return render_template("login.html")


@app.route('/complaintsroom/<string:id>', methods=['GET', 'POST'])
def complaintsroom(id):
    msg = ''
    if request.method == 'POST':
        data = request.form
        Room_no = data['name']
        complaint = data['complaint']
        if len(Room_no) > 0 and len(complaint) > 0:
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("INSERT INTO complaintsroom VALUES(NULL, %s, %s, %s, 0)", [id, Room_no, complaint])

            mysql.connection.commit()
            cur.close()
            msg = '   A complaint has been successfully registered'
        else:
            msg = '   Please fill out the form !'
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('SELECT Room_no from roomdetail where R_ID=%s', [id, ])
    no = cur.fetchall()
    cur.close()
    if 'loggedin' in session:
        return render_template("complaintsroom.html", msg=msg, datas=no, id=id, username=session['username'],
                               email1=session['email1'])
    else:
        return render_template("login.html")

@app.route('/complaintsbuilder/<string:id>', methods=['GET', 'POST'])
def complaintsbuilder(id):
    msg = ''
    if request.method == 'POST':
        data = request.form
        pname = data['name']
        complaint = data['complaint']
        if len(pname) > 0 and len(complaint) > 0:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO complaintsbuilder VALUES(NULL, %s, %s, %s,0)", (id, pname, complaint))
            mysql.connection.commit()
            cur.close()
            msg = '   A complaint has been successfully registered'
        else:
            msg = '   Please fill out the form !'
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT Pname from projectdetail where P_ID=%s",(id) )
    pn = cur.fetchall()
    cur.close()
    if 'loggedin' in session:
        return render_template("complaintsbuilder.html", msg=msg, datas=pn, id=id, username=session['username'],
                               email1=session['email1'])
    else:
        return render_template("login.html")


@app.route("/book_apt/<string:id>", methods=['GET', 'POST'])
def book_apt(id):
    if 'loggedin' in session:
        if session['username'] != 'admin':
            msg=''
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('select * from book_meet_apt where A_ID=%s and id=%s',([id], [session['id']]))
            res= cursor.fetchall()
            if res:
                msg= 'You have already booked a meeting for this apartment!'
                return render_template("search.html", msg=msg,username=session['username'], email1=session['email1'])
            elif request.method == 'POST':
                A_ID = request.form['A_ID']
                Aname = request.form['Aname']
                Fullname = request.form['fullname']
                Email = request.form['email']
                Mobile = request.form['mobile']
                Address = request.form['Address']
                Landmark = request.form['Landmark']
                City = request.form['City']
                Pincode = request.form['Pincode']
                State = request.form['State']
                Country = request.form['Country']
                Occupation = request.form['Occupation']
                Slot = request.form['Slot']
                booking_date = request.form['booking_date']
                if len(A_ID) > 0 and len(Aname) > 0 and len(Email) > 0 and len(Mobile) > 0 and len(
                        Fullname) > 0 and len(
                        City) > 0 and len(Slot) > 0 and len(Address) > 0 and len(Landmark) > 0 and len(
                    Pincode) > 0 and len(State) > 0 and len(Country) > 0 and len(Occupation)>0 and len(booking_date)>0:
                    if not re.match(r'[^@]+@[^@]+\.[^@]+', Email):
                        msg = 'Invalid email address !'
                    elif len(Mobile) != 10:
                        msg = 'Enter 10 digit number !'
                    else:
                        cursor.execute(
                            'INSERT INTO book_meet_apt VALUES (%s, % s, % s, % s, % s, % s, % s, %s, %s, %s, %s)',
                            (A_ID, session['id'], Address, Landmark, City, Pincode, State, Country, Occupation, Slot, booking_date))
                        mysql.connection.commit()
                        cursor.close()
                        return render_template("search.html", username=session['username'], email1=session['email1'])
                else:
                    msg = 'Please fill out the form !'
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute('SELECT Aname from apartmentdetail where A_ID=%s', [id, ])
            data = cur.fetchall()
            cur.execute('select fullname,email,mobile from accounts where username=%s', [session['username'], ])
            data1 = cur.fetchall()
            l = list(data)
            l1 =list(data1)
            cur.close()
            return render_template("book_apt.html", datas=l, data1=l1, msg=msg, A_ID=id, username=session['username'],
                                   email1=session['email1'])
    return redirect(url_for('login'))

@app.route("/book_meet_display", methods=['GET', 'POST'])
def book_meet_display():
    if 'loggedin' in session:
        if session['username'] != 'admin':
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM book_meet_apt where A_ID in (select A_ID from apartmentdetail where id=%s)',
                           [session['id']])
            result = cursor.fetchall()
            r = list(result)
            cursor.execute(
                'SELECT A_ID, Aname FROM apartmentdetail where id= %s and A_ID in (select A_ID from book_meet_apt)',
                [session['id']])
            result1 = cursor.fetchall()
            r1 = list(result1)
            ans = []
            for i in r:
                for j in r1:
                    if i['A_ID'] == j['A_ID']:
                        k = []
                        k.append(i['A_ID'])
                        k.append(i['id'])
                        k.append(i['Address'])
                        k.append(i['Landmark'])
                        k.append(i['City'])
                        k.append(i['Pincode'])
                        k.append(i['State'])
                        k.append(i['Country'])
                        k.append(i['Occupation'])
                        k.append(i['Slot'])
                        k.append(i['booking_date'])
                        k.append(j['Aname'])
                        cursor.execute('select fullname, email, mobile from accounts where id=%s', [i['id']])
                        result2 = cursor.fetchall()
                        r2 = list(result2)
                        k.append(r2[0]['fullname'])
                        k.append(r2[0]['email'])
                        k.append(r2[0]['mobile'])
                        ans.append(k)

            cursor.execute('SELECT * FROM book_meet_room where R_ID in (select R_ID from roomdetail where id=%s)',
                           [session['id']])
            resultr = cursor.fetchall()
            rr = list(resultr)
            cursor.execute(
                'SELECT R_ID, Bname, Room_no FROM roomdetail where id= %s and R_ID in (select R_ID from book_meet_room)',
                [session['id']])
            resultr1 = cursor.fetchall()
            rr1 = list(resultr1)
            ansr = []
            for i in rr:
                for j in rr1:
                    if i['R_ID'] == j['R_ID']:
                        k = []
                        k.append(i['R_ID'])
                        k.append(i['id'])
                        k.append(i['Address'])
                        k.append(i['Landmark'])
                        k.append(i['City'])
                        k.append(i['Pincode'])
                        k.append(i['State'])
                        k.append(i['Country'])
                        k.append(i['Occupation'])
                        k.append(i['Slot'])
                        k.append(i['booking_date'])
                        k.append(j['Bname'])
                        cursor.execute('select fullname, email, mobile from accounts where id=%s', [i['id']])
                        result2 = cursor.fetchall()
                        r2 = list(result2)
                        k.append(r2[0]['fullname'])
                        k.append(r2[0]['email'])
                        k.append(r2[0]['mobile'])
                        k.append(j['Room_no'])
                        ansr.append(k)

            cursor.execute('SELECT * FROM book_meet_project where P_ID in (select P_ID from projectdetail where id=%s)',
                           [session['id']])
            resultp = cursor.fetchall()
            rp = list(resultp)
            cursor.execute(
                'SELECT P_ID, Pname, Flattype FROM projectdetail where id= %s and P_ID in (select P_ID from book_meet_project)',
                [session['id']])
            resultp1 = cursor.fetchall()
            rp1 = list(resultp1)
            ansp = []
            for i in rp:
                for j in rp1:
                    if i['P_ID'] == j['P_ID']:
                        k = []
                        k.append(i['P_ID'])
                        k.append(i['id'])
                        k.append(i['Address'])
                        k.append(i['Landmark'])
                        k.append(i['City'])
                        k.append(i['Pincode'])
                        k.append(i['State'])
                        k.append(i['Country'])
                        k.append(i['Occupation'])
                        k.append(i['Slot'])
                        k.append(i['booking_date'])
                        k.append(j['Pname'])
                        cursor.execute('select fullname, email, mobile from accounts where id=%s', [i['id']])
                        result2 = cursor.fetchall()
                        r2 = list(result2)
                        k.append(r2[0]['fullname'])
                        k.append(r2[0]['email'])
                        k.append(r2[0]['mobile'])
                        k.append(j['Flattype'])
                        ansp.append(k)
            cursor.close()
            print(ansp)
            print(ansr)
            return render_template("book_meet_display.html", ans=ans,ansr=ansr, ansp=ansp, username=session['username'],
                                   email1=session['email1'])
    return redirect(url_for('login'))

@app.route("/accept_apt/<string:id>/<string:aid>", methods=['GET', 'POST'])
def accept_apt(id, aid):
    if 'loggedin' in session:
        if session['username'] != 'admin':
            msg=''
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            if request.method == 'POST':
                A_ID = aid
                buyer_id = id
                Aname = request.form['Aname']
                Fullname = request.form['fullname']
                Email = request.form['email']
                Mobile = request.form['mobile']
                Address = request.form['Address']
                Landmark = request.form['Landmark']
                City = request.form['City']
                Pincode = request.form['Pincode']
                State = request.form['State']
                Country = request.form['Country']
                starttime = request.form['starttime']
                endtime = request.form['endtime']
                booking_date = request.form['booking_date']
                if len(A_ID) > 0 and len(Aname) > 0 and len(Email) > 0 and len(Mobile) > 0 and len(
                        Fullname) > 0 and len(
                        City) > 0 and len(starttime) > 0 and len(Address) > 0 and len(Landmark) > 0 and len(
                    Pincode) > 0 and len(State) > 0 and len(Country) > 0 and len(endtime)>0 and len(booking_date)>0:
                    if not re.match(r'[^@]+@[^@]+\.[^@]+', Email):
                        msg = 'Invalid email address !'
                    elif len(Mobile) != 10:
                        msg = 'Enter 10 digit number !'
                    else:
                        cursor.execute(
                            'INSERT INTO accept_meet_apt VALUES (NULL,%s, % s, % s, % s, % s, % s, % s, %s, %s, %s, %s, %s)',
                            (A_ID, session['id'],buyer_id, Address, Landmark, City, Pincode, State, Country, booking_date, starttime, endtime))
                        mysql.connection.commit()

                        cursor.execute('delete from book_meet_apt where A_ID=%s and id=%s', [A_ID, buyer_id, ])
                        mysql.connection.commit()
                        cursor.close()
                        return render_template("search.html", username=session['username'], email1=session['email1'])
                else:
                    msg = 'Please fill out the form !'
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute('SELECT Aname from apartmentdetail where A_ID=%s', [aid, ])
            data = cur.fetchall()
            cur.execute('select fullname,email,mobile from accounts where username=%s', [session['username'], ])
            data1 = cur.fetchall()
            l = list(data)
            l1 =list(data1)
            cur.close()
            return render_template("accept_apt.html", datas=l, data1=l1, msg=msg, A_ID=aid, buyer_id=id, username=session['username'],
                                   email1=session['email1'])
    return redirect(url_for('login'))

@app.route("/book_room/<string:id>", methods=['GET', 'POST'])
def book_room(id):
    if 'loggedin' in session:
        if session['username'] != 'admin':
            msg=''
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('select * from book_meet_room where R_ID=%s and id=%s',([id], [session['id']]))
            res= cursor.fetchall()
            if res:
                msg= 'You have already booked a meeting for this room!'
                return render_template("search.html", msg=msg,username=session['username'], email1=session['email1'])
            elif request.method == 'POST':
                R_ID = request.form['R_ID']
                Bname = request.form['Bname']
                Room_no = request.form['Room_no']
                Fullname = request.form['fullname']
                Email = request.form['email']
                Mobile = request.form['mobile']
                Address = request.form['Address']
                Landmark = request.form['Landmark']
                City = request.form['City']
                Pincode = request.form['Pincode']
                State = request.form['State']
                Country = request.form['Country']
                Occupation = request.form['Occupation']
                Slot = request.form['Slot']
                booking_date = request.form['booking_date']
                if len(R_ID) > 0 and len(Bname) > 0 and len(Email) > 0 and len(Mobile) > 0 and len(
                        Fullname) > 0 and len(
                        City) > 0 and len(Slot) > 0 and len(Address) > 0 and len(Landmark) > 0 and len(
                    Pincode) > 0 and len(State) > 0 and len(Country) > 0 and len(Occupation)>0 and len(booking_date)>0 and len(Room_no) >0:
                    if not re.match(r'[^@]+@[^@]+\.[^@]+', Email):
                        msg = 'Invalid email address !'
                    elif len(Mobile) != 10:
                        msg = 'Enter 10 digit number !'
                    else:
                        cursor.execute(
                            'INSERT INTO book_meet_room VALUES (%s, % s, % s, % s, % s, % s, % s, %s, %s, %s, %s)',
                            (R_ID, session['id'], Address, Landmark, City, Pincode, State, Country, Occupation, Slot, booking_date))
                        mysql.connection.commit()
                        cursor.close()
                        return render_template("search.html", username=session['username'], email1=session['email1'])
                else:
                    msg = 'Please fill out the form !'
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute('SELECT Bname, Room_no from roomdetail where R_ID=%s', [id, ])
            data = cur.fetchall()
            cur.execute('select fullname,email,mobile from accounts where username=%s', [session['username'], ])
            data1 = cur.fetchall()
            l = list(data)
            l1 =list(data1)
            cur.close()
            return render_template("book_room.html", datas=l, data1=l1, msg=msg, R_ID=id, username=session['username'],
                                   email1=session['email1'])
    return redirect(url_for('login'))


@app.route("/accept_room/<string:id>/<string:rid>", methods=['GET', 'POST'])
def accept_room(id, rid):
    if 'loggedin' in session:
        if session['username'] != 'admin':
            msg=''
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            if request.method == 'POST':
                R_ID = rid
                buyer_id = id
                Bname = request.form['Bname']
                Room_no = request.form['Room_no']
                Fullname = request.form['fullname']
                Email = request.form['email']
                Mobile = request.form['mobile']
                Address = request.form['Address']
                Landmark = request.form['Landmark']
                City = request.form['City']
                Pincode = request.form['Pincode']
                State = request.form['State']
                Country = request.form['Country']
                starttime = request.form['starttime']
                endtime = request.form['endtime']
                booking_date = request.form['booking_date']
                if len(R_ID) > 0 and len(Bname) > 0 and len(Room_no)>0 and len(Email) > 0 and len(Mobile) > 0 and len(
                        Fullname) > 0 and len(
                        City) > 0 and len(starttime) > 0 and len(Address) > 0 and len(Landmark) > 0 and len(
                    Pincode) > 0 and len(State) > 0 and len(Country) > 0 and len(endtime)>0 and len(booking_date)>0:
                    if not re.match(r'[^@]+@[^@]+\.[^@]+', Email):
                        msg = 'Invalid email address !'
                    elif len(Mobile) != 10:
                        msg = 'Enter 10 digit number !'
                    else:
                        cursor.execute(
                            'INSERT INTO accept_meet_room VALUES (NULL,%s, % s, % s, % s, % s, % s, % s, %s, %s, %s, %s, %s)',
                            (R_ID, session['id'],buyer_id, Address, Landmark, City, Pincode, State, Country, booking_date, starttime, endtime))
                        mysql.connection.commit()

                        cursor.execute('delete from book_meet_room where R_ID=%s and id=%s', [R_ID, buyer_id, ])
                        mysql.connection.commit()
                        cursor.close()
                        return render_template("search.html", username=session['username'], email1=session['email1'])
                else:
                    msg = 'Please fill out the form !'
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute('SELECT Bname, Room_no from roomdetail where R_ID=%s', [rid, ])
            data = cur.fetchall()
            cur.execute('select fullname,email,mobile from accounts where username=%s', [session['username'], ])
            data1 = cur.fetchall()
            l = list(data)
            l1 =list(data1)
            cur.close()
            return render_template("accept_room.html", datas=l, data1=l1, msg=msg, R_ID=rid, buyer_id=id, username=session['username'],
                                   email1=session['email1'])
    return redirect(url_for('login'))

@app.route("/book_project/<string:id>", methods=['GET', 'POST'])
def book_project(id):
    if 'loggedin' in session:
        if session['username'] != 'admin':
            msg=''
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('select * from book_meet_project where P_ID=%s and id=%s',([id], [session['id']]))
            res= cursor.fetchall()
            if res:
                msg= 'You have already booked a meeting for this project!'
                return render_template("search.html", msg=msg,username=session['username'], email1=session['email1'])
            elif request.method == 'POST':
                P_ID = request.form['P_ID']
                Pname = request.form['Pname']
                Flattype = request.form['Flattype']
                Fullname = request.form['fullname']
                Email = request.form['email']
                Mobile = request.form['mobile']
                Address = request.form['Address']
                Landmark = request.form['Landmark']
                City = request.form['City']
                Pincode = request.form['Pincode']
                State = request.form['State']
                Country = request.form['Country']
                Occupation = request.form['Occupation']
                Slot = request.form['Slot']
                booking_date = request.form['booking_date']
                if len(P_ID) > 0 and len(Pname) > 0 and len(Flattype)>0 and len(Email) > 0 and len(Mobile) > 0 and len(
                        Fullname) > 0 and len(
                        City) > 0 and len(Slot) > 0 and len(Address) > 0 and len(Landmark) > 0 and len(
                    Pincode) > 0 and len(State) > 0 and len(Country) > 0 and len(Occupation)>0 and len(booking_date)>0:
                    if not re.match(r'[^@]+@[^@]+\.[^@]+', Email):
                        msg = 'Invalid email address !'
                    elif len(Mobile) != 10:
                        msg = 'Enter 10 digit number !'
                    else:
                        cursor.execute(
                            'INSERT INTO book_meet_project VALUES (%s, % s, % s, % s, % s, % s, % s, %s, %s, %s, %s)',
                            (P_ID, session['id'], Address, Landmark, City, Pincode, State, Country, Occupation, Slot, booking_date))
                        mysql.connection.commit()
                        cursor.close()
                        return render_template("search.html", username=session['username'], email1=session['email1'])
                else:
                    msg = 'Please fill out the form !'
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute('SELECT Pname, Flattype from projectdetail where P_ID=%s', [id, ])
            data = cur.fetchall()
            cur.execute('select fullname,email,mobile from accounts where username=%s', [session['username'], ])
            data1 = cur.fetchall()
            l = list(data)
            l1 =list(data1)
            cur.close()
            return render_template("book_project.html", datas=l, data1=l1, msg=msg, P_ID=id, username=session['username'],
                                   email1=session['email1'])
    return redirect(url_for('login'))



@app.route("/accept_project/<string:id>/<string:pid>", methods=['GET', 'POST'])
def accept_project(id, pid):
    if 'loggedin' in session:
        if session['username'] != 'admin':
            msg=''
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            if request.method == 'POST':
                P_ID = pid
                buyer_id = id
                Pname = request.form['Pname']
                Flattype = request.form['Flattype']
                Fullname = request.form['fullname']
                Email = request.form['email']
                Mobile = request.form['mobile']
                Address = request.form['Address']
                Landmark = request.form['Landmark']
                City = request.form['City']
                Pincode = request.form['Pincode']
                State = request.form['State']
                Country = request.form['Country']
                starttime = request.form['starttime']
                endtime = request.form['endtime']
                booking_date = request.form['booking_date']
                if len(P_ID) > 0 and len(Pname) > 0 and len(Flattype)>0 and len(Email) > 0 and len(Mobile) > 0 and len(
                        Fullname) > 0 and len(
                        City) > 0 and len(starttime) > 0 and len(Address) > 0 and len(Landmark) > 0 and len(
                    Pincode) > 0 and len(State) > 0 and len(Country) > 0 and len(endtime)>0 and len(booking_date)>0:
                    if not re.match(r'[^@]+@[^@]+\.[^@]+', Email):
                        msg = 'Invalid email address !'
                    elif len(Mobile) != 10:
                        msg = 'Enter 10 digit number !'
                    else:
                        cursor.execute(
                            'INSERT INTO accept_meet_project VALUES (NULL,%s, % s, % s, % s, % s, % s, % s, %s, %s, %s, %s, %s)',
                            (P_ID, session['id'],buyer_id, Address, Landmark, City, Pincode, State, Country, booking_date, starttime, endtime))
                        mysql.connection.commit()

                        cursor.execute('delete from book_meet_project where P_ID=%s and id=%s', [P_ID, buyer_id, ])
                        mysql.connection.commit()
                        cursor.close()
                        return render_template("search.html", username=session['username'], email1=session['email1'])
                else:
                    msg = 'Please fill out the form !'
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute('SELECT Pname,Flattype from projectdetail where P_ID=%s', [pid, ])
            data = cur.fetchall()
            cur.execute('select fullname,email,mobile from accounts where username=%s', [session['username'], ])
            data1 = cur.fetchall()
            l = list(data)
            l1 =list(data1)
            cur.close()
            return render_template("accept_project.html", datas=l, data1=l1, msg=msg, P_ID=pid, buyer_id=id, username=session['username'],
                                   email1=session['email1'])
    return redirect(url_for('login'))

app.run(debug=True)