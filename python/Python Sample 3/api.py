# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import timedelta

from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import mixins
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from help_ticket.api import Pagination
from settings.models import Settings
from ticket.serializers import CommentAddedSerializer
from .models import Ticket, Comment, TicketLog, TicketRating, TicketStatus
from .serializers import TicketCreateSerializer, TicketSerializer, CommentAddSerializer, CommentSerializer, \
    TicketLogSerializer, TicketActionSerializer, TicketRejectSerializer, TicketRatingSerializer, \
    TicketChangeDeptSerializer, MyTicketSerializer, TicketAddEstimatedHrsSerializer, ListTicketSerializer


class TicketReadView(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Ticket.objects.all().order_by('-updated_at')
    serializer_class = ListTicketSerializer
    pagination_class = Pagination

    def retrieve(self, request, pk=None):
        try:
            ticket = Ticket.objects\
                .prefetch_related('ticket_attachment')\
                .select_related('ticket_rating')\
                .accessed_by(request.user)\
                .get(pk=pk)

            # for managing rating view for pc and ticket owner
            # ticket created by == accessed by show rating to owner
            if ticket.created_by_id == request.user.id or ticket.created_by_external_id == request.user.id:
                serialized = MyTicketSerializer(ticket, accessed_by=request.user)
            else:
                # serializer manages rating view permission
                serialized = TicketSerializer(ticket, accessed_by=request.user)
            return Response(serialized.data)
        except:
            raise Http404

    @action(methods=['GET'], detail=False)
    def submitted_open(self, request):
        """return: All Open(Pending/In-progress/Rejected) tickets submitted by logged-in user """

        order_by = '-updated_at'
        _filter = {
            # 'created_by_id': request.user.id,
            'status__in': [TicketStatus.Pending.value,
                           TicketStatus.InProgress.value,
                           TicketStatus.Rejected.value]
        }

        tickets = Ticket.objects\
            .filter(**_filter)\
            .created_by(request.user)\
            .order_by(order_by)

        page = self.paginate_queryset(tickets)
        if page is not None:
            serializer = self.get_serializer(page, accessed_by=request.user, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(tickets, accessed_by=request.user, many=True)
        return Response(serializer.data, status=200)

    @action(methods=['GET'], detail=False)
    def created_by_me(self, request):
        order_by = '-updated_at'
        if request.GET.get('o'):
            by = request.GET.get('o')
            order = ''
            if by[0] == '-':
                by = by.replace('-', '')
                order = '-'

            if by == 'id':
                order_by = "%s%s" % (order, by)
            elif by == 'department':
                order_by = "%s%s" % (order, 'department__name')

        _filter = {
            # 'created_by_id': request.user.id
        }

        if request.GET.get('status') and int(request.GET.get('status')) > 0:

            if request.GET.get('status') == str(TicketStatus.InProgress.value):
                _filter['status__in'] = [TicketStatus.InProgress.value, TicketStatus.Rejected.value]
            else:
                _filter['status'] = request.GET.get('status')

        tickets = Ticket.objects\
            .filter(**_filter)\
            .created_by(request.user)\
            .order_by(order_by)

        page = self.paginate_queryset(tickets)
        if page is not None:
            # managing ratings for ticket owners show rating
            serializer = self.get_serializer(page, accessed_by=request.user, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(tickets, accessed_by=request.user, many=True)
        return Response(serializer.data, status=200)

    @action(methods=['GET'], detail=False)
    def assigned_to_dept(self, request):
        try:

            screen = request.GET.get('screen')
            order_by = '-updated_at'

            if not (request.user.is_process_coordinator
                    or request.user.has_permission('account.can_check_helpdesk_all_tickets')
                    or request.user.help_department or (screen == 'assigned_to_me')):
                return Response({}, status=200)

            if request.GET.get('o'):
                by = request.GET.get('o')
                order = ''
                if by[0] == '-':
                    by = by.replace('-', '')
                    order = '-'

                if by == 'id':
                    order_by = "%s%s" % (order, by)
                elif by == 'department':
                    order_by = "%s%s" % (order, 'department__name')

            _filter = {}

            if request.GET.get('q'):
                query = request.GET.get('q')
                try:
                    _filter['id'] = int(query)
                except Exception as e:
                    _filter['detail__contains'] = query

            if request.GET.get('start_date') and request.GET.get('end_date'):
                start_date = request.GET.get('start_date')
                end_date = request.GET.get('end_date')
                _filter['created_at__range'] = (start_date, end_date)

            if not request.user.is_process_coordinator \
                    and not request.user.has_permission('account.can_check_helpdesk_all_tickets') \
                    and request.user.help_department:
                _filter['department'] = request.user.help_department.department.id

            if screen == 'open':
                _filter['status__in'] = [TicketStatus.Pending.value, TicketStatus.InProgress.value]
                if request.user.is_process_coordinator \
                        or request.user.has_permission('account.can_check_helpdesk_all_tickets'):
                    _filter['status__in'].append(TicketStatus.Rejected.value)
            elif screen == 'closed':
                _filter['status__in'] = [TicketStatus.Completed.value, TicketStatus.Closed.value]
                if not request.user.is_process_coordinator \
                        and not request.user.has_permission('account.can_check_helpdesk_all_tickets'):
                    _filter['status__in'].append(TicketStatus.Rejected.value)
            elif screen == 'assigned_to_me':
                _filter['assigned_to_id'] = request.user.id
                _filter['status__in'] = [TicketStatus.Pending.value, TicketStatus.InProgress.value]

            if request.GET.get('status') and int(request.GET.get('status')) > 0:
                _filter['status'] = request.GET.get('status')

            if request.GET.get('assigned_to_id'):
                _filter['assigned_to_id'] = request.GET.get('assigned_to_id')

            if request.GET.get('department') and int(request.GET.get('department')) > 0:
                _filter['department_id'] = request.GET.get('department')

            tickets = Ticket.objects.filter(**_filter).order_by(order_by)

            page = self.paginate_queryset(tickets)

            if page is not None:
                serializer = self.get_serializer(page, accessed_by=request.user, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(tickets, accessed_by=request.user, many=True)
            return Response(serializer.data, status=200)
        except Exception as e:
            print (e)
        return Response({}, status=200)

    @action(methods=['GET'], detail=False)
    def meta(self, request):
        _filter = {
            'status': TicketStatus.Pending.value
        }

        if not request.user.is_process_coordinator \
                and not request.user.has_permission('account.can_check_helpdesk_all_tickets') \
                and request.user.help_department:
            _filter['department'] = request.user.help_department.department.id

        if request.user.is_process_coordinator \
            or request.user.has_permission('account.can_check_helpdesk_all_tickets') \
                or request.user.help_department:
            total_pending_tickets = Ticket.objects.filter(**_filter).count()
        else:
            total_pending_tickets = 0

        total_pending_assigned_tickets = Ticket.objects.filter(
            assigned_to_id=request.user.id, status=TicketStatus.Pending.value).count()

        average_rating = 0.0
        try:
            rating_qry = Ticket.objects.raw(
                'SELECT ticket.id, AVG(rating.rating) AS avg_rating FROM ticket_ticket as ticket '
                'INNER JOIN ticket_ticketrating as rating ON ticket.id = rating.ticket_id '
                'WHERE ticket.assigned_to_id={0}'.format(
                    request.user.id,
                    TicketStatus.Completed.value
                )
            )

            average_rating = rating_qry[0].avg_rating
        except:
            pass

        return Response({
            'total_pending_tickets': total_pending_tickets,
            'total_pending_assigned_tickets': total_pending_assigned_tickets,
            'user_average_rating': average_rating,
        }, status=200)


class TicketActionView(mixins.CreateModelMixin, viewsets.GenericViewSet):

    def get_serializer_class(self):
        if self.action == 'create':
            return TicketCreateSerializer

        if self.action == 'accept' or self.action == 'mark_done':
            return TicketActionSerializer

        if self.action == 'estimated_hrs':
            return TicketAddEstimatedHrsSerializer

        if self.action == 'reject' or self.action == 'close':
            return TicketRejectSerializer

        if self.action == 'change_dept':
            return TicketChangeDeptSerializer

        if self.action == 'comment':
            return CommentAddSerializer

        if self.action == 'comments':
            return CommentSerializer

        if self.action == 'logs':
            return TicketLogSerializer

    def create(self, request, *args, **kwargs):
        serialized = TicketCreateSerializer(data=request.data)
        print(request.data)
        if serialized.is_valid(raise_exception=True):
            files = request.FILES.getlist('files')
            ticket = serialized.create(by=request.user, attachments=files)
            serialized = TicketSerializer(ticket, accessed_by=request.user)
            return Response(serialized.data, status=201)

    @action(methods=['PUT'], detail=True)
    def change_dept(self, request, pk):
        ticket = Ticket.objects.accessed_by(request.user).filter(pk=pk).first()
        if ticket:
            serialized = TicketChangeDeptSerializer(data=request.data)
            if serialized.is_valid(raise_exception=True):
                ticket = serialized.change_dept(ticket, request.user)
                serializer = TicketSerializer(ticket, accessed_by=request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            raise Http404

    @action(methods=['PUT'], detail=True)
    def accept(self, request, pk):
        ticket = Ticket.objects.accessed_by(request.user).filter(pk=pk).first()
        if ticket:
            serialized = TicketActionSerializer(data=request.data)
            if serialized.is_valid(raise_exception=True):
                ticket = serialized.accept(ticket, request.user)
                serialized = TicketSerializer(ticket, accessed_by=request.user)
                return Response(serialized.data)
        else:
            raise Http404

    @action(methods=['PUT'], detail=True)
    def mark_done(self, request, pk):
        ticket = Ticket.objects.accessed_by(request.user).filter(pk=pk).first()
        if ticket:
            serialized = TicketActionSerializer(data=request.data)
            if serialized.is_valid(raise_exception=True):
                ticket = serialized.done(ticket, request.user)
                serialized = TicketSerializer(ticket, accessed_by=request.user)
                return Response(serialized.data)
        else:
            raise Http404

    @action(methods=['PUT'], detail=True)
    def estimated_hrs(self, request, pk):
        ticket = Ticket.objects.accessed_by(request.user).filter(pk=pk).first()

        if ticket:
            serialized = TicketAddEstimatedHrsSerializer(data=request.data)
            if serialized.is_valid(raise_exception=True):
                ticket = serialized.add_estimate(ticket, request.user)
                serialized = TicketSerializer(ticket, accessed_by=request.user)
                return Response(serialized.data)
        else:
            raise Http404

    @action(methods=['PUT'], detail=True)
    def reject(self, request, pk):
        ticket = Ticket.objects.accessed_by(request.user).filter(pk=pk).first()

        if ticket:
            serialized = TicketRejectSerializer(data=request.data)
            if serialized.is_valid(raise_exception=True):
                ticket = serialized.reject(ticket, request.user)
                serialized = TicketSerializer(ticket, accessed_by=request.user)
                return Response(serialized.data)
        else:
            raise Http404

    @action(methods=['PUT'], detail=True)
    def close(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        serialized = TicketRejectSerializer(data=request.data)
        if serialized.is_valid(raise_exception=True):
            ticket = serialized.close(ticket, request.user)
            serialized = TicketSerializer(ticket, accessed_by=request.user)
            return Response(serialized.data)

    @action(methods=['POST'], detail=True)
    def comment(self, request, pk):
        ticket = Ticket.objects.accessed_by(request.user).filter(pk=pk).first()
        if ticket:
            serialized = CommentAddSerializer(data=request.data)
            if serialized.is_valid(raise_exception=True):
                comment = serialized.add(ticket, request.user)
                serialized = CommentAddedSerializer(comment)
                return Response(serialized.data)
            return Response(serialized.error, status=status.HTTP_403_FORBIDDEN)
        else:
            raise Http404

    @action(methods=['GET'], detail=True)
    def comments(self, request, pk):
        ticket = Ticket.objects.accessed_by(request.user).filter(pk=pk).first()
        if ticket:
            comments = Comment.objects.filter(object_id=pk).order_by('id')
            serialized = CommentSerializer(comments, many=True)
            return Response(serialized.data)
        else:
            raise Http404

    @action(methods=['GET'], detail=True)
    def logs(self, request, pk):
        ticket = Ticket.objects.accessed_by(request.user).filter(pk=pk).first()

        if ticket:
            logs = TicketLog.objects.filter(ticket_id=ticket.id).select_related('added_by').order_by('-id')
            serialized = TicketLogSerializer(logs, many=True)
            return Response(serialized.data)
        else:
            raise Http404




class TicketRatingView(viewsets.GenericViewSet):
    serializer_class = TicketRatingSerializer
    pagination_class = Pagination

    @action(methods=['POST'], detail=True)
    def ticket_rating(self, request, pk):
        try:
            ticket = Ticket.objects.get(pk=int(pk))

            serialized = TicketRatingSerializer(data=request.data)
            if serialized.is_valid(raise_exception=True):
                rating = serialized.rate(ticket)
                serialized = TicketRatingSerializer(rating)
                return Response(serialized.data)
            return Response(serialized.error, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            print(e)
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['PUT'], detail=True)
    def rating_update(self, request, pk):
        try:
            ticket_rating_update = Settings.objects.get(key='time_limit_to_edit_rating')

            rating = TicketRating.objects.filter(ticket__id=pk)

            if not rating:
                return Response({"error": "Ticket not found."}, status=status.HTTP_200_OK)

            data = {
                'rating': request.data['rating'],
                'comment': request.data['comment']
            }

            rating_updated = rating.filter(created_at__gt=(timezone.now() - \
                                                           timedelta(hours=int(ticket_rating_update.value)))).update(
                **data)

            if rating_updated:
                serializer = TicketRatingSerializer(data)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Time is up."}, status=status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    # return all unrated ticket by ticket owner.
    @action(methods=['GET'], detail=False)
    def unrated_tickets(self, request):
        tickets = Ticket.objects \
            .filter(status=TicketStatus.Completed.value, ticket_rating=None) \
            .created_by(request.user) \
            .order_by('-id')

        page = self.paginate_queryset(tickets)
        serializer = MyTicketSerializer(page, accessed_by=request.user, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
