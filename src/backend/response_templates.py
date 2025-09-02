from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
import random
from order_utils import format_order_items

def error_response(message: str, context: Any = None, status_code: int = 400) -> JSONResponse:
    error_messages = {
        "invalid_order_id": "❌ Please enter a valid Order ID (numbers only)",
        "order_not_found": f"❌ Order #{context if context else 'N/A'} not found",
        "order_creation_failed": f"❌ {context if context else 'Order creation failed'}",
        "database_error": "⚠️ Temporary database issue",
        "system_error": f"⚠️ Our systems are busy. {context if context else 'Please try again later.'}",
        "item_not_found": f"❌ We don't have information about '{context.replace('_', ' ') if context and hasattr(context, 'replace') else 'that item'}'",
        "support_ticket_failed": f"❌ Failed to create support ticket: {context if context else 'Unknown error'}",
        "reservation_failed": f"❌ Reservation failed: {context if context else 'Please try again'}",
        "feedback_failed": f"❌ Failed to submit feedback: {context if context else 'Please try again'}"
    }
    
    # Safely get the error message
    fulfillment_text = error_messages.get(message, "⚠️ Something went wrong")
    if context is None and ':' in fulfillment_text:
        fulfillment_text = fulfillment_text.split(':')[0]  # Remove context part if None
    
    return JSONResponse(
        content={
            "fulfillmentText": fulfillment_text,
            "payload": {
                "richContent": [[{
                    "type": "chips",
                    "options": [
                        {"text": "🔄 Try again"},
                        {"text": "📞 Contact support"}
                    ]
                }]]
            }
        },
        status_code=status_code
    )

def product_price_response(item: Dict) -> JSONResponse:
    return JSONResponse(
        content={
            "fulfillmentText": (
                f"💰 Price Information:\n"
                f"🍽️ Item: {item['name'].title()}\n"
                f"💵 Price: Rs. {item['price']:.2f}\n"
                f"📦 Category: {item['category']}\n\n"
                f"Would you like to place an order?"
            ),
            "payload": {
                "richContent": [[{
                    "type": "chips",
                    "options": [
                        {
                            "text": "🛒 Place Order",
                            "intent": "PlaceOrder",
                            "parameters": {"dish_items": item['name']}
                        } if item['in_stock'] else
                        {
                            "text": "⏳ Notify when available",
                            "intent": "Notify_Me"
                        },
                        {
                            "text": "🔙 Back to menu",
                            "intent": "Show_Menu"
                        }
                    ]
                }]]
            }
        }
    )

def product_stock_response(item: Dict) -> JSONResponse:
    status = "✅ In stock" if item['in_stock'] else "❌ Out of stock"
    return JSONResponse(
        content={
            "fulfillmentText": (
                f"📦 Availability Information:\n"
                f"🍽️ Item: {item['name'].title()}\n"
                f"🔄 Status: {status}\n"
                f"📦 Category: {item['category']}"
            ),
            "payload": {
                "richContent": [[{
                    "type": "chips",
                    "options": [
                        {
                            "text": "🛒 Place Order",
                            "intent": "PlaceOrder",
                            "parameters": {"dish_items": item['name']}
                        } if item['in_stock'] else
                        {
                            "text": "⏳ Notify when available",
                            "intent": "Notify_Me"
                        },
                        {
                            "text": "🔙 Back to menu",
                            "intent": "Show_Menu"
                        }
                    ]
                }]]
            }
        }
    )

def product_full_response(item: Dict) -> JSONResponse:
    return JSONResponse(
        content={
            "fulfillmentText": (
                f"ℹ️ Product Information:\n"
                f"🍽️ Item: {item['name'].title()}\n"
                f"💰 Price: Rs. {item['price']:.2f}\n"
                f"📦 Status: {'✅ In stock' if item['in_stock'] else '❌ Out of stock'}\n"
                f"🍽️ Category: {item['category']}\n\n"
                f"Would you like to place an order?"
            ),
            "payload": {
                "richContent": [[{
                    "type": "chips",
                    "options": [
                        {
                            "text": "🛒 Place Order",
                            "intent": "PlaceOrder",
                            "parameters": {"dish_items": item['name']}
                        } if item['in_stock'] else
                        {
                            "text": "⏳ Notify me", 
                            "intent": "Notify_Me"
                        },
                        {
                            "text": "🔍 More details",
                            "intent": "Product_Details"
                        }
                    ]
                }]]
            }
        }
    )

