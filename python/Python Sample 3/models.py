# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import timedelta, datetime

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from enum import Enum, unique

from departments.models import Department, Employee


@unique
class TicketStatus(Enum):
    Pending = 1
    InProgress = 2
    Rejected = 3
    Completed = 4
    Closed = 5


@unique
class TicketLogType(Enum):
    Assigned = "Assigned"
    Rejected = "Rejected"
    InProgress = "In Progress"
    Completed = "Completed"
    Closed = "Closed"
    Estimation = "Estimation"
    DepartmentChanged = "Department Changed"


class TicketQuerySet(models.QuerySet):
    def created_by(self, accessed_by):
        if accessed_by.is_external_contact:
            return self.filter(created_by_external_id=accessed_by.id)
        return self.filter(created_by_id=accessed_by.id)

    def accessed_by(self, accessed_by):
        """
        :param accessed_by: User who is going to access the ticket
        :return: permitted ticket objects

        A Ticket should be accessed by:
        1. Who has permission account.can_check_helpdesk_all_tickets
        2. PC can access the ticket.
        3. Who generated the ticket.
        4. Assigned department can access the ticket.
        """

        tickets = self

        if accessed_by.has_permission('account.can_check_helpdesk_all_tickets') \
                or accessed_by.is_process_coordinator:
            # A Ticket should be accessed by:
            # 1. Who has permission account.can_check_helpdesk_all_tickets
            # 2. PC can access the ticket.
            return tickets

        if accessed_by.help_department:
            # If user is not PC or not has permission account.can_check_helpdesk_all_tickets
            # the ticket can only be accessed by the:
            # 3. user who had generated the ticket or
            # 4. user belongs to the assigned department.
            tickets = tickets \
                .filter(
                Q(created_by_id=accessed_by.id) | Q(department_id=accessed_by.help_department.department.id))
        else:
            # if user has not permission permission account.can_check_helpdesk_all_tickets and
            # if user is not a PC and
            # if user is not belongs to the Assigned department, the ticket is accessible only to
            # as per point #3. Who generated the ticket.
            tickets = tickets.created_by(accessed_by)

        return tickets


class TicketManager(models.Manager):
    def get_queryset(self):
        return TicketQuerySet(self.model, using=self._db).select_related('assigned_to')

    def accessed_by(self, accessed_by):
        """
        :param accessed_by: User who is going to access the ticket
        :return: permitted ticket objects
        """
        return self.get_queryset().accessed_by(accessed_by)


