import pandas as pd
import matplotlib.pyplot as plt
from firebase import firebase as fb
#import firebase_admin
#from firebase_admin import credentials, db
import time
import pygal
#import numpy
import json

#Reading in Dataset
strk_data = pd.read_csv("Bird_strikes.csv", encoding="ISO-8859-1")

#store specific columns in CSV as lists (to allow for data cleaning to be done with list indexxing)
csv_breed_lst = strk_data["WildlifeSpecies"].tolist()
breed_df = sorted(csv_breed_lst)

csv_strike_lst = strk_data["NumberStruckActual"].tolist()
strike_df = sorted(csv_strike_lst)

size_df = strk_data["WildlifeSize"].tolist()

"""
JSON
"""
# Keep only relevant columns
df_filtered = strk_data[['AirportName', 'WildlifeSpecies', 'WildlifeSize']]
# Clean missing values
df_filtered = df_filtered.dropna()

# Count occurrences of each bird species at each airport
bird_strikes_summary = df_filtered.groupby(['AirportName', 'WildlifeSpecies', 'WildlifeSize']).size().reset_index(name='Strikes')

bird_strikes_list = bird_strikes_summary.to_dict(orient='records')
bird_strikes_json = json.dumps(bird_strikes_list, indent=4)

json_file_path = "bird_strikes.json"
with open(json_file_path, "w") as json_file:
    json_file.write(bird_strikes_json)
    
"""
Sorting functions
"""
#sorting algorithm to ensure there aren't multiples of each bird name in breed_lst
def sortbreed(df):
    bl = []
    for x in range(len(df)):
        if bl.count(df[x]) == 0 and df[x] != "Hawks, eagles, vultures" and df[x] != "Pigeons, doves":
            bl.append(df[x])
    return bl
breed_lst = sortbreed(breed_df)

#writing a csv file to show the amount of strikes for each species
with open("temp_bird_data.csv", "w+") as f:
    f.write("Breed,Strikes\n")
    #cycles thru each breed alphabetically to add them to the csv properly
    total_strike_lst = []
    for x in range(len(breed_lst)):
        b = breed_lst[x]
        c = 0
        #totals the amount of each breed involved in a crash for each index pos
        for y in range(len(csv_strike_lst)):
            if csv_breed_lst[y] == b:
                c += csv_strike_lst[y]

        f.write(f"{breed_lst[x]}, {c}\n ")
        
    

new_strk_data = pd.read_csv("temp_bird_data.csv", encoding="ISO-8859-1")
new_strike_df = new_strk_data["Strikes"].tolist()

#runs the lists to find the top n most common breeds
#n = input number, b = list of breeds, s = no. strikes
def topnbirdsfunct(n, b, s):    
    temp_s = s.copy()
    l, bl = [], []

    x = 0
    while x < int(n):
        m = max(temp_s)
        ip = b[s.index(m)]
        hit_list = ["Unknown bird - small", "Unknown bird - medium", "Unknown bird - large"]
        if ip not in hit_list:
            l.append(ip)
            bl.append(m)
            x += 1
        temp_s.remove(m)
        
    if len(l) != len(bl):
        min_len = min(len(l), len(bl))
        l, bl = l[:min_len], bl[:min_len]
    return l, bl

#Makes list of states without duplicate values
state_df = strk_data["OriginState"].tolist()
def sortstate(df):
    sl = []
    
    for x in range(len(df)):
        if sl.count(df[x]) == 0 and not pd.isna(df[x]):
            sl.append(df[x])
    return sl

#makes a list of the total strikes in each state for use in graphs
def strikestate(s_state, us_state, strike):
    total_strikestate_lst = []
    for x in range(len(s_state)):
        b = s_state[x]
        c = 0
        #totals the amount of each breed involved in a crash for each index pos
        for y in range(len(strike)):
            if us_state[y] == b:
                c += strike[y]
        total_strikestate_lst.append(int(c))
    return total_strikestate_lst


