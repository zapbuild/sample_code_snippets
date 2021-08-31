import re, requests
from os.path import join

from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as APIValidationError

from util.common import de_emojify
from departments.models import Department
from departments.serializers import DepartmentSerializer as DepartmentSerializerToBeRemoved
from .file_handler import FileHelper
from .models import Ticket, Comment, TicketLog, TicketRating, TicketStatus, TicketAttachment
from .signals import ticket_generated


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ('id', 'name', 'description', 'acceptance_duration',)


class TicketCreateSerializer(serializers.ModelSerializer):
    attachment_urls = serializers.JSONField(required=False, help_text='List of urls e.g ["http://zapbuild.com/a.png"] '
                                                                      'use case is GupSup chat bot')
    question = serializers.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(TicketCreateSerializer, self).__init__(*args, **kwargs)
        self.fields['phone'].required = False


    @staticmethod
    def _predict_department_id(by, detail):
        department_id = settings.PC_DEPT_ID
        try:
            response = requests.get(settings.HELPTICKET_AI_URL + '/?details=' + detail)
            json_data = response.json()
            department_id = json_data['data']
        except:
            pass

        # in case user belongs to department and tries to increase his performance index by
        # creating the ticket for his department and resolve it immediately, in that case
        # assign that ticket to PC
        if by.help_department and department_id == by.help_department.department.id:
            department_id = settings.PC_DEPT_ID

        return department_id

    def create(self, by, attachments, *args, **kwargs):
        try:
            attachment_urls = None
            try:
                attachment_urls = self.validated_data.pop('attachment_urls')
            except:
                pass

            question = self.validated_data.get('question', None)

            if self.validated_data.get('department', None):
                department_id = self.validated_data.get('department').id
            elif question and question == '4':
                # Question 4 is COVID-19 related ticket so assign Hardcoded department id i.e. 6 for COVID-19 NGO
                department_id = 6
            else:
                department_id = TicketCreateSerializer._predict_department_id(by, self.validated_data.get('detail'))

            ticket = Ticket(
                name=("%s %s" % (by.first_name, by.last_name)).strip(),
                email='' if by.is_external_contact else by.email,
                phone=self.validated_data.get('phone', by.mobile),
                urgency_level=self.validated_data.get('urgency_level'),
                department_id=department_id,
                detail=de_emojify(self.validated_data.get('detail')),
            )

            if by.is_external_contact:
                ticket.created_by_external_id = by.id
            else:
                ticket.created_by_id = by.id

            ticket.save()

            FileHelper.upload(ticket.id, attachments)
            if attachment_urls:
                FileHelper.download(ticket.id, attachment_urls)
            try:
                ticket_generated.send(sender=TicketCreateSerializer, ticket=ticket, by=by)
            except Exception as e:
                print(e)

            return ticket
        except Exception as e:
            raise serializers.ValidationError(e)

    class Meta:
        model = Ticket
        fields = ('phone', 'urgency_level', 'detail', 'department', 'attachment_urls', 'question',)


class CommentAddSerializer(serializers.ModelSerializer):
    def add(self, ticket, added_by):
        if ticket.status in [TicketStatus.Completed.value, TicketStatus.Completed.value]:
            raise serializers.ValidationError("Ticket is closed.")

        comment = Comment(
            content_object=ticket,
            added_by_name=added_by.full_name,
            comment_type=self.data.get('comment_type', None),
            body=de_emojify(self.data.get('body'))
        )

        if added_by.is_external_contact:
            comment.added_by_external_id = added_by.id
        else:
            comment.added_by_id = added_by.id

        comment.save()
        return comment

    class Meta:
        model = Comment
        fields = ('comment_type', 'body')


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'


