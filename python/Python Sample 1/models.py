import json
from datetime import timedelta, datetime, date
from collections import OrderedDict
from dateutil.relativedelta import relativedelta
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models, transaction
from account.models import Employee as AccountEmployee
from timelog.models import Holiday
from .util import MonthYear

LEAVE_APPROVAL_PENDING = 'P'
LEAVE_APPROVED = 'A'
LEAVE_DECLINED = 'D' # When supervisor Decline/cancel his subordinates leave
LEAVE_CANCELED = 'C' # When Employee cancel his applied leave

LEAVE_STATUS = (
    (LEAVE_APPROVAL_PENDING, 'Pending'),
    (LEAVE_APPROVED, 'Approved'),
    (LEAVE_DECLINED, 'Declined'),
    (LEAVE_CANCELED, 'Canceled'),
)


class EmployeeManager(models.Manager):
    def attendances(self, accessed_by, month, year):
        """
        :param month: Integer, month of the attendance record
        :param year: Integer, year of the attendance record
        :return: processed list of the attendance
        """
        month_year = start_date = date(year, month, 1)
        end_date = start_date + relativedelta(day=31)
        delta = timedelta(days=1)

        dates = []
        while start_date <= end_date:
            dates.append(start_date)
            start_date += delta

        attendance_prefetch = models.Prefetch(
            'attendance',
            queryset=Attendance.objects \
                .filter(date__month=month, date__year=year) \
                .order_by('-date'),
            to_attr='monthly_attendance'
        )

        employees = self.get_queryset() \
            .prefetch_related(attendance_prefetch) \
            .filter(empid__isnull=False) \
            .exclude(user__is_active=False, user__updated_at__lte=end_date) \
            .order_by('empid')

        if not accessed_by.has_perm('attendance.can_manage_full_attendance_leaves'):
            team_employee_ids = [emp.pk for emp in accessed_by.get_team()]
            employees = employees.filter(pk__in=team_employee_ids + [accessed_by.pk])
        # employees = employees.filter(pk=3)
        for e in employees:
            e.prepare_attendance(dates)
            e.prepare_leave_summary(month_year)

        return employees


