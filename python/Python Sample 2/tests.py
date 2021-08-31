from django.core.exceptions import PermissionDenied
from django.test import TestCase

from account.models import User
from lead.models import Status, Actor, Action, Lead


# def test(req):
#     # lead = Lead.objects.get(pk=1)
#     # print('===============status=========================')
#     # print(lead.status)
#     # print('===============list status actions=============')
#     # print(lead.status.actions.all())
#     # print('=========Execute actions==============')
#     # print(lead.status)
#     # Action.objects.get(key='pitch').execute(lead, req.user)
#     # print(lead.status)
#     s = Status.objects.get(pk=2)
#     # s = StatusSerializer(s)
#     # print(s.data)
#     s.change_sequence(3)
#     print(s)
#
#     return JsonResponse({'success': False}, safe=False)


class LeadActionTestCase(TestCase):
    def setUp(self):
        all_from_dept = Actor.objects.create(name='All from department', key='all_from_dept')
        creator = Actor.objects.create(name='Creator', key='creator')
        assigned_member = Actor.objects.create(name='Assigned Member', key='assigned_to')

        status_new = Status.objects.create(name='New', key='new', sequence=1, show_on_board=1)
        status_accepted = Status.objects.create(name='Accepted', key='accepted', sequence=2, show_on_board=1)
        status_rejected = Status.objects.create(name='Rejected', key='rejected', sequence=0)
        status_pitched = Status.objects.create(name='Pitched', key='pitched', sequence=3, show_on_board=1)
        status_res_generated = Status.objects.create(name='Response Generated', key='response_generated', sequence=4,
                                                     show_on_board=1)

        action_accept = Action.objects.create(name='Accept', key='accept', next_status=status_accepted)
        action_accept.actors.add(assigned_member)

        action_reject = Action.objects.create(name='Reject', key='reject', next_status=status_rejected)
        action_reject.actors.add(assigned_member)

        action_pitch = Action.objects.create(name='Pitch', key='pitch', next_status=status_pitched)
        action_pitch.actors.add(assigned_member)

        action_response = Action.objects.create(name='Response', key='response', next_status=status_res_generated)

        status_new.actions.add(action_accept)
        status_new.actions.add(action_reject)

        status_accepted.actions.add(action_pitch)
        status_pitched.actions.add(action_response)

        self.naresh = User.objects.create(email='naresh@g.com', first_name='Naresh', last_name='Kumar', is_active=True)
        self.sunny = User.objects.create(email='sunny@g.com', first_name='Sunny', last_name='Kumar', is_active=True)
        Lead.objects.create(name='LMS Optimization', status=status_new, created_by=self.naresh, assigned_to=self.sunny)

    def test_can_accept_new_lead(self):
        """The lead with new status can be accepted by the assigned member"""
        new_lead = Lead.objects.filter(status__key='new').first()
        accepted_lead = Action.objects.get(key='accept').execute(new_lead, by=self.sunny)
        self.assertEqual(new_lead.status.key, 'accepted')
        self.assertEqual(accepted_lead.status.key, 'accepted')

    def test_lead_cannot_be_acccept_by_memeber_other_than_assigned(self):
        """The lead can not be accept by member other than assigned user"""
        new_lead = Lead.objects.filter(status__key='new').first()

        with self.assertRaises(PermissionDenied) as cm:
            Action.objects.get(key='accept').execute(new_lead, by=self.naresh)

        self.assertEqual(
            "Not Permitted",
            str(cm.exception)
        )

    def test_should_not_pitch_the_new_lead(self):
        """The new lead can not be pitched directly"""
        new_lead = Lead.objects.filter(status__key='new').first()

        with self.assertRaises(PermissionDenied) as cm:
            Action.objects.get(key='pitch').execute(new_lead, by=self.sunny)

        self.assertEqual(
            "Action 'pitch' is not allowed as this stage",
            str(cm.exception)
        )

    def test_pitch_the_new_lead_directly_if_action_pitch_is_added(self):
        """The new lead can be pitched directly if Pitch action is linked to the status"""
        new_status = Status.objects.get(key='new')
        action_pitch = Action.objects.get(key='pitch')
        new_status.actions.add(action_pitch)

        new_lead = Lead.objects.filter(status__key='new').first()

        pitched_lead = Action.objects.get(key='pitch').execute(new_lead, by=self.sunny)
        self.assertEqual(pitched_lead.status.key, 'pitched')

    def test_can_reject_new_lead(self):
        """The lead with new status can be rejected by by the assigned member"""
        new_lead = Lead.objects.filter(status__key='new').first()
        accepted_lead = Action.objects.get(key='reject').execute(new_lead, by=self.sunny)
        self.assertEqual(new_lead.status.key, 'rejected')
        self.assertEqual(accepted_lead.status.key, 'rejected')

    def test_status_get_squence(self):
        statuses = Status.objects.list()
        required = [Status.objects.get(key='new'),
                    Status.objects.get(key='accepted'),
                    Status.objects.get(key='pitched'),
                    Status.objects.get(key='response_generated')
                    ]
        self.assertEqual(statuses, required)
