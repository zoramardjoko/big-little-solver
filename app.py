import streamlit as st
from biglittlematcher import BigLittleMatcher
import graphviz
from collections import defaultdict
import json
import base64
from galeshapely import GaleShapley

st.set_page_config(page_title="Big-Little Matcher", layout="wide")

st.title("Big-Little Matcher")
st.markdown("""
This app helps you solve different variants of the Big-Little matching problem. Choose the type of matching problem and provide your data to find optimal matches.
""")

# Dictionary containing descriptions for each problem type
problem_descriptions = {
    "Gale-Shapley Algorithm": """
    The original algorithm for solving the stable matching problem. It guarantees a stable matching
    in O(n²) time, where n is the number of participants. This algorithm favors the proposing side.
    """,

    "Classic Stable Matching (SMP)": """
    The standard problem where each participant ranks all potential matches in strict order of preference. 
    The goal is to find a stable matching where no two participants would prefer each other over their assigned matches.
    """,
    
    "Stable Matching with Ties (SMT)": """
    Extends SMP by allowing ties in preference lists, where a participant may rank multiple others equally.
    This might be suitable for cases where people are indifferent between multiple matches.
    """,
    
    "Stable Matching with Ties and Incomplete Lists (SMTI)": """
    Further extends SMT by allowing participants to leave some preferences blank.
    It assumes that the missing preferences are the worst possible matches.
    """,
    
    "Optimized Matching (with Preference Weights)": """
    Instead of focusing solely on stability, this approach maximizes overall satisfaction based on preference rankings. 
    It allows for specifying how much weight to give to big preferences versus little preferences.
    """
}

# Sidebar for selecting the matching problem type
st.sidebar.header("Choose Matching Problem")
problem_type = st.sidebar.selectbox(
    "Select the type of matching problem:",
    list(problem_descriptions.keys())
)

# Initialize session state for storing matches and littles as proposers
if 'gs_matches' not in st.session_state:
    st.session_state.gs_matches = None
if 'show_littles_as_proposers' not in st.session_state:
    st.session_state.show_littles_as_proposers = False
if 'littles_proposer_clicked' not in st.session_state:
    st.session_state.littles_proposer_clicked = False
if 'big_prefs' not in st.session_state:
    st.session_state.big_prefs = None
if 'little_prefs' not in st.session_state:
    st.session_state.little_prefs = None

# Display the description for the selected problem type
st.sidebar.markdown("### About this matching problem")
st.sidebar.markdown(problem_descriptions[problem_type])

# Function to display graphviz objects
def render_graphviz(graph):
    dot_source = graph.source
    st.graphviz_chart(dot_source)

