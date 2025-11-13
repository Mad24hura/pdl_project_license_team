from flask import Flask, render_template, request, redirect, url_for, session, flash
import csv
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Helper functions for CSV operations
def read_csv(path):
    """Read CSV file and return list of dictionaries with error handling"""
    try:
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except FileNotFoundError:
        print(f"Warning: CSV file {path} not found")
        return []
    except Exception as e:
        print(f"Error reading CSV file {path}: {e}")
        return []

def safe_get(row, key, default=''):
    """Safely get a value from a dictionary with a default fallback"""
    return row.get(key, default) if isinstance(row, dict) else default

def validate_csv_data(data, required_fields, data_type="unknown"):
    """Validate CSV data and log any issues"""
    if not isinstance(data, list):
        print(f"Warning: {data_type} data is not a list")
        return False
    
    if not data:
        print(f"Warning: {data_type} data is empty")
        return False
    
    for i, row in enumerate(data):
        if not isinstance(row, dict):
            print(f"Warning: Row {i} in {data_type} is not a dictionary")
            continue
            
        for field in required_fields:
            if field not in row:
                print(f"Warning: Missing field '{field}' in row {i} of {data_type}")
    
    return True

def backup_csv_files():
    """Create backup of all CSV files"""
    import shutil
    from datetime import datetime
    
    backup_dir = f"backups/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    csv_files = ['data/licenses.csv', 'data/requests.csv', 'data/users.csv']
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            shutil.copy2(csv_file, backup_dir)
    
    print(f"Backup created in {backup_dir}")
    return backup_dir

def write_csv(path, fieldnames, rows):
    """Write list of dictionaries to CSV file"""
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def add_row(path, fieldnames, new_row):
    """Add a new row to CSV file"""
    rows = read_csv(path)
    rows.append(new_row)
    write_csv(path, fieldnames, rows)

def categorize_licenses():
    """Categorize licenses into active, expiring, and expired"""
    today = datetime.today().date()
    active, expiring, expired = [], [], []
    
    licenses = read_csv('data/licenses.csv')
    required_fields = ['id', 'expiry_date', 'status']
    validate_csv_data(licenses, required_fields, "licenses")
    
    for lic in licenses:
        try:
            exp_date_str = safe_get(lic, 'expiry_date', '')
            status = safe_get(lic, 'status', '')
            
            if not exp_date_str or not status:
                print(f"Warning: License {safe_get(lic, 'id', 'unknown')} missing expiry_date or status")
                continue
                
            exp_date = datetime.strptime(exp_date_str, '%Y-%m-%d').date()
            days_left = (exp_date - today).days
            
            if days_left > 30:
                active.append(lic)
            elif 0 <= days_left <= 30:
                expiring.append(lic)
            else:
                expired.append(lic)
        except ValueError as e:
            print(f"Warning: Invalid date format for license {safe_get(lic, 'id', 'unknown')}: {e}")
            continue
        except Exception as e:
            print(f"Error processing license {safe_get(lic, 'id', 'unknown')}: {e}")
            continue
    
    return active, expiring, expired

def get_dashboard_stats():
    """Get statistics for dashboard cards"""
    licenses = read_csv('data/licenses.csv')
    requests = read_csv('data/requests.csv')
    
    # Validate data
    validate_csv_data(licenses, ['id', 'status'], "licenses")
    validate_csv_data(requests, ['request_id', 'status'], "requests")
    
    active, expiring, expired = categorize_licenses()
    
    return {
        'total_licenses': len(licenses),
        'active_licenses': len(active),
        'expiring_licenses': len(expiring),
        'expired_licenses': len(expired),
        'pending_requests': len([r for r in requests if safe_get(r, 'status') == 'Pending'])
    }

# Routes
@app.route('/')
@app.route('/login')
def login():
    if 'user' in session:
        if safe_get(session['user'], 'role') == 'Admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']
    
    users = read_csv('data/users.csv')
    
    for user in users:
        if (safe_get(user, 'username') == username and 
            safe_get(user, 'password') == password and 
            safe_get(user, 'role') == role):
            session['user'] = user
            if role == 'Admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
    
    flash('Invalid credentials. Please try again.', 'error')
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user' not in session or safe_get(session['user'], 'role') != 'Admin':
        return redirect(url_for('login'))
    
    stats = get_dashboard_stats()
    return render_template('admin_dashboard.html', stats=stats)

