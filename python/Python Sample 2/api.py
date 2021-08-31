from django.core.exceptions import PermissionDenied
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from dsr.api import Pagination
from account.models import Department
from leads.models import Lead, Status
from .serializers import LeadListSerializer, LeadUpdateSerializer, LeadChangeDeptSerializer, LeadAcceptSerializer, \
    LeadRejectSerializer, DepartmentSerializer, LeadHelpDeptSerializer, BDLeadDetailSerializer, StatusSerializer

# http://gitlab.zapbuild.com/zapbuild/teamsquare/blob/followup/

class LeadView(mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   viewsets.GenericViewSet):
    queryset = Lead.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('status',)
    pagination_class = Pagination

    def get_serializer_class(self):
        if self.action == 'list':
            return LeadListSerializer

        if self.action == 'retrieve':
            return LeadListSerializer

        if self.action == 'update':
            return LeadUpdateSerializer

        if self.action == 'partial_update':
            return LeadUpdateSerializer

        if self.action == 'assign_dept':
            return LeadChangeDeptSerializer

        if self.action == 'assign_helpdept':
            return LeadHelpDeptSerializer

        if self.action == 'accept':
            return LeadAcceptSerializer

        if self.action == 'departments':
            return DepartmentSerializer

        if self.action == 'reject' or self.action == 'close':
            return LeadRejectSerializer

        return LeadUpdateSerializer

    def get_queryset(self):
        if self.request:
            self.queryset = Lead.objects.accessed_by(self.request.user).order_by('-updated_at')
        return self.queryset

    def retrieve(self, request, pk=None):
        try:
            lead = Lead.objects\
                .accessed_by(request.user)\
                .get(pk=pk)
            serialized = LeadListSerializer(lead, accessed_by=request.user)
            return Response(serialized.data)
        except:
            raise Http404

    def list(self, request):
        order_by = '-updated_at'

        _filter = {
            # 'status': request.query_params.get('status')
        }

        leads = Lead.objects \
            .filter(**_filter) \
            .accessed_by(request.user) \
            .order_by(order_by)

        page = self.paginate_queryset(leads)
        if page is not None:
            serializer = self.get_serializer(page, accessed_by=request.user, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(leads, accessed_by=request.user, many=True)
        return Response(serializer.data, status=200)

    @action(methods=['GET'], detail=False)
    def departments(self, request):
        departments = Department.objects.filter(parent=None,
                                                permissions__codename='can_process_lead',
                                                permissions__content_type__model='lead',
                                                permissions__content_type__app_label='leads')
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['PUT'], detail=True)
    def assign_dept(self, request, pk):
        lead = Lead.objects.accessed_by(request.user).filter(pk=pk).first()
        if lead:
            serialized = LeadChangeDeptSerializer(data=request.data)
            if serialized.is_valid(raise_exception=True):
                lead = serialized.assign_dept(lead, request.user)
                serializer = LeadListSerializer(lead, accessed_by=request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            raise Http404

    @action(methods=['PUT'], detail=True)
    def assign_helpdept(self, request, pk):
        lead = Lead.objects.accessed_by(request.user).filter(pk=pk).first()
        if lead:
            serialized = LeadHelpDeptSerializer(data=request.data)
            if serialized.is_valid(raise_exception=True):
                lead = serialized.assign_dept(lead, request.user)
                serializer = LeadListSerializer(lead, accessed_by=request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            raise Http404


    @action(methods=['PUT'], detail=True)
    def accept(self, request, pk):
        lead = Lead.objects.accessed_by(request.user).filter(pk=pk).first()
        if lead:
            serialized = LeadAcceptSerializer(data=request.data)
            if serialized.is_valid(raise_exception=True):
                ticket = serialized.accept(lead, request.user)
                serialized = LeadListSerializer(ticket, accessed_by=request.user)
                return Response(serialized.data)
        else:
            raise Http404

    @action(methods=['PUT'], detail=True)
    def reject(self, request, pk):
        lead = Lead.objects.accessed_by(request.user).filter(pk=pk).first()
        if lead:
            serialized = LeadRejectSerializer(data=request.data)
            if serialized.is_valid(raise_exception=True):
                ticket = serialized.reject(lead, request.user)
                serialized = LeadListSerializer(ticket, accessed_by=request.user)
                return Response(serialized.data)
        else:
            raise Http404

    @action(methods=['PUT'], detail=True)
    def close(self, request, pk):
        lead = Lead.objects.accessed_by(request.user).filter(pk=pk).first()
        if lead:
            serialized = LeadRejectSerializer(data=request.data)
            if serialized.is_valid(raise_exception=True):
                ticket = serialized.close(lead, request.user)
                serialized = LeadListSerializer(ticket, accessed_by=request.user)
                return Response(serialized.data)
        else:
            raise Http404



class BDLeadView(mixins.RetrieveModelMixin,
               viewsets.GenericViewSet):

    queryset = Lead.objects.all()

    def get_queryset(self):
        self.queryset = Lead.objects.leads(self.request.user)
        return self.queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return LeadListSerializer
        elif self.action == 'retrieve':
            return BDLeadDetailSerializer
        return super(BDLeadView, self).get_serializer_class()

    def _create(self, request):
        """Create new lead
        prospect: { "full_name": "Naresh Kumar",
                    "emails": [{"email": "nareshkumar@zapbuild.com"}],
                    "phones":[{"phone": "9888573673"}, {"phone": "1234567890"}]
                    }
        """
        # serialized = LeadCreateSerializer(data=request.data)
        # if serialized.is_valid(raise_exception=True):
        #     lead = serialized.create(by=request.user)
        #     serialized = LeadListSerializer(lead)
        # return Response(serialized.data, status=200)

    @action(methods=['GET'], detail=False)
    def statuses(self, request):
        statuses = Status.objects.list()
        serialized = StatusSerializer(statuses, many=True, accessed_by=request.user)
        return Response(serialized.data, status=200)

    @action(methods=['GET'], detail=False)
    def all_statuses(self, request):
        statuses = Status.objects.list(all=True)
        serialized = StatusSerializer(statuses, many=True, accessed_by=request.user)
        return Response(serialized.data, status=200)

    @action(methods=['GET'], detail=False)
    def reminder_summary(self, request):
        reminders = Lead.objects.reminder_summary(request.user)
        return Response(list(reminders), status=200)