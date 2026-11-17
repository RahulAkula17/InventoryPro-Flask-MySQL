# InventoryPro — Inventory and Sales Management

A minimal relational-database project built with **Python, Flask, MySQL, HTML, Bootstrap and Jinja2**. It demonstrates relational schema design, primary/foreign keys, joins, CRUD, and atomic sales transactions.

## Features
- Dashboard: number of products, customers, suppliers, sales; low-stock list; latest sales
- Full create/read/update/delete for products, categories, suppliers, and customers
- Record sales (one product per sale in this minimal UI), view sales and line items
- Stock automatically decreases after a successful sale
- REST JSON product CRUD API at `/api/products`
- Referential integrity: records referenced by sales cannot be deleted

## Database relationships
- `categories (1) → (many) products`
- `suppliers (1) → (many) products`
- `customers (1) → (many) sales`
- `sales (1) → (many) sale_items`
- `products (1) → (many) sale_items`

`sale_items` resolves the many-to-many relationship between sales and products, although the current create-sale form adds one product per sale. Tables use InnoDB, foreign keys, and numeric checks.

## Re-create locally

**Prerequisites:** Python 3.10+ and a running local MySQL 8.0+ server. Commands below assume Terminal on macOS/Linux; Windows equivalents are listed.

1. Clone the repository or extract the project archive, and enter its folder:
   ```bash
    git clone https://github.com/RahulAkula17/InventoryPro-Flask-MySQL.git
    cd InventoryPro-Flask-MySQL
   ```
   Replace the URL with your real GitHub repository URL after uploading.
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
   Windows PowerShell: `py -m venv .venv` then `.venv\Scripts\Activate.ps1`.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Ensure the MySQL server is running and import the schema and demo data:
   ```bash
   mysql -u root -p < sql/schema.sql
   mysql -u root -p < sql/sample_data.sql
   ```
   If `mysql` is not on your PATH on macOS, use `/usr/local/mysql/bin/mysql` instead. You can alternatively paste the SQL files into MySQL Workbench and execute them in sequence. **Run sample_data.sql only once** on a new database.
5. Make a local `.env` file:
   ```bash
   cp .env.example .env
   ```
   Windows PowerShell: `Copy-Item .env.example .env`. Update `MYSQL_USER` and `MYSQL_PASSWORD` to match your local MySQL installation. Never upload `.env` to GitHub.
6. Start the app:
   ```bash
   python app.py
   ```
   Open **http://127.0.0.1:5000**.
7. Verify the connection at **http://127.0.0.1:5000/api/health**.

## API examples
```bash
# READ all products
curl http://127.0.0.1:5000/api/products

# CREATE (category 1 and supplier 1 exist in sample data)
curl -X POST http://127.0.0.1:5000/api/products \
  -H 'Content-Type: application/json' \
  -d '{"product_name":"Webcam","category_id":1,"supplier_id":1,"price":34.99,"quantity":10,"reorder_level":3}'

# READ single product
curl http://127.0.0.1:5000/api/products/1

# UPDATE product 1
curl -X PUT http://127.0.0.1:5000/api/products/1 \
  -H 'Content-Type: application/json' \
  -d '{"product_name":"Wireless Mouse","category_id":1,"supplier_id":1,"price":22.99,"quantity":25,"reorder_level":5}'

# DELETE a newly created product (replace ID; products in past sales cannot be deleted)
curl -X DELETE http://127.0.0.1:5000/api/products/7
```

## Demo script
1. Open **Dashboard**; explain aggregate counts and low-stock query.
2. Open **Products**; add an item, edit price, then delete it.
3. Open **Categories / Suppliers / Customers**; demonstrate relational lookup records.
4. Open **Sales → New sale**; select customer/product and quantity; complete sale.
5. Return to **Products** and show quantity reduced; open **Sales** and its detail page.
6. Open `/api/products` to show an API response from a SQL JOIN.

## Limitations
This is a local classroom prototype, **not a production-deployed system**. There is no user login, CSRF protection, or access control; run it only on your machine. The sale form currently supports one product per sale; the database design supports multiple. Database error messages are intended for local debugging and should not be exposed in production. For production, disable Flask debug mode and configure authentication, CSRF protection, input limits, and more robust error handling.

## Screenshots and final submission
Capture your *running* dashboard, products page, new product form, and sales page and add screenshots to `screenshots/` for the report. Insert the actual GitHub URL in the final report and presentation.
