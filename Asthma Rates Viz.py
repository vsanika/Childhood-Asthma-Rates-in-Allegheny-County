# -*- coding: utf-8 -*-
"""Team10_FINAL_Project1

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1kpV6BG3R1KSLyBvXmcEJTOlG5GvOvHA9

# Project 1: Childhood Asthma Events in Allegheny County
### Sanika Vaidya and Kai Tiede
### Team 10

# Presentation Link

https://youtu.be/oFR2aLxLjgo

*Before running this notebook, please make sure you have downloaded the data available in the google drive folder. These include:*
*  *2017 income.csv*
*  *dataset_asthma-2017.csv*
*  *Allegheny_County_Census_Tracts_2016 (folder with multiple files)*
*  *kx-pittsburgh-pa-neighborhoods-SHP (folder with multiple files)*
*  *alcogisallegheny-county-municipal-boundaries (folder with multiple files)*

# Introduction

Asthma is a chronic respiratory disease that affects a significant number of children in the United States. According to the Centers for Disease Control and Prevention (CDC), approximately 1 in 12 children, or 6 million, have asthma. If left uncontrolled, asthma can lead to permanent lung damage, hospitalizations, and even death. The burden of asthma is particularly heavy on low-income families and communities of color, who experience higher rates of asthma-related emergency department visits and hospitalizations.

To address this issue, the Allegheny County Health Department's Asthma Task Group was established in 2018 to identify strategies for improving asthma outcomes and reducing healthcare costs. One of the primary goals of the Task Group is to lower the proportion of children who visit emergency rooms for asthma, with a specific focus on those who receive Medicaid-funded services. Medicaid is a health insurance program for low-income families, and children from these families are more likely to have asthma and experience worse outcomes than their peers.

To conduct a comprehensive analysis, this project will utilize two data sets. The first data set comes from data.gov and provides information on Childhood Asthma Healthcare Utilization at the census tract level in Allegheny County. This data is clean and includes information on asthma-related visits to the Emergency Department (ED), hospitalizations, urgent care visits, and asthma controller medication dispensing events.

The second data set comes from the American Community Survey and provides demographic information, including mean income in 2017 dollars, for each census tract in Allegheny County. While this data needed cleaning, it provided valuable insights into the socioeconomic factors that may influence asthma outcomes in the county.

To achieve its goals, the Asthma Task Group recognized the need to better understand healthcare utilization patterns for children with asthma, including emergency department visits and hospitalizations. By analyzing these patterns, the Task Group hopes to identify factors that may contribute to inadequate asthma control and exacerbations. This information can then be used to develop interventions that improve asthma outcomes and reduce healthcare costs.
Furthermore, the findings from this project could serve as a model for other regions experiencing similar healthcare inequities. By sharing its best practices and lessons learned, the Asthma Task Group can influence programs and policy choices that aim to decrease healthcare disparities and enhance access to healthcare services for children with asthma. Ultimately, the project has the potential to improve the lives of children with asthma in Allegheny County and beyond.

Additionally, this project has the potential to inform policy decisions aimed at reducing healthcare disparities in Allegheny County and beyond. By shedding light on the root causes of asthma-related emergency department visits and hospitalizations, this project can help to guide the allocation of resources and funding towards the most effective interventions. Ultimately, this project aims to improve the health outcomes and quality of life for children with asthma in Allegheny County and beyond.

# Approach

*   To start with, we reviewed the raw data files of both datasets to identify any potential ways to combine the files and gain a general understanding of the information contained within them.
*   Next, we utilized Colab to analyze and clean the data, ultimately merging the two files into a single dataset.
*   Afterwards, we conducted exploratory data analysis (EDA) on the merged dataset to gain insights into the data's characteristics and relationships between variables.
*   To further enhance our analysis, we utilized mapping structures for Allegheny County. These use polygons of Allegheny County's census tracts provided by Allegheny County's GIS Open Data website (see sources for link).
*   Finally, we evaluated the resulting output dataset to answer few key questions.

# Legend for the hospitalization data:

### ED_visits: asthma-related visits to the Emergency Department (ED)
### ED_hosp: hospitalizations
### UC_visits: urgent care visits
### Asthma_use: asthma controller medication dispensing events

# Libraries
"""

