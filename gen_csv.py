import pandas as pd
import os

data = {
    "Name": [
        "Arjun Sharma", "Priya Nair", "Rohit Das",
        "Sneha Patel", "Karan Mehta", "Divya Rao"
    ],
    "Email": [
        "arjun.sharma@email.com", "priya.nair@email.com", "rohit.das@email.com",
        "sneha.patel@email.com", "karan.mehta@email.com", "divya.rao@email.com"
    ],
    "GPA": [9.1, 8.4, 6.9, 7.8, 9.4, 7.2],
    "Math": [95, 88, 60, 75, 98, 70],
    "Python": [92, 85, 55, 80, 96, 65],
    "DSA": [90, 78, 50, 72, 95, 60],
    "Machine_Learning": [88, 70, 45, 65, 97, 55],
    "DBMS": [85, 82, 70, 68, 88, 75],
    "Communication": [80, 90, 75, 85, 72, 88],
    "Projects_Count": [5, 3, 1, 2, 6, 2],
    "Internships": [2, 1, 0, 1, 3, 1],
    "Backlogs": [0, 0, 3, 1, 0, 2],
    "Graduation_Year": [2024, 2024, 2024, 2024, 2024, 2024],
    "College": [
        "IIT Bombay", "NIT Trichy", "Local Engineering College",
        "VIT Vellore", "IIT Delhi", "Manipal Institute"
    ]
}

df = pd.DataFrame(data)
os.makedirs("/mnt/user-data/outputs/test_data", exist_ok=True)
df.to_csv("/mnt/user-data/outputs/test_data/candidates.csv", index=False)
print("CSV saved")
print(df.to_string())