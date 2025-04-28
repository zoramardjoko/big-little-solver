# Big-Little Matcher

A tool for solving various types of Big-Little matching problems typically used in fraternity/sorority pairing.

# Try it out: https://big-little-solver.streamlit.app/

## Features

- Solves multiple variants of matching problems:
  - Classic Stable Matching (SMP)
  - Stable Matching with Ties (SMT)
  - Stable Matching with Ties and Incomplete Lists (SMTI)
  - Optimized Matching (with Preference Weights)
- Interactive web interface for data input and visualization
- Ability to use example data or input custom data
- Visualizes matches with a graph
- Checks for instabilities in the matching
- Allows downloading results as JSON

## Requirements

- Python 3.7+
- Required packages: streamlit, ortools, graphviz, ipython

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/kevinhehe/big-little-solver.git
   cd big-little-solver
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the Streamlit app:

```
streamlit run app.py
```

This will start a local web server and open the app in your default web browser.

### Using the App

1. Choose the type of matching problem you want to solve from the sidebar
2. Select whether to use example data or enter your own custom data
3. If using custom data, enter your data in JSON format in the text areas provided
4. For Optimized Matching, you can adjust the preference weight and other parameters
5. Click "Solve Matching Problem" to run the algorithm
6. View the results, including a visualization of the matches, statistics, and any instabilities
7. Optionally download the results as a JSON file

## Data Format

### Classic Stable Matching (SMP)
```python
bigs = {"Ishaan": {}, "Cindy": {}, "Thomas": {}}
littles = {"Swapneel": {}, "Zora": {}, "Kevin": {}}
big_prefs = {
    "Ishaan": ["Swapneel", "Zora", "Kevin"], 
    "Cindy": ["Kevin", "Swapneel", "Zora"], 
    "Thomas": ["Zora", "Kevin", "Swapneel"]
}
little_prefs = {
    "Swapneel": ["Thomas", "Ishaan", "Cindy"], 
    "Zora": ["Cindy", "Thomas", "Ishaan"], 
    "Kevin": ["Ishaan", "Cindy", "Thomas"]
}
```

### SMT and SMTI
```python
# Lower rank = higher preference, equal ranks = ties
big_prefs = {
    "Ishaan": {"Swapneel": 1, "Kevin": 2, "Zora": 1},  # Tie between Swapneel and Zora
    "Cindy": {"Swapneel": 3, "Kevin": 1, "Zora": 2},
    "Thomas": {"Swapneel": 1, "Kevin": 2, "Zora": 3}
}
```

### Optimized Matching
```python
# Can specify maximum number of matches
bigs = {"Ishaan": {"max": 1}, "Cindy": {"max": 2}, "Thomas": {"max": 1}}
littles = {"Swapneel": {"max": 1}, "Zora": {"max": 1}, "Kevin": {"max": 1}}
```

## Credits

Built by Kevin He and Zora Mardjoko 
