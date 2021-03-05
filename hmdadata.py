### import FFIEC Cencus to use with HMDA Data
from csv import DictReader, writer
import decimal
import io
import requests
import numpy as np  
import matplotlib.pyplot as plt  


#as per requirement average household income of less than $50,000 per year in 2019
INCOME_CUTOFF = 50000
# grouping different race groups extracted from hmdata data
RACIAL_GROUPS = [
    'American Indian or Alaska Native',
    'Asian',
    'Black or African American', 
    'Native Hawaiian or Other Pacific Islander',
    'White',
    'Joint',
    '2 or more minority races',
    'Race Not Available'
]


#The client is interested in identifying Metropolitan Statistical Areas (MSA’s) that have an average household income of less than $50,000 per year in 2019 
# and joining that list to CFPB’s HMDA dataset
# The MSA data can be obtained using the Census API. After analysis, it seems the code
#DP03_0063E (Estimate!!INCOME AND BENEFITS (IN 2019 INFLATION-ADJUSTED DOLLARS)!!Total households!!Mean household income (dollars))
# append the attribute and replace with Geography code 310 and correspoding api.census.gov link

#function to get areas where average house income less than 50k as per the DP list
def get_areas_under_50k():
    mylist = ['DP03_0063E']

    areas_under_50k = []

    for DP in mylist:

        response = requests.get (f'https://api.census.gov/data/2019/acs/acs5/profile?get=NAME,{DP}&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:*')

        if response.status_code != 200:
            raise Exception('Unable to retrieve census data')

        response_json = response.json()
        # Start at 1 to skip header line
        for i in range(1, len(response_json)):
            area = response_json[i]
            #print(area)
            income = int(area[1])
            if income < INCOME_CUTOFF:
                areas_under_50k.append(area)
    return areas_under_50k

    #print(DP,response.text)
    #print (response.status_code)


#3. For each MSA identified in step 2, retrieve loan-level data from the HMDA Data Browser API
# using the following endpoint: 
# https://ffiec.cfpb.gov/v2/data-browser-api/view/csv?msamds=<MSA_ID>&years=2019, 
# where <MSA_ID> is the MSA identifier.

