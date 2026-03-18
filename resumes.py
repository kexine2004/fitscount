from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import os

OUT = "/mnt/user-data/outputs/test_data"
os.makedirs(OUT, exist_ok=True)

candidates = [
    {
        "filename": "ArjunSharma.pdf",
        "name": "Arjun Sharma",
        "email": "arjun.sharma@email.com",
        "phone": "+91-9876543210",
        "summary": "Passionate Data Scientist with strong foundations in ML, deep learning, and Python. IIT Bombay graduate with hands-on experience in production ML systems.",
        "skills": "Python, TensorFlow, PyTorch, Scikit-learn, SQL, Docker, AWS, Git, Pandas, NumPy, FastAPI, Spark",
        "experience": [
            ("Data Science Intern", "Google India", "May 2023 – Aug 2023",
             "Built an NLP pipeline for sentiment analysis on 10M+ reviews. Improved model accuracy by 12% using BERT fine-tuning. Deployed model via FastAPI on GCP."),
            ("ML Research Intern", "IIT Bombay AI Lab", "Dec 2022 – Feb 2023",
             "Implemented Graph Neural Networks for molecule property prediction. Published findings in an international conference workshop."),
        ],
        "projects": [
            ("Stock Price Predictor", "LSTM + Transformer hybrid model for NSE stock forecasting. Achieved RMSE of 2.3 on test set. Deployed as a web app with Streamlit."),
            ("Face Recognition Attendance System", "Real-time attendance using OpenCV + FaceNet. 98.7% accuracy on 500 student dataset."),
            ("RAG Chatbot for College FAQ", "Built a retrieval-augmented chatbot using LangChain + Chroma + GPT-4. Reduced support queries by 40%."),
            ("Image Segmentation for Medical Imaging", "U-Net implementation for tumour detection. Used for a hackathon, won 1st place."),
            ("Fraud Detection Pipeline", "XGBoost + SMOTE pipeline for credit card fraud detection on 1M transaction dataset."),
        ],
        "education": "B.Tech Computer Science | IIT Bombay | GPA: 9.1/10 | 2020–2024",
        "achievements": "JEE Advanced AIR 312 | Google Summer of Code 2023 | Smart India Hackathon Winner 2022",
    },
    {
        "filename": "PriyaNair.pdf",
        "name": "Priya Nair",
        "email": "priya.nair@email.com",
        "phone": "+91-9876501234",
        "summary": "Full-stack developer with strong communication skills and interest in AI/ML. NIT Trichy graduate with experience in web development and data analysis.",
        "skills": "Python, JavaScript, React, Node.js, SQL, MongoDB, Scikit-learn, Tableau, REST APIs, Git",
        "experience": [
            ("Software Development Intern", "Infosys", "Jun 2023 – Aug 2023",
             "Developed REST APIs for a banking portal using Node.js and MongoDB. Improved API response time by 30% through query optimization."),
        ],
        "projects": [
            ("Sales Dashboard", "Interactive Tableau dashboard for retail sales analysis. Used by 3 retail managers for weekly reporting."),
            ("Student Portal Web App", "Full-stack MERN application for college student management. 500+ active users."),
            ("Twitter Sentiment Analyzer", "Python + VADER + Tweepy pipeline to track brand sentiment. Visualized results with Plotly."),
        ],
        "education": "B.Tech IT | NIT Trichy | GPA: 8.4/10 | 2020–2024",
        "achievements": "Best Outgoing Student Award 2024 | TCS CodeVita Round 2 Qualifier",
    },
    {
        "filename": "RohitDas.pdf",
        "name": "Rohit Das",
        "email": "rohit.das@email.com",
        "phone": "+91-9812345678",
        "summary": "Computer science graduate looking for opportunities in software development. Basic knowledge of Python and web technologies.",
        "skills": "Python (basic), HTML, CSS, Java (basic), MS Office",
        "experience": [],
        "projects": [
            ("Personal Portfolio Website", "Simple HTML/CSS portfolio website showcasing personal projects."),
        ],
        "education": "B.Tech CSE | Local Engineering College | GPA: 6.9/10 | 2020–2024",
        "achievements": "Participated in college tech fest 2023",
    },
    {
        "filename": "SnehaPatel.pdf",
        "name": "Sneha Patel",
        "email": "sneha.patel@email.com",
        "phone": "+91-9845612300",
        "summary": "Aspiring data analyst with solid Python skills and growing interest in machine learning. VIT graduate with good communication and presentation abilities.",
        "skills": "Python, Pandas, NumPy, Matplotlib, SQL, Power BI, Excel, Scikit-learn (beginner), Git",
        "experience": [
            ("Data Analyst Intern", "Wipro", "Jul 2023 – Sep 2023",
             "Performed EDA on customer churn dataset of 50K records. Created Power BI dashboards for business stakeholders. Wrote SQL queries for automated reporting."),
        ],
        "projects": [
            ("Customer Churn Prediction", "Logistic Regression + Random Forest model with 78% accuracy on telecom dataset."),
            ("E-commerce Sales Analysis", "End-to-end EDA and visualization project using Pandas and Seaborn."),
        ],
        "education": "B.Tech CSE | VIT Vellore | GPA: 7.8/10 | 2020–2024",
        "achievements": "2nd Place – VIT Data Analytics Hackathon 2023 | Google Data Analytics Certificate",
    },
    {
        "filename": "KaranMehta.pdf",
        "name": "Karan Mehta",
        "email": "karan.mehta@email.com",
        "phone": "+91-9900112233",
        "summary": "Top-performing AI/ML engineer from IIT Delhi with exceptional academic record and multiple research publications. Specialist in deep learning, NLP, and MLOps.",
        "skills": "Python, PyTorch, TensorFlow, HuggingFace, LangChain, Kubernetes, Docker, MLflow, AWS SageMaker, Spark, Scala, SQL, C++",
        "experience": [
            ("AI Research Intern", "Microsoft Research India", "May 2023 – Aug 2023",
             "Researched efficient fine-tuning of LLMs using LoRA and QLoRA. Reduced training cost by 60% while maintaining 97% of baseline performance. Co-authored a paper submitted to NeurIPS 2024."),
            ("Data Science Intern", "Flipkart", "Dec 2022 – Feb 2023",
             "Built a real-time recommendation engine using collaborative filtering and matrix factorization. Served 1M+ users. A/B tested model variants leading to 8% CTR improvement."),
            ("ML Engineering Intern", "Ola", "May 2022 – Jul 2022",
             "Developed ETA prediction model using gradient boosting. Integrated into production with 95% accuracy within 2-minute window."),
        ],
        "projects": [
            ("LLM-powered Code Review Assistant", "Fine-tuned CodeLlama on internal codebase for automated PR reviews. Reduced review time by 35%."),
            ("Multi-modal Sentiment Analysis", "Combined text + image features using late fusion for social media sentiment. SOTA on custom benchmark."),
            ("AutoML Pipeline", "Built end-to-end AutoML system with hyperparameter tuning, feature selection, and model deployment."),
            ("Real-time Object Detection Edge Device", "YOLOv8 optimized for Raspberry Pi using TensorRT. 30 FPS on edge hardware."),
            ("Federated Learning Framework", "Privacy-preserving ML across distributed hospital data. Published in IEEE conference."),
            ("Knowledge Graph for Drug Discovery", "NLP + GNN pipeline to extract drug-protein interactions from research papers."),
        ],
        "education": "B.Tech CSE (AI Specialization) | IIT Delhi | GPA: 9.4/10 | 2020–2024",
        "achievements": "JEE Advanced AIR 48 | NeurIPS 2024 Paper Submission | Kaggle Master (Top 1%) | ACM ICPC Regionalist | NVIDIA Deep Learning Fellowship",
    },
    {
        "filename": "DivyaRao.pdf",
        "name": "Divya Rao",
        "email": "divya.rao@email.com",
        "phone": "+91-9988776655",
        "summary": "Graduate with decent academic background and interest in data science. Looking to transition into analytics or data roles. Good soft skills and team player.",
        "skills": "Python (intermediate), SQL, Excel, Tableau, Basic ML concepts, Communication, Leadership",
        "experience": [
            ("Data Entry & Analysis Intern", "Local Startup", "Jun 2023 – Jul 2023",
             "Maintained Excel sheets and created basic charts for weekly reporting. Assisted in data cleaning for a customer database."),
        ],
        "projects": [
            ("House Price Prediction", "Linear regression model on Kaggle Boston Housing dataset. Basic EDA included."),
            ("Student Grade Analysis", "Excel-based analysis of class performance with charts and pivot tables."),
        ],
        "education": "B.Tech CSE | Manipal Institute | GPA: 7.2/10 | 2020–2024",
        "achievements": "Cultural Secretary, College Student Council 2022–23",
    },
]