@app.route('/user_dashboard')
def user_dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    username = safe_get(session['user'], 'username', '')
    user_department = safe_get(session['user'], 'department', '')
    
    if not username:
        flash('User session invalid. Please login again.', 'error')
        return redirect(url_for('login'))
    
    stats = get_dashboard_stats()
    
    # Get user-specific data with validation
    all_requests = read_csv('data/requests.csv')
    all_licenses = read_csv('data/licenses.csv')
    
    validate_csv_data(all_requests, ['request_id', 'username'], "requests")
    validate_csv_data(all_licenses, ['id', 'assigned_department'], "licenses")
    
    user_requests = [r for r in all_requests if safe_get(r, 'username') == username]
    user_licenses = [l for l in all_licenses if safe_get(l, 'assigned_department') == user_department]
    
    return render_template('user_dashboard.html', 
                         stats=stats, 
                         user_requests=user_requests,
                         user_licenses=user_licenses)

@app.route('/add_license', methods=['GET', 'POST'])
def add_license():
    if 'user' not in session or safe_get(session['user'], 'role') != 'Admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            # Validate required fields
            required_fields = ['name', 'category', 'key', 'department', 'start_date', 'expiry_date']
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'Please fill in the {field} field.', 'error')
                    return redirect(url_for('add_license'))
            
            # Validate date format
            try:
                start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
                expiry_date = datetime.strptime(request.form['expiry_date'], '%Y-%m-%d')
                if expiry_date <= start_date:
                    flash('Expiry date must be after start date.', 'error')
                    return redirect(url_for('add_license'))
            except ValueError:
                flash('Please enter dates in YYYY-MM-DD format.', 'error')
                return redirect(url_for('add_license'))
            
            license_data = {
                'id': f"L{len(read_csv('data/licenses.csv')) + 1:03d}",
                'software_name': request.form['name'],
                'category': request.form['category'],
                'license_key': request.form['key'],
                'assigned_department': request.form['department'],
                'assigned_device': request.form.get('assigned_device', 'Not assigned'),
                'start_date': request.form['start_date'],
                'expiry_date': request.form['expiry_date'],
                'status': 'Active'
            }
            
            fieldnames = ['id', 'software_name', 'category', 'license_key', 'assigned_department', 'assigned_device', 'start_date', 'expiry_date', 'status']
            add_row('data/licenses.csv', fieldnames, license_data)
            flash('License added successfully!', 'success')
            return redirect(url_for('view_licenses'))
        except Exception as e:
            flash(f'Error adding license: {str(e)}', 'error')
            return redirect(url_for('add_license'))
    
    users = read_csv('data/users.csv')
    return render_template('add_license.html', users=users)

@app.route('/view_licenses')
def view_licenses():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    active, expiring, expired = categorize_licenses()
    return render_template('view_licenses.html', 
                         active=active, 
                         expiring=expiring, 
                         expired=expired)

@app.route('/requests')
def requests():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    all_requests = read_csv('data/requests.csv')
    
    # Filter requests based on user role
    if safe_get(session['user'], 'role') == 'Admin':
        # Admin sees all requests
        filtered_requests = all_requests
    else:
        # Users see only their own requests
        username = safe_get(session['user'], 'username', '')
        filtered_requests = [r for r in all_requests if safe_get(r, 'username') == username]
    
    return render_template('requests.html', requests=filtered_requests)

@app.route('/approve_request/<request_id>')
def approve_request(request_id):
    if 'user' not in session or safe_get(session['user'], 'role') != 'Admin':
        return redirect(url_for('login'))
    
    requests = read_csv('data/requests.csv')
    for req in requests:
        if safe_get(req, 'request_id') == request_id:
            req['status'] = 'Approved'
            break
    
    fieldnames = ['request_id', 'username', 'software_name', 'reason', 'date', 'status', 'device']
    write_csv('data/requests.csv', fieldnames, requests)
    flash('Request approved successfully!', 'success')
    return redirect(url_for('requests'))

