# Imperial Diet Taiwan Text Visualization (1894–1945)

An interactive Streamlit dashboard that visualizes Taiwan-related discussions in the Proceedings of the Imperial Diet of Japan (1894–1945), combining natural language processing, word frequency analysis, and historical context, assisted by ChatGPT.

## Project Overview

This project explores historical parliamentary records using NLP techniques to analyze how Taiwan-related discourse evolved between 1894 and 1945.

The dashboard allows users to explore:
Word frequency changes over time
Interactive word clouds by year
Historical political timeline context
Government leadership changes
Geographic visualization of Taiwan region context

## Features

### Word Cloud Analysis
Tokenization using `SudachiPy`
Extracts noun-based keywords
Dynamic word cloud by selected year

### Interactive Controls
Year slider (1894–1945)
Top-N noun selector
Adjustable word cloud width/height

### Historical Context Panel (by Year)
Displays contextual information for each selected year (if applicable):
Major historical events
Governor-General of Taiwan/Vice Governor-General/Chief Administrator

### Document Visualizations
Document distribution by year
Document distribution by decade

### Geographic Map
Built with `Folium`
Visualizes regional context of Taiwan area


## Methodology

### Text Processing Pipeline
Tokenization: `sudachipy`
Script normalization: Katakana to Hiragana conversion
Noun extraction only (focus on meaningful semantic units)
Custom noun filtering (can be extended in future)

### Visualization Stack
`streamlit`: dashboard UI
`matplotlib`: word cloud rendering
`folium`: map visualization
`streamlit-folium`: map embedding (to be added in future)

## Installation
```bash
pip install -r requirements.txt

## Data Source
This project uses historical parliamentary records from the **Imperial Diet Proceedings Database** provided by the National Diet Library of Japan.

Main database:  
https://teikokugikai-i.ndl.go.jp/#/

Description:  
This system provides full-text searchable records of the Imperial Diet of Japan (1890–1947), including speeches, committees, and proceedings. It allows keyword search, filtering by date, and access to original historical documents.

API documentation (optional technical reference):  
https://teikokugikai-i.ndl.go.jp/teikoku_api.html

### Citation
National Diet Library (NDL), *Imperial Diet Proceedings Search System*,  
https://teikokugikai-i.ndl.go.jp/#/ (accessed 2026-05-28)