def order_success_response(message: str, order_id: str, items: List[Tuple[str, int]]) -> JSONResponse:
    items_str = format_order_items(items)
    return JSONResponse(
        content={
            "fulfillmentText": (
                f"🎉 Order #{order_id} confirmed!\n"
                f"🍽️ Items: {items_str}\n"
                f"⏳ Estimated ready by: {(datetime.now() + timedelta(minutes=random.randint(20, 40))).strftime('%I:%M %p')}\n"
                f"🔍 Check status with: 'Status #{order_id}'"
            ),
            "payload": {
                "richContent": [[
                    {
                        "type": "info",
                        "title": "✅ Order Confirmed",
                        "text": [
                            f"Order #{order_id} confirmed!",
                            f"Items: {items_str}",
                            f"Estimated ready by: {(datetime.now() + timedelta(minutes=random.randint(20, 40))).strftime('%I:%M %p')}"
                        ]
                    },
                    {
                        "type": "chips",
                        "options": [
                            {"text": f"🔍 Check order #{order_id}", "intent": "Check_Status"},
                            {"text": "🛒 New order", "intent": "Place_Order"}
                        ]
                    }
                ]]
            }
        }
    )

def support_ticket_response(description: str, name: Optional[str] = None) -> JSONResponse:
    greeting = f"Thanks, {name}! " if name else ""
    return JSONResponse(
        content={
            "fulfillmentText": (
                f"🎫 {greeting}Support ticket created!\n"
                f"📝 We've received your request about: {description}\n"
                f"👨‍💻 Our technical team will contact you soon.\n"
                f"⏱️ Expected response time: within 24 hours"
            ),
            "payload": {
                "richContent": [[
                    {
                        "type": "info",
                        "title": "✅ Support Request Received",
                        "text": [
                            f"Ticket ID: #{random.randint(1000, 9999)}",
                            f"Issue: {description}",
                            "Our team will contact you shortly",
                            "Priority: Medium"
                        ]
                    },
                    {
                        "type": "chips",
                        "options": [
                            {"text": "🛒 Place an order", "intent": "Place_Order"},
                            {"text": "❓ FAQ", "intent": "FAQ"},
                            {"text": "🏠 Back to main menu", "intent": "Main_Menu"}
                        ]
                    }
                ]]
            }
        }
    )

def feedback_prompt_name_response() -> JSONResponse:
    """Response to ask for user's name for feedback"""
    return JSONResponse(
        content={
            "fulfillmentText": "💬 I'd love to hear your feedback! May I have your name, please?",
            "payload": {
                "richContent": [[{
                    "type": "chips",
                    "options": [
                        {"text": "⏩ Skip this step", "intent": "GiveCustomerFeedback - skip_name"},
                        {"text": "🏠 Main Menu", "intent": "Main_Menu"}
                    ]
                }]]
            }
        }
    )

def feedback_prompt_phone_response(name: Optional[str] = None) -> JSONResponse:
    """Response to ask for user's phone number for feedback"""
    greeting = f"Thanks, {name}! " if name else ""
    return JSONResponse(
        content={
            "fulfillmentText": f"📱 {greeting}Can you share your phone number?",
            "payload": {
                "richContent": [[{
                    "type": "chips",
                    "options": [
                        {"text": "⏩ Skip this step", "intent": "GiveCustomerFeedback - skip_phone"},
                        {"text": "🏠 Main Menu", "intent": "Main_Menu"}
                    ]
                }]]
            }
        }
    )

def feedback_prompt_text_response(name: Optional[str] = None) -> JSONResponse:
    """Response to ask for feedback text"""
    greeting = f"Thanks{', ' + name if name else ''}! " 
    return JSONResponse(
        content={
            "fulfillmentText": f"📝 {greeting}Please share your feedback.",
            "payload": {
                "richContent": [[{
                    "type": "chips",
                    "options": [
                        {"text": "🏠 Main Menu", "intent": "Main_Menu"}
                    ]
                }]]
            }
        }
    )