!pip install geopandas # Uncomment if have not installed geopandas
!pip install shapely # Uncomment if have not installed shapely
import numpy as np
import pandas as pd
import os
import re
import seaborn as sns
import matplotlib.pyplot as plt
import altair as alt
import geopandas as gpd
import shapely
import json
from sklearn.impute import SimpleImputer
from sklearn.cluster import KMeans

"""# Import files (Colab)"""

from google.colab import files

uploaded = files.upload() # Upload '2017 income.csv' and 'dataset_asthma-2017.csv' here

"""# Bring in income data"""

inc = pd.read_csv('2017 income.csv') # Make sure data are in the same folder as notebook in using Jupyter notebooks
inc.head()

"""# Prepare data for use
## Clean income table

Before we can begin our analysis we must ensure our data are usable. We begin with cleaning the income dataset. Our cleaning consisted of the following steps:

1.   Limit observations to estimates only
2.   Transpose the table so that census tract level observations are the rows
3.   Rename columns
4.   Alter census tracts so we can join them with our asthma data
5.   Remove unnecessary columns
6.   Clean numerical data so they are machine readable


"""

inc2 = inc.loc[:,inc.columns.str.endswith('Households!!Estimate')] # Only look at household estimates
inc2.insert(len(inc2.columns), 'Label', inc.loc[:,'Label (Grouping)']) # Add back the labels
inc2.head()

inc2 = inc2.set_index('Label') # Make label is index so they are the column names when transposed
inc3 = inc2.T # Transpose table
inc3 = inc3.reset_index(level=0) # Make sure census tract isn't index
inc3.rename(columns = {'index':'Tract', 'Total':'Count'}, inplace = True) # rename tracts and count
inc3.head()

inc3.dtypes #Check data types

def remove_letters(s):
    '''
    Removes letters from a string
    
    remove_letters('abc123') -> '123' 
    '''
    s = re.sub(r'[^0-9]', '', s)
    return s

inc3['Tract'] = inc3['Tract'].apply(remove_letters) # Remove letters so Tract is just digits
inc3.head()

def make_tract(s):
  '''
  Turn a shortened version of an allegheny county census tract into the longer version
  '''
  if len(s) == 3:
    s = '420030' + s + '00'
  if len(s) == 4:
    s = '42003' + s + '00'
  if len(s) == 6:
    s = '42003' + s
  return s

inc3['Tract'] = inc3['Tract'].apply(make_tract) # Add extra numbers so can join with asthma
inc3.head()

inc3 = inc3.drop(inc3.columns[[14,16,17]], axis = 1) # Remove empty columns
inc3.head()

inc3.rename(columns = {'\xa0\xa0\xa0\xa0Less than $10,000':'Less than 10,000', '\xa0\xa0\xa0\xa0$10,000 to $14,999':'10,000 to 14,999', '\xa0\xa0\xa0\xa0$15,000 to $24,999':'15,000 to 24,999', 
                       '\xa0\xa0\xa0\xa0$25,000 to $34,999':'25,000 to 34,999','\xa0\xa0\xa0\xa0$35,000 to $49,999':'35,000 to 49,000', '\xa0\xa0\xa0\xa0$50,000 to $74,999':'50,000 to 74,999', 
                       '\xa0\xa0\xa0\xa0$75,000 to $99,999':'75,000 to 99,999','\xa0\xa0\xa0\xa0$100,000 to $149,999':'100,000 to 149,0000',
                       '\xa0\xa0\xa0\xa0$150,000 to $199,999':'150,000 to 199,999', '\xa0\xa0\xa0\xa0$200,000 or more':'200,000 or more', 
                       '\xa0\xa0\xa0\xa0Household income in the past 12 months': 'Household income in last 12 months'}, inplace = True) # Rename weird columns