class Employee(AccountEmployee):
    LEAVE_SUMMARY_CACHE_KEY = 'EMP_LEAVE_SUMMARY_{emp_id}_{year}_{month}'

    objects = EmployeeManager()

    class Meta:
        proxy = True
        managed = False

    @property
    def attendance_table(self):
        if not hasattr(self, '_attendance'):
            raise Exception('Please call prepare_attendance(dates) method before calling attendance_table')
        return self._attendance

    @property
    def leave_summary(self):
        if not hasattr(self, '_summary'):
            raise Exception('Please call prepare_leave_summary(month_year) method before calling leave_summary')
        return self._summary

    @property
    def credited_days(self):
        if not hasattr(self, '_credited_days'):
            raise Exception('Please call prepare_attendance(dates) method before calling credited_day')
        return self._credited_days

    @property
    def short_leaves(self):
        if not hasattr(self, '_short_leaves'):
            raise Exception('Please call prepare_attendance(dates) method before calling credited_day')
        return self._short_leaves

    @property
    def absent(self):
        if not hasattr(self, '_absent'):
            raise Exception('Please call prepare_attendance(dates) method before calling credited_day')
        return self._absent

    def prepare_attendance(self, dates):
        # TODO this function is not as per standard need to revamp it later
        self._attendance = OrderedDict()
        self._credited_days = 0
        self._absent = 0
        self._short_leaves = 0
        for _date in dates:
            attendance = Attendance(employee=self, date=_date)
            self._attendance[_date] = attendance
            self._credited_days += attendance.day_status[1]

        for attendance in self.monthly_attendance:
            self._attendance[attendance.date] = attendance
            if attendance.date.weekday() not in [5, 6] and attendance.day_status[0] != 'H':
                self._credited_days += attendance.day_status[1]
                if attendance.day_status[0] == Attendance.PRESENT \
                        and attendance.duration >= 6 and attendance.duration < 8.30:
                    # Timelog between 6 hours to 8.30 hours will be considered as shortleave
                    self._short_leaves += 1

        # Calculate Absent
        total_working_days = 0
        selected_month_year = MonthYear(dates[0])

        current_month_year = MonthYear(datetime.today())
        if selected_month_year == current_month_year:
            total_working_days = datetime.today().day
        elif selected_month_year < current_month_year:
            total_working_days = selected_month_year.last_date().day

        # Timelog between 6 hours to 8.30 hours will be considered as shortleave for twice a month,
        # present in RED. Every 3 such cases will be marked as one full day leave
        self._credited_days -= self._short_leaves // 3

        self._absent = total_working_days - self._credited_days


    def prepare_leave_summary(self, month_year, clear_cache=False):
        """
        Prepare the leave summary of Employee
        :param month_year: selected month_year of type datetime.date() or MonthYear
        :param clear_cache: Boolean
        :return: leave summary of selected month year
        """

        if not isinstance(month_year, MonthYear):
            month_year = MonthYear(month_year)

        summary = None
        cache_key = Employee.LEAVE_SUMMARY_CACHE_KEY \
            .format(emp_id=self.pk, year=month_year.year, month=month_year.month)

        if not clear_cache:
            # Try to read summary from cache
            summary = cache.get(cache_key)

        if not summary:
            summary = {}
            default = {'available': 0, 'unapproved': 0, 'availed': 0}
            EL = AllotedLeave.objects\
                .values('pk', 'available', 'unapproved', 'availed', 'month_year')\
                .filter(employee=self, month_year__lte=month_year.get(), type__abbr='EL')\
                .order_by('-month_year')\
                .first()

            if EL and EL['month_year'] != month_year.get():
                EL['unapproved'] = 0
                EL['availed'] = 0

            summary['EL'] = EL or default

            SL = AllotedLeave.objects\
                .values('available', 'unapproved', 'availed', 'month_year') \
                .filter(employee=self, month_year__lte=month_year.get(), type__abbr='SL') \
                .order_by('-month_year') \
                .first()

            if SL and SL['month_year'] != month_year.get():
                SL['unapproved'] = 0
                SL['availed'] = 0

            summary['SL'] = SL or default

            # Cache only for current month and older months
            if month_year <= MonthYear(datetime.today().date()):
                cache.set(cache_key, summary, timeout=5184000)
                # timeout is in second, here 5184000 sec = 2 Months

        self._summary = summary if summary else AllotedLeave()
        return summary


    def update_leave_summary_cache(self, month_year):
        current_month_year = MonthYear(datetime.today())

        if type(month_year) != MonthYear:
            month_year = MonthYear(month_year)

        while current_month_year >= month_year:
            self.prepare_leave_summary(month_year, clear_cache=True)
            month_year = month_year.next()

    def prepare_leave_summary_last_two_months(self, month_year):
        """
        This method is not being used but usefull to understand the current struction of leaves in future
        :param month_year: selected month year
        :return: summary of last 2 months
        """
        cache_key = Employee.LEAVE_SUMMARY_CACHE_KEY \
            .format(emp_id=self.pk, year=month_year.year, month=month_year.month)

        summary = cache.get(cache_key)

        if not summary:
            alloted = list(AllotedLeave.objects \
                           .filter(employee=self, month_year__lte=month_year) \
                           .order_by('-month_year')[:2])

            if len(alloted) > 0:
                selected_month_leave_summary = alloted.pop(0)
            else:
                selected_month_leave_summary = AllotedLeave()

            previouse_month_year = month_year + relativedelta(months=-1)
            summary = {
                'selected': selected_month_leave_summary,
                'previous': None,

            }

            if len(alloted) > 0 and selected_month_leave_summary.month_year <= previouse_month_year:
                summary['previous'] = selected_month_leave_summary
            elif len(alloted) > 0:
                previous_month_leave_summary = alloted.pop(0)
                summary['previous'] = previous_month_leave_summary
            else:
                previous_month_leave_summary = AllotedLeave()
                summary['previous'] = previous_month_leave_summary

            cache.add(cache_key, summary, 10)

        self._summary = summary
        return summary


