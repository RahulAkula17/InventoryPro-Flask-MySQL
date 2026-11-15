USE inventorypro;
-- Run once after schema.sql. Re-running will add duplicate suppliers/customers/products.
INSERT INTO categories (category_name, description) VALUES
('Electronics', 'Electronic accessories and devices'),
('Office Supplies', 'Office and desk essentials'),
('Furniture', 'Office furniture');

INSERT INTO suppliers (supplier_name, email, phone) VALUES
('TechSource Wholesale', 'sales@techsource.example', '555-0101'),
('OfficeHub Distribution', 'support@officehub.example', '555-0102'),
('DeskWorks Co.', 'orders@deskworks.example', '555-0103');

INSERT INTO customers (customer_name, email, phone) VALUES
('Alex Johnson', 'alex@example.com', '555-1001'),
('Morgan Lee', 'morgan@example.com', '555-1002'),
('Taylor Smith', 'taylor@example.com', '555-1003');

INSERT INTO products (product_name, category_id, supplier_id, price, quantity, reorder_level) VALUES
('Wireless Mouse', 1, 1, 24.99, 30, 5),
('Mechanical Keyboard', 1, 1, 79.99, 15, 5),
('USB-C Hub', 1, 1, 39.50, 4, 8),
('Notebook Pack', 2, 2, 12.99, 48, 10),
('Desk Organizer', 2, 2, 18.00, 3, 5),
('Adjustable Monitor Stand', 3, 3, 49.99, 8, 4);
