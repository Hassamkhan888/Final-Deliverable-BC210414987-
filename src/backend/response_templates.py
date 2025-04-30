from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
import random
from order_utils import format_order_items

def error_response(message: str, context: Any = None, status_code: int = 400) -> JSONResponse:
    error_messages = {
        "invalid_order_id": "❌ Please enter a valid Order ID (numbers only)",
        "order_not_found": f"❌ Order #{context} not found",
        "order_creation_failed": f"❌ {context}",
        "database_error": "⚠️ Temporary database issue",
        "system_error": "⚠️ Our systems are busy. Please try again later.",
        "item_not_found": f"❌ We don't have information about '{context.replace('_', ' ')}'",
        "support_ticket_failed": f"❌ Failed to create support ticket: {context}",
        "reservation_failed": f"❌ Reservation failed: {context}"
    }
    
    return JSONResponse(
        content={
            "fulfillmentText": error_messages.get(message, "⚠️ Something went wrong"),
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
                f"💵 Price: ${item['price']:.2f}\n"
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
                f"💰 Price: ${item['price']:.2f}\n"
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

def support_ticket_response(description: str) -> JSONResponse:
    return JSONResponse(
        content={
            "fulfillmentText": (
                f"🛎️ Support ticket created!\n"
                f"We've received your request about: {description}\n"
                f"Our team will contact you soon."
            ),
            "payload": {
                "richContent": [[
                    {
                        "type": "info",
                        "title": "✅ Support Request Received",
                        "text": [
                            "Your support ticket has been created",
                            f"Issue: {description}",
                            "We'll contact you shortly"
                        ]
                    },
                    {
                        "type": "chips",
                        "options": [
                            {"text": "🛒 Place an order", "intent": "Place_Order"},
                            {"text": "🏠 Back to main menu", "intent": "Main_Menu"}
                        ]
                    }
                ]]
            }
        }
    )

def ask_for_order_items() -> JSONResponse:
    return JSONResponse(
        content={
            "fulfillmentText": "What would you like to order today? (Example: '2 chicken biryani and 1 pepsi')",
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
            "fulfillmentText": "Please provide your Order ID (example: '1019')",
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
    status_msg = {
        'Pending': "⏳ Awaiting confirmation",
        'Confirmed': "✅ Being prepared",
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
                        "title": f"Order #{order['order_id']} Status",
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
        "guest_count": "How many guests will be dining?",
        "reserve_date": "What date would you like to book for? (e.g., tomorrow or June 15)",
        "reserve_time": "What time would you prefer? (e.g., 7pm or 19:30)"
    }
    return JSONResponse(
        content={"fulfillmentText": questions[missing_param]}
    )

def confirm_reservation(guests: int, date: str, time: str) -> JSONResponse:
    return JSONResponse(
        content={
            "fulfillmentText": f"📅 Confirm reservation for {guests} guests on {date} at {time}?",
            "payload": {
                "richContent": [[{
                    "type": "chips",
                    "options": [
                        {"text": "✅ Confirm", "intent": "ConfirmReservation"},
                        {"text": "✏️ Edit", "intent": "ModifyReservation"}
                    ]
                }]]
            }
        }
    )

def reservation_success_response(reservation_id: int, guests: int, date: str, time: str) -> JSONResponse:
    return JSONResponse(
        content={
            "fulfillmentText": (
                f"🎉 Reservation confirmed! (ID: #{reservation_id})\n"
                f"👥 Guests: {guests}\n"
                f"📅 Date: {date}\n"
                f"⏰ Time: {time}\n\n"
                f"We'll send a confirmation shortly."
            ),
            "payload": {
                "richContent": [[
                    {
                        "type": "info",
                        "title": "✅ Reservation Confirmed",
                        "text": [
                            f"Reservation #{reservation_id} confirmed!",
                            f"Guests: {guests}",
                            f"Date: {date}",
                            f"Time: {time}"
                        ]
                    },
                    {
                        "type": "chips",
                        "options": [
                            {"text": "📅 View my reservations", "intent": "ViewReservations"},
                            {"text": "🛎️ Special requests", "intent": "SpecialRequests"}
                        ]
                    }
                ]]
            }
        }
    )