# Function to create example data based on problem type
def get_example_data(problem_type):
    if problem_type == "Classic Stable Matching (SMP)":
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
        return bigs, littles, big_prefs, little_prefs
        
    elif problem_type == "Stable Matching with Ties (SMT)":
        bigs = {"Ishaan": {}, "Cindy": {}, "Thomas": {}}
        littles = {"Swapneel": {}, "Zora": {}, "Kevin": {}}
        # In SMT, lower rank = higher preference, and equal ranks = ties
        big_prefs = {
            "Ishaan": {"Swapneel": 1, "Kevin": 2, "Zora": 1},  # Tie between Swapneel and Zora
            "Cindy": {"Swapneel": 3, "Kevin": 1, "Zora": 2},
            "Thomas": {"Swapneel": 1, "Kevin": 2, "Zora": 3}
        }
        little_prefs = {
            "Swapneel": {"Ishaan": 2, "Cindy": 3, "Thomas": 1},
            "Zora": {"Ishaan": 3, "Cindy": 1, "Thomas": 2},
            "Kevin": {"Ishaan": 1, "Cindy": 1, "Thomas": 2}  # Tie between Ishaan and Cindy
        }
        return bigs, littles, big_prefs, little_prefs
        
    elif problem_type == "Stable Matching with Ties and Incomplete Lists (SMTI)":
        bigs = {"Ishaan": {}, "Cindy": {}, "Thomas": {}}
        littles = {"Swapneel": {}, "Zora": {}, "Kevin": {}}
        # In SMTI, some preferences might be missing
        big_prefs = {
            "Ishaan": {"Swapneel": 1, "Zora": 1},  # Ishaan doesn't rank Kevin
            "Cindy": {"Swapneel": 3, "Kevin": 1, "Zora": 2},
            "Thomas": {"Swapneel": 1, "Kevin": 2}  # Thomas doesn't rank Zora
        }
        little_prefs = {
            "Swapneel": {"Ishaan": 2, "Thomas": 1},  # Swapneel doesn't rank Cindy
            "Zora": {"Ishaan": 3, "Cindy": 1, "Thomas": 2},
            "Kevin": {"Ishaan": 1, "Cindy": 1}  # Kevin doesn't rank Thomas
        }
        return bigs, littles, big_prefs, little_prefs
    
    elif problem_type == "Gale-Shapley Algorithm":
        # For Gale-Shapley, we only need preference lists, not bigs/littles dictionaries
        proposer_prefs = {
            "Ishaan": ["Swapneel", "Zora", "Kevin"], 
            "Cindy": ["Kevin", "Swapneel", "Zora"], 
            "Thomas": ["Zora", "Kevin", "Swapneel"]
        }
        receiver_prefs = {
            "Swapneel": ["Thomas", "Ishaan", "Cindy"], 
            "Zora": ["Cindy", "Thomas", "Ishaan"], 
            "Kevin": ["Ishaan", "Cindy", "Thomas"]
        }
        # Return empty dictionaries for bigs/littles to maintain interface
        empty_bigs = {"Ishaan": {}, "Cindy": {}, "Thomas": {}}
        empty_littles = {"Swapneel": {}, "Zora": {}, "Kevin": {}}
        return empty_bigs, empty_littles, proposer_prefs, receiver_prefs
    
    else:  # Optimized Matching
        bigs = {"Ishaan": {"max": 1}, "Cindy": {"max": 2}, "Thomas": {"max": 1}}
        littles = {"Swapneel": {"max": 1}, "Zora": {"max": 1}, "Kevin": {"max": 1}, "Morgan": {"max": 1}}
        big_prefs = {
            "Ishaan": ["Swapneel", "Zora", "Kevin", "Morgan"],
            "Cindy": ["Zora", "Swapneel", "Morgan", "Kevin"],
            "Thomas": ["Kevin", "Morgan", "Swapneel", "Zora"]
        }
        little_prefs = {
            "Swapneel": ["Ishaan", "Cindy", "Thomas"],
            "Zora": ["Cindy", "Ishaan", "Thomas"],
            "Kevin": ["Thomas", "Ishaan", "Cindy"],
            "Morgan": ["Thomas", "Cindy", "Ishaan"]
        }
        return bigs, littles, big_prefs, little_prefs

# Function to convert input data from UI to the appropriate format
def parse_input_data(problem_type, bigs_text, littles_text, big_prefs_text, little_prefs_text):
    try:
        bigs = json.loads(bigs_text)
        littles = json.loads(littles_text)
        
        if problem_type in ["Stable Matching with Ties (SMT)", "Stable Matching with Ties and Incomplete Lists (SMTI)"]:
            big_prefs = json.loads(big_prefs_text)
            little_prefs = json.loads(little_prefs_text)
        else:
            big_prefs = json.loads(big_prefs_text)
            little_prefs = json.loads(little_prefs_text)
            
        return bigs, littles, big_prefs, little_prefs
    except json.JSONDecodeError as e:
        st.error(f"Error parsing JSON input: {str(e)}")
        return None, None, None, None

# Input data section
st.header("Input Data")

# Use tabs for different input methods
input_method = st.radio("Choose input method:", ["Use Example Data", "Enter Custom Data"])

if input_method == "Use Example Data":
    # Load example data based on the problem type
    bigs, littles, big_prefs, little_prefs = get_example_data(problem_type)
    
    # Display the example data
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Bigs")
        st.json(bigs)
        st.subheader("Big Preferences")
        st.json(big_prefs)
    with col2:
        st.subheader("Littles")
        st.json(littles)
        st.subheader("Little Preferences")
        st.json(little_prefs)

else:  # Enter Custom Data
    st.markdown("""
    **Enter your data in JSON format:**
    - For bigs/littles, you can include a "max" field to specify maximum matches.
    - For preferences, use ranked lists or dictionaries based on the problem type.
    """)
    
    # Get example data first to show as placeholders
    example_bigs, example_littles, example_big_prefs, example_little_prefs = get_example_data(problem_type)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Bigs")
        bigs_text = st.text_area("Enter bigs data (JSON):", height=150, value=json.dumps(example_bigs, indent=2))
        
        st.subheader("Big Preferences")
        big_prefs_text = st.text_area("Enter big preferences (JSON):", height=200, value=json.dumps(example_big_prefs, indent=2))
    
    with col2:
        st.subheader("Littles")
        littles_text = st.text_area("Enter littles data (JSON):", height=150, value=json.dumps(example_littles, indent=2))
        
        st.subheader("Little Preferences")
        little_prefs_text = st.text_area("Enter little preferences (JSON):", height=200, value=json.dumps(example_little_prefs, indent=2))
    
    # Parse the input data when the user clicks "Solve"
    if st.button("Validate Input"):
        bigs, littles, big_prefs, little_prefs = parse_input_data(
            problem_type, bigs_text, littles_text, big_prefs_text, little_prefs_text
        )
        if bigs and littles and big_prefs and little_prefs:
            st.success("Input data validated successfully!")
        
