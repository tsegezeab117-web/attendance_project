from flask import Flask, render_template, request, redirect, url_for
from fpdf import FPDF
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText
import webbrowser, threading, smtplib, sqlite3, os


class AttendanceApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.add_route()
        self.shifts = {
                        "green team": ["Maros", "Tesfay", "Bunimi", "Baba", "Liya"],
                        "red team": ["Alex", "Paul", "Sara", "Mike", "Ruth"],
                        "blue team": ["Alen", "John", "Grace", "Dina", "Nathan"],
                        "yellow team": ["Mechenen", "Lee", "Tom", "Helen", "Fiona"]
                        }
        self.create_table()

    @staticmethod
    def connect_database():
        conn = sqlite3.connect('attendance.db')
        return conn

    def create_table(self):
        conn = self.connect_database()
        cursor = conn.cursor()
        cursor.execute('''
                        CREATE TABLE IF NOT EXISTS yellow (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        time_in TEXT NOT NULL,
                        signature_time_in TEXT NOT NULL,
                        break_time TEXT NOT NULL,
                        time_out TEXT NOT NULL,
                        signature_time_out TEXT NOT NULL
                        )
                        ''')

        cursor.execute('''
                                CREATE TABLE IF NOT EXISTS blue (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                name TEXT NOT NULL,
                                time_in TEXT NOT NULL,
                                signature_time_in TEXT NOT NULL,
                                break_time TEXT NOT NULL,
                                time_out TEXT NOT NULL,
                                signature_time_out TEXT NOT NULL
                                )
                                ''')

        cursor.execute('''
                                CREATE TABLE IF NOT EXISTS red (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                name TEXT NOT NULL,
                                time_in TEXT NOT NULL,
                                signature_time_in TEXT NOT NULL,
                                break_time TEXT NOT NULL,
                                time_out TEXT NOT NULL,
                                signature_time_out TEXT NOT NULL
                                )
                                ''')

        cursor.execute('''
                                CREATE TABLE IF NOT EXISTS green (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                name TEXT NOT NULL,
                                time_in TEXT NOT NULL,
                                signature_time_in TEXT NOT NULL,
                                break_time TEXT NOT NULL,
                                time_out TEXT NOT NULL,
                                signature_time_out TEXT NOT NULL
                                )
                                ''')

        conn.commit()
        conn.close()

    def save_to_database(self, attendance_list, shift):
        conn = self.connect_database()
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO {shift}"
                       "(name, time_in, signature_time_in, break_time, time_out, signature_time_out)"
                       " VALUES (?, ?, ?, ?, ?, ?)",
                       (
                        attendance_list['name'],
                        attendance_list['time_in'],
                        attendance_list['signature_time_in'],
                        attendance_list['break_time'],
                        attendance_list['time_out'],
                        attendance_list['signature_time_out']
                        )
                        )

        conn.commit()
        conn.close()

    def qurry_data(self, shift):
        with self.connect_database() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {shift}")
            sql_data = cursor.fetchall()
            return sql_data

    def add_route(self):
        @self.app.route('/')
        def home():
            return render_template('attendance_app.html', shifts=list(self.shifts.keys()))

        @self.app.route('/shift/<shift_name>')
        def shift_page(shift_name):
            employees = self.shifts.get(shift_name.lower(), [])
            return render_template('shift.html', shift_name=shift_name.title(), employees=employees)

        @self.app.route('/attendance/<shift_name>/<employee_name>')
        def attendance(shift_name, employee_name):
            return render_template('employee_attendance.html', shift_name=shift_name.title(),
                                   employee_name=employee_name.title())

        @self.app.route('/add_to_database/<employee_name>/<shift_name>', methods=['POST'])
        def add_database(employee_name, shift_name):
            a = list(shift_name)[1:]
            pick_team = shift_name[1:a.index(' ')+1]
            self.pdf_data(pick_team)
            shift = shift_name
            name = employee_name
            time_in = request.form.get('time_in')
            signature_time_in = request.form.get('signature_time_in')
            break_time = request.form.get('break_time')
            time_out = request.form.get('time_out')
            signature_time_out = request.form.get('signature_time_out')

            attendance_data = {
                                'name': name,
                                'time_in': time_in,
                                'signature_time_in': signature_time_in,
                                'break_time': break_time,
                                'time_out': time_out,
                                'signature_time_out': signature_time_out
                                }

            self.save_to_database(attendance_data, pick_team)

            return redirect(url_for('home'))

        @self.app.route('/pdf_to_email/<shift_name>', methods=['POST'])
        def send_email_with_pdf(shift_name):
            a = list(shift_name)
            pick_team = shift_name[:a.index(' ')]
            team_leader_email = request.form.get('team_leader_email')
            sender_email = "tsegezeabtesfay18@gmail.com"  # Replace with your Gmail
            sender_password = "vqwtzlxuzsdtqeuh"  # Replace with your app password

            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = team_leader_email
            msg['Subject'] = "Attendance PDF Report"

            # Body of the email
            msg.attach(MIMEText("Please find the attached PDF report.", 'plain'))

            filename = f"sqlite_data_report_{pick_team}.pdf"

            # Open PDF file
            with open(filename, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={filename}')
                msg.attach(part)

            # Send the email
            try:
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
                server.quit()
                # print("Email sent successfully!")
                email_check = "Email sent successfully!"
            except Exception as e:
                email_check = "Failed to send email:", e
                # print("Failed to send email:", e)

            return render_template('send_the_attendance.html', email_check=email_check)

    def run(self):
        self.app.run(debug=True)

    def pdf_data(self, shift):

        rows = self.qurry_data(shift)

        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Add header
        pdf.cell(200, 10, txt="User Data Report", ln=True, align='C')
        pdf.ln(10)

        # Add table headers
        pdf.set_font("Arial", 'B', size=12,)
        pdf.cell(10, 10, "ID", 1, align='C')
        pdf.cell(50, 10, "Name", 1, align='C')
        pdf.cell(20, 10, "time in", 1, align='C')
        pdf.cell(30, 10, "signature", 1, align='C')
        pdf.cell(25, 10, "break", 1, align='C')
        pdf.cell(20, 10, "time out", 1, align='C')
        pdf.cell(30, 10, "signature", 1, align='C')
        pdf.ln()

        # Add table rows
        pdf.set_font("Arial", size=12)
        for row in rows:
            pdf.cell(10, 10, str(row[0]), 1, align='C')
            pdf.cell(50, 10, row[1], 1, align='C')
            pdf.cell(20, 10, row[2], 1, align='C')
            pdf.cell(30, 10, row[3], 1, align='C')
            pdf.cell(25, 10, row[4], 1, align='C')
            pdf.cell(20, 10, row[5], 1, align='C')
            pdf.cell(30, 10, row[6], 1, align='C')
            pdf.ln()

        # Save PDF
        pdf.output(f"sqlite_data_report_{shift}.pdf")

    @staticmethod
    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5000/")


if __name__ == '__main__':
    attendance_app = AttendanceApp()
    # threading.Timer(1.0, attendance_app.open_browser).start()
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1.0, attendance_app.open_browser).start()
    # attendance_app.create_table()
    attendance_app.run()