def feedback_submitted_response(name: Optional[str] = None) -> JSONResponse:
    """Response after successful feedback submission"""
    greeting = f"Thank you, {name}! " if name else "Thank you! "
    return JSONResponse(
        content={
            "fulfillmentText": f"✨ {greeting}We appreciate your valuable feedback! Your thoughts will help us improve our services.",
            "payload": {
                "richContent": [[
                    {
                        "type": "info",
                        "title": "✅ Feedback Received",
                        "text": [
                            "✅ Your feedback has been submitted successfully",
                            "🙏 We're grateful for your input",
                            "🌟 Your feedback helps us improve"
                        ]
                    },
                    {
                        "type": "chips",
                        "options": [
                            {"text": "🛒 Place an order", "intent": "Place_Order"},
                            {"text": "📅 Make reservation", "intent": "MakeReservation"},
                            {"text": "🏠 Main menu", "intent": "Main_Menu"}
                        ]
                    }
                ]]
            }
        }
    )

def feedback_cancelled_response() -> JSONResponse:
    """Response when user cancels feedback"""
    return JSONResponse(
        content={
            "fulfillmentText": "👍 No problem at all! If you change your mind later, feel free to share your feedback anytime.",
            "payload": {
                "richContent": [[{
                    "type": "chips",
                    "options": [
                        {"text": "🛒 Place an order", "intent": "Place_Order"},
                        {"text": "📅 Make reservation", "intent": "MakeReservation"},
                        {"text": "🏠 Main menu", "intent": "Main_Menu"}
                    ]
                }]]
            }
        }
    )

def technical_support_name_response() -> JSONResponse:
    """Response to ask for user's name for technical support"""
    return JSONResponse(
        content={
            "fulfillmentText": "🔧 I'm sorry to hear you're experiencing an issue. May I have your name, please?",
            "payload": {
                "richContent": [[{
                    "type": "chips",
                    "options": [
                        {"text": "⏩ Skip this step", "intent": "Technical_Support - skip_name"},
                        {"text": "❌ Cancel", "intent": "Technical_Support - cancel"}
                    ]
                }]]
            }
        }
    )

def technical_support_phone_response(name: Optional[str] = None) -> JSONResponse:
    """Response to ask for user's phone number for technical support"""
    greeting = f"Thanks, {name}! " if name else ""
    return JSONResponse(
        content={
            "fulfillmentText": f"📱 {greeting}Can you share your phone number in case we need to follow up?",
            "payload": {
                "richContent": [[{
                    "type": "chips",
                    "options": [
                        {"text": "⏩ Skip this step", "intent": "Technical_Support - skip_phone"},
                        {"text": "❌ Cancel", "intent": "Technical_Support - cancel"}
                    ]
                }]]
            }
        }
    )

def technical_support_issue_response(name: Optional[str] = None) -> JSONResponse:
    """Response to ask for issue type"""
    greeting = f"Thanks{', ' + name if name else ''}! "
    return JSONResponse(
        content={
            "fulfillmentText": f"🔍 {greeting}What type of issue are you facing?",
            "payload": {
                "richContent": [[{
                    "type": "chips",
                    "options": [
                        {"text": "📱 Device Problem", "intent": "Technical_Support - issue", "parameters": {"issue": "device"}},
                        {"text": "🔐 Account Issue", "intent": "Technical_Support - issue", "parameters": {"issue": "account"}},
                        {"text": "💻 Technical Issue", "intent": "Technical_Support - issue", "parameters": {"issue": "technical"}},
                        {"text": "🌐 Website Problem", "intent": "Technical_Support - issue", "parameters": {"issue": "website"}},
                        {"text": "❓ Other", "intent": "Technical_Support - issue", "parameters": {"issue": "general"}}
                    ]
                }]]
            }
        }
    )

def technical_support_description_response(issue_type: str) -> JSONResponse:
    """Response to ask for detailed description of technical issue"""
    emoji_map = {
        "device": "📱",
        "account": "🔐",
        "technical": "💻",
        "website": "🌐",
        "general": "❓"
    }
    emoji = emoji_map.get(issue_type, "🔧")
    
    return JSONResponse(
        content={
            "fulfillmentText": f"{emoji} Please describe your {issue_type} issue in detail.",
            "payload": {
                "richContent": [[{
                    "type": "chips",
                    "options": [
                        {"text": "❌ Cancel", "intent": "Technical_Support - cancel"}
                    ]
                }]]
            }
        }
    )

def technical_support_cancelled_response() -> JSONResponse:
    """Response when user cancels technical support request"""
    return JSONResponse(
        content={
            "fulfillmentText": "👍 I understand. If you need help later, feel free to contact our support team anytime.",
            "payload": {
                "richContent": [[{
                    "type": "chips",
                    "options": [
                        {"text": "🛒 Place an order", "intent": "Place_Order"},
                        {"text": "❓ FAQ", "intent": "FAQ"},
                        {"text": "🏠 Main Menu", "intent": "Main_Menu"}
                    ]
                }]]
            }
        }
    )

