from flask import Flask, render_template, request
import sqlite3
import requests


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        title_user = request.form['title']
        area_user = request.form['area']
        salary_user = request.form['salary']

        conn = sqlite3.connect('vacancies.db')
        cursor = conn.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS vacancies (
                            id INTEGER PRIMARY KEY,
                            title TEXT,
                            company TEXT,
                            salary TEXT,
                            area TEXT
                        )''')
        url = "https://api.hh.ru/vacancies"
        params = {
            "text": str(title_user),
            "per_page": 10
        }
        response = requests.get(url, params=params)

        cursor.execute('DELETE FROM vacancies WHERE title != ?', (title_user,))

        if response.status_code == 200:
            data = response.json()
            for vacancy in data['items']:
                title = vacancy['name']
                company = vacancy['employer']['name']
                salary = vacancy['salary']
                if salary:
                    if salary.get('from') and salary.get('to'):
                        salary_value = (salary['from'] + salary['to']) // 2
                    elif salary.get('from'):
                        salary_value = salary['from']
                    elif salary.get('to'):
                        salary_value = salary['to']
                    else:
                        salary_value = None
                else:
                    salary_value = None

                area = vacancy['area']['name']

                if salary_value is not None:
                    cursor.execute('SELECT * FROM vacancies WHERE title=? AND company=? AND salary=? AND area=?',
                                   (title, company, salary_value, area))
                else:
                    cursor.execute('SELECT * FROM vacancies WHERE title=? AND company=? AND salary IS NULL AND area=?',
                                   (title, company, area))
                existing_data = cursor.fetchone()

                if not existing_data:
                    if salary_value is not None:
                        cursor.execute('INSERT INTO vacancies (title, company, salary, area) VALUES (?, ?, ?, ?)',
                                       (title, company, salary_value, area))
                    else:
                        cursor.execute('INSERT INTO vacancies (title, company, area) VALUES (?, ?, ?)',
                                       (title, company, area))

        conn.commit()

        cursor.execute('SELECT title, company, salary FROM vacancies WHERE area=? AND salary>=?',
                       (area_user, salary_user))
        vacancies = cursor.fetchall()
        cursor.execute("SELECT COUNT(*) FROM vacancies WHERE area=?", (area_user,))
        count = cursor.fetchone()[0]
        conn.close()

        return render_template('index.html', vacancies=vacancies, count=count)
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