@app.route('/reject_request/<request_id>')
def reject_request(request_id):
    if 'user' not in session or safe_get(session['user'], 'role') != 'Admin':
        return redirect(url_for('login'))
    
    requests = read_csv('data/requests.csv')
    for req in requests:
        if safe_get(req, 'request_id') == request_id:
            req['status'] = 'Rejected'
            break
    
    fieldnames = ['request_id', 'username', 'software_name', 'reason', 'date', 'status', 'device']
    write_csv('data/requests.csv', fieldnames, requests)
    flash('Request rejected.', 'info')
    return redirect(url_for('requests'))

@app.route('/manage_users')
def manage_users():
    if 'user' not in session or safe_get(session['user'], 'role') != 'Admin':
        return redirect(url_for('login'))
    
    users = read_csv('data/users.csv')
    show_form = request.args.get('show_form', '')
    return render_template('manage_users.html', users=users, show_form=show_form)

@app.route('/add_user', methods=['POST'])
def add_user():
    if 'user' not in session or safe_get(session['user'], 'role') != 'Admin':
        return redirect(url_for('login'))
    
    try:
        # Validate required fields
        required_fields = ['username', 'password', 'role']
        for field in required_fields:
            if not request.form.get(field):
                flash(f'Please fill in the {field} field.', 'error')
                return redirect(url_for('manage_users'))
        
        # Check if username already exists
        existing_users = read_csv('data/users.csv')
        username = request.form['username']
        if any(safe_get(user, 'username') == username for user in existing_users):
            flash('Username already exists. Please choose a different username.', 'error')
            return redirect(url_for('manage_users'))
        
        user_data = {
            'username': username,
            'password': request.form['password'],
            'role': request.form['role'],
            'email': request.form.get('email', ''),
            'department': request.form.get('department', ''),
            'status': 'Active'
        }
        
        fieldnames = ['username', 'password', 'role', 'email', 'department', 'status']
        add_row('data/users.csv', fieldnames, user_data)
        flash('User added successfully!', 'success')
        return redirect(url_for('manage_users'))
    except Exception as e:
        flash(f'Error adding user: {str(e)}', 'error')
        return redirect(url_for('manage_users'))

@app.route('/confirm_delete_user/<username>')
def confirm_delete_user(username):
    if 'user' not in session or safe_get(session['user'], 'role') != 'Admin':
        return redirect(url_for('login'))
    
    users = read_csv('data/users.csv')
    user_to_delete = None
    for u in users:
        if safe_get(u, 'username') == username:
            user_to_delete = u
            break
    
    if not user_to_delete:
        flash('User not found.', 'error')
        return redirect(url_for('manage_users'))
    
    return render_template('confirm_delete_user.html', user=user_to_delete)

@app.route('/delete_user/<username>', methods=['POST'])
def delete_user(username):
    if 'user' not in session or safe_get(session['user'], 'role') != 'Admin':
        return redirect(url_for('login'))
    
    confirm_delete = request.form.get('confirm_delete')
    if not confirm_delete:
        flash('Please confirm deletion by checking the checkbox.', 'error')
        return redirect(url_for('confirm_delete_user', username=username))
    
    users = read_csv('data/users.csv')
    users = [u for u in users if safe_get(u, 'username') != username]
    
    fieldnames = ['username', 'password', 'role', 'email', 'department', 'status']
    write_csv('data/users.csv', fieldnames, users)
    flash('User deleted successfully!', 'success')
    return redirect(url_for('manage_users'))

@app.route('/request_license', methods=['GET', 'POST'])
def request_license():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'GET':
        return render_template('request_license.html')
    
    # POST method
    try:
        # Validate required fields
        if not request.form.get('software') or not request.form.get('reason') or not request.form.get('device'):
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('request_license'))
        
        username = safe_get(session['user'], 'username', '')
        if not username:
            flash('User session invalid. Please login again.', 'error')
            return redirect(url_for('login'))
        
        request_data = {
            'request_id': f"R{len(read_csv('data/requests.csv')) + 1:03d}",
            'username': username,
            'software_name': request.form['software'],
            'reason': request.form['reason'],
            'date': datetime.now().strftime('%Y-%m-%d'),
            'status': 'Pending',
            'device': request.form.get('device', 'Not specified')
        }
        
        fieldnames = ['request_id', 'username', 'software_name', 'reason', 'date', 'status', 'device']
        add_row('data/requests.csv', fieldnames, request_data)
        flash('License request submitted successfully!', 'success')
        return redirect(url_for('requests'))
    except Exception as e:
        flash(f'Error submitting request: {str(e)}', 'error')
        return redirect(url_for('request_license'))

