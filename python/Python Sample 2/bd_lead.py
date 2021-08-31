from datetime import datetime, timedelta
from django.db import models
from enum import Enum, unique
from django.core.exceptions import PermissionDenied

from account.models import Client
from django.db.models import F, Q, Count
from account.models import User

class Actor(models.Model):
    """One who acts; a doer. In simple words the entity that performs a role e.g.
    1. The one who creates the leads,
    2. The one who accept the lead.
    3. The department to whome lead is assigned
    4. In a single line the one who changes status of the leads.
    """
    name = models.CharField(max_length=50, blank=False)
    key = models.CharField(max_length=50, blank=False)
    def __str__(self):
        return self.name

class Action(models.Model):
    """The action perform by the Actor e.g.
    1. To create a lead by an actor is a Create action
    2. To accept a lead by an actor is a Accept action
    3. To reject a lead by an actor is a Accept action
    4. To pitch a lead by an actor is a Pitch action
    5. To respond a lead by an actor is Reponse action
    """
    name = models.CharField(max_length=50, blank=False)
    key = models.CharField(max_length=50, blank=False)
    next_status = models.ForeignKey('Status', blank=True, null=True, on_delete=models.DO_NOTHING)
    note_required = models.BooleanField(default=False)
    actors = models.ManyToManyField(Actor)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name

    def execute(self, lead, by, note=None):
        """Change status of the lead only if
        1. Does the action performed is as per the sequence defined?
        2. User who is performing action has sufficient permissions by checking the actors
        3. Assign lead to current user if action is Accept [Hard coded]
        4. Reset Assignee to None if action is Reject [Hard coded]
        5. Set followup reminder
        """
        # 1. Check the sequence
        can_execute = False
        for action in lead.status.actions.all():
            if action == self:
                can_execute = True
                break
        if not can_execute:
            raise PermissionDenied("Action '%s' is not allowed as this stage" % self.key)
        # 2. Check the permissions
        can_execute = False
        for actor in self.actors.all():
            if actor.key == 'all_from_dept':
                can_execute = True
                break
            elif actor.key == 'creator' and lead.created_by == by:
                can_execute = True
                break
            elif actor.key == 'assigned_to' and lead.assigned_to == by:
                can_execute = True
                break
        if not can_execute:
            raise PermissionDenied('Not Permitted')
        lead.status = self.next_status
        # 3. Assign lead to current user if status action is Accept [Hard coded]
        # 4. Reset Assignee to None if action is Reject [Hard coded]
        if self.key == 'accept':
            lead.assigned_to = by
        elif self.key == 'reject':
            lead.assigned_to = None
        # 5. Set followup reminder
        followup_reminder = BDLeadFollowUpReminder.objects \
            .filter(status=lead.status, source=lead.source) \
            .first()
        if followup_reminder:
            lead.next_followup_at = followup_reminder.datetime()
        if self.note_required:
            pass
        lead.save()
        BDLeadLog(
            lead=lead,
            log_type=lead.status.name,
            log=note,
            by=by
        ).save()
        return lead

class StatusManager(models.Manager):
    def list(self, all=False):
        """get status list as per status action configuration"""
        new_status = self.model.objects.get(key='new')
        statuses = [new_status]
        def seq(status):
            for action in status.actions.all():
                if all or action.next_status.show_on_board:
                    statuses.append(action.next_status)
                    seq(action.next_status)
        seq(new_status)
        if not all:
            statuses = set(statuses)
        return statuses