class CommentAddedSerializer(CommentSerializer):
    """
    for: Get List of relevant employees related to ticket.
    param: ticket id
    return: List of relevant employees related to ticket.
    """
    visible_to = serializers.SerializerMethodField()
    wa_notifiacatins = serializers.SerializerMethodField()

    def get_wa_notifiacatins(self, obj):
        ticket = Ticket.objects.get(pk=obj.object_id)
        return {
            'owner': ticket.phone if obj.added_by_id != ticket.created_by_id else None,
            'whatsapp_group': {
                'name': ticket.department.whatsapp_group,
                'admin': ticket.department.whatsapp_group_admin
            }
        }

    def get_visible_to(self, obj):
        ticket = Ticket.objects.get(pk=obj.object_id)

        visible_to = []
        if ticket.created_by_id:
            visible_to += [ticket.created_by_id]

        if not ticket.assigned_to_id:
            visible_to += [emp['employee_id'] for emp in
                           ticket.department.department_employees.values('employee_id').all()]
        else:
            visible_to.append(ticket.assigned_to_id)
        return visible_to


class RatingSerializer(serializers.ModelSerializer):
    rating = serializers.SerializerMethodField(method_name='access_denied')
    comment = serializers.SerializerMethodField(method_name='access_denied')

    def __init__(self, *args, **kwargs):
        try:
            accessed_by = kwargs.pop('accessed_by')
            if accessed_by.is_process_coordinator or accessed_by.has_permission(
                    'account.can_check_helpdesk_all_tickets'):
                self.fields['rating'] = serializers.DecimalField(max_digits=2, decimal_places=1)
                self.fields['comment'] = serializers.CharField(max_length=250)
        except:
            pass  # Do nothing

        super(RatingSerializer, self).__init__(*args, **kwargs)

    def access_denied(self, obj):
        return None

    class Meta:
        model = TicketRating
        fields = ('rating', 'comment')


class MyRatingSerializer(serializers.ModelSerializer):
    """
    Only for those ratings whose 
    ticket.created_by_id == ticket accessed_by_id (current user/loggedin user)
    """

    class Meta:
        model = TicketRating
        fields = ('created_at', 'rating', 'comment')


class TicketAttachmentSerializer(serializers.ModelSerializer):
    image_path = serializers.SerializerMethodField()

    class Meta:
        model = TicketAttachment
        fields = ('id', 'original_name', 'uuid_name', 'image_path')

    def get_image_path(self, obj):
        return join(settings.MEDIA_URL, 'tickets/{0}'.format(obj.uuid_name))


class TicketSerializer(serializers.ModelSerializer):
    ticket_rating = RatingSerializer()
    department = DepartmentSerializerToBeRemoved()
    urgency_level = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    attachments = TicketAttachmentSerializer(source='ticket_attachment', many=True)
    assigned_to = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    def get_permissions(self, ticket):
        return {
            'can_reject': ticket.can_reject(self.accessed_by),
            'can_accept': ticket.can_accept(self.accessed_by),
            'can_add_estimates': ticket.can_add_estimates(self.accessed_by),
            'can_close': ticket.can_close(self.accessed_by),
            'can_mark_done': ticket.can_mark_done(self.accessed_by),
            'can_change_dept': ticket.can_change_dept(self.accessed_by),
            'can_comment': ticket.can_comment(self.accessed_by),
        }

    def __init__(self, *args, **kwargs):
        try:
            self.accessed_by = kwargs.pop('accessed_by')
            if 'ticket_rating' in self.__class__.Meta.fields:
                self.fields['ticket_rating'] = RatingSerializer(accessed_by=self.accessed_by)
        except Exception as e:
            self.accessed_by = None

        super(TicketSerializer, self).__init__(*args, **kwargs)

    def get_assigned_to(self, ticket):
        if ticket.assigned_to:
            return ticket.assigned_to.name

    def get_urgency_level(self, ticket):
        status = {level[0]: level[1] for level in Ticket.URGENCY_LEVEL}
        return status[ticket.urgency_level]

    def get_status(self, ticket):
        if self.accessed_by:
            if self.accessed_by.id == ticket.created_by_id \
                    and ticket.status == TicketStatus.Rejected.value:
                # if the user who is accessing the ticket == the user who had created that ticket
                # and ticket is status is rejected, show him the ticket is Pending.
                # We dont want to show him that ticket is rejected by department.
                # PC will handle it and assign it to other department.
                status = TicketStatus.Pending
            else:
                status = TicketStatus(ticket.status)
        else:
            status = TicketStatus(ticket.status)

        # Format status value for frontend use
        # e.g if status is InProgress convert it into In Progress
        return re.sub("([a-z])([A-Z])", "\g<1> \g<2>", status.name)

    class Meta:
        model = Ticket
        fields = (
            'id', 'email', 'name', 'accepted_at', 'estimated_hrs', 'status', 'phone', 'urgency_level', 'department', \
            'detail', 'remaining_time', 'deadline', 'to_be_accepted_by', 'assigned_to_id', 'completed_at',
            'ticket_rating', 'created_by_id', 'created_by_external_id', 'attachments', 'assigned_to', 'permissions')


