# 📊 Team 262 — Data Analytics & Insights

Data processing scripts, survey analysis, and metrics visualization for the Team 262 project.

## 💻 Tech Stack
* **Language:** Python 3.x
* **Key Libraries:** Pandas, NumPy, Matplotlib, Seaborn
* **Package Manager:** pip

## ⚙️ Environment Setup

1. Create and activate a virtual environment:
    ```bash
    # Linux / macOS / WSL
    python3 -m venv venv
    source venv/bin/activate

    # Windows (PowerShell)
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    ```

2. Install required dependencies:
    pip install -r requirements.txt

3. 🔐 Data Hygiene & Security
    Never commit raw survey exports or datasets containing personal data (*.csv, *.xlsx).

    Keep raw data in local directories ignored by Git (data/, datasets/).