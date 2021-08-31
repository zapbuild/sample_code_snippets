from collections import OrderedDict
from rest_framework import serializers
from django.core.exceptions import ValidationError
from account.models import User
from attendance.models import Attendance, Employee, AppliedLeaves, LeaveType, LEAVE_STATUS
from attendance.models import LEAVE_APPROVED, LEAVE_APPROVAL_PENDING, LEAVE_DECLINED
from attendance.leave_application import LeaveApplication
from attendance.signals import leave_applied, leave_approved, leave_declined, leave_canceled

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name')

class AttendanceSerializer(serializers.ModelSerializer):
    day_status = serializers.SerializerMethodField()
    day_value = serializers.SerializerMethodField()

    def get_day_status(self, obj):
        return obj.day_status[0]

    def get_day_value(self, obj):
        return obj.day_status[1]

    class Meta:
        model = Attendance
        fields = ('pk', 'date', 'start_time', 'end_time', 'duration', 'day_status', 'day_value')


class EmployeesAttendanceSerializer(serializers.ModelSerializer):
    user = EmployeeSerializer()
    attendance = serializers.SerializerMethodField()

    def get_attendance(self, employee):
        data = OrderedDict()
        for date, attendance in employee.attendance_table.items():
            data[str(date)] = AttendanceSerializer(attendance).data
        return data

    class Meta:
        model = Employee
        fields = ('user', 'empid', 'attendance', 'leave_summary', 'credited_days', 'short_leaves', 'absent')


class ApplyLeaveSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        try:
            self.applied_by = kwargs.pop('applied_by')
        except Exception as e:
            self.applied_by = None
        super(ApplyLeaveSerializer, self).__init__(*args, **kwargs)

    def validate(self, data):
        # Start date should always be smaller than enddate
        if data.get('start_date') > data.get('end_date'):
            raise serializers.ValidationError({'end_date': 'End date should always be greater thant start date'})
        is_start_date_exist = AppliedLeaves.objects.filter(
            employee=self.applied_by.employee,
            start_date__lte=data.get('start_date'),
            end_date__gte=data.get('start_date'),
            status__in=[LEAVE_APPROVED, LEAVE_APPROVAL_PENDING, LEAVE_DECLINED])

        is_start_end_exist = AppliedLeaves.objects.filter(
            employee=self.applied_by.employee,
            start_date__lte=data.get('end_date'),
            end_date__gte=data.get('end_date'),
            status__in = [LEAVE_APPROVED, LEAVE_APPROVAL_PENDING, LEAVE_DECLINED])

        is_start_end_exist_middle = AppliedLeaves.objects.filter(
            employee=self.applied_by.employee,
            start_date__lte=data.get('end_date'),
            end_date__gte=data.get('start_date'),
            status__in=[LEAVE_APPROVED, LEAVE_APPROVAL_PENDING, LEAVE_DECLINED])

        date_exists_queryset = is_start_date_exist | is_start_end_exist | is_start_end_exist_middle

        if date_exists_queryset:
            dates = ', '.join(["%s - %s" % (applied.start_date, applied.end_date) for applied in date_exists_queryset])
            raise serializers.ValidationError({'start_date': "The leaves for dates %s are already applied" % dates})

        return data


    def apply_leave(self):
        attendance_mgr = LeaveApplication(self.applied_by.employee,
                                          self.validated_data.get('type'),
                                          self.validated_data.get('start_date'),
                                          self.validated_data.get('end_date'),
                                          self.validated_data.get('start_day'),
                                          self.validated_data.get('end_day'),
                                          self.validated_data.get('reason'),
                                          )

        employee_leaves = attendance_mgr.prepare_leaves()
        paid_leaves_month_year = attendance_mgr.mark_paid_leaves()
        attendance_mgr.update_alloted_leaves(paid_leaves_month_year)
        self.leave = attendance_mgr.create_leaves()

        for m in employee_leaves:
            for attendance in employee_leaves[m]:
                attendance.applied_leave = self.leave
                attendance.save()

        # Update the leave summary cache
        # first of all Cast the account.models.employee object with attendance.models.Employee
        self.applied_by.employee.__class__ = Employee
        self.applied_by.employee.update_leave_summary_cache(self.leave.start_date)

        leave_applied.send(sender=ApplyLeaveSerializer, leave=self.leave)
        return self.leave

    class Meta:
        model = AppliedLeaves
        fields = ('type', 'start_date', 'end_date', 'start_day', 'end_day', 'reason')



class ApproveLeaveSerializer(serializers.Serializer):
    def approve(self, applied_leave, by):
        try:
            applied_leave.approve(
                by=by
            )
            leave_approved.send(sender=ApplyLeaveSerializer, leave=applied_leave, by=by)
            return applied_leave
        except ValidationError as e:
            raise serializers.ValidationError({'non_field_errors': [e.message]})




class DeclineLeaveSerializer(serializers.Serializer):
    reason = serializers.CharField()
    def decline(self, applied_leave, by):
        try:
            reason = self.validated_data.get('reason', None)
            applied_leave.decline(
                by=by,
                reason=reason
            )
            leave_declined.send(sender=ApplyLeaveSerializer, leave=applied_leave, reason=reason, by=by)
            return applied_leave
        except ValidationError as e:
            raise serializers.ValidationError({'non_field_errors': [e.message]})

    def cancel(self, applied_leave, by):
        try:
            reason = self.validated_data.get('reason', None)
            applied_leave.cancel(
                by=by,
                reason=reason
            )
            leave_canceled.send(sender=ApplyLeaveSerializer, leave=applied_leave, reason=reason, by=by)
            return applied_leave
        except ValidationError as e:
            raise serializers.ValidationError({'non_field_errors': [e.message]})


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ('pk', 'full_name', 'empid')

class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = ('pk', 'name', 'abbr')


class LeaveSerializer(serializers.ModelSerializer):
    day_status = serializers.SerializerMethodField()

    def get_day_status(self, obj):
        return obj.leave_type[0]

    class Meta:
        model = Attendance
        fields = ('pk', 'date', 'start_time', 'end_time', 'duration', 'day_status')

class ListLeaveSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer()
    leave_days = LeaveSerializer(many=True)
    type = LeaveTypeSerializer()
    status = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    def get_permissions(self, ticket):
        return {
            'can_approve': ticket.can_approve(self.accessed_by),
            'can_decline': ticket.can_decline(self.accessed_by),
            'can_cancel': ticket.can_cancel(self.accessed_by),
        }

    def __init__(self, *args, **kwargs):
        try:
            self.accessed_by = kwargs.pop('accessed_by')
        except Exception as e:
            self.accessed_by = None

        super(ListLeaveSerializer, self).__init__(*args, **kwargs)

    def get_status(self, leave):
        for status in LEAVE_STATUS:
            if status[0] == leave.status:
                return status[1]
        return '-'

    class Meta:
        model = AppliedLeaves
        fields = ('pk', 'employee', 'type', 'start_date', 'end_date', 'leave_days', 'status', 'permissions')
