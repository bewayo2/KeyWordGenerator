"""
Custom CSS styles for Google Ads-like dashboard appearance.
"""

GOOGLE_ADS_STYLE = """
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    /* Header styling */
    h1 {
        color: #1a73e8;
        font-size: 2rem;
        font-weight: 400;
        margin-bottom: 0.5rem;
    }
    
    h2 {
        color: #202124;
        font-size: 1.5rem;
        font-weight: 400;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }
    
    h3 {
        color: #5f6368;
        font-size: 1.125rem;
        font-weight: 500;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    
    /* Card-like styling for sections */
    .stDataFrame {
        border: 1px solid #dadce0;
        border-radius: 8px;
        padding: 1rem;
        background-color: #ffffff;
    }
    
    /* Button styling */
    .stDownloadButton > button {
        background-color: #1a73e8;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.625rem 1.5rem;
        font-weight: 500;
        transition: background-color 0.2s;
    }
    
    .stDownloadButton > button:hover {
        background-color: #1557b0;
    }
    
    /* Primary button (highlighted) */
    div[data-testid="stDownloadButton"]:first-of-type > button {
        background-color: #1a73e8;
        font-size: 1rem;
        padding: 0.75rem 2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
    }
    
    /* Secondary button */
    div[data-testid="stDownloadButton"]:nth-of-type(2) > button {
        background-color: #ffffff;
        color: #1a73e8;
        border: 1px solid #dadce0;
    }
    
    div[data-testid="stDownloadButton"]:nth-of-type(2) > button:hover {
        background-color: #f8f9fa;
    }
    
    /* Info boxes styling */
    .stInfo {
        background-color: #e8f0fe;
        border-left: 4px solid #1a73e8;
        border-radius: 4px;
        padding: 1rem;
    }
    
    .stSuccess {
        background-color: #e6f4ea;
        border-left: 4px solid #34a853;
        border-radius: 4px;
        padding: 1rem;
    }
    
    .stWarning {
        background-color: #fef7e0;
        border-left: 4px solid #fbbc04;
        border-radius: 4px;
        padding: 1rem;
    }
    
    .stError {
        background-color: #fce8e6;
        border-left: 4px solid #ea4335;
        border-radius: 4px;
        padding: 1rem;
    }
    
    /* Text input styling */
    .stTextInput > div > div > input {
        border: 1px solid #dadce0;
        border-radius: 4px;
        padding: 0.5rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #1a73e8;
        box-shadow: 0 0 0 2px rgba(26, 115, 232, 0.2);
    }
    
    /* Text area styling */
    .stTextArea > div > div > textarea {
        border: 1px solid #dadce0;
        border-radius: 4px;
        padding: 0.75rem;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #1a73e8;
        box-shadow: 0 0 0 2px rgba(26, 115, 232, 0.2);
    }
    
    /* Number input styling */
    .stNumberInput > div > div > input {
        border: 1px solid #dadce0;
        border-radius: 4px;
    }
    
    /* Checkbox styling */
    .stCheckbox > label {
        color: #202124;
        font-weight: 400;
    }
    
    /* Divider styling */
    hr {
        border: none;
        border-top: 1px solid #dadce0;
        margin: 2rem 0;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        color: #5f6368;
        font-weight: 500;
    }
    
    /* Remove default Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom card styling for results */
    .results-card {
        background-color: #ffffff;
        border: 1px solid #dadce0;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    /* Metric boxes styling */
    .metric-box {
        background-color: #f8f9fa;
        border: 1px solid #dadce0;
        border-radius: 4px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
"""