class Attendance(models.Model):
    UNCERTAIN = '-'
    PRESENT = 'P'
    ABSENT = 'A'
    HALF_DAY = 'HD'
    LOSS_OF_PAY = 'L'
    LOP_HALF_DAY = 'LH'
    WEEK_ENDS = 'S'

    # EARNED_LEAVE = 'EL' # Managed
    # EARNED_LEAVE_HALF = 'EH' # Managed
    # SICK_LEAVE = 'SL' # Managed
    # SICK_LEAVE_HALF = 'SH' # Managed
    #
    # SL_LOP = 'S/L'
    # SL_EL = 'S/E'
    # EL_LOP = 'E/L'

    STATUS = (
        (PRESENT, 'Present'),
        (ABSENT, 'Absent'),
        (LOSS_OF_PAY, 'Loss of Pay LOP'),
        (LOP_HALF_DAY, 'LOP Half Day'),
        (HALF_DAY, 'Half Day'),
        # (EL_LOP, 'EL + LOP'),
        # (EARNED_LEAVE, 'Earned Leave'),
        # (EARNED_LEAVE_HALF, 'Earned Leave Half'),
        # (SICK_LEAVE, 'Sick Leave'),
        # (SICK_LEAVE_HALF, 'Sick Leave Half'),
        # (SL_EL, 'SL + EL'),
        # (SL_LOP, 'SL + LOP'),
    )

    employee = models.ForeignKey(Employee, on_delete=models.DO_NOTHING, related_name='attendance')
    date = models.DateField()
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    duration = models.FloatField(blank=True, null=True)

    leave_type1 = models.CharField(max_length=4, blank=True, null=True)
    leave_type1_value = models.FloatField(blank=True, null=True, help_text='Percentage value of the day')

    # To handle the two types of leave e.g. User applied for SL but SL is
    # 0.5 in his account he can apply half EL for the rest hald day
    leave_type2 = models.CharField(max_length=4, blank=True, null=True)
    leave_type2_value = models.FloatField(blank=True, null=True, help_text='Percentage value of the day')

    leave_status = models.CharField(max_length=2, choices=LEAVE_STATUS, default=LEAVE_APPROVAL_PENDING)
    applied_leave = models.ForeignKey('AppliedLeaves', on_delete=models.CASCADE, blank=True, null=True, related_name='leave_days')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        default_permissions = ()
        permissions = (
            ('can_manage_full_attendance_leaves', 'Can manage attendance & Leaves'),
        )

    @property
    def day_status(self):
        """
        Represent the current day status i.e. P, A, HD, L, EL, SL, E/S with the day value as 1., 0.5
        It dose not includes the Pending/Cancelled/Declined leaves
        :return: (status, day_value) e.g. (SL, 0.5) for Sick leave half day.

        Please note day_value varies on the current date
        """
        if hasattr(self, '_cached_day_status'):
            # Use Cached/stored day status
            return self._cached_day_status
        else:
            # Cache/store the computed value if day_status call multiple times
            self._cached_day_status = self._day_status(ignore_leave_status=False)

        return self._cached_day_status

    @property
    def leave_type(self):
        """
        Represent the leave type L, EL, SL, E/S whether it is approved/cancelled/decline
        :return: string L, EL, SL, E/S
        """
        return self._day_status(ignore_leave_status=True)

    def _day_status(self, ignore_leave_status=True):
        """
        Ths function consider the upper hand of applied leave e.g. EL, means that if employee has applied for the leave
        but also logged his hours then the his days status will remaines EL not as present

        :param ignore_leave_status: Boolean, If we want result set of only Approved leaves then set is False
        :return: (status, day_value),
            where status can be A, P, L, LH SL, EL, SH, EH, S/L, E/L, S/E,  Holiday, weekdays(S) etc.
            and day_value can be 0.5, 1
        """

        # Status determines the day status it can be Present(P), Absent(A),
        # Loss of Pay(L), LH, SL, EL, S/E, S/L, Holiday, weekdays(S) etc.
        # Initially lest consider it as UNCERTAIN i.e. Hyphen ( - )
        status = Attendance.UNCERTAIN

        # Day value is a parameter which delermine the salary to be credited for a day
        # if day value is 0.5 then employee is eligible for half day salary if day value is 1 the full day salary
        # e.g. employee has approve Half sick leave then 0,5 should be credited ho his account
        # but if leave is Loss of Pay the zero (0) should be credited
        day_value = 0

        # This is as same as day_value but unlike day_value it also considers
        # the LOSS_OF_PAY and LOP_HALF_DAY. This is useful to determine the total leave applied
        # in a day so that we can consider the log hrs (Attendance.duration) if its less then 1
        leave_day_value = 0

        is_valid_status = True
        if not ignore_leave_status:
            is_valid_status = self.leave_status == LEAVE_APPROVED

        today = date.today()

        if self.leave_type1 and is_valid_status:

            if self.date <= today:
                # This code is just to evaluate day value future is not certain
                # so the Leave date grater than or equal to today are not consider to evaluate the day_value
                leave_day_value += self.leave_type1_value
                if self.leave_type1 != Attendance.LOSS_OF_PAY:
                    day_value += self.leave_type1_value
                if self.leave_type2:
                    leave_day_value += self.leave_type1_value
                    if self.leave_type2 != Attendance.LOSS_OF_PAY:
                        day_value += self.leave_type2_value


            # This code is to determine the leave status
            leave_type1_obj = LeaveType.find_by_abbr(self.leave_type1)

            # Lets update it as a Full day leave so set the status leave_type1_obj.abbr.
            # Examples of this kind of status are L, SL, EL
            status = leave_type1_obj.abbr
            if self.leave_type1_value < 1:
                # if leave_type1_value is less then 1 e.g. 0.5 in mostly all cases, then its consider as half day
                # e.g. LOP_HALF_DAY(LH), SICK_LEAVE_HALF(SH), and EARNED_LEAVE_HALF(EH)
                status = leave_type1_obj.half_day_abbr

            if self.leave_type1_value < 1 and self.leave_type2:
                # if leave_type1_value is 0.5 i.e. less than 1 and there is some value in self.leave_type2
                # then it must be a mixed day leave e.g. SL_LOP(S/L), SL_EL(S/E), and EL_LOP(E/L)
                leave_type2_obj = LeaveType.find_by_abbr(self.leave_type2)
                status = "%s/%s" % (leave_type1_obj.mixed_day_abbr, leave_type2_obj.mixed_day_abbr)

        if leave_day_value < 1:
            # if leave_day_value is < 1, leave is either not applied, if applied then its not for the full day
            # so for the case its not applied then our status could be P, A, S,
            # if applied for the half day then our status could be S/L, E/L if not weekdays and holidays
            if self.date <= today:
                if status == Attendance.UNCERTAIN:
                    # Case1 leave is not applied
                    status_by_duration = Attendance.ABSENT
                    # if duration is less than 3 it will be considered as absent
                    if self.duration:
                        if self.duration >= 3 and self.duration < 6:
                            # This will be consider has half day
                            status_by_duration = Attendance.HALF_DAY
                            day_value = 0.5
                        elif self.duration >= 6 and self.duration < 8.30:
                            # Present with red P
                            status_by_duration = Attendance.PRESENT
                            day_value = 1
                        elif self.duration >= 8.30:
                            status_by_duration = Attendance.PRESENT
                            day_value = 1
                    status = status_by_duration
                elif self.date.weekday() not in [5, 6]:
                    # Case2 Half day leave is applied and its not a weekday
                    # and log duration is less than 3
                    # If half day leave is applied then leave type object should be leave_type1_obj
                    duration = self.duration if self.duration else 0
                    if duration < 3:
                        status = "%s/L" % leave_type1_obj.mixed_day_abbr

            if status in [Attendance.UNCERTAIN, Attendance.ABSENT]:
                holidays = [holiday.date for holiday in Holiday.objects.year(self.date.year)]
                if self.date in holidays:
                    status = 'H'
                    day_value = 1
                elif self.date.weekday() in [5, 6]:
                    status = Attendance.WEEK_ENDS
                    day_value = 1


        if self.date > today:
            # Wild card check if date is future date then day value is always gonna Zero ( 0 )
            day_value = 0

        day_value = min(day_value, 1)
        return (status, day_value)


    def _day_status_with_logtime_priority(self, ignore_leave_status=True):
        """this function take log time on priority ie. if user has taken leave and added logs of more than 6 Hrs
        then he/she should be considered as Present.
        Note: This function is not being used but can be used in future
        """
        today = date.today()

        status_by_duration = Attendance.UNCERTAIN
        day_value = 0
        if self.date < today:
            status_by_duration = Attendance.ABSENT
            # if duration is less than 3 it will be considered as absent
            if self.duration:
                if self.duration >= 3 and self.duration < 6:
                    # This will be consider has half day
                    status_by_duration = Attendance.HALF_DAY
                    day_value = 0.5
                elif self.duration >= 6 and self.duration < 8.30:
                    # Present with red P
                    status_by_duration = Attendance.PRESENT
                    day_value = 1
                elif self.duration >= 8.30:
                    status_by_duration = Attendance.PRESENT
                    day_value = 1

        is_valid_status = True
        if not ignore_leave_status:
            is_valid_status = self.leave_status == LEAVE_APPROVED

        if self.leave_type1 and self.leave_type1 != Attendance.LOSS_OF_PAY and is_valid_status:
            # This block is just to update day value
            day_value += self.leave_type1_value
            if self.leave_type2 and self.leave_type2 != Attendance.LOSS_OF_PAY:
                day_value += self.leave_type2_value


        if status_by_duration in [Attendance.UNCERTAIN, Attendance.ABSENT, Attendance.HALF_DAY]\
                and self.leave_type1 and is_valid_status:
            # This block is just to update leave type
            status = self.leave_type1
            leave_type1_obj = None

            if status_by_duration == Attendance.ABSENT:
                if self.leave_type1 and self.leave_type1_value < 1:
                    # for the statues like LOSS_OF_PAY(L), SL_LOP(S/L), and EL_LOP(E/L)
                    if self.leave_type1 == Attendance.LOSS_OF_PAY:
                        status = Attendance.LOSS_OF_PAY
                    else:
                        leave_type1_obj = LeaveType.find_by_abbr(self.leave_type1)
                        if leave_type1_obj:
                            status = "%s/L" % leave_type1_obj.mixed_day_abbr


            if status_by_duration == Attendance.HALF_DAY or (
                self.leave_type1 and self.leave_type1_value < 1):  # == 0.5:
                # for the statues like LOP_HALF_DAY(LH), SICK_LEAVE_HALF(SH), and EARNED_LEAVE_HALF(EH)
                if self.leave_type1 == Attendance.LOSS_OF_PAY:
                    if status_by_duration == Attendance.HALF_DAY:
                        status = Attendance.HALF_DAY
                    else:
                        status = Attendance.LOP_HALF_DAY
                else:
                    leave_type1_obj = LeaveType.find_by_abbr(self.leave_type1)
                    if leave_type1_obj:
                        status = leave_type1_obj.half_day_abbr

            # if user is absent by the duration method then we can consider the leave_type2
            if status_by_duration in [Attendance.UNCERTAIN, Attendance.ABSENT]\
                    and self.leave_type2 and self.leave_type2_value:
                # for the statues like SL_LOP(S/L), SL_EL(S/E), and EL_LOP(E/L)
                if self.leave_type2 == Attendance.LOSS_OF_PAY and leave_type1_obj:
                    status = "%s/L" % leave_type1_obj.mixed_day_abbr
                else:
                    leave_type2_obj = LeaveType.find_by_abbr(self.leave_type2)
                    if leave_type2_obj:
                        if leave_type1_obj:
                            status = "%s/%s" % (leave_type1_obj.mixed_day_abbr, leave_type2_obj.mixed_day_abbr)
                        else:
                            status = "L/%s" % leave_type2_obj.mixed_day_abbr

            if not status:
                status = self.status
        else:
            status = status_by_duration

        # Consider Saturday Sunday and other holidays
        # TODO include Holidays in below condition
        if status_by_duration not in [Attendance.PRESENT, Attendance.HALF_DAY]:
            if self.date.weekday() in [5, 6]:
                if status in [Attendance.UNCERTAIN, Attendance.ABSENT, Attendance.LOSS_OF_PAY, Attendance.LOP_HALF_DAY]:
                    status = Attendance.WEEK_ENDS
                    if self.date <= today:
                        day_value = 1

        if self.date > today:
            # if status == Attendance.ABSENT:
            #     status = Attendance.UNCERTAIN
            day_value = 0

        day_value = min(day_value, 1)

        return (status, day_value)

    @staticmethod
    def sec_to_duration(seconds):
        min, sec = divmod(seconds, 60)
        hour, min = divmod(min, 60)
        return "%d.%02d" % (hour, min)

    def duration_add_sec(self, seconds):
        seconds = self.duration_in_sec() + seconds
        self.duration =  Attendance.sec_to_duration(seconds)
        return self.duration

    def duration_in_sec(self):
        h, m = str(self.duration).split('.')
        if len(m) == 1:
            m = m + "0"
        return int(h) * 3600 + int(m) * 60