#function to determine the top n costliest strikes
cost_lst = strk_data["Cost"].tolist()
def cost_strike(lst):
    filtered_lst = []
    
    #cleaning numerical values as ","s must be removed for the numbers to be interpreted properly as integers
    for x in range(len(lst)):
        el = str(lst[x])
        if el != "0":
            el = el.replace(",", "")
            filtered_lst.append(int(el))
            
    sorted_lst = sorted(filtered_lst, reverse=True)
    return sorted_lst

def topn_cost(s_lst, us_lst, n):
    temp_s_lst = []
    #loop to remove duplicate values in the sorted list
    for x in range(len(s_lst)):
        if s_lst[x] not in temp_s_lst:
            temp_s_lst.append(s_lst[x])
        
    s_lst = temp_s_lst     
        
    for x in range(len(us_lst)):
        string = us_lst[x]
        us_lst[x] = string.replace(",", "")
    
    new_cost_lst = s_lst[:n]
    #getting the index position of the costs in new_cost_lst
    id_pos = []
    for x in range(len(new_cost_lst)):
        id_pos.append(us_lst.index(str(new_cost_lst[x])))

    return new_cost_lst, id_pos
"""
pie chart & bar chart functions: (by including this as a function, it mitigates the need to assign every
element of a graph every time it is wanted.
Rather, it can be called with one line, where the data is passed into it as lists)
"""
def pie(lab, data, title):
    
    print(type(lab[0]))
    plt.pie(data, labels=lab)
    # Add title
    plt.title(title)

    #Adjust layout and display the plot
    plt.tight_layout()
    
    plt.savefig('1.png')
    plt.close()
    
def bar(x, y, xlab, ylab, title):
    
    # creating the chart object
    bar_chart = pygal.Bar()
     
    # naming the title
    bar_chart.title = f'{title}'       
     
    for i in range(len(x)):
        bar_chart.add(x[i], y[i])
     
    bar_chart.render_to_file(f"{title}.svg")

#Strikes per state bar chart isn't altered dynamically by firebase and thus can just be generated once here>>
sortstate = sortstate(state_df)
strikes_perstate = strikestate(sortstate, state_df, csv_strike_lst)
bar(sortstate, strikes_perstate, "State Names", "Total Strikes Per State", "Number of Strikes in Each State")

#Connecting to firebase
fb_cnnctn = fb.FirebaseApplication("https://birds-2b89b-default-rtdb.europe-west1.firebasedatabase.app/", None)
fb_data = fb_cnnctn.get("/GraphingInfo/", None)
   
