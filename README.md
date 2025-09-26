# Canadian Government Grants Tracker

A Django-based web application that provides transparency into Canadian government grants and contributions, helping citizens understand how their tax dollars are being spent.

## Features

### 🏛️ Grant Database
- **Complete Grant Listings**: Browse all government grants from 2018-2024
- **Advanced Search & Filtering**: Search by recipient, program, province, value, and fiscal year
- **Detailed Grant Information**: Full details including recipient, program purpose, timeline, and outcomes

### 💰 Major Funding Tracker
- **High-Value Grants**: Automatically flags grants over $1 million
- **Investment Analysis**: Statistics on major government investments
- **Sector Breakdown**: See which industries receive the most funding

### 🚩 Notable Grants Section
- **Controversial Projects**: Highlights grants that have drawn public criticism
- **International Development**: Special focus on overseas spending like the "Greening Our Rice" project in Vietnam
- **Public Interest**: Projects involving gender equity, climate initiatives, and cultural funding

### 🧮 Tax Contribution Calculator
**The most innovative feature** - Calculate your personal contribution to each grant:

1. **Input Your Finances**:
   - Annual income (before tax)
   - GST-eligible spending (goods/services with tax)

2. **Automatic Calculation**:
   - Federal income tax using 2024 brackets
   - GST paid (5% on eligible purchases)
   - Total tax contribution

3. **Personal Grant Shares**:
   - Your exact dollar contribution to each grant
   - Percentage of your income going to specific projects
   - Share of controversial grants like international development

**Example**: If you earn $75,000 and pay $15,000 in federal taxes, you contributed approximately $0.75 to a $20M grant (your tax share × grant amount ÷ total federal revenue).

### 📊 Statistics Dashboard
**Comprehensive analytics and insights**:

- **Overview Metrics**: Total grants, funding amounts, averages, and key performance indicators
- **Yearly Trends**: Multi-year analysis showing funding patterns and growth over time
- **Geographic Analysis**: Provincial and territorial distribution of grants and recipients
- **Sector Breakdown**: Industry analysis showing which sectors receive the most funding
- **Program Analysis**: Most funded government programs and their effectiveness
- **Value Distribution**: Analysis of grant sizes from small to mega-grants
- **Recipient Analysis**: Top recipient organizations and funding patterns
- **Notable Categories**: Breakdown of controversial grants by type (international, climate, etc.)
- **Interactive Charts**: Visual representations using Chart.js for easy interpretation

### 🚀 API Documentation
**Complete REST API access**:

1. **Grant Search API** (`/api/search/`):
   - Full-text search across titles, recipients, descriptions
   - Advanced filtering by province, year, value ranges, recipient type
   - Sorting and pagination support
   - Returns up to 1000 results per query

2. **Statistics API** (`/api/stats/`):
   - Basic grant statistics and aggregations
   - Provincial and yearly breakdowns
   - Top programs by funding

3. **Recipients API** (`/api/recipients/`):
   - Top recipients analysis
   - Breakdown by organization type
   - Provincial recipient distribution

4. **Comprehensive Stats API** (`/api/comprehensive-stats/`):
   - Detailed analytics and insights
   - Value distributions and trends
   - Notable grant category analysis

5. **Tax Calculator API** (`/api/calculate/`):
   - Personal tax contribution calculations
   - Grant share estimations
   - Yearly breakdown of contributions

All APIs return JSON data with no authentication required for public access.

## Technical Implementation

### Backend (Django)
- **Models**: Grant, TaxCalculation, TaxBracket, CanadianTaxData
- **Data Import**: Management command to process CSV files from government open data
- **API Endpoints**: RESTful APIs for calculations and statistics
- **Admin Interface**: Full admin panel for grant management

### Frontend
- **Responsive Design**: Bootstrap 5 with custom styling
- **Interactive Calculator**: Real-time tax calculations with AJAX
- **Search & Filtering**: Advanced filtering with pagination
- **Data Visualization**: Statistics and charts for grant analysis

### Data Processing
- **CSV Import**: Handles multiple years of government data (2018-2024)
- **Data Cleaning**: Parses currency values, dates, and handles encoding issues
- **Auto-Classification**: Automatically flags major funding and notable grants
- **Keyword Detection**: Identifies controversial projects based on content analysis

## Installation & Setup

1. **Clone and Setup**:
```bash
git clone <repository>
cd Canada_grants
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Database Setup**:
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

3. **Import Grant Data**:
```bash
python manage.py import_grants --csv-dir csv
```

4. **Run Development Server**:
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` to access the application.

## Data Sources

- **Government of Canada Open Data**: Official grants and contributions data
- **Tax Brackets**: 2024 federal income tax rates
- **Revenue Estimates**: Federal government revenue data for calculations

## Key URLs

### User Interface
- `/` - Homepage with statistics and recent grants
- `/grants/` - Complete grant listings with search/filter
- `/major-funding/` - Grants over $1 million
- `/notable/` - Controversial or notable grants
- `/statistics/` - Comprehensive statistics dashboard with interactive charts
- `/calculator/` - Tax contribution calculator
- `/api/` - API documentation with interactive examples
- `/admin/` - Django admin interface

### API Endpoints
- `/api/stats/` - Basic grant statistics and aggregations
- `/api/search/` - Advanced grant search with filtering and pagination
- `/api/recipients/` - Recipient analysis and top recipients
- `/api/comprehensive-stats/` - Detailed analytics and insights
- `/api/calculate/` - Personal tax contribution calculator (POST)

## Notable Features

### Tax Calculator Logic
The calculator uses this formula to determine your personal contribution:
```
Your Grant Share = (Your Total Federal Taxes ÷ Total Federal Revenue) × Grant Amount
```

This gives citizens a tangible understanding of their personal stake in government spending.

### Controversial Grant Detection
The system automatically flags grants containing keywords like:
- Gender, diversity, equity, inclusion
- Climate change, carbon initiatives
- International development projects
- Arts and cultural funding
- Indigenous reconciliation programs

### Real-World Impact
Citizens can see exactly how much they personally contributed to projects like:
- $20M "Greening Our Rice" project in Vietnam
- Large corporate subsidies
- International aid programs
- Cultural and arts initiatives

## Future Enhancements

- **Provincial Tax Integration**: Include provincial taxes in calculations
- **Public Comments**: Allow citizen feedback on grants
- **Geographic Mapping**: Interactive maps showing grant distribution
- **Mobile App**: Native mobile application
- **Real-time Data Updates**: Automated data refresh from government sources
- **Grant Outcome Tracking**: Follow-up on grant results and effectiveness
- **Comparison Tools**: Compare grants across years, provinces, or programs
- **Export Features**: PDF reports and CSV exports for analysis
- **Advanced Analytics**: Machine learning insights and predictions

## Contributing

This project aims to increase government transparency and citizen engagement. Contributions welcome for:
- Additional data sources
- Enhanced visualizations
- Mobile responsiveness improvements
- Performance optimizations
- Documentation updates

## License

Open source project for government transparency and public accountability.