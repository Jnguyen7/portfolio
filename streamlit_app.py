#from tkinter import HORIZONTAL
#from turtle import width
from operator import irshift
from statistics import mean
#from turtle import color
from pyparsing import col
from streamlit_option_menu import option_menu
import time
import base64

# import libraries for data backend
from modulefinder import STORE_NAME
import re
#from tkinter.font import names
from tracemalloc import start
from unicodedata import name
from bs4 import BeautifulSoup
from numpy import choose, pad
from prometheus_client import Metric
import requests
from urllib.request import urlopen
import pandas as pd
from pprint import pprint

# import libraries for streamlit app
#from turtle import title
import plotly.express as px
from soupsieve import select
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


# website documentation: https://medium.com/codex/create-a-multi-page-app-with-the-new-streamlit-option-menu-component-3e3edaf7e7ad
# link for icons : https://icons.getbootstrap.com/
# compress pdf : https://www.adobe.com/acrobat/online/compress-pdf.html?mv=search&sdid=DZTGZX2P&ef_id=CjwKCAiAjoeRBhAJEiwAYY3nDARHYPn2H7Cs1ZrGfMDx01ikownQ-DYhp0EX_mKnwWtC6TyrWP3tjBoCG_QQAvD_BwE:G:s&s_kwcid=AL!3085!3!559402382057!e!!g!!pdf%20compress!12981897010!121481297003&cmpn=mobile-search&gclid=CjwKCAiAjoeRBhAJEiwAYY3nDARHYPn2H7Cs1ZrGfMDx01ikownQ-DYhp0EX_mKnwWtC6TyrWP3tjBoCG_QQAvD_BwE



# ----- ----- ----- #
# ----- Data Backend ------ #
# ----- ----- ----- #

# Dictionary Of All Micro Center Stores in The USA
store_ids = {
'CA-Tustin' : 101,
'CO-Denver' : 181,
'GA-Duluth' : 65,
'GA-Marietta' : 41,
'IL-Chicago' : 151,
'IL-Wesmont' : 25,
'KS-Overland Park' : 191,
'MA-Cambridge' : 121,
'MD-Rockville' : 85,
'MI-Madison Heights' : 55,
'MN-St. Louis Park' : 45,
'MO-Brentwood' : 95,
'NJ-North Jersey' : 75,
'NY-Westbury' : 171,
'NY-Brooklyn' : 115,
'NY-Flushing' : 145,
'NY-Yonkers' : 105,
'OH-Columbus' : 141,
'OH-Mayfield Heights' : 51,
'OH-Sharonville' : 71,
'PA-St. Davids' : 61,
'TX-Houston' : 155,
'TX-Dallas' : 131,
'VA-Fairfax' : 81,
}

def get_headers():
    r = requests.get('http://httpbin.org/headers')

    your_head = r.json()
    user_agent = your_head['headers']['User-Agent']

    header_dictionary = {
    'User-Agent' : user_agent
    }
    return header_dictionary

your_header = get_headers()

# Function to Find Soup JSON For Page 1
def find_soup(integer):
    #headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36'}
    headers  = your_header
    URL = f'https://www.microcenter.com/search/search_results.aspx?Ntk=all&sortby=match&rpp=96&N=4294966937&myStore=true&storeid={integer}&page=1'
    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup

# Function to Find Soup JSON For Page 2
def find_soup2(integer):
    #headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36'}
    headers  = your_header
    URL = f'https://www.microcenter.com/search/search_results.aspx?Ntk=all&sortby=match&rpp=96&N=4294966937&myStore=true&storeid={integer}&page=2'
    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup

# Function to Find Product Information For One Store
def find_info(soup, integer):
    categories = soup.find_all('a', {'id':f'hypProductH2_{integer}'})
    for d in categories:
        data_name = (d.get('data-name'))
        data_brand = (d.get('data-brand'))
        data_price = (d.get('data-price'))
        href_link = 'https://www.microcenter.com'+ d.get('href')
        return data_name, data_brand, data_price, href_link

# Function to Find Ratings For Store Products
def find_ratings(soup, integer):
    categories = soup.find_all('li', {'id':f'pwrapper_{integer}', 'class' : 'product_wrapper'})
    ratelist = []
    for soup_class in categories:
        reviews = soup_class.find_all('div', {'class' : 'ratingstars'})
        for soup_class in reviews:
            div = soup_class.find_all('div')
            for i in div:
                for j in i:
                    ratelist.append(j.text)

    if ratelist[0] == '0 Reviews':
        stars = 0
        numbers = 0
        return stars, numbers
    else:
        stars = int(str(ratelist[0])[0:1])
        numbers = int(re.findall(r'\d+', ratelist[1])[0])
        return stars, numbers

# Function to Find Inventory Count For Store Products
def find_inventory(soup, integer):
    categories = soup.find_all('li', {'id':f'pwrapper_{integer}', 'class' : 'product_wrapper'})
    for soup_class in categories:
        inventory = soup_class.find_all('div', {'class' : 'stock'})
        for cut in inventory:
            return(str(cut.text))

# Function to Find Maximum Number Of Items Displayed For One Store
def find_item_num(soup):
    emplist = []
    categories = soup.find_all('div', {'id':'bottomPagination', 'class' : 'pagination'})
    for soup_class in categories:
        num = soup_class.find_all('p', {'class' : 'status'})
        for i in num:
            emplist.append(i.text)
            
    numbers = (re.findall(r'\d+', emplist[0]))
    return (int(numbers[2]))

# Function For A List of All Product Information For One Store
def create_list2(store_id, store_integer):
    soup = find_soup(store_id)
    newlist = []
    if store_integer <= 96:
        for integer in range(0,store_integer):
            inventory_count = find_inventory(soup,integer).strip()
            inv_count = (re.findall(r'\d+', inventory_count))
            listprime = {
                'product_name' : find_info(soup,integer)[0],
                'brand_name' : find_info(soup,integer)[1],
                'product_price' : find_info(soup,integer)[2],
                'product_link' : find_info(soup,integer)[3],
                'product_star_count' : find_ratings(soup,integer)[0],
                'product_review_count' : find_ratings(soup,integer)[1],
                'product_inventory_count' : inv_count[0],
                #'product_inventory_name' : inventory_count
            }
            newlist.append(listprime)
    
    else:
        newsoup = find_soup2(store_id)
        second_page_integer = int(store_integer - 96)

        # Getting products between 1 and max items of 96
        for integer in range(0,96):
            inventory_count = find_inventory(soup,integer).strip()
            inv_count = (re.findall(r'\d+', inventory_count))
            listprime = {
                'product_name' : find_info(soup,integer)[0],
                'brand_name' : find_info(soup,integer)[1],
                'product_price' : find_info(soup,integer)[2],
                'product_link' : find_info(soup,integer)[3],
                'product_star_count' : find_ratings(soup,integer)[0],
                'product_review_count' : find_ratings(soup,integer)[1],
                'product_inventory_count' : inv_count[0],
                #'product_inventory_name' : inventory_count
            }
            newlist.append(listprime)
        
        # Getting products between 97 - store_integer
        #newurl = bottom_pagination(find_soup(store_integer))
        
        for integer in range(0,second_page_integer):
            inventory_count = find_inventory(newsoup,integer).strip()
            inv_count = (re.findall(r'\d+', inventory_count))
            listprime = {
                'product_name' : find_info(newsoup,integer)[0],
                'brand_name' : find_info(newsoup,integer)[1],
                'product_price' : find_info(newsoup,integer)[2],
                'product_link' : find_info(newsoup,integer)[3],
                'product_star_count' : find_ratings(newsoup,integer)[0],
                'product_review_count' : find_ratings(newsoup,integer)[1],
                'product_inventory_count' : inv_count[0],
                #'product_inventory_name' : inventory_count
            }
            newlist.append(listprime)
    return newlist

# Function For Pandas Dataframe
def get_df(store_list):
    store_data = pd.DataFrame(store_list, columns=['product_name', 'brand_name','product_price', 'product_link', 'product_star_count','product_review_count', 'product_inventory_count'])
    return store_data

# Final Call Function
@st.cache(allow_output_mutation=True, show_spinner=False)
def get_data(store_name):
        store_name_id = find_soup(store_ids[store_name])
        item_num = find_item_num(store_name_id)

        store_df = get_df(create_list2(store_ids[store_name],item_num))
        store_df['product_inventory_count'] = store_df['product_inventory_count'].astype('int64')
        store_df['product_price'] = store_df['product_price'].astype('float')
        return store_df

# ----- ----- ----- #
# ----- Data Charts ------ #
# ----- ----- ----- #

def pie_chart(df):
    pie_data = df['product_inventory_count'].to_list()
    pie_labels = df.index
    colors = sns.color_palette("hls",8)

    pie_label_size = pie_labels.size
    explode_list = []
    for i in range(0,pie_label_size):
        explode_list.append(0.02)

    max_value = max(pie_data)
    max_value_index = pie_data.index(max_value)
    explode_list[max_value_index] = 0.1

    pie_explode = explode_list

    plt.pie(pie_data, labels=pie_labels, colors=colors, autopct = '%0.0f%%', explode=explode_list, shadow= False, startangle=90,textprops={'color': 'Black', 'fontsize':25}, wedgeprops={'linewidth':6},center=(0.1,0.1), rotatelabels=True)
    plt.rcParams["figure.figsize"] = [50,50]

    gif_runner = st.image('images/processing.gif')

    st.set_option('deprecation.showPyplotGlobalUse', False)
    st.pyplot()

    gif_runner.empty()

def bar_chart(df):
    top_five_price = df.sort_values(by='product_price', ascending=False).nlargest(5, 'product_price').round(2)

    colors = sns.color_palette("hls",8)
    #ax, fig = plt.subplots(figsize=[15,7])
    #sns.barplot(x=top_five_price.index, y = 'product_price', data = top_five_price, palette= colors)

    fig = plt.subplots(figsize=[15,7])
    ax = sns.barplot(x=top_five_price.index, y = 'product_price', data = top_five_price, palette= colors)

    for bar, label in zip(ax.patches, top_five_price['product_price']):
        x = bar.get_x()
        width = bar.get_width()
        height = bar.get_height()
        ax.text(x+width/2., height + 1, label, ha="center") 

    gif_runner = st.image('images/processing.gif')

    st.set_option('deprecation.showPyplotGlobalUse', False)
    st.pyplot()

    gif_runner.empty()

def get_label_rotation(angle, offset):
    # Rotation must be specified in degrees :(
    rotation = np.rad2deg(angle + offset)
    if angle <= np.pi:
        alignment = "right"
        rotation = rotation + 180
    else: 
        alignment = "left"
    return rotation, alignment

