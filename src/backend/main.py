from fastapi import FastAPI, Request
import re
from fastapi.responses import JSONResponse
import logging
import uvicorn
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from database import (
    create_order, get_order_status, get_menu_item_details, 
    create_support_ticket, create_reservation, submit_customer_feedback,
    extract_name_value
)
from order_utils import (
    extract_order_details, extract_order_id, extract_dish_item,
    is_price_query, is_stock_query, extract_item_and_intent, 
    normalize_item_name, extract_support_request_details,
    is_technical_support_request, is_feedback_request
)
from response_templates import (
    error_response, order_success_response, ask_for_order_items,
    ask_for_order_number, order_status_response, product_price_response,
    product_stock_response, product_full_response, support_ticket_response,
    reservation_success_response, ask_reservation_question,
    feedback_prompt_name_response, feedback_prompt_phone_response,
    feedback_prompt_text_response, feedback_submitted_response,
    feedback_cancelled_response, technical_support_name_response,
    technical_support_phone_response, technical_support_issue_response,
    technical_support_description_response, technical_support_cancelled_response
)
from fastapi import FastAPI
from admin import router as admin_router  # Make sure this matches your file name
import uvicorn
from fastapi.requests import Request  # Needed if using Request in webhook
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Restaurant Admin API")

origins = [ "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Admin router
app.include_router(admin_router, prefix="/admin", tags=["Admin"])

@app.get("/")
def root():
    return {"message": "Restaurant Admin API is running!"}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation state tracking
conversation_state: Dict[str, Dict[str, Any]] = {}

def extract_guest_count(user_input: str) -> Optional[int]:
    """Extract guest count from user input with better pattern matching"""
    patterns = [
        r'(\d+)\s*(?:guests?|people|persons?)',
        r'(\d+)\s*(?:pax)',
        r'(?:for|party of)\s*(\d+)',
        r'^(\d+)$',
    ]
    
    user_input = user_input.lower().strip()
    
    for pattern in patterns:
        match = re.search(pattern, user_input)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                continue
    
    return None

def clear_all_contexts(session_id: str):
    """Clear all contexts for a fresh start"""
    if session_id in conversation_state:
        conversation_state[session_id]["reservation"]["awaiting"] = None
        conversation_state[session_id]["order"]["awaiting"] = None
        conversation_state[session_id]["feedback"]["awaiting"] = None
        conversation_state[session_id]["support"]["awaiting"] = None

def clear_reservation_context(session_id: str):
    """Clear reservation context for a session"""
    if session_id in conversation_state:
        conversation_state[session_id]["reservation"] = {
            "name": None,
            "phone_number": None,
            "guests": None,
            "datetime": None,
            "retry_count": 0,
            "awaiting": None
        }

def clear_order_context(session_id: str):
    """Clear order context for a session"""
    if session_id in conversation_state:
        conversation_state[session_id]["order"] = {
            "name": None,
            "phone_number": None,
            "items": [],
            "awaiting": None
        }

def clear_feedback_context(session_id: str):
    """Clear feedback context for a session"""
    if session_id in conversation_state:
        conversation_state[session_id]["feedback"] = {
            "name": None,
            "phone_number": None,
            "text": None,
            "awaiting": None
        }

def clear_support_context(session_id: str):
    """Clear support context for a session"""
    if session_id in conversation_state:
        conversation_state[session_id]["support"] = {
            "name": None,
            "phone_number": None,
            "issue_type": None,
            "description": None,
            "awaiting": None
        }

def extract_datetime_info(text: str) -> Optional[Dict[str, Any]]:
    """Extract date and time information from text"""
    patterns = [
        r'(\d+)\s+([a-z]{3,})\s+(\d{2,4})\s+(\d{1,2})\s+([ap]m)',
        r'(\d{1,2})/(\d{1,2})/(\d{2,4})\s+(\d{1,2})\s+([ap]m)',
        r'([a-z]{3,})\s+(\d{1,2})(?:,|\s+)?\s+(\d{2,4})(?:\s+at)?\s+(\d{1,2})\s+([ap]m)',
        r'(\d+)\s+([a-z]{3,})\s+(\d{1,2})\s+([ap]m)',
    ]
    
    text = text.lower()
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return {
                'match': match,
                'pattern': pattern
            }
    
    return None

def ask_for_order_name() -> JSONResponse:
    return JSONResponse(
        content={
            "fulfillmentText": "👤 May I have your name, please?",
            "payload": {
                "richContent": [[{
                    "type": "chips",
                    "options": [
                        {"text": "Main Menu", "intent": "Main_Menu"}
                    ]
                }]]
            }
        }
    )

def ask_for_order_phone() -> JSONResponse:
    return JSONResponse(
        content={
            "fulfillmentText": "📱 Can you share your phone number?",
            "payload": {
                "richContent": [[{
                    "type": "chips",
                    "options": [
                        {"text": "Main Menu", "intent": "Main_Menu"}
                    ]
                }]]
            }
        }
    )

def ask_for_reservation_name() -> JSONResponse:
    return JSONResponse(
        content={
            "fulfillmentText": "👤 May I have your name, please?",
            "payload": {
                "richContent": [[{
                    "type": "chips",
                    "options": [
                        {"text": "Main Menu", "intent": "Main_Menu"}
                    ]
                }]]
            }
        }
    )

def ask_for_reservation_phone() -> JSONResponse:
    return JSONResponse(
        content={
            "fulfillmentText": "📱 Can you share your phone number?",
            "payload": {
                "richContent": [[{
                    "type": "chips",
                    "options": [
                        {"text": "Main Menu", "intent": "Main_Menu"}
                    ]
                }]]
            }
        }
    )

def improved_ask_for_order_items() -> JSONResponse:
    """Improved order items request with better examples"""
    return JSONResponse(
        content={
            "fulfillmentText": "🍽️ What would you like to order today? Please specify quantity and items (Example: '2 chicken biryani and 1 pepsi' or '10 burgers')",
            "payload": {
                "richContent": [[{
                    "type": "chips",
                    "options": [
                        {"text": "🍗 2 Chicken Biryani + 🥤 1 Pepsi"},
                        {"text": "🍔 1 Beef Burger + 🥤 2 Colas"},
                        {"text": "🍔 5 Burgers"},
                        {"text": "🍖 1 Mutton Karahi + 🫓 2 Naan"},
                        {"text": "📝 Custom order..."}
                    ]
                }]]
            }
        }
    )

@app.post("/webhook")
async def webhook(request: Request):
    try:
        req = await request.json()
        query_result = req.get("queryResult", {})
        user_input = query_result.get("queryText", "").strip().lower()
        session_id = req.get("session", "default").split('/')[-1]
        
        # Initialize session if not exists
        if session_id not in conversation_state:
            conversation_state[session_id] = {
                "context": None,
                "awaiting_order_id": False,
                "cart": [],
                "reservation": {
                    "name": None,
                    "phone_number": None,
                    "guests": None,
                    "datetime": None,
                    "retry_count": 0,
                    "awaiting": None
                },
                "order": {
                    "name": None,
                    "phone_number": None,
                    "items": [],
                    "awaiting": None
                },
                "feedback": {
                    "name": None,
                    "phone_number": None,
                    "text": None,
                    "awaiting": None
                },
                "support": {
                    "name": None,
                    "phone_number": None,
                    "issue_type": None,
                    "description": None,
                    "awaiting": None
                }
            }

        session = conversation_state[session_id]

        # Debug logging
        logger.info(f"Incoming request - Intent: {query_result.get('intent', {}).get('displayName')}")
        logger.info(f"Parameters: {query_result.get('parameters', {})}")
        logger.info(f"Session ID: {session_id}")
        logger.info(f"User input: {user_input}")
        logger.info(f"Order context: {session['order']}")
        
        # Extract intent and parameters for cleaner code
        intent = query_result.get("intent", {}).get("displayName", "")
        parameters = query_result.get("parameters", {})

        # Handle order requests that should start fresh
        if user_input in ["new order", "place order"] and session["order"]["awaiting"] not in ["name", "phone_number"]:
            logger.info("Starting new order flow")
            clear_order_context(session_id)
            clear_all_contexts(session_id)  # Clear other contexts too
            order_context = session["order"]
            order_context["awaiting"] = "name"
            return ask_for_order_name()

        # PRIORITY: Check active contexts first before intent matching
        reservation_context = session["reservation"]
        order_context = session["order"]
        feedback_context = session["feedback"]
        support_context = session["support"]
        
        # Handle reservation context states
        if reservation_context["awaiting"] == "name":
            logger.info(f"Reservation: collecting name - {user_input}")
            reservation_context["name"] = user_input
            reservation_context["awaiting"] = "phone_number"
            return ask_for_reservation_phone()
            
        elif reservation_context["awaiting"] == "phone_number":
            logger.info(f"Reservation: collecting phone - {user_input}")
            phone_cleaned = re.sub(r'\D', '', user_input)
            if phone_cleaned and len(phone_cleaned) >= 6:
                reservation_context["phone_number"] = phone_cleaned
                reservation_context["awaiting"] = "guest_count"
                logger.info(f"Reservation: phone accepted, moving to guest_count")
                return ask_reservation_question("guest_count")
            else:
                logger.warning(f"Reservation: invalid phone - {user_input}")
                return JSONResponse(
                    content={
                        "fulfillmentText": "❌ Please provide a valid phone number (at least 6 digits). Example: 03123456789",
                        "payload": {
                            "richContent": [[{
                                "type": "chips",
                                "options": [
                                    {"text": "Main Menu", "intent": "Main_Menu"}
                                ]
                            }]]
                        }
                    }
                )
                
        elif reservation_context["awaiting"] == "guest_count":
            logger.info(f"Reservation: collecting guest count - {user_input}")
            guests = extract_guest_count(user_input)
            if guests is not None:
                if 1 <= guests <= 50:
                    reservation_context["guests"] = guests
                    reservation_context["awaiting"] = "datetime"
                    return ask_reservation_question("reserve_date_time")
                else:
                    return JSONResponse(
                        content={
                            "fulfillmentText": f"❌ I can only accommodate 1-20 guests per reservation. You requested {guests} guests. Please choose a number between 1 and 20.",
                            "payload": {
                                "richContent": [[{
                                    "type": "chips",
                                    "options": [
                                        {"text": "👥 10 guests"},
                                        {"text": "👥 15 guests"}, 
                                        {"text": "👥 20 guests"},
                                        {"text": "Main Menu", "intent": "Main_Menu"}
                                    ]
                                }]]
                            }
                        }
                    )
            else:
                return JSONResponse(
                    content={
                        "fulfillmentText": "👥 I need a number of guests for your reservation. Please tell me how many people will be dining (1-20 guests).",
                        "payload": {
                            "richContent": [[{
                                "type": "chips",
                                "options": [
                                    {"text": "👥 2 guests"},
                                    {"text": "👥 4 guests"},
                                    {"text": "👥 6 guests"},
                                    {"text": "👥 8 guests"}
                                ]
                            }]]
                        }
                    }
                )
                
        elif reservation_context["awaiting"] == "datetime":
            logger.info(f"Reservation: collecting datetime - {user_input}")
            if any(month in user_input for month in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]):
                success, message, reservation_id = create_reservation_with_customer_info(
                    guests=reservation_context["guests"],
                    datetime_param=user_input,
                    name=reservation_context["name"],
                    phone_number=reservation_context["phone_number"]
                )
                
                if success:
                    guests = reservation_context["guests"]
                    clear_reservation_context(session_id)
                    return reservation_success_response(
                        reservation_id=reservation_id,
                        guests=guests,
                        date="Selected Date",
                        time="Selected Time"
                    )
                else:
                    return error_response("reservation_failed", message)
            else:
                return ask_reservation_question("reserve_date_time")
                
        # Handle order context states  
        if order_context["awaiting"] == "name":
            logger.info(f"Order: collecting name - {user_input}")
            order_context["name"] = user_input
            order_context["awaiting"] = "phone_number"
            return ask_for_order_phone()
            
        elif order_context["awaiting"] == "phone_number":
            logger.info(f"Order: collecting phone - {user_input}")
            order_context["phone_number"] = user_input
            order_context["awaiting"] = "items"
            return improved_ask_for_order_items()
            
        elif order_context["awaiting"] == "items":
            logger.info(f"Order: collecting items - {user_input}")
            items = extract_order_details(user_input)
            
            if not items:
                return JSONResponse(
                    content={
                        "fulfillmentText": "❌ I couldn't understand your order. Please tell me what you'd like with quantities (Example: '2 biryani and 1 pepsi', '5 burgers', '3 chicken karahi')",
                        "payload": {
                            "richContent": [[{
                                "type": "chips",
                                "options": [
                                    {"text": "🍗 2 biryani + 🥤 1 pepsi"},
                                    {"text": "🍔 5 burgers"},
                                    {"text": "🍗 3 chicken karahi"},
                                    {"text": "🍔 1 beef burger + 🥤 1 cola"},
                                    {"text": "Main Menu", "intent": "Main_Menu"}
                                ]
                            }]]
                        }
                    }
                )
            
            logger.info(f"Order: items extracted - {items}")
            success, message, order_id = create_order_with_customer_info(
                items=items,
                name=order_context["name"],
                phone_number=order_context["phone_number"]
            )
            
            clear_order_context(session_id)
            
            if not success:
                return error_response("order_creation_failed", message)
            
            return order_success_response(message, order_id, items)

        # Handle feedback context states
        if feedback_context["awaiting"] == "name":
            logger.info(f"Feedback: collecting name - {user_input}")
            feedback_context["name"] = user_input
            feedback_context["awaiting"] = "phone_number"
            return feedback_prompt_phone_response(feedback_context["name"])
            
        elif feedback_context["awaiting"] == "phone_number":
            logger.info(f"Feedback: collecting phone - {user_input}")
            feedback_context["phone_number"] = user_input
            feedback_context["awaiting"] = "feedback_text"
            return feedback_prompt_text_response(feedback_context["name"])
            
        elif feedback_context["awaiting"] == "feedback_text":
            logger.info(f"Feedback: collecting text - {user_input}")
            feedback_context["text"] = user_input
            
            success, message = submit_customer_feedback(
                user_id=session_id,
                name=feedback_context["name"],
                phone_number=feedback_context["phone_number"],
                feedback_text=feedback_context["text"]
            )
            
            name = feedback_context["name"]
            clear_feedback_context(session_id)
            if success:
                return feedback_submitted_response(name)
            else:
                return error_response("feedback_failed", message)
                
        # Handle support context states
        if support_context["awaiting"] == "name":
            logger.info(f"Support: collecting name - {user_input}")
            support_context["name"] = user_input
            support_context["awaiting"] = "phone_number"
            return technical_support_phone_response(support_context["name"])
            
        elif support_context["awaiting"] == "phone_number":
            logger.info(f"Support: collecting phone - {user_input}")
            support_context["phone_number"] = user_input
            support_context["awaiting"] = "issue_type"
            return technical_support_issue_response(support_context["name"])
            
        elif support_context["awaiting"] == "issue_type":
            logger.info(f"Support: collecting issue type - {user_input}")
            
            # Special handling for when user provides issue description instead of type
            if "device" in user_input and "not working" in user_input:
                # User is describing the issue directly
                issue_type = "device"
                support_context["issue_type"] = issue_type
                support_context["description"] = user_input
                
                # Create support ticket immediately since we have all info
                success, message = create_support_ticket(
                    session_id=session_id,
                    name=support_context["name"],
                    phone_number=support_context["phone_number"],
                    issue_type=support_context["issue_type"],
                    description=support_context["description"]
                )
                
                name = support_context["name"]
                description = support_context["description"]
                
                clear_support_context(session_id)
                
                if success:
                    return support_ticket_response(description, name)
                else:
                    return error_response("support_ticket_failed", message)
            
            # Normal flow - extract issue type
            issue_type, _ = extract_support_request_details(user_input)
            support_context["issue_type"] = issue_type
            support_context["awaiting"] = "description"
            return technical_support_description_response(issue_type)
            
        elif support_context["awaiting"] == "description":
            logger.info(f"Support: collecting description - {user_input}")
            support_context["description"] = user_input
            
            success, message = create_support_ticket(
                session_id=session_id,
                name=support_context["name"],
                phone_number=support_context["phone_number"],
                issue_type=support_context["issue_type"],
                description=support_context["description"]
            )
            
            name = support_context["name"]
            description = support_context["description"]
            
            clear_support_context(session_id)
            
            if success:
                return support_ticket_response(description, name)
            else:
                return error_response("support_ticket_failed", message)
                
        # Check if we're in the middle of the support flow and they say "my device is not working"
        if support_context["awaiting"] == "description" and "device" in user_input and "not working" in user_input:
            # We already have name and phone number, just create the ticket with those
            issue_type, _ = extract_support_request_details(user_input)
            
            success, message = create_support_ticket(
                session_id=session_id,
                name=support_context["name"],
                phone_number=support_context["phone_number"],
                issue_type=issue_type or "device",
                description=user_input
            )
            
            name_value = extract_name_value(support_context["name"])
            
            # Clear context
            clear_support_context(session_id)
            
            if success:
                return support_ticket_response(user_input, name_value)
            else:
                return error_response("support_ticket_failed", message)
                
        # Handle technical support requests immediate only when we have collected name and phone
        if support_context["awaiting"] == "issue_type" and "device" in user_input and "not working" in user_input:
            issue_type, _ = extract_support_request_details(user_input)
            
            success, message = create_support_ticket(
                session_id=session_id,
                name=support_context["name"],
                phone_number=support_context["phone_number"],
                issue_type=issue_type or "device",
                description=user_input
            )
            
            name_value = extract_name_value(support_context["name"])
            
            # Clear context
            clear_support_context(session_id)
            
            if success:
                return support_ticket_response(user_input, name_value)
            else:
                return error_response("support_ticket_failed", message)

        # Handle Place Order Intent with name/phone collection
        if intent == "PlaceOrder" or user_input in ["i want to order"]:
            logger.info("Handling PlaceOrder intent")
            order_context = session["order"]
            
            # Clear other contexts when starting order
            clear_all_contexts(session_id)
            
            # Get parameters from Dialogflow
            name = parameters.get("name")
            phone_number = parameters.get("phone-number")
            
            # If both name and phone are provided via parameters
            if name and phone_number:
                order_context["name"] = name
                order_context["phone_number"] = phone_number
                order_context["awaiting"] = "items"
                return improved_ask_for_order_items()
            
            # Handle the staged collection flow
            if order_context["awaiting"] is None:
                if name:
                    order_context["name"] = name
                    order_context["awaiting"] = "phone_number"
                    return ask_for_order_phone()
                else:
                    order_context["awaiting"] = "name"
                    return ask_for_order_name()
                    
            elif order_context["awaiting"] == "name":
                order_context["name"] = user_input
                order_context["awaiting"] = "phone_number"
                return ask_for_order_phone()
                
            elif order_context["awaiting"] == "phone_number":
                order_context["phone_number"] = user_input
                order_context["awaiting"] = "items"
                return improved_ask_for_order_items()

        # Handle reservation flow separately  
        if intent == "MakeReservation" or user_input in ["make reservation", "book reservation", "reservation"]:
            logger.info("Starting reservation flow")
            clear_all_contexts(session_id)
            
            reservation_context = session["reservation"]
            
            # Get parameters from Dialogflow
            name = parameters.get("name")
            phone_number = parameters.get("phone-number")
            guest_count = parameters.get("guest_count")
            reserve_date_time = parameters.get("reserve_date_time")
            
            # If all required info is provided via parameters
            if name and phone_number and guest_count and reserve_date_time:
                success, message, reservation_id = create_reservation_with_customer_info(
                    guests=guest_count,
                    datetime_param=reserve_date_time,
                    name=name,
                    phone_number=phone_number
                )
                
                clear_reservation_context(session_id)
                
                if success:
                    return reservation_success_response(
                        reservation_id=reservation_id,
                        guests=guest_count,
                        date="Date",
                        time="Time"
                    )
                else:
                    return error_response("reservation_failed", message)
            
            # Start the staged collection flow
            if name:
                reservation_context["name"] = name
                reservation_context["awaiting"] = "phone_number"
                logger.info("Reservation: name from parameters, asking for phone")
                return ask_for_reservation_phone()
            else:
                reservation_context["awaiting"] = "name"
                logger.info("Reservation: starting with name request")
                return ask_for_reservation_name()

        # Handle feedback requests outside of direct intent
        if is_feedback_request(user_input) and intent != "GiveCustomerFeedback":
            clear_all_contexts(session_id)
            feedback_context = session["feedback"]
            feedback_context["awaiting"] = "name"
            return feedback_prompt_name_response()

        # Handle technical support requests outside of direct intent
        if is_technical_support_request(user_input) and intent != "Technical_Support":
            clear_all_contexts(session_id)
            support_context = session["support"]
            support_context["awaiting"] = "name"
            return technical_support_name_response()

        # Handle feedback intent
        if intent.startswith("GiveCustomerFeedback"):
            # Clear other contexts
            clear_all_contexts(session_id)
            feedback_context = session["feedback"]
            
            if intent == "GiveCustomerFeedback - skip_name":
                feedback_context["awaiting"] = "phone_number"
                return feedback_prompt_phone_response()
                
            elif intent == "GiveCustomerFeedback - skip_phone":
                feedback_context["awaiting"] = "feedback_text"
                return feedback_prompt_text_response(extract_name_value(feedback_context["name"]))
                
            elif intent == "GiveCustomerFeedback":
                name = parameters.get("name")
                phone_number = parameters.get("phone-number")
                feedback_text = parameters.get("feedback-text")
                
                if name and phone_number and feedback_text:
                    feedback_context["name"] = name
                    feedback_context["phone_number"] = phone_number
                    feedback_context["text"] = feedback_text
                    
                    success, message = submit_customer_feedback(
                        user_id=session_id,
                        name=feedback_context["name"],
                        phone_number=feedback_context["phone_number"],
                        feedback_text=feedback_context["text"]
                    )
                    
                    name_value = extract_name_value(feedback_context["name"])
                    clear_feedback_context(session_id)
                    if success:
                        return feedback_submitted_response(name_value)
                    else:
                        return error_response("feedback_failed", message)
                
                if feedback_context["awaiting"] is None:
                    feedback_context["awaiting"] = "name"
                    return feedback_prompt_name_response()
                    
                elif feedback_context["awaiting"] == "name":
                    feedback_context["name"] = user_input
                    feedback_context["awaiting"] = "phone_number"
                    return feedback_prompt_phone_response(feedback_context["name"])
                    
                elif feedback_context["awaiting"] == "phone_number":
                    feedback_context["phone_number"] = user_input
                    feedback_context["awaiting"] = "feedback_text"
                    return feedback_prompt_text_response(feedback_context["name"])
                    
                elif feedback_context["awaiting"] == "feedback_text":
                    feedback_context["text"] = user_input
                    
                    success, message = submit_customer_feedback(
                        user_id=session_id,
                        name=feedback_context["name"],
                        phone_number=feedback_context["phone_number"],
                        feedback_text=feedback_context["text"]
                    )
                    
                    name = feedback_context["name"]
                    clear_feedback_context(session_id)
                    if success:
                        return feedback_submitted_response(name)
                    else:
                        return error_response("feedback_failed", message)
                
                feedback_context["awaiting"] = "name"
                return feedback_prompt_name_response()

        # Handle technical support intent
        elif intent.startswith("Technical_Support"):
            # Clear other contexts
            clear_all_contexts(session_id)
            support_context = session["support"]
            
            if intent == "Technical_Support - cancel":
                clear_support_context(session_id)
                return technical_support_cancelled_response()
                
            elif intent == "Technical_Support - skip_name":
                support_context["awaiting"] = "phone_number"
                return technical_support_phone_response()
                
            elif intent == "Technical_Support - skip_phone":
                support_context["awaiting"] = "issue_type"
                return technical_support_issue_response(extract_name_value(support_context["name"]))
                
            elif intent == "Technical_Support - issue":
                issue = parameters.get("issue")
                if issue:
                    support_context["issue_type"] = issue
                    support_context["awaiting"] = "description"
                    return technical_support_description_response(issue)
                else:
                    support_context["awaiting"] = "issue_type"
                    return technical_support_issue_response(extract_name_value(support_context["name"]))
                
            elif intent == "Technical_Support":
                name = parameters.get("name")
                phone_number = parameters.get("phone-number")
                issue = parameters.get("issue")
                description = parameters.get("description")
                
                if name and phone_number and issue and description:
                    support_context["name"] = name
                    support_context["phone_number"] = phone_number
                    support_context["issue_type"] = issue
                    support_context["description"] = description
                    
                    success, message = create_support_ticket(
                        session_id=session_id,
                        name=support_context["name"],
                        phone_number=support_context["phone_number"],
                        issue_type=support_context["issue_type"],
                        description=support_context["description"]
                    )
                    
                    name_value = extract_name_value(support_context["name"])
                    description = support_context["description"]
                    
                    clear_support_context(session_id)
                    
                    if success:
                        return support_ticket_response(description, name_value)
                    else:
                        return error_response("support_ticket_failed", message)
                
                if support_context["awaiting"] is None:
                    support_context["awaiting"] = "name"
                    return technical_support_name_response()
                    
                elif support_context["awaiting"] == "name":
                    support_context["name"] = user_input
                    support_context["awaiting"] = "phone_number"
                    return technical_support_phone_response(support_context["name"])
                    
                elif support_context["awaiting"] == "phone_number":
                    support_context["phone_number"] = user_input
                    support_context["awaiting"] = "issue_type"
                    return technical_support_issue_response(support_context["name"])
                    
                elif support_context["awaiting"] == "issue_type":
                    issue_type, _ = extract_support_request_details(user_input)
                    support_context["issue_type"] = issue_type
                    support_context["awaiting"] = "description"
                    return technical_support_description_response(issue_type)
                    
                elif support_context["awaiting"] == "description":
                    support_context["description"] = user_input
                    
                    success, message = create_support_ticket(
                        session_id=session_id,
                        name=support_context["name"],
                        phone_number=support_context["phone_number"],
                        issue_type=support_context["issue_type"],
                        description=support_context["description"]
                    )
                    
                    name = support_context["name"]
                    description = support_context["description"]
                    
                    clear_support_context(session_id)
                    
                    if success:
                        return support_ticket_response(description, name)
                    else:
                        return error_response("support_ticket_failed", message)
                
                support_context["awaiting"] = "name"
                return technical_support_name_response()

        # Check if we're awaiting an order ID
        if session.get("awaiting_order_id"):
            order_id = extract_order_id(user_input)
            if order_id:
                session["awaiting_order_id"] = False
                success, order, error = get_order_status(order_id)
                if success:
                    return order_status_response(order)
                return error_response(error, order_id)
            else:
                return ask_for_order_number()

        # Handle direct order status requests
        if ("order id" in user_input or "order status" in user_input or "status of" in user_input) and any(c.isdigit() for c in user_input):
            order_id = extract_order_id(user_input)
            if order_id:
                success, order, error = get_order_status(order_id)
                if success:
                    return order_status_response(order)
                return error_response(error, order_id)

        # Handle price queries
        if is_price_query(user_input):
            dish_item = extract_dish_item(user_input)
            if not dish_item:
                return error_response("item_not_found", "Please specify an item")
            
            success, item_details, error = get_menu_item_details(dish_item)
            if not success:
                return error_response(error, dish_item)
            
            return product_price_response(item_details)

        # Handle stock queries
        elif is_stock_query(user_input):
            dish_item = extract_dish_item(user_input)
            if not dish_item:
                return error_response("item_not_found", "Please specify an item")
            
            success, item_details, error = get_menu_item_details(dish_item)
            if not success:
                return error_response(error, dish_item)
            
            return product_stock_response(item_details)

        # Handle product details requests
        if intent in ["Product_FAQ", "Product_Details"]:
            dish_item, info_type = extract_item_and_intent(user_input)
            dish_item = dish_item or parameters.get("dish_items")
            
            if not dish_item:
                return error_response("item_not_found", "that item")
            
            success, item_details, error = get_menu_item_details(dish_item)
            if not success:
                return error_response(error, dish_item)
            
            return product_full_response(item_details)

        # Handle order status check requests
        if "order status" in user_input or "what is my order status" in user_input:
            order_id = extract_order_id(user_input)
            if order_id:
                success, order, error = get_order_status(order_id)
                if success:
                    return order_status_response(order)
                return error_response(error, order_id)
            else:
                session["awaiting_order_id"] = True
                return ask_for_order_number()

        # Default fallback - start order flow if user wants to order
        if any(phrase in user_input for phrase in ["order", "food", "menu", "hungry"]):
            clear_all_contexts(session_id)
            order_context = session["order"]
            order_context["awaiting"] = "name"
            return ask_for_order_name()

        # Final fallback
        return improved_ask_for_order_items()

    except Exception as e:
        logger.error(f"System error: {str(e)}", exc_info=True)
        return error_response("system_error", str(e))

# Helper functions
def create_order_with_customer_info(items, name, phone_number):
    """Create order with customer information"""
    try:
        success, message, order_id = create_order(items, extract_name_value(name), phone_number)
        return success, message, order_id
    except Exception as e:
        logger.error(f"Error creating order with customer info: {e}")
        return False, str(e), None

def create_reservation_with_customer_info(guests, datetime_param, name, phone_number):
    """Create reservation with customer information"""
    try:
        success, message, reservation_id = create_reservation(
            guests, datetime_param, extract_name_value(name), phone_number
        )
        return success, message, reservation_id
    except Exception as e:
        logger.error(f"Error creating reservation with customer info: {e}")
        return False, str(e), None

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)