def remove_percent(s):
    '''
    Removes a percent sign from a string
    '''
    s = re.sub('%', '', s)
    return s

lst = ['Less than 10,000', '10,000 to 14,999', '15,000 to 24,999', '25,000 to 34,999', '35,000 to 49,000', '50,000 to 74,999', '75,000 to 99,999', '100,000 to 149,0000', '150,000 to 199,999', 
       '200,000 or more', 'Household income in last 12 months']
for i in lst:
  inc3[i] = inc3[i].apply(remove_percent) # Remove percent sign from all numbers

inc3.head()

lst = ['Count', 'Median income (dollars)', 'Mean income (dollars)']

for i in lst:
    inc3[i] = inc3[i].apply(lambda s: s.replace(',', '')) # Remove commas

inc3.head()

inc3 = inc3.apply(pd.to_numeric, errors='coerce') # Make all data types numeric
inc3.head()

inc3.dtypes # Check data types

"""## Read in asthma dataset"""

asthma = pd.read_csv('dataset_asthma-2017.csv')
asthma.rename(columns = {'Census_tract':'Tract'}, inplace = True) # Rename to match inc3
asthma.head()

asthma.dtypes # Check data types

"""## Join both datasets"""

df = asthma.join(inc3.set_index('Tract'), on = 'Tract') # Left join on tract
df.head()

"""# Add Polygons and Centroids

Since our data are best illustrated in a map format, we are including shape files so that we can make maps in altair. To ready the data for this step we join in the census tracts' shape files and create centroids (longitude and latitude) for each census tract.

## Upload shape files
"""

# Upload ALL files in the Allegheny_County_Census_Tracts_2016 folder
uploaded = files.upload()

"""## Read in shape file"""

gdf = gpd.read_file('Allegheny_County_Census_Tracts_2016.shp')
gdf

"""The shape files include all of the census tracts in Allegheny County. Since we don't have data for every single census tract in our main data, these missing tracts will be blank in our maps.

## Clean shape files

To make joining the shape files to our main data as smooth as possible we will process and clean the data first. This includes:
1.   Cleaning the census tract variable to match our data
2.   Removing unnecessary columns
"""

gdf['Tract'] = gdf['TRACTCE'].apply(make_tract) # Add extra numbers so can join with df
gdf.head()

gdf2 = gdf[['Tract', 'geometry']] # Limit to geometry and Tract
gdf2.head()

"""## Join shapefiles to main data"""

gdf2.dtypes

gdf2['Tract'] = gdf2['Tract'].astype(int)

gdf3 = gdf2.join(df.set_index('Tract'), on = 'Tract') # Left join on tract
gdf3.head()

gdf3.plot() # Check polygons

"""## Create longitude and latitude variables for the centroid of each census tract"""

# Source: https://www.districtdatalabs.com/altair-choropleth-viz
gdf3['x'] = gdf['geometry'].centroid.x # Create longitude value for centroid
gdf3['y'] = gdf['geometry'].centroid.y # Create latitude value for centroid

gdf3.head()

"""## Upload Neighborhood shape files"""

# Upload ALL files in kx-pittsburgh-pa-neighborhoods folder
uploaded = files.upload()

hoods = gpd.read_file('pittsburgh-pa-neighborhoods.shp')
hoods.head()

hoods = hoods[['hood', 'geometry']] # Limit to geometry and Tract
hoods.head()

hoods.plot()

"""## Upload Municipality shape files"""

# Upload ALL files in alcogisallegheny-county-municipal-boundaries folder
uploaded = files.upload()

mun = gpd.read_file('LandRecords_LANDRECORDS_OWNER_Municipalities.shp')
mun.head()

mun = mun[['LABEL', 'geometry']] # Limit to geometry and Tract
mun.head()

mun.plot()

"""# EDA

The initial step of any effective exploratory data analysis (EDA) involves checking for null values within the dataset. If null values are detected, there are several possible approaches to handling them. One option is to remove any rows that contain null values, while another option is to impute the missing values with an appropriate value based on the distribution of the data. The best approach will depend on the specifics of the dataset and the goals of the analysis. Regardless of the method chosen, addressing null values is a crucial step towards ensuring the accuracy and reliability of any subsequent analysis.
"""