class Ticket(models.Model):
    URGENCY_LEVEL = (
        (1, 'Today'),
        (2, 'Next 48 hours'),
        (3, 'This Week'),
        (4, 'Not Urgent')
    )

    created_by_id = models.IntegerField(null=True, blank=True)
    created_by_external_id = models.IntegerField(null=True, blank=True)
    # assigned_to_id = models.IntegerField(null=True, blank=True)
    assigned_to = models.ForeignKey(Employee, on_delete=models.DO_NOTHING, null=True, blank=True)

    email = models.EmailField(max_length=70, blank=True)
    name = models.CharField(max_length=100, null=False)
    phone = models.BigIntegerField()
    urgency_level = models.IntegerField(choices=URGENCY_LEVEL)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.CASCADE)
    detail = models.TextField(null=False, blank=False)
    status = models.IntegerField(choices=[(status.name, status.value) for status in TicketStatus], default=1)
    accepted_at = models.DateTimeField(null=True)
    estimated_hrs = models.IntegerField(null=True)
    completed_at = models.DateTimeField(null=True)
    rejected_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    to_be_accepted_by = models.DateTimeField(blank=True, null=True)

    objects = TicketManager()

    def __str__(self):
        return str(self.id)

    @property
    def deadline(self):
        if self.accepted_at and self.estimated_hrs:
            return timezone.localtime(self.accepted_at + timedelta(hours=self.estimated_hrs))
        return None

    @property
    def remaining_time(self):
        if self.estimated_hrs and self.accepted_at:
            deadline = self.accepted_at + timedelta(hours=self.estimated_hrs)
            current_time = timezone.now()
            if self.status == TicketStatus.Completed.value:
                return deadline - self.completed_at
            elif current_time > deadline:
                return "Over Due"
            else:
                return deadline - current_time

        else:
            return None

    def can_reject(self, by, raise_exception=False):
        # Here we may check the pending status, i.e. only tickets with pending status can be rejected
        # Only those tickets can be rejected which are not accepted yet
        if self.assigned_to_id:
            if raise_exception:
                raise ValidationError('Ticket is already accepted')
            return False

        if self.status == TicketStatus.Rejected.value:
            if raise_exception:
                raise ValidationError('Ticket is already rejected')
            return False

        if by.help_department and by.help_department.department == self.department:
            return True

        return False

    def can_accept(self, by, raise_exception=False):
        # Here we may check the pending status, i.e. only tickets with pending status can be accepted
        # Only those tickets can be accepted which are not accepted yet
        if self.assigned_to_id:
            if raise_exception:
                raise ValidationError('Ticket is already accepted')
            return False

        if by.help_department and by.help_department.department == self.department:
            return True

        return False

    def can_add_estimates(self, by, raise_exception=False):
        """
        Add estimated hours to the ticket only if:
        1. Ticket is in pending state.
        2. Ticket is assigned to the doer
        3. Estimated hours is null or zero
        """

        if not (self.status == TicketStatus.Pending.value
                and self.assigned_to_id == by.id
                and not self.estimated_hrs):
            if raise_exception:
                raise ValidationError('Ticket either not assigned or hours is already added')
            return False
        return True

    def can_close(self, by, raise_exception=False):
        # Only rejected tickets can be closed
        if self.status != TicketStatus.Rejected.value:
            if raise_exception:
                raise ValidationError('Only rejected ticket can be closed')
            return False

        # Only PC and Admin can close the ticket
        if not by.is_process_coordinator and not by.has_permission('account.can_check_helpdesk_all_tickets'):
            if raise_exception:
                raise ValidationError('Only PC/Admin can close the ticket.')
            return False

        return True

    def can_mark_done(self, by, raise_exception=False):
        # Only InProgress ticket can pe marked Done
        if self.status != TicketStatus.InProgress.value:
            if raise_exception:
                raise ValidationError('Only In progress ticket can be marked as done')
            return False

        # Only those tickets can be done which are not accepted yet
        if not self.assigned_to_id:
            if raise_exception:
                raise ValidationError('Ticket is not assigned yet', 404)
            return False

        if not self.estimated_hrs:
            if raise_exception:
                raise ValidationError('Estimation is not given yet', 404)
            return False

        # Only assigned user and manager of dept. can mark it done
        if not (self.assigned_to_id == by.id
                or (by.help_department
                    and by.help_department.is_manager
                    and (by.help_department.department == self.department))):
            if raise_exception:
                raise ValidationError('Only assigned user and manager of dept. can mark it done.')
            return False

        return True

    def can_change_dept(self, by, raise_exception=False):
        if self.status not in \
                [TicketStatus.Pending.value, TicketStatus.InProgress.value, TicketStatus.Rejected.value]:
            if raise_exception:
                raise ValidationError('The Dept. can be changed only of Pending, In Progress, and Rejected tickets')
            return False

        # Only PC and Admin can change the department
        if not by.is_process_coordinator and not by.has_permission('account.can_check_helpdesk_all_tickets'):
            if raise_exception:
                raise ValidationError('Only PC/Admin can change the department.')
            return False

        return True

    def can_comment(self, by, raise_exception=False):
        if self.status in [TicketStatus.Completed.value, TicketStatus.Closed.value]:
            if raise_exception:
                raise ValidationError("Can't comment on Closed and Completed ticket.")
            return False
        return True

    def add_estimate(self, hours, by):
        """
        :param hours: hours in integer
        :param by: current user
        :return: ticket
        """

        if self.can_add_estimates(by, raise_exception=True):
            self.estimated_hrs = hours
            self.status = TicketStatus.InProgress.value
            self.save()

            TicketLog(
                ticket=self,
                log_type=TicketLogType.Estimation.value,
                log="%s Hrs" % hours,
                assigned_department=self.department,
                assigned_employee=self.assigned_to_id,
                added_by_id=by.id
            ).save()

            return self

    def accept(self, by, assigned_to_id=None, estimated_hrs=0):
        if self.can_accept(by, raise_exception=True):
            if assigned_to_id and by.help_department.is_manager \
                    and by.help_department.department == self.department:
                # Only manager of the department can assign the ticket to other
                self.assigned_to_id = assigned_to_id
            else:
                # If user is not manager assign it to himself
                self.assigned_to_id = by.id

            self.estimated_hrs = estimated_hrs

            # if estimated Hours is zero means ticket is still in pending state else its in-progress
            if self.estimated_hrs > 0:
                self.status = TicketStatus.InProgress.value
                log_type = TicketLogType.InProgress.value
            else:
                log_type = TicketLogType.Assigned.value

            self.accepted_at = timezone.now()
            self.save()

            TicketLog(
                ticket=self,
                log_type=log_type,
                assigned_department=self.department,
                assigned_employee=self.assigned_to_id,
                added_by_id=by.id
            ).save()

            return self

    def reject(self, by, reason):
        if self.can_reject(by, raise_exception=True):
            self.status = TicketStatus.Rejected.value
            self.save()

            TicketLog(
                ticket=self,
                log_type=TicketLogType.Rejected.value,
                log=reason,
                assigned_department=self.department,
                added_by_id=by.id
            ).save()

            return self

    def close(self, by, reason):
        if self.can_close(by, raise_exception=True):
            self.status = TicketStatus.Closed.value
            self.save()

            TicketLog(
                ticket=self,
                log_type=TicketLogType.Closed.value,
                log=reason,
                added_by_id=by.id
            ).save()

            return self

    def done(self, by, note):
        if self.can_mark_done(by, raise_exception=True):
            self.status = TicketStatus.Completed.value
            self.completed_at = timezone.now()
            self.save()

            TicketLog(
                ticket=self,
                log_type=TicketLogType.Completed.value,
                log=note,
                assigned_department=self.department,
                assigned_employee=self.assigned_to_id,
                added_by_id=by.id
            ).save()

            return self

    def change_dept(self, by, department):
        if self.can_change_dept(by, raise_exception=True):
            if self.department == department and self.status != TicketStatus.Rejected.value:
                raise ValidationError("Can't reassign to same department.")

            older_department = self.department.name
            self.department = department
            self.status = TicketStatus.Pending.value
            self.assigned_to_id = None
            self.estimated_hrs = None
            self.save(reset_acceptance_duration=True)

            TicketLog(
                ticket=self,
                log_type=TicketLogType.DepartmentChanged.value,
                assigned_department=self.department,
                log="%s > %s" % (older_department, self.department.name),
                added_by_id=by.id
            ).save()

            return self

    def save(self, reset_acceptance_duration=False, *args, **kwargs):
        if not self.id or reset_acceptance_duration:
            acceptance_hours = Department.objects.get(id=self.department.id).acceptance_duration
            self.to_be_accepted_by = datetime.now() + timedelta(hours=acceptance_hours)
        super(Ticket, self).save(*args, **kwargs)