def build_pdf(c):
    path = os.path.join(OUT, c["filename"])
    doc  = SimpleDocTemplate(path, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()

    NAME  = ParagraphStyle("NAME",  fontSize=20, fontName="Helvetica-Bold",
                           textColor=colors.HexColor("#1a237e"), alignment=TA_CENTER, spaceAfter=4)
    META  = ParagraphStyle("META",  fontSize=9,  fontName="Helvetica",
                           textColor=colors.grey, alignment=TA_CENTER, spaceAfter=10)
    SUMM  = ParagraphStyle("SUMM",  fontSize=10, fontName="Helvetica",
                           textColor=colors.HexColor("#333333"), spaceAfter=8, leading=14)
    SEC   = ParagraphStyle("SEC",   fontSize=12, fontName="Helvetica-Bold",
                           textColor=colors.HexColor("#283593"), spaceBefore=10, spaceAfter=4)
    BODY  = ParagraphStyle("BODY",  fontSize=9.5, fontName="Helvetica",
                           textColor=colors.HexColor("#222222"), leading=14, spaceAfter=4)
    BOLD  = ParagraphStyle("BOLD",  fontSize=10, fontName="Helvetica-Bold",
                           textColor=colors.HexColor("#111111"), spaceAfter=2)
    SMALL = ParagraphStyle("SMALL", fontSize=8.5, fontName="Helvetica",
                           textColor=colors.grey, spaceAfter=3)

    story = []

    story.append(Paragraph(c["name"], NAME))
    story.append(Paragraph(f'{c["email"]}  •  {c["phone"]}', META))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#283593")))
    story.append(Spacer(1, 6))

    story.append(Paragraph("PROFESSIONAL SUMMARY", SEC))
    story.append(Paragraph(c["summary"], SUMM))

    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Paragraph("TECHNICAL SKILLS", SEC))
    story.append(Paragraph(c["skills"], BODY))

    if c["experience"]:
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        story.append(Paragraph("WORK EXPERIENCE", SEC))
        for title, company, period, desc in c["experience"]:
            story.append(Paragraph(f"{title} — {company}", BOLD))
            story.append(Paragraph(period, SMALL))
            story.append(Paragraph(desc, BODY))
            story.append(Spacer(1, 4))

    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Paragraph("PROJECTS", SEC))
    for pname, pdesc in c["projects"]:
        story.append(Paragraph(f"▸ {pname}", BOLD))
        story.append(Paragraph(pdesc, BODY))

    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Paragraph("EDUCATION", SEC))
    story.append(Paragraph(c["education"], BODY))

    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Paragraph("ACHIEVEMENTS & CERTIFICATIONS", SEC))
    story.append(Paragraph(c["achievements"], BODY))

    doc.build(story)
    print(f"  ✅ {c['filename']}")


print("Generating PDFs...")
for cand in candidates:
    build_pdf(cand)
print("Done!")