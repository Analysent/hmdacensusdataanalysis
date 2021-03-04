### import FFIEC Cencus to use with HMDA Data
from csv import DictReader, DictWriter
import decimal
import io
import requests

#as per requirement average household income of less than $50,000 per year in 2019
INCOME_CUTOFF = 50000

#for responses in response
#1. The client is interested in identifying Metropolitan Statistical Areas (MSA’s) that have an average household income of less than $50,000 per year in 2019 
# and joining that list to CFPB’s HMDA dataset



# 2.The MSA data can be obtained using the Census API. 
#DP03_0063E (Estimate!!INCOME AND BENEFITS (IN 2019 INFLATION-ADJUSTED DOLLARS)!!Total households!!Mean household income (dollars))

def get_areas_under_50k():
	mylist = ['DP03_0063E']

	areas_under_50k = []

	for DP in mylist:

		response = requests.get (f'https://api.census.gov/data/2019/acs/acs5/profile?get=NAME,{DP}&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:*')

		if response.status_code != 200:
			raise Exception('Unable to retrieve census data')

		response_json = response.json()

		#print(response_json[0])
		# Looked for DP list in census data and 
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


#3.	For each MSA identified in step 2, retrieve loan-level data from the HMDA Data Browser API
# using the following endpoint: 
# https://ffiec.cfpb.gov/v2/data-browser-api/view/csv?msamds=<MSA_ID>&years=2019, 
# where <MSA_ID> is the MSA identifier.


def aggregate_loan_data(areas_under_50k):
	with open('output.csv', 'w') as csv_file:
		fieldnames = [
		'msamds','total_loans','White','Joint','Race Not Available','Black or African American', 
		'Asian',
		'American Indian or Alaska Native',
		 'Native Hawaiian or Other Pacific Islander',
		 '2 or more minority races',
		 "avg_loan_amount",
		 "avg_loan_to_value_ratio",
		 "avg_interest_rate",
		 "avg_total_loan_costs",
		 "avg_loan_term",
		 "avg_property_value", 
		 "avg_income",
		 "avg_tract_minority_population_percent"
		  ]

		writer = DictWriter (csv_file, fieldnames=fieldnames)
		writer.writeheader()
    	
    
		for area in areas_under_50k:
			msamds = area[2]
			url = f'https://ffiec.cfpb.gov/v2/data-browser-api/view/csv?msamds={msamds}&years=2019'
			#print(url)
			response = requests.get(url)

			if response.status_code != 200:
				raise Exception('Could not retrieve msamds')

			#print(type(response.content))


			"""
			filename = 'temp.csv'
			with open(filename, 'wb') as csv_file:
				csv_file.write(response.content)


			with open(filename) as csv_file:
				reader = DictReader(csv_file)
				for row in reader:
					print(row)
			"""
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

			print("loan amount:",loan_amount)
			print("total loans:", total_loans)
			#if there is no total_loans data, don't perform write a row
			if not total_loans:
				continue
			avg_loan_amount = loan_amount/total_loans
			avg_loan_to_value_ratio = loan_to_value_ratio/total_loans
			avg_interest_rate = interest_rate/total_loans
			avg_total_loan_costs = total_loan_costs/total_loans
			avg_loan_term = loan_term/total_loans
			avg_property_value = property_value/total_loans
			avg_income = income/total_loans
			avg_tract_minority_population_percent = tract_minority_population_percent/total_loans

			row_data = {
				'msamds': msamds,
				'total_loans': total_loans,
				'avg_loan_amount': '{:.2f}'.format(avg_loan_amount),
				'avg_loan_to_value_ratio': '{:.2f}'.format(avg_loan_to_value_ratio),
				'avg_interest_rate': '{:.2f}'.format(avg_interest_rate),
				'avg_total_loan_costs': '{:.2f}'.format(avg_total_loan_costs),
				'avg_loan_term': '{:.2f}'.format(avg_loan_term),
				'avg_property_value': '{:.2f}'.format(avg_property_value),
				'avg_income': '{:.2f}'.format(avg_income),
				'avg_tract_minority_population_percent': '{:.2f}'.format(avg_tract_minority_population_percent),
			}
			row_data.update(loans_by_race)


			"""
		    ['total_loans','White','Joint','Race Not Available','Black or African American', 
		'American Indian or Alaska Native',
		 'Native Hawaiian or Other Pacific Islander',
		 '2 or more minority races',
		 "avg_loan_amount", "avg_loan_to_value_ratio", "avg_interest_rate", "avg_total_loan_costs", "avg_loan_term", "avg_property_value", "avg_income"]
		 	"""


			writer.writerow(row_data)

			print ('total_loans:',total_loans)
			print ('loans_by_race:',loans_by_race)
			print ('loan_amount:', loan_amount)
			print ('avg_loan_amount:', avg_loan_amount)
			print ('avg_loan_to_value_ratio:', avg_loan_to_value_ratio)
			print ('avg_interest_rate:', avg_interest_rate)
			print ('avg_total_loan_costs:', avg_total_loan_costs)
			print ('avg_loan_term:', avg_loan_term)
			print ('avg_property_value:', avg_property_value)
			print ('avg_income:', avg_income)
			print('avg_tract_minority_population_percent:',avg_tract_minority_population_percent)
			"""
			4.	The response from each HMDA API call will be a CSV file with individual level mortgage loan data.  Generate a final CSV with the following aggregations applied to each MSA.  The final CSV file should have a single row for each MSA identified in Step 2.
				a.	A column with the total number of loans for this MSA.
				b.	A column for each value of the ‘derived_race’ field, with a count of loans that fall under that category.
				c.	Columns containing the average of the following fields "loan_amount", "loan_to_value_ratio", "interest_rate", "total_loan_costs", "loan_term", "property_value", "income"
				d.	A column containing the average of "tract_minority_population_percent", processed to avoid unintentional weighting of values due to an uneven distribution of loans across tracts.
			"""

			#for msamds
			#msamds_total += 


def main():
	areas_under_50k = get_areas_under_50k()
	#print(areas_under_50k)

	aggregate_loan_data(areas_under_50k)
	#aggregate_loan_data([['test', '', '41900']])


if __name__ == "__main__":
	main()

#json format and then convert to csv

# Go to the website https://api.census.gov/data/2019/acs/acs5/profile/variables.html
#  Find the income code requirement less than $50,000
# 
# Manually select the attributes from the above source
#For example (DP03_0052E)DP03_0052PE, DP03_0053E
# For all the attributes programatically call the API to download the data
# from the identified attributes
#{
#  "name": "DP03_0052PE",
#  "label": "Percent!!INCOME AND BENEFITS (IN 2019 INFLATION-ADJUSTED DOLLARS)!!Total households!!Less than $10,000",
# "concept": "SELECTED ECONOMIC CHARACTERISTICS",
# "predicateType": "float",
# "group": "DP03",
# "limit": 0,
# "attributes": "DP03_0052PEA,DP03_0052PM,DP03_0052PMA"
#}
# request.get from the following
# https://api.census.gov/data/2019/acs/acs5/profile/examples.html
# append the attribute and replace with Geography code 310
# https://api.census.gov/data/2019/acs/acs5/profile?get=NAME,DP02_0001E&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:*
# DP02_0001E update the name with identified attribute name (e.g.  DP03_0052PE )
# after putting the result in CSV file then will be joining both HMDA and census data


