# Software License Management System (SLMS)

A complete web application for managing software licenses built with Flask, HTML, and CSS. This system provides both admin and user interfaces for license management, request handling, and user administration.

## 🚀 Features

### Admin Features
- **Dashboard Overview**: Summary cards showing total, active, expiring, and expired licenses
- **License Management**: Add, view, and manage software licenses
- **User Management**: Add and delete system users
- **Request Management**: Approve or reject license requests
- **License Allocation**: View license distribution across categories

### User Features
- **User Dashboard**: Personal license overview and statistics
- **License Requests**: Submit new license requests
- **View Licenses**: Browse available licenses
- **Help & Support**: FAQ and contact support system

## 📁 Project Structure

```
/license_management_system
├── app.py                 # Main Flask application
├── /templates             # HTML templates
│   ├── base.html         # Base template with sidebar
│   ├── login.html        # Login page
│   ├── admin_dashboard.html
│   ├── user_dashboard.html
│   ├── add_license.html
│   ├── view_licenses.html
│   ├── requests.html
│   ├── manage_users.html
│   └── help.html
├── /static/css
│   └── style.css         # Comprehensive CSS styles
├── /data                 # CSV data files
│   ├── users.csv         # User accounts
│   ├── licenses.csv      # License information
│   └── requests.csv      # License requests
└── README.md
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Installation Steps

1. **Clone or download the project**
   ```bash
   # If you have the project files, navigate to the directory
   cd license_management_system
   ```

2. **Install Flask**
   ```bash
   pip install flask
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Access the application**
   - Open your web browser
   - Navigate to `http://127.0.0.1:5000`
   - You'll be redirected to the login page

## 🔐 Demo Credentials

### Admin Account
- **Username**: `admin`
- **Password**: `admin123`
- **Role**: `Admin`

### User Account
- **Username**: `user`
- **Password**: `user123`
- **Role**: `User`

### Additional Test Users
- `john.doe` / `password123`
- `jane.smith` / `password123`
- `mike.johnson` / `password123`
- `sarah.williams` / `password123`
- `tom.brown` / `password123`
- `emily.davis` / `password123`

## 🎨 Design Features

- **Modern UI**: Clean, professional interface with pastel color palette
- **Responsive Design**: Works on desktop and tablet devices
- **Dashboard Cards**: Visual summary statistics
- **Data Tables**: Organized display of licenses and users
- **Status Indicators**: Color-coded status badges
- **Navigation**: Intuitive sidebar navigation

## 📊 Data Management

The application uses CSV files for data storage:

- **users.csv**: Stores user accounts with username, password, and role
- **licenses.csv**: Contains license information including name, category, expiry dates
- **requests.csv**: Tracks license requests with status and dates

## 🔧 Technical Details

### Technologies Used
- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3
- **Data Storage**: CSV files
- **Styling**: Custom CSS with Poppins font
- **No JavaScript**: Pure HTML/CSS implementation

### Key Features
- Session-based authentication
- Role-based access control (Admin/User)
- CSV data manipulation
- Responsive design
- Form validation
- Flash messaging system

## 🚀 Usage Guide

### For Administrators
1. **Login** with admin credentials
2. **Dashboard**: View system overview and statistics
3. **Add License**: Create new software licenses
4. **Manage Users**: Add or remove system users
5. **Review Requests**: Approve or reject license requests
6. **View Licenses**: Monitor all licenses and their status

### For Users
1. **Login** with user credentials
2. **Dashboard**: View personal license statistics
3. **Request License**: Submit new license requests
4. **View Requests**: Check status of submitted requests
5. **Help & Support**: Access FAQ and contact support

## 🎯 Key Routes

- `/` or `/login` - Login page
- `/admin_dashboard` - Admin overview
- `/user_dashboard` - User overview
- `/add_license` - Add new license (Admin only)
- `/view_licenses` - View all licenses
- `/requests` - Manage license requests
- `/manage_users` - User management (Admin only)
- `/help` - Help and support

## 🔒 Security Features

- Session-based authentication
- Role-based access control
- Password protection
- Secure logout functionality

## 📱 Responsive Design

The application is designed to work on:
- Desktop computers (primary)
- Tablets (responsive)
- Mobile devices (basic support)

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**
   - Change the port in `app.py`: `app.run(debug=True, port=5001)`

2. **CSV file not found**
   - Ensure the `data` folder exists with the CSV files

3. **Login not working**
   - Check that `users.csv` exists and has the correct format

4. **Styling issues**
   - Verify that `static/css/style.css` exists and is accessible

## 📝 License

This project is created for educational and demonstration purposes.

## 🤝 Contributing

This is a demonstration project. Feel free to use it as a starting point for your own license management system.

## 📞 Support

For questions or issues, please refer to the Help & Support section within the application or check the FAQ.

---

**Note**: This application is designed for demonstration purposes and uses CSV files for data storage. For production use, consider implementing a proper database system and additional security measures.
