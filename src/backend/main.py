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

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation state tracking
conversation_state: Dict[str, Dict[str, Any]] = {}

def clear_reservation_context(session_id: str):
    """Clear reservation context for a session"""
    if session_id in conversation_state:
        conversation_state[session_id]["reservation"] = {
            "guests": None,
            "datetime": None,
            "retry_count": 0
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
    # Try various regex patterns to capture different date formats
    patterns = [
        # 10 jan 25 10 pm
        r'(\d+)\s+([a-z]{3,})\s+(\d{2,4})\s+(\d{1,2})\s+([ap]m)',
        # 1/1/25 2 pm
        r'(\d{1,2})/(\d{1,2})/(\d{2,4})\s+(\d{1,2})\s+([ap]m)',
        # January 10, 2025 at 2 PM
        r'([a-z]{3,})\s+(\d{1,2})(?:,|\s+)?\s+(\d{2,4})(?:\s+at)?\s+(\d{1,2})\s+([ap]m)',
        # 10 jan 10 pm
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
                    "guests": None,
                    "datetime": None,
                    "retry_count": 0
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
        
        # Extract intent and parameters for cleaner code
        intent = query_result.get("intent", {}).get("displayName", "")
        parameters = query_result.get("parameters", {})

        # Check if we're in the middle of the support flow and they say "my device is not working"
        support_context = session["support"]
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

        # Special case: If we're waiting for a reservation date and time, and the user provides it
        # This is a direct handling of the date time case
        reservation_context = session.get("reservation", {})
        if reservation_context.get("guests") and "jan" in user_input and "pm" in user_input:
            # We have direct date entry in the input
            guests = reservation_context.get("guests")
            datetime_param = user_input
            
            # Parse date time info for display
            datetime_info = extract_datetime_info(user_input)
            
            # Create the reservation directly
            success, message, reservation_id = create_reservation(
                guests=guests,
                datetime_param=datetime_param
            )
            
            if success:
                # Get display date and time from input
                display_date = "Jan 01, 2025"  # Default 
                display_time = "2:00 PM"      # Default
                
                if datetime_info:
                    match = datetime_info['match']
                    pattern = datetime_info['pattern']
                    
                    # Handle different patterns
                    if pattern == r'(\d+)\s+([a-z]{3,})\s+(\d{2,4})\s+(\d{1,2})\s+([ap]m)':
                        # 10 jan 25 10 pm
                        day = match.group(1)
                        month = match.group(2).capitalize()
                        year = match.group(3)
                        hour = match.group(4) 
                        ampm = match.group(5).upper()
                        
                        # Format 2-digit year to 4 digits
                        if len(year) == 2:
                            year = "20" + year
                            
                        display_date = f"{month} {day}, {year}"
                        display_time = f"{hour}:00 {ampm}"
                        
                    elif pattern == r'(\d{1,2})/(\d{1,2})/(\d{2,4})\s+(\d{1,2})\s+([ap]m)':
                        # 1/1/25 2 pm
                        month_num = int(match.group(1))
                        day = match.group(2)
                        year = match.group(3)
                        hour = match.group(4)
                        ampm = match.group(5).upper()
                        
                        # Convert month number to name
                        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                        month = months[month_num - 1]
                        
                        # Format 2-digit year to 4 digits
                        if len(year) == 2:
                            year = "20" + year
                            
                        display_date = f"{month} {day}, {year}"
                        display_time = f"{hour}:00 {ampm}"
                        
                    elif pattern == r'([a-z]{3,})\s+(\d{1,2})(?:,|\s+)?\s+(\d{2,4})(?:\s+at)?\s+(\d{1,2})\s+([ap]m)':
                        # January 10, 2025 at 2 PM
                        month = match.group(1).capitalize()
                        day = match.group(2)
                        year = match.group(3)
                        hour = match.group(4)
                        ampm = match.group(5).upper()
                        
                        display_date = f"{month} {day}, {year}"
                        display_time = f"{hour}:00 {ampm}"
                        
                    else:
                        # 10 jan 10 pm - no year
                        day = match.group(1)
                        month = match.group(2).capitalize()
                        hour = match.group(3)
                        ampm = match.group(4).upper()
                        
                        display_date = f"{month} {day}, 2025"
                        display_time = f"{hour}:00 {ampm}"
                
                # Clear reservation data
                clear_reservation_context(session_id)
                
                # Return successful reservation response
                return reservation_success_response(
                    reservation_id=reservation_id,
                    guests=guests,
                    date=display_date,
                    time=display_time
                )
            else:
                return error_response("reservation_failed", message)

        # Handle GiveCustomerFeedback intent and its flow
        if intent.startswith("GiveCustomerFeedback"):
            feedback_context = session["feedback"]
            
            # Handle skip name action
            if intent == "GiveCustomerFeedback - skip_name":
                feedback_context["awaiting"] = "phone_number"
                return feedback_prompt_phone_response()
                
            # Handle skip phone action
            elif intent == "GiveCustomerFeedback - skip_phone":
                feedback_context["awaiting"] = "feedback_text"
                return feedback_prompt_text_response(extract_name_value(feedback_context["name"]))
                
            # Main intent
            elif intent == "GiveCustomerFeedback":
                # Extract parameters if provided
                name = parameters.get("name")
                phone_number = parameters.get("phone-number")
                feedback_text = parameters.get("feedback-text")
                
                # If user directly provides all information in one message
                if name and phone_number and feedback_text:
                    feedback_context["name"] = name
                    feedback_context["phone_number"] = phone_number
                    feedback_context["text"] = feedback_text
                    
                    # Submit feedback with session ID
                    success, message = submit_customer_feedback(
                        user_id=session_id,  # Use session_id here
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
                
                # Handle the staged flow for collecting feedback
                if feedback_context["awaiting"] is None:
                    # Starting the flow - ask for name
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
                    
                    # Submit feedback with session ID
                    success, message = submit_customer_feedback(
                        user_id=session_id,  # Use session_id here
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
                
                # If no awaiting state is set, start the feedback flow
                feedback_context["awaiting"] = "name"
                return feedback_prompt_name_response()
            
        # Handle Technical_Support intent and its flow
        elif intent.startswith("Technical_Support"):
            support_context = session["support"]
            
            # Handle cancel action
            if intent == "Technical_Support - cancel":
                clear_support_context(session_id)
                return technical_support_cancelled_response()
                
            # Handle skip name action
            elif intent == "Technical_Support - skip_name":
                support_context["awaiting"] = "phone_number"
                return technical_support_phone_response()
                
            # Handle skip phone action
            elif intent == "Technical_Support - skip_phone":
                support_context["awaiting"] = "issue_type"
                return technical_support_issue_response(extract_name_value(support_context["name"]))
                
            # Handle issue type selection
            elif intent == "Technical_Support - issue":
                issue = parameters.get("issue")
                if issue:
                    support_context["issue_type"] = issue
                    support_context["awaiting"] = "description"
                    return technical_support_description_response(issue)
                else:
                    support_context["awaiting"] = "issue_type"
                    return technical_support_issue_response(extract_name_value(support_context["name"]))
                
            # Main intent
            elif intent == "Technical_Support":
                # Extract parameters if provided
                name = parameters.get("name")
                phone_number = parameters.get("phone-number")
                issue = parameters.get("issue")
                description = parameters.get("description")
                
                # If user directly provides all information in one message
                if name and phone_number and issue and description:
                    support_context["name"] = name
                    support_context["phone_number"] = phone_number
                    support_context["issue_type"] = issue
                    support_context["description"] = description
                    
                    # Create support ticket with session ID
                    success, message = create_support_ticket(
                        session_id=session_id,
                        name=support_context["name"],
                        phone_number=support_context["phone_number"],
                        issue_type=support_context["issue_type"],
                        description=support_context["description"]
                    )
                    
                    name_value = extract_name_value(support_context["name"])
                    description = support_context["description"]
                    
                    # Make sure to clear the context BEFORE returning the response
                    clear_support_context(session_id)
                    
                    if success:
                        return support_ticket_response(description, name_value)
                    else:
                        return error_response("support_ticket_failed", message)
                
                # Handle the staged flow for collecting support info
                if support_context["awaiting"] is None:
                    # Starting the flow - ask for name
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
                    # Try to identify issue type from user input
                    issue_type, _ = extract_support_request_details(user_input)
                    support_context["issue_type"] = issue_type
                    support_context["awaiting"] = "description"
                    return technical_support_description_response(issue_type)
                    
                elif support_context["awaiting"] == "description":
                    support_context["description"] = user_input
                    
                    # Create support ticket with session ID
                    success, message = create_support_ticket(
                        session_id=session_id,
                        name=support_context["name"],
                        phone_number=support_context["phone_number"],
                        issue_type=support_context["issue_type"],
                        description=support_context["description"]
                    )
                    
                    name = support_context["name"]
                    description = support_context["description"]
                    
                    # Make sure to clear the context BEFORE returning the response
                    clear_support_context(session_id)
                    
                    if success:
                        return support_ticket_response(description, name)
                    else:
                        return error_response("support_ticket_failed", message)
                
                # If no awaiting state is set, start the technical support flow
                support_context["awaiting"] = "name"
                return technical_support_name_response()

        # Handle initial technical support requests (start flow)
        if is_technical_support_request(user_input) and "device" in user_input and "not working" in user_input:
            # Start the support flow instead of directly creating a ticket
            # This ensures we collect name and phone number
            support_context["awaiting"] = "name"
            return technical_support_name_response()

        # Handle feedback requests outside of direct intent
        if is_feedback_request(user_input) and intent != "GiveCustomerFeedback":
            # Start the GiveCustomerFeedback flow
            feedback_context = session["feedback"]
            feedback_context["awaiting"] = "name"
            return feedback_prompt_name_response()

        # Handle technical support requests outside of direct intent
        if is_technical_support_request(user_input) and intent != "Technical_Support":
            # Start the Technical_Support flow
            support_context = session["support"]
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
                # If no order ID found, ask again
                return ask_for_order_number()

        # Handle direct order status requests (with ID included)
        if ("order id" in user_input or "order status" in user_input or "status of" in user_input) and any(c.isdigit() for c in user_input):
            order_id = extract_order_id(user_input)
            if order_id:
                success, order, error = get_order_status(order_id)
                if success:
                    return order_status_response(order)
                return error_response(error, order_id)

        # Clear context if user explicitly asks for reservation while in order flow
        if "reservation" in user_input and session.get("context"):
            logger.info("Clearing order context for reservation request")
            session["context"] = None
            clear_reservation_context(session_id)
            return ask_reservation_question("guest_count")

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

        # Handle reservation intent - simplified approach
        if intent == "MakeReservation" or "reservation" in user_input or "book" in user_input:
            # First, check if we're awaiting a datetime (already have guests)
            if session["reservation"].get("guests") and not session["reservation"].get("datetime"):
                if any(month in user_input for month in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]):
                    # Extract date information for display
                    datetime_info = extract_datetime_info(user_input)
                    
                    if datetime_info:
                        # Save the datetime string
                        session["reservation"]["datetime"] = user_input
                        
                        # Create the reservation
                        success, message, reservation_id = create_reservation(
                            guests=session["reservation"]["guests"],
                            datetime_param=user_input
                        )
                        
                        if success:
                            # Extract display date and time from input
                            display_date = "January 1, 2025"  # Default 
                            display_time = "2:00 PM"          # Default
                            
                            match = datetime_info['match']
                            pattern = datetime_info['pattern']
                            
                            # Extract month and convert to text if needed
                            month_names = ["January", "February", "March", "April", "May", "June", 
                                          "July", "August", "September", "October", "November", "December"]
                            month_abbr = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                                         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                            
                            # Try to extract parts based on the pattern
                            try:
                                if pattern.startswith(r'(\d+)\s+([a-z]{3,})'):
                                    # Format: 10 jan 25 10 pm or 10 jan 10 pm
                                    day = match.group(1)
                                    month_text = match.group(2).lower()
                                    
                                    # Find month index
                                    month_idx = -1
                                    for i, abbr in enumerate(month_abbr):
                                        if month_text.startswith(abbr.lower()):
                                            month_idx = i
                                            break
                                    
                                    month = month_abbr[month_idx] if month_idx >= 0 else "Jan"
                                    
                                    # Get year if available
                                    year = "2025"  # Default
                                    if len(match.groups()) >= 3:
                                        year_text = match.group(3)
                                        if len(year_text) == 2:
                                            year = "20" + year_text
                                        else:
                                            year = year_text
                                    
                                    # Get time
                                    if len(match.groups()) >= 5:
                                        hour = match.group(4)
                                        ampm = match.group(5).upper()
                                        display_time = f"{hour}:00 {ampm}"
                                    elif len(match.groups()) >= 4:
                                        hour = match.group(3)
                                        ampm = match.group(4).upper()
                                        display_time = f"{hour}:00 {ampm}"
                                    
                                    display_date = f"{month} {day}, {year}"
                                    
                                elif pattern.startswith(r'(\d{1,2})/(\d{1,2})/'):
                                    # Format: 1/1/25 2 pm
                                    month_num = int(match.group(1))
                                    day = match.group(2)
                                    year_text = match.group(3)
                                    hour = match.group(4)
                                    ampm = match.group(5).upper()
                                    
                                    month = month_abbr[month_num-1]
                                    
                                    if len(year_text) == 2:
                                        year = "20" + year_text
                                    else:
                                        year = year_text
                                    
                                    display_date = f"{month} {day}, {year}"
                                    display_time = f"{hour}:00 {ampm}"
                            except Exception as e:
                                logger.error(f"Error parsing date for display: {e}")
                                # Use defaults if parsing fails
                                
                            # Clear context
                            guests = session["reservation"]["guests"]
                            clear_reservation_context(session_id)
                            
                            # Return success response
                            return reservation_success_response(
                                reservation_id=reservation_id,
                                guests=guests,
                                date=display_date,
                                time=display_time
                            )
                        else:
                            return error_response("reservation_failed", message)
                else:
                    # Not a date format we recognize, ask again
                    return ask_reservation_question("reserve_date_time")
            
            # Handle guest count if not provided yet
            if not session["reservation"].get("guests"):
                # Try to extract guest count from input
                guest_match = re.search(r'(\d+)\s*(?:guests?|people)', user_input.lower())
                if guest_match:
                    try:
                        guests = int(guest_match.group(1))
                        if 1 <= guests <= 20:
                            session["reservation"]["guests"] = guests
                            session["reservation"]["retry_count"] = 0
                            
                            # Now ask for date and time
                            return ask_reservation_question("reserve_date_time")
                        else:
                            return ask_reservation_question("guest_count")
                    except (ValueError, TypeError):
                        return ask_reservation_question("guest_count")
                else:
                    # Check if it's a guest parameter
                    guests = parameters.get("guest_count")
                    if guests is not None and guests != '':
                        try:
                            guests = int(float(guests))
                            if 1 <= guests <= 20:
                                session["reservation"]["guests"] = guests
                                session["reservation"]["retry_count"] = 0
                                
                                # Now ask for date and time
                                return ask_reservation_question("reserve_date_time")
                            else:
                                return ask_reservation_question("guest_count")
                        except (ValueError, TypeError):
                            return ask_reservation_question("guest_count")
                    else:
                        # If we still don't have guest count, ask for it
                        return ask_reservation_question("guest_count")

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
            # First check if order ID is already in the input
            order_id = extract_order_id(user_input)
            if order_id:
                success, order, error = get_order_status(order_id)
                if success:
                    return order_status_response(order)
                return error_response(error, order_id)
            else:
                # If no order ID found, set context and ask for it
                session["awaiting_order_id"] = True
                return ask_for_order_number()

        # Handle new orders
        elif intent == "PlaceOrder" or any(w in user_input for w in ["order", "want", "get"]):
            if session.get("context"):
                del session["context"]
                
            items = extract_order_details(user_input)
            if not items:
                return ask_for_order_items()
            
            success, message, order_id = create_order(items)
            if not success:
                return error_response("order_creation_failed", message)
            
            return order_success_response(message, order_id, items)

        # Default response
        return ask_for_order_items()

    except Exception as e:
        logger.error(f"System error: {str(e)}", exc_info=True)
        return error_response("system_error", str(e))

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)