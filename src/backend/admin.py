from fastapi import APIRouter, HTTPException, Body
from database import get_db_connection
from datetime import timedelta

router = APIRouter()

# ---------------- Reservations ----------------
@router.get("/reservations")
def get_reservations():
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, customer_name, phone, guests, reservation_date, reservation_time, status, DATE_FORMAT(created_at, '%d-%m-%Y %H:%i:%s') AS created_at, DATE_FORMAT(updated_at, '%d-%m-%Y %H:%i:%s') AS updated_at FROM reservations ORDER BY id DESC")
        rows = cursor.fetchall()

        for row in rows:
            if isinstance(row["reservation_time"], timedelta):
                row["reservation_time"] = str(row["reservation_time"])  # "14:00:00"
        return rows



# ---------------- Support Tickets ----------------
@router.get("/support_tickets")
def get_tickets():
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id,customer_name,phone,user_message,issue_category,status,DATE_FORMAT(created_at, '%d-%m-%Y %H:%i:%s') AS created_at FROM support_tickets ORDER BY ID DESC")
        return cursor.fetchall()

# ---------------- Menu Items ----------------
@router.get("/menu_items")
def get_menu_items():
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM menu_items")
        return cursor.fetchall()

# ---------------- Orders ----------------
@router.get("/orders")
def get_orders():
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT order_id, status, estimated_time, DATE_FORMAT(created_at, '%d-%m-%Y') AS created_at FROM orders ORDER BY order_id DESC")
        return cursor.fetchall()
    

@router.put("/orders/{order_id}")
def update_order_status(order_id: int, data: dict = Body(...)):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE orders SET status = %s WHERE order_id = %s",
            (data["status"], order_id)  # ✅ use dict key
        )
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Order not found")

        return {"message": "Order status updated successfully"}
    
# ---------------- Order Items ----------------
@router.get("/order_items")
def get_order_items():
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, order_id, customer_name,phone,food_item,quantity,DATE_FORMAT(created_at,'%Y-%m-%d %H:%i:%s') AS created_at FROM order_items ORDER BY ID DESC")
        return cursor.fetchall()


@router.get("/customer_feedback")
def get_feedback():
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id,customer_name,phone,feedback_text,source_platform,DATE_FORMAT(submitted_at, '%Y-%m-%d %H:%i:%s') as submitted_at FROM customer_feedback ORDER BY ID DESC")
        return cursor.fetchall()
