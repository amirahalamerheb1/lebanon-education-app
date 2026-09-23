# Where education diverges in Lebanon

Interactive Streamlit page on education attainment across Lebanese towns (Impact Open Data, via AUB CODEC).
Pick a governorate, then drill into its districts to compare education profiles and town-level
illiteracy against tertiary education.

**Live app:** https://YOUR-APP-NAME.streamlit.app

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Files
- `app.py` - the Streamlit page (linked governorate dropdown and district multiselect, two Plotly charts)
- `data_prep.py` - loading and cleaning (drops incomplete rows and rows whose levels do not sum to about 100%, repairs district names)
- `lebanon_education.csv` - source data
- `requirements.txt` - dependencies for Streamlit Community Cloud
