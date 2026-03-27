# Archr Companies Portal

A full-stack web application for managing company product data, built with Django REST API backend and Angular frontend.

## 🏗️ Project Structure

```
archr-companies/
├── back_end/                    # Django REST API backend
│   ├── company_portal/          # Django project settings
│   │   ├── settings.py          # Main configuration
│   │   ├── azure_settings.py    # Azure deployment config
│   │   ├── gcp_settings.py      # GCP deployment config
│   │   └── urls.py              # URL routing
│   ├── main/                    # Main Django app
│   │   ├── models/              # Database models
│   │   │   ├── users.py         # User, Company, Role models
│   │   │   ├── products.py      # Product-related models
│   │   │   ├── questionnaires.py # Survey/questionnaire models
│   │   │   ├── aspects.py       # Scoring aspects
│   │   │   └── scoring.py       # Scoring logic
│   │   ├── serializers/         # API serializers
│   │   ├── views/               # API views
│   │   └── migrations/          # Database migrations
│   ├── requirements.txt         # Python dependencies
│   └── manage.py               # Django management script
└── front_end/
    └── company-portal/          # Angular frontend
        ├── src/
        │   ├── app/
        │   │   ├── home/                # Product browsing/management
        │   │   ├── login/               # User authentication
        │   │   ├── signup/              # User registration
        │   │   ├── password-reset/      # Password reset functionality
        │   │   ├── create-product/      # Product creation
        │   │   ├── edit-product/        # Product editing
        │   │   ├── uploaded-products/   # Uploaded products management
        │   │   ├── side-menu/           # Navigation menu
        │   │   ├── product-components/  # Reusable product components
        │   │   ├── services/            # API & business logic services
        │   │   │   ├── api.service.ts          # Main API communication
        │   │   │   ├── user.service.ts         # User management
        │   │   │   ├── filter.service.ts       # Product filtering logic
        │   │   │   ├── authguard.service.ts    # Route protection
        │   │   │   ├── productCsvService.ts    # CSV handling
        │   │   │   └── error-handling/         # Global error handling
        │   │   ├── models/              # TypeScript interfaces & types
        │   │   │   ├── product-entities.model.ts  # Product data models
        │   │   │   ├── user.ts                    # User & auth models
        │   │   │   ├── questionnaire.model.ts     # Survey models
        │   │   │   ├── filter.model.ts            # Filter models
        │   │   │   ├── aspect.ts                  # Scoring aspects
        │   │   │   └── company.ts                 # Company models
        │   │   ├── app.component.ts     # Root component
        │   │   └── app.config.ts        # App configuration
        │   ├── environments/            # Environment configurations
        │   │   ├── environment.ts       # Development config
        │   │   └── environment.prod.ts  # Production config
        │   ├── styles/                  # Global styles & Tailwind CSS
        │   ├── main.ts                  # Application bootstrap
        │   └── index.html               # HTML entry point
        ├── package.json                 # Node.js dependencies
        ├── angular.json                 # Angular CLI configuration
        ├── tailwind.config.js           # Tailwind CSS configuration
        └── proxyconfig.json             # Development proxy settings
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.12+** with pip
- **Node.js 18+** with npm
- **MySQL 8.0+** or MySQL Workbench
- **Git**

### 1. Clone the Repository

```bash
git clone https://github.com/Hjalmar-Ohman/archr-companies.git
cd archr-companies
```

### 2. Database Setup

1. **Install MySQL**
   - Download and install [MySQL Workbench](https://dev.mysql.com/downloads/workbench/)

2. **Create Database**
   ```sql
   CREATE DATABASE company_portal_db;
   CREATE USER 'root'@'localhost' IDENTIFIED BY 'your_password';
   GRANT ALL PRIVILEGES ON company_portal_db.* TO 'root'@'localhost';
   FLUSH PRIVILEGES;
   ```

3. **Environment Configuration**
   - Create a `.env` file in the `back_end/` directory:
   ```env
   MYSQL_PASSWORD=your_mysql_password
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ```

### 3. Backend Setup (Django)

```bash
# Navigate to backend directory
cd back_end

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Populate with sample data
python manage.py populate_data

# Start development server
python manage.py runserver
```

The API will be available at `http://localhost:8000/`

### 4. Frontend Setup (Angular)

```bash
# Navigate to frontend directory
cd front_end/company-portal

# Install dependencies
npm install

# Start development server with proxy configuration
npm run start:dev
```

The application will be available at `http://localhost:4200/`

## 🔧 Development Workflow

### Backend Development

- **Models**: Define data structure in `back_end/main/models/`
- **API Endpoints**: Create views in `back_end/main/views/`
- **Serializers**: Handle JSON serialization in `back_end/main/serializers/`
- **URLs**: Configure routing in `back_end/main/urls.py`

### Frontend Development

- **Components**: Angular components in `front_end/company-portal/src/app/`
- **Services**: API communication in `front_end/company-portal/src/app/services/`
- **Models**: TypeScript interfaces in `front_end/company-portal/src/app/models/`
- **Routing**: Configure in `front_end/company-portal/src/main.ts`

### Key API Endpoints

- `POST /api/auth/login/` - User authentication
- `GET /api/models/products/` - List products
- `POST /api/models/products/search/` - Search products with filters
- `GET /api/models/myproducts/` - Get company's products
- `POST /api/models/myproducts/` - Add products to company
- `GET /api/models/all-filters/` - Get available filters

## 🛠️ Available Scripts

### Backend
```bash
python manage.py runserver          # Start development server
python manage.py migrate            # Apply database migrations
python manage.py makemigrations     # Create new migrations
python manage.py createsuperuser    # Create admin user
python manage.py populate_data      # Load sample data
```

### Frontend
```bash
npm run start:dev    # Development server with API proxy
```