gdf3.isna().sum()

gdf3[gdf3.isnull().any(axis=1)]

"""After conducting an initial review, it appears that there are eight rows within our dataset where income data is entirely absent. Given that these rows would not provide any meaningful insights for our analysis, we have decided to remove them from our dataset. By eliminating these irrelevant rows, we can focus our analysis on the most informative and useful data, ultimately enhancing the accuracy and value of our findings."""

gdf3 = gdf3.drop([26, 27, 67, 68, 80, 102, 211, 212])

gdf3[gdf3.isnull().any(axis=1)]

"""It appears that there are a few rows where median and/or mean income data is missing. Although these rows represent a small portion of the dataset, it is still important to address the missing values to ensure the accuracy of our analysis. To determine the best approach for handling these missing values, we will first assess the distribution of these two columns. Based on our findings, we will then decide on the most appropriate method for imputing the missing values. By taking a thoughtful and data-driven approach to addressing missing values, we can ensure that our analysis is both comprehensive and reliable."""

dist_median = alt.Chart(gdf3).mark_bar().encode(
    alt.X('Median income (dollars)', bin=True),
    y='count()'
)

dist_mean = alt.Chart(gdf3).mark_bar().encode(
    alt.X('Mean income (dollars)', bin=True),
    y='count()'
)

dist_median | dist_mean

"""After carefully reviewing the distribution of mean and median income data, we have determined that the distribution is uniform and there are only a small number of missing values. As a result, we have decided to impute the missing values with the mean income value."""

imputer = SimpleImputer(strategy="mean")
features=["Median income (dollars)","Mean income (dollars)"]
gdf3[features] = imputer.fit_transform(gdf3[features])

# Now we see that there are no missing values in our dataset
gdf3.isna().sum()

gdf3.dtypes

gdf3['Tract'] = gdf3['Tract'].astype(str)

# Get an overview/range/distribution of the data
gdf3.describe()

"""To better understand the relationships between variables in our dataset, we have generated a correlation matrix. The matrix provides valuable insights into any potential correlations that may exist between variables, allowing us to make informed decisions during our analysis. Upon reviewing the matrix, we have observed that there is only one moderately strong correlation between ED visits and hospitalization."""

# We will now display a correlation matrix to identify any relationship between the variables

fig, ax = plt.subplots(figsize=(20, 20))

corr = gdf3.corr()
sns.heatmap(corr, annot=True)

sns.heatmap(corr, annot=True, ax=ax,xticklabels=corr.columns, yticklabels=corr.columns)
ax.set_xticklabels(corr.columns, fontsize=8)
ax.set_yticklabels(corr.columns, fontsize=8)
plt.show()

# From this, we can see that there is a somewhat high correlation between ED visits and hopitalizations

"""# Questions

*All of our maps come in pairs of two. The first shows the relationship and includes relevant tooltips. The second layers neighborhoods and municipalities on top of the first map so you can reference where the census tracts are located. When viewing maps, look at the first map to get a sense of the relationship. Then, look at the second map to get a sense of the location.*

## Question 1: Is the occurrence of asthma in children equally distributed across census tracts?

The first question we explore is whether the occurrence of asthma is equally distributed across census tracts. First, we use a histogram to explore this question.
"""

# Source: https://altair-viz.github.io/gallery/simple_histogram.html

alt.Chart(gdf3).mark_bar().encode(
    alt.X('Asthma_use:Q', 
          bin=alt.BinParams(minstep = 25)),
    y='count()',
    tooltip=['count()']
)

"""The histogram shows that distribution of asthma cases in children is highly right skewed. One hundred and thirty-two census tracts have between 0 and 24 cases, one hundred and forty-six have between 25 and 49, eighty-seven have between 50 and 74, twenty-four have between 75 and 99, three have between 100 and 124, one has between 200 and 224, and one has between 225 and 249.

We next use a map of Allegheny county to explore this question.
"""