#function to aggregate the loan data per msamdds derived from above steps. Create response 
# from requests using cfpb ffiec data source
# created dictionary with required columns
# address conversion error based on data values/types
def aggregate_loan_data(areas_under_50k):
    
    # array to be used for csv writer and also visualization
    loan_data=[]

    for area in areas_under_50k:
        msamds = area[2]
        url = f'https://ffiec.cfpb.gov/v2/data-browser-api/view/csv?msamds={msamds}&years=2019'
        #print(url)
        response = requests.get(url)

        if response.status_code != 200:
            raise Exception('Could not retrieve msamds')

        string_content = response.content.decode("utf-8") 
        csv_file = io.StringIO(string_content)

        reader = DictReader(csv_file)
        total_loans = 0
        loans_by_race = {}
        loan_amount = decimal.Decimal("0")
        loan_to_value_ratio = decimal.Decimal("0")
        loan_to_value_ratio = 0
        interest_rate=decimal.Decimal("0")
        total_loan_costs=decimal.Decimal("0")
        loan_term=0
        property_value=decimal.Decimal("0")
        income=decimal.Decimal("0")
        tract_minority_population_percent = decimal.Decimal("0")

        for row in reader:
            total_loans = total_loans + 1
            derived_race = row.get("derived_race")
            #print('row:', row)
            #print('derived_race:',derived_race)

            if derived_race not in loans_by_race:
                loans_by_race[derived_race] = 0

            loans_by_race[derived_race] += 1


            try:
                loan_amount_raw = row.get("loan_amount")
                #print('loan_amount_raw', loan_amount_raw)
                loan_amount += decimal.Decimal(loan_amount_raw)

            except decimal.InvalidOperation:
                pass
            #loan_amount += decimal.Decimal(row.get("loan_amount"))
            #TypeError: conversion from NoneType to Decimal is not supported
            try:
                loan_to_value_ratio_raw = row.get("loan_to_value_ratio")
                #print('loan_to_value_ratio_raw', loan_to_value_ratio_raw)
                loan_to_value_ratio += decimal.Decimal(loan_to_value_ratio_raw)

            except decimal.InvalidOperation:
                pass
            try:
                interest_rate_raw = row.get("interest_rate")
                #print('interest_rate_raw', interest_rate_raw)
                interest_rate += decimal.Decimal(interest_rate_raw)
            except decimal.InvalidOperation:
                pass
            try:
                total_loan_costs_raw = row.get("total_loan_costs")
                #print('total_loan_costs_raw', total_loan_costs_raw)
                total_loan_costs += decimal.Decimal(total_loan_costs_raw)
            except decimal.InvalidOperation:
                pass    
            try:

                loan_term += int(row.get("loan_term"))
            except ValueError:
                pass
            try:
                property_value_raw = row.get("property_value")
                #print('property_value_raw', property_value_raw)
                property_value += decimal.Decimal(property_value_raw)
            except decimal.InvalidOperation:
                # What to do here?
                pass    
            try:
                income_raw = row.get("income")
                #print('income_raw', income_raw)
                income += decimal.Decimal(income_raw)
            except decimal.InvalidOperation:
                # What to do here?
                pass    
            try:
                tract_minority_population_percent_raw = row.get("tract_minority_population_percent")
                #print('tract_minority_population_percent_raw', tract_minority_population_percent_raw)
                tract_minority_population_percent += decimal.Decimal(tract_minority_population_percent_raw)
            except decimal.InvalidOperation:
                # What to do here?
                pass    

        #if there is no total_loans data, don't perform write a row
        if not total_loans:
            continue
        # average calculations of the data fields as per the requirement 4
        avg_loan_amount = loan_amount/total_loans
        avg_loan_to_value_ratio = loan_to_value_ratio/total_loans
        avg_interest_rate = interest_rate/total_loans
        avg_total_loan_costs = total_loan_costs/total_loans
        avg_loan_term = loan_term/total_loans
        avg_property_value = property_value/total_loans
        avg_income = income/total_loans
        avg_tract_minority_population_percent = tract_minority_population_percent/total_loans

        # creating arrays with all the loan data.

        # First, the MSA and total loans
        row_data = [
            msamds,
            total_loans,
        ]

        # Second, the loans per racial group
        for key in RACIAL_GROUPS:
            row_data.append(loans_by_race.get(key, 0))

        # Third, the calculated values
        row_data.extend([
            avg_loan_amount,
            avg_loan_to_value_ratio,
            avg_interest_rate,
            avg_total_loan_costs,
            avg_loan_term,
            avg_property_value,
            avg_income,
            avg_tract_minority_population_percent
        ])

        loan_data.append(row_data)

    return loan_data

# function to write the csv file with specific fieldnames
def write_csv(data):
    with open('output.csv', 'w') as csv_file:

        racial_groups = [
            'American Indian or Alaska Native',
            'Asian',
            'Black or African American', 
            'Native Hawaiian or Other Pacific Islander',
            'White',
            'Joint',
            '2 or more minority races',
            'Race Not Available'
        ]
        
        fieldnames = [
        'msamds',
        'total_loans'
        ]
        fieldnames.extend(RACIAL_GROUPS)
        fieldnames.extend([
         "avg_loan_amount",
         "avg_loan_to_value_ratio",
         "avg_interest_rate",
         "avg_total_loan_costs",
         "avg_loan_term",
         "avg_property_value", 
         "avg_income",
         "avg_tract_minority_population_percent"
          ])

        loan_writer = writer(csv_file)
        loan_writer.writerow(fieldnames)

        for row_data in data:
            loan_writer.writerow(row_data)


#Function to use numpy to visualize number of loans by race
def visualize_loans_by_race(loan_data):
    loan_np = np.array(loan_data)
    # extracting the columns that contains loan by race information as array contains all data
    loans_by_race = loan_np[:, 2:(2+len(RACIAL_GROUPS))]
    # summing the totals in columns
    # reference: https://stackoverflow.com/questions/13567345/how-to-calculate-the-sum-of-all-columns-of-a-2d-numpy-array-efficiently
    sum_loans_by_race = loans_by_race.sum(axis=0)
      
    # plotting 
    plt.title("Bar graph")  
    plt.xlabel("Racial Groups")  
    plt.ylabel("Number of loans")  
    plt.bar(RACIAL_GROUPS, sum_loans_by_race)
    plt.xticks(rotation=-90)
    plt.show()
    

#main method to call the above functions
def main():
    
    areas_under_50k = get_areas_under_50k()
    loan_data = aggregate_loan_data(areas_under_50k)
    write_csv(loan_data)
    visualize_loans_by_race(loan_data)


if __name__ == "__main__":
    main()