class LeaveType(models.Model):
    LEAVE_TYPE_CACHE_KEY = 'LEAVE_TYPE_{abbr}'
    MONTHLY = 'M'
    QUARTERLY = 'Q'
    YEARLY = 'Y'
    SPECIAL = 'S'
    TYPES = (
        (MONTHLY, 'Monthly'),
        (QUARTERLY, 'Quarterly'),
        (YEARLY, 'Yearly'),
        (SPECIAL, 'Special'),
    )
    name = models.CharField(max_length=200)
    abbr = models.CharField(max_length=2, help_text="e.g. SL for Sick leave")
    half_day_abbr = models.CharField(max_length=2, help_text="e.g. SH for Sick leave Half")
    mixed_day_abbr = models.CharField(max_length=2, help_text="e.g. S for SL_EL i.e. S/E")
    days = models.FloatField()
    credit_frequency = models.CharField(max_length=1, choices=TYPES)
    carried_forword = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @staticmethod
    def find_by_abbr(abbr):
        cache_key = LeaveType.LEAVE_TYPE_CACHE_KEY.format(abbr=abbr)
        leave_type = cache.get(cache_key)
        if leave_type:
            return leave_type

        if abbr == Attendance.LOSS_OF_PAY:
            # create dummy Loss of pay leave type
            leave_type = LeaveType(name='Loss of Pay',
                             abbr=Attendance.LOSS_OF_PAY,
                             half_day_abbr=Attendance.LOP_HALF_DAY,
                             mixed_day_abbr='L')
        else:
            leave_type = LeaveType.objects.filter(abbr=abbr).first()

        cache.add(cache_key, leave_type)
        return leave_type

    def __str__(self):
        return self.name