d = True
while d == True:
    c = True
    bird_nval_lst = []  
    cost_nval_lst = []
    
    new_bird_nval_lst = []  
    new_cost_nval_lst = []

    #Retrieving 'n' value from 'birds' node
    if 'birds' in fb_data:
        for key, value in fb_data['birds'].items():
            bird_nval_lst.append(int(value['n']))

    #Retrieving 'n' value from 'costs' node
    if 'costs' in fb_data:
        for key, value in fb_data['costs'].items():
            cost_nval_lst.append(int(value['n']))

    while c == True:
        #Making separate new readings from the same nodes after a 0.001ms delay to check for new values in the database
        fb_data = fb_cnnctn.get("/GraphingInfo/", None)
    
        new_bird_nval_lst = []  #Reset the lists
        new_cost_nval_lst = []  
             
        time.sleep(0.001)

        #Retrieving 'n' value from 'birds' node
        if 'birds' in fb_data:
            for key, value in fb_data['birds'].items():
                new_bird_nval_lst.append(int(value['n']))

        #Retrieving 'n' value from 'costs' node
        if 'costs' in fb_data:
            for key, value in fb_data['costs'].items():
                new_cost_nval_lst.append(int(value['n']))
        

        print("Bird:", new_bird_nval_lst)
        print("Cost:", new_cost_nval_lst)

        #Check if the length of new data is greater than the old data 
        if len(new_bird_nval_lst) > len(bird_nval_lst):
            # Use the most recent number of birds from new_bird_nval_lst
            if len(new_bird_nval_lst) <= 1:
                topnbirds = topnbirdsfunct(new_bird_nval_lst[0], breed_lst, new_strike_df)

                topnbreeds_lst, topnstrikes_lst = topnbirds

                # Flatten the list of topnbreeds_lst
                temp_lst = []
                for t in topnbreeds_lst:
                    if isinstance(t, (list, tuple)):  # Only flatten nested lists
                        temp_lst.extend(t)
                    elif isinstance(t, str):  
                        temp_lst.append(t)
                topnbreeds_lst = temp_lst

                print(topnbreeds_lst)
                pie(topnbreeds_lst, topnstrikes_lst, f'The top {new_bird_nval_lst[0]} most likely birds to be involved in a strike')
                c = False
                
            elif len(new_bird_nval_lst) > 1:
                topnbirds = topnbirdsfunct(new_bird_nval_lst[-1], breed_lst, new_strike_df)

                topnbreeds_lst, topnstrikes_lst = topnbirds

                # Flatten the list of topnbreeds_lst
                temp_lst = []
                for t in topnbreeds_lst:
                    if isinstance(t, (list, tuple)):  # Only flatten nested lists
                        temp_lst.extend(t)
                    elif isinstance(t, str):  
                        temp_lst.append(t)
                topnbreeds_lst = temp_lst

                print(topnbreeds_lst)
                pie(topnbreeds_lst, topnstrikes_lst, f'The top {new_bird_nval_lst[-1]} most likely birds to be involved in a strike')
                c = False
            
    
        if len(new_cost_nval_lst) > len(cost_nval_lst):
            if len(new_cost_nval_lst) <= 1:
                # Assuming some function to handle the costs data (implement logic here)
                #n = int(input("Enter a number (n):\n"))
                
                sorted_cost_lst = cost_strike(cost_lst)
                #topn_cost_lst is a tuple, contains the list and the index positions theyre located in on the unsorted list
                topn_cost_tuple = topn_cost(sorted_cost_lst, cost_lst, new_cost_nval_lst[0])
                
                #top n costs
                topn_cost_lst = topn_cost_tuple[0]
                #index positions of each cost
                topn_id_pos = topn_cost_tuple[1]
                # (You can add more code here to handle costs data)
                df_airlines = strk_data["Operator"].tolist()
                
                topn_costs_airlines = []
                for x in range(len(topn_id_pos)):
                    topn_costs_airlines.append(df_airlines[topn_id_pos[x]])
                print(topn_costs_airlines)
                #bar(sortstate, strikes_perstate, "State Names", "Total Strikes Per State", "Number of Strikes in Each State")
                bar(topn_costs_airlines, topn_cost_lst, "Airlines", "Cost per Strike", f"Top {new_cost_nval_lst[0]} Most Expensive Strikes")
                c = False
            elif len(new_bird_nval_lst) > 1:
                sorted_cost_lst = cost_strike(cost_lst)
                #topn_cost_lst is a tuple, contains the list and the index positions theyre located in on the unsorted list
                topn_cost_tuple = topn_cost(sorted_cost_lst, cost_lst, new_cost_nval_lst[-1])
                
                #top n costs
                topn_cost_lst = topn_cost_tuple[0]
                #index positions of each cost
                topn_id_pos = topn_cost_tuple[1]
                # (You can add more code here to handle costs data)
                df_airlines = strk_data["Operator"].tolist()
                
                topn_costs_airlines = []
                for x in range(len(topn_id_pos)):
                    topn_costs_airlines.append(df_airlines[topn_id_pos[x]])
                print(topn_costs_airlines)
                #bar(sortstate, strikes_perstate, "State Names", "Total Strikes Per State", "Number of Strikes in Each State")
                bar(topn_costs_airlines, topn_cost_lst, "Airlines", f"Top {new_cost_nval_lst[-1]} Most Expensive Strikes", "Expensive_Strikes" )
                c = False
               
    




     

    


