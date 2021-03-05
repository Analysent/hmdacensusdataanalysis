# hmda census data analysis for mean income less than or equal to 50k


Description:

    #Loan information under 50k based on census data DP code for mean income less than or equal to 50k.  
    #Identified Metropolitan Statistical Areas (MSA’s) that have an average household income of less than $50,000 per year in 2019 and joining that list to CFPB’s HMDA dataset.
    #Read the csv file from census site and also used the DP code 
    from hmda database to collect additional home loan, borrower demography data.  Identified a proper variable to use (DP03_0063E), and retrieve a list of MSA’s matching the criteria 
    #Wrote the csv with columns described as per the requirement 
        total number of loans
        loans by race 
        loan amount 
        loan to value ratio 
        interest rate
        total loan costs
        loan term
        property value
        income
        tract minority population percent
    # Visualized a bar graph using numpy and matplotlib library to show number of loans by race

## how to use the code

Clone the project:

    git clone https://github.com/Analysent/hmdacensusdataanalysis.git

Create a virtualenv using Python 3 and install dependencies. E.g. on OSX:

    python3 -m venv venv
    . venv/bin/activate
    pip install -r requirements.txt

Run code:

    python hmdadata.py
