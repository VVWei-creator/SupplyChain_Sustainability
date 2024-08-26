# Supply Chain Sustainability Reporting with Python - https://towardsdatascience.com/supply-chain-sustainability-reporting-with-python-161c1f63f267

# Aims: to report CO2 emission of the Distribution Network using Python and PowerBI

# Definition of CO2 emission by scope: here we are going to use Scope 3 which has its definition below
# Scope 3 : all indirect emissions occuring in the value chain of the company, e.g. Transportation, Waste of Operations, Business Travels

# The formula of CO2 emission using Emission Factors:
# E_CO2 = W_goods * D * F_mode
# 
# E_CO2: emissions in kg of CO2 equivalent (kgCO2eq)
# W_goods: weight of the goods (Ton)
# D: distance from your warehouse to the final distination (km)
# F_mode: emissions factor for each transportation mdoe (kgCO2eq/t.km)
# 
# We have 4 files as testing data in data folder:
# Fact table - shipped order lines (order_lines.csv)
# Dimentional tables - Master Data; Distance By Mode(distance.csv); Adreess book(gps_locations.csv); Business Units (uom_conversions.csv)

# ERP stands for Enterprise Resource Planning

######################################################## TO IMPORT DATA FROM CSV AND JOIN TABLES ############################################
import pandas as pd 
# Import Order Lines Data 
df_lines = pd.read_csv('/Users/veraph/Desktop/Supply Chain Projects/Descriptive Analytics/Supply Chain Sustainability Reporting/Data/order_lines.csv',index_col=0)
print("{:,} order lines to process".format(len(df_lines)))
#print(df_lines.head())

# net weight = weight of product without packaging
# gross weight = weight of product with packaging
# In this project, we consider gross weight

# 1 Unit = 1 product
# 1 Carton = 1 Unites 
# 1 Pallet = 20 Cartons
# In this project, we use total weight per unit instead of carton. Because quantity per order line is low and no full cartons are shipped

df_uom = pd.read_csv('/Users/veraph/Desktop/Supply Chain Projects/Descriptive Analytics/Supply Chain Sustainability Reporting/Data/uom_conversions.csv',index_col=0)
print("{:,} Unit of Measure Conversions".format(len(df_uom)))
# Join two tables
df_join = df_lines.copy()
COLS_JOIN = ['Item Code']
df_join = pd.merge(df_join,df_uom,on=COLS_JOIN,how='left',suffixes=('', '_y'))
df_join.drop(df_join.filter(regex='_y$').columns.tolist(),axis=1,inplace=True)
print("{:,} records".format(len(df_join)))
#print(df_join.head())

# Collect Distance by Mode and GPS location for PBI
# Mode -  Air; Sea; Road; Rail

# Import Location File
df_dist = pd.read_csv('/Users/veraph/Desktop/Supply Chain Projects/Descriptive Analytics/Supply Chain Sustainability Reporting/Data/distances.csv',index_col=0)
# to add Localtion column
df_dist['Location'] = df_dist['Customer Country'].astype(str) + ', ' + df_dist['Customer City'].astype(str)

# Import GPS file
df_gps = pd.read_csv('/Users/veraph/Desktop/Supply Chain Projects/Descriptive Analytics/Supply Chain Sustainability Reporting/Data/gps_locations.csv', index_col = 0)
print("{:,} Locations".format(len(df_gps)))

# Join GPS with Location
df_dist = pd.merge(df_dist, df_gps, on='Location', how='left', suffixes=('', '_y'))
df_dist.drop(df_dist.filter(regex='_y$').columns.tolist(),axis=1, inplace=True)

# Merge with two join tables 
COLS_JOIN = ['Warehouse Code', 'Customer Code']
df_join = pd.merge(df_join, df_dist, on = COLS_JOIN, how='left', suffixes=('', '_y'))
df_join.drop(df_join.filter(regex='_y$').columns.tolist(),axis=1, inplace=True)
print("{:,} records".format(len(df_join)))

######################################### TO CALCULATE CO2 EMISSION USING EMISSION FACTORS ##################################
# Calcualte Weight (kg)
df_join['KG'] = df_join['Units'] * df_join['Conversion Ratio']

GPBY_ORDER = ['Date', 'Month-Year', 
        'Warehouse Code', 'Warehouse Name', 'Warehouse Country', 'Warehouse City',
        'Customer Code', 'Customer Country', 'Customer City','Location', 'GPS 1', 'GPS 2', 
        'Road', 'Rail', 'Sea', 'Air',
        'Order Number']
df_agg = pd.DataFrame(df_join.groupby(GPBY_ORDER)[['Units', 'KG']].sum()) #group by columns in the GPBY_ORDER and get sum of units and kg columns 
df_agg.reset_index(inplace = True)
#print(df_agg.head())

# Calculate CO2 Emission 
dict_co2e = dict(zip(['Air' ,'Sea', 'Road', 'Rail'],[2.1, 0.01, 0.096, 0.028]))
#print(dict_co2e) => {'Air': 2.1, 'Sea': 0.01, 'Road': 0.096, 'Rail': 0.028}

MODES=['Air' ,'Sea', 'Road', 'Rail']

for mode in MODES:
    df_agg['CO2'+mode] = df_agg['KG'].astype(float)/1000 * df_agg[mode].astype(float) * dict_co2e[mode]

df_agg['CO2 Total'] = df_agg[['CO2'+ mode for mode in MODES]].sum(axis=1)

#df_agg.to_csv("Final beforing Mapping.csv")

# Mapping the delivery mode
df_agg['Delivery Mode'] = df_agg[MODES].astype(float).apply(
    lambda t: [mode if t[mode]>0 else '-' for mode in MODES], axis = 1)
#print(df_agg['Delivery Mode'])

dict_map = dict(zip(df_agg['Delivery Mode'].astype(str).unique(), 
  [i.replace("'-',",'').replace(", '-'",'').replace("'",'').replace(' ','') for i in df_agg['Delivery Mode'].astype(str).unique()]))

#print(df_agg['Delivery Mode'].astype(str).unique())
#print(df_agg['Delivery Mode'].astype(str).unique()[1].replace("'-',",'').replace(", '-'",'').replace("'",''))
#print(dict_map)

df_agg['Delivery Mode'] = df_agg['Delivery Mode'].astype(str).map(dict_map)
print(df_agg['Delivery Mode'])
#print(df_agg.head(10))