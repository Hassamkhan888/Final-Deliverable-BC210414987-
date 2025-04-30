CREATE DATABASE restaurant_db;
USE restaurant_db;



-- 2. Customers table
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL DEFAULT 'Guest',
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT IGNORE INTO customers (customer_id, name) VALUES (1, 'Guest Customer');

-- 3. Orders table
CREATE TABLE IF NOT EXISTS orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL DEFAULT 1,
    status ENUM('Pending','Confirmed','Preparing','On the way','Delivered','Cancelled') DEFAULT 'Pending',
    estimated_time VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
) AUTO_INCREMENT=1000;

-- 4. Order items table
CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    food_item VARCHAR(100) NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS `menu_items` (
  `item_id` INT AUTO_INCREMENT PRIMARY KEY,  -- Unique identifier for each menu item
  `name` VARCHAR(50) NOT NULL UNIQUE,        -- Name of the menu item (e.g., "pepsi")
  `price` DECIMAL(10,2) NOT NULL,            -- Price of the item
  `in_stock` BOOLEAN DEFAULT TRUE,           -- Availability status (TRUE if in stock)
  `category` ENUM('Appetizers','Main Course','Desserts','Beverages') NOT NULL,  -- Item category
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Date and time the item was added to the menu
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `menu_items` (`name`, `price`, `category`, `in_stock`) VALUES
('pepsi', 1.99, 'Beverages', 1),
('chicken_biryani', 12.99, 'Main Course', 1),
('samosa', 3.49, 'Appetizers', 0),
('chocolate_lava', 5.99, 'Desserts', 1),
('beef_burger', 8.99, 'Main Course', 1),
('mutton_karahi', 14.99, 'Main Course', 1),
('garlic_naan', 2.49, 'Main Course', 1),
('seekh_kebab', 9.99, 'Main Course', 1);

CREATE TABLE support_tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL COMMENT 'Unique chat session ID from Dialogflow',
    user_message TEXT NOT NULL COMMENT 'What the user said (e.g., "My device isn\'t working")',
    issue_category VARCHAR(50) NOT NULL COMMENT 'General problem type (e.g., technical, support)',
    status VARCHAR(20) DEFAULT 'open' COMMENT 'Ticket status: open, resolved, or closed',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE reservations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL COMMENT 'Unique chat session ID from Dialogflow',
    guests INT NOT NULL COMMENT 'Number of people for the reservation',
    reservation_date DATE NOT NULL COMMENT 'Date of the reservation',
    reservation_time TIME NOT NULL COMMENT 'Time of the reservation',
    status VARCHAR(20) DEFAULT 'pending' COMMENT 'Reservation status: pending, confirmed, or canceled',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);



DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS products;
Drop table cart_items;

select * From reservations;
Select * From support_tickets;
Select * From cart_items;
Select * From menu_items;
SELECT * FROM orders;
SELECT * FROM order_items;
SELECT * FROM customers;
Drop table customers;

DELETE FROM menu_items
WHERE item_id > 0;


show tables;
drop table menu_items;
drop table products;
drop table restaurants;