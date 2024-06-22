import streamlit as st
import pandas as pd
import math
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# Average weekly spend (excluding rent) for a malaysian as taken from https://wise.com/us/blog/cost-of-living-in-malaysia#:~:text=You%20can%20live%20well%20for%20much%20less%20if%20you%20choose%20a%20home%20outside%20of%20the%20city%20center%2C%20or%20in%20another%20city%20entirely.
avg_weekly_spend = 573.40
# Average annual salary for a malaysian worker taken from: https://www.instarem.com/blog/average-salary-in-malaysia/
avg_annual_salary=79,300
# Average annual savings rate taken from https://www.straitstimes.com/asia/se-asia/malaysians-saving-less-most-do-not-have-enough-in-retirement-funds-survey
avg_annual_savings = 4800

# Risk returns here: https://www.syfe.com/core/core-growth
risk_data = pd.DataFrame({
    'risk_level': ['Low', 'Medium', 'High']
    , 'return': [3.8, 8.3, 11.5]
    , 'volatility': [1.5, 4, 8]
})
# FOr return projection

def plot_investment_growth(initial_amount, risk_data):
    # Define the date range
    date_range = pd.date_range(start="2024-06", end="2026-06", freq='M')

    # Initialize the dataframe to hold the results
    results = pd.DataFrame(index=date_range)

    #  Define color palette for the lines
    colors = {
        'Low': 'green',
        'Medium': 'blue',
        'High': 'purple',
        'Inflation': 'red'
    }

    return_dct = {}
    
    # Calculate the growth for each risk level
    for index, row in risk_data.iterrows():
        risk_level = row['risk_level']
        rate_of_return = row['return'] / 100  # converting percentage to decimal
        volatility = row['volatility']/100 # converting percentage to decimal
        return_dct[risk_level]=rate_of_return
        
        # Simulate the growth
        growth = [initial_amount]
        for i in range(1, len(date_range)):
            growth.append(growth[-1] * (1 + rate_of_return / 12))
        
        results[risk_level] = growth

        # Calculate the error bands based on volatility
        results[f'{risk_level}_upper'] = results[risk_level] * (1 + volatility)
        results[f'{risk_level}_lower'] = results[risk_level] * (1 - volatility)
    
    # Calculate the inflation benchmark
    inflation_rate = 0.03
    inflation_growth = [initial_amount]
    for i in range(1, len(date_range)):
        inflation_growth.append(inflation_growth[-1] * (1 + inflation_rate / 12))
    
    results['Inflation'] = inflation_growth
    
    # Plot the results using Plotly
    fig = make_subplots(rows=1, cols=1)
    
    # Add traces in the desired order
    order = ['High', 'Medium', 'Low', 'Inflation']
    for risk_level in order:
        if risk_level not in results.columns:
            continue
        line_style = dict(color=colors.get(risk_level, 'black'))
        if risk_level == 'Inflation':
            line_style.update({'dash': 'dash', 'color': 'red'})
        
        fig.add_trace(
            go.Scatter(
                x=results.index,
                y=results[risk_level],
                mode='lines',
                name=f"{risk_level} ({return_dct[risk_level]*100}% returns)" if risk_level != 'Inflation' else f"Inflation (3%)",
                line=line_style
                , hovertemplate='%{y:,.2f} RM'
            )
        )
        # if risk_level != 'Inflation':
        #     # Add Error bands
        #     fig.add_trace(
        #         go.Scatter(
        #             x=list(results.index) + list(results.index[::-1]),
        #             y=list(results[f'{risk_level}_upper']) + list(results[f'{risk_level}_lower'][::-1]),
        #             fill='toself',
        #             fillcolor=f'rgba(255, 182, 193, 0.2)' if risk_level == 'Low' else f'rgba(173, 216, 230, 0.2)' if risk_level == 'Medium' else f'rgba(216, 191, 216, 0.2)',
        #             line=dict(color='rgba(255, 255, 255, 0)'),
        #             showlegend=False,
        #             name=f'{risk_level} range'
        #         )
        #     )
    
    # Update the layout
    fig.update_layout(
        title="Investment Growth next 2 Years",
        hovermode='x unified',
        xaxis=dict(
            title="Date",
            titlefont=dict(size=18),
            tickfont=dict(size=14)
        ),
        yaxis=dict(
            title="Investment Value (RM)",
            titlefont=dict(size=18),
            tickfont=dict(size=14),
            tickformat=','
        ),
        legend_title="Investment Risk Level",
        legend_title_font=dict(size=12),
        font=dict(size=16),  # General font size for the plot
        template="plotly_dark"
        , legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=0.01
        )
    )
    
    return fig