class Status(models.Model):
    """Represent the current state of the lead e.e.
    1. New a new lead
    2. Accepted an accepted lead by an actor
    3. Rejected a rejected lead by an actor
    4. Pitched a pitched lead by an actor
    """
    name = models.CharField(max_length=50, blank=False)
    key = models.CharField(max_length=50, blank=False)
    sequence = models.IntegerField()
    actions = models.ManyToManyField(Action, blank=True)
    show_on_board = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = StatusManager()
    def change_sequence(self, sequence):
        """Change sequence order of the status
        1. sequence order should not be same as current
        2. Get the status whose sequence is equal to proposed sequence
        """
        if self.sequence == sequence:
            return False
        if self.sequence > sequence:
            statuses = Status.objects.filter(sequence__gte=sequence, sequence__lt=self.sequence)
            statuses.update(sequence=F('sequence') + 1)
        else:
            statuses = Status.objects.filter(sequence__lte=sequence, sequence__gt=self.sequence)
            statuses.update(sequence=F('sequence') - 1)
        self.sequence = sequence
        self.save()
    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural = "statuses"


class BDLeadManager(models.Manager):
    def leads(self, accessed_by):
        """
        :param accessed_by: User who is going to access the lead
        :return: queryset
        A leads should be accessed by:
        1. Who generated the lead.
        2. Supervisor of assigned member can access the lead.
        3. Assigned member can access the lead.
        """
        # 2. Supervisor of assigned member can access the lead.
        team = list(accessed_by.team.filter(is_active=True))
        # 3. Assigned member can access the lead.
        team.append(accessed_by)
        self = self.filter(Q(assigned_to__in=team) | Q(created_by=accessed_by))
        return self
    def reminder_summary(self, accessed_by):
        """get lead reminders"""
        # return self.model.objects.filter(next_followup_at__lte=datetime.now())
        return self.model.objects.leads(accessed_by) \
            .values('status_id', 'status__name') \
            .annotate(count=Count('status_id'))


class BDLead(models.Model):
    SOURCES = (
        ('email', 'Email'),
    )
    name = models.CharField(max_length=250, blank=False)
    description = models.TextField(blank=False)
    source = models.CharField(max_length=10, choices=SOURCES)
    url = models.URLField(max_length=250)
    status = models.ForeignKey(Status, on_delete=models.DO_NOTHING)
    estimated_budget = models.FloatField()
    referred_by = models.CharField(max_length=250)
    prospect = models.ForeignKey(Client, on_delete=models.DO_NOTHING)
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    assigned_to = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='assigned_leads')
    next_followup_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # tags = TaggableManager()
    objects = BDLeadManager()


    def __str__(self):
        return self.name

# class Lead(models.Model):
#     SOURCES = (
#         ('email', 'Email'),
#     )
#     name = models.CharField(max_length=250, blank=False)
#     description = models.TextField(blank=False)
#     source = models.CharField(max_length=10, choices=SOURCES)
#     url = models.URLField(max_length=250, blank=True, null=True)
#     estimated_budget = models.FloatField(blank=True, null=True)
#     referred_by = models.CharField(max_length=250, blank=True, null=True)
#     prospect = models.ForeignKey(Client, on_delete=models.DO_NOTHING)
#     next_followup_at = models.DateTimeField(blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#
#     objects = LeadManager()
#
#     def __str__(self):
#         return self.name


class BDLeadFollowUpReminder(models.Model):
    @unique
    class Unit(Enum):
        hours = "hours"
        minutes = "minutes"

    source = models.CharField(max_length=10, choices=BDLead.SOURCES)
    status = models.ForeignKey(Status, on_delete=models.DO_NOTHING)
    after = models.IntegerField()
    unit = models.CharField(max_length=10,
                            choices=[(u.name, u.value) for u in Unit],
                            default="hours")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s %s" % (self.after, self.unit)
    def datetime(self):
        """Get reminder datetime"""
        reminder_after = {
            str(self.unit): self.after
        }
        return datetime.now() + timedelta(**reminder_after)


class BDLeadLog(models.Model):
    lead = models.ForeignKey(BDLead, on_delete=models.DO_NOTHING)
    log_type = models.CharField(max_length=50, default='')
    log = models.TextField(null=True, blank=True)
    by = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return str(self.id) + " " + str(self.lead.id)
