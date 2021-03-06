import os
import sys
import pandas as pd
import time
from pathlib import Path
from datetime import datetime
import late

# Constants
# Salary grade for labor
LOW_SALARY = 10000
# Total working days
WORKING_DAYS = 26

# Master attendance dictionary
days_dict = {}

# Calculate per day cost on direct employees
def perDayDirectEmpCost(file, outfile, dates):
	# Sort dates
	dates.sort(key = lambda date: datetime.strptime(date, '%d-%b'))
	print('Calculating direct employee costs from:', file)
	# Construct a dataframe for employee salaries
	df = pd.read_csv(file)
	# making new data frame with dropped NA values 
	df = df.dropna(axis = 0, how ='any')
	df.set_index('EmpNo', inplace=True)
	# Get only direct employee records
	df = df.loc[df['EmpType'] == 'direct']

	# Construct header
	header = 'Day,Cost'

	# Write out file header and contents	
	with open(outfile, 'w') as f:
		# Write header
		f.write(header + '\n')
		# Iterate across dates
		for date in dates:
			cost_for_day = 0
			# Iterate across employees
			for index, row in df.iterrows():
				# If present then add cost
				if(row[date]=='P'):
					cost_for_day += round(row['Salary']/WORKING_DAYS,2)
		
			cost_for_day = round(cost_for_day,2)
			# Construct and Write row
			row = str(date) + ',' + str(cost_for_day) 
			f.write(row + '\n')

		
	# Close output CSV file
	f.close()
	print('Writing out to Cost Per Day file at ' + str(outfile) + ' completed...')


# Write master attendance dict to csv
def writeMasterToCSV(output_path, df, dates):
	# Sort dates
	dates.sort(key = lambda date: datetime.strptime(date, '%d-%b'))
	
	# Construct Header
	header = 'EmpNo,Name,Count,Salary,EmpType'
	for date in dates:
		header = header + ',' + date

	# Write out file header and contents	
	with open(output_path, 'w') as f:
		# Write header
		f.write(header + '\n')
		
		# Iterate over all the employees in the master dictionary
		for emp in days_dict:

			# Get values from each row of dictionary
			count = days_dict[emp]['count']
			name = days_dict[emp]['name']
			attendance = days_dict[emp]['attendance']
			# Get the daily salary for a person	
			salary = df.loc[emp,'Total Salary'] if emp in df.index else 0
			# Classify employee from salary
			emptype = 'indirect' if salary < LOW_SALARY else 'direct'

			# Initialize CSV file data row
			row = str(emp) + ',' + str(name) + ',' + str(count) + ',' + str(salary) + ',' + str(emptype)
		
			# Determine whether present or absent for the days
			for date in dates:
				status = ''
				# No entry recorded in file for that day
				if attendance.get(date) == None:
					status = 'X'
				# File entry present
				else:
					status = attendance[date]
				# Append status to row to be written
				row = row + ',' + status
			
			# Write row
			f.write(row + '\n')

	# Close output CSV file
	f.close()
	print('Writing out to Emp-Attendance file at ' + str(output_path) + ' completed...')
	
# Create a master dictionary for each employe and their attendance across the dates
def countDailyAttendance(d, date, dfsalary):
	count = 0
	for x in d:
		# Get status and name of each employee
		status = d[x]['Status']
		name = d[x]['Name']
		intime = d[x]['InTime']
		shift = d[x]['Shift']

		# Update record for employee with empno = x
		if days_dict.get(x) == None:
			# Initialize employee entry
			days_dict[x] = {'count': 0, 'name': name, 'attendance': {}}
			
			# Check if keyword 'present' is in status
			if ('Present' in status):
				days_dict[x]['count'] = 1
				days_dict[x]['attendance'][date] = late.checkLate(x,intime,shift,dfsalary)
			else:
				days_dict[x]['attendance'][date] = 'A'
			
			# Count Number of employees inserted	 
			count = count + 1
		
		# Employee already present, no need to insert
		elif days_dict.get(x) != None:
			# Check if keyword 'present' is in status
			if ('Present' in status):
				days_dict[x]['count'] += 1
				days_dict[x]['attendance'][date] = late.checkLate(x,intime,shift,dfsalary)
			else:
				days_dict[x]['attendance'][date] = 'A'

	if count > 0:
		print('Total employees inserted from file for',date,':',count)


# Get each file from the input folder and convert into a dictionary
def createEmpAttendanceDict(data_source, dfsalary):
	dates = []
	for filename in os.listdir(data_source):
		try:
			if filename.endswith('.csv') and not 'salary' in filename:
				# Get date from filename
				date = os.path.splitext(filename)[0]
				dates.append(date)
				# Get source file path
				file_path = Path(Path(data_source) / filename)
				# Create Data Frame
				df = pd.read_csv(file_path, index_col='E. Code', usecols=['E. Code', 'Name', 'Status', 'InTime', 'Shift'])
				d = df.to_dict('index')
				# Update master dictionary with attendances for that day
				countDailyAttendance(d, date, dfsalary)
		except Exception as e:
			print('[ERROR] There was an issue with file ' + filename + ', it will be skipped over')
			print(e)

	return dates

if __name__ == '__main__':
	
	start = time.time()
	print('Execution started...')
	data_source = Path(Path(os.getcwd()) / 'input')
	print('Source: ', data_source)
	
	# Get employee-salary rate file
	salaryfile = Path(Path(os.getcwd()) / 'input/salary-eid.csv')
	# Construct a dataframe for employee salaries
	dfsalary = pd.read_csv(salaryfile)
	# making new data frame with dropped NA values 
	dfsalary = dfsalary.dropna(axis = 0, how ='any')
	dfsalary.set_index('Employee Code', inplace=True)
	
	# Get dates
	dates = createEmpAttendanceDict(data_source, dfsalary)
	# Set path for employee attendance file
	output_path = Path(Path(os.getcwd()) / 'output/attendance-count.csv')
	# Write out the attendances to CSV
	writeMasterToCSV(output_path, dfsalary, dates)
	cost_for_day_file = Path(Path(os.getcwd()) / 'output/cost-per-day.csv')
	# Calculate and write the cost per day variation for direct emps
	perDayDirectEmpCost(output_path, cost_for_day_file, dates)
	end = time.time()
	print('Execution finished in',str(round(end-start,2)),'secs')
	# required for executables
	# input('You can close this window now...')