def ask_for_order_items() -> JSONResponse:
    return JSONResponse(
        content={
            "fulfillmentText": "🍽️ What would you like to order today? (Example: '2 chicken biryani and 1 pepsi')",
            "payload": {
                "richContent": [[{
                    "type": "chips",
                    "options": [
                        {"text": "🍛 2 Chicken Biryani + 🥤 1 Pepsi", "intent": "Quick_Order"},
                        {"text": "🍔 1 Beef Burger + 🥤 2 Colas", "intent": "Quick_Order"},
                        {"text": "🍲 1 Mutton Karahi + 🫓 2 Naan", "intent": "Quick_Order"},
                        {"text": "📝 Custom order...", "intent": "Custom_Order"}
                    ]
                }]]
            }
        }
    )

def ask_for_order_number() -> JSONResponse:
    return JSONResponse(
        content={
            "fulfillmentText": "🔢 Please provide your Order ID (example: '1019')",
            "payload": {
                "richContent": [[{
                    "type": "chips",
                    "options": [
                        {"text": "🔍 Check order status", "intent": "Check_Status"},
                        {"text": "🛒 Place new order", "intent": "Place_Order"}
                    ]
                }]]
            }
        }
    )

def order_status_response(order: Dict) -> JSONResponse:
    status_emoji = {
        'Pending': "⏳",
        'Confirmed': "✅",
        'Preparing': "👨‍🍳",
        'On the way': "🛵",
        'Delivered': "🎉",
        'Cancelled': "❌"
    }.get(order['status'], "🔄")
    
    status_msg = {
        'Pending': "⏳ Awaiting confirmation",
        'Confirmed': "✅ Your order is confirmed",
        'Preparing': "👨‍🍳 Cooking in progress",
        'On the way': f"🛵 Out for delivery (ETA: {order['estimated_time']})",
        'Delivered': "🎉 Delivered",
        'Cancelled': "❌ Cancelled"
    }.get(order['status'], order['status'])
    
    return JSONResponse(
        content={
            "fulfillmentText": (
                f"📦 Order #{order['order_id']}\n"
                f"{status_msg}\n"
                f"🍽️ Items: {order['items']}"
            ),
            "payload": {
                "richContent": [[
                    {
                        "type": "info",
                        "title": f"{status_emoji} Order #{order['order_id']} Status",
                        "text": [
                            f"Status: {status_msg}",
                            f"Items: {order['items']}",
                            f"Estimated: {order.get('estimated_time', '')}"
                        ]
                    },
                    {
                        "type": "chips",
                        "options": [
                            {"text": "🛒 New order", "intent": "Place_Order"},
                            {"text": "📞 Support", "intent": "Contact_Support"}
                        ]
                    }
                ]]
            }
        }
    )

def ask_reservation_question(missing_param: str) -> JSONResponse:
    questions = {
        "guest_count": "👥 How many guests will be dining? (1-20)",
        "reserve_date_time": "📅 What date and time would you like to book for? (e.g., '10 Jan 10 AM' or 'January 10 2 PM')"
    }
    return JSONResponse(
        content={"fulfillmentText": questions[missing_param]}
    )

def reservation_success_response(reservation_id: int, guests: int, date: str, time: str) -> JSONResponse:
    return JSONResponse(
        content={
            "fulfillmentText": (
                f"🎉 Reservation confirmed!\n"
                f"📅 Date: {date}\n"
                f"⏰ Time: {time}\n"
                f"👥 Guests: {guests}\n"
                f"Your reservation ID is #{reservation_id}"
            ),
            "payload": {
                "richContent": [[
                    {
                        "type": "info",
                        "title": "✅ Reservation Confirmed",
                        "text": [
                            f"Reservation #{reservation_id} confirmed!",
                            f"📅 Date: {date}",
                            f"⏰ Time: {time}",
                            f"👥 Guests: {guests}"
                        ]
                    },
                    {
                        "type": "chips",
                        "options": [
                            {"text": "📅 View my reservations", "intent": "ViewReservations"},
                            {"text": "🛎️ Special requests", "intent": "SpecialRequests"},
                            {"text": "🛒 Place an order", "intent": "PlaceOrder"}
                        ]
                    }
                ]]
            }
        }
    )