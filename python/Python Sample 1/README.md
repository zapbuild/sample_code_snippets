# Attendance: Since most of the people around the globe are working from home, so this application is helpful to manage the attendance of employees based to their daily working logs.
* The status logs in range >= 3 Hrs and < 6 Hrs are considered as Half day.
* The status logs in range >= 6 and  < 8.30 are considered as Full day 
* the status logs below 3 Hrs are considered as Absent.

The logs to be entered by the employees manually through a given interface.

# Leaves:
This feature enables the employee to apply leaves on this platform, hence it can be accepted/rejected by the respective supervisors. Sandwich day is also handled in this is app. 

# To Import leaves from csv file
`python manage.py import_leaves` Here is the list of csv column EmpID,Name,EL,SL

| EmpID     | Name           | EL  | SL |
| ----------|:--------------:| ---:|---:|
| 0002      | Ramandeep Singh| 15  | 75 |     
| 0023      | Pooja Singh    | 11  | 25 |


# Credit leaves automatically
`python manage.py credit_leaves` run this command on 1st day of every months(one may use crontab) so that it can credit Quarterly and Yearly leaves to employees account.

# Files information
1. en.po is localization file to translating the app content. Suppose if application is for Arabic contries put ar.po files for arabic translations
2. api.py file is to handle http requests it accept the data from client and respond the client from processed data.
3. serializers.py file is to convert the json data from http to Python objects and Python objects to json with respective validations.
4. models.py represents the database interface, business logic related to the objects is witten over this file. 

# 

# Run test cases.
`python manage.py test attendance.v1.tests.LeaveTestCase`   


