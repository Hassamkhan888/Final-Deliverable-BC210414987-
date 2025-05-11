🍽️ KarachiBites – Restaurant Chatbot (NLP-Powered Virtual Assistant)

Welcome to the KarachiBites Chatbot Project! 🍔✨
This AI-powered virtual assistant, built using Dialogflow, simulates a human-like waiter, making your dining experience interactive and convenient. It helps customers:

🥡 Place Food Orders

🍴 Browse the Menu

📅 Book Tables

💬 Get Instant Support

📝 Leave Feedback

The chatbot enhances customer convenience while reducing staff workload, offering a smooth and interactive dining experience.

🚀 Project Overview

This is an NLP-based chatbot developed using Dialogflow and FastAPI, specifically designed for KarachiBites, a fictional restaurant. The chatbot assists users with various tasks:

🍔 Ordering Food

📜 Checking Menu Availability

🛋️ Booking Tables

🤖 Answering Common Questions

📝 Collecting Customer Feedback

By leveraging natural language processing, the bot delivers a seamless, smart experience, improving both customer satisfaction and operational efficiency. 🧠💡


🛠️ Setup Instructions

Follow these steps to run the KarachiBites Chatbot locally on your machine:

Clone the Repository

git clone https://github.com/Hassamkhan888/Final-Deliverable-BC210414987-.git
cd Final-Deliverable-BC210414987-

Set Up the Python Environment
Install the required libraries:

pip install -r requirements.txt

Configure the MySQL Database

Create a new MySQL database

Import the provided SQL schema

Update the database credentials in the backend code

Integrate Dialogflow

Import the Dialogflow agent (in .zip or .json format)

Set up intents and entities

Generate a service account key for API communication

Run the FastAPI Backend
Start the backend server:

uvicorn app:app --reload

Launch the Frontend

Open the index.html file in your browser

Or connect it to the FastAPI routes for full functionality

Important: Ensure your Dialogflow webhook is pointing to your backend URL (local or deployed).

🧠 How It Works

User Interaction
The customer talks to the chatbot through the website.

Intent Detection
Dialogflow detects user intent and extracts relevant information (e.g., food item or quantity).

Backend Processing
Dialogflow sends a webhook request to the FastAPI backend, which processes the request and interacts with the MySQL database.

Response Handling
A response is sent back to Dialogflow and displayed to the user in real-time.

💡 Chatbot Features

🍔 Menu Browsing: View the full menu with available items

🥡 Order Placement: Place orders directly through the chatbot

🕰️ Order Tracking: Get real-time updates on order status

📅 Table Booking: Reserve a table for dining in

🤖 Support & FAQs: Get instant support for common queries

📝 Customer Feedback Collection: Share feedback after dining

🎓 Reflection and Learning

Through KarachiBites, I gained practical experience in the following:

🤖 Natural Language Processing with Dialogflow

⚙️ Backend Development with FastAPI

🗄️ Database Integration using MySQL

🌐 Frontend Design with HTML, CSS, and JavaScript

🔄 Real-time API Interaction for seamless communication

This project significantly enhanced my understanding of:

Human-computer interaction through conversational AI

Automation of customer service with AI

Restaurant workflow and logic

🔮 Future Improvements

🗣️ Voice-Based Chatbot Interaction: Allow voice commands for hands-free interaction

📊 Admin Dashboard: A dashboard for restaurant staff to manage orders, tables, and feedback

🍽️ AI-Based Food Recommendations: Suggest personalized food options based on customer preferences

📈 Advanced Feedback Analytics: Better analytics and reporting on customer feedback for restaurant improvement

📌 Repository Link

KarachiBites Chatbot GitHub: https://github.com/Hassamkhan888/Final-Deliverable-BC210414987-

📸 Screenshots

Here are some screenshots of the KarachiBites Chatbot in action:


![image](https://github.com/user-attachments/assets/6683eb42-d5a3-4c19-aca1-1539bc917495)

![image](https://github.com/user-attachments/assets/1a37c4e1-6291-4c31-89c4-c00c78b4ef01)

![image](https://github.com/user-attachments/assets/23902047-d787-4387-bf9e-9ecbc57ed6ab)

![image](https://github.com/user-attachments/assets/bb28147b-9f0b-468b-83df-0902ff3fb34f)

![image](https://github.com/user-attachments/assets/2337e91b-9b8c-46eb-861a-e5555d98499e)

![image](https://github.com/user-attachments/assets/ae76c3bb-98f6-432f-9896-1fa63b2897e8)

![image](https://github.com/user-attachments/assets/e27dcc6e-a048-4b33-958f-bd5d55671dbd)

![image](https://github.com/user-attachments/assets/598a3b7e-a514-46db-990e-a9485564fe8b)

![image](https://github.com/user-attachments/assets/0497637b-5b1f-4cab-a607-76beabfdedc3)

![image](https://github.com/user-attachments/assets/1fea5814-f60b-45f0-ba83-125535142e31)

![image](https://github.com/user-attachments/assets/ce6e4f34-7d96-425f-a925-b016824a25eb)

![image](https://github.com/user-attachments/assets/a2aa4cf0-d1fa-4657-84f2-ef222b66ef44)