class AllotedLeaveManager(models.Manager):
    def allot_leaves(self, employee, month_year, _type, leaves, comment='Automatically', is_scheduled=False):
        """
        :param employee: (Employee) To whome leaves will be alloted
        :param month_year: (datetime.date()) Its any date from 1-31 of the month to which you wanna assign leaves
        :param _type: (LeaveType) Sick leave / Earned leave
        :param leaves: (Integer) number of leaves you want to assign
        :return: alloted leave object
        """
        month_year = MonthYear(month_year)

        alloted = AllotedLeave.objects \
            .filter(employee=employee,
                    month_year__lte=month_year.get(),
                    type=_type) \
            .order_by('-month_year') \
            .first()


        # if last alloted is month_year is selected month_year then increase the available leaves
        if alloted and alloted.month_year == month_year.get():
            alloted.add_log(brought_forward=alloted.available, new=leaves, comment=comment)
            alloted.available += leaves
        else:
            available = leaves
            if alloted:
                available += alloted.available
            alloted = AllotedLeave(
                employee=employee,
                type=_type,
                available=available,
                month_year=month_year.get()
            )
            alloted.add_log(brought_forward=0, new=leaves, comment=comment)

        # now increase the available of next monthes alloted if any
        AllotedLeave.objects \
            .filter(employee=employee,
                    month_year__gt=month_year.get(),
                    type=_type) \
            .update(available=models.F('available') + leaves)


        if is_scheduled and not _type.carried_forword:
            alloted.available = leaves

        alloted.save()

        # Update the leave summary cache
        alloted.employee.update_leave_summary_cache(month_year)

        return alloted


