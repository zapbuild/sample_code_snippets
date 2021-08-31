import re
from django.db.models import Sum
from rest_framework import serializers
from django.core.exceptions import ValidationError
from rest_framework.exceptions import ValidationError as APIValidationError

from account.models import Group, Department
from leads.models import Lead, LeadStatus, BDLead, Action, Status


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ('id', 'name')

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name')


class LeadListSerializer(serializers.ModelSerializer):
    department = GroupSerializer()
    permissions = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    source = serializers.SerializerMethodField()

    def get_permissions(self, lead):
        return {
            'can_reject': lead.can_reject(self.accessed_by),
            'can_accept': lead.can_accept(self.accessed_by),
            'can_close': lead.can_close(self.accessed_by),
            'can_change_dept': lead.can_change_dept(self.accessed_by)
        }

    def __init__(self, *args, **kwargs):
        try:
            self.accessed_by = kwargs.pop('accessed_by')
        except Exception as e:
            self.accessed_by = None
        super(LeadListSerializer, self).__init__(*args, **kwargs)

    def get_status(self, lead):
        status = LeadStatus(lead.status)

        # Format status value for frontend use
        # e.g if status is InProgress convert it into In Progress
        return re.sub("([a-z])([A-Z])", r'\g<1> \g<2>', status.name)

    def get_source(self, lead):
        return lead.source.title()

    class Meta:
        model = Lead
        fields = '__all__'

class LeadUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        exclude = ('text', 'uid', 'source',)


class LeadChangeDeptSerializer(serializers.ModelSerializer):
    def assign_dept(self, lead, by):
        try:
            lead.assign_dept(by=by, department=self.validated_data.get('department'))
            return lead
        except ValidationError as e:
            raise APIValidationError(e.message)

    class Meta:
        model = Lead
        fields = ("department",)


class LeadHelpDeptSerializer(serializers.ModelSerializer):
    def assign_dept(self, lead, by):
        try:
            lead.assign_helpdept(by=by,
                                 helpticket_id=self.validated_data.get('helpticket_id'),
                                 helpticket_department=self.validated_data.get('helpticket_department'))
            return lead
        except ValidationError as e:
            raise APIValidationError(e.message)

    class Meta:
        model = Lead
        fields = ("helpticket_id", 'helpticket_department',)

class LeadAcceptSerializer(serializers.ModelSerializer):
    def accept(self, lead, by):
        try:
            lead.accept(
                by=by
            )
            return lead
        except ValidationError as e:
            raise APIValidationError(e.message)

    class Meta:
        model = Lead
        fields = ()

class LeadRejectSerializer(serializers.ModelSerializer):
    note = serializers.CharField(required=True)
    def reject(self, lead, by):
        try:
            lead.reject(
                by=by,
                note=self.validated_data.get('note')
            )
            return lead
        except ValidationError as e:
            raise APIValidationError(e.message)

    def close(self, lead, by):
        try:
            lead.close(
                by=by,
                note=self.validated_data.get('note')
            )
            return lead
        except ValidationError as e:
            raise APIValidationError(e.message)

    class Meta:
        model = Lead
        fields = ('note',)



class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = ('name', 'key', 'note_required', 'next_status',)

class StatusSerializer(serializers.ModelSerializer):
    actions = ActionSerializer(many=True)
    total_leads = serializers.SerializerMethodField()
    total_budget = serializers.SerializerMethodField()
    def __init__(self, *args, **kwargs):
        try:
            self.accessed_by = kwargs.pop('accessed_by')
        except Exception as e:
            self.accessed_by = None
        super(StatusSerializer, self).__init__(*args, **kwargs)
    class Meta:
        model = Status
        fields = ('id', 'name', 'key', 'actions', 'total_leads', 'total_budget')
    def get_total_leads(self, status):
        return BDLead.objects.leads(self.accessed_by).filter(status=status).count()
    def get_total_budget(self, status):
        calc = BDLead.objects.leads(self.accessed_by)\
            .filter(status=status)\
            .aggregate(total_budget=Sum('estimated_budget'))
        total_budget = calc['total_budget'] if calc['total_budget'] else 0
        return total_budget

class BDLeadDetailSerializer(serializers.ModelSerializer):
    # status = LeadStatusSerializer()
    # prospect = ClientSerializer()
    # source = LeadSourceSerializer()
    # assigned_to = EmployeeSerializer()
    # comments = CommentSerializer(many=True)
    class Meta:
        model = BDLead
        fields = '__all__'