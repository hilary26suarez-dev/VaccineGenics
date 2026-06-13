# VaccineGenics Setup Script (Windows PowerShell)
# Run this once to set up the project environment

Write-Host "=== VaccineGenics Setup ===" -ForegroundColor Cyan

# Install Python dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install python-dotenv numpy scipy pandas plotly streamlit requests tqdm openai seaborn matplotlib scikit-learn

# Optional: Azure AI packages (needed for Azure Foundry agent mode)
Write-Host ""
Write-Host "Install Azure AI packages? (needed for Azure Foundry agent mode)" -ForegroundColor Yellow
$install_azure = Read-Host "Install azure-ai-agents, azure-identity? [y/N]"
if ($install_azure -eq "y" -or $install_azure -eq "Y") {
    pip install azure-ai-agents azure-identity azure-ai-projects
}

# Copy .env
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host ".env created from .env.example — fill in your Azure credentials" -ForegroundColor Green
}

# Pre-generate cohort
Write-Host ""
Write-Host "Pre-generating synthetic cohort..." -ForegroundColor Yellow
$env:PYTHONIOENCODING = "utf-8"
python -c "
import sys; sys.path.insert(0, '.')
from src.synthetic.patient_generator import get_or_generate_cohort
cohort = get_or_generate_cohort(1000)
print(f'Cohort ready: {len(cohort)} patients')
"

Write-Host ""
Write-Host "=== Setup complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "To run the pipeline:    python run_pipeline.py"
Write-Host "To run the UI:          streamlit run run_ui.py"
Write-Host "To fetch ClinVar data:  python run_pipeline.py --fetch-clinvar"
