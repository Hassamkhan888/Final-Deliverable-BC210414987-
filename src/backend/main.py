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
        logger.info(f"Support context: {session['support']}")
        
        # Extract intent and parameters for cleaner code
        intent = query_result.get("intent", {}).get("displayName", "")
        parameters = query_result.get("parameters", {})

        # Handle technical support requests immediately without intent matching
        # This is to handle "my device is not working" type messages directly
        if is_technical_support_request(user_input) and "device" in user_input and "not working" in user_input:
            # Auto-extract device issue information
            issue_type, description = extract_support_request_details(user_input)
            
            # Create support ticket with session ID
            success, message = create_support_ticket(
                session_id=session_id,
                name="User",  # Default name
                phone_number=None,  # No phone number
                issue_type=issue_type,
                description=user_input  # Use the whole message as description
            )
            
            if success:
                return support_ticket_response(user_input)
            else:
                return error_response("support_ticket_failed", message)

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

        # Handle feedback requests outside of direct intent
        if is_feedback_request(user_input) and intent != "GiveCustomerFeedback":
            # Start the GiveCustomerFeedback flow
            feedback_context = session["feedback"]
            feedback_context["awaiting"] = "name"
            return feedback_prompt_name_response()

        # Handle technical support requests outside of direct intent - EXCEPT those directly handled above
        if is_technical_support_request(user_input) and intent != "Technical_Support" and not ("device" in user_input and "not working" in user_input):
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

        # Handle reservation intent
        if intent == "MakeReservation" or "reservation" in user_input:
            try:
                # Extract and validate guests
                guests = parameters.get("guest_count")
                if guests is not None and guests != '':  # Handle empty string case
                    try:
                        guests = int(float(guests))  # Handle both int and float inputs
                        if guests < 1 or guests > 20:
                            session["reservation"]["retry_count"] += 1
                            if session["reservation"]["retry_count"] > 2:
                                clear_reservation_context(session_id)
                                return error_response(
                                    "reservation_failed", 
                                    "Maximum attempts reached. Please start over."
                                )
                            return ask_reservation_question("guest_count")
                        session["reservation"]["guests"] = guests
                        session["reservation"]["retry_count"] = 0
                    except (ValueError, TypeError):
                        session["reservation"]["retry_count"] += 1
                        if session["reservation"]["retry_count"] > 2:
                            clear_reservation_context(session_id)
                            return error_response(
                                "reservation_failed", 
                                "Maximum attempts reached. Please start over."
                            )
                        return ask_reservation_question("guest_count")
                else:
                    return ask_reservation_question("guest_count")

                # Custom handling for date format "10 jan 25 2 pm"
                if user_input and any(month in user_input for month in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]) and re.search(r'\b\d{1,2}\s', user_input):
                    session["reservation"]["datetime"] = user_input
                    session["reservation"]["retry_count"] = 0
                # Standard datetime parameter extraction
                else:
                    datetime_param = parameters.get("reserve_date_time")
                    if datetime_param and datetime_param != []:  # Handle empty list case
                        session["reservation"]["datetime"] = datetime_param
                        session["reservation"]["retry_count"] = 0
                    else:
                        return ask_reservation_question("reserve_date_time")

                # Create reservation
                # Check for directly entered date time in user input
                success, message, reservation_id = create_reservation(
                    guests=session["reservation"]["guests"],
                    datetime_param=session["reservation"]["datetime"]
                )

                if success:
                    # Format display date and time
                    try:
                        datetime_param = session["reservation"]["datetime"]
                        if isinstance(datetime_param, dict) and 'date_time' in datetime_param:
                            dt_str = datetime_param['date_time']
                        elif isinstance(datetime_param, list) and len(datetime_param) > 0 and isinstance(datetime_param[0], dict) and 'date_time' in datetime_param[0]:
                            dt_str = datetime_param[0]['date_time']
                        else:
                            dt_str = str(datetime_param)

                        if 'T' in dt_str:
                            dt_obj = datetime.strptime(dt_str.split('+')[0], '%Y-%m-%dT%H:%M:%S')
                            display_date = dt_obj.strftime('%b %d, %Y')
                            display_time = dt_obj.strftime('%I:%M %p')
                        else:
                            formats = [
                                '%d %b %y %I %p', '%d %B %y %I %p',  # Add support for 2-digit year formats
                                '%d %b %I %p', '%d %B %I %p',
                                '%b %d %I %p', '%B %d %I %p',
                                '%d %b %H:%M', '%d %B %H:%M',
                                '%b %d %H:%M', '%B %d %H:%M'
                            ]
                            dt_obj = None
                            for fmt in formats:
                                try:
                                    dt_obj = datetime.strptime(dt_str, fmt)
                                    break
                                except ValueError:
                                    continue
                            
                            if dt_obj is None:
                                raise ValueError("Unrecognized format")
                            
                            if dt_obj.year == 1900:
                                current_year = datetime.now().year
                                dt_obj = dt_obj.replace(year=current_year)
                                if dt_obj < datetime.now():
                                    dt_obj = dt_obj.replace(year=current_year + 1)
                            
                            display_date = dt_obj.strftime('%b %d, %Y')
                            display_time = dt_obj.strftime('%I:%M %p')
                    except Exception as e:
                        logger.error(f"Error formatting datetime: {e}")
                        display_date = "your selected date"
                        display_time = "your selected time"

                    # Clear reservation data
                    clear_reservation_context(session_id)

                    return reservation_success_response(
                        reservation_id=reservation_id,
                        guests=guests,
                        date=display_date,
                        time=display_time
                    )
                else:
                    session["reservation"]["retry_count"] += 1
                    if session["reservation"]["retry_count"] > 2:
                        clear_reservation_context(session_id)
                        return error_response("reservation_failed", "Maximum attempts reached. Please start over.")
                    return error_response("reservation_failed", message)

            except Exception as e:
                logger.error(f"Error processing reservation: {str(e)}")
                clear_reservation_context(session_id)
                return error_response("reservation_failed", str(e))

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