def add_labels(angles, values, labels, offset, ax):
    
    # This is the space between the end of the bar and the label
    padding = 4
    
    # Iterate over angles, values, and labels, to add all of them.
    for angle, value, label, in zip(angles, values, labels):
        angle = angle
        
        # Obtain text rotation and alignment
        rotation, alignment = get_label_rotation(angle, offset)

        # And finally add the text
        ax.text(
            x=angle, 
            y=value + padding, 
            s=label, 
            ha=alignment, 
            va="center", 
            rotation=rotation, 
            rotation_mode="anchor"
        ) 

def grouped_bar_chart(test_df):
    test_df_sorted = (test_df.groupby(['brand_name']).apply(lambda x: x.sort_values(["product_review_count"], ascending = False)).reset_index(drop=True))

    VALUES = test_df_sorted["product_review_count"].values 
    LABELS = test_df_sorted["product_name"].values
    GROUP = test_df_sorted["brand_name"].values

    PAD = 3
    ANGLES_N = len(VALUES) + PAD * len(np.unique(GROUP))

    ANGLES = np.linspace(0, 2 * np.pi, num=ANGLES_N, endpoint=False)
    WIDTH = (2 * np.pi) / len(ANGLES)


    OFFSET = np.pi / 2

    # Specify offset
    #ax.set_theta_offset(OFFSET)
    offset = 0
    IDXS = []

    GROUPS_SIZE = []
    unique, counts = np.unique(GROUP, return_counts=True)
    result = np.column_stack((unique, counts))

    for i in range(0, len(result)):
        GROUPS_SIZE.append(result[i][1])
    for size in GROUPS_SIZE:
        IDXS += list(range(offset + PAD, offset + size + PAD))
        offset += size + PAD

    fig, ax = plt.subplots(figsize=(20, 10), subplot_kw={"projection": "polar"})

    ax.set_theta_offset(OFFSET)
    ax.set_ylim(-100, 100)
    ax.set_frame_on(False)
    ax.xaxis.grid(False)
    ax.yaxis.grid(False)
    ax.set_xticks([])
    ax.set_yticks([])

    GROUPS_SIZE = []
    unique, counts = np.unique(GROUP, return_counts=True)
    result = np.column_stack((unique, counts))

    for i in range(0, len(result)):
        GROUPS_SIZE.append(result[i][1])
    COLORS = [f"C{i}" for i, size in enumerate(GROUPS_SIZE) for _ in range(size)]

    # Add bars to represent ...
    ax.bar(
        ANGLES[IDXS], VALUES, width=WIDTH, color=COLORS, 
        edgecolor="white", linewidth=2
    )

    add_labels(ANGLES[IDXS], VALUES, LABELS, OFFSET, ax)

    offset = 0 
    test_list = unique.tolist()
    for group, size in zip(test_list, GROUPS_SIZE):
        # Add line below bars
        x1 = np.linspace(ANGLES[offset + PAD], ANGLES[offset + size + PAD - 1], num=50)
        ax.plot(x1, [-5] * 50, color="#333333")
        
        # Add text to indicate group
        ax.text(
            np.mean(x1), -20, group, color="#333333", fontsize=14, 
            fontweight="bold", ha="center", va="center"
        )
        
        # Add reference lines at 20, 40, 60, and 80
        x2 = np.linspace(ANGLES[offset], ANGLES[offset + PAD - 1], num=50)
        ax.plot(x2, [20] * 50, color="#bebebe", lw=0.8)
        ax.plot(x2, [40] * 50, color="#bebebe", lw=0.8)
        ax.plot(x2, [60] * 50, color="#bebebe", lw=0.8)
        ax.plot(x2, [80] * 50, color="#bebebe", lw=0.8)
        
        offset += size + PAD

    gif_runner = st.image('images/processing.gif')

    st.set_option('deprecation.showPyplotGlobalUse', False)
    st.pyplot()

    gif_runner.empty()

def most_expensive(test_df):
    prices = test_df.sort_values(by=['product_price'], ascending=False).head(10).sort_values('product_price')
    my_range = range(0,len(prices))

    fig = plt.figure(figsize=(14,10))

    plt.hlines(y=prices['product_name'], xmin=0, xmax=prices['product_price'], color='black')
    plt.plot(prices['product_price'], my_range, "o", color = 'black')
    plt.xlabel('Price (USD)', fontsize=20)
    plt.ylabel('Product Name',fontsize=20)
    plt.yticks(fontsize=15)
    plt.xticks(fontsize=15)
    plt.xlim(0,max(prices['product_price'])+100)
    plt.grid()
    plt.title("Most Expensive Products", fontsize=20, x=0.5,y=1.02)

    gif_runner = st.image('images/processing.gif')
    st.set_option('deprecation.showPyplotGlobalUse', False)
    st.pyplot()
    gif_runner.empty()

def least_expensive(test_df):
    prices = test_df.sort_values(by=['product_price'], ascending=True).head(10).sort_values('product_price')
    my_range = range(0,len(prices))

    fig = plt.figure(figsize=(14,10))

    plt.hlines(y=prices['product_name'], xmin=0, xmax=prices['product_price'], color='black')
    plt.plot(prices['product_price'], my_range, "o", color = 'black')
    plt.xlabel('Price (USD)', fontsize=20)
    plt.ylabel('Product Name',fontsize=20)
    plt.yticks(fontsize=15)
    plt.xticks(fontsize=15)
    plt.xlim(0,max(prices['product_price'])+100)
    plt.grid()
    plt.title("Least Expensive Products", fontsize=20, x=0.5,y=1.02)

    gif_runner = st.image('images/processing.gif')
    st.set_option('deprecation.showPyplotGlobalUse', False)
    st.pyplot()
    gif_runner.empty()



# ----- Functions ----- #

