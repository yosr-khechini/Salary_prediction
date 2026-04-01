"""
Script to recreate the SQLite database with INSAF-compatible tables and sample data
"""
import sqlite3
import os
from werkzeug.security import generate_password_hash

# Database path
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'app.db')

# Ensure instance directory exists
os.makedirs(os.path.dirname(db_path), exist_ok=True)

print(f"Database path: {db_path}")

# Remove existing database
if os.path.exists(db_path):
    os.remove(db_path)
    print("Removed existing database")

# Connect to database (creates new one)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create employees table with INSAF-compatible structure
print("Creating employees table...")
cursor.execute("""
    CREATE TABLE employees (
        matricule INTEGER PRIMARY KEY,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        birth_date DATE NOT NULL,
        grade VARCHAR(20),
        echelon INTEGER,
        indice INTEGER,
        corps VARCHAR(50),
        salaire_base DECIMAL(10, 2),
        indemnite_residence DECIMAL(10, 2),
        indemnite_transport DECIMAL(10, 2),
        situation_familiale VARCHAR(20),
        nombre_enfants INTEGER DEFAULT 0,
        date_joined DATE,
        date_titularisation DATE,
        date_left DATE
    )
""")

# Insert 30 employees with INSAF-compatible data
# (matricule, first_name, last_name, birth_date, grade, echelon, indice, corps, salaire_base, indemnite_residence, indemnite_transport, situation_familiale, nombre_enfants, date_joined, date_titularisation, date_left)
employees_data = [
    (1001, 'Ahmed', 'Benali', '1985-03-15', 'A2', 5, 450, 'Technique', 2500.00, 150.00, 100.00, 'Marié(e)', 2, '2015-01-10', '2016-01-10', None),
    (1002, 'Fatima', 'Zahra', '1990-07-22', 'A3', 3, 380, 'Administratif', 2000.00, 120.00, 80.00, 'Célibataire', 0, '2018-03-05', '2019-03-05', None),
    (1003, 'Mohamed', 'Alami', '1988-11-30', 'A1', 7, 550, 'Technique', 3500.00, 200.00, 120.00, 'Marié(e)', 3, '2014-06-15', '2015-06-15', None),
    (1004, 'Khadija', 'Bouzid', '1992-04-18', 'B', 4, 320, 'Administratif', 1800.00, 100.00, 70.00, 'Célibataire', 0, '2019-09-01', '2020-09-01', None),
    (1005, 'Youssef', 'Tazi', '1983-09-05', 'A1', 10, 650, 'Administratif', 5000.00, 300.00, 180.00, 'Marié(e)', 4, '2010-02-20', '2011-02-20', None),
    (1006, 'Amina', 'Rachidi', '1995-01-12', 'A2', 2, 400, 'Technique', 2200.00, 130.00, 90.00, 'Célibataire', 0, '2020-01-15', '2021-01-15', None),
    (1007, 'Omar', 'Fassi', '1987-06-25', 'A2', 6, 480, 'Administratif', 2800.00, 160.00, 110.00, 'Marié(e)', 2, '2016-04-10', '2017-04-10', None),
    (1008, 'Salma', 'Benjelloun', '1991-12-08', 'A2', 5, 460, 'Administratif', 3000.00, 180.00, 120.00, 'Marié(e)', 1, '2017-07-22', '2018-07-22', None),
    (1009, 'Karim', 'Chraibi', '1986-02-14', 'A1', 8, 580, 'Technique', 3200.00, 190.00, 130.00, 'Marié(e)', 2, '2013-11-05', '2014-11-05', None),
    (1010, 'Laila', 'Idrissi', '1993-08-30', 'C', 2, 220, 'Administratif', 1500.00, 80.00, 50.00, 'Célibataire', 0, '2021-02-01', '2022-02-01', None),
    (1011, 'Hassan', 'Berrada', '1984-05-20', 'B', 6, 350, 'Technique', 1700.00, 90.00, 60.00, 'Marié(e)', 3, '2015-08-12', '2016-08-12', None),
    (1012, 'Nadia', 'Kettani', '1989-10-03', 'A2', 5, 470, 'Administratif', 2600.00, 140.00, 100.00, 'Marié(e)', 1, '2016-12-01', '2017-12-01', None),
    (1013, 'Rachid', 'Amrani', '1982-07-17', 'A2', 7, 500, 'Administratif', 2900.00, 170.00, 110.00, 'Marié(e)', 2, '2012-03-25', '2013-03-25', None),
    (1014, 'Zineb', 'Lahlou', '1994-03-28', 'A3', 3, 360, 'Technique', 2100.00, 110.00, 80.00, 'Célibataire', 0, '2019-05-18', '2020-05-18', None),
    (1015, 'Mehdi', 'Sqalli', '1988-09-11', 'A2', 5, 460, 'Technique', 2700.00, 150.00, 100.00, 'Marié(e)', 1, '2017-10-08', '2018-10-08', None),
    (1016, 'Sara', 'Bennis', '1996-06-05', 'D', 1, 150, 'Technique', 500.00, 30.00, 20.00, 'Célibataire', 0, '2023-01-10', None, None),
    (1017, 'Amine', 'Tahiri', '1985-12-22', 'A1', 8, 560, 'Administratif', 3100.00, 185.00, 125.00, 'Marié(e)', 2, '2014-09-15', '2015-09-15', None),
    (1018, 'Hajar', 'Mouline', '1991-04-09', 'A3', 4, 380, 'Administratif', 1900.00, 105.00, 75.00, 'Célibataire', 0, '2018-06-20', '2019-06-20', None),
    (1019, 'Driss', 'Belhaj', '1980-01-30', 'A1', 12, 700, 'Technique', 5500.00, 350.00, 200.00, 'Marié(e)', 4, '2008-05-01', '2009-05-01', None),
    (1020, 'Meryem', 'Kabbaj', '1993-11-15', 'B', 3, 300, 'Administratif', 1800.00, 95.00, 65.00, 'Célibataire', 0, '2020-03-10', '2021-03-10', None),
    (1021, 'Hamza', 'Filali', '1987-08-08', 'A1', 9, 620, 'Technique', 3800.00, 220.00, 140.00, 'Marié(e)', 2, '2015-02-28', '2016-02-28', None),
    (1022, 'Imane', 'Sekkat', '1990-02-25', 'A2', 5, 465, 'Technique', 2650.00, 145.00, 100.00, 'Marié(e)', 1, '2017-04-15', '2018-04-15', None),
    (1023, 'Khalid', 'Bennani', '1983-10-12', 'A1', 8, 580, 'Administratif', 3300.00, 195.00, 130.00, 'Marié(e)', 3, '2011-08-20', '2012-08-20', None),
    (1024, 'Houda', 'Zniber', '1995-07-04', 'A3', 2, 350, 'Technique', 2150.00, 125.00, 85.00, 'Célibataire', 0, '2021-06-01', '2022-06-01', None),
    (1025, 'Adil', 'Mekouar', '1986-04-16', 'A2', 6, 490, 'Administratif', 2750.00, 155.00, 105.00, 'Marié(e)', 2, '2014-11-10', '2015-11-10', None),
    (1026, 'Soukaina', 'Jaidi', '1992-09-28', 'A2', 4, 430, 'Technique', 2400.00, 135.00, 95.00, 'Célibataire', 0, '2019-08-05', '2020-08-05', None),
    (1027, 'Mustapha', 'Elghazi', '1981-03-07', 'A1', 10, 660, 'Administratif', 4000.00, 240.00, 160.00, 'Marié(e)', 3, '2009-12-01', '2010-12-01', None),
    (1028, 'Rim', 'Berrechid', '1994-12-19', 'A3', 3, 340, 'Administratif', 1750.00, 90.00, 60.00, 'Célibataire', 0, '2022-02-14', '2023-02-14', None),
    (1029, 'Ayoub', 'Cherkaoui', '1989-06-23', 'A1', 7, 540, 'Technique', 3150.00, 180.00, 120.00, 'Marié(e)', 1, '2018-01-22', '2019-01-22', None),
    (1030, 'Loubna', 'Slaoui', '1997-05-10', 'C', 1, 200, 'Administratif', 1400.00, 75.00, 50.00, 'Célibataire', 0, '2023-04-03', None, None),
]