# Sample DataFrame with selectable options categorized and their prices
data=pd.read_csv("./select_options.csv")
df = pd.DataFrame(data)

# Dictionary mapping questions to their respective categories
question_category_mapping = {
    "What's for lunch today?": 'meal',
    "What's for dinner today?": 'meal'
    , 'How are you getting around today?' : 'transport'
    , "What's happening this weekend?": "leisure"
}

# Mapping categories to how frequently to extrapolate them
category_frequency_mapping ={
    "meal": 'day'
    , 'transport': 'day'
    , 'leisure':'week'
}

# function to display select options
def format_options(label):
    price = df.loc[df['option']==label, 'price'].tolist()[0]
    return f"{label} (RM {price})"
    

# Function to extract options based on category
def get_options_by_category(category):
    return df[df['category'] == category]['option'].tolist()

# Function to calculate total amount spent based on selections per question
def calculate_total_amount(selections):
    total_amounts = {}
    for question, selected_options in selections.items():
        total = sum(df[df['option'].isin(selected_options)]['price'])
        total_amounts[question] = total
    return total_amounts

# Calculate the total roundup per question category
def calculate_total_roundup(selections):
    # Initialize the roundup dictionary at the CATEGORY level
    # E.g. {'meal': 0, 'leisure': 0, 'transport': 0}
    rounded_differences = {x: 0 for x in question_category_mapping.values()}
    # Aggregate by question
    for question, selected_options in selections.items():
        # What is the category for this question?
        question_category=question_category_mapping[question]
        # Compute the roundup amount for each option
        for option in selected_options:
            original_price = df[df['option'] == option]['price'].values[0]
            rounded_price = math.ceil(original_price)
            difference = rounded_price - original_price
            # Add it to the total roundup for that question category
            rounded_differences[question_category] += difference
    return rounded_differences

# Compute total weekly spending by question category
def weekly_spend_by_cat(total_amounts):
    result = {x: 0 for x in category_frequency_mapping.keys()}
    for question, total in total_amounts.items():
        # What category is this question?
        category = question_category_mapping[question]
        # How often does this happen? Either daily or weekly
        freq= category_frequency_mapping[category]
        if freq=='day':
            result[category] += (total*7)
        else:
            result[category] += total
    return result


# Compute the roundup differences extrapolated to week, month, year
def extrapolate_roundup_to_year(rounded_differences):
    roundup_extrapolate = {'week': 0, 'month':0, 'year':0}
    for category, roundup in rounded_differences.items():
        # How often does this happen? Either daily or weekly
        freq= category_frequency_mapping[category]
        # compute the weekly roundup for this category
        if freq=='day':
            week_round = roundup*7
        else:
            week_round = roundup #otherwise it must be a weekly frequency
        # Monthly value is simply 4x the weekly one
        month_round = week_round*4
        # Yearly value is 12x the monthly one
        year_round = month_round*12
        # Add to the final dictionary
        roundup_extrapolate['week'] += week_round
        roundup_extrapolate['month'] += month_round
        roundup_extrapolate['year'] += year_round
    return roundup_extrapolate


    