@app.route('/search_license_by_category', methods=['GET'])
def search_license_by_category():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    licenses = read_csv('data/licenses.csv')
    
    # Get unique categories
    categories = sorted(list(set([safe_get(lic, 'category', '') for lic in licenses if safe_get(lic, 'category')])))
    
    selected_category = request.args.get('category', '')
    filtered_licenses = []
    
    if selected_category:
        filtered_licenses = [lic for lic in licenses if safe_get(lic, 'category') == selected_category]
    
    return render_template('search_license_by_category.html', 
                         categories=categories,
                         selected_category=selected_category,
                         licenses=filtered_licenses)

@app.route('/search_devices_by_license', methods=['GET'])
def search_devices_by_license():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    licenses = read_csv('data/licenses.csv')
    
    # Get unique software names
    software_names = sorted(list(set([safe_get(lic, 'software_name', '') for lic in licenses if safe_get(lic, 'software_name')])))
    
    selected_software = request.args.get('software_name', '')
    filtered_devices = []
    
    if selected_software:
        filtered_devices = [lic for lic in licenses if safe_get(lic, 'software_name') == selected_software]
    
    return render_template('search_devices_by_license.html', 
                         software_names=software_names,
                         selected_software=selected_software,
                         devices=filtered_devices)

@app.route('/edit_license', methods=['GET', 'POST'])
def edit_license():
    if 'user' not in session or safe_get(session['user'], 'role') != 'Admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            license_id = request.form.get('license_id')
            if not license_id:
                flash('License ID is required.', 'error')
                return redirect(url_for('edit_license'))
            
            licenses = read_csv('data/licenses.csv')
            license_to_update = None
            for lic in licenses:
                if safe_get(lic, 'id') == license_id:
                    license_to_update = lic
                    break
            
            if not license_to_update:
                flash('License not found.', 'error')
                return redirect(url_for('edit_license'))
            
            # Update license data
            required_fields = ['name', 'category', 'key', 'department', 'start_date', 'expiry_date']
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'Please fill in the {field} field.', 'error')
                    return redirect(url_for('edit_license', license_id=license_id))
            
            # Validate date format
            try:
                start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
                expiry_date = datetime.strptime(request.form['expiry_date'], '%Y-%m-%d')
                if expiry_date <= start_date:
                    flash('Expiry date must be after start date.', 'error')
                    return redirect(url_for('edit_license', license_id=license_id))
            except ValueError:
                flash('Please enter dates in YYYY-MM-DD format.', 'error')
                return redirect(url_for('edit_license', license_id=license_id))
            
            # Update the license
            license_to_update['software_name'] = request.form['name']
            license_to_update['category'] = request.form['category']
            license_to_update['license_key'] = request.form['key']
            license_to_update['assigned_department'] = request.form['department']
            license_to_update['assigned_device'] = request.form.get('assigned_device', 'Not assigned')
            license_to_update['start_date'] = request.form['start_date']
            license_to_update['expiry_date'] = request.form['expiry_date']
            
            fieldnames = ['id', 'software_name', 'category', 'license_key', 'assigned_department', 'assigned_device', 'start_date', 'expiry_date', 'status']
            write_csv('data/licenses.csv', fieldnames, licenses)
            flash('License updated successfully!', 'success')
            return redirect(url_for('edit_license', license_id=license_id))
        except Exception as e:
            flash(f'Error updating license: {str(e)}', 'error')
            return redirect(url_for('edit_license'))
    
    # GET method
    license_id = request.args.get('license_id', '')
    license = None
    error = None
    
    if license_id:
        licenses = read_csv('data/licenses.csv')
        for lic in licenses:
            if safe_get(lic, 'id') == license_id:
                license = lic
                break
        if not license:
            error = f'License ID "{license_id}" not found.'
    
    return render_template('edit_license.html', license=license, license_id=license_id, error=error)