class Comment(models.Model):
    COMMENT_TYPE = (
        ('general', 'General'),
        ('reject', 'Reject'),
    )
    body = models.TextField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    added_by_id = models.IntegerField(null=True, blank=True)
    added_by_external_id = models.IntegerField(null=True, blank=True)
    added_by_name = models.CharField(max_length=75, null=True, blank=True)
    comment_type = models.CharField(max_length=50, choices=COMMENT_TYPE, default='general')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.body)


class TicketLog(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.DO_NOTHING)
    log_type = models.CharField(max_length=50,
                                choices=[(log_type.name, log_type.value) for log_type in TicketLogType],
                                default='')
    log = models.TextField()
    assigned_department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.DO_NOTHING)
    assigned_employee = models.IntegerField(null=True, blank=True)
    # by = models.IntegerField(null=True, blank=True)
    added_by = models.ForeignKey(Employee, on_delete=models.DO_NOTHING, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id) + " " + str(self.ticket.id)


class TicketRating(models.Model):
    id = models.AutoField(primary_key=True)
    ticket = models.OneToOneField(Ticket, related_name="ticket_rating", on_delete=models.DO_NOTHING, unique=True)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0.0, null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.comment


class TicketAttachment(models.Model):
    id = models.AutoField(primary_key=True)
    ticket = models.ForeignKey(Ticket, related_name="ticket_attachment", on_delete=models.CASCADE)
    original_name = models.CharField(max_length=100)
    uuid_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Notification(models.Model):
    WHATSAPP = 'WA'
    NOTIFICATION_VIA = [
        (WHATSAPP, 'WhatsApp')
    ]

    channel = models.CharField(
        max_length=2,
        choices=NOTIFICATION_VIA,
        default=WHATSAPP,
    )

    hook_response = models.TextField()
    timestamp = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
