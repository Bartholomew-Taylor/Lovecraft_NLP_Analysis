import pandas as pd
import numpy as np
from env import api_key
import requests
import json
import os
from bs4 import BeautifulSoup

def get_links_to_bills():
    """
    This function gets the links to the full text of bills from the gov info api.
    """
    filename = "links_to_summary.csv"
    
    #Checks if file is catched
    if os.path.isfile(filename):
        
        links = pd.read_csv(filename)
        
        list_of_links = list(links['0'])

        return list_of_links

    else:
    
        #Builds the url using your api key.
        url = f"https://api.govinfo.gov/collections/BILLS/2001-01-01T01%3A01%3A01Z/2023-01-01T01%3A01%3A01Z?pageSize=1000&offsetMark=%2A{api_key}"

        #Gets each page
        response = requests.get(url)

        #Converts from json
        data = response.json()

        #Makes list to collect links
        list_of_links = []

        #Loop to collect links from first page
        for item in data['packages']:
            list_of_links.append(item['packageLink'])

        #Sets the variable to break the while loop
        next_page = data['nextPage']

        #While loop to collect the remaining links
        while next_page != None: #first json coming in, next_page url coming in.

            nextPage_link = next_page + api_key #Creates new url 
            response = requests.get(nextPage_link) #Gets new info
            data = response.json() #Makes new info readable
            next_page = data['nextPage'] #nextpage link assigned

            for item in data['packages']:
                list_of_links.append(item['packageLink'])

        #Saving links to csv
        pd.Series(links).to_csv("links_to_summary.csv", index=False)


        return list_of_links
    
def acquire_bills(links, filename="data_bills.csv"):
    """
    This function gets a bill, it's sponsor and their party affiliation.
    """
    
    #Checks if file is catched
    if os.path.isfile(filename):
        
        return pd.read_csv(filename)
        
    else:
        # Parameters for the API request
        params = {
            'offset': 0,
            'pageSize': 1000,
            'api_key': f'{api_key[9:]}'}

        #List to hold data
        master_list = []
        n = 0
        i = 0
        #Loop for getting full dataset
        for link in links:
            n += 1
            #To handle bills without sponsors
            try:
                #Get the summary data
                response = requests.get(link, params=params)
                data = response.json()

                #Primary sponsor
                member = data['members'][0]['memberName']
                #Party affiliation
                party = data['members'][0]['party']

                #Getting text of bill
                link_to_bill = data['download']['txtLink']
                response = requests.get(link_to_bill, params=params)

                # Make a soup variable holding the response content
                soup = BeautifulSoup(response.text, 'html.parser')
                text_of_bill = soup.find('body')

                #Create a dictionary of the items and append to a list
                temp_dictionary = {"sponsor":member,
                                   "party":party,
                                   "bill_text":str(text_of_bill)}
                
                master_list.append(temp_dictionary)

                i += 1
                if i % 100 == 0:
                    print(f'Attempted: {n} --- Acquired: {i}')
            except KeyError:
                pass
        
        return_list = pd.DataFrame(master_list)
        #Saving links to csv
        return_list.to_csv(filename, index=False)        
        
        return return_list

        