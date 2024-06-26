from flask import Flask, render_template, request
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

#load the dataset
try:
    dataset = pd.read_csv("merit.csv")
except FileNotFoundError:
    print("Error: File 'merit.csv' not found.")
    dataset = None  # or any other appropriate action, like creating an empty DataFrame

def calculate_merit(mdcet_score, fsc_score, matric_score):
    # Calculate individual components of merit
    mdcet_percentage = (mdcet_score / 200) * 100
    mdcet_merit = mdcet_percentage * 0.5

    fsc_percentage = (fsc_score / 1100) * 100
    fsc_merit = fsc_percentage * 0.4

    matric_percentage = (matric_score / 1100) * 100
    matric_merit = matric_percentage * 0.1

    # Calculate total merit
    total_merit = mdcet_merit + fsc_merit + matric_merit
    return total_merit

def get_position(merit):
    try:
        # Sort the dataset by merit in descending order
        dataset_sorted = dataset.sort_values(by='Merit', ascending=False)

        # Find the position of the student's merit in the sorted dataset
        position = (dataset_sorted['Merit'] > merit).sum() + 1
        return position
    except KeyError:
        print("Error: Column 'Merit' not found in the dataset.")
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/result', methods=['POST'])
def result():
    if request.method == 'POST':
        mdcet_score = float(request.form['mdcet_score'])
        fsc_score = float(request.form['fsc_score'])
        matric_score = float(request.form['matric_score'])

        # Calculate merit
        merit = calculate_merit(mdcet_score, fsc_score, matric_score)

        # Get position
        position = get_position(merit)

        if position is not None:
            total_students = len(dataset) if dataset is not None else "unknown"

            # Generate interactive plots
            if dataset is not None:
                # Merit comparison histogram
                fig_hist = px.histogram(dataset, x='Merit', nbins=30, title='Merit Score Comparison')
                fig_hist.add_vline(x=merit, line_dash='dash', line_color='red', annotation_text="Your Merit")

                # Merit vs. Position scatter plot
                dataset['Position'] = dataset['Merit'].rank(ascending=False)
                fig_scatter = px.scatter(dataset, x='Position', y='Merit', title='Merit vs. Position',
                                         labels={'Position': 'Position (Descending)', 'Merit': 'Merit Score'})

                # Convert plots to HTML
                graph_html_hist = fig_hist.to_html(full_html=False, include_plotlyjs='cdn')
                graph_html_scatter = fig_scatter.to_html(full_html=False, include_plotlyjs='cdn')
            else:
                graph_html_hist = None
                graph_html_scatter = None

            return render_template('index.html', mdcet_score=mdcet_score, fsc_score=fsc_score, matric_score=matric_score,
                                   merit=merit, total_students=total_students, position=position,
                                   graph_html_hist=graph_html_hist, graph_html_scatter=graph_html_scatter)
        else:
            return "Error: Unable to calculate the result."
    return "Error: Method not allowed."



#####------------<<<NU MERIT CALCULATOR FUNCTIONS>>>---------------#####


@app.route('/NUindex')
def NUindex():
    return render_template('NUindex.html', aggregate=None)

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        # Get form data
        matric_percentage = float(request.form['matric_percentage'])
        fsc_percentage = float(request.form['fsc_percentage'])
        nu_test_marks = float(request.form['nu_test_marks'])
        wrong_mcqs_except_english = int(request.form['wrong_mcqs_except_english'])
        wrong_mcqs_english = int(request.form['wrong_mcqs_english'])

        # Calculate the aggregate
        aggregate = (matric_percentage * 0.1) + \
                    (fsc_percentage * 0.4) + \
                    ((nu_test_marks - (wrong_mcqs_except_english * 0.25) - (wrong_mcqs_english * 0.25 * 0.33)) * 0.5)
        
        # Create the bar chart
        program_aggregates = {
            'BS Computer Science': 73,
            'BS Software Engineering': 73,
            'BS Artificial Intelligence': 72,
            'BS Electrical Engineering': 72,
            'BS Cyber Security': 68,
            'BS Data Science': 68,
            'BS Financial Technology': 61,
            'BS Business Administration': 59,
            'BS Accounting and Finance': 58,
            'BS Business Analytics': 56
        }

        programs = list(program_aggregates.keys())
        aggregates = list(program_aggregates.values())

        plt.figure(figsize=(12, 8))
        bars = plt.bar(programs, aggregates, label='Program Merit', alpha=0.7, color='skyblue')
        plt.axhline(y=aggregate, color='r', linestyle='--', linewidth=2, label=f'Your Aggregate: {aggregate:.2f}')
        plt.xticks(rotation=45, ha='right', fontsize=10)
        plt.ylabel('Aggregate Percentage', fontsize=12)
        plt.title('Comparison of Your Aggregate with Program Merits', fontsize=14)
        plt.legend()
        plt.grid(axis='y', linestyle='--', linewidth=0.7, alpha=0.7)

        # Add values on top of the bars
        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2, yval, round(yval, 2), va='bottom', ha='center', fontsize=10, color='black')

        img = io.BytesIO()
        plt.tight_layout()
        plt.savefig(img, format='png')
        img.seek(0)
        chart_url = base64.b64encode(img.getvalue()).decode()

        return render_template('NUindex.html', aggregate=aggregate, chart_url=chart_url)
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    app.run(debug=True)
