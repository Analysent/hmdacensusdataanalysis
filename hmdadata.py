### import FFIEC Cencus to use with HMDA Data
from csv import DictReader
import io
import requests


INCOME_CUTOFF = 50000

#for responses in response
#1. The client is interested in identifying Metropolitan Statistical Areas (MSA’s) that have an average household income of less than $50,000 per year in 2019 and joining that list to CFPB’s HMDA dataset
#DP03_0052PEA,
#DP03_0052PM,
#DP03_0052PMA
#DP03_0052EA,
#DP03_0052M,
#DP03_0052MA
#DP03_0052PEA,
#DP03_0052PM,
#DP03_0052PMA
# DP03_0052PEA,DP03_0052PM,DP03_0052PMA
#DP03_0052EA,DP03_0052M,DP03_0052MA
#DP03_0052PEA,DP03_0052PM,DP03_0052PMA
# DP03_0053EA,DP03_0053M,DP03_0053MA
# DP03_0053PEA,DP03_0053PM,DP03_0053PMA
#DP03_0054EA,DP03_0054M,DP03_0054MA


# 2.The MSA data can be obtained using the Census API. 
# mylist = ['DP03_0052PEA','DP03_0052PM','DP03_0052PMA','DP03_0052EA','DP03_0052M','DP03_0052MA','DP03_0052PEA','DP03_0052PM','DP03_0052PMA','DP03_0052PEA','DP03_0052PM', 'DP03_0052EA','DP03_0052M','DP03_0052MA', 
# 'DP03_0052PEA','DP03_0052PM','DP03_0052PMA', 'DP03_0053EA','DP03_0053M','DP03_0053MA', 'DP03_0053PEA','DP03_0053PM','DP03_0053PMA',
# 'DP03_0054EA','DP03_0054M','DP03_0054MA']

mylist = ['DP03_0063E']

areas_under_50k = []

for DP in mylist:

	response = requests.get (f'https://api.census.gov/data/2019/acs/acs5/profile?get=NAME,{DP}&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:*')

	if response.status_code != 200:
		raise Exception('Unable to retrieve census data')

	response_json = response.json()

	print(response_json[0])
	# Finds very few areas under 50,000 which seems odd -- would expect more. Is this the right DP?
	# Start at 1 to skip header line
	for i in range(1, len(response_json)):
		area = response_json[i]
		#print(area)
		# ["Big Stone Gap, VA Micro Area","57868","13720"]
		income = int(area[1])
		if income < INCOME_CUTOFF:
			areas_under_50k.append(area)

			break
	#print(DP,response.text)
	#print (response.status_code)

print(areas_under_50k)


#3.	For each MSA identified in step 2, retrieve loan-level data from the HMDA Data Browser API
# using the following endpoint: 
# https://ffiec.cfpb.gov/v2/data-browser-api/view/csv?msamds=<MSA_ID>&years=2019, 
# where <MSA_ID> is the MSA identifier.

#  curl "https://ffiec.cfpb.gov/v2/data-browser-api/view/aggregations?states=MD&years=2018&actions_taken=5,6&races=White,Asian,Joint"

for area in areas_under_50k:
	msamds = area[2]
	url = f'https://ffiec.cfpb.gov/v2/data-browser-api/view/csv?msamds={msamds}&years=2019'
	print(url)
	response = requests.get(url)

	if response.status_code != 200:
		raise Exception('Could not retrieve msamds')

	print(type(response.content))

	filename = 'temp.csv'
	with open(filename, 'wb') as csv_file:
		csv_file.write(response.content)


	with open(filename) as csv_file:
		reader = DictReader(csv_file)
		for row in reader:
			print(row)
	"""
	string_content = response.content.decode("utf-8") 
	csv_data = io.StringIO(string_content)
	csv_data.seek(0)
	print(csv_data)
	"""

	break


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