# Source: https://altair-viz.github.io/gallery/choropleth.html
choro = alt.Chart(gdf3).mark_geoshape(
    stroke='gray'
).encode(
    color=alt.Color('Asthma_use:Q',
                    scale = alt.Scale(scheme = 'bluepurple'),
                    title='Asthma Counts')
).properties(
    width=600,
    height=600
)

municip = alt.Chart(mun).mark_geoshape( # municipality layer
    filled = False,
    stroke='black'
).encode(tooltip=['LABEL:N'])

hood = alt.Chart(hoods).mark_geoshape( # neighborhood layer
    filled = False,
    stroke='black'
).encode(tooltip=['hood:N'])

choro | (choro + municip + hood)

"""We see that census tract 42003409000 (Pine Township) has 240 cases of adolescent asthma and census tract 42003020100 (Central Business District) has 223 cases. These are the main two outliers.

It is possible that these counts are so high due to the census tract having a larger population. We will check this with another choropleth map.
"""

sample = alt.Chart(gdf3).mark_geoshape(
    stroke='gray'
).encode(
    color=alt.Color('Total_members:Q', 
                    type = 'quantitative', 
                    scale = alt.Scale(scheme = 'yelloworangered'), 
                    title='Count'),
    tooltip=['Tract:O','Total_members:Q']
).properties(
    width=600,
    height=600
)

sample | (sample + municip + hood)

"""Census tract 42003409000 (Pine Township) does have a larger estimated population (4,449) compared to other census tracts. We will now create a new variable to represent the asthma case rate by dividing the asthma case estimate by the estimated population for each census tract."""

gdf3['Asthma_Per'] = gdf3['Asthma_use']/gdf3['Total_members']*100 # Asthma event rate

"""We will now explore the asthma rate in allegheny county using a choropleth map."""

asth_rate = alt.Chart(gdf3).mark_geoshape(
    stroke='gray'
).encode(
    color=alt.Color('Asthma_Per:Q', 
                    type = 'quantitative', 
                    scale = alt.Scale(scheme = 'yellowgreenblue'), 
                    title='Asthma Rate'),
    tooltip=['Tract:O', 'Asthma_use:Q', 'Total_members:Q', 'Asthma_Per:Q']
).properties(
    width=600,
    height=600
)

asth_rate | (asth_rate + municip + hood)

"""The three tracts with the largest rate of childhood asthma are census tracts 42003980700 (South Shore) with 50%, 42003980500 (Squirrel Hill South, specifically Schenley Park) 50%, and 42003980100 (part of Highland Park) with 25%. However, these rates are less surprising because the total members are so low (2, 4, and 4 respecitvely) that if even one case of asthma was recorded it would be noticable.

To better visualize the distribution of asthma rates we will remove these census tracts.
"""

gdf4 = gdf3.loc[gdf3['Total_members'] > 4 ]

print(gdf3.shape[0], gdf4.shape[0])

n_asth = alt.Chart(gdf4).mark_geoshape(
    stroke='gray'
).encode(
    color=alt.Color('Asthma_Per:Q', 
                    type = 'quantitative', 
                    scale = alt.Scale(scheme = 'yellowgreenblue'), 
                    title='Asthma Rate'),
    tooltip=['Tract:O', 'Asthma_use:Q', 'Total_members:Q', 'Asthma_Per:Q']
).properties(
    width=600,
    height=600
)

n_asth | (n_asth + municip + hood)

asth_top5 = gdf4.nlargest(5,'Asthma_Per')
asth_top5[['Tract', 'Asthma_use', 'Total_members', 'Asthma_Per']]

top5 = alt.Chart(asth_top5).mark_geoshape(
    stroke='gray',
    fill='blue'
).encode(
    tooltip=['Tract:O', 'Asthma_use:Q', 'Total_members:Q', 'Asthma_Per:Q']
).properties(
    width=800,
    height=800
)

top5 + municip + hood

