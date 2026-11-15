"""InventoryPro: a minimal Flask + MySQL inventory/sales system."""
from decimal import Decimal, InvalidOperation
import os
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
from mysql.connector import Error, IntegrityError
from database import get_db

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'local-development-only-change-me')


def query_all(sql, params=()):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def query_one(sql, params=()):
    rows = query_all(sql, params)
    return rows[0] if rows else None


def execute(sql, params=()):
    connection = get_db()
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
        connection.commit()
        return cursor.lastrowid
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def as_money(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError('Price must be a valid number')
    if not amount.is_finite() or amount < 0 or amount > Decimal('99999999.99'):
        raise ValueError('Price must be between 0 and 99999999.99')
    if amount != amount.quantize(Decimal('0.01')):
        raise ValueError('Use no more than two decimal places for price')
    return amount


def positive_int(value, label, allow_zero=False):
    try:
        result = int(str(value))
    except (ValueError, TypeError):
        raise ValueError(f'{label} must be an integer')
    if result < (0 if allow_zero else 1):
        raise ValueError(f'{label} must be {"zero or greater" if allow_zero else "greater than zero"}')
    return result


def product_values(data):
    name = str(data.get('product_name', '')).strip()
    if not name or len(name) > 150:
        raise ValueError('Product name is required (maximum 150 characters)')
    return (
        name,
        positive_int(data.get('category_id'), 'Category'),
        positive_int(data.get('supplier_id'), 'Supplier'),
        as_money(data.get('price')),
        positive_int(data.get('quantity'), 'Quantity', allow_zero=True),
        positive_int(data.get('reorder_level', 5), 'Reorder level', allow_zero=True),
    )


def products_query():
    return '''SELECT p.product_id, p.product_name, p.category_id, p.supplier_id,
                     p.price, p.quantity, p.reorder_level,
                     c.category_name, s.supplier_name
              FROM products AS p
              INNER JOIN categories AS c ON p.category_id = c.category_id
              INNER JOIN suppliers AS s ON p.supplier_id = s.supplier_id'''


@app.route('/')
def dashboard():
    stats = query_one('''SELECT (SELECT COUNT(*) FROM products) AS products,
                                (SELECT COUNT(*) FROM customers) AS customers,
                                (SELECT COUNT(*) FROM suppliers) AS suppliers,
                                (SELECT COUNT(*) FROM sales) AS sales''')
    low_stock = query_all('''SELECT product_name, quantity, reorder_level FROM products
                             WHERE quantity <= reorder_level ORDER BY quantity ASC''')
    recent_sales = query_all('''SELECT s.sale_id, s.sale_date, s.total_amount, c.customer_name
                                FROM sales s JOIN customers c ON c.customer_id=s.customer_id
                                ORDER BY s.sale_date DESC, s.sale_id DESC LIMIT 5''')
    return render_template('dashboard.html', stats=stats, low_stock=low_stock, recent_sales=recent_sales)


@app.route('/products')
def products():
    return render_template('products.html', products=query_all(products_query() + ' ORDER BY p.product_id DESC'))


@app.route('/products/new', methods=['GET', 'POST'])
def new_product():
    if request.method == 'POST':
        try:
            values = product_values(request.form)
            execute('''INSERT INTO products
                       (product_name, category_id, supplier_id, price, quantity, reorder_level)
                       VALUES (%s,%s,%s,%s,%s,%s)''', values)
            flash('Product added successfully.', 'success')
            return redirect(url_for('products'))
        except (ValueError, Error) as exc:
            flash(f'Could not add product: {exc}', 'danger')
    return render_template('product_form.html', product=None, categories=query_all('SELECT * FROM categories ORDER BY category_name'), suppliers=query_all('SELECT * FROM suppliers ORDER BY supplier_name'))


@app.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
def edit_product(product_id):
    product = query_one('SELECT * FROM products WHERE product_id=%s', (product_id,))
    if not product:
        return ('Product not found', 404)
    if request.method == 'POST':
        try:
            values = product_values(request.form)
            execute('''UPDATE products SET product_name=%s, category_id=%s,
                       supplier_id=%s, price=%s, quantity=%s, reorder_level=%s
                       WHERE product_id=%s''', values + (product_id,))
            flash('Product updated successfully.', 'success')
            return redirect(url_for('products'))
        except (ValueError, Error) as exc:
            flash(f'Could not update product: {exc}', 'danger')
    return render_template('product_form.html', product=product, categories=query_all('SELECT * FROM categories ORDER BY category_name'), suppliers=query_all('SELECT * FROM suppliers ORDER BY supplier_name'))


@app.post('/products/<int:product_id>/delete')
def delete_product(product_id):
    try:
        execute('DELETE FROM products WHERE product_id=%s', (product_id,))
        flash('Product deleted (if it existed).', 'success')
    except IntegrityError:
        flash('Cannot delete a product referenced by past sales.', 'danger')
    return redirect(url_for('products'))


# Lightweight, usable CRUD pages for categories, suppliers, and customers.
RESOURCES = {
    'categories': ('category_id', ['category_name', 'description'], 'Categories'),
    'suppliers': ('supplier_id', ['supplier_name', 'email', 'phone'], 'Suppliers'),
    'customers': ('customer_id', ['customer_name', 'email', 'phone'], 'Customers'),
}


@app.route('/manage/<resource>', methods=['GET', 'POST'])
def manage(resource):
    if resource not in RESOURCES:
        return ('Not found', 404)
    pk, fields, title = RESOURCES[resource]
    if request.method == 'POST':
        values = [request.form.get(field, '').strip() or None for field in fields]
        if not values[0]:
            flash(f'{fields[0].replace("_", " ").title()} is required.', 'danger')
        else:
            try:
                columns = ', '.join(fields)
                placeholders = ', '.join(['%s'] * len(fields))
                execute(f'INSERT INTO {resource} ({columns}) VALUES ({placeholders})', values)
                flash('Record added successfully.', 'success')
            except Error as exc:
                flash(f'Could not save: {exc}', 'danger')
        return redirect(url_for('manage', resource=resource))
    rows = query_all(f'SELECT * FROM {resource} ORDER BY {pk} DESC')
    return render_template('manage.html', resource=resource, pk=pk, fields=fields, title=title, rows=rows)


@app.post('/manage/<resource>/<int:record_id>/update')
def update_resource(resource, record_id):
    if resource not in RESOURCES:
        return ('Not found', 404)
    pk, fields, _ = RESOURCES[resource]
    values = [request.form.get(field, '').strip() or None for field in fields]
    if not values[0]:
        flash('Name is required.', 'danger')
    else:
        try:
            setters = ', '.join(f'{field}=%s' for field in fields)
            execute(f'UPDATE {resource} SET {setters} WHERE {pk}=%s', values + [record_id])
            flash('Record updated.', 'success')
        except Error as exc:
            flash(f'Could not update: {exc}', 'danger')
    return redirect(url_for('manage', resource=resource))


@app.post('/manage/<resource>/<int:record_id>/delete')
def delete_resource(resource, record_id):
    if resource not in RESOURCES:
        return ('Not found', 404)
    pk, _, _ = RESOURCES[resource]
    try:
        execute(f'DELETE FROM {resource} WHERE {pk}=%s', (record_id,))
        flash('Record deleted.', 'success')
    except IntegrityError:
        flash('Record is referenced by other records and cannot be deleted.', 'danger')
    return redirect(url_for('manage', resource=resource))


@app.route('/sales')
def sales():
    rows = query_all('''SELECT s.sale_id, s.sale_date, s.total_amount, c.customer_name
                        FROM sales s JOIN customers c ON s.customer_id=c.customer_id
                        ORDER BY s.sale_id DESC''')
    return render_template('sales.html', sales=rows)


@app.route('/sales/new', methods=['GET', 'POST'])
def new_sale():
    if request.method == 'POST':
        connection = None
        cursor = None
        try:
            customer_id = positive_int(request.form.get('customer_id'), 'Customer')
            product_id = positive_int(request.form.get('product_id'), 'Product')
            quantity = positive_int(request.form.get('quantity'), 'Quantity')
            connection = get_db()
            connection.start_transaction()
            cursor = connection.cursor(dictionary=True)
            cursor.execute('SELECT customer_id FROM customers WHERE customer_id=%s', (customer_id,))
            if not cursor.fetchone():
                raise ValueError('Customer does not exist')
            cursor.execute('SELECT product_id, price, quantity FROM products WHERE product_id=%s FOR UPDATE', (product_id,))
            product = cursor.fetchone()
            if not product:
                raise ValueError('Product does not exist')
            if quantity > product['quantity']:
                raise ValueError(f'Insufficient stock: only {product["quantity"]} available')
            total = product['price'] * quantity
            cursor.execute('INSERT INTO sales (customer_id, total_amount) VALUES (%s,%s)', (customer_id, total))
            sale_id = cursor.lastrowid
            cursor.execute('INSERT INTO sale_items (sale_id, product_id, quantity, unit_price) VALUES (%s,%s,%s,%s)', (sale_id, product_id, quantity, product['price']))
            cursor.execute('UPDATE products SET quantity=quantity-%s WHERE product_id=%s', (quantity, product_id))
            connection.commit()
            flash(f'Sale #{sale_id} created. Inventory updated.', 'success')
            return redirect(url_for('sales'))
        except (ValueError, Error) as exc:
            if connection:
                connection.rollback()
            flash(f'Could not create sale: {exc}', 'danger')
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    return render_template('sale_form.html', customers=query_all('SELECT * FROM customers ORDER BY customer_name'), products=query_all('SELECT * FROM products ORDER BY product_name'))


@app.route('/sales/<int:sale_id>')
def sale_detail(sale_id):
    sale = query_one('''SELECT s.*, c.customer_name FROM sales s
                        JOIN customers c ON s.customer_id=c.customer_id WHERE s.sale_id=%s''', (sale_id,))
    if not sale:
        return ('Sale not found', 404)
    items = query_all('''SELECT si.*, p.product_name FROM sale_items si
                         JOIN products p ON si.product_id=p.product_id WHERE si.sale_id=%s''', (sale_id,))
    return render_template('sale_detail.html', sale=sale, items=items)


# JSON REST API: demonstrate all four operations on products.
@app.get('/api/products')
def api_products():
    return jsonify(query_all(products_query() + ' ORDER BY p.product_id'))


@app.get('/api/products/<int:product_id>')
def api_product(product_id):
    product = query_one(products_query() + ' WHERE p.product_id=%s', (product_id,))
    return (jsonify(product), 200) if product else (jsonify({'error': 'Product not found'}), 404)


@app.post('/api/products')
def api_create_product():
    try:
        values = product_values(request.get_json(silent=True) or {})
        new_id = execute('''INSERT INTO products (product_name, category_id, supplier_id, price, quantity, reorder_level)
                            VALUES (%s,%s,%s,%s,%s,%s)''', values)
        return jsonify({'message': 'Product created', 'product_id': new_id}), 201
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    except IntegrityError:
        return jsonify({'error': 'Invalid category or supplier'}), 400


@app.put('/api/products/<int:product_id>')
def api_update_product(product_id):
    if not query_one('SELECT product_id FROM products WHERE product_id=%s', (product_id,)):
        return jsonify({'error': 'Product not found'}), 404
    try:
        values = product_values(request.get_json(silent=True) or {})
        execute('''UPDATE products SET product_name=%s, category_id=%s, supplier_id=%s,
                   price=%s, quantity=%s, reorder_level=%s WHERE product_id=%s''', values + (product_id,))
        return jsonify({'message': 'Product updated'})
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    except IntegrityError:
        return jsonify({'error': 'Invalid category or supplier'}), 400


@app.delete('/api/products/<int:product_id>')
def api_delete_product(product_id):
    if not query_one('SELECT product_id FROM products WHERE product_id=%s', (product_id,)):
        return jsonify({'error': 'Product not found'}), 404
    try:
        execute('DELETE FROM products WHERE product_id=%s', (product_id,))
        return jsonify({'message': 'Product deleted'})
    except IntegrityError:
        return jsonify({'error': 'Product is referenced by a sale'}), 409


@app.get('/api/health')
def api_health():
    return jsonify({'status': 'ok', 'database': query_one('SELECT DATABASE() AS name')['name']})


if __name__ == "__main__":
    app.run(debug=True, port=5001)