@app.route('/delete_license', methods=['GET', 'POST'])
def delete_license():
    if 'user' not in session or safe_get(session['user'], 'role') != 'Admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            license_id = request.form.get('license_id')
            confirm_delete = request.form.get('confirm_delete')
            
            if not license_id:
                flash('License ID is required.', 'error')
                return redirect(url_for('delete_license'))
            
            if not confirm_delete:
                flash('Please confirm deletion by checking the checkbox.', 'error')
                return redirect(url_for('delete_license', license_id=license_id))
            
            licenses = read_csv('data/licenses.csv')
            license_to_delete = None
            for lic in licenses:
                if safe_get(lic, 'id') == license_id:
                    license_to_delete = lic
                    break
            
            if not license_to_delete:
                flash('License not found.', 'error')
                return redirect(url_for('delete_license'))
            
            # Remove the license
            licenses = [lic for lic in licenses if safe_get(lic, 'id') != license_id]
            fieldnames = ['id', 'software_name', 'category', 'license_key', 'assigned_department', 'assigned_device', 'start_date', 'expiry_date', 'status']
            write_csv('data/licenses.csv', fieldnames, licenses)
            flash('License deleted successfully!', 'success')
            return redirect(url_for('delete_license'))
        except Exception as e:
            flash(f'Error deleting license: {str(e)}', 'error')
            return redirect(url_for('delete_license'))
    
    # GET method
    license_id = request.args.get('license_id', '')
    license = None
    error = None
    
    if license_id:
        licenses = read_csv('data/licenses.csv')
        for lic in licenses:
            if safe_get(lic, 'id') == license_id:
                license = lic
                break
        if not license:
            error = f'License ID "{license_id}" not found.'
    
    return render_template('delete_license.html', license=license, license_id=license_id, error=error)

@app.route('/admin_view_licenses')
def admin_view_licenses():
    if 'user' not in session or safe_get(session['user'], 'role') != 'Admin':
        return redirect(url_for('login'))
    
    licenses = read_csv('data/licenses.csv')
    
    # Get unique values for filters
    categories = sorted(list(set([safe_get(lic, 'category', '') for lic in licenses if safe_get(lic, 'category')])))
    software_names = sorted(list(set([safe_get(lic, 'software_name', '') for lic in licenses if safe_get(lic, 'software_name')])))
    departments = sorted(list(set([safe_get(lic, 'assigned_department', '') for lic in licenses if safe_get(lic, 'assigned_department')])))
    
    # Get filter parameters
    search_id_param = request.args.get('license_id', '').strip()
    selected_category = request.args.get('category', '')
    selected_software = request.args.get('software_name', '')
    selected_department = request.args.get('department', '')
    
    # Determine if license_id is for search or for viewing details
    # If it's clicked from the table, show details but keep the list
    # If it's from search box, filter the list
    view_details = request.args.get('view_details', '')
    selected_license_id = search_id_param if view_details else None
    search_id = search_id_param if not view_details else ''
    
    # Filter licenses
    filtered_licenses = licenses
    
    # Only filter by search_id if it's not being used for detail view
    if search_id and not selected_license_id:
        filtered_licenses = [lic for lic in filtered_licenses if safe_get(lic, 'id', '').upper() == search_id.upper()]
    
    if selected_category:
        filtered_licenses = [lic for lic in filtered_licenses if safe_get(lic, 'category') == selected_category]
    
    if selected_software:
        filtered_licenses = [lic for lic in filtered_licenses if safe_get(lic, 'software_name') == selected_software]
    
    if selected_department:
        filtered_licenses = [lic for lic in filtered_licenses if safe_get(lic, 'assigned_department') == selected_department]
    
    # Get selected license for detail view
    selected_license = None
    if selected_license_id:
        for lic in licenses:
            if safe_get(lic, 'id') == selected_license_id:
                selected_license = lic
                break
    
    return render_template('admin_view_licenses.html',
                         licenses=filtered_licenses,
                         categories=categories,
                         software_names=software_names,
                         departments=departments,
                         search_id=search_id,
                         selected_category=selected_category,
                         selected_software=selected_software,
                         selected_department=selected_department,
                         selected_license_id=selected_license_id if selected_license_id else '',
                         selected_license=selected_license)