class AllotedLeave(models.Model):
    """
    Holdes the leaves count of employees
    This table will have only single entry for the combination of employee, leave_type, month_year
    The entry for the selected month_year will be first entry from month_year__lte = selected_month_year
    """
    employee = models.ForeignKey(Employee, on_delete=models.DO_NOTHING, related_name='alloted_leaves')
    type = models.ForeignKey(LeaveType, on_delete=models.DO_NOTHING)
    available = models.FloatField(default=0)
    unapproved = models.FloatField(default=0,
                                   help_text="Waiting for the approval. "
                                             "in case of decline/approval this will be reset to zero(0)")
    availed = models.FloatField(default=0)
    month_year = models.DateField(
                                  help_text='Allocated leaves for the specified month/year. '
                                            'Always save the first date of the month')
    logs = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AllotedLeaveManager()

    @property
    def total_availed(self):
        return self.availed + self.unapproved

    @property
    def total_leaves(self):
        return self.availed + self.unapproved + self.available

    def get_logs(self):
        if self.logs:
            return json.loads(self.logs)
        return []

    def add_log(self, brought_forward, new, comment=''):
        logs = self.get_logs()
        logs.append({
            'date': str(datetime.today().date()),
            'log': "B/F %s, added %s leaves" % (brought_forward, new),
            'comment': comment
        })
        self.logs = json.dumps(logs)


    def __str__(self):
        return "%s %s %s" %(self.month_year, self.type, self.available)

