🍽️ Restaurant Chatbot – NLP-Powered Virtual Assistant

Welcome to the Restaurant Chatbot Project! This AI-powered virtual assistant, built using Dialogflow, simulates a human-like waiter. It helps customers:

🧾 Place food orders

📖 Browse the menu

📅 Book tables

🙋 Get instant support

📝 Leave feedback

The chatbot enhances customer convenience while reducing staff workload, offering a smooth and interactive dining experience.


🚀 Project Overview

This project is an NLP-based chatbot built using Dialogflow, tailored for restaurants. It assists users in:

🧾 Ordering food

📋 Checking menu availability

📆 Booking tables

❓ Answering common questions

💬 Collecting customer feedback

With natural language conversations, the bot offers a seamless and friendly experience, improving both customer satisfaction and operational efficiency.


🛠️ Setup Instructions

Follow these steps to run the project on your local machine:

📥 Clone the repository

git clone <your-repo-link>

🐍 Set up the Python environment


pip install -r requirements.txt

🗄️ Configure the MySQL database

Create a new MySQL database

Import the provided SQL schema

Update database credentials in the backend code

🤖 Integrate Dialogflow

Import the Dialogflow agent (.zip or .json)

Set up intents and entities

Generate a service account key for API communication

🔌 Run the FastAPI backend


uvicorn app:app --reload

🌐 Launch the frontend

Open the HTML file in your browser

Or connect it to FastAPI routes for full functionality

⚠️ Make sure your Dialogflow webhook is connected to your local or deployed backend URL.



🧠 Chatbot + Dialogflow Integration

Here's how everything connects:

👤 User Interaction: The customer talks to the chatbot through the website or app.

🔍 Intent Detection: Dialogflow detects user intent and extracts key info (like food item or size).

🔁 Webhook Trigger: Dialogflow sends a webhook call to the FastAPI backend.

🧮 Backend Processing: API logic runs, interacts with the MySQL database, and handles the request.

💬 Response Generation: A response is sent back to Dialogflow and shown to the user.

🧾 Chatbot Features:
📖 Menu Browsing

🛒 Order Placement

📦 Order Tracking

📅 Table Booking

🆘 Support & FAQs


🎓 Reflection and Learning

This project offered a deep dive into:

🤖 Natural language processing with Dialogflow

⚙️ Backend development using FastAPI

🗄️ Database integration using MySQL

🎨 Frontend creation with HTML, CSS, and JavaScript

🔄 Real-time interaction handling

It also improved my understanding of:

💡 User-centered design

🧠 How AI can automate tasks traditionally performed by humans


🔮 Future Work

Here’s what’s planned for upcoming improvements:

🎙️ Voice-Based Interaction – Let users talk to the bot instead of typing

🖥️ Admin Dashboard – A backend panel for restaurant staff to manage orders in real time

🍔 AI-Based Food Recommendations – Smart suggestions based on user history

⭐ Enhanced Feedback System – Collect and analyze reviews for better service