class MyTicketSerializer(TicketSerializer):
    """
    Only for those tickets whose 
    created_by_id == ticket accessed_by_id (current user/loggedin user)
    """

    def __init__(self, *args, **kwargs):
        super(MyTicketSerializer, self).__init__(*args, **kwargs)
        self.fields['ticket_rating'] = MyRatingSerializer()


class ListTicketSerializer(TicketSerializer):
    """
    Only for those tickets whose
    created_by_id == ticket accessed_by_id (current user/loggedin user)
    """

    class Meta:
        model = Ticket
        fields = (
            'id', 'email', 'name', 'accepted_at', 'estimated_hrs', 'status', 'phone', 'urgency_level', 'department', \
            'detail', 'remaining_time', 'deadline', 'to_be_accepted_by', 'assigned_to_id', 'completed_at',
            'ticket_rating', 'created_by_id', 'created_by_external_id', 'assigned_to', 'permissions')


class TicketLogSerializer(serializers.ModelSerializer):
    by = serializers.SerializerMethodField()

    def get_by(self, log):
        return log.added_by.name

    class Meta:
        model = TicketLog
        fields = '__all__'


class TicketActionSerializer(serializers.ModelSerializer):
    assigned_to_id = serializers.IntegerField(default=0)
    estimated_hrs = serializers.IntegerField(default=0)
    note = serializers.CharField(default='')

    def accept(self, ticket, by):
        try:
            ticket.accept(
                assigned_to_id=self.validated_data.get('assigned_to_id'),
                by=by,
                estimated_hrs=self.validated_data.get('estimated_hrs', None)
            )
            return ticket
        except ValidationError as e:
            raise APIValidationError(e.message)

    def done(self, ticket, by):
        try:
            note = self.validated_data.get('note', None)
            if note:
                note = de_emojify(note)

            ticket.done(by=by, note=note)
            return ticket
        except ValidationError as e:
            raise APIValidationError(e)

    class Meta:
        model = Ticket
        fields = ('estimated_hrs', 'assigned_to_id', 'note',)


class TicketAddEstimatedHrsSerializer(serializers.ModelSerializer):
    estimated_hrs = serializers.IntegerField()

    def add_estimate(self, ticket, by):
        try:
            ticket.add_estimate(hours=self.data.get('estimated_hrs'), by=by)
            return ticket
        except ValidationError as e:
            raise APIValidationError(e.message)

    class Meta:
        model = Ticket
        fields = ('estimated_hrs',)


class TicketRejectSerializer(serializers.ModelSerializer):
    reason = serializers.CharField()

    def reject(self, ticket, by):
        try:
            ticket.reject(
                by=by,
                reason=self.validated_data.get('reason', None)
            )
            return ticket
        except ValidationError as e:
            raise APIValidationError(e)

    def close(self, ticket, by):
        try:
            ticket.close(
                by=by,
                reason=self.validated_data.get('reason', None)
            )
            return ticket
        except ValidationError as e:
            raise APIValidationError(e)

    class Meta:
        model = Ticket
        fields = ('reason',)


class TicketRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketRating
        fields = ("rating", "comment",)

    def rate(self, ticket):
        rating = TicketRating(
            ticket=ticket,
            rating=self.validated_data.get('rating'),
            comment=de_emojify(self.validated_data.get('comment'))
        )
        rating.save()
        return rating


class TicketChangeDeptSerializer(serializers.ModelSerializer):
    def change_dept(self, ticket, by):
        try:
            ticket.change_dept(by=by, department=self.validated_data.get('department'))
            return ticket
        except ValidationError as e:
            raise APIValidationError(e.message)

    class Meta:
        model = Ticket
        fields = ("department",)
