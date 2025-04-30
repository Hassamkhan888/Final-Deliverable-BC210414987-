from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging
import uvicorn
from typing import Dict, Any, List, Optional
from datetime import datetime
from database import (
    create_order, get_order_status, get_menu_item_details, 
    create_support_ticket, create_reservation
)
from order_utils import (
    extract_order_details, extract_order_id, extract_dish_item,
    is_price_query, is_stock_query, extract_item_and_intent, 
    normalize_item_name, extract_support_request_details,
    is_technical_support_request
)
from response_templates import (
    error_response, order_success_response, ask_for_order_items,
    ask_for_order_number, order_status_response, product_price_response,
    product_stock_response, product_full_response, support_ticket_response,
    ask_reservation_question, confirm_reservation, reservation_success_response
)

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation state tracking
conversation_state: Dict[str, Dict[str, Any]] = {}

@app.post("/webhook")
async def webhook(request: Request):
    try:
        req = await request.json()
        query_result = req.get("queryResult", {})
        user_input = query_result.get("queryText", "").strip()
        session_id = req.get("session", "default").split('/')[-1]
        
        # Initialize session if not exists
        if session_id not in conversation_state:
            conversation_state[session_id] = {"context": None, "cart": []}

        # Debug logging
        logger.info(f"Incoming request - Intent: {query_result.get('intent', {}).get('displayName')}")
        logger.info(f"Parameters: {query_result.get('parameters', {})}")

        # Handle technical support requests first
        if is_technical_support_request(user_input):
            issue_type, description = extract_support_request_details(user_input)
            if not description:
                return error_response("Please describe your issue in more detail")
            
            success, message = create_support_ticket(
                session_id,
                issue_type or "technical",
                description
            )
            
            if not success:
                return error_response("support_ticket_failed", message)
            
            return support_ticket_response(description)

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

        # Process other intents
        intent = query_result.get("intent", {}).get("displayName", "")
        parameters = query_result.get("parameters", {})

        # Handle reservation intent
        if intent == "MakeReservation":
            # Check for missing parameters
            if not parameters.get("guest_count"):
                return ask_reservation_question("guest_count")
            if not parameters.get("reserve_date"):
                return ask_reservation_question("reserve_date")
            if not parameters.get("reserve_time"):
                return ask_reservation_question("reserve_time")
            
            # If we have all parameters, confirm the reservation
            return confirm_reservation(
                guests=int(parameters["guest_count"]),
                date=parameters["reserve_date"],
                time=parameters["reserve_time"]
            )
        
        # Handle reservation confirmation
        elif intent == "ConfirmReservation":
            if all(k in parameters for k in ["guest_count", "reserve_date", "reserve_time"]):
                try:
                    # Debug log the raw parameters
                    logger.info(f"Raw reservation parameters - guests: {parameters['guest_count']}, "
                               f"date: {parameters['reserve_date']}, time: {parameters['reserve_time']}")
                    
                    # Create the reservation
                    success, message, reservation_id = create_reservation(
                        session_id=session_id,
                        guests=int(parameters["guest_count"]),
                        date_str=parameters["reserve_date"],
                        time_str=parameters["reserve_time"]
                    )
                    
                    if success:
                        logger.info(f"Successfully created reservation ID: {reservation_id}")
                        # Format date/time for display
                        try:
                            if 'T' in parameters["reserve_date"]:
                                display_date = datetime.strptime(parameters["reserve_date"].split('T')[0], '%Y-%m-%d').strftime('%b %d, %Y')
                            else:
                                display_date = parameters["reserve_date"]
                            
                            if 'T' in parameters["reserve_time"]:
                                display_time = datetime.strptime(parameters["reserve_time"].split('T')[1][:5], '%H:%M').strftime('%I:%M %p')
                            else:
                                display_time = parameters["reserve_time"]
                        except Exception as e:
                            logger.error(f"Error formatting display date/time: {e}")
                            display_date = parameters["reserve_date"].split('T')[0] if 'T' in parameters["reserve_date"] else parameters["reserve_date"]
                            display_time = parameters["reserve_time"].split('T')[1][:5] if 'T' in parameters["reserve_time"] else parameters["reserve_time"]
                        
                        return reservation_success_response(
                            reservation_id=reservation_id,
                            guests=int(parameters["guest_count"]),
                            date=display_date,
                            time=display_time
                        )
                    else:
                        logger.error(f"Reservation failed: {message}")
                        return error_response("reservation_failed", message)
                except Exception as e:
                    logger.error(f"Error confirming reservation: {str(e)}")
                    return error_response("reservation_failed", "Invalid reservation details")

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

        # Handle order status checks
        elif intent == "CheckOrderStatus" or "order status" in user_input.lower():
            order_id = extract_order_id(user_input)
            if order_id:
                success, order, error = get_order_status(order_id)
                if success:
                    return order_status_response(order)
                return error_response(error, order_id)
            
            conversation_state[session_id]["context"] = "awaiting_order_id"
            return ask_for_order_number()

        # Handle new orders
        elif intent == "PlaceOrder" or any(w in user_input.lower() for w in ["order", "want", "get"]):
            if conversation_state[session_id].get("context"):
                del conversation_state[session_id]["context"]
                
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
        return error_response("system_error")

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)