from datetime import datetime

from django.contrib import admin
from django.contrib.auth.hashers import make_password
from django import forms

from tgbot.models import Role, Authorization, CustomUser, Question, Tournament, TournamentSchedule, Weekday, Location, \
    PlacePoints


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """"
    Настраивает админку для модели Role
    """
    list_display = [
        'role_name',
        'is_active',
        'is_staff',
        'is_superuser'
    ]
    list_filter = [
        'is_active',
        'is_staff',
        'is_superuser'
    ]
    search_fields = [
        'role_name'
    ]


@admin.register(Authorization)
class AuthorizationAdmin(admin.ModelAdmin):
    """"
    Настраивает админку для модели Authorization
    """
    list_display = [
        'telegram_id',
        'full_name',
        'telegram_nickname',
        'date_of_birth',
        'phone_number',
        'role'
    ]
    search_fields = [
        'uid',
        'registration_datetime',
        'full_name',
        'date_of_birth',
        'phone_number',
        'telegram_nickname',
        'telegram_id',
        'role',
        'password'
    ]


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    """"
    Настраивает админку для модели CustomUser
    """
    list_display = [
        'username',
        'role'
    ]

    def save_model(self, request, obj, form, change):
        password = form.cleaned_data.get('password')

        if password:
            if 'pbkdf2' not in password:
                obj.password = make_password(form.cleaned_data['password'])
            obj.save()


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """"
    Настраивает админку для модели Question
    """
    list_display = [
        'id',
        'tour_id',
        'tour_question_number_id',
        'question_text',
        'correct_answer'
    ]
    list_filter = [
        'tour_id'
    ]
    search_fields = [
        'question_text'
    ]
    list_per_page = 20


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    """"
    Настраивает админку для модели Tournament
    """
    list_display = [
        'id',
        'tournament_name',
        'description',
    ]
    list_filter = [
        'id'
    ]
    search_fields = [
        'tournament_name',
        'description',
    ]


@admin.register(TournamentSchedule)
class TournamentScheduleAdmin(admin.ModelAdmin):
    """"
    Настраивает админку для модели TournamentSchedule
    """
    # form = TournamentScheduleForm
    list_display = [
        'tournament',
        'tournament_date',
        'weekday',
        'begin_time',
        'close_time',
        'location',
        'details',
        'image'
    ]

    search_fields = [
        'tournament',
        'location',
        'details',
    ]

    ordering = [
        'date',
        'start_time',
        'end_time',
    ]

    exclude = [
        'weekday',
    ]

    def tournament_date(self, obj):
        return obj.date.strftime('%d.%m.%Y')

    def begin_time(self, obj):
        return obj.start_time.strftime('%H:%M')

    def close_time(self, obj):
        return obj.end_time.strftime('%H:%M')


@admin.register(Weekday)
class WeekdayAdmin(admin.ModelAdmin):
    """"
    Настраивает админку для модели Weekday
    """
    list_display = [
        'id',
        'name',
    ]

    search_fields = [
        'name',
    ]


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """"
    Настраивает админку для модели Location
    """
    list_display = [
        'id',
        'name',
        'address'
    ]

    search_fields = [
        'name',
        'address'
    ]


@admin.register(PlacePoints)
class PlacePointsAdmin(admin.ModelAdmin):
    list_display = [
        'place',
        'points'
    ]

    search_fields = [
        'place',
    ]

    ordering = [
        'place',
    ]

    list_filter = [
        'points',
    ]
