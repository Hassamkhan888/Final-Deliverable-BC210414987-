import mysql.connector
from typing import Iterator, List, Tuple, Dict, Optional, Union, Any
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

def verify_tables() -> bool:
    """Verify all required tables exist with correct structure"""
    return (verify_reservations_table() and 
            verify_feedback_table() and 
            verify_orders_table() and
            verify_support_tickets_table())

def verify_reservations_table() -> bool:
    """Verify the reservations table has required columns"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SHOW COLUMNS FROM reservations")
            columns = {column[0] for column in cursor.fetchall()}
            required_columns = {'id', 'guests', 'reservation_date', 'reservation_time', 'status'}
            if not required_columns.issubset(columns):
                missing = required_columns - columns
                logger.error(f"Reservations table missing columns: {missing}")
                return False
            return True
    except Exception as e:
        logger.error(f"Error verifying reservations table: {e}")
        return False

def verify_feedback_table() -> bool:
    """Verify the customer_feedback table exists with required columns"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES LIKE 'customer_feedback'")
            if not cursor.fetchone():
                logger.info("Creating customer_feedback table...")
                cursor.execute("""
                    CREATE TABLE customer_feedback (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        session_id VARCHAR(255),
                        customer_name VARCHAR(100),
                        phone VARCHAR(20),
                        feedback_text TEXT NOT NULL,
                        source_platform VARCHAR(50) DEFAULT 'chatbot',
                        submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_feedback_session (session_id)
                    ) ENGINE=InnoDB
                """)
                conn.commit()
                return True
                
            cursor.execute("SHOW COLUMNS FROM customer_feedback")
            columns = {column[0] for column in cursor.fetchall()}
            required_columns = {'id', 'session_id', 'customer_name', 'phone', 'feedback_text', 'source_platform', 'submitted_at'}
            if not required_columns.issubset(columns):
                missing = required_columns - columns
                logger.error(f"customer_feedback table missing columns: {missing}")
                return False
            return True
    except Exception as e:
        logger.error(f"Error verifying feedback table: {e}")
        return False

def verify_support_tickets_table() -> bool:
    """Verify the support_tickets table exists with required columns"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES LIKE 'support_tickets'")
            if not cursor.fetchone():
                logger.info("Creating support_tickets table...")
                cursor.execute("""
                    CREATE TABLE support_tickets (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        session_id VARCHAR(255) NOT NULL,
                        customer_name VARCHAR(100),
                        phone VARCHAR(20),
                        user_message TEXT NOT NULL,
                        issue_category VARCHAR(50) NOT NULL,
                        status ENUM('open','in_progress','resolved','closed') DEFAULT 'open',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB
                """)
                conn.commit()
                return True
                
            cursor.execute("SHOW COLUMNS FROM support_tickets")
            columns = {column[0] for column in cursor.fetchall()}
            required_columns = {'id', 'session_id', 'customer_name', 'phone', 'user_message', 'issue_category', 'status', 'created_at'}
            if not required_columns.issubset(columns):
                missing = required_columns - columns
                logger.error(f"support_tickets table missing columns: {missing}")
                return False
            return True
    except Exception as e:
        logger.error(f"Error verifying support tickets table: {e}")
        return False

def verify_orders_table() -> bool:
    """Verify the orders table has required columns"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SHOW COLUMNS FROM orders")
            columns = {column[0] for column in cursor.fetchall()}
            required_columns = {'order_id', 'status', 'estimated_time'}
            if not required_columns.issubset(columns):
                missing = required_columns - columns
                logger.error(f"Orders table missing columns: {missing}")
                return False
            return True
    except Exception as e:
        logger.error(f"Error verifying orders table: {e}")
        return False

def extract_name_value(name_param: Any) -> Optional[str]:
    """Extract name value from parameter which might be a string or dict"""
    if isinstance(name_param, dict) and 'name' in name_param:
        return name_param['name']
    elif isinstance(name_param, str):
        return name_param
    return None

def submit_customer_feedback(
    user_id: Optional[str], 
    name: Any,
    phone_number: Optional[str],
    feedback_text: str, 
    source_platform: str = "chatbot"
) -> Tuple[bool, str]:
    """Submit customer feedback to the database with additional fields"""
    try:
        # Extract name value if it's a dictionary
        name_value = extract_name_value(name)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO customer_feedback 
                (session_id, customer_name, phone, feedback_text, source_platform)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, name_value, phone_number, feedback_text, source_platform))
            conn.commit()
            return True, "Feedback submitted successfully"
    except mysql.connector.Error as err:
        logger.error(f"Database error submitting feedback: {err}")
        return False, f"Database error: {err}"
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        return False, f"Failed to submit feedback: {str(e)}"

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