class AppliedLeaves(models.Model):
    FULL_DAY= 1
    HALF_DAY = 0.5

    DAY_TYPES = (
        (FULL_DAY, 'Full Day'),
        (HALF_DAY, 'Half Day')
    )

    employee = models.ForeignKey(Employee, on_delete=models.DO_NOTHING, related_name='applied_leaves')
    type = models.ForeignKey(LeaveType, on_delete=models.DO_NOTHING)
    start_date = models.DateField()
    end_date = models.DateField()
    start_day = models.FloatField(choices=DAY_TYPES, default=FULL_DAY)

    # End day can be equal to or greater than start_day.
    # If End day and Start day is same (hence start_day and end_day value will be same)
    # it means its single day leave
    end_day = models.FloatField(choices=DAY_TYPES, default=FULL_DAY)
    reason = models.CharField(max_length=200)
    approved_at  = models.DateTimeField(blank=True, null=True)
    status_updated_by = models.ForeignKey(Employee, on_delete=models.DO_NOTHING, blank=True, null=True)
    status = models.CharField(max_length=2, choices=LEAVE_STATUS, default=LEAVE_APPROVAL_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def can_approve(self, by, raise_exception=False):
        if self.status not in [LEAVE_APPROVAL_PENDING]:
            if raise_exception:
                raise ValidationError('Sorry can\'t approve the %s leaves' % self.status)
            return False

        self.employee.get_supervisors()

        if not by.has_perm('attendance.can_manage_full_attendance_leaves'):
            if by not in self.employee.get_supervisors():
                if raise_exception:
                    raise ValidationError('Only admin/supervisors can approve the leave.')
                return False

        return True

    def can_decline(self, by, raise_exception=False):
        if self.status not in [LEAVE_APPROVAL_PENDING]:
            if raise_exception:
                raise ValidationError('Sorry can\'t declined the %s leaves' % self.status)
            return False

        return True

    def can_cancel(self, by, raise_exception=False):
        if self.employee == by.employee:
            if self.status != LEAVE_APPROVAL_PENDING:
                if raise_exception:
                    raise ValidationError('Sorry can\'t canceled the %s leaves' % self.status)
                return False
        else:
            if self.status not in [LEAVE_APPROVED]:
                # Cancel by supervision is always after leave approval
                if raise_exception:
                    raise ValidationError('Sorry can\'t canceled the %s leaves' % self.status)
                return False

            if not by.has_perm('attendance.can_manage_full_attendance_leaves'):
                if by not in self.employee.get_supervisors():
                    if raise_exception:
                        raise ValidationError('Only admin/supervisors and applicant can cancel the leave')
                    return False

        return True

    @transaction.atomic
    def approve(self, by):
        if self.can_approve(by, raise_exception=True):
            self.approved_at = datetime.now()
            self.status_updated_by = by.employee
            self.status = LEAVE_APPROVED

            attendance_as_leave_queryset = self.leave_days\
                .filter(leave_status=LEAVE_APPROVAL_PENDING)

            leaves_per_month = {}

            for attendance in attendance_as_leave_queryset:
                if attendance.leave_type1 not in [Attendance.LOSS_OF_PAY, Attendance.LOP_HALF_DAY]:
                    month_year = MonthYear(attendance.date)
                    if month_year not in leaves_per_month:
                        leaves_per_month[month_year] = 0
                    leaves_per_month[month_year] += attendance.leave_type1_value

            attendance_as_leave_queryset.update(leave_status=LEAVE_APPROVED)

            self.save()

            for month_year, leave_count in leaves_per_month.items():
                AllotedLeave.objects \
                    .filter(employee=self.employee,
                            type=self.type,
                            month_year__gte=month_year.first_date(),
                            month_year__lte=month_year.last_date()) \
                    .update(unapproved=models.F('unapproved') - leave_count,
                            availed=models.F('availed') + leave_count)

            # Update the leave summary cache
            self.employee.update_leave_summary_cache(self.start_date)

            LeaveLog(
                applied_leave=self,
                log_type=LEAVE_APPROVED,
                added_by=by.employee
            ).save()

    @transaction.atomic
    def decline(self, by, reason):
        if self.can_decline(by, raise_exception=True):
            self._cancel(by, reason=reason, new_status=LEAVE_DECLINED)

    @transaction.atomic
    def cancel(self, by, reason):
        # Cancel by supervision is always leave approval
        if self.can_cancel(by, raise_exception=True):
            if self.employee == by.employee:
                return self._cancel_by_applicant(by, reason)

            self._cancel(by, reason=reason)


    def _cancel_by_applicant(self, by, reason):
        attendance_as_leave_queryset = self.leave_days.all()

        leaves_per_month = {}
        for attendance in attendance_as_leave_queryset:
            if attendance.leave_type1 not in [Attendance.LOSS_OF_PAY, Attendance.LOP_HALF_DAY]:
                month_year = MonthYear(attendance.date)
                if month_year not in leaves_per_month:
                    leaves_per_month[month_year] = 0
                leaves_per_month[month_year] += attendance.leave_type1_value

        attendance_as_leave_queryset.update(leave_status=LEAVE_CANCELED,
                                            leave_type1=None,
                                            leave_type1_value=None,
                                            leave_type2=None,
                                            leave_type2_value=None)

        self.status_updated_by = by.employee
        self.status = LEAVE_CANCELED
        self.save()

        for month_year, leave_count in leaves_per_month.items():
            AllotedLeave.objects\
                .filter(employee=self.employee,
                        type=self.type,
                        month_year__gte=month_year.first_date(),
                        month_year__lte=month_year.last_date())\
                .update(available=models.F('available') + leave_count,
                        unapproved=models.F('unapproved') - leave_count)

        LeaveLog(
            applied_leave=self,
            log_type=LEAVE_CANCELED,
            added_by=by.employee,
            log=reason,
        ).save()

    def _cancel(self, by, reason, new_status=LEAVE_CANCELED):
        if new_status not in [LEAVE_CANCELED, LEAVE_DECLINED]:
            raise ValidationError('Wrong status selection for canceling a leave')

        attendance_as_leave_queryset = self.leave_days \
            .filter(leave_status=self.status)

        leaves_per_month = {}

        for attendance in attendance_as_leave_queryset:
            if attendance.leave_type1 not in [Attendance.LOSS_OF_PAY, Attendance.LOP_HALF_DAY]:
                month_year = MonthYear(attendance.date)
                if month_year not in leaves_per_month:
                    leaves_per_month[month_year] = 0
                leaves_per_month[month_year] += attendance.leave_type1_value

        attendance_as_leave_queryset.update(leave_status=new_status,
                                            leave_type1=None,
                                            leave_type1_value=None,
                                            leave_type2=None,
                                            leave_type2_value=None)

        self.status_updated_by = by.employee
        self.status = new_status
        self.save()

        for month_year, leave_count in leaves_per_month.items():
            alloted_leaves = AllotedLeave.objects\
                .filter(employee=self.employee,
                        type=self.type,
                        month_year__gte=month_year.first_date(),
                        month_year__lte=month_year.last_date())

            if new_status == LEAVE_CANCELED:
                # Cancel by supervision is always after leave approval
                # So transfer the leaves from availed to available
                alloted_leaves.update(availed=models.F('availed') - leave_count,
                                      available=models.F('available') + leave_count)
            else:
                # Declined case
                # Declined by supervisor is when leave is in pending state
                # So transfer the leaves from unapproved to available
                alloted_leaves.update(unapproved=models.F('unapproved') - leave_count,
                                      available=models.F('available') + leave_count)


        # Update the leave summary cache
        self.employee.update_leave_summary_cache(self.start_date)

        LeaveLog(
            applied_leave=self,
            log_type=new_status,
            added_by=by.employee,
            log=reason,
        ).save()


    def back_to_panding(self):
        """
        Turns back the Approved leaves to the Pending state,
        Hence incrase the count of unapproved and decrease the count of availed in alloted leaves

        Use case 1: Emp applied leave for 12 Aug 21 He got approval for supervision
        Then he applied one more leave for 13 Augh 21, This will merge 12 Aug and 13 Aug leaves in
        sigle applied leave application with status as Pending Approval

        Use case 2: Leaves are already approved and employee has applied more more leaves
        but it makes the sandwith with already approved leaves
        :return: None
        """
        if self.status == LEAVE_APPROVED:
            attendance_as_leave_queryset = self.leave_days \
                .filter(leave_status=self.status)

            leaves_per_month = {}

            for attendance in attendance_as_leave_queryset:
                if attendance.leave_type1 not in [Attendance.LOSS_OF_PAY, Attendance.LOP_HALF_DAY]:
                    month_year = MonthYear(attendance.date)
                    if month_year not in leaves_per_month:
                        leaves_per_month[month_year] = 0
                    leaves_per_month[month_year] += attendance.leave_type1_value

            attendance_as_leave_queryset.update(leave_status=LEAVE_APPROVAL_PENDING)

            self.status = LEAVE_APPROVAL_PENDING
            self.save()

            for month_year, leave_count in leaves_per_month.items():
                AllotedLeave.objects \
                    .filter(employee=self.employee,
                            type=self.type,
                            month_year__gte=month_year.first_date(),
                            month_year__lte=month_year.last_date()) \
                    .update(unapproved=models.F('unapproved') + leave_count,
                            availed=models.F('availed') - leave_count)


class LeaveLog(models.Model):
    applied_leave = models.ForeignKey(AppliedLeaves, on_delete=models.DO_NOTHING)
    log_type = models.CharField(max_length=50,
                                choices=[(log_type[0], log_type[1]) for log_type in LEAVE_STATUS],
                                default=LEAVE_APPROVAL_PENDING)
    log = models.TextField()
    added_by = models.ForeignKey(Employee, on_delete=models.DO_NOTHING, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)