🍽️ KarachiBites – Restaurant Chatbot (NLP-Powered Virtual Assistant)

Welcome to the KarachiBites Chatbot Project! 🍔✨
This AI-powered virtual assistant, built using Dialogflow, simulates a human-like waiter, making your dining experience interactive and convenient.

It helps customers:

🥡 Place Food Orders

🕰️ Check Order Status

🍴 Browse the Menu

📅 Book Tables

💬 Get Instant Support

📝 Leave Feedback

The chatbot enhances customer convenience while reducing staff workload, offering a smooth and interactive dining experience.

🚀 Project Overview

This is an NLP-based chatbot developed using Dialogflow + FastAPI + MySQL + Frontend (HTML/JS/React) for KarachiBites, a fictional restaurant.

The chatbot assists users with:

🍔 Ordering Food & Checking Status

📜 Checking Menu Availability

🛋️ Booking Tables

🤖 Answering Common Questions

📝 Collecting Customer Feedback

By leveraging NLP, the bot delivers a seamless and smart experience, improving both customer satisfaction and operational efficiency. 🧠💡


🛠️ Setup Instructions

🔹 1. Clone the Repository

 [KarachiBites Chatbot GitHub](https://github.com/Hassamkhan888/Final-Deliverable-BC210414987-.git)
 
 git clone https://github.com/Hassamkhan888/Final-Deliverable-BC210414987-.git
cd Final-Deliverable-BC210414987-


🔹 2. Backend (FastAPI + MySQL)

Create Python Environment

python -m venv venv

venv\Scripts\activate

Resturant_db

Configure MySQL

Create a database (e.g., karachibites_db)

Import the provided .sql schema

Update credentials in backend code

Run FastAPI Backend

uvicorn app:app --reload --port 5000


3. Connect with Dialogflow

Download the Agent ZIP

👉 [KarachiBites_Agent.zip](https://github.com/Hassamkhan888/Final-Deliverable-BC210414987-/blob/5c8f538710772b28ae14972e8a114379cd3588e5/dialogflow_agent.zip)

Import in Dialogflow Console

Go to Agent Settings → Export and Import → Restore from ZIP

Upload the downloaded dialogflow_agent.zip

Webhook Integration (ngrok)

Start backend server on port 5000

Run ngrok:

Copy generated URL (e.g., https://abc123.ngrok.io)

In Dialogflow → Fulfillment → Webhook, set URL:

https://abc123.ngrok.io/webhook

Save and enable ✅

4. Frontend

Open index.html in browser

or

Connect frontend to backend routes for dynamic functionality

5. Admin Panel

If admin panel is in /admin folder:

Navigate to folder

cd admin

Install dependencies

npm install

Run development server

npm run dev

Open in browser

http://localhost:3000

Quick Demo Run

For a fast demo:

# Backend
uvicorn app:app --reload --port 5000

# Start ngrok (new terminal)
ngrok http 5000

# Admin Panel
cd admin
npm run dev


Then:

Import Dialogflow agent ZIP

Set webhook to ngrok URL

Open index.html or admin panel → start chatting 🎉

🧠 How It Works

User Interaction → customer chats on website

Intent Detection → Dialogflow extracts intent & entities

Backend Processing → FastAPI + MySQL handle requests

Response → Sent back to Dialogflow → shown to user

💡 Features

🍔 Menu Browsing

🥡 Order Placement & Tracking

📅 Table Booking

🤖 Support & FAQs

📝 Customer Feedback

🎓 Reflection & Learning

Through KarachiBites, I gained experience in:

🤖 NLP with Dialogflow

⚙️ Backend with FastAPI

🗄️ Database Integration with MySQL

🌐 Frontend (HTML/CSS/JS) + Admin Dashboard

🔄 Real-time API communication

🔮 Future Improvements

🗣️ Voice-Based Interaction

📊 Admin Dashboard Enhancements

🍽️ AI-Based Food Recommendations

📈 Advanced Feedback Analytics

📌 Repository Link

👉 KarachiBites Chatbot GitHub
📌 Repository Link

KarachiBites Chatbot GitHub: https://github.com/Hassamkhan888/Final-Deliverable-BC210414987-

📸 Screenshots
Here are some screenshots of the KarachiBites Chatbot in action:

![image](https://github.com/user-attachments/assets/538ebfee-921c-418f-a96c-2e0b0ecb518c)

![image](https://github.com/user-attachments/assets/9852da2e-a764-4aa9-9e9f-af460b216b57)

![image](https://github.com/user-attachments/assets/cfb9df72-6a14-44d6-a2fc-c91f87ba144f)

![image](https://github.com/user-attachments/assets/0169711c-8ffb-44ac-8290-4f7732890586)

![image](https://github.com/user-attachments/assets/964c5ea3-be8a-4419-9184-3bd280bde0fc)

![image](https://github.com/user-attachments/assets/5231384c-420f-42b0-85fc-3cf13fcd67b5)

![image](https://github.com/user-attachments/assets/df8f69aa-6768-4b88-8931-fe5ea231c67d)

![image](https://github.com/user-attachments/assets/b3538d2f-27b9-4fe6-90e7-e5abe163993b)

![image](https://github.com/user-attachments/assets/46522216-9bc6-4b47-88bb-d1795eab6baa)

![image](https://github.com/user-attachments/assets/fd8524a4-46a1-4718-abc1-80ab8d1abd95)

![image](https://github.com/user-attachments/assets/c6490aae-c495-46e7-8285-1359116a1546)

![image](https://github.com/user-attachments/assets/106c9aad-548a-4ac9-894b-ff85d68cdad9)
