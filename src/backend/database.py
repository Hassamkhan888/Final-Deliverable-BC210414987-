import mysql.connector
from typing import Iterator, List, Tuple, Dict, Optional, Union
from contextlib import contextmanager
from mysql.connector.connection import MySQLConnection
from datetime import datetime, timedelta
import random
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Khan@123",
    "database": "restaurant_db",
    "autocommit": True
}

@contextmanager
def get_db_connection() -> Iterator[MySQLConnection]:
    """Establish and return a database connection with context manager"""
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        yield conn
    except mysql.connector.Error as err:
        logger.error(f"Database connection error: {err}")
        raise Exception(f"Database Connection Error: {err}")
    finally:
        if conn and conn.is_connected():
            conn.close()

def verify_reservations_table() -> bool:
    """Verify the reservations table exists and has correct structure"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SHOW COLUMNS FROM reservations LIKE 'reservation_date'
            """)
            if not cursor.fetchone():
                logger.error("Reservations table missing or has incorrect structure")
                return False
            return True
    except Exception as e:
        logger.error(f"Error verifying reservations table: {e}")
        return False

def create_order(items: List[Tuple[str, int]]) -> Tuple[bool, str, Optional[int]]:
    """Create a new order in the database"""
    if not items:
        return False, "No items in order", None

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            estimated_time = (datetime.now() + timedelta(minutes=random.randint(20, 40))).strftime('%H:%M')
            
            cursor.execute("""
                INSERT INTO orders (status, estimated_time)
                VALUES ('Confirmed', %s)
            """, (estimated_time,))
            order_id = cursor.lastrowid

            for item_name, quantity in items:
                clean_item_name = item_name.replace(' ', '_').lower().strip()
                cursor.execute("""
                    INSERT INTO order_items (order_id, food_item, quantity)
                    VALUES (%s, %s, %s)
                """, (order_id, clean_item_name, quantity))

            conn.commit()
            return True, "Order created successfully", order_id
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        return False, f"Failed to create order: {str(e)}", None

def get_order_status(order_id: str) -> Tuple[bool, Optional[Dict], str]:
    """Check order status from database"""
    try:
        clean_id = ''.join(c for c in order_id if c.isdigit())
        if not clean_id:
            return False, None, "invalid_order_id"
        
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT order_id, status, estimated_time FROM orders WHERE order_id = %s", (clean_id,))
            order = cursor.fetchone()
            
            if not order:
                return False, None, "order_not_found"
            
            cursor.execute("SELECT food_item, quantity FROM order_items WHERE order_id = %s", (clean_id,))
            items = cursor.fetchall()
            order['items'] = ", ".join(f"{item['quantity']} {item['food_item'].replace('_', ' ')}" for item in items)
            
            return True, order, ""
    except Exception as e:
        logger.error(f"Error checking order status: {e}")
        return False, None, f"database_error:{str(e)}"

