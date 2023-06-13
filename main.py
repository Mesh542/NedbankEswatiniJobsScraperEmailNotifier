# This program automatically fetches job listings from the Nedbank Eswatini website and sends them to a specified
# user via email (gmail). The email would have to be configured to use 2-FA and to use the privacy key that acts as a
# password. You can specify it as an environment variable or directly, but the former is more secure.
# run <pyinstaller --onefile main.py> without brackets to make .py file .exe. Pip install pyinstaller if need be
# AUTHOR: Mesh
import requests
from bs4 import BeautifulSoup
from email.message import EmailMessage
import ssl
import smtplib
import os
import sqlite3
import datetime

try:
    response = requests.get('https://www.nedbank.co.sz/content/nedbank-swaziland/desktop/sz/en/careers/vacancies0.html')
    soup = BeautifulSoup(response.content, "html.parser")
    jobs = soup.find_all("div", class_="copy")[2]
    conn = sqlite3.connect('nedbank_jobs.db',
                             detect_types=sqlite3.PARSE_DECLTYPES |
                             sqlite3.PARSE_COLNAMES)

    conn.execute('''CREATE TABLE IF NOT EXISTS JOBS
             (ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
             JOB_NAME           TEXT    NOT NULL,
             LINK            TEXT     NOT NULL,
             DATE   DATE       NOT NULL);''')

    insert_statement = "INSERT INTO JOBS (JOB_NAME, LINK, DATE) \
        VALUES (?, ?, ?);"
    final_jobs = []
    count = 1

    cursor = conn.cursor()
    rows = cursor.execute("SELECT * from JOBS").fetchall()
    jobs_from_db = []
    job_links_from_db = []
    for row in rows:
        jobs_from_db.append(row[1])
        job_links_from_db.append(row[2])
        days_lapsed = datetime.date.today() - row[3]
        if days_lapsed.days == 30:
            cursor.execute(f"DELETE FROM JOBS WHERE ID = {row[0]}")

    for job in jobs.find_all("li"):
        if job.find('a').string not in jobs_from_db and job.find('a').get('href') not in job_links_from_db:
            cursor.execute(insert_statement, (job.find('a').string, job.find('a').get('href'), datetime.date.today()))
            final_jobs.append(f'{count}. Job: {job.find("a").string} -- Link: {job.find("a").get("href")}')
            count += 1

    # Creating the email client
    if final_jobs:
        email_sender = 'example@gmail.com'
        # Created an environment variable with the password string for security
        email_password = os.environ.get('GMAIL_PW')
        email_receiver = 'example@gmail.com'
        subject = 'Nedbank job posts'
        body = f'''
        URL: https://www.nedbank.co.sz/content/nedbank-swaziland/desktop/sz/en/careers/vacancies0.html

        JOBS: {final_jobs}
        '''

        em = EmailMessage()
        em['from'] = email_sender
        em['To'] = email_receiver
        em['Subject'] = subject
        em.set_content(body)

        context = ssl.create_default_context()

        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(email_sender, email_password)
            smtp.sendmail(email_sender, email_receiver, em.as_string())

    conn.commit()
    conn.close()
except Exception as e:
    print(e)
    exit(-1)