"""The census tracts with the highest asthma rates are now:
*  42003051100 (Terrace Village) with 18.0%
*  42003120800 (Homewood West) with 15.2%
*  42003050600 (Upper Hill) with 14.6%
*  42003030500 (Crawford-Roberts) with 14.5%
*  42003051000 (Terrace Village) with 13.9%

These census tracts are all within the city limits of Pittsburgh. They also all appear to be in historically underserved communities. Overall, the occurrence of asthma events do not seem to be equally distributed across the county.

## Question 2: Are median income levels and asthma rates related?

We then explore the relationship between median income and asthma rates.

We begin by looking at a choropleth map of median income across Allegheny County.
"""

med_inc = alt.Chart(gdf4).mark_geoshape(
    stroke='gray'
).encode(
    color=alt.Color('Median income (dollars):Q', 
                    type = 'quantitative', 
                    scale = alt.Scale(scheme = 'purples'), 
                    title='Median Income'), 
    tooltip=['Tract', 'Median income (dollars):Q']
).properties(
    width=600,
    height=600
)

med_inc | (med_inc + municip + hood)

inc_top5 = gdf4.nlargest(5,'Median income (dollars)')
inc_top5[['Tract', 'Median income (dollars)', 'Asthma_Per']]

i_top5 = alt.Chart(inc_top5).mark_geoshape(
    stroke='gray',
    fill='purple'
).encode(
    tooltip=['Tract', 'Median income (dollars):Q']
).properties(
    width=800,
    height=800
)

i_top5 + municip + hood

inc_bot5 = gdf4.nsmallest(5,'Median income (dollars)')
inc_bot5[['Tract', 'Median income (dollars)', 'Asthma_Per']]

i_bot5 = alt.Chart(inc_bot5).mark_geoshape(
    stroke='gray',
    fill='purple'
).encode(
    tooltip=['Tract', 'Median income (dollars):Q']
).properties(
    width=800,
    height=800
)

i_bot5 + municip + hood

"""The five census tracts with the highest median incomes are:
*  42003140100 (Squirrel Hill South) with 177,824 dollars 
*  42003422000 (Fox Chapel Borough) with 162,054 dollars 
*  42003409000 (Pine Township) with 148,795 dollars
*  42003563300 (Sewickley Heights Borough/Sewickley Hills Borough) with 148,125 dollars 
*  42003446000 (Edgeworth Borough) with 142,206 dollars

Besides the census tract in Squirrel Hill South, all of these tracts are outside of Pittsburgh's city limits.

The five census tracts with the lowest median incomes are:
*  42003260900 (Northview Heights) with 13,358 dollars 
*  42003982200 (North Oakland) with 14,250 dollars 
*  42003562300 (Hazelwood and Glen Hazel) with 14,432 dollars 
*  42003551900 (McKeesport) with 15,467 dollars 
*  42003051000 (Terrace Village) with 15,739 dollars 

Besides McKeesport, all of these census tracts are within Pittsburgh's city limits.

To explore how asthma rates are related to median incomes we created a scatter plot of the two variables.
"""

alt.Chart(gdf4).mark_circle(
    opacity=0.3
).encode(
    x='Median income (dollars):Q',
    y='Asthma_Per:Q',
    tooltip=['Tract:N', 'Median income (dollars):Q', 'Asthma_Per:Q', 'Total_members:Q']
)

"""Overall, it appears that there is a negative relationship between median income and asthma rates. However, after about 60,000/80,000 dollars this relationship plateaus. It appears that, in general, census tracts with a median income less than $40,000 tend to have slightly higher asthma event rates than other census tracts.

## Question 3: Are there any census tracts which have higher concentration rate of asthma related emergency room visits?

We will now look at emergency room visits.

We begin with calculating an emergency room visit rate and creating a choropleth map with this rate.
"""

gdf4['ED_Per'] = gdf4['ED_visits']/gdf4['Total_members']*100 # Emergency room rate

