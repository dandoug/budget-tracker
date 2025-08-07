# Budget Tracker & Reporting System

A comprehensive budget tracking and reporting system that compares your planned budget against actual spending data from Simplifi exports.

## Features

- 📊 **Budget vs Actual Analysis**: Compare planned spending with actual expenses
- 📈 **Interactive Visualizations**: Charts and graphs powered by Plotly
- 📱 **Web Interface**: User-friendly Streamlit web application
- 📄 **PDF Reports**: Generate comprehensive budget reports
- 🏷️ **Smart Category Matching**: Automatically match actual expenses to budget categories
- 📅 **Date Range Analysis**: Analyze spending patterns over custom time periods
- 📊 **Excel Export**: Export analysis data to Excel for further processing

## Project Structure


## Getting Started

### Prerequisites

- Python 3.12+
- Conda (for environment management)
- Docker (optional, for containerized deployment)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd budget-tracker
   ```

2. **Create conda environment**
   ```bash
   conda env create -f environment.yml
   conda activate budget-tracker
   ```

3. **Run the application**
   ```bash
   streamlit run app/web/streamlit_app.py
   ```

### Docker Deployment

1. **Build the container**
   ```bash
   docker build -t budget-tracker .
   ```

2. **Run the container**
   ```bash
   docker run -p 8501:8501 budget-tracker
   ```

## Usage

### Budget File Format

Create a YAML file with your budget structure:

```yaml
# Budget for 2025
income:
  - source: Salary
    amount: 5000
  - source: Side Business
    amount: 1000

expenses:
  - category: Housing
    amount: 1500
    subcategories:
      - category: Rent
        amount: 1400
      - category: Renter's Insurance
        amount: INHERITED  # Inherits from parent category
  - category: Food
    amount: 600
```

### Simplifi Export
Export your P&L data from Simplifi as CSV or XLSX format and upload it through the web interface.
### Web Interface
1. **Upload Files**: Use the sidebar to upload your budget YAML and Simplifi export
2. **Select Date Range**: Choose the analysis period
3. **View Analysis**: Explore the Overview, Charts, and Details tabs
4. **Generate Reports**: Export PDF reports or Excel files

## Configuration
### Environment Variables
- `STREAMLIT_SERVER_PORT`: Port for Streamlit server (default: 8501)
- `STREAMLIT_SERVER_ADDRESS`: Server address (default: 0.0.0.0)

### Chart Themes
Available themes:
- plotly_white (default)
- plotly_dark
- ggplot2
- seaborn

## Development
### Running Tests
```shell
pytest tests/
```
## AI Assistant
### Code Structure
- **Parser modules**: Handle loading and parsing of budget and actual spending data
- **Analysis modules**: Perform budget vs actual analysis and variance calculations
- **Output modules**: Generate charts, reports, and exports
- **Web module**: Streamlit web interface

### Adding New Features
1. Create appropriate module in the `app/` directory
2. Add corresponding tests in `tests/`
3. Update the Streamlit interface if needed
4. Update documentation

## Deployment Options
### Streamlit Cloud
1. Connect your GitHub repository to Streamlit Cloud
2. Configure the app path: `app/web/streamlit_app.py`
3. Set environment: `python = "3.12"`

### Docker
Use the included Dockerfile for containerized deployment to any platform that supports Docker containers.

### Self-hosted
Run directly with Streamlit on your own server:
``` bash
streamlit run app/web/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
