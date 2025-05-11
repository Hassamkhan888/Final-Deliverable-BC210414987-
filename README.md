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