def create_support_ticket(
    session_id: str, 
    name: Any,
    phone_number: Optional[str],
    issue_type: str, 
    description: str
) -> Tuple[bool, str]:
    """Create a new support ticket in the database with enhanced fields"""
    try:
        # Extract name value if it's a dictionary
        name_value = extract_name_value(name)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO support_tickets 
                (session_id, customer_name, phone, user_message, issue_category, status)
                VALUES (%s, %s, %s, %s, %s, 'open')
            """, (session_id, name_value, phone_number, description, issue_type))
            conn.commit()
            return True, "Support ticket created successfully"
    except Exception as e:
        logger.error(f"Error creating support ticket: {e}")
        return False, f"Failed to create support ticket: {str(e)}"

def create_reservation(guests: int, datetime_param: Union[str, dict, list]) -> Tuple[bool, str, Optional[int]]:
    """Create a new reservation in the database"""
    try:
        if not verify_reservations_table():
            return False, "Reservations system unavailable", None
            
        # Validate guest count
        try:
            guests = int(guests)
            if guests < 1 or guests > 20:
                return False, "Number of guests must be between 1 and 20", None
        except (ValueError, TypeError):
            return False, "Please enter a valid number of guests (1-20)", None

        # Parse datetime parameter
        datetime_str = ""
        if isinstance(datetime_param, dict) and 'date_time' in datetime_param:
            datetime_str = datetime_param['date_time']
        elif isinstance(datetime_param, list) and len(datetime_param) > 0 and isinstance(datetime_param[0], dict) and 'date_time' in datetime_param[0]:
            datetime_str = datetime_param[0]['date_time']
        elif isinstance(datetime_param, str):
            datetime_str = datetime_param
        else:
            return False, "Invalid datetime format", None

        # Parse datetime with multiple format support
        try:
            # Add new formats to support 2-digit years (e.g., "10 jan 25 2 pm")
            natural_formats = [
                '%d %b %y %I %p', '%d %B %y %I %p',  # 10 Jan 25 10 PM (with 2-digit year)
                '%d %b %I %p', '%d %B %I %p',  # 10 Jan 10 PM
                '%b %d %I %p', '%B %d %I %p',  # Jan 10 10 PM
                '%d %b %H:%M', '%d %B %H:%M',  # 10 Jan 22:00
                '%b %d %H:%M', '%B %d %H:%M'   # Jan 10 22:00
            ]
            
            dt_obj = None
            for fmt in natural_formats:
                try:
                    dt_obj = datetime.strptime(datetime_str, fmt)
                    break
                except ValueError:
                    continue
            
            # If natural formats didn't work, try ISO format
            if dt_obj is None and 'T' in datetime_str:
                if '+' in datetime_str:
                    datetime_str = datetime_str.split('+')[0]
                dt_obj = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S')
            
            if dt_obj is None:
                raise ValueError("Unrecognized datetime format")

            # Handle year assignment for dates without year
            if dt_obj.year == 1900:  # Default year when not specified
                current_year = datetime.now().year
                dt_obj = dt_obj.replace(year=current_year)
                # Handle year rollover if date is in the past
                if dt_obj < datetime.now():
                    dt_obj = dt_obj.replace(year=current_year + 1)

            reservation_date = dt_obj.date()
            reservation_time = dt_obj.time()
            
        except ValueError as e:
            logger.error(f"DateTime parsing error: {e}")
            return False, "Please use format like '10 Jan 10 AM', '10 Jan 25 2 PM', or 'January 10 2 PM'", None

        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check for existing reservations
            cursor.execute("""
                SELECT 1 FROM reservations 
                WHERE reservation_date = %s 
                AND reservation_time = %s
                LIMIT 1
            """, (reservation_date, reservation_time.strftime('%H:%M:%S')))
            
            if cursor.fetchone():
                return False, "This time slot is already booked. Please choose another time.", None
            
            # Insert new reservation
            cursor.execute("""
                INSERT INTO reservations 
                (guests, reservation_date, reservation_time, status)
                VALUES (%s, %s, %s, 'confirmed')
            """, (
                guests,
                reservation_date,
                reservation_time.strftime('%H:%M:%S')
            ))
            
            reservation_id = cursor.lastrowid
            conn.commit()
            
            return True, "Reservation created successfully", reservation_id
                
    except mysql.connector.Error as err:
        logger.error(f"Database error: {err}")
        return False, f"Database error: {err}", None
    except Exception as e:
        logger.error(f"Error creating reservation: {str(e)}")
        return False, f"Failed to create reservation: {str(e)}", None