def show_pdf(file_path):
    with open(file_path,"rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="1200" height="800" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def download_pdf(file_path):
    with open(file_path, "rb") as pdf_file:
        PDFbyte = pdf_file.read()

    st.download_button(label="Download PDF", 
            data=PDFbyte,
            file_name=file_path,
            mime='application/octet-stream')

# ----- ----- ----- #
# ----- Data Charts ------ #
# ----- ----- ----- #

def scatter_plot(df, x, y):
    sns.jointplot(x=df["y"], y=-df["x"], kind='scatter', s=200, color='m', edgecolor="skyblue", linewidth=2)
    sns.set(style="white", color_codes=True)

    st.set_option('deprecation.showPyplotGlobalUse', False)
    st.pyplot()

def hex_plot(df, x, y):
    sns.jointplot(x=df["y"], y=-df["x"], kind='hex', marginal_kws=dict(bins=30, fill=True))
    sns.set(style="white", color_codes=True)

    st.set_option('deprecation.showPyplotGlobalUse', False)
    st.pyplot()

def kde_plot(df, x, y):
    sns.jointplot(x=df["y"], y=-df["x"], kind='kde', color="skyblue")

    sns.set(style="white", color_codes=True)

    st.set_option('deprecation.showPyplotGlobalUse', False)
    st.pyplot()   

# ----- ----- ----- #
# ----- ----- ----- #
# ----- Main site ----- #
# ----- ----- ----- #
# ----- ----- ----- #

# ----- TITLE BAR ----- # 
st.set_page_config(page_title="Joshua Nguyen", page_icon=":computer:", layout="wide")

st.header('Joshua Nguyen :speech_balloon:')

with st.sidebar:
    choose = option_menu("Main Menu", ["Home", "Find A GPU","Full Projects", "Archive", "About Me & Contact"],
                         icons=['house','shop-window', 'archive-fill', 'book','person-lines-fill'],
                         menu_icon="briefcase", default_index=0,
                         styles={
        "container": {"padding": "5!important", "background-color": "#fafafa"},
        "icon": {"color": "#001219", "font-size": "25px"}, 
        "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
        "nav-link-selected": {"background-color": "#ddbea9"},
    }
    )
    

if choose == "Home":
        st.markdown(""" <style> .font {
        font-size:35px ; font-family: 'serif'; color: #001219;} 
        </style> """, unsafe_allow_html=True)
        st.markdown('<p class="font">Data Analyst/Scientist From Houston, Texas, USA</p>', unsafe_allow_html=True)

        # ----- Texas Scatter Plot ----- #      
        texas_data = pd.read_csv('csv_files/texas3.csv')
        home_col1, home_col2, home_col3 = st.columns(3)
        with home_col1:
            scatter_plot(texas_data, 'x', 'y')
        with home_col2:
            hex_plot(texas_data, 'x', 'y')
        with home_col3:
            kde_plot(texas_data, 'x', 'y')
        st.dataframe(texas_data)

elif choose == "Full Projects":
    # ----- Amazon Best Sellers ----- #
    feature_image1 = 'images/amazon.png'
    with st.container():
        image_col, text_col = st.columns((1,3))
        with image_col:
            st.image(feature_image1, use_column_width= True)
        with text_col:
            st.markdown(""" <style> .font {
        font-size:35px ; font-family: 'Cooper Black'; color: #FF9633;} 
        </style> """, unsafe_allow_html=True)
            st.markdown('<p class="font">Amazons ‘Best’ Sellers </p>', unsafe_allow_html=True)    
            st.markdown("By Joshua Nguyen - Project that webscrapes Amazon's Best Sellers Page. Its main goal is to direct how individual businesses can achieve Amazon's top sellers list.")
            st.markdown("View code on my GitHub Repo: https://github.com/Jnguyen7/Python/blob/main/amazon_best_sellers.ipynb")
            st.markdown("Tools: Python")

    col1, col2,col3= st.columns(3)
    with col1:  
        if st.button('Read PDF',key='1'):            
            show_pdf('pdfs/Amazon_best_sellers-compressed.pdf')
    with col2:
        st.button('Close PDF',key='2')                   
    with col3:
        download_pdf('pdfs/Amazon_best_sellers-compressed.pdf')

    st.markdown("---")

    # ----- Movie Clips Analysis ----- #
    feature_image1 = 'images/movieclips.png'
    with st.container():
        image_col, text_col = st.columns((1,3))
        with image_col:
            st.image(feature_image1,  use_column_width= True)
        with text_col:
            st.markdown('<p class="font">MovieClips Fandango Data Analysis</p>', unsafe_allow_html=True)    
            st.markdown("By Joshua Nguyen - Project that analyzes MovieClips' Youtube channel. Its main goal seeks to improve viewership for this channel.")
            st.markdown("View code on my GitHub Repo: https://github.com/Jnguyen7/SQL/blob/main/MovieClips.sql")
            st.markdown("View Tableau Dashboard: https://public.tableau.com/app/profile/joshua.nguyen/viz/MovieClipsDataAnalysis/Dashboard1")
            st.markdown("Tools: Tableau, SQL, Python")
    col1, col2,col3= st.columns(3)
    with col1:  
        if st.button('Read PDF',key='3'):            
            show_pdf('pdfs/MovieClips_Analysis.pdf')
    with col2:
        st.button('Close PDF',key='4')                   
    with col3:
        download_pdf('pdfs/MovieClips_Analysis.pdf')

    st.markdown("---")


    # ----- Weather Analysis ----- #
    feature_image1 = 'images/weather.png'
    with st.container():
        image_col, text_col = st.columns((1,3))
        with image_col:
            st.image(feature_image1,  use_column_width= True)
        with text_col:
            st.markdown('<p class="font">MovieClips Fandango Data Analysis</p>', unsafe_allow_html=True)    
            st.markdown("By Joshua Nguyen - Project that uses API to extract and analyze real time weather data throughout the United States of America. Its main goal is to help meterologists predict natural weather disasters like tornadoes.")
            st.markdown("View code on my GitHub Repo: https://github.com/Jnguyen7/Python/blob/main/weather_forecast_data.ipynb")
            st.markdown("View Tableau Dashboard: https://public.tableau.com/app/profile/joshua.nguyen/viz/Weather_data_16479998134410/CityDashboard?publish=yes")
            st.markdown("Tools: Tableau, Python")
    col1, col2,col3= st.columns(3)
    with col1:  
        if st.button('Read PDF',key='5'):            
            show_pdf('pdfs/Weather_Data.pdf')
    with col2:
        st.button('Close PDF',key='6')                   
    with col3:
        download_pdf('pdfs/Weather_Data.pdf')

    st.markdown("---")

    # ----- Flu Vaccination ----- #
    feature_image1 = 'images/flu.png'
    with st.container():
        image_col, text_col = st.columns((1,3))
        with image_col:
            st.image(feature_image1,  use_column_width= True)
        with text_col:
            st.markdown('<p class="font">Flu Vaccinations Data Analysis</p>', unsafe_allow_html=True)    
            st.markdown("By Joshua Nguyen - project that explores the Influenza Vaccination Status in the United States of America Between 2014 to 2021")
            st.markdown("View code on my GitHub Repo: https://github.com/Jnguyen7/SQL/blob/main/Vaccination.sql")
            st.markdown("View Tableau Dashboard: https://public.tableau.com/app/profile/joshua.nguyen/viz/Weather_data_16479998134410/CityDashboard?publish=yes")
            st.markdown("Tools: SQL, Tableau")
    col1, col2,col3= st.columns(3)
    with col1:  
        if st.button('Read PDF',key='7'):            
            show_pdf('pdfs/Flu_Vaccination_Project.pdf')
    with col2:
        st.button('Close PDF',key='8')                   
    with col3:
        download_pdf('pdfs/Flu_Vaccination_Project.pdf')

    st.markdown("---")

    # ----- Real Estate Analysis ----- #
    feature_image1 = 'images/nyc.png'
    with st.container():
        image_col, text_col = st.columns((1,3))
        with image_col:
            st.image(feature_image1,  use_column_width= True)
        with text_col:
            st.markdown('<p class="font">Real Estate Data Analysis</p>', unsafe_allow_html=True)    
            st.markdown("By Joshua Nguyen - Project that analyzes real estate market in New York City. Its main goal seeks to create a interactive dashboard that helps potential real estate investors.")
            st.markdown("View code on my GitHub Repo: https://github.com/Jnguyen7/Excel/tree/main")
            st.markdown("Tools: Excel")
    col1, col2,col3= st.columns(3)
    with col1:  
        if st.button('Read PDF',key='9'):            
            show_pdf('pdfs/Real_Estate_Analysis.pdf')
    with col2:
        st.button('Close PDF',key='10')                   
    with col3:
        download_pdf('pdfs/Real_Estate_Analysis.pdf')

    st.markdown("---")

    # ----- RLife ----- #
    feature_image1 = 'images/R.png'
    with st.container():
        image_col, text_col = st.columns((1,3))
        with image_col:
            st.image(feature_image1,  use_column_width= True)
        with text_col:
            st.markdown('<p class="font">R Documentation</p>', unsafe_allow_html=True)    
            st.markdown("By Joshua Nguyen - This manual contains and provides the fundamental basis of R and RStudio in a rudimentary vernacular for the common layperson. It also archives some of Joshua Nguyen’s projects in R and statistical computation.")
            st.markdown("Tools: R")
    col1, col2,col3= st.columns(3)
    with col1:  
        if st.button('Read PDF',key='11'):            
            show_pdf('pdfs/R_Life.pdf')
    with col2:
        st.button('Close PDF',key='12')                   
    with col3:
        download_pdf('pdfs/R_Life.pdf')

    st.markdown("---")




elif choose == "Archive":
    choose = option_menu(None,["Python", "SQL", "Machine Learning"],
                         icons=['list-nested', 'server','gear-wide-connected'],
                         orientation = 'horizontal',
                         styles={
        "container": {"padding": "5!important", "background-color": "#fafafa"},
        "icon": {"color": "#001219", "font-size": "25px"}, 
        "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
        "nav-link-selected": {"background-color": "#ddbea9"},
    }
    )

    if choose == "Python":
        st.markdown(""" <style> .font {
        font-size:35px ; font-family: 'Montserrat'; color: #FF9633;} 
        </style> """, unsafe_allow_html=True)
        iris = pd.read_csv('csv_files/iris.csv')
        col1,col2,col3 = st.columns([1,3,1])
        with col2:
            st.subheader('Iris Dataset')
            st.dataframe(iris)
        
        choose_py = option_menu(None,["Barplot","Grouped Circular Barplot", "Scatterplot", "Lollipop", "Radar Plot", "Pie Plot", "Tree Map"],
                         icons=['bar-chart-line-fill', 'pie-chart','graph-up', 'sliders', 'bullseye', 'pie-chart-fill', 'tree-fill'],
                         styles={
        "container": {"padding": "5!important", "background-color": "#fafafa"},
        "icon": {"color": "#001219", "font-size": "25px"}, 
        "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
        "nav-link-selected": {"background-color": "#ddbea9"},
        }
        )
        if choose_py == "Barplot":
            st.markdown('<p class="font">Barplots Using Seaborn</p>', unsafe_allow_html=True)

            bar_code = '''
            # Import Libraries
import pandas as pd
import seaborn as sns

# Import dataset
iris = pd.read_csv('iris.csv')

# Color palette
colors = sns.color_palette("hls", 8)

# Set Dark Background
sns.set(style="darkgrid")

# Initialize Plot Grid
ax, fig = plt.subplots(figsize= [10,7])

# Create Plot
bar_fig = sns.barplot(
    data = iris,
    x = 'variety',
    y = 'petal.length',
    palette = colors,
    estimator = mean)      
'''

            st.code(bar_code, language='python')

            colors = sns.color_palette("hls", 8)
            sns.set(style="darkgrid")
            ax, fig = plt.subplots(figsize= [10,7])
            bar_fig = sns.barplot(
                data = iris,
                x = 'variety',
                y = 'petal.length',
                palette = colors,
                estimator = mean)
            st.pyplot()

            st.markdown('<p class="font">Customized Grouped Barplots With Seaborn</p>', unsafe_allow_html=True)

            
            # Horizontal Group Bar Chart Petal Length Vs Petal Width

            hbar_code = '''
            # Import Libraries
import pandas as pd
import seaborn as sns

# Import dataset
iris = pd.read_csv('iris.csv')

# Group Values by Mean Values
grouped_iris = iris.groupby('variety').mean()

# Initialize Plot
sns.set(style="darkgrid")
barWidth = 0.3

# Height of Petal Length Bars
petal_length_bars = grouped_iris['petal.length'].tolist()

# Height of Petal Width Bars
petal_width_bars = grouped_iris['petal.width'].tolist()

# List of Grouped Variety Names
petal_variety = grouped_iris.index.tolist()

# The x position of bars
r1 = np.arange(len(petal_length_bars))
r2 = [x + barWidth for x in r1]

# Create Petal Length Bars
plt.bar(r1, 
    petal_length_bars,
    width = barWidth,
    color = 'blue',
    edgecolor = 'black',
    capsize=7,
    label='petal length',
    alpha = 0.4)

# Create Petal Width Bars
plt.bar(r2,
    petal_width_bars,
    width = barWidth,
    color = 'cyan',
    edgecolor = 'black',
    capsize=7,
    label='petal width',
    alpha = 0.4)

# Plot Layout
plt.xticks([r + barWidth for r in range(len(petal_length_bars))], petal_variety)
plt.ylabel('height')
plt.title('Mean Size Comparison Between Petal Length Vs Petal Width Between Iris Species')
plt.legend()

# Show Plot
plt.show()   
'''
            st.code(hbar_code, language='python')

            grouped_iris = iris.groupby('variety').mean()
            sns.set(style="darkgrid")
            barWidth = 0.3

            # height of petal length bars
            petal_length_bars = grouped_iris['petal.length'].tolist()

            # height of petal width bars
            petal_width_bars = grouped_iris['petal.width'].tolist()

            # List of Grouped Variety
            petal_variety = grouped_iris.index.tolist()


            # The x position of bars
            r1 = np.arange(len(petal_length_bars))
            r2 = [x + barWidth for x in r1]

            # Create blue bars
            plt.bar(r1, petal_length_bars, width = barWidth, color = 'blue', edgecolor = 'black', capsize=7, label='petal length', alpha = 0.4)

            # Create cyan bars
            plt.bar(r2, petal_width_bars, width = barWidth, color = 'cyan', edgecolor = 'black', capsize=7, label='petal width', alpha = 0.4)

            # general layout
            plt.xticks([r + barWidth for r in range(len(petal_length_bars))], petal_variety)
            plt.ylabel('height')
            plt.title('Mean Size Comparison Between Petal Length Vs Petal Width Between Iris Species')
            plt.legend()
            
            # Show graphic
            st.pyplot()

        if choose_py == "Radar Plot":
            st.markdown('<p class="font">Radar Plots Using Seaborn</p>', unsafe_allow_html=True)

            radarplot = '''
            # Import Libraries
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D

# Import dataset
texas_data = pd.read_csv('csv_files/texas3.csv')

# Create Function to Rescale Numeric Variables
def rescale(x):
    return (x-np.min(x))/np.ptp(x)

# Group By Class
iris_radar = (
    iris.groupby('variety').agg(
        avg_petal_length = ('petal.length', np.mean),
        avg_petal_width = ('petal.width', np.mean),
        avg_sepal_length = ('sepal.length', np.mean),
        avg_sepal_width = ('sepal.width', np.mean)
    )
    .apply(lambda x: rescale(x))
    .reset_index()
)
'''
            radar_plot = '''
            # Background Colors
BG_WHITE = "#fbf9f4"
BLUE = "#2a475e"
GREY70 = "#b3b3b3"
GREY_LIGHT = "#f2efe8"
COLORS = ["#FF5A5F", "#FFB400", "#007A87"]

# Creating List of Iris Species
SPECIES = iris_radar["variety"].values.tolist()

# Creating List of Iris Dimensions, i.e., petal width, length and sepal length and width
VARIABLES = iris_radar.columns.tolist()[1:]
VARIABLES_N = len(VARIABLES)

# Plot Angles
ANGLES = [n / VARIABLES_N * 2 * np.pi for n in range(VARIABLES_N)]
ANGLES += ANGLES[:1]

# Tick Labels
X_VERTICAL_TICK_PADDING = 5
X_HORIZONTAL_TICK_PADDING = 50    

# Angle values going from 0 to 2*pi
HANGLES = np.linspace(0, 2 * np.pi)

# Plot Axis
H0 = np.zeros(len(HANGLES))
H1 = np.ones(len(HANGLES)) * 0.5
H2 = np.ones(len(HANGLES))

# Initialize Plot
fig = plt.figure(figsize=(14, 10))
ax = fig.add_subplot(111, polar=True)

fig.patch.set_facecolor(BG_WHITE)
ax.set_facecolor(BG_WHITE)

# Rotate Degrees on Top
ax.set_theta_offset(np.pi / 2)
ax.set_theta_direction(-1)

# Setting Lower Limit to Reduce Gap
# for values that are 0 (the minimums)
ax.set_ylim(-0.1, 1.05)

# Plot Lines and Dots
for idx, species in enumerate(SPECIES):
    values = iris_radar.iloc[idx].drop("variety").values.tolist()
    values += values[:1]
    ax.plot(ANGLES, values, c=COLORS[idx], linewidth=4, label=species)
    ax.scatter(ANGLES, values, s=160, c=COLORS[idx], zorder=10)

# Setting Values For Angular Axis
ax.set_xticks(ANGLES[:-1])
ax.set_xticklabels(VARIABLES, size=14)

# Removing Lines For Radial Axis
ax.set_yticks([])
ax.yaxis.grid(False)
ax.xaxis.grid(False)

# Removing Spines
ax.spines["start"].set_color("none")
ax.spines["polar"].set_color("none")

# Adding Lines For Custom Lines At Y-Axis
ax.plot(HANGLES, H0, ls=(0, (6, 6)), c=GREY70)
ax.plot(HANGLES, H1, ls=(0, (6, 6)), c=COLORS[2])
ax.plot(HANGLES, H2, ls=(0, (6, 6)), c=GREY70)

# Fill Circle With Radius 1
ax.fill(HANGLES, H2, GREY_LIGHT)

# Creating Custom Guide For Angular Axis
ax.plot([0, 0], [0, 1], lw=2, c=GREY70)
ax.plot([np.pi, np.pi], [0, 1], lw=2, c=GREY70)
ax.plot([np.pi / 2, np.pi / 2], [0, 1], lw=2, c=GREY70)
ax.plot([-np.pi / 2, -np.pi / 2], [0, 1], lw=2, c=GREY70)

# Adding Levels, Values of Radial Axis
PAD = 0.05
ax.text(-0.4, 0 + PAD, "0%", size=16, fontname="Roboto")
ax.text(-0.4, 0.5 + PAD, "50%", size=16, fontname="Roboto")
ax.text(-0.4, 1 + PAD, "100%", size=16, fontname="Roboto")
ax.fill(ANGLES, values, 'b', alpha=0.1)

handles = [
    Line2D(
        [], [], 
        c=color, 
        lw=3, 
        marker="o", 
        markersize=8, 
        label=species
    )
    for species, color in zip(SPECIES, COLORS)
]

legend = ax.legend(
    handles=handles,
    loc=(1, 0),       # bottom-right
    labelspacing=1.5, # add space between labels
    frameon=False     # don't put a frame
)

# Plot Text 
for text in legend.get_texts():
    text.set_fontname("Sans Serif") 
    text.set_fontsize(16) 

# Tick Label Positions
XTICKS = ax.xaxis.get_major_ticks()
for tick in XTICKS[0::2]:
    tick.set_pad(X_VERTICAL_TICK_PADDING)
    
for tick in XTICKS[1::2]:
    tick.set_pad(X_HORIZONTAL_TICK_PADDING)

# Plot Title
fig.suptitle(
    "Radar Plot of Iris Species",
    x = 0.1,
    y = 1,
    ha="left",
    fontsize=32,
    fontname="Roboto",
    color=BLUE,
    weight="bold",    
)

# Show Plot
fig.show()
'''
            
            st.code(radarplot, language='python')
            st.code(radar_plot, language='python')

            def rescale(x):
                return (x-np.min(x))/np.ptp(x)

            iris_radar = (
                iris.groupby('variety').agg(
                    avg_petal_length = ('petal.length', np.mean),
                    avg_petal_width = ('petal.width', np.mean),
                    avg_sepal_length = ('sepal.length', np.mean),
                    avg_sepal_width = ('sepal.width', np.mean)
                )
                .apply(lambda x: rescale(x))
                .reset_index()
            )

            BG_WHITE = "#fbf9f4"
            BLUE = "#2a475e"
            GREY70 = "#b3b3b3"
            GREY_LIGHT = "#f2efe8"
            COLORS = ["#FF5A5F", "#FFB400", "#007A87"]

            # The three species of iris
            SPECIES = iris_radar["variety"].values.tolist()

            # The four variables in the plot
            VARIABLES = iris_radar.columns.tolist()[1:]
            VARIABLES_N = len(VARIABLES)

            # The angles at which the values of the numeric variables are placed
            ANGLES = [n / VARIABLES_N * 2 * np.pi for n in range(VARIABLES_N)]
            ANGLES += ANGLES[:1]

            # Padding used to customize the location of the tick labels
            X_VERTICAL_TICK_PADDING = 5
            X_HORIZONTAL_TICK_PADDING = 50    

            # Angle values going from 0 to 2*pi
            HANGLES = np.linspace(0, 2 * np.pi)

            # Used for the equivalent of horizontal lines in cartesian coordinates plots 
            # The last one is also used to add a fill which acts a background color.
            H0 = np.zeros(len(HANGLES))
            H1 = np.ones(len(HANGLES)) * 0.5
            H2 = np.ones(len(HANGLES))

            # Initialize layout ----------------------------------------------
            fig = plt.figure(figsize=(14, 10))
            ax = fig.add_subplot(111, polar=True)

            fig.patch.set_facecolor(BG_WHITE)
            ax.set_facecolor(BG_WHITE)

            # Rotate the "" 0 degrees on top. 
            # There it where the first variable, avg_bill_length, will go.
            ax.set_theta_offset(np.pi / 2)
            ax.set_theta_direction(-1)

            # Setting lower limit to negative value reduces overlap
            # for values that are 0 (the minimums)
            ax.set_ylim(-0.1, 1.05)

            # Plot lines and dots --------------------------------------------
            for idx, species in enumerate(SPECIES):
                values = iris_radar.iloc[idx].drop("variety").values.tolist()
                values += values[:1]
                ax.plot(ANGLES, values, c=COLORS[idx], linewidth=4, label=species)
                ax.scatter(ANGLES, values, s=160, c=COLORS[idx], zorder=10)

            # Set values for the angular axis (x)
            ax.set_xticks(ANGLES[:-1])
            ax.set_xticklabels(VARIABLES, size=14)

            # Remove lines for radial axis (y)
            ax.set_yticks([])
            ax.yaxis.grid(False)
            ax.xaxis.grid(False)

            # Remove spines
            ax.spines["start"].set_color("none")
            ax.spines["polar"].set_color("none")

            # Add custom lines for radial axis (y) at 0, 0.5 and 1.
            ax.plot(HANGLES, H0, ls=(0, (6, 6)), c=GREY70)
            ax.plot(HANGLES, H1, ls=(0, (6, 6)), c=COLORS[2])
            ax.plot(HANGLES, H2, ls=(0, (6, 6)), c=GREY70)

            # Now fill the area of the circle with radius 1.
            # This create the effect of gray background.
            ax.fill(HANGLES, H2, GREY_LIGHT)

            # Custom guides for angular axis (x).
            # These four lines do not cross the y = 0 value, so they go from 
            # the innermost circle, to the outermost circle with radius 1.
            ax.plot([0, 0], [0, 1], lw=2, c=GREY70)
            ax.plot([np.pi, np.pi], [0, 1], lw=2, c=GREY70)
            ax.plot([np.pi / 2, np.pi / 2], [0, 1], lw=2, c=GREY70)
            ax.plot([-np.pi / 2, -np.pi / 2], [0, 1], lw=2, c=GREY70)

            # Add levels -----------------------------------------------------
            # These labels indicate the values of the radial axis
            PAD = 0.05
            ax.text(-0.4, 0 + PAD, "0", size=16, fontname="Roboto")
            ax.text(-0.4, 0.5 + PAD, "0.5", size=16, fontname="Roboto")
            ax.text(-0.4, 1 + PAD, "1", size=16, fontname="Roboto")
            ax.fill(ANGLES, values, 'b', alpha=0.1)

            from matplotlib.lines import Line2D
            handles = [
                Line2D(
                    [], [], 
                    c=color, 
                    lw=3, 
                    marker="o", 
                    markersize=8, 
                    label=species
                )
                for species, color in zip(SPECIES, COLORS)
            ]

            legend = ax.legend(
                handles=handles,
                loc=(1, 0),       # bottom-right
                labelspacing=1.5, # add space between labels
                frameon=False     # don't put a frame
            )

            # Iterate through text elements and change their properties
            for text in legend.get_texts():
                text.set_fontname("Sans Serif") # Change default font 
                text.set_fontsize(16)       # Change default font size

            # Adjust tick label positions ------------------------------------
            XTICKS = ax.xaxis.get_major_ticks()
            for tick in XTICKS[0::2]:
                tick.set_pad(X_VERTICAL_TICK_PADDING)
                
            for tick in XTICKS[1::2]:
                tick.set_pad(X_HORIZONTAL_TICK_PADDING)

            # Add title ------------------------------------------------------
            fig.suptitle(
                "Radar Plot of Iris Species",
                x = 0.1,
                y = 1,
                ha="left",
                fontsize=32,
                fontname="Roboto",
                color=BLUE,
                weight="bold",    
            )

            st.pyplot()


        if choose_py == 'Scatterplot':
            st.markdown('<p class="font">Scatterplots Using Seaborn</p>', unsafe_allow_html=True)
            scatter = '''
            # Import Libraries
import pandas as pd
import seaborn as sns

# Import dataset
texas_data = pd.read_csv('csv_files/texas3.csv')

# Scatterplot
sns.set(style="white", color_codes=True)
sns.jointplot(x=texas_data["y"],
    y=-texas_data["x"],
    kind='scatter',
    s=200,
    color='m',
    edgecolor="skyblue",
    linewidth=2)

plt.show()

# Hex Plot
sns.set(style="white", color_codes=True)
sns.jointplot(x=texas_data["y"],
    y=-texas_data["x"],
    kind='hex',
    marginal_kws=dict(bins=30, fill=True))

plt.show()

# Kernal Density Estimation
sns.set(style="white", color_codes=True)
sns.jointplot(x=texas_data["y"],
    y=-texas_data["x"],
    kind='kde',
    color="skyblue")

plt.show()
'''
            st.code(scatter, language='python')

            # ----- Texas Scatter Plot ----- #      
            texas_data = pd.read_csv('csv_files/texas3.csv')
            home_col1, home_col2, home_col3 = st.columns(3)
            with home_col1:
                st.subheader('Scatterplot')
                scatter_plot(texas_data, 'x', 'y')
            with home_col2:
                st.subheader('Hex Plot')
                hex_plot(texas_data, 'x', 'y')
            with home_col3:
                st.subheader('KDE Plot')
                kde_plot(texas_data, 'x', 'y')
                        
        

        if choose_py == "Lollipop":
            st.markdown('<p class="font">Lollipop Plots Using Seaborn</p>', unsafe_allow_html=True)

            bar_code = '''
            # Import Libraries
import pandas as pd
import seaborn as sns

# Import dataset
iris = pd.read_csv('iris.csv')

# Aggregate by Variety and Fidning range of Dataframe
top_petal_length = iris.groupby(by=['variety']).mean()
my_range = range(0,len(top_petal_length))

# Initialize Plot
fig = plt.figure(figsize=(10,7))

# Creating Stems
plt.stem(top_petal_length['petal.length'])
plt.xticks(my_range, top_petal_length.index)

# Label Plot
plt.xlabel('Variety', fontsize=20)
plt.ylabel('Mean Petal Length',fontsize=20)
plt.title("Average Petal Length By Iris Variety", fontsize=20, x=0.5,y=1.02)   
'''


            st.code(bar_code, language='python')

            

            top_petal_length = iris.groupby(by=['variety']).mean()
            my_range = range(0,len(top_petal_length))

            fig = plt.figure(figsize=(5,5))

            plt.stem(top_petal_length['petal.length'])
            plt.xticks(my_range, top_petal_length.index)

            plt.xlabel('Variety', fontsize=20)
            plt.ylabel('Mean Petal Length',fontsize=20)
            plt.title("Average Petal Length By Iris Variety", fontsize=20, x=0.5,y=1.02)
            st.pyplot()

            st.markdown('<p class="font">Lollipop Difference Plots With Seaborn</p>', unsafe_allow_html=True)

            bar_code1 = '''
            # Import Libraries
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Import dataset
iris = pd.read_csv('iris.csv')

# Aggregate by Variety and Fidning range of Dataframe
mean_iris = iris.groupby(by=['variety']).mean()
my_range = range(0,len(mean_iris))

# Initialize Plot
fig = plt.figure(figsize=(10,7))

# Creating Stems
plt.hlines(y=my_range, xmin=top_petal_length['petal.length'], xmax=top_petal_length['sepal.width'], color='grey', alpha=0.4)
plt.scatter(top_petal_length['petal.length'], my_range, color='skyblue', alpha=1, label='Petal Length')
plt.scatter(top_petal_length['sepal.width'], my_range, color='green', alpha=0.4 , label='Sepal Length')
plt.legend()

# Label Plot
plt.yticks(my_range, top_petal_length.index)
plt.title("Mean Difference of Sepal Length Compared to Petal Length In Iris Dataset", loc='left')
plt.xlabel('Length')
plt.ylabel('Variety')
'''


            st.code(bar_code1, language='python')
            fig1 = plt.figure(figsize=(5,5))
            plt.hlines(y=my_range, xmin=top_petal_length['petal.length'], xmax=top_petal_length['sepal.width'], color='grey', alpha=0.4)
            plt.scatter(top_petal_length['petal.length'], my_range, color='skyblue', alpha=1, label='Petal Length')
            plt.scatter(top_petal_length['sepal.width'], my_range, color='green', alpha=0.4 , label='Sepal Length')
            plt.legend()

            plt.yticks(my_range, top_petal_length.index)
            plt.title("Mean Difference of Sepal Length Compared to Petal Length In Iris Dataset", loc='left')
            plt.xlabel('Length')
            plt.ylabel('Variety')

            st.pyplot()



        if choose_py == "Pie Plot":
            st.markdown('<p class="font">Pie Plots Using Seaborn</p>', unsafe_allow_html=True)

            pie_code = '''
            # Import Libraries
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Import dataset
iris = pd.read_csv('iris.csv')

# Aggregate by Variety 
iris_pie = iris.groupby(by = 'variety').agg(avg_petal_length = ('petal.length', np.mean))

# Creating Lists of Index and Values
iris_mean_petal_length = iris_pie['avg_petal_length'].to_list()
pie_labels = iris_pie.index.to_list()

# Creating Explosion List For Expanding Largest Pie Plot
pie_label_size = len(pie_labels)
explode_list = []
for i in range(0, pie_label_size):
    explode_list.append(0.02)
max_value = max(iris_mean_petal_length)
max_value_index = iris_mean_petal_length.index(max_value)
explode_list[max_value_index] = 0.04

# Creating Plot
colors = sns.color_palette("hls",8)
plt.pie(
    iris_mean_petal_length, 
    labels = pie_labels,
    colors= colors,
    autopct= '%0.0f%%', 
    explode= explode_list,
    shadow = False,
    startangle= 90,
    textprops= {'color': 'Black', 'fontsize':50},
    wedgeprops = {'linewidth':6},
    center = (0.1,0.1),
    rotatelabels= True
)
plt.rcParams["figure.figsize"] = [25,25]
plt.show()
'''


            st.code(pie_code, language='python')

            iris_pie = iris.groupby(by = 'variety').agg(avg_petal_length = ('petal.length', np.mean))
            iris_mean_petal_length = iris_pie['avg_petal_length'].to_list()
            pie_labels = iris_pie.index.to_list()

            colors = sns.color_palette("hls",8)

            pie_label_size = len(pie_labels)

            explode_list = []
            for i in range(0, pie_label_size):
                explode_list.append(0.02)

            max_value = max(iris_mean_petal_length)
            max_value_index = iris_mean_petal_length.index(max_value)
            explode_list[max_value_index] = 0.04

            plt.pie(
                iris_mean_petal_length, 
                labels = pie_labels,
                colors= colors,
                autopct= '%0.0f%%', 
                explode= explode_list,
                shadow = False,
                startangle= 90,
                textprops= {'color': 'Black', 'fontsize':25},
                wedgeprops = {'linewidth':6},
                center = (0.1,0.1),
                rotatelabels= True
            )

            plt.rcParams["figure.figsize"] = [25,25]
            st.pyplot()

        if choose_py == "Tree Map":
            st.markdown('<p class="font">Tree Maps Using Seaborn</p>', unsafe_allow_html=True)
            tree_code = '''
            # Import Libraries
import pandas as pd
import seaborn as sns
import matplotlib
import squarify

# Import dataset
iris = pd.read_csv('iris.csv')

# Aggregate by Variety 
iris_tree = iris.groupby(by = 'variety').agg(avg_petal_length = ('petal.length', np.mean))

# Creating Color Scheme Based On Values
color_map = matplotlib.cm.Blues
min_value = min(iris_tree['avg_petal_length'])
max_value = max(iris_tree['avg_petal_length'])
norm = matplotlib.colors.Normalize(vmin = min_value, vmax= max_value)
colors = [color_map(norm(value)) for value in iris_tree['avg_petal_length']]

squarify.plot(
    sizes=iris_tree['avg_petal_length'],
    label= iris_tree.index,
    alpha = 0.8,
    color = colors,
    pad = True,
    text_kwargs={'fontsize':25, 'fontname':"Times New Roman Bold",'weight':'bold'})
plt.axis('off')
plt.show()
'''


            st.code(tree_code, language='python')


            import matplotlib
            import squarify
            iris_pie = iris.groupby(by = 'variety').agg(avg_petal_length = ('petal.length', np.mean))
            # color palette
            color_map = matplotlib.cm.Blues
            min_value = min(iris_pie['avg_petal_length'])
            max_value = max(iris_pie['avg_petal_length'])
            norm = matplotlib.colors.Normalize(vmin = min_value, vmax= max_value)
            colors = [color_map(norm(value)) for value in iris_pie['avg_petal_length']]

            squarify.plot(sizes=iris_pie['avg_petal_length'], label= iris_pie.index, alpha = 0.8, color = colors, pad = True, text_kwargs={'fontsize':25, 'fontname':"Times New Roman Bold",'weight':'bold'})
            plt.axis('off')
            st.pyplot()






    if choose == "SQL":
        choose_sql = option_menu(None,["Important SQl Functions", "Recursion/Looping in SQL", "Case Statements", 'Aggregate Functions','Rollups','Ranking Functions', 'Analytic Functions', 'Modifying Data', 'Date', 'Strings'],
                            icons=['blank', 'blank', 'blank', 'blank', 'blank','blank', 'blank', 'blank', 'blank', 'blank'],
                            styles={
        "container": {"padding": "5!important", "background-color": "#fafafa"},
        "icon": {"color": "#001219", "font-size": "25px"}, 
        "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
        "nav-link-selected": {"background-color": "#ddbea9"},
        },
        #orientation = 'horizontal'
        )
        
        if choose_sql == "Important SQl Functions":
            sql_df = pd.read_csv('csv_files/sql_df.csv')
            department_df = pd.read_csv('csv_files/sql_department.csv')
            df_col1, df_col2 = st.columns([2,1])
            with df_col1: 
                st.subheader('Employee Table')
                st.dataframe(sql_df)
            with df_col2: 
                st.subheader('Department Table')
                st.dataframe(department_df)
            st.markdown(""" <style> .font {
            font-size:35px ; font-family: 'Cooper Black'; color: #FF9633;} 
            </style> """, unsafe_allow_html=True)
            st.markdown('<p class="font">Finding Duplicate Records In A Table</p>', unsafe_allow_html=True)  
            st.write('Uses Basic Count and Aggregate Function')
        
            code_find_duplicate = '''SELECT *, COUNT(employee_id)
    FROM employees
    GROUP BY 1,2
    WHERE COUNT(employee_id) > 1;'''

            st.code(code_find_duplicate, language='sql')

            st.markdown('<p class="font">Deleting Duplicate Records From A Table</p>', unsafe_allow_html=True)  
            st.write('Uses Common Table Expressions, and ROW_NUMBER() and PARTITION functions')

            code_find_duplicate_delete = '''WITH CTE AS(
    SELECT *, ROW_NUMBER() OVER(PARTITION BY employee_id, employee_name ORDER BY employee_id, employee_name ASC) row_numb
    )
    DELETE 
        FROM employees
        INNER JOIN CTE
        ON employees.employee_id = CTE.employee_id
        WHERE CTE.row_numb > 1;'''

            st.code(code_find_duplicate_delete, language='sql')

            st.markdown('<p class="font">Find the Manager For Each Employee</p>', unsafe_allow_html=True)  
            st.write('Uses Self Joins')

            code_self_join = '''SELECT e.employee_id, e.employee_name, m.employee_id, m.employee_name
    FROM employees e
    LEFT JOIN employees m
    ON e.manager_id = m.employee_id;'''

            st.code(code_self_join, language='sql')

            st.markdown('<p class="font">Find the Second Highest Salary</p>', unsafe_allow_html=True)  
            st.write('Uses MAX() Function and Subqueries')

            code_max = '''SELECT MAX(salary)
    FROM employees
    WHERE MAX(salary) < 
    (
    SELECT MAX(salary)
    FROM employees
    );'''
            st.code(code_max, language='sql')

            st.warning('Using this method is not always accurate. For example, what happens if there is a tie? Using Rank() function is a more optimal solution.')

            st.markdown('<p class="font">Find the Departments With Less Than Three Employees</p>', unsafe_allow_html=True)  
            st.write('Uses COUNT(), JOIN and Aggregate Functions')

            code_max = '''SELECT department_id, department_name
    FROM department
    RIGHT JOIN employees
    ON employees.department_id = department_id 
    GROUP BY department.department_id
    HAVING COUNT(employees.employee_id) > 3
    ;'''
            st.code(code_max, language='sql')

        if choose_sql == "Recursion/Looping in SQL":
            sql_df = pd.read_csv('csv_files/physicians.csv')
            st.subheader('Employee Table')
            st.dataframe(sql_df)
            st.markdown(""" <style> .font {
            font-size:35px ; font-family: 'Cooper Black'; color: #FF9633;} 
            </style> """, unsafe_allow_html=True)
            st.markdown('<p class="font">Finding The Foward Chain</p>', unsafe_allow_html=True)  
            st.write('Assuming physcians can only refer patients to one physican, find which physician refers to 300000003 and the physican who refers to the former, ect.')
        
            code_find_foward = '''With RECURSIVE referrals(Referral_from) AS
    (SELECT refers_to
        FROM physicians
        WHERE employeeID = 300000003
    UNION ALL
    SELECT physicians.refers_to
        FROM referrals
        INNER JOIN physicians
            ON referrals.employeeID = physicians.referral_from
    )
    SELECT referrals.referral_from, CONCAT(physicians.first_name, ' ',physicians.surname) AS physician_name
        FROM referrals
        INNER JOIN physicians
            ON referrals.referral_from = physicians.employeeID
        ORDER BY physicians.employeeID DESC;'''

            st.code(code_find_foward, language='sql')

            st.markdown('<p class="font">Finding The Reverse Chain</p>', unsafe_allow_html=True)
            st.write('Assuming physcians can only refer patients to one physican, Using Recursive, return the downward referral chain for physician 300000002, i.e., find which physician refers to this physican and the physican who refers to the former, ect.')
        
            code_find_reverse = '''With RECURSIVE referrals(EmployeeID) AS
    (SELECT employeeID
        FROM physicians
        WHERE refers_to = 300000002
    UNION ALL
    SELECT physicians.employeeID
        FROM referrals
        INNER JOIN physicians
            ON referrals.employeeID = physicians.refers_to
    )
    SELECT referrals.employeeID, CONCAT(physicians.first_name, ' ',physicians.surname) AS physician_name
        FROM referrals
        INNER JOIN physicians
            ON referrals.employeeID = physicians.employeeID
        ORDER BY referrals.employeeID'''

            st.code(code_find_reverse, language='sql')  
           

        if choose_sql == "Case Statements":
            phys_df = pd.read_csv('csv_files/physicians.csv')
            meds_df = pd.read_csv('csv_files/medications.csv')
            ptns_df = pd.read_csv('csv_files/patients.csv')
            RX_df = pd.read_csv('csv_files/prescription.csv')
            df_col1,df_col2 = st.columns(2)
            df_col3,df_col4 = st.columns(2)

            with df_col1: 
                st.subheader('Physicians Table') 
                st.dataframe(phys_df)
            with df_col2: 
                st.subheader('Medications Table') 
                st.dataframe(meds_df)
            with df_col3: 
                st.subheader('Patient Table') 
                st.dataframe(ptns_df)
            with df_col4: 
                st.subheader('RX Table')
                st.dataframe(RX_df)
            
            
            st.markdown(""" <style> .font {
            font-size:35px ; font-family: 'Cooper Black'; color: #FF9633;} 
            </style> """, unsafe_allow_html=True)
            st.markdown('<p class="font">Categorizing Based On Numerical Varibles</p>', unsafe_allow_html=True)  
            st.subheader(' Return list of all medications brought by patients in our hospital of all time long with the total cost while remembering that patients who were prescribed a medication from a physician that is not their PCP will cost twice as much. In our case, the cost of the medication is per single 1 unit dose.')
        
            code_ptn_pcp = '''SELECT
    MRN, PCP
    FROM patients;
    '''
            st.write('First, lets output patients with their PCP.')
            st.code(code_ptn_pcp, language='sql')

            code_pcp_rx = '''SELECT
    physicianID, patient
    FROM medications
        WHERE (physicianID, patient) IN
    (
    SELECT
        MRN, PCP
        FROM patients
    );
    '''
            st.write('Next, we will group patients who were prescribed medications by their PCP.')
            st.code(code_pcp_rx, language='sql')


            code_answer = '''SELECT
    RX.name, 
    SUM(med.dose * RX.cost * 
        CASE
            WHEN
                (med.physicianID, med.patient) IN
                    SELECT
                        physicianID, patient
                        FROM medications
                            WHERE (physicianID, patient) IN
                                (
                                SELECT
                                    MRN, PCP
                                    FROM patients
                                ) THEN 1
            ELSE 2 --Remember to double price for patients not prescribed by their PCP
        END)::FLOAT AS total_cost
    FROM RX
        LEFT JOIN medications med
            ON RX.code = med.medication
        GROUP BY RX.code,
        ORDER BY RX.code
;
    '''
            st.write('Finally, we use CASE statements to categorize our numerical variables and answer the prompt.')
            st.code(code_answer, language='sql')

        if choose_sql == "Ranking Functions":
            st.markdown(""" <style> .font {
            font-size:35px ; font-family: 'Cooper Black'; color: #FF9633;} 
            </style> """, unsafe_allow_html=True)
            st.markdown('<p class="font">Ranking Functions</p>', unsafe_allow_html=True) 
            st.write('Calculates the ranking of each row within each group. This is useful for selecting the top N records per group')

            st.subheader('ROW_NUMBER()')
            st.warning('Function numbers all rows sequentially.')
            st.subheader('RANK()')
            st.warning('Function ranks all rows but will rank repeated measures (ties) with the same ranking value, i.e, gaps.')
            st.subheader('DENSE_RANK()')
            st.warning('Function ranks all rows but will skip ranks for repeated measures (ties), i.e. no gaps.')


            code_ranking = ''' SELECT value,
    ROW_NUMBER(value) OVER(ORDER BY value ASC) AS 'row_num',
    RANK(value) OVER(ORDER BY value ASC) AS 'row_rank',
    DENSE_RANK(value) OVER(ORDER BY value ASC) AS 'dense_row_rank'
FROM table;'''

            st.code(code_ranking, language='sql')
            ranking = [[3,1,1,1], [4,2,2,2], [5,3,3,3], [5,4,3,3], [7,5,5,4], [7,6,5,4], [8,7,7,5]]
            ranking_df = pd.DataFrame(data=ranking, columns=['value', 'row_num', 'row_rank', 'dense_row_rank'])

            st.dataframe(ranking_df)

        if choose_sql == "Analytic Functions":
            st.markdown(""" <style> .font {
            font-size:35px ; font-family: 'Cooper Black'; color: #FF9633;} 
            </style> """, unsafe_allow_html=True)
            st.markdown('<p class="font">Analytical Functions</p>', unsafe_allow_html=True) 
            st.write('Accesses the values of multiple rows in a window. Can be used to compare multiple rows and calculates the difference between rows.')
            st.error('Offset value cannot be negative')

            st.subheader('LAG()')
            st.warning('Accesses rows before current row.')

            st.subheader('LEAD()')
            st.warning('Accesses rows after current row.')

            code_anal = '''SELECT value,
    LAG(value, 2) OVER(ORDER BY value ASC) AS 'Lag',
    LEAD(value, 2) OVER(ORDER BY value ASC) AS 'Lead'
FROM table;'''
            
            anal = [['3','Null','5'], ['4','Null','5'], ['5','3','7'], ['5','4','7'], ['7','5','8'], ['7','5','Null'], ['8','7','Null']]
            anal_df = pd.DataFrame(data=anal, columns=['value', 'LAG', 'LEAD'])

            st.code(code_anal, language='sql')
            st.dataframe(anal_df)

        if choose_sql == "Modifying Data":
            st.markdown(""" <style> .font {
            font-size:35px ; font-family: 'Cooper Black'; color: #FF9633;} 
            </style> """, unsafe_allow_html=True)
            st.markdown('<p class="font">Modifying Data</p>', unsafe_allow_html=True) 
            st.write('Operations that alter data like inserting, updating and deleting information from a table are collectively known as Data Manipulation Language, DML. On the other hand, Data Definition Language, DDL, is used to define the data structure itself. For example, creating and changing tables are examples of a DDL.')
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.subheader('Members')
                st.write('''
    | memid         | integer      |
    |---------------|--------------|
    | firstname     | varchar(200) |
    | surname       | varchar(200) |
    | address       | varchar(200) |
    | zipcode       | integer      |
    | telephone     | varchar(20)  |
    | recommendedby | integer      |
    | joindate      | timestamp    |
                ''')
            with col2:
                st.subheader('Bookings')
                st.write('''
    | facid     | integer   |
    |-----------|-----------|
    | memid     | integer   |
    | starttime | timestamp |
    | slots     | integer   |                
                ''')
            with col3:
                st.subheader('Facilities')
                st.write('''
| facid              | integer      |
|--------------------|--------------|
| name               | varchar(200) |
| membercost         | float        |
| guestcost          | float        |
| initialoutlay      | float        |
| monthlymaintenance | float        |             
    ''')

            st.markdown('---')
            st.markdown('<p class="font">Adding New Values To A Table</p>', unsafe_allow_html=True) 
            st.write('The website club is adding a new facility - Amazon. We need to add it into the facilities table.')
            st.code('''UPDATE TABLE facilities VALUES (9, 'Amazon', 20, 30, 100000, 800);''', language='sql')

            st.markdown('<p class="font">Inserting New Values To A Table Automatically</p>', unsafe_allow_html=True) 
            st.write('The website club is adding a new facility - Tesla. We need to add it into the facilities table with the next available facility id.')
            st.code('''UPDATE TABLE facilities VALUES ((SELECT MAX(facid) FROM facilities)+1, 'Tesla', 50, 60, 1500000, 1000);''', language='sql')

            st.markdown('<p class="font">Updating Existing Data</p>', unsafe_allow_html=True) 
            st.write('Amazon has increased its member and guest cost to 40 and 50 USD, respectively. Please update this in the facilities table.')
            st.code('''UPDATE TABLE facilities 
    SET membercost = 40,
    guestcost = 50
    WHERE name = 'Amazon';''', language='sql')


            st.markdown('<p class="font">Updating Data Based On The Contents Of Another Row</p>', unsafe_allow_html=True) 
            st.write('Amazon is building a new facility that costs 10 percent less than the facility at Tesla. Please update this in the facilities table.')
            st.code('''UPDATE TABLE facilities 
    SET initialoutlay = 0.90 * (SELECT intialoutlay FROM facilities WHERE name = 'Tesla')
    WHERE name = 'Amazon';''', language='sql')

            st.markdown('<p class="font">Deleting Existing Data</p>', unsafe_allow_html=True) 
            st.write('Delete the facilities table.')
            st.code('''DELETE FROM facilities;''', language='sql')

            st.markdown('<p class="font">Deleting Existing Data Bassed On A Subquery</p>', unsafe_allow_html=True) 
            st.write('Delete members who are not enrolled in any facilities.')
            st.code('''DELETE FROM members 
    WHERE memid NOT IN (SELECT memid FROM bookings);''', language='sql')


        if choose_sql == "Aggregate Functions":
            st.markdown(""" <style> .font {
            font-size:35px ; font-family: 'Cooper Black'; color: #FF9633;} 
            </style> """, unsafe_allow_html=True)
            st.markdown('<p class="font">Aggregating Data</p>', unsafe_allow_html=True)
            st.write('Aggregation functions in SQL allows you to collect a set of values to return a single value. For example, MAX(), SUM(), COUNT() and AVG() are aggregate functions.')


        if choose_sql == "Date":
            st.markdown(""" <style> .font {
            font-size:35px ; font-family: 'Cooper Black'; color: #FF9633;} 
            </style> """, unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.subheader('Members')
                st.write('''
    | memid         | integer      |
    |---------------|--------------|
    | firstname     | varchar(200) |
    | surname       | varchar(200) |
    | address       | varchar(200) |
    | zipcode       | integer      |
    | telephone     | varchar(20)  |
    | recommendedby | integer      |
    | joindate      | timestamp    |
                ''')
            with col2:
                st.subheader('Bookings')
                st.write('''
    | facid     | integer   |
    |-----------|-----------|
    | memid     | integer   |
    | starttime | timestamp |
    | slots     | integer   |                
                ''')
            with col3:
                st.subheader('Facilities')
                st.write('''
| facid              | integer      |
|--------------------|--------------|
| name               | varchar(200) |
| membercost         | float        |
| guestcost          | float        |
| initialoutlay      | float        |
| monthlymaintenance | float        |             
    ''')
            st.markdown('<p class="font">Date </p>', unsafe_allow_html=True)
            





        if choose_sql == "Rollups":
            st.markdown(""" <style> .font {
            font-size:35px ; font-family: 'Cooper Black'; color: #FF9633;} 
            </style> """, unsafe_allow_html=True)
            st.markdown('<p class="font">Rollup Functions</p>', unsafe_allow_html=True)
            st.write('The Rollup function in SQL is an extension of the GROUP BY clause that allows you to include extra rows that represent the subtotals or super-aggregate rows. This function generates multiple grouping sets.')
            st.subheader('Movies')
            st.write('''
| movie_title       | varchar(100) |
|-------------------|--------------|
| description_count | integer      |
| publisheddate     | yyyy-mm-dd   |
| published_time    | hh:mm:ss     |
| view_count        | integer      |
| like_count        | integer      |
| comment_count     | integer      |           
''')
            
            st.markdown('<p class="font">Aggregating Per Month And Year</p>', unsafe_allow_html=True)
            st.write('What is the average monthly view count per day per month per year for this Youtube channel.')
            rollup_code = '''WITH CTE AS(
        SELECT 
            movie_title,
            YEAR(publisheddate) AS years,
            MONTH(publisheddate) AS months,
            DAY(publisheddate) AS days,
            view_count
        FROM movies
        )
        SELECT 
            years, months, days,
            IF(GROUPING(years), 'Every year', years) AS year_grouping,
            IF(GROUPING(months), 'Every month', months) AS month_grouping,
            IF(GROUPING(days), 'Every day', day) AS day_grouping,
            SUM(view_count)
        FROM CTE
            GROUP BY years,months,days WITH ROLLUP
            ORDER BY years,months,days;'''
            st.code(rollup_code, language='sql')
            st.write('''
| years | months   | days      | year_grouping | month_grouping | day_grouping | view_count  |
|-------|----------|-----------|---------------|----------------|--------------|-------------|
| Null  | Null     | Null      | Every year    | Every month    | Every day    | 35199594996 |
| 2015  | Null     | Null      | 2015          | Every month    | Every day    | 4021014751  |
| 2015  | August   | Null      | 2015          | August         | Every day    | 214677925   |
| 2015  | August   | Friday    | 2015          | August         | Friday       | 52716149    |
| 2015  | August   | Monday    | 2015          | August         | Monday       | 8796249     |
| 2015  | August   | Thursday  | 2015          | August         | Thursday     | 15228612    |
| 2015  | August   | Tuesday   | 2015          | August         | Tuesday      | 135902705   |
| 2015  | December | Wednesday | 2015          | December       | Wednesday    | 2034210     |
| 2015  | December | Null      | 2015          | December       | Every day    | 425876935   |        
''')


    if choose == "Machine Learning":
        choose_ML = option_menu(None,["Basic Terminology","Linear Regression", "Logistic Regression", "Decision Tree", "Support Vector Machine (SVM)", "Naive Bayes", "K-Nearest Neightbors (KNN)", "K-Means", "Random Forest", "Dimension Redcution Algorithms", "Gradient Boosting & AdaBoost" ],
                            icons=['journal-richtext','graph-up-arrow', 'graph-up-arrow', 'tree', 'file-bar-graph', 'blank','blank', 'blank', 'blank', 'blank', 'blank'],
                            styles={
        "container": {"padding": "5!important", "background-color": "#fafafa"},
        "icon": {"color": "#001219", "font-size": "25px"}, 
        "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
        "nav-link-selected": {"background-color": "#ddbea9"},
        },
        #orientation = 'horizontal'
        )
        st.markdown(""" <style> .font {
            font-size:35px ; font-family: 'Cooper Black'; color: #FF9633;} 
            </style> """, unsafe_allow_html=True)

        if choose_ML == "Basic Terminology":
            st.markdown('<p class="font">Basic Terminology</p>', unsafe_allow_html=True)
            st.header('Training Sets')
            st.write('Training a model is the process of iteratively improving prediction equations by looping the dataset multiple times. Each iteration, we will update the weight and bias values in the direction indicated by the slop of the gradient. Training is completed when either we reach an acceptable error threshold or when subsequent training iterations fail to reduce cost.')

            st.header('Cost Function')
            st.write('The cost function figures out the best possible values for the slope and y-intercept in a linear regresional analysis. We choose the best slope and intercept points by minimizing the error between the predicted and actual values. In order to minimize the error, we take the difference between the predicted values and the ground truth. By squaring the error difference and summing it over all data points and dividing that by the total number of data points, we will obtain the average squared error over all data points. This cost function is known as the Mean Square Error (MSE) function.')
            st.latex(r'''
MSE = \frac{1}{n} \sum_{i=1}^{n} (Y_i - y_i)^2

''')
            st.latex(r'''
\textrm{n = number of data points}\\
Y_i \textrm{= observed values}\\
y_i \textrm{= predicted values}
''')
            st.header('Gradient Descent')
            st.write('Gradient descent updates the slope and y-intercept values to reduce the cost of the MSE function. For example, we will start with an initial slope and y-intercept value, and we change these values iteratively to reduce the cost. The number of steps we take in the gradient descent algorithm is called the learning rate which decides how fast the algorithm converges to the minima. Of note, taking smaller steps in the descent is accurate however it will be costly. Taking larger steps in the descent will be less costly but at the expense of its accuracy in converging to the minima.')

            st.header('Model Evaluation')
            st.write('If the model is working, then we need to see the cost function decrease after every iteration.')

            st.header('Prediction')
            st.write('Prediction refers to the output of an algorithm after it has been trained on a historical dataset and applied to new data when forcasting the liklihood of a particular outcome.')
            
            st.header('Classification')
            st.write('Classification refers to the output of an algorithm that is categorical.')




            
        if choose_ML == "Linear Regression":
            st.markdown('<p class="font">Linear Regression</p>', unsafe_allow_html=True)
            st.warning("Linear model that assumes a linear relationship between the input variables (x) and the single output variable (y). That is, y can be calculated from a linear combination of the input variables, x.")  
            
            cols1, cols2 = st.columns(2)
            with cols1:
                st.header("Python")

                python_LR= '''
# Import Libraries 
from sklearn import linear_model

# Train and Test Datasets
# Identify Feature and Response Variable/s
##### Note that values must be numerical and numpy arrays #####
X_train = input_variables_values_training_data
X_test = input_variables_values_tests_data
y_train = target_variables_values_training_data

# Create Linear Regression Object
linear = linear_model.LinearRegression()

# Training Model With Training Sets
linear.fit(X_train, y_train)

# Check Score
linear.score(X_train, y_train)

# Equation Coefficient and Intercept
print('Coefficient:', linear.coef_)
print('Intercept:', linear.intercept_)

# Predict Output
predicted = linear.predict(X_test)
'''
                st.code(python_LR, language='python')


            with cols2:
                st.header("R")
                R_LR= '''
# Train and Test Datasets
# Identify Feature and Response Variable/s
##### Note that values must be numerical and numpy arrays #####
X_train <- input_variables_values_training_data
X_test <- input_variables_values_tests_data
y_train <- target_variables_values_training_data
x <- cbind(X_train, y_train)

# Training Model With Training Sets
linear <- lm(y_train ~ ., data = x)

# Check Score
summary(linear)

# Predict Output
predicted = predict(linear, X_test)
'''
                st.code(R_LR, language='R')


        if choose_ML == "Logistic Regression":
            st.markdown('<p class="font">Logistic Regression</p>', unsafe_allow_html=True)
            st.warning('Logistic Regression models the probability of a discrete outcome given an input variable by having the log-odds for the event be a linear combination of one ore more independent variables. The most common logistic regression models a binary outcome. For example, something that can take two such as true/false, yes/no, male/female, ect.')
            cols1, cols2 = st.columns(2)
            with cols1:
                st.header("Python")

                python_LR= '''
# Import Libraries 
from sklearn.linear_model import LogisticRegression

# Train and Test Datasets
# Identify Feature and Response Variable/s
##### Note that values must be numerical and numpy arrays #####
X_train = input_variables_values_training_data
X_test = input_variables_values_tests_data
y_train = target_variables_values_training_data

# Create Logistic Regression Object
log_model = LogisticRegression()

# Training Model With Training Sets
log_model.fit(X_train, y_train)

# Check Score
log_model.score(X_train, y_train)

# Equation Coefficient and Intercept
print('Coefficient:', log_model.coef_)
print('Intercept:', log_model.intercept_)

# Predict Output
predicted = log_model.predict(X_test)
'''
                st.code(python_LR, language='python')


            with cols2:
                st.header("R")
                R_LR= '''
# Train and Test Datasets
# Identify Feature and Response Variable/s
##### Note that values must be numerical and numpy arrays #####
X_train <- input_variables_values_training_data
X_test <- input_variables_values_tests_data
y_train <- target_variables_values_training_data
x <- cbind(X_train, y_train)

# Training Model With Training Sets
log_model <- lm(y_train ~ ., data = x, family = 'binomial')

# Check Score
summary(log_model)

# Predict Output
predicted = predict(log_model, X_test)
'''
                st.code(R_LR, language='R')



        if choose_ML == "Decision Tree":
            st.markdown('<p class="font">Decision Tree</p>', unsafe_allow_html=True)
            st.warning('Decision Trees are a non-parametric supervised learning method for classification and regression that predicts the value of a target variable by learning simple decision rules inferred from the data features. A decision can be seen as a piecewise constant approximation.')
            cols1, cols2 = st.columns(2)
            tree_py = '''
# Import Libraries 
from sklearn import tree

# Train and Test Datasets
# Identify Feature and Response Variable/s
##### Note that values must be numerical and numpy arrays #####
X_train = input_variables_values_training_data
X_test = input_variables_values_tests_data
y_train = target_variables_values_training_data

# Create Tree Object
tree_model = tree.DecisionTreeClassifier(criterion = 'gini') # for the classification type, algrothim is by default 'gini' but entropy (information gain) can be used instead

# Regressional Tree Object
regression_tree_model = tree.DecisionTreeRegressor()

# Training Model With Training Sets
tree_model.fit(X_train, y_train)

# Check Score
tree_model.score(X_train, y_train)

# Predict Output
predicted = tree_model.predict(X_test)      

# Plot Tree
clf = tree_model.fit(X_train, y_train)
tree_model.plot(clf)
'''
            R_tree= '''
# Import packages
library(rpart)

# Train and Test Datasets
# Identify Feature and Response Variable/s
##### Note that values must be numerical and numpy arrays #####
X_train <- input_variables_values_training_data
X_test <- input_variables_values_tests_data
y_train <- target_variables_values_training_data

x <- cbind(X_train, y_train)

# Tree Model
clf <- rpart(y_train ~., data = x, method = "class")

# Check Score
summary(clf)

# Predict Output
predicted = predict(clf, X_test)
'''
            with cols1:
                st.code(tree_py, language='python')
            with cols2:
                st.code(R_tree, language='R')











elif choose == "About Me & Contact":
    col1, col2 = st.columns( [0.8, 0.2])
    with col1:               # To display the header text using css style
        st.markdown(""" <style> .font {
        font-size:35px ; font-family: 'Cooper Black'; color: #FF9633;} 
        </style> """, unsafe_allow_html=True)
        st.markdown('<p class="font">About Me </p>', unsafe_allow_html=True)    
    
    port_pic = st.image('images/PortfolioPic.jpg', use_column_width=False)

    st.write("I graduated from the University of Texas at Austin with a BSc. in Mathematics with emphasis in the Health Sciences. I possess three years of experience in designing, executing and maintaining large datasets for private industry and academic research in the health sciences and health care field. Additionally, I have a background in computational and statistical analysis including Machine Learning. I am a subservient individual with strong communication skills with both technical and non-technical audiences.")    
    st.write("---")
    st.write("email: jnguyen7[at]utexas[dot]edu")

elif choose == 'Find A GPU':

    # ----- Main Title ------ #
    st.title(":computer: Micro Center Graphics Processing Units :computer:")
    st.markdown("##")

    # ----- BACKGROUND ----- # 
    main_gif = st.image('images/main.gif', use_column_width=True)

    # ----- SIDE BAR ----- # 
    st.sidebar.header("Filters")

    # ----- Select Store ----- #
    mystore = store_ids.keys()
    dropdown = st.sidebar.selectbox("Please Select Micro Center Store:", mystore)
    start_execution = st.sidebar.button('Get Data')

    # ----- Initialize Session State ------ #
    if "load_state" not in st.session_state:
        st.session_state.load_state = False

    # ----- Getting Pandas Dataframe and Display Results ------ #
    if start_execution or st.session_state.load_state:
        st.session_state.load_state = True
#        with col2:
        main_gif.empty()
        gif_runner = st.image('images/processing.gif')
        st.session_state['data_frame'] = get_data(dropdown)
        data_frame = st.session_state['data_frame']
        data_frame['product_price'] = data_frame['product_price'].astype(float)
        data_frame['product_inventory_count'] = data_frame['product_inventory_count'].astype(int) 
        gif_runner.empty()   

        # ----- Top KPI ------
        max_high = data_frame['product_price'].max()
        min_low = data_frame['product_price'].min()
        average_price = round(data_frame['product_price'].mean(),2)
        median_price = data_frame['product_price'].median()
        total_inventory = data_frame['product_inventory_count'].sum()
        average_review = round(data_frame['product_star_count'].mean(),2)
        total_review_count = data_frame['product_review_count'].sum()

        # ----- SIDE BAR ----- #
        st.sidebar.subheader('Brand')
        selected_brands = st.sidebar.multiselect(label = "", options = data_frame['brand_name'].unique())
        st.sidebar.subheader('Price')
        min_value = st.sidebar.slider(label="Minimum Price", min_value= round(min_low), max_value=round(max_high))
        if min_value:
            max_value = st.sidebar.slider(label="Maximum Price", min_value= round(min_value), max_value=round(max_high))
        filter_inventory = st.sidebar.radio(label='Filter Inventory', options= ('Include All Items', 'Exclude Sold Out Items'))
        filter_reviews = st.sidebar.radio(label='Filter Reviews', options= ('Include All Items', 'Exclude Items With No Reviews'))    
        filter_data = st.sidebar.button('Filter Products')    

        selected_store = [key for key, value in store_ids.items() if value == store_ids[dropdown]][0]
        st.header(f"Data Descriptions For: {selected_store}")
        left_column, middle_column, right_column = st.columns(3)
        with left_column:
            st.header(":dollar: Price :dollar:")
            st.metric(label="Least Expensive", value = f"${min_low}")
            st.metric(label="Most Expensive", value = f"${max_high}")
            st.metric(label="Average Price", value = f"${average_price}")
            st.metric(label="Median Price", value = f"${median_price}")
        with middle_column:
            st.header(":house: Inventory :house:")
            st.metric(label="Total Products Sold", value = data_frame['product_name'].count())
            st.metric(label="Total Inventory Count", value = total_inventory)
        with right_column:
            st.header(":star: Reviews :star:")
            st.metric(label="Average Reviews", value = average_review)
            st.metric(label="Total Reviews", value = total_review_count)

        st.markdown("---")
        st.header("All Products For Your Store :point_down:")
        st.dataframe(data_frame)

        most_expensive(data_frame)

        least_expensive(data_frame)    

        # ----- Main Dashboard ----- # 
        
        # ----- Initalize Session State 2 ----- # 
        if "load_state2" not in st.session_state:
            st.session_state.load_state2 = False
            data_frame_prime = pd.DataFrame

        if filter_data or st.session_state.load_state2:
            st.session_state.load_state2 = True
            if filter_inventory == 'Include All Items':
                data_frame_prime = data_frame[data_frame['brand_name'].isin(selected_brands)]
                data_frame_prime = data_frame_prime[data_frame_prime['product_price'] > min_value]
                data_frame_prime = data_frame_prime[data_frame_prime['product_price'] < max_value]
                if filter_reviews == 'Include All Items':
                    data_frame_prime = data_frame_prime
                else:
                    data_frame_prime = data_frame_prime[data_frame_prime['product_review_count'] > 0]
            else:
                data_frame_prime = data_frame[data_frame['product_inventory_count']>0]
                data_frame_prime = data_frame_prime[data_frame['brand_name'].isin(selected_brands)]
                data_frame_prime = data_frame_prime[data_frame_prime['product_price'] > min_value]
                data_frame_prime = data_frame_prime[data_frame_prime['product_price'] < max_value]
                if filter_reviews == 'Include All Items':
                    data_frame_prime = data_frame_prime
                else:
                    data_frame_prime = data_frame_prime[data_frame_prime['product_review_count'] > 0] 

            #data_frame_prime = data_frame[data_frame['brand_name'].isin(selected_brands)]
            #data_frame_prime = data_frame_prime[data_frame_prime['product_price'] > min_value]
            #data_frame_prime = data_frame_prime[data_frame_prime['product_price'] < max_value]

            # ----- Filtered KPI ------ #
            max_high_prime = data_frame_prime['product_price'].max()
            min_low_prime = data_frame_prime['product_price'].min()
            average_price_prime = round(data_frame_prime['product_price'].mean(),2)
            median_price_prime = data_frame_prime['product_price'].median()
            total_inventory_prime = data_frame_prime['product_inventory_count'].sum()
            average_review_prime = round(data_frame_prime['product_star_count'].mean(),2)
            total_review_count_prime = data_frame_prime['product_review_count'].sum()

            st.markdown("---")
            st.header(f"Data Descriptions For: {selected_brands} With Prices Between {min_value} And {max_value} USD")
            left_column, middle_column, right_column = st.columns(3)
            with left_column:
                st.header(":dollar: Price :dollar:")
                st.metric(label="Least Expensive", value = f"${min_low_prime}")
                st.metric(label="Most Expensive", value = f"${max_high_prime}")
                st.metric(label="Average Price", value = f"${average_price_prime}")
                st.metric(label="Median Price", value = f"${median_price_prime}")
            with middle_column:
                st.header(":house: Inventory :house:")
                st.metric(label="Total Products Sold", value = data_frame_prime['product_name'].count())
                st.metric(label="Total Inventory Count", value = total_inventory_prime)
            with right_column:
                st.header(":star: Reviews :star:")
                st.metric(label="Average Reviews", value = average_review_prime)
                st.metric(label="Total Reviews", value = total_review_count_prime)

            # ----- Pie Chart ------ #
            # Distribution of Product Inventory
            grouped_df = data_frame_prime.groupby(by=['brand_name']).sum()
            avg_df = data_frame_prime.groupby(by=['brand_name']).mean()

            graph_col1, graph_col2 = st.columns(2)

            with graph_col1:
                st.header(':bank: Distribution of Inventory :bank:')
                pie_chart(grouped_df)

            # ----- Bar Plot ------ #
            # Top Most Expensive Brand
            with graph_col2:
                st.header(':moneybag: Distribution of Average Price :moneybag:')
                bar_chart(avg_df)

            # ----- Grouped Bar Chart ------ #
            # Total Review Count
            st.header(':star2: Distribution of Review Count :star2:')
            grouped_bar_chart(data_frame_prime)


            st.header("Your Products :point_down:")
            st.dataframe(data_frame_prime)
            

    else:
        print("")
















# ----- Hide Streamlit Style ------ #
hide_st_style = """
    <style>
    MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """
st.markdown(hide_st_style, unsafe_allow_html=True)