def get_menu_item_details(item_name: str) -> Tuple[bool, Optional[Dict], str]:
    """Get complete menu item details with flexible matching"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Try exact match first
            db_name = item_name.replace(' ', '_').lower()
            cursor.execute("""
                SELECT name, price, in_stock, category 
                FROM menu_items 
                WHERE name = %s
                LIMIT 1
            """, (db_name,))
            item = cursor.fetchone()
            
            if not item:
                # Try partial match if exact not found
                cursor.execute("""
                    SELECT name, price, in_stock, category 
                    FROM menu_items 
                    WHERE name LIKE %s
                    ORDER BY 
                        CASE 
                            WHEN name LIKE %s THEN 1  # Starts with
                            WHEN name LIKE %s THEN 2  # Contains
                            ELSE 3
                        END
                    LIMIT 1
                """, (
                    f"%{db_name}%",
                    f"{db_name}%",
                    f"%{db_name}%"
                ))
                item = cursor.fetchone()
            
            if not item:
                return False, None, "item_not_found"
            
            return True, {
                "name": item['name'].replace('_', ' '),
                "price": float(item['price']),
                "in_stock": bool(item['in_stock']),
                "category": item['category']
            }, ""
    except Exception as e:
        logger.error(f"Error getting menu item: {e}")
        return False, None, f"database_error:{str(e)}"

def create_support_ticket(session_id: str, issue_type: str, description: str) -> Tuple[bool, str]:
    """Create a new support ticket in the database"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO support_tickets 
                (session_id, user_message, issue_category, status)
                VALUES (%s, %s, %s, 'open')
            """, (session_id, description, issue_type))
            conn.commit()
            return True, "Support ticket created successfully"
    except Exception as e:
        logger.error(f"Error creating support ticket: {e}")
        return False, f"Failed to create support ticket: {str(e)}"

def create_reservation(session_id: str, guests: int, date_str: str, time_str: str) -> Tuple[bool, str, Optional[int]]:
    """Create a new reservation in the database with proper date/time formatting"""
    try:
        # First verify the table exists
        if not verify_reservations_table():
            return False, "Reservations system unavailable", None
            
        from datetime import datetime
        
        # Parse date (handle multiple formats)
        try:
            if 'T' in date_str:  # ISO format
                reservation_date = datetime.strptime(date_str.split('T')[0], '%Y-%m-%d').date()
            elif re.match(r'\d{4}-\d{2}-\d{2}', date_str):  # YYYY-MM-DD
                reservation_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:  # Natural language (e.g., "10 jan")
                now = datetime.now()
                try:
                    parsed_date = datetime.strptime(date_str.strip(), '%d %b')
                except ValueError:
                    parsed_date = datetime.strptime(date_str.strip(), '%b %d')
                
                # Handle year rollover
                current_year = now.year
                if (parsed_date.month < now.month) or \
                   (parsed_date.month == now.month and parsed_date.day < now.day):
                    reservation_date = parsed_date.replace(year=current_year + 1).date()
                else:
                    reservation_date = parsed_date.replace(year=current_year).date()
        except ValueError as e:
            logger.error(f"Date parsing error: {e}")
            return False, f"Invalid date format: {date_str}", None

        # Parse time (handle multiple formats)
        try:
            if 'T' in time_str:  # ISO format
                time_part = time_str.split('T')[1].split('+')[0]
                reservation_time = datetime.strptime(time_part, '%H:%M:%S').time()
            else:  # Natural language time
                time_str = time_str.lower().strip()
                if 'am' in time_str or 'pm' in time_str:
                    time_str = re.sub(r'[^a-z0-9]', '', time_str)  # Clean string
                    time_obj = datetime.strptime(time_str, '%I%p')
                    reservation_time = time_obj.time()
                elif ':' in time_str:
                    reservation_time = datetime.strptime(time_str, '%H:%M').time()
                else:
                    hour = int(time_str)
                    if hour < 0 or hour > 23:
                        raise ValueError("Invalid hour")
                    reservation_time = datetime.strptime(f"{hour}:00", '%H:%M').time()
        except ValueError as e:
            logger.error(f"Time parsing error: {e}")
            return False, f"Invalid time format: {time_str}", None

        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Debug before insertion
            logger.info(f"Inserting reservation: session_id={session_id}, guests={guests}, "
                       f"date={reservation_date}, time={reservation_time}")
            
            try:
                cursor.execute("""
                    INSERT INTO reservations 
                    (session_id, guests, reservation_date, reservation_time, status)
                    VALUES (%s, %s, %s, %s, 'pending')
                """, (
                    session_id,
                    guests,
                    reservation_date,
                    reservation_time.strftime('%H:%M:%S')
                ))
                
                reservation_id = cursor.lastrowid
                conn.commit()
                
                # Verify insertion
                cursor.execute("SELECT 1 FROM reservations WHERE id = %s", (reservation_id,))
                if not cursor.fetchone():
                    logger.error("Insert failed - no record created")
                    return False, "Reservation failed", None
                
                logger.info(f"Reservation {reservation_id} created successfully")
                return True, "Reservation created successfully", reservation_id
                
            except mysql.connector.Error as err:
                logger.error(f"Database error: {err}")
                conn.rollback()
                return False, f"Database error: {err}", None
                
    except Exception as e:
        logger.error(f"Error creating reservation: {str(e)}")
        return False, f"Failed to create reservation: {str(e)}", None