@app.route('/admin_active_licenses')
def admin_active_licenses():
    if 'user' not in session or safe_get(session['user'], 'role') != 'Admin':
        return redirect(url_for('login'))
    
    active, _, _ = categorize_licenses()
    
    # Filter by license ID if provided
    search_id = request.args.get('license_id', '').strip()
    if search_id:
        active = [lic for lic in active if safe_get(lic, 'id', '').upper() == search_id.upper()]
    
    return render_template('admin_active_licenses.html',
                         licenses=active,
                         search_id=search_id)

@app.route('/admin_expiring_licenses')
def admin_expiring_licenses():
    if 'user' not in session or safe_get(session['user'], 'role') != 'Admin':
        return redirect(url_for('login'))
    
    _, expiring, _ = categorize_licenses()
    
    # Filter by license ID if provided
    search_id = request.args.get('license_id', '').strip()
    if search_id:
        expiring = [lic for lic in expiring if safe_get(lic, 'id', '').upper() == search_id.upper()]
    
    return render_template('admin_expiring_licenses.html',
                         licenses=expiring,
                         search_id=search_id)

@app.route('/admin_expired_licenses')
def admin_expired_licenses():
    if 'user' not in session or safe_get(session['user'], 'role') != 'Admin':
        return redirect(url_for('login'))
    
    _, _, expired = categorize_licenses()
    
    # Filter by license ID if provided
    search_id = request.args.get('license_id', '').strip()
    if search_id:
        expired = [lic for lic in expired if safe_get(lic, 'id', '').upper() == search_id.upper()]
    
    return render_template('admin_expired_licenses.html',
                         licenses=expired,
                         search_id=search_id)

@app.route('/help')
def help():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    return render_template('help.html')

@app.route('/backup_data')
def backup_data():
    if 'user' not in session or safe_get(session['user'], 'role') != 'Admin':
        return redirect(url_for('login'))
    
    try:
        backup_dir = backup_csv_files()
        flash(f'Backup created successfully in {backup_dir}', 'success')
    except Exception as e:
        flash(f'Error creating backup: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/contact_support', methods=['POST'])
def contact_support():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    contact_data = {
        'request_id': f"C{len(read_csv('data/requests.csv')) + 1:03d}",
        'username': safe_get(session['user'], 'username', ''),
        'software_name': f"Support Request: {request.form['subject']}",
        'reason': request.form['message'],
        'date': datetime.now().strftime('%Y-%m-%d'),
        'status': 'Pending',
        'device': 'Support Request'
    }
    
    fieldnames = ['request_id', 'username', 'software_name', 'reason', 'date', 'status', 'device']
    add_row('data/requests.csv', fieldnames, contact_data)
    flash('Support request submitted successfully!', 'success')
    return redirect(url_for('help'))

def startup_validation():
    """Validate CSV files on startup"""
    print("Starting Flask application...")
    print("Validating CSV files...")
    
    # Check if CSV files exist and are readable
    csv_files = {
        'data/licenses.csv': ['id', 'software_name', 'category', 'license_key', 'assigned_department', 'assigned_device', 'start_date', 'expiry_date', 'status'],
        'data/requests.csv': ['request_id', 'username', 'software_name', 'reason', 'date', 'status', 'device'],
        'data/users.csv': ['username', 'password', 'role', 'email', 'department', 'status']
    }
    
    for file_path, required_fields in csv_files.items():
        try:
            data = read_csv(file_path)
            validate_csv_data(data, required_fields, file_path)
            print(f"✓ {file_path} validated successfully")
        except Exception as e:
            print(f"✗ Error validating {file_path}: {e}")
    
    print("Startup validation complete!")

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('backups', exist_ok=True)
    
    # Run startup validation
    startup_validation()
    
    # Create initial backup
    try:
        backup_csv_files()
    except Exception as e:
        print(f"Warning: Could not create initial backup: {e}")
    
    print("Starting Flask server...")
    app.run(debug=True)