ed = alt.Chart(gdf4).mark_geoshape(
    stroke='gray'
).encode(
    color=alt.Color('ED_Per:Q', 
                    type = 'quantitative', 
                    scale = alt.Scale(scheme = 'greens'), 
                    title='Emergency Room Rate'),
    tooltip=['Tract','ED_Per:Q']
).properties(
    width=600,
    height=600
)

ed | (ed + municip + hood)

ed_top5 = gdf4.nlargest(5,'ED_Per')
ed_top5[['Tract', 'ED_visits', 'Total_members', 'ED_Per']]

e_top5 = alt.Chart(ed_top5).mark_geoshape(
    stroke='gray',
    fill = 'green'
).properties(
    width=800,
    height=800
)

e_top5 + municip + hood

"""We see that the five census tracts with the highest emergency room rates are:
*  Census tract 42003051100 (Terrace Village) with 6.0%
*  Census tract 42003050100 (Middle Hill) with 3.6%
*  Census tract 42003130200 (Homewood North) with 3.6%
*  Census tract 42003561200 (Wilkinsburg Borough) with 3.5%
*  Census tract 42003050900 (Bedford Dwellings) with 3.3%

We see that all but one of these census tracts (Wilkinsburg Borough) are within the city limits of Pittsburgh.

To better visualize the relationship between emergency room visits and asthma events we use two scatter plots. The first shows the relationship between counts of each variable. The second shows the relationship between the rates of both variables.
"""

alt.Chart(gdf4).mark_circle(
    opacity=0.3
).encode(
    x='Asthma_use:Q',
    y='ED_visits:Q',
    tooltip=['Tract','Asthma_use:Q','ED_visits:Q']
)

alt.Chart(gdf4).mark_circle(
    opacity=0.3
).encode(
    x='Asthma_Per:Q',
    y='ED_Per:Q',
    tooltip=['Tract','Asthma_Per:Q','ED_Per:Q','Count:Q']
)

"""We see that there is a clear positive relationship between these two variables. This relationship is apparent in both the counts graph and the rates graph.

We will next explore the relationship between emergency room rates and the sample size in that census tract.
"""

chart = alt.Chart(gdf4).mark_circle().encode(
    x=alt.X('Total_members:Q', title='Total Members'),
    y=alt.Y('ED_Per:Q', title='Emergency Room Rate'),
    tooltip=['Tract:N', 'ED_Per:Q']
).properties(
    width=500,
    height=300,
    title='Census Tracts with High Concentration of ED Visits'
)

chart

"""We see that as the emergency rate increases, the sample size decreases, showing a negative relationship between the two.

Lastly, we visualize the relationship between asthma event rates and emergeny room rates on a map.
"""

asth_choro = alt.Chart(gdf4).mark_geoshape(
    stroke='gray'
).encode(
    color=alt.Color('Asthma_Per:Q', 
                    type = 'quantitative', 
                    scale = alt.Scale(scheme = 'yellowgreenblue'), 
                    title='Asthma Rate'), 
    tooltip=['Tract','Asthma_Per:Q','ED_Per:Q', 'Count:Q']
).properties(
    width=600,
    height=600
)

ed_points = alt.Chart(gdf4).mark_circle().encode(
    longitude='x:Q',
    latitude='y:Q',
    size=alt.Size('ED_Per:Q', 
                  title='Emergency Room Rate'),
    color=alt.value('red'),
    tooltip=['Tract','Asthma_Per:Q','ED_Per:Q', 'Count:Q']
).properties(
    width=600,
    height=600
)

(asth_choro + ed_points) | (asth_choro + ed_points + municip + hood)

"""We see that the census tracts with larger emergency room rates tend to be centered in and surrounding the city of Pittsburgh. This map helps us visualize the positive relationship we saw in the scatterplots in a geographical sense.

Overall, it is apparent that census tracts that have higer rates of asthma usage events also see higher rates of asthma emergency room visists. These areas that have higher asthma event rates and emergency room rates appear to be clustered in and directly surrounding the city of Pittsburgh.

## Question 4: Are there any clusters of census tracts with similar values?

The scatterplot is displaying the relationship between four variables: ED_visits, Asthma_use, Median income (dollars), and Total_members.

The x-axis shows the number of ED (emergency department) visits per year for each data point.
The y-axis shows the prevalence of asthma among a population in each data point.
The color channel indicates the median income in dollars of the population in each data point.
The size channel indicates the total number of members in the population in each data point.
Therefore, the scatterplot is potentially showing how ED visits and asthma prevalence vary with income and population size.

But this scatterplot does not give us a clear overview of the clusters, therefore we will display clusters using k-means.
"""

