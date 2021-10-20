import datetime
from django.http import Http404
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, mixins, permissions, status
from dsr.api import Pagination
from timelog.models import Holiday
from timelog.serializers import HolidaySerializer
from attendance.models import AppliedLeaves, Employee, LeaveType
from .serializers import (EmployeesAttendanceSerializer, ApplyLeaveSerializer, ApproveLeaveSerializer,
                          ListLeaveSerializer, LeaveTypeSerializer, DeclineLeaveSerializer)

class AttendanceAPI(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Employee.objects.filter(status=Employee.CONFIRMED)
    def get_serializer_class(self):
        if self.action == 'list':
            return EmployeesAttendanceSerializer

    def list(self, request):
        today = datetime.datetime.today()
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))

        employees = Employee.objects.attendances(self.request.user, month, year)
        serializer = EmployeesAttendanceSerializer(employees, many=True)
        holidays = Holiday.objects.year(year)
        holidays_serializer = HolidaySerializer(holidays, many=True)
        return Response({'attendances': serializer.data,
                         'holidays': holidays_serializer.data},
                        status=200)


class LeaveAPI(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = AppliedLeaves.objects.all()
    pagination_class = Pagination

    def get_serializer_class(self):
        if self.action == 'create':
            return ApplyLeaveSerializer
        if self.action == 'pending':
            return ListLeaveSerializer
        if self.action == 'approve':
            return ApproveLeaveSerializer
        if self.action in ['decline', 'cancel']:
            return DeclineLeaveSerializer

    def create(self, request, *args, **kwargs):
        serialized = ApplyLeaveSerializer(data=request.data, applied_by=request.user)

        if serialized.is_valid(raise_exception=True):
            leave = serialized.apply_leave()
            serializer = ApplyLeaveSerializer(leave, applied_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['GET'], detail=False)
    def team(self, request):
        _filter = {}
        if not request.user.has_perm('attendance.can_manage_full_attendance_leaves'):
            team_employee_ids = [emp.pk for emp in request.user.employee.get_team()]
            _filter['employee_id__in'] = set(team_employee_ids)

        if request.GET.get('status', None):
            if request.GET.get('status') == 'C':
                _filter['status__in'] = ['C', 'D']
            else:
                _filter['status'] = request.GET.get('status')

        applied_leaves = AppliedLeaves.objects\
            .prefetch_related('type', 'leave_days', 'employee__user')\
            .filter(**_filter)\
            .order_by('-id')

        page = self.paginate_queryset(applied_leaves)
        if page is not None:
            serializer = ListLeaveSerializer(page, accessed_by=request.user, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ListLeaveSerializer(applied_leaves, accessed_by=request.user, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    @action(methods=['GET'], detail=False)
    def mine(self, request):

        _filter = {
            'employee': request.user.employee
        }

        if request.GET.get('status', None):
            if request.GET.get('status') == 'C':
                _filter['status__in'] = ['C', 'D']
            else:
                _filter['status'] = request.GET.get('status')

        applied_leaves = AppliedLeaves.objects \
            .prefetch_related('type', 'leave_days', 'employee__user') \
            .filter(**_filter)\
            .order_by('-id')

        page = self.paginate_queryset(applied_leaves)
        if page is not None:
            serializer = ListLeaveSerializer(page, accessed_by=request.user, many=True)
            return self.get_paginated_response(serializer.data)

        serialized = ListLeaveSerializer(applied_leaves, accessed_by=request.user, many=True)
        return Response(serialized.data, status.HTTP_200_OK)

    @action(methods=['PUT'], detail=True)
    def approve(self, request, pk):
        # TODO check if employee is a team member of current user
        applied_leaves = AppliedLeaves.objects.filter(pk=pk).first()
        if applied_leaves:
            serialized = ApproveLeaveSerializer(data=request.data)
            if serialized.is_valid(raise_exception=True):
                applied_leaves = serialized.approve(applied_leaves, request.user)
                serialized = ListLeaveSerializer(applied_leaves, accessed_by=request.user)
                return Response(serialized.data, status=status.HTTP_200_OK)
        else:
            raise Http404


    @action(methods=['PUT'], detail=True)
    def decline(self, request, pk):
        # TODO check if employee is a team member of current user
        applied_leaves = AppliedLeaves.objects.filter(pk=pk).first()
        if applied_leaves:
            serialized = DeclineLeaveSerializer(data=request.data)
            if serialized.is_valid(raise_exception=True):
                applied_leaves = serialized.decline(applied_leaves, request.user)
                serialized = ListLeaveSerializer(applied_leaves, accessed_by=request.user)
                return Response(serialized.data, status=status.HTTP_200_OK)
        else:
            raise Http404

    @action(methods=['PUT'], detail=True)
    def cancel(self, request, pk):
        # TODO check if employee is a team member of current user
        applied_leaves = AppliedLeaves.objects.filter(pk=pk).first()
        if applied_leaves:
            serialized = DeclineLeaveSerializer(data=request.data)
            if serialized.is_valid(raise_exception=True):
                applied_leaves = serialized.cancel(applied_leaves, request.user)
                serialized = ListLeaveSerializer(applied_leaves, accessed_by=request.user)
                return Response(serialized.data, status=status.HTTP_200_OK)
        else:
            raise Http404


class LeaveTypeAPI(viewsets.GenericViewSet):
    queryset = LeaveType.objects.all()
    def get_serializer_class(self):
        return LeaveTypeSerializer

    @action(methods=['GET'], detail=False)
    def leaves(self, request):
        today = datetime.datetime.today()
        leave_types = LeaveType.objects.all()
        leave_types_serializer = LeaveTypeSerializer(leave_types, many=True)

        holidays = Holiday.objects.year(today.year)
        holidays_serializer = HolidaySerializer(holidays, many=True)

        month_year = datetime.date(today.year, today.month, 1)
        # Typecase employee object to class attendance.models.Employee
        # so that we can access prepare_leave_summary method
        request.user.employee.__class__ = Employee

        leave_summary = request.user.employee.prepare_leave_summary(month_year=month_year)
        application_last_date = datetime.date(today.year, today.month, 3)
        return Response({'leave_types': leave_types_serializer.data,
                         'leave_summary': leave_summary,
                         'application_last_date': application_last_date,
                         'holidays': holidays_serializer.data},
                        status=200)
