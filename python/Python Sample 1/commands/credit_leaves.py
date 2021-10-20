from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from attendance.models import AllotedLeave, LeaveType, Employee
from common.util.common import Common
common = Common()

class Command(BaseCommand):
    help = 'Credits leaves to the employee\'s account'

    # def add_arguments(self, parser):
    #     parser.add_argument('poll_ids', nargs='+', type=int)

    def _credit_leaves(self, date, frequency):
        """
        :param date: Date to which leaves are being credit, we'll extrace month year from this date
        :param frequency: LeaveType.QUARTERLY, LeaveType.YEARLY
        :return: None
        """
        leave_types = LeaveType.objects.filter(
            credit_frequency=frequency,
            is_active=True
        )

        frequency_title = ''
        for type in LeaveType.TYPES:
            if type[0] == frequency:
                frequency_title = type [1]
                break


        mail_list = []
        for leave_type in leave_types:
            for employee in Employee.objects.filter(status=Employee.CONFIRMED):
                AllotedLeave.objects.allot_leaves(employee, date, leave_type, leave_type.days,
                                                  comment="%s %s leaves added." % (frequency_title, frequency),
                                                  is_scheduled=True)
                leave_summary = employee.current_leave_summary(leave_type.abbr)
                mail_args = {
                    "mail_template_args": {
                        'user': employee.user,
                        'leave_type': leave_type,
                        'frequency_title': frequency_title,
                        'summary': leave_summary[leave_type.abbr]
                    },
                    "mail_to": employee.user.email, "mail_template": "notifications/attendance/leaves_credited.html",
                    "mail_subject": '%s %ss Credited' % (frequency_title, leave_type.name)
                }
                mail_list.append(mail_args)

        common.send_mass_mail(mail_list)

    def _credit_quarterly_leaves(self, today):
        starting_months_of_quarters = [1, 4, 7, 10]
        if today.month in starting_months_of_quarters:
            self._credit_leaves(today, LeaveType.QUARTERLY)


    def _credit_yearly_leaves(self, today):
        if today.month == 1:
            self._credit_leaves(today, LeaveType.YEARLY)

    def handle(self, *args, **options):
        today = datetime.today().date()
        self._credit_quarterly_leaves(today)
        self._credit_yearly_leaves(today)
