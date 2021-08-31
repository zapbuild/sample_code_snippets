from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.core.exceptions import ValidationError

from account.models import User
from timelog.models import Holiday
from attendance.models import Employee, LeaveType, AllotedLeave, Attendance
from attendance.leave_application import LeaveApplication
import datetime
from freezegun import freeze_time

class LeaveTestCase(TestCase):
    def setUp(self):
        # holiday = Holiday.objects.create('H1', )
        self.supervisor_user = User.objects.create(email='supervisor@g.com', first_name='Supervisor', last_name='Kumar',
                                               mobile='+919888573671', is_active=True)
        self.supervisor_employee = Employee.objects.create(user=self.supervisor_user, empid='20', email=self.supervisor_user.email,
                                                       status=Employee.CONFIRMED)

        self.naresh_user = User.objects.create(email='naresh@g.com', first_name='Naresh', last_name='Kumar', mobile='+919888573673', is_active=True)
        self.naresh_employee = Employee.objects.create(user=self.naresh_user, empid='24',
                                                       email=self.naresh_user.email, status=Employee.CONFIRMED,
                                                       department_supervisor=self.supervisor_employee)
        self.leaves_type_sick = LeaveType.objects.create(name='Sick Leave', abbr='SL', half_day_abbr='SH',
                                                         mixed_day_abbr='S', days=3, credit_frequency=LeaveType.YEARLY,
                                                         carried_forword=False, is_active=True)
        self.leaves_type_earned = LeaveType.objects.create(name='Earned Leave', abbr='EL', half_day_abbr='EH',
                                                         mixed_day_abbr='E', days=3.25, credit_frequency=LeaveType.QUARTERLY,
                                                         carried_forword=True, is_active=True)

    @staticmethod
    def apply_leave(employee, type, start_date, end_date, start_day, end_day):
        attendance_mgr = LeaveApplication(employee, type, start_date, end_date, start_day, end_day, 'Testing..')
        employee_leaves = attendance_mgr.prepare_leaves()
        paid_leaves_month_year = attendance_mgr.mark_paid_leaves()
        attendance_mgr.update_alloted_leaves(paid_leaves_month_year)
        leave = attendance_mgr.create_leaves()

        for m in employee_leaves:
            for attandance in employee_leaves[m]:
                attandance.applied_leave = leave
                attandance.save()

        return leave

    def test_sandwich_weekends_start_date_changed(self):
        """Use case: Employee had applied leaves for 9 July 2021 (Friday)
        Now he is applying the holiday for 12 July 2021 (Monday)
        Merge the older leave with new leaves
        So there will be 4 leaves from 9 to 12 i.e. 9 July 2021, 10 July 2021, 11 July 2021, 12 July 2021
        Hence older applied leaves updated with new start date
        """
        # Step 1 Allot 5 Sick leaves
        AllotedLeave.objects.allot_leaves(
            self.naresh_employee, datetime.date(2021, 7, 1),
            self.leaves_type_sick, 5
        )
        # Applye leave for 9 July 2021 (Friday)
        LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_sick,
                                  datetime.date(2021, 7, 9), datetime.date(2021, 7, 9), 1, 1)

        # now Applye leave for 12 July 2021 (Monday)
        applied_leave = LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_sick,
                                                  datetime.date(2021, 7, 12), datetime.date(2021, 7, 12), 1, 1)

        # We have applied the leave with date(2021, 12, 9) but after processing the leave application the
        # start date should be chagned to date(2021, 7, 9) becuase of sandwich
        self.assertEqual(applied_leave.start_date, datetime.date(2021, 7, 9))

    def test_sandwich_weekends_end_date_changed(self):
        """Use case: Employee had applied leaves for 12 July 2021 (Friday)
        Now he is applying the holiday for 9 July 2021 (Monday)
        Merge the older leave with new leaves
        So there will be 4 leaves from 9 to 12 i.e. 9 July 2021, 10 July 2021, 11 July 2021, 12 July 2021
        Hence older applied leaves updated with new end date
        """
        # Step 1 Allot 5 Sick leaves
        AllotedLeave.objects.allot_leaves(
            self.naresh_employee, datetime.date(2021, 7, 1),
            self.leaves_type_sick, 5
        )
        # Applye leave for 9 July 2021 (Friday)
        LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_sick,
                                  datetime.date(2021, 7, 12), datetime.date(2021, 7, 12), 1, 1)

        # now Applye leave for 12 July 2021 (Monday)
        applied_leave = LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_sick,
                                                  datetime.date(2021, 7, 9), datetime.date(2021, 7, 9), 1, 1)

        self.assertEqual(applied_leave.end_date, datetime.date(2021, 7, 12))

    def test_sandwich_weekends_attendance_entries(self):
        """Use case: Employee had applied leaves for 9 July 2021 (Friday)
        Now he is applying the holiday for 12 July 2021 (Monday)
        Merge the older leave with new leaves
        So there will be 4 leaves from 9 to 12 i.e. 9 July 2021, 10 July 2021, 11 July 2021, 12 July 2021
        Hence older applied leaves updated with new start date
        Hence entries Attendance of type leave will be 3 instead of 1 so the count of leave will be for
        one that was already created for  9 July 2021 and three 10 July 2021, 11 July 2021, 12 July 2021
        """
        # Step 1 Allot 5 Sick leaves
        AllotedLeave.objects.allot_leaves(
            self.naresh_employee, datetime.date(2021, 7, 1),
            self.leaves_type_sick, 5
        )
        # Applye leave for 9 July 2021 (Friday)
        LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_sick,
                                  datetime.date(2021, 7, 9), datetime.date(2021, 7, 9), 1, 1)

        # now Applye leave for 12 July 2021 (Monday)
        applied_leave = LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_sick,
                                                  datetime.date(2021, 7, 12), datetime.date(2021, 7, 12), 1, 1)

        applied_leaves = Attendance.objects.filter(applied_leave=applied_leave)
        applied_leave_dates = [leave.date for leave in applied_leaves]

        self.assertEqual(applied_leave_dates, [
            datetime.date(2021, 7, 9), datetime.date(2021, 7, 10), datetime.date(2021, 7, 11), datetime.date(2021, 7, 12)
        ])

    def test_sandwich_holidays_end_date_changed(self):
        """Use case: Employee had applied leaves for 9 July 2021 (Friday)
        There is a holiday on 8 July, Employee applied for one more leave for 7 July
        Merge the older leave with new leaves
        So there will be 3 leaves from 7 to 9 i.e. 7 July 2021, 8 July 2021, 9 July 2021
        Hence older applied leaves updated with new end date
        """
        # Step 1 Allot 5 Sick leaves
        AllotedLeave.objects.allot_leaves(
            self.naresh_employee, datetime.date(2021, 7, 1),
            self.leaves_type_sick, 5
        )
        # Add holiday for 8 July
        Holiday.objects.create(name='H1', date=datetime.date(2021, 7, 8))
        # Applye leave for 9 July 2021 (Friday)
        LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_sick,
                                  datetime.date(2021, 7, 9), datetime.date(2021, 7, 9), 1, 1)
        # now Applye leave for 7 July 2021 (Monday)
        applied_leave = LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_sick,
                                                  datetime.date(2021, 7, 7), datetime.date(2021, 7, 7), 1, 1)
        # We have applied the leave with date(2021, 12, 7) but after processing the leave application the
        # end date should be chagned to date(2021, 7, 9) becuase of sandwich holiday
        self.assertEqual(applied_leave.end_date, datetime.date(2021, 7, 9))
        # Test the attendance table entries
        applied_leaves = Attendance.objects.filter(applied_leave=applied_leave)
        applied_leave_dates = [leave.date for leave in applied_leaves]
        self.assertEqual(applied_leave_dates, [datetime.date(2021, 7, 9), datetime.date(2021, 7, 7), datetime.date(2021, 7, 8)])

    def test_sandwich_holidays_start_date_changed(self):
        """Use case: Employee had applied leaves for 7 July 2021 (Friday)
        There is a holiday on 8 July, Employee applied for one more leave for 9 July
        Merge the older leave with new leaves
        So there will be 3 leaves from 7 to 9 i.e. 7 July 2021, 8 July 2021, 9 July 2021
        Hence older applied leaves updated with new start date
        """
        # Step 1 Allot 5 Sick leaves
        AllotedLeave.objects.allot_leaves(
            self.naresh_employee, datetime.date(2021, 7, 1),
            self.leaves_type_sick, 5
        )
        # Add holiday for 8 July
        Holiday.objects.create(name='H1', date=datetime.date(2021, 7, 8))
        # Apply leave for 7 July 2021 (Friday)
        LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_sick,
                                  datetime.date(2021, 7, 7), datetime.date(2021, 7, 7), 1, 1)
        # now Apply leave for 9 July 2021 (Monday)
        applied_leave = LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_sick,
                                                  datetime.date(2021, 7, 9), datetime.date(2021, 7, 9), 1, 1)
        # We have applied the leave with date(2021, 12, 9) but after processing the leave application the
        # start date should be chagned to date(2021, 7, 7) becuase of sandwich holiday
        self.assertEqual(applied_leave.start_date, datetime.date(2021, 7, 7))
        # Test the attendance table entries
        applied_leaves = Attendance.objects.filter(applied_leave=applied_leave)
        applied_leave_dates = [leave.date for leave in applied_leaves]
        self.assertEqual(applied_leave_dates, [datetime.date(2021, 7, 7), datetime.date(2021, 7, 8), datetime.date(2021, 7, 9)])

    def test_sandwich_weekend_holidays_start_date_changed(self):
        """Use case: Employee had applied leaves for 9 July 2021 (Friday)
        There is a holiday on 12 July(Monday), Employee applied for one more leave for 13 July (Tuesday)
        Merge the older leave with new leaves
        So there will be 5 leaves from 9 to 13 i.e. 9 July 2021, 10 July 2021, 11 July 2021, 12 July 2021, 13 July 2021
        Hence older applied leaves updated with new end date
        """
        # Step 1 Allot 5 Sick leaves
        AllotedLeave.objects.allot_leaves(
            self.naresh_employee, datetime.date(2021, 7, 1),
            self.leaves_type_sick, 5
        )
        # Add holiday for 12 July
        Holiday.objects.create(name='H1', date=datetime.date(2021, 7, 12))
        # Apply leave for 9 July 2021 (Monday)
        applied_leave = LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_sick,
                                                  datetime.date(2021, 7, 9), datetime.date(2021, 7, 9), 1, 1)
        # Apply leave for 13 July 2021 (Friday)
        LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_sick,
                                  datetime.date(2021, 7, 13), datetime.date(2021, 7, 13), 1, 1)
        # We have applied the leave with date(2021, 12, 9) but after processing the leave application the
        # start date should be chagned to date(2021, 7, 7) becuase of sandwich holiday
        self.assertEqual(applied_leave.start_date, datetime.date(2021, 7, 9))

        # Test the attendance table entries
        applied_leaves = Attendance.objects.filter(applied_leave=applied_leave)
        applied_leave_dates = [leave.date for leave in applied_leaves]
        self.assertEqual(applied_leave_dates, [datetime.date(2021, 7, 9), datetime.date(2021, 7, 10), datetime.date(2021, 7, 11),
                                               datetime.date(2021, 7, 12), datetime.date(2021, 7, 13)])

    def test_apply_leaves_in_two_month_range_28july_5aug(self):
        """Use case: Employee has applied leaves where start date is in july month and end date in August month
        i.e. within 2 month range.
        Employee is alloted with 10 Earned Leaves for the MonthYear(7, 2021) i.e. July
        Employee has applied for 28 July 2021 to 5 Aug 2021
        System will deduct 4 Earned leaves from July Month and 5 Earned leaves from Aug month
        """
        # Step 1. Allot 10 Earned leaves
        with freeze_time("2021-07-29"):
            AllotedLeave.objects.allot_leaves(
                self.naresh_employee, datetime.date(2021, 7, 1),
                self.leaves_type_earned, 10
            )
            # Apply leave for 28 July 2021 to 5 Aug 2021
            applied_leave = LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_earned,
                                                      datetime.date(2021, 7, 28), datetime.date(2021, 8, 5), 1, 1)

            # Get Applloted leaves
            alloted_leaves = AllotedLeave.objects.filter(employee=self.naresh_employee)
            self.assertEqual(alloted_leaves[0].month_year, datetime.date(2021, 7, 1))
            self.assertEqual(alloted_leaves[0].unapproved, 4.0)
            self.assertEqual(alloted_leaves[0].available, 6)

            self.assertEqual(alloted_leaves[1].month_year, datetime.date(2021, 8, 1))
            self.assertEqual(alloted_leaves[1].unapproved, 5.0)
            self.assertEqual(alloted_leaves[1].available, 1)

            # check the leaves dates from applicant prospective
            leave_dates = [(leave.date, leave.leave_type[0]) for leave in Attendance.objects.filter(employee=self.naresh_employee)]
            # TODO test with current date 24 July if there provision to set the current date
            self.assertEqual(leave_dates, [(datetime.date(2021, 7, 28), 'EL'), (datetime.date(2021, 7, 29), 'EL'),
                                           (datetime.date(2021, 7, 30), 'EL'), (datetime.date(2021, 7, 31), 'EL'),
                                           (datetime.date(2021, 8, 1), 'EL'), (datetime.date(2021, 8, 2), 'EL'),
                                           (datetime.date(2021, 8, 3), 'EL'), (datetime.date(2021, 8, 4), 'EL'),
                                           (datetime.date(2021, 8, 5), 'EL') ])

            # check the leaves dates from supervisor prospective, as leaves are not approved yet
            leave_dates = [(leave.date, leave.day_status[0]) for leave in
                           Attendance.objects.filter(employee=self.naresh_employee)]
            self.assertEqual(leave_dates, [(datetime.date(2021, 7, 28), 'A'), (datetime.date(2021, 7, 29), 'A'),
                                           (datetime.date(2021, 7, 30), '-'), (datetime.date(2021, 7, 31), 'S'),
                                           (datetime.date(2021, 8, 1), 'S'), (datetime.date(2021, 8, 2), '-'),
                                           (datetime.date(2021, 8, 3), '-'), (datetime.date(2021, 8, 4), '-'),
                                           (datetime.date(2021, 8, 5), '-')])

    def test_employee_spent_some_hrs_and_applied_leave_for_same_day(self):
        """Use case: Employee has spent some hrs i.e. 0.30, 1,....4  then he applied leave.
        The leave will update the same attendance record that was used to log the hrs for the same day with the leaves
        related columns.
        """
        # Log some time for a particular date
        _date = datetime.date(2021, 7, 22)
        logged_attendance = Attendance.objects.create(
            employee=self.naresh_employee,
            date=_date,
            start_time=datetime.time(9, 30, 00),
            end_time=datetime.time(9, 35, 00),
            duration=0.5
        )
        # Now applied a leave for same date
        applied_leave = LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_sick,_date, _date, .5, .5)
        attendances_as_leave = Attendance.objects.filter(applied_leave=applied_leave)
        # Now a single attendance object with leave status will be created lets check that first
        self.assertEqual(len(attendances_as_leave), 1)
        # This leave object will be the same object where employee has logged some hrs
        attendance_as_leave = attendances_as_leave[0]
        self.assertEqual(logged_attendance.pk, attendance_as_leave.pk)
        # As we have not allocated Sick leave or earned leave to user to applied leave will be LOP type i.e. L
        self.assertEqual(attendance_as_leave.leave_type1, 'L')

    def test_status_absent_sick_leave_half_past_date(self):
        """Use case: Employee is absent on 14 July 2021, later he has applied for SL half
        The resultant day status will be S/L and day value as 0.5
        """
        with freeze_time("2021-07-25"):
            # Suppose today is 2021-07-25
            # 1. Allot SL to the empoloyee
            AllotedLeave.objects.allot_leaves(
                self.naresh_employee, datetime.date(2021, 7, 1),
                self.leaves_type_sick, 2
            )
            # Apply leave for past date lets set it 2021-07-14
            applied_leave = LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_sick,
                                                      datetime.date(2021, 7, 14), datetime.date(2021, 7, 14), 0.5, 0.5)

            # Get attendace
            attendance = Attendance.objects.filter(applied_leave=applied_leave).first()
            self.assertEqual(attendance.leave_type, ('S/L', 0.5))
            # Leave is not approve so day status should be Absent A
            self.assertEqual(attendance.day_status, ('A', 0))

    def test_status_sick_leave_half_future_date(self):
        """Use case: Employee has applied for SL half for the future date
        The resultant day status will be SH and day value as 0 (here day value is zero(0) because future is not certain)
        """
        with freeze_time("2021-07-25"):
            # Suppose today is 2021-07-25
            # 1. Allot SL to the empoloyee
            AllotedLeave.objects.allot_leaves(
                self.naresh_employee, datetime.date(2021, 7, 1),
                self.leaves_type_sick, 2
            )
            # Apply leave for future date i.e. 2021-07-26
            applied_leave = LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_sick,
                                                      datetime.date(2021, 7, 26), datetime.date(2021, 7, 26), 0.5, 0.5)

            # Get attendace
            attendance = Attendance.objects.filter(applied_leave=applied_leave).first()
            self.assertEqual(attendance.leave_type, ('SH', 0))

            # Leave is not approved so day status should be '-' for the future date
            self.assertEqual(attendance.day_status, ('-', 0))

    def test_applied_sickleave_half_backdate(self):
        """Use case: Apply sick leave half for back date and there is no hours logged in timelog
        The leave_type will be S/L ('S/L', 0.5)
        :return:
        """
        AllotedLeave.objects.allot_leaves(
            self.naresh_employee, datetime.date(2021, 7, 1),
            self.leaves_type_sick, 5
        )
        # Applye leave for 9 July 2021 (Friday)
        LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_sick,
                                  datetime.date(2021, 7, 9), datetime.date(2021, 7, 9), 0.5, 0.5)

        attandance = Attendance.objects.first()
        self.assertEqual(attandance.leave_type, ('S/L', 0.5))


    def test_only_supervisor_admin_can_approve_the_leave(self):
        AllotedLeave.objects.allot_leaves(
            self.naresh_employee, datetime.date(2021, 7, 1),
            self.leaves_type_sick, 2
        )

        applied_leave = LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_sick,
                                                  datetime.date(2021, 7, 5), datetime.date(2021, 7, 7), 1, 1)
        # Approve the applied leave
        with self.assertRaises(ValidationError  ) as cm:
            applied_leave.approve(self.naresh_user)

        self.assertEqual(
            'Only admin/supervisors can approve the leave.',
            cm.exception.message
        )


    def test_only_pending_leave_can_be_canceled_leave_by_applicant(self):
        AllotedLeave.objects.allot_leaves(
            self.naresh_employee, datetime.date(2021, 7, 1),
            self.leaves_type_sick, 2
        )

        applied_leave = LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_sick,
                                                  datetime.date(2021, 7, 5), datetime.date(2021, 7, 7), 1, 1)
        # Approve the applied leave
        applied_leave.approve(self.supervisor_user)
        with self.assertRaises(ValidationError  ) as cm:
            applied_leave.cancel(self.naresh_user, 'testing')

        self.assertEqual(
            "Sorry can't canceled the A leaves",
            cm.exception.message
        )

    def test_only_approve_leave_can_be_canceled_leave_by_supervisior_or_admin(self):
        AllotedLeave.objects.allot_leaves(
            self.naresh_employee, datetime.date(2021, 7, 1),
            self.leaves_type_sick, 2
        )

        applied_leave = LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_sick,
                                                  datetime.date(2021, 7, 5), datetime.date(2021, 7, 7), 1, 1)
        # Cancel the approved leave
        with self.assertRaises(ValidationError  ) as cm:
            applied_leave.cancel(self.supervisor_user, 'testing')

        # it should through an error
        self.assertEqual(
            "Sorry can't canceled the P leaves",
            cm.exception.message
        )


    def test_apply_start_halfday_end_halfday(self):
        """Use case: Employee has 2 EL in his account
        He applied EL from 24 Aug Half day to 26 Aug Half day
        2 EL should be deducted from his account
        """
        with freeze_time("2021-08-14"):
            # Step 1. Allot 2 Earned leaves
            AllotedLeave.objects.allot_leaves(
                self.naresh_employee, datetime.date(2021, 8, 14),
                self.leaves_type_earned, 2
            )

            # Apply leave from 24 Aug Half day to 26 Aug Half day
            applied_leave = LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_earned,
                                                      datetime.date(2021, 8, 24), datetime.date(2021, 8, 26), 0.5, 0.5)

            alloted_leaves = AllotedLeave.objects.filter(employee=self.naresh_employee).first()

            # There will be two unaproved leaves and 0 avaialble leaves in employee's account
            self.assertEqual(alloted_leaves.unapproved, 2.0)
            self.assertEqual(alloted_leaves.available, 0)

            applied_leaves = Attendance.objects.filter(applied_leave=applied_leave)
            applied_leave_dates = [(leave.date, leave.leave_type[0]) for leave in applied_leaves]

            self.assertEqual(applied_leave_dates, [
                (datetime.date(2021, 8, 24), 'EH'),
                (datetime.date(2021, 8, 25), 'EL'),
                (datetime.date(2021, 8, 26), 'EH')
            ])

            leave_summary = self.naresh_employee.prepare_leave_summary(month_year=datetime.date(2021, 8, 14), clear_cache=True)
            self.assertEqual(leave_summary['EL']['unapproved'], 2.0)
            self.assertEqual(leave_summary['EL']['available'], 0.0)
            self.assertEqual(leave_summary['EL']['availed'], 0.0)

    def test_apply_end_halfday(self):
        with freeze_time("2021-08-14"):
            # Step 1. Allot 1.5 Earned leaves
            AllotedLeave.objects.allot_leaves(
                self.naresh_employee, datetime.date(2021, 8, 14),
                self.leaves_type_earned, 1.5
            )

            applied_leave = LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_earned,
                                                      datetime.date(2021, 8, 24), datetime.date(2021, 8, 26), 1, 0.5)

            alloted_leaves = AllotedLeave.objects.filter(employee=self.naresh_employee).first()
            self.assertEqual(alloted_leaves.unapproved, 1.5)
            self.assertEqual(alloted_leaves.available, 0)

            applied_leaves = Attendance.objects.filter(applied_leave=applied_leave)
            applied_leave_dates = [(leave.date, leave.leave_type[0]) for leave in applied_leaves]

            self.assertEqual(applied_leave_dates, [
                (datetime.date(2021, 8, 24), 'EL'),
                (datetime.date(2021, 8, 25), 'E/L'),
                (datetime.date(2021, 8, 26), 'LH')
            ])

    def test_sl_cant_carried_forward(self):
        """Use case:
        SL is not carried forward to next year
        Its 30 Dec 2021, Emplyee has 2 Sick leaves(which can't be carried forward to next year)
        He has applied sick leave for 30 Dec 2021 and 01 Jan 2022, The sick leave for 2022 will
        turns into LOP becuase the SL leaves of 2021 cant be carried forward to 2022
        """
        with freeze_time("2021-12-25"):
            # Allot 2 SL's in 2021
            AllotedLeave.objects.allot_leaves(
                self.naresh_employee, datetime.date(2021, 8, 11),
                self.leaves_type_sick, 2
            )

            # Apply SL for 30 Dec 2021 and 01 Jan 2022
            applied_leave = LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_sick,
                                                      datetime.date(2021, 12, 31), datetime.date(2022, 1, 1), 1, 1)

            applied_leaves = Attendance.objects.filter(applied_leave=applied_leave)
            applied_leave_dates = [(leave.date, leave.leave_type[0]) for leave in applied_leaves]

            self.assertEqual(applied_leave_dates, [
                (datetime.date(2021, 12, 31), 'SL'),
                (datetime.date(2022, 1, 1), 'L'),
            ])

    def test_sl_carried_forward_can_apply_for_dec_from_jan(self):
        """Use case:
        The leaves which cant carried forward (SL) can be applied for Dec from Jan
        Its 01 Jan 2022, Emplyee has 2 Sick leaves in 2021
        He has applied sick leave for 25 Dec 2021, Good news is Sick leave availed :)
        """
        with freeze_time("2022-01-01"):
            # Allot 2 SL's in 2021
            AllotedLeave.objects.allot_leaves(
                self.naresh_employee, datetime.date(2021, 8, 11),
                self.leaves_type_sick, 2
            )

            # Apply SL for 25 Dec 2021
            applied_leave = LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_sick,
                                                      datetime.date(2021, 12, 25), datetime.date(2021, 12, 25), 1, 1)

            applied_leaves = Attendance.objects.filter(applied_leave=applied_leave)
            applied_leave_dates = [(leave.date, leave.leave_type[0]) for leave in applied_leaves]

            self.assertEqual(applied_leave_dates, [
                (datetime.date(2021, 12, 25), 'SL'),
            ])


    def test_sl_carried_forward_can_apply_for_jan_from_jan(self):
        """Use case:
        SL is not carried forward to next year
        Its 01 Jan 2022, Emplyee has 2 Sick leaves in 2021
        He has applied sick leave for 31 Dec 2021, 01 Jan 2022, These sick leave turns into LOP
        becuase the SL leaves of 2021 cant be carried forward to 2022
        """
        with freeze_time("2022-01-01"):
            # Allot 2 SL's in 2021
            AllotedLeave.objects.allot_leaves(
                self.naresh_employee, datetime.date(2021, 8, 11),
                self.leaves_type_sick, 2
            )

            # Apply SL for 31 Dec 2021, 01 Jan 2022
            applied_leave = LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_sick,
                                                      datetime.date(2021, 12, 31), datetime.date(2022, 1, 1), 1, 1)

            applied_leaves = Attendance.objects.filter(applied_leave=applied_leave)
            applied_leave_dates = [(leave.date, leave.leave_type[0]) for leave in applied_leaves]


            self.assertEqual(applied_leave_dates, [
                (datetime.date(2021, 12, 31), 'SL'),
                (datetime.date(2022, 1, 1), 'L'),
            ])

    def test_apply_approve_cancel_leave(self):
        a = AllotedLeave.objects.allot_leaves(
            self.naresh_employee, datetime.date(2021, 7, 1),
            self.leaves_type_sick, 2
        )
        leave_summary = self.naresh_employee.prepare_leave_summary(month_year=datetime.date(2021, 7, 5), clear_cache=True)
        self.assertEqual(leave_summary['SL']['available'], 2.0)
        self.assertEqual(leave_summary['SL']['unapproved'], 0.0)
        self.assertEqual(leave_summary['SL']['availed'], 0.0)

        applied_leave = LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_sick,
                                                  datetime.date(2021, 7, 5), datetime.date(2021, 7, 7), 1, 1)

        # Approve the applied leave
        leave_summary = self.naresh_employee.prepare_leave_summary(month_year=datetime.date(2021, 7, 5),
                                                                   clear_cache=True)
        self.assertEqual(leave_summary['SL']['available'], 0.0)
        self.assertEqual(leave_summary['SL']['unapproved'], 2.0)
        self.assertEqual(leave_summary['SL']['availed'], 0.0)


        applied_leave.approve(self.supervisor_user)

        leave_summary = self.naresh_employee.prepare_leave_summary(month_year=datetime.date(2021, 7, 5),
                                                                  clear_cache=True)
        self.assertEqual(leave_summary['SL']['available'], 0.0)
        self.assertEqual(leave_summary['SL']['unapproved'], 0.0)
        self.assertEqual(leave_summary['SL']['availed'], 2.0)


        applied_leave.cancel(self.supervisor_user, 'testing')

        leave_summary = self.naresh_employee.prepare_leave_summary(month_year=datetime.date(2021, 7, 5),
                                                                   clear_cache=True)
        self.assertEqual(leave_summary['SL']['available'], 2.0)
        self.assertEqual(leave_summary['SL']['unapproved'], 0.0)
        self.assertEqual(leave_summary['SL']['availed'], 0.0)

    def test_apply_approve_cancel_leave(self):
        a = AllotedLeave.objects.allot_leaves(
            self.naresh_employee, datetime.date(2021, 7, 1),
            self.leaves_type_sick, 2
        )
        leave_summary = self.naresh_employee.prepare_leave_summary(month_year=datetime.date(2021, 7, 5), clear_cache=True)
        self.assertEqual(leave_summary['SL']['available'], 2.0)
        self.assertEqual(leave_summary['SL']['unapproved'], 0.0)
        self.assertEqual(leave_summary['SL']['availed'], 0.0)

        applied_leave = LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_sick,
                                                  datetime.date(2021, 7, 5), datetime.date(2021, 7, 7), 1, 1)

        # Approve the applied leave
        leave_summary = self.naresh_employee.prepare_leave_summary(month_year=datetime.date(2021, 7, 5),
                                                                   clear_cache=True)
        self.assertEqual(leave_summary['SL']['available'], 0.0)
        self.assertEqual(leave_summary['SL']['unapproved'], 2.0)
        self.assertEqual(leave_summary['SL']['availed'], 0.0)

        applied_leave.cancel(self.naresh_user, 'testing')

        leave_summary = self.naresh_employee.prepare_leave_summary(month_year=datetime.date(2021, 7, 5),
                                                                   clear_cache=True)
        self.assertEqual(leave_summary['SL']['available'], 2.0)
        self.assertEqual(leave_summary['SL']['unapproved'], 0.0)
        self.assertEqual(leave_summary['SL']['availed'], 0.0)


    def test_approve_leave_applied_consecutive_merge_them_as_pending_approval(self):
        """Use case: Emp applied leave for 12 Aug 21 He got approval for supervision
        Then he applied one more leave for 13 Augh 21, This will merge 12 Aug and 13 Aug leaves in
        sigle applied leave application with status as Pending Approval"""

        with freeze_time("2021-08-11"):
            # Step 1. Allot 3 Earned leaves
            AllotedLeave.objects.allot_leaves(
                self.naresh_employee, datetime.date(2021, 8, 11),
                self.leaves_type_earned, 3
            )

            applied_leave = LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_earned,
                                                      datetime.date(2021, 8, 12), datetime.date(2021, 8, 12), 1, 1)

            applied_leave.approve(self.supervisor_user)

            leave_summary = self.naresh_employee.prepare_leave_summary(month_year=datetime.date(2021, 8, 11),
                                                                       clear_cache=True)
            self.assertEqual(leave_summary['EL']['available'], 2.0)
            self.assertEqual(leave_summary['EL']['unapproved'], 0.0)
            self.assertEqual(leave_summary['EL']['availed'], 1.0)

            applied_leave = LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_earned,
                                                      datetime.date(2021, 8, 13), datetime.date(2021, 8, 13), 1, 1)

            leave_summary = self.naresh_employee.prepare_leave_summary(month_year=datetime.date(2021, 8, 11),
                                                                       clear_cache=True)

            self.assertEqual(leave_summary['EL']['available'], 1.0)
            self.assertEqual(leave_summary['EL']['unapproved'], 2.0)
            self.assertEqual(leave_summary['EL']['availed'], 0.0)


    def test_insufficient_sick_leaves_deduct_from_earned_leaves(self):
        """Use case: Employee has 2 SL in his account but he has applied 3 leaves
        deduct the third leave from earned leaves if available
        Note: this feature is not included in this application as per discussion with Management we have removed this feature
        """
        # Step 1 Allot 2 Sick leaves and 2 Earned leaves
        AllotedLeave.objects.allot_leaves(
            self.naresh_employee, datetime.date(2021, 7, 1),
            self.leaves_type_sick, 2
        )
        alloted_earned = AllotedLeave.objects.allot_leaves(
            self.naresh_employee, datetime.date(2021, 7, 1),
            self.leaves_type_earned, 2
        )
        # Step 3 apply 3 SLs
        applied_leave = LeaveTestCase.apply_leave(self.naresh_employee, self.leaves_type_sick,
                                                  datetime.date(2021, 7, 5), datetime.date(2021, 7, 7), 1, 1)

        ## self.assertEqual(alloted_earned.available, 1)