# Streamlit application layout
def main():
    # Display logo
    # st.title("Effortless Micro-Investing")
    st.image("logo.png", use_column_width=True)
    html_text = '''
    <p style='color:gold';"font-weight:bold">INVEST2U</p> makes investing frictionless and fun with the <p style='color:DarkBlue';"font-weight:bold">SaveUp Mechanic</p>.

    Each purchase is rounded up to the nearest dollar, and the difference is invested in a portfolio of your choosing!
    '''

    st.markdown('''
                **INVEST2U** makes investing frictionless and fun with the *SaveUp Mechanic*.

                Each purchase is rounded up to the nearest dollar, and the difference is invested in a portfolio of your choosing!

'''
                , unsafe_allow_html=True)

    # Dictionary to store selections
    selections = {}

    # Create a single column layout
    with st.container():
        for question, category in question_category_mapping.items():
            options = get_options_by_category(category)
            selections[question] = st.multiselect(question, options, format_func=format_options, placeholder='Choose one or more options')

    # Compute button. Only run when user wants to recompute
    if st.button('Round Up!'):
        # Compute the total weekly spending per category then sum to total
        total_amounts = calculate_total_amount(selections)
        weekly_spend = weekly_spend_by_cat(total_amounts)
        weekly_spend = sum(weekly_spend.values())
        # Compute the weekly, monthly, and yearly roundup amounts
        roundup_amounts = calculate_total_roundup(selections=selections)
        extrapolated_amounts = extrapolate_roundup_to_year(rounded_differences=roundup_amounts)
        weekly_roundup = extrapolated_amounts['week']
        yearly_roundup = extrapolated_amounts['year']
        
        # Display total amounts spent for each question
        # st.write("Total amount spent for each question:")
        # for question, total in total_amounts.items():
        #     st.write(f"{question}: ${total:.2f}")

        # Display total roundup for each category
        # st.write("Total roundup for each category:")
        # for category, total_roundup in roundup_amounts.items():
        #     st.write(f"{category}: ${total_roundup:.2f}")

        # Want to display:
        # 1. Total raw spend a week 
        # 2. Total Roundup Every Week 
        # 3. Total invested every year
        # Obtain the extrapolated values
        col1, col2, col3 = st.columns(3)
        # How much lower than the average weekly spend is this
        tmp_prop = round((weekly_spend - avg_weekly_spend)/avg_weekly_spend*100,1)
        col1.metric(f"Total Spending per week", f"RM {weekly_spend:.2f}", f"{tmp_prop}% {'higher' if tmp_prop>0 else 'lower'} than average*")
        # What proportion of the weekly roundup is the weekly spending? 
        tmp_prop = round(weekly_roundup/weekly_spend*100,1)
        col2.metric(f"Total Roundup per week", f"RM {weekly_roundup:.2f}", f"  {tmp_prop}% of normal spend")
        # What % of the avg annual savings rate is this
        tmp_prop=round(yearly_roundup/avg_annual_savings*100, 1)
        # To prevent display of delta arrow in metric component
        st.write(
            """
            <style>
            [data-testid="stMetricDelta"] svg {
                display: none;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        col3.metric(f"Total Invested per year", f"RM {yearly_roundup:,.2f}", f"{tmp_prop}% of avg* yearly savings")

        # Create the plot
        fig = plot_investment_growth(yearly_roundup, risk_data=risk_data)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("""
                    **Small, frequent investments can compound into substantial savings.** 
                    
                    **Big things are powered by small wins!**
                    """)
        st.divider()

        spend_url = 'https://wise.com/us/blog/cost-of-living-in-malaysia#:~:text=You%20can%20live%20well%20for%20much%20less%20if%20you%20choose%20a%20home%20outside%20of%20the%20city%20center%2C%20or%20in%20another%20city%20entirely'
        st.write(f"*Average weekly spending based on approximation from [source](%s)" % spend_url)
        save_url = 'https://www.straitstimes.com/asia/se-asia/malaysians-saving-less-most-do-not-have-enough-in-retirement-funds-survey'
        st.write(f"*Average yearly saving based on approximation from [source](%s)" % save_url)
        
        

if __name__ == "__main__":
    main()
