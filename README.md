# AI Data Analysis Agent

A beginner-friendly interactive data analysis app built with Python and Streamlit. Upload a CSV file to inspect data quality, explore columns, clean data, create charts, view summary metrics, and ask questions about the dataset. An optional OpenAI-powered assistant can explain patterns from calculated dataset summaries.

## Features

- Upload and preview CSV datasets
- Inspect data types, missing values, and duplicate rows
- Create a cleaned copy by removing duplicate rows and filling missing numeric values with medians and text values with `Unknown`
- Download the cleaned dataset as a CSV
- Explore value counts for a selected column
- Generate interactive charts when the relevant columns exist:
  - Revenue by product
  - Profit by region
  - Monthly revenue trend
- Display business summary metrics when matching columns exist
- Ask common questions using calculated answers
- Optionally ask an OpenAI model to explain dataset summaries

## Built with

- Python
- Streamlit
- Pandas
- Plotly Express
- OpenAI Python SDK (optional AI feature)

## Run locally on Windows

### 1. Download or clone this repository

Open PowerShell in the project folder.

### 2. Install dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell does not allow activation, use the Python executable inside `.venv` directly or follow your local Python installation instructions.

### 3. Start the app

```powershell
python -m streamlit run app.py
```

Streamlit will print a local URL, usually `http://localhost:8501`, which you can open in your browser.

### 4. Try the included sample dataset

Upload `data/retail_sales_analysis_dataset.csv` in the app. You can also upload another CSV file. Some charts and questions only appear or work when the uploaded dataset has the relevant column names.

## Enable the AI-powered assistant (optional)

The standard calculated-answer mode does not require an OpenAI API key. The AI-powered mode does.

In PowerShell, set your key for the current session without writing it into the source code:

```powershell
$env:OPENAI_API_KEY = Read-Host "Paste your OpenAI API key"
python -m streamlit run app.py
```

Keep the key private. Do not commit it, include it in screenshots, or paste it into `app.py`. The key is session-specific when set this way; set it again in a new PowerShell window.

For a local Streamlit secrets setup, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`, replace the example value with your own key, and keep `secrets.toml` out of Git. The app checks the environment variable first and then Streamlit secrets.

OpenAI API usage may incur charges and requires an account/API project with access to the configured model. Do not upload sensitive or confidential datasets to an external AI service unless you have permission to do so.

## Data cleaning notes

Cleaning creates a separate copy; the uploaded data is not overwritten. Duplicate rows are removed. Missing numeric values are filled with each numeric column's median, while missing text/category values are filled with `Unknown`. Consider whether these choices make sense for your own dataset before using the results for decisions.

## Limitations

- This is a portfolio project and a work in progress, not a replacement for a full data governance or business intelligence platform.
- Built-in chart and question logic recognises specific column names such as `Product`, `Region`, `Revenue_GBP`, `Profit_GBP`, `Sales_Channel`, and `Order_ID`.
- The AI assistant receives dataset-level summaries and selected group totals rather than every raw row. Its explanations may still be incorrect, so verify important results against the data.
- Large CSV files may take time or use substantial memory depending on your computer.

## Project structure

```text
ai-data-analysis-agent/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   └── secrets.toml.example
└── data/
    └── retail_sales_analysis_dataset.csv
```

## Future improvements

- Support more flexible column names and data types
- Add automated tests
- Improve error handling for very large or malformed CSV files
- Add a deployed demo with securely configured secrets
- Add more chart types and user-selected chart fields

## Author

Created as a hands-on portfolio project to practise Python, data analysis, interactive visualisation, and AI integration.