scatter = alt.Chart(gdf3).mark_point().encode(
    x='ED_visits',
    y='Asthma_use',
    color='Median income (dollars)',
    size='Total_members',
    tooltip=['Tract', 'ED_visits', 'Asthma_use', 'Median income (dollars)', 'Total_members']
).properties(
    width=500,
    height=300
).interactive()

scatter

"""We will perform k-means clustering on the 'ED_visits', 'Asthma_use', and 'Total_members' features, creating five clusters. Then, we will examine if any of these clusters exhibit similar median income values."""

features = ['ED_visits', 'Asthma_use', 'Total_members']
kmeans = KMeans(n_clusters=5, random_state=0).fit(gdf3[features])
gdf3['cluster'] = kmeans.labels_

color_scale = alt.Scale(domain=list(range(5)), range=['blue', 'green', 'red', 'yellow', 'pink'])

scatter = alt.Chart(gdf3).mark_point().encode(
    x='ED_visits',
    y='Asthma_use',
    color=alt.Color('cluster:N', scale=color_scale),
    size='Total_members',
    tooltip=['Tract', 'ED_visits', 'Asthma_use', 'Median income (dollars)', 'Total_members', 'cluster']
).properties(
    width=500,
    height=300
).interactive()

scatter

"""Upon examining the scatterplot, we observe that clusters 0, 1, 2, and 4 appear to be located in close proximity to each other, albeit with some variations in their values. When we plotted the range of median incomes for these clusters, we found that they exhibit a wide spectrum of income levels. In contrast, cluster 3 appears as an outlier on the scatterplot, and the range of median income for this cluster suggests that it belongs to the higher income group."""

n_clusters = kmeans.n_clusters  # Get the number of clusters from the model
income_range = alt.vconcat()  # Initialize an empty vertical concatenation

for n in range(n_clusters):
    income_range |= alt.Chart(gdf3).transform_filter(
        alt.datum.cluster == n
    ).mark_bar().encode(
        x='cluster:N',
        y='min(Median income (dollars)):Q',
        y2='max(Median income (dollars)):Q',
        color=alt.Color('cluster:N', scale=color_scale)
    ).properties(
        width=50,
        height=300
    )



scatter | income_range

"""# References

## Writing:

Centers for Disease Control and Prevention. (2018, May 10). Asthma in children. Centers for Disease Control and Prevention. Retrieved March 17, 2023, from https://www.cdc.gov/vitalsigns/childhood-asthma/index.html 

Publisher Allegheny County. (2023, January 24). Childhood asthma healthcare utilization. Catalog. Retrieved March 17, 2023, from https://catalog.data.gov/dataset/childhood-asthma-healthcare-utilization

## Data:

Publisher Allegheny County. (2023, January 24). Childhood asthma healthcare utilization. Catalog. Retrieved March 17, 2023, from https://catalog.data.gov/dataset/childhood-asthma-healthcare-utilization

U.S. Census Bureau. (2017). Explore census data. Retrieved March 17, 2023, from https://data.census.gov/table?t=Income%2B%28Households%2C%2BFamilies%2C%2BIndividuals%29&g=0500000US42003%241400000&y=2017&tid=ACSST5Y2017.S1901

Koordinates. (2018, September 18). Pittsburgh, PA neighborhoods. Retrieved March 17, 2023, from https://koordinates.com/layer/97313-pittsburgh-pa-neighborhoods/

WPRDC. (2021, February 11). Allegheny county municipal boundaries. Retrieved March 17, 2023, from https://data.wprdc.org/dataset/allegheny-county-municipal-boundaries
"""