# Additional parameters based on problem type
if problem_type == "Optimized Matching (with Preference Weights)":
    st.subheader("Additional Parameters")
    preference_weight = st.slider(
        "Preference Weight (Higher values favor big preferences over little preferences)",
        min_value=0.0, max_value=1.0, value=0.5, step=0.1
    )
    enforce_exactly_one = st.checkbox("Enforce exactly one match per participant", value=False)

# Solve button
if st.button("Solve Matching Problem"):
    with st.spinner("Solving..."):
        if input_method == "Use Example Data":
            # Use example data
            bigs, littles, big_prefs, little_prefs = get_example_data(problem_type)
        else:
            # Parse user input
            bigs, littles, big_prefs, little_prefs = parse_input_data(
                problem_type, bigs_text, littles_text, big_prefs_text, little_prefs_text
            )
            
        if problem_type == "Gale-Shapley Algorithm":
            # For Gale-Shapley we only need preference lists
            if not all([big_prefs, little_prefs]):
                st.error("Invalid input data. Please check your JSON format for preference lists.")
            else:
                # Prepare data for Gale-Shapley
                # For Gale-Shapley, we need simple preference lists
                if input_method == "Enter Custom Data":
                    # Convert preferences to lists if they're not already
                    if isinstance(list(big_prefs.values())[0], dict):
                        # Convert from dict to list format
                        big_prefs_lists = {}
                        for big, prefs in big_prefs.items():
                            # Sort by preference value (lower is better)
                            big_prefs_lists[big] = [p for p, _ in sorted(prefs.items(), key=lambda x: x[1])]
                        big_prefs = big_prefs_lists
                        
                        little_prefs_lists = {}
                        for little, prefs in little_prefs.items():
                            # Sort by preference value (lower is better)
                            little_prefs_lists[little] = [p for p, _ in sorted(prefs.items(), key=lambda x: x[1])]
                        little_prefs = little_prefs_lists
                
                try:
                    # Create GaleShapley instance with bigs as proposers
                    gs = GaleShapley(big_prefs, little_prefs)
                    matches = gs.match()
                    
                    # Store matches and preferences in session state
                    st.session_state.gs_matches = matches
                    st.session_state.big_prefs = big_prefs
                    st.session_state.little_prefs = little_prefs
                    st.session_state.show_littles_as_proposers = True
                    
                    # Display results
                    st.header("Gale-Shapley Results")
                    
                    # Create tabs for the two different approaches
                    tab1, tab2 = st.tabs(["Bigs as Proposers", "Littles as Proposers"])
                    
                    with tab1:
                        st.markdown("### Bigs as Proposers (optimize bigs' preferences)")
                        
                        # Create a graphviz object for visualization
                        graph = graphviz.Graph()
                        COLORS = ['aqua', 'coral', 'darkgreen', 'gold', 'darkolivegreen1',
                                'deeppink', 'crimson', 'darkorchid', 'bisque', 'yellow']
                        
                        # Add edges and nodes to the graph
                        for big, little in matches:
                            graph.edge(f'{big}', f'{little}', penwidth="1")
                            graph.node(f'{big}', color=COLORS[hash(big) % len(COLORS)])
                            graph.node(f'{little}', color=COLORS[hash(little) % len(COLORS)])
                        
                        # Display the graph
                        st.subheader("Matching Visualization")
                        render_graphviz(graph)
                        
                        # Display all matches in a table
                        st.subheader("Matches")
                        match_data = []
                        for big, little in matches:
                            match_data.append({"Big": big, "Little": little})
                        
                        st.table(match_data)
                    
                    with tab2:
                        st.markdown("### Littles as Proposers (optimize littles' preferences)")
                        
                        # Create GaleShapley with littles as proposers
                        gs_alt = GaleShapley(little_prefs, big_prefs)
                        matches_alt = gs_alt.match()
                        
                        # Invert the matches to maintain big->little format
                        matches_alt = [(little, big) for big, little in matches_alt]
                        
                        # Create a graphviz object for visualization
                        graph_alt = graphviz.Graph()
                        
                        # Add edges and nodes to the graph
                        for big, little in matches_alt:
                            graph_alt.edge(f'{big}', f'{little}', penwidth="1")
                            graph_alt.node(f'{big}', color=COLORS[hash(big) % len(COLORS)])
                            graph_alt.node(f'{little}', color=COLORS[hash(little) % len(COLORS)])
                        
                        # Display the graph
                        st.subheader("Matching Visualization")
                        render_graphviz(graph_alt)
                        
                        # Display all matches in a table
                        st.subheader("Matches")
                        match_data_alt = []
                        for big, little in matches_alt:
                            match_data_alt.append({"Big": big, "Little": little})
                        
                        st.table(match_data_alt)
                    
                    # Compare the two results
                    st.subheader("Comparison")
                    different = set(matches) != set(matches_alt)
                    if different:
                        st.warning("The two solutions are different! This shows how the Gale-Shapley algorithm favors the proposing side.")
                    else:
                        st.success("Both approaches produce the same matching!")
                    
                    # Provide download option for the results
                    st.subheader("Download Results")
                    col1, col2 = st.columns(2)
                    
                    def to_json_file(matches, proposers):
                        result = {
                            "matches": [{"big": b, "little": l} for b, l in matches],
                            "problem_type": "Gale-Shapley Algorithm",
                            "proposers": proposers
                        }
                        return json.dumps(result, indent=2)
                    
                    with col1:
                        st.download_button(
                            label="Download Bigs as Proposers Results",
                            data=to_json_file(matches, "bigs"),
                            file_name="gale_shapley_bigs_proposers.json",
                            mime="application/json"
                        )
                    
                    with col2:
                        st.download_button(
                            label="Download Littles as Proposers Results",
                            data=to_json_file(matches_alt, "littles"),
                            file_name="gale_shapley_littles_proposers.json",
                            mime="application/json"
                        )
                    
                except Exception as e:
                    st.error(f"Error solving with Gale-Shapley: {str(e)}")
        elif not all([bigs, littles, big_prefs, little_prefs]):
            st.error("Invalid input data. Please check your JSON format.")
        else:
            # Create the matcher for other algorithms
            matcher = BigLittleMatcher(bigs, littles, big_prefs, little_prefs)
            
            # Build the appropriate model based on the problem type
            if problem_type == "Classic Stable Matching (SMP)":
                matcher.build_model()
            elif problem_type == "Stable Matching with Ties (SMT)":
                matcher.build_model_smt()
            elif problem_type == "Stable Matching with Ties and Incomplete Lists (SMTI)":
                matcher.build_model_smti()
            else:  # Optimized Matching
                matcher.build_model_optimize(
                    preference_weight=preference_weight,
                    enforce_exactly_one=enforce_exactly_one
                )
            
            try:
                # Solve the model
                matches, objective_value, solve_time = matcher.solve()
                
                # Display results
                st.header("Matching Results")
                
                # Create a graphviz object for visualization
                graph = graphviz.Graph()
                COLORS = ['aqua', 'coral', 'darkgreen', 'gold', 'darkolivegreen1',
                        'deeppink', 'crimson', 'darkorchid', 'bisque', 'yellow']
                
                # Add edges and nodes to the graph
                for b, l in matches:
                    penwidth = str(matcher.scores.get((b, l), 1)) if hasattr(matcher, 'scores') else "1"
                    graph.edge(f'{b}', f'{l}', penwidth=penwidth)
                    graph.node(f'{b}', color=COLORS[hash(b) % len(COLORS)])
                    graph.node(f'{l}', color=COLORS[hash(l) % len(COLORS)])
                
                # Display the graph
                st.subheader("Matching Visualization")
                render_graphviz(graph)
                
                # Display statistics
                st.subheader("Statistics")
                st.write("Solver Response:")
                st.text(matcher.solver.ResponseStats())
                
                if problem_type == "Optimized Matching (with Preference Weights)":
                    st.write(f"Total preference score: {objective_value:.2f}")
                
                st.write(f"Solve time: {solve_time:.4f} seconds")
                
                # Check for instabilities and display them
                instabilities = matcher.check_instabilities(matches)
                if instabilities:
                    st.warning(f"Found {len(instabilities)} instabilities:")
                    for b, l in instabilities:
                        st.write(f"- ({b}, {l})")
                else:
                    st.success("No instabilities found - the matching is stable!")
                
                # Display all matches in a table
                st.subheader("Matches")
                match_data = []
                for b, l in matches:
                    match_data.append({"Big": b, "Little": l})
                
                st.table(match_data)
                
                # Provide download option for the results
                def to_json_file(matches, objective_value):
                    result = {
                        "matches": [{"big": b, "little": l} for b, l in matches],
                        "objective_value": float(objective_value),
                        "problem_type": problem_type
                    }
                    return json.dumps(result, indent=2)
                
                st.download_button(
                    label="Download Results as JSON",
                    data=to_json_file(matches, objective_value),
                    file_name="matching_results.json",
                    mime="application/json"
                )
                
            except Exception as e:
                st.error(f"Error solving the model: {str(e)}")

# Add footer
st.markdown("---")
st.markdown("Built with Streamlit by [Zora Mardjoko](https://github.com/zoramardjoko) and [Kevin He](https://github.com/Haokius)") 