cursor.executemany("""
    INSERT INTO employees (matricule, first_name, last_name, birth_date, grade, echelon, indice, corps, salaire_base, indemnite_residence, indemnite_transport, situation_familiale, nombre_enfants, date_joined, date_titularisation, date_left)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", employees_data)
print("Inserted 30 employees with INSAF-compatible data")

# Create users table
print("Creating users table...")
cursor.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(64) NOT NULL UNIQUE,
        email_adress VARCHAR(120) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        matricule INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (matricule) REFERENCES employees(matricule)
    )
""")

# Create indexes
cursor.execute("CREATE INDEX idx_users_username ON users(username)")
cursor.execute("CREATE INDEX idx_users_email ON users(email_adress)")

# Insert admin user
admin_hash = generate_password_hash('admin123')
cursor.execute("INSERT INTO users (username, email_adress, password_hash, matricule) VALUES (?, ?, ?, ?)",
    ('admin', 'admin@company.com', admin_hash, 1005))
print("Inserted admin user (admin/admin123)")

# Create recruitment table with INSAF-compatible structure
print("Creating recruitment table...")
cursor.execute("""
    CREATE TABLE recruitment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matricule INTEGER NOT NULL,
        recruitment_date DATE NOT NULL,
        grade VARCHAR(20),
        corps VARCHAR(50),
        first_name VARCHAR(100),
        last_name VARCHAR(100),
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (matricule) REFERENCES employees(matricule)
    )
""")

# Create termination table with INSAF-compatible structure
print("Creating termination table...")
cursor.execute("""
    CREATE TABLE termination (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matricule INTEGER NOT NULL,
        termination_date DATE NOT NULL,
        grade VARCHAR(20),
        corps VARCHAR(50),
        first_name VARCHAR(100),
        last_name VARCHAR(100),
        reason VARCHAR(200),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (matricule) REFERENCES employees(matricule)
    )
""")

# Create prediction_history table
print("Creating prediction_history table...")
cursor.execute("""
    CREATE TABLE prediction_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        start_year INTEGER NOT NULL,
        end_year INTEGER NOT NULL,
        recruitments INTEGER NOT NULL,
        departures INTEGER NOT NULL,
        initial_employees INTEGER NOT NULL,
        result_json TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")

conn.commit()

# Verify the data
print("\n=== Verification ===")
cursor.execute("SELECT COUNT(*) FROM employees")
print(f"Total employees: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM users")
print(f"Total users: {cursor.fetchone()[0]}")

cursor.execute("SELECT matricule, first_name, last_name, grade, corps FROM employees LIMIT 5")
print("\nFirst 5 employees:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} {row[2]} - Grade {row[3]} ({row[4]})")

conn.close()
print("\n✓ Database setup complete with INSAF-compatible data!")
