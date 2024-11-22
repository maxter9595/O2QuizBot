import os
import time
import random
import re
from io import BytesIO
from itertools import groupby

import django
import telebot
import pandas as pd
from django.core.exceptions import ObjectDoesNotExist
from telebot import types
from openpyxl import Workbook
from datetime import datetime
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

os.environ.setdefault(
    key='DJANGO_SETTINGS_MODULE',
    value='quiz.settings'
)
django.setup()

from quiz.settings import BOT_TOKEN
from tgbot.models import Authorization, CustomUser, PointsTransaction, Question, Tournament, PointsTournament, \
    Standings, TournamentSchedule, Weekday, Location, PlacePoints

bot = telebot.TeleBot(BOT_TOKEN)


def update_standings_places():
    """
    Обновляет места в турнирной таблице
    """
    standings_list = Standings.objects.order_by('-tournament_points')
    quiz_standings_list = Standings.objects.order_by('-quiz_points')
    total_standings_list = Standings.objects.order_by('-total_points', 'full_name')

    for index, standings_group in enumerate(
            groupby(standings_list, key=lambda x: x.tournament_points), start=1
    ):
        for standings in standings_group[1]:
            standings.tournament_place = index
            standings.save()

    for index, quiz_standings_group in enumerate(
            groupby(quiz_standings_list, key=lambda x: x.quiz_points), start=1
    ):
        for quiz_standings in quiz_standings_group[1]:
            quiz_standings.quiz_place = index
            quiz_standings.save()

    for index, total_standings_group in enumerate(
            groupby(total_standings_list, key=lambda x: (x.total_points, x.full_name)), start=1
    ):
        for total_standings in total_standings_group[1]:
            total_standings.final_place = index
            total_standings.save()


def update_tournament_points(telegram_id):
    """"
    Выводит общие очки, набранные пользователем во время турнира
    """
    auth_data = Authorization.objects.filter(
        telegram_id=telegram_id,
    )
    telegram_id = auth_data.first()

    tournament_sender_data = PointsTournament.objects.filter(
        sender_telegram_id=telegram_id,
    )

    if tournament_sender_data:
        tournament_points = 0
        points_received_or_transferred = 0
        bonuses = 0
        total_transfer_loss = 0
        total_transfer_income = 0

        for item in tournament_sender_data:
            tournament_points += item.tournament_points if item.tournament_points else 0
            points_received_or_transferred += item.points_received_or_transferred if item.points_received_or_transferred else 0
            bonuses += item.bonuses if item.bonuses else 0
            total_transfer_loss += item.points_transferred if item.points_transferred else 0

        sender_data_vals = [
            tournament_points,
            points_received_or_transferred,
            bonuses,
        ]

        tournament_receiver_data = PointsTournament.objects.filter(
            receiver_telegram_id=telegram_id,
        )

        if tournament_receiver_data:
            for item in tournament_receiver_data:
                total_transfer_income += item.points_transferred if item.points_transferred else 0

        standing_participant = Standings.objects.filter(
            participant_telegram=telegram_id,
        )

        auth_data = Authorization.objects.filter(
            telegram_id=telegram_id,
        )

        if not standing_participant.exists() and auth_data.exists():
            standing_participant = Standings(
                participant_telegram=telegram_id,
                full_name=auth_data.first().full_name,
            ).save()

            standing_participant = Standings.objects.filter(
                participant_telegram=telegram_id,
            )

        if standing_participant:
            standing_participant.update(
                tournament_points=sum(
                    sender_data_vals
                ) + (
                    total_transfer_income - total_transfer_loss
                ),
            )

            standing_participant.update(
                total_points=standing_participant.first().quiz_points + standing_participant.first().tournament_points
            )
            update_standings_places()


def update_quiz_points(telegram_id):
    """"
    Выводит общие очки, набранные пользователем во время викторины
    """
    auth_data = Authorization.objects.filter(
        telegram_id=telegram_id,
    )
    telegram_id = auth_data.first()

    tournament_sender_data = PointsTransaction.objects.filter(
        sender_telegram_id=telegram_id,
    )

    if tournament_sender_data:
        tournament_points = 0
        points_received_or_transferred = 0
        bonuses = 0
        total_transfer_loss = 0
        total_transfer_income = 0

        for item in tournament_sender_data:
            tournament_points += item.tournament_points if item.tournament_points else 0
            points_received_or_transferred += item.points_received_or_transferred if item.points_received_or_transferred else 0
            bonuses += item.bonuses if item.bonuses else 0
            total_transfer_loss += item.points_transferred if item.points_transferred else 0

        sender_data_vals = [
            tournament_points,
            points_received_or_transferred,
            bonuses,
        ]

        tournament_receiver_data = PointsTransaction.objects.filter(
            receiver_telegram_id=telegram_id,
        )

        if tournament_receiver_data:
            for item in tournament_receiver_data:
                total_transfer_income += item.points_transferred if item.points_transferred else 0

        standing_participant = Standings.objects.filter(
            participant_telegram=telegram_id,
        )

        auth_data = Authorization.objects.filter(
            telegram_id=telegram_id,
        )

        if not standing_participant.exists() and auth_data.exists():
            standing_participant = Standings(
                participant_telegram=telegram_id,
                full_name=auth_data.first().full_name,
            ).save()

            standing_participant = Standings.objects.filter(
                participant_telegram=telegram_id,
            )

        if standing_participant:
            standing_participant.update(
                quiz_points=sum(
                    sender_data_vals
                ) + (
                    total_transfer_income - total_transfer_loss
                )
            )

            standing_participant.update(
                total_points=standing_participant.first().quiz_points + standing_participant.first().tournament_points
            )
            update_standings_places()


def hello_text():
    return '\n'.join([
                'Добро пожаловать!',
                '',
                'Предлагаем Вам широкий спектр услуг в организации междугородных и ' +\
                'международных перевозок грузов большегрузным автомобильным транспортом на ' +\
                'территории РФ и СНГ.',
                '',
                'Транспортная компания «О2RUS» успешно работает на рынке транспортных услуг ' +\
                'с 2005 года и имеет репутацию надежного партнера.',
                '',
                'Наша миссия – оказание качественных услуг по организации автомобильных грузоперевозок ' +\
                'в комплексе с минимизацией затрат на логистику.',
                '',
                'За 15 лет Клиентами компании стали многие крупные и средние российские предприятия.'
                '',
                'Автопарк транспортной компании «О2RUS» на сегодняшний день составляет более 320 ' +\
                'современных автопоездов не старше 4 лет.',
                '',
                'Офис: РФ, РТ, Набережные Челны, пр. Мира, д. 49 "Б", 6 этаж, ' +\
                'офисы: 10/15/19 Тел.: +7 (8552) 20-00-22 E-mail: o2rus@o2rus.ru  ',
                '',
                '📝 Для регистрации введите /register',
                '🔒 Для авторизации введите /login',
                '🔒 Для изменения пароля введите /password'
            ])


@bot.message_handler(commands=['start'])
def start(message):
    """
    Запускает бота для регистрации и авторизации пользователей + для добавления/изменения афиш и баннеров для админов
    """
    markup_start = True
    user_auth = Authorization.objects.filter(telegram_id=message.from_user.id)

    if user_auth.exists():
        user_id = user_auth.first().id
        custom_user = CustomUser.objects.filter(id=user_id)

        if custom_user.exists():
            if custom_user.first().is_authorized:
                bot.send_message(
                    chat_id=message.chat.id,
                    text='Вы уже авторизованы',
                )
                markup_start = False

    if markup_start:
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        btn_register = types.KeyboardButton(
            text='Регистрация'
        )

        btn_login = types.KeyboardButton(
            text='Авторизация'
        )

        btn_password = types.KeyboardButton(
            text='Забыл пароль'
        )

        mon_btn = types.KeyboardButton(
            text='пн'
        )

        tue_btn = types.KeyboardButton(
            text='вт'
        )

        wed_btn = types.KeyboardButton(
            text='ср'
        )

        thu_btn = types.KeyboardButton(
            text='чт'
        )

        fri_btn = types.KeyboardButton(
            text='пт'
        )

        sat_btn = types.KeyboardButton(
            text='сб'
        )

        sun_btn = types.KeyboardButton(
            text='вс'
        )

        markup.add(
            mon_btn,
            tue_btn,
            wed_btn,
            thu_btn,
            fri_btn,
            sat_btn,
            sun_btn,
            btn_register,
            btn_login,
            btn_password
        )

        bot.reply_to(
            message=message,
            text=hello_text(),
            reply_markup=markup,
        )


@bot.message_handler(func=lambda message: message.text in ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс'])
def test_function_text(message):
    """
    Позволяет начать работать с данными турниров в разрезе выбранной недели
    """
    day_of_week = message.text

    user_auth = Authorization.objects.filter(telegram_id=message.from_user.id)
    user_id = user_auth.first().id
    custom_user = CustomUser.objects.filter(id=user_id).first()

    bad_message = False

    if message.text == "Главное меню":
        main_menu(message)
        bad_message = True

    if message.text == "Назад к регистрации":
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        btn_register = types.KeyboardButton(
            text='Регистрация'
        )

        btn_login = types.KeyboardButton(
            text='Авторизация'
        )

        btn_password = types.KeyboardButton(
            text='Забыл пароль'
        )

        mon_btn = types.KeyboardButton(
            text='пн'
        )

        tue_btn = types.KeyboardButton(
            text='вт'
        )

        wed_btn = types.KeyboardButton(
            text='ср'
        )

        thu_btn = types.KeyboardButton(
            text='чт'
        )

        fri_btn = types.KeyboardButton(
            text='пт'
        )

        sat_btn = types.KeyboardButton(
            text='сб'
        )

        sun_btn = types.KeyboardButton(
            text='вс'
        )

        markup.add(
            mon_btn,
            tue_btn,
            wed_btn,
            thu_btn,
            fri_btn,
            sat_btn,
            sun_btn,
            btn_register,
            btn_login,
            btn_password
        )

        bot.reply_to(
            message=message,
            text=hello_text(),
            reply_markup=markup,
        )

        bad_message = True

    if custom_user:
        if not bad_message:
            if custom_user.role_id in [1, 2]:
                markup = types.ReplyKeyboardMarkup(
                    resize_keyboard=True
                )

                add_banner = types.KeyboardButton(
                    text=f"Добавить/Изменить баннер",
                )

                change_tournament_info = types.KeyboardButton(
                    text=f"Добавить/Изменить афишу",
                )

                watch_tournament_info = types.KeyboardButton(
                    text=f"Посмотреть расписание",
                )

                auth_data = Authorization.objects.filter(
                    telegram_id=message.from_user.id
                )

                custom_user = CustomUser.objects.get(
                    username_id=auth_data.first().id
                )

                if custom_user.is_authorized:
                    get_registration = types.KeyboardButton(
                        text=f"Главное меню",
                    )

                else:
                    get_registration = types.KeyboardButton(
                        text='Назад к регистрации',
                    )

                markup.add(
                    add_banner,
                    change_tournament_info,
                    watch_tournament_info,
                    get_registration
                )

                response = bot.reply_to(
                    message=message,
                    text="Выберите, что хотите сделать",
                    reply_markup=markup,
                )

                bot.register_next_step_handler(
                    response,
                    work_with_tournament_db,
                    day_of_week
                )

            else:
                weekday_dict = {
                    'пн': 1,
                    'вт': 2,
                    'ср': 3,
                    'чт': 4,
                    'пт': 5,
                    'сб': 6,
                    'вс': 7,
                }

                schedule = TournamentSchedule.objects.filter(
                    weekday=weekday_dict.get(day_of_week)
                ).order_by('date')

                if schedule:
                    text_info_list = []
                    image_path = []
                    is_image = False

                    for event in schedule:
                        start = event.start_time.strftime('%H:%M')
                        end = event.end_time.strftime('%H:%M')
                        event_date = event.date.strftime('%d.%m.%Y')

                        event_time = f"<b>Дата и время турнира:</b> {event_date}, {start} - {end}"
                        event_location = f"<b>Место проведения:</b> {event.location.name} ({event.location.address})"
                        details = f"<b>Описание турнира:</b> {event.details}"

                        if event.image:
                            is_image = True
                            image_path.append(event.image)

                        text_info_list.append(
                            '\n'.join(
                                [f'<b>{event.tournament}</b>', ' ', event_time, event_location, details]
                            )
                        )

                    if text_info_list:
                        for text in text_info_list:
                            if is_image:
                                try:
                                    with open('./' + image_path[0].url, 'rb') as photo:
                                        bot.send_photo(
                                            chat_id=message.chat.id,
                                            photo=photo,
                                            caption=text,
                                            parse_mode='HTML'
                                        )

                                except Exception as e:
                                    print(
                                        f"Ошибка при отправке фото: {e}"
                                    )

                                    bot.send_message(
                                        message.chat.id,
                                        text,
                                        parse_mode='HTML'
                                    )

                            else:
                                bot.send_message(
                                    message.chat.id,
                                    text,
                                    parse_mode='HTML'
                                )

                elif message.text == 'Главное меню':
                    main_menu(message)

                else:
                    bot.send_message(
                        message.chat.id,
                        'На этот день нет турниров',
                    )

                    auth_data = Authorization.objects.filter(
                        telegram_id=message.from_user.id
                    )

                    custom_user = CustomUser.objects.get(
                        username_id=auth_data.first().id
                    )

                    if custom_user.is_authorized:
                        main_menu(message)

                    else:
                        markup = types.ReplyKeyboardMarkup(
                            resize_keyboard=True
                        )

                        btn_register = types.KeyboardButton(
                            text='Регистрация'
                        )

                        btn_login = types.KeyboardButton(
                            text='Авторизация'
                        )

                        btn_password = types.KeyboardButton(
                            text='Забыл пароль'
                        )

                        mon_btn = types.KeyboardButton(
                            text='пн'
                        )

                        tue_btn = types.KeyboardButton(
                            text='вт'
                        )

                        wed_btn = types.KeyboardButton(
                            text='ср'
                        )

                        thu_btn = types.KeyboardButton(
                            text='чт'
                        )

                        fri_btn = types.KeyboardButton(
                            text='пт'
                        )

                        sat_btn = types.KeyboardButton(
                            text='сб'
                        )

                        sun_btn = types.KeyboardButton(
                            text='вс'
                        )

                        markup.add(
                            mon_btn,
                            tue_btn,
                            wed_btn,
                            thu_btn,
                            fri_btn,
                            sat_btn,
                            sun_btn,
                            btn_register,
                            btn_login,
                            btn_password
                        )

                        bot.send_message(
                            chat_id=message.chat.id,
                            text="Меню регистрации",
                            reply_markup=markup
                        )

    else:
        bot.send_message(
            chat_id=message.chat.id,
            text='Вы не зарегистрированы. Для регистрации введите /register"',
        )


def work_with_tournament_db(message, day_of_week):
    """
    Позволяет начать работу с афишей или баннеров в зависимости от выбора конкретной кнопки в чат-боте ТГ
    """
    weekday_dict = {
        'пн': 1,
        'вт': 2,
        'ср': 3,
        'чт': 4,
        'пт': 5,
        'сб': 6,
        'вс': 7,
    }

    weekday_id = weekday_dict.get(day_of_week)

    tournament_schedule = TournamentSchedule.objects.filter(
        weekday_id=weekday_id
    )

    if message.text == "Добавить/Изменить баннер":
        if tournament_schedule.exists():
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            tournament_dict = {}

            for tournament_item in tournament_schedule:
                tournament_id = tournament_item.id
                tournament_name = tournament_item.tournament.tournament_name
                date = tournament_item.date.strftime('%d.%m.%Y')
                start = tournament_item.start_time.strftime('%H:%M')
                end = tournament_item.end_time.strftime('%H:%M')

                tournament_description = f'{tournament_name} ({date} {start}-{end}, Турнир №{tournament_id})'
                tournament_dict[tournament_description] = tournament_id

                markup.add(
                    types.KeyboardButton(
                        text=tournament_description
                    )
                )

            auth_data = Authorization.objects.filter(
                telegram_id=message.from_user.id
            )

            custom_user = CustomUser.objects.get(
                username_id=auth_data.first().id
            )

            if custom_user.is_authorized:
                markup.add(
                    types.KeyboardButton(
                        text='Главное меню'
                    )
                )

            else:
                markup.add(
                    types.KeyboardButton(
                        text='Назад к регистрации'
                    )
                )

            response = bot.send_message(
                message.chat.id,
                f"Пожалуйста, выберите турнир для добавления/изменения баннера",
                reply_markup=markup
            )

            bot.register_next_step_handler(
                response,
                get_image,
                tournament_dict
            )

        else:
            bot.send_message(
                chat_id=message.chat.id,
                text=f"Нет информации о турнирах, проводимых в {day_of_week}"
            )

            auth_data = Authorization.objects.filter(
                telegram_id=message.from_user.id
            )

            custom_user = CustomUser.objects.get(
                username_id=auth_data.first().id
            )

            if not custom_user.is_authorized:
                markup = types.ReplyKeyboardMarkup(
                    resize_keyboard=True
                )

                btn_register = types.KeyboardButton(
                    text='Регистрация'
                )

                btn_login = types.KeyboardButton(
                    text='Авторизация'
                )

                btn_password = types.KeyboardButton(
                    text='Забыл пароль'
                )

                mon_btn = types.KeyboardButton(
                    text='пн'
                )

                tue_btn = types.KeyboardButton(
                    text='вт'
                )

                wed_btn = types.KeyboardButton(
                    text='ср'
                )

                thu_btn = types.KeyboardButton(
                    text='чт'
                )

                fri_btn = types.KeyboardButton(
                    text='пт'
                )

                sat_btn = types.KeyboardButton(
                    text='сб'
                )

                sun_btn = types.KeyboardButton(
                    text='вс'
                )

                markup.add(
                    mon_btn,
                    tue_btn,
                    wed_btn,
                    thu_btn,
                    fri_btn,
                    sat_btn,
                    sun_btn,
                    btn_register,
                    btn_login,
                    btn_password
                )

                bot.send_message(
                    chat_id=message.chat.id,
                    text="Меню регистрации",
                    reply_markup=markup
                )

            else:
                main_menu(message)

    elif message.text == "Добавить/Изменить афишу":
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        add_poster = types.KeyboardButton(
            text="Добавить афишу",
        )

        change_poster = types.KeyboardButton(
            text="Изменить афишу",
        )

        auth_data = Authorization.objects.filter(
            telegram_id=message.from_user.id
        )

        custom_user = CustomUser.objects.get(
            username_id=auth_data.first().id
        )

        if custom_user.is_authorized:
            get_registration = markup.add(
                types.KeyboardButton(
                    text='Главное меню'
                )
            )

        else:
            get_registration = markup.add(
                types.KeyboardButton(
                    text='Назад к регистрации'
                )
            )

        markup.add(
            add_poster,
            change_poster,
            get_registration
        )

        response = bot.reply_to(
            message=message,
            text="Уточните, что хотите сделать с афишей",
            reply_markup=markup,
        )

        bot.register_next_step_handler(
            response,
            work_with_schedule_db,
            weekday_id,
            day_of_week,
            tournament_schedule
        )

    elif message.text == 'Посмотреть расписание':
        weekday_dict = {
            'пн': 1,
            'вт': 2,
            'ср': 3,
            'чт': 4,
            'пт': 5,
            'сб': 6,
            'вс': 7,
        }

        schedule = TournamentSchedule.objects.filter(
            weekday=weekday_dict.get(day_of_week)
        ).order_by('date')

        if schedule:
            text_info_list = []
            image_path = []
            is_image = False

            for event in schedule:
                start = event.start_time.strftime('%H:%M')
                end = event.end_time.strftime('%H:%M')
                event_date = event.date.strftime('%d.%m.%Y')

                event_time = f"<b>Дата и время турнира:</b> {event_date}, {start} - {end}"
                event_location = f"<b>Место проведения:</b> {event.location.name} ({event.location.address})"
                details = f"<b>Описание турнира:</b> {event.details}"

                if event.image:
                    is_image = True
                    image_path.append(event.image)

                text_info_list.append(
                    '\n'.join(
                        [f'<b>{event.tournament}</b>', ' ', event_time, event_location, details]
                    )
                )

            if text_info_list:
                for text in text_info_list:
                    if is_image:
                        try:
                            with open('./' + image_path[0].url, 'rb') as photo:
                                bot.send_photo(
                                    chat_id=message.chat.id,
                                    photo=photo,
                                    caption=text,
                                    parse_mode='HTML'
                                )

                        except Exception as e:
                            print(
                                f"Ошибка при отправке фото: {e}"
                            )

                            bot.send_message(
                                message.chat.id,
                                text,
                                parse_mode='HTML'
                            )

                    else:
                        bot.send_message(
                            message.chat.id,
                            text,
                            parse_mode='HTML'
                        )

        elif message.text == 'Главное меню':
            main_menu(message)

        else:
            bot.send_message(
                message.chat.id,
                'На этот день нет турниров',
            )

    elif message.text == "Назад к регистрации":
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        btn_register = types.KeyboardButton(
            text='Регистрация'
        )

        btn_login = types.KeyboardButton(
            text='Авторизация'
        )

        btn_password = types.KeyboardButton(
            text='Забыл пароль'
        )

        mon_btn = types.KeyboardButton(
            text='пн'
        )

        tue_btn = types.KeyboardButton(
            text='вт'
        )

        wed_btn = types.KeyboardButton(
            text='ср'
        )

        thu_btn = types.KeyboardButton(
            text='чт'
        )

        fri_btn = types.KeyboardButton(
            text='пт'
        )

        sat_btn = types.KeyboardButton(
            text='сб'
        )

        sun_btn = types.KeyboardButton(
            text='вс'
        )

        markup.add(
            mon_btn,
            tue_btn,
            wed_btn,
            thu_btn,
            fri_btn,
            sat_btn,
            sun_btn,
            btn_register,
            btn_login,
            btn_password
        )

        bot.send_message(
            chat_id=message.chat.id,
            text="Меню регистрации",
            reply_markup=markup
        )

    elif message.text == 'Главное меню':
        main_menu(message)

    else:
        bot.send_message(
            chat_id=message.chat.id,
            text='Некорректный ответ',
        )


def work_with_schedule_db(message, weekday_id, day_of_week, tournament_schedule):
    """
    Начинает работу с афишей. Здесь админ выбирает добавление или изменение афиши
    """
    if message.text == "Добавить афишу":
        response = bot.send_message(
            message.chat.id,
            f"Введите название турнира",
        )

        bot.register_next_step_handler(
            response,
            get_tournament_name,
            weekday_id
        )

    elif message.text == "Изменить афишу":
        if tournament_schedule.exists():
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            tournament_dict = {}

            for tournament_item in tournament_schedule:
                tournament_id = tournament_item.id
                tournament_name = tournament_item.tournament.tournament_name
                date = tournament_item.date.strftime('%d.%m.%Y')
                start = tournament_item.start_time.strftime('%H:%M')
                end = tournament_item.end_time.strftime('%H:%M')

                tournament_description = f'{tournament_name} ({date} {start}-{end}, Турнир №{tournament_id})'
                tournament_dict[tournament_description] = tournament_id

                markup.add(
                    types.KeyboardButton(
                        text=tournament_description
                    )
                )

            auth_data = Authorization.objects.filter(
                telegram_id=message.from_user.id
            )

            custom_user = CustomUser.objects.get(
                username_id=auth_data.first().id
            )

            if custom_user.is_authorized:
                markup.add(
                    types.KeyboardButton(
                        text='Главное меню'
                    )
                )

            else:
                markup.add(
                    types.KeyboardButton(
                        text='Назад к регистрации'
                    )
                )

            response = bot.send_message(
                message.chat.id,
                f"Пожалуйста, выберите турнир для изменения афиши",
                reply_markup=markup
            )

            bot.register_next_step_handler(
                response,
                change_poster,
                tournament_dict,
                weekday_id
            )

        else:
            bot.send_message(
                chat_id=message.chat.id,
                text=f"Нет информации о турнирах, проводимых в {day_of_week}"
            )

            auth_data = Authorization.objects.filter(
                telegram_id=message.from_user.id
            )

            custom_user = CustomUser.objects.get(
                username_id=auth_data.first().id
            )

            if not custom_user.is_authorized:
                markup = types.ReplyKeyboardMarkup(
                    resize_keyboard=True
                )

                btn_register = types.KeyboardButton(
                    text='Регистрация'
                )

                btn_login = types.KeyboardButton(
                    text='Авторизация'
                )

                btn_password = types.KeyboardButton(
                    text='Забыл пароль'
                )

                mon_btn = types.KeyboardButton(
                    text='пн'
                )

                tue_btn = types.KeyboardButton(
                    text='вт'
                )

                wed_btn = types.KeyboardButton(
                    text='ср'
                )

                thu_btn = types.KeyboardButton(
                    text='чт'
                )

                fri_btn = types.KeyboardButton(
                    text='пт'
                )

                sat_btn = types.KeyboardButton(
                    text='сб'
                )

                sun_btn = types.KeyboardButton(
                    text='вс'
                )

                markup.add(
                    mon_btn,
                    tue_btn,
                    wed_btn,
                    thu_btn,
                    fri_btn,
                    sat_btn,
                    sun_btn,
                    btn_register,
                    btn_login,
                    btn_password
                )

                bot.send_message(
                    chat_id=message.chat.id,
                    text="Меню регистрации",
                    reply_markup=markup
                )

            else:
                main_menu(message)

    elif message.text in ["Назад к регистрации", "Главное меню"]:
        auth_data = Authorization.objects.filter(
            telegram_id=message.from_user.id
        )

        custom_user = CustomUser.objects.get(
            username_id=auth_data.first().id
        )

        if not custom_user.is_authorized and message.text == "Назад к регистрации":
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_register = types.KeyboardButton(
                text='Регистрация'
            )

            btn_login = types.KeyboardButton(
                text='Авторизация'
            )

            btn_password = types.KeyboardButton(
                text='Забыл пароль'
            )

            mon_btn = types.KeyboardButton(
                text='пн'
            )

            tue_btn = types.KeyboardButton(
                text='вт'
            )

            wed_btn = types.KeyboardButton(
                text='ср'
            )

            thu_btn = types.KeyboardButton(
                text='чт'
            )

            fri_btn = types.KeyboardButton(
                text='пт'
            )

            sat_btn = types.KeyboardButton(
                text='сб'
            )

            sun_btn = types.KeyboardButton(
                text='вс'
            )

            markup.add(
                mon_btn,
                tue_btn,
                wed_btn,
                thu_btn,
                fri_btn,
                sat_btn,
                sun_btn,
                btn_register,
                btn_login,
                btn_password
            )

            bot.send_message(
                chat_id=message.chat.id,
                text="Меню регистрации",
                reply_markup=markup
            )

        else:
            main_menu(message)


def get_tournament_name(message, weekday_id):
    """
    Фиксирует название турнира и запрашивает дату проведения турнира
    """
    tournament_name = message.text

    tournament_data = Tournament.objects.filter(
        tournament_name=tournament_name
    ).filter()

    tournament_data_dict = {}
    if not tournament_data.exists():
        tournament_data_dict['tournament_name'] = tournament_name

        response = bot.send_message(
            message.chat.id,
            f"Введите дату и время проведения турнира в формате ДД.ММ.ГГГГ ЧЧ:ММ-ЧЧ:ММ (пример: 23.09.2024 20:00-20:20)"
        )

        bot.register_next_step_handler(
            response,
            get_tournament_date,
            weekday_id,
            tournament_data_dict
        )

    else:
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        add_poster = types.KeyboardButton(
            text="Добавить афишу",
        )

        change_poster = types.KeyboardButton(
            text="Изменить афишу",
        )

        auth_data = Authorization.objects.filter(
            telegram_id=message.from_user.id
        )

        custom_user = CustomUser.objects.get(
            username_id=auth_data.first().id
        )

        if custom_user.is_authorized:
            get_registration = markup.add(
                types.KeyboardButton(
                    text='Главное меню'
                )
            )

        else:
            get_registration = markup.add(
                types.KeyboardButton(
                    text='Назад к регистрации'
                )
            )

        markup.add(
            add_poster,
            change_poster,
            get_registration
        )

        response = bot.reply_to(
            message=message,
            text="Афиша с таким названием уже существует",
            reply_markup=markup,
        )


def get_tournament_date(message, weekday_id, tournament_data_dict):
    """
    Фиксирует и проверяет дату проведения турнира. Запрашивает доступное место для проведения турнира
    """
    text_answer = ""
    date_time_input = message.text.strip()
    date_time_pattern = r'^\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}-\d{2}:\d{2}$'

    if not re.match(date_time_pattern, date_time_input):
        text_answer += "Неверный формат. Пожалуйста, введите данные в формате ДД.ММ.ГГГГ ЧЧ:ММ-ЧЧ:ММ"
    else:
        date_str, time_str = date_time_input.split(' ')

        try:
            tournament_date = datetime.strptime(date_str, "%d.%m.%Y").date()
        except ValueError:
            text_answer += "Неверная дата. Пожалуйста, введите дату в формате ДД.ММ.ГГГГ"

        if tournament_date.isoweekday() != weekday_id:
            text_answer += f"Дата {date_str} не соответствует дню недели"
        else:
            tournament_data_dict['weekday_id'] = weekday_id

        start_time_str, end_time_str = time_str.split('-')
        time_pattern = r'^\d{2}:\d{2}$'

        if not re.match(time_pattern, start_time_str) or not re.match(time_pattern, end_time_str):
            text_answer += "Неверный формат времени. Пожалуйста, введите время в формате ЧЧ:ММ-ЧЧ:ММ."
        else:
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time = datetime.strptime(end_time_str, "%H:%M").time()

            if start_time >= end_time:
                text_answer += "Время начала должно быть меньше времени окончания"

            else:
                tournament_data_dict['date'] = tournament_date
                tournament_data_dict['start_time'] = start_time
                tournament_data_dict['end_time'] = end_time
                text_answer += "Выберите место проведения турнира"

        if text_answer == "Выберите место проведения турнира":
            locations = Location.objects.all()

            if locations:
                markup = types.ReplyKeyboardMarkup(
                    resize_keyboard=True
                )

                address_dict = {}
                for location in locations:
                    address_info_text = f'{location.name} ({location.address})'
                    address_dict[address_info_text] = location.id

                    btn = types.KeyboardButton(
                        text=address_info_text
                    )
                    markup.add(btn)

                response = bot.send_message(
                    message.chat.id,
                    f"Выберите доступное место проведения турнира",
                    reply_markup=markup
                )

                bot.register_next_step_handler(
                    response,
                    get_poster_place,
                    tournament_data_dict,
                    address_dict,
                )

            else:
                markup = types.ReplyKeyboardMarkup(
                    resize_keyboard=True
                )

                add_poster = types.KeyboardButton(
                    text="Добавить афишу",
                )

                change_poster = types.KeyboardButton(
                    text="Изменить афишу",
                )

                auth_data = Authorization.objects.filter(
                    telegram_id=message.from_user.id
                )

                custom_user = CustomUser.objects.get(
                    username_id=auth_data.first().id
                )

                if custom_user.is_authorized:
                    get_registration = markup.add(
                        types.KeyboardButton(
                            text='Главное меню'
                        )
                    )

                else:
                    get_registration = markup.add(
                        types.KeyboardButton(
                            text='Назад к регистрации'
                        )
                    )

                markup.add(
                    add_poster,
                    change_poster,
                    get_registration
                )

                response = bot.reply_to(
                    message=message,
                    text="В базе нет доступных мест проведения. Обратитесь к администратору для добавления новых мест",
                    reply_markup=markup,
                )

        else:
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            add_poster = types.KeyboardButton(
                text="Добавить афишу",
            )

            change_poster = types.KeyboardButton(
                text="Изменить афишу",
            )

            auth_data = Authorization.objects.filter(
                telegram_id=message.from_user.id
            )

            custom_user = CustomUser.objects.get(
                username_id=auth_data.first().id
            )

            if custom_user.is_authorized:
                get_registration = markup.add(
                    types.KeyboardButton(
                        text='Главное меню'
                    )
                )

            else:
                get_registration = markup.add(
                    types.KeyboardButton(
                        text='Назад к регистрации'
                    )
                )

            markup.add(
                add_poster,
                change_poster,
                get_registration
            )

            response = bot.reply_to(
                message=message,
                text=text_answer,
                reply_markup=markup,
            )


def get_poster_place(message, tournament_data_dict, address_dict):
    """
    Фиксирует место проведения турнира и запрашивает описание
    """
    address = message.text
    address_id = address_dict.get(address)
    tournament_data_dict['location_id'] = address_id

    response = bot.reply_to(
        message=message,
        text="Заполните описание турнира",
    )

    bot.register_next_step_handler(
        response,
        get_poster_description,
        tournament_data_dict
    )


def get_poster_description(message, tournament_data_dict):
    """
    Фиксирует описание турнира и добавляет заполненные данные в модель TournamentSchedule
    """
    tournament_data_dict['description'] = message.text

    new_tournament = Tournament.objects.create(
        tournament_name=tournament_data_dict.get('tournament_name'),
        description=tournament_data_dict.get('description'),
    )

    new_schedule = TournamentSchedule.objects.create(
        tournament=new_tournament,
        date=tournament_data_dict.get('date'),
        start_time=tournament_data_dict.get('start_time'),
        end_time=tournament_data_dict.get('end_time'),
        details=tournament_data_dict.get('description'),
        location=Location.objects.get(pk=tournament_data_dict.get('location_id')),
        weekday=Weekday.objects.get(pk=tournament_data_dict.get('weekday_id')),
    )

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    add_poster = types.KeyboardButton(
        text="Добавить афишу",
    )

    change_poster = types.KeyboardButton(
        text="Изменить афишу",
    )

    auth_data = Authorization.objects.filter(
        telegram_id=message.from_user.id
    )

    custom_user = CustomUser.objects.get(
        username_id=auth_data.first().id
    )

    if custom_user.is_authorized:
        get_registration = markup.add(
            types.KeyboardButton(
                text='Главное меню'
            )
        )

    else:
        get_registration = markup.add(
            types.KeyboardButton(
                text='Назад к регистрации'
            )
        )
    markup.add(
        add_poster,
        change_poster,
        get_registration
    )

    bot.send_message(
        message.chat.id,
        f"Афиша успешно добавлена. Турнир '{new_tournament.tournament_name}' был успешно добавлен в расписание",
        reply_markup=markup,
    )


def change_poster(message, tournament_dict, weekday_id):
    """
    Начинает работу над изменениями данных афиши турнира в БД.
    В этом случае админ выбирает то, что хочет изменить в
    расписании конкретного турнира (название турнира,
    дата его проведения и др.)
    """
    tournament_id = tournament_dict.get(message.text)

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    tournament_name = types.KeyboardButton(
        text='Название турнира'
    )

    tournament_date = types.KeyboardButton(
        text='Дата проведения'
    )

    tournament_time = types.KeyboardButton(
        text='Время проведения'
    )

    tournament_place = types.KeyboardButton(
        text='Место проведения'
    )

    tournament_description = types.KeyboardButton(
        text='Описание турнира'
    )

    end_changes = types.KeyboardButton(
        text='Завершить изменения'
    )

    markup.add(
        tournament_name,
        tournament_date,
        tournament_time,
        tournament_place,
        tournament_description,
        end_changes,
    )

    response = bot.send_message(
        message.chat.id,
        f"Выберите любой параметр для изменения. После изменения всех необходимых параметров нажмите 'Завершить изменения'",
        reply_markup=markup
    )

    bot.register_next_step_handler(
        response,
        change_poster_processing,
        tournament_id,
        weekday_id,
    )


def change_poster_processing(message, tournament_id, weekday_id):
    """
    Обрабатывает конкретный выбор, связанный с изменением афиши турнира
    """
    if message.text == 'Название турнира':
        response = bot.send_message(
            message.chat.id,
            f"Введите название турнира",
        )

        bot.register_next_step_handler(
            response,
            change_poster_name,
            tournament_id,
            weekday_id,
        )

    elif message.text == 'Дата проведения':
        response = bot.send_message(
            message.chat.id,
            f"Введите дату проведения в формате ДД.ММ.ГГГГ (пример: 23.09.2024)",
        )

        bot.register_next_step_handler(
            response,
            change_poster_date,
            tournament_id,
            weekday_id,
        )

    elif message.text == 'Время проведения':
        response = bot.send_message(
            message.chat.id,
            f"Введите время проведения в формате ЧЧ:ММ-ЧЧ:ММ (пример: 20:20-20:50)",
        )

        bot.register_next_step_handler(
            response,
            change_poster_time,
            tournament_id,
            weekday_id,
        )

    elif message.text == 'Место проведения':
        locations = Location.objects.all()

        if locations:
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            address_dict = {}
            for location in locations:
                address_info_text = f'{location.name} ({location.address})'
                address_dict[address_info_text] = location.id

                btn = types.KeyboardButton(
                    text=address_info_text
                )
                markup.add(btn)

            response = bot.send_message(
                message.chat.id,
                f"Выберите доступное место проведения турнира",
                reply_markup=markup
            )

            bot.register_next_step_handler(
                response,
                change_poster_choose_place,
                tournament_id,
                weekday_id,
                address_dict,
            )

        else:
            bot.send_message(
                message.chat.id,
                "В базе нет доступных мест проведения. Обратитесь к администратору для добавления новых мест."
            )

            auth_data = Authorization.objects.filter(
                telegram_id=message.from_user.id
            )

            custom_user = CustomUser.objects.get(
                username_id=auth_data.first().id
            )

            if not custom_user.is_authorized:
                markup = types.ReplyKeyboardMarkup(
                    resize_keyboard=True
                )

                btn_register = types.KeyboardButton(
                    text='Регистрация'
                )

                btn_login = types.KeyboardButton(
                    text='Авторизация'
                )

                btn_password = types.KeyboardButton(
                    text='Забыл пароль'
                )

                mon_btn = types.KeyboardButton(
                    text='пн'
                )

                tue_btn = types.KeyboardButton(
                    text='вт'
                )

                wed_btn = types.KeyboardButton(
                    text='ср'
                )

                thu_btn = types.KeyboardButton(
                    text='чт'
                )

                fri_btn = types.KeyboardButton(
                    text='пт'
                )

                sat_btn = types.KeyboardButton(
                    text='сб'
                )

                sun_btn = types.KeyboardButton(
                    text='вс'
                )

                markup.add(
                    mon_btn,
                    tue_btn,
                    wed_btn,
                    thu_btn,
                    fri_btn,
                    sat_btn,
                    sun_btn,
                    btn_register,
                    btn_login,
                    btn_password
                )

                bot.send_message(
                    chat_id=message.chat.id,
                    text="Меню регистрации",
                    reply_markup=markup
                )

            else:
                main_menu(message)

    elif message.text == 'Описание турнира':
        response = bot.send_message(
            message.chat.id,
            f"Введите описание для выбранного турнира",
        )

        bot.register_next_step_handler(
            response,
            change_poster_description,
            tournament_id,
            weekday_id,
        )

    elif message.text == 'Завершить изменения':
        auth_data = Authorization.objects.filter(
            telegram_id=message.from_user.id
        )

        custom_user = CustomUser.objects.get(
            username_id=auth_data.first().id
        )

        if not custom_user.is_authorized:
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_register = types.KeyboardButton(
                text='Регистрация'
            )

            btn_login = types.KeyboardButton(
                text='Авторизация'
            )

            btn_password = types.KeyboardButton(
                text='Забыл пароль'
            )

            mon_btn = types.KeyboardButton(
                text='пн'
            )

            tue_btn = types.KeyboardButton(
                text='вт'
            )

            wed_btn = types.KeyboardButton(
                text='ср'
            )

            thu_btn = types.KeyboardButton(
                text='чт'
            )

            fri_btn = types.KeyboardButton(
                text='пт'
            )

            sat_btn = types.KeyboardButton(
                text='сб'
            )

            sun_btn = types.KeyboardButton(
                text='вс'
            )

            markup.add(
                mon_btn,
                tue_btn,
                wed_btn,
                thu_btn,
                fri_btn,
                sat_btn,
                sun_btn,
                btn_register,
                btn_login,
                btn_password
            )

            bot.send_message(
                chat_id=message.chat.id,
                text="Меню регистрации",
                reply_markup=markup
            )

        else:
            main_menu(message)


def change_poster_description(message, tournament_id, weekday_id):
    """
    Меняет описание афиши турнира
    """
    description = message.text

    poster_data = TournamentSchedule.objects.filter(
        id=tournament_id,
    ).first()

    poster_data.details = description
    poster_data.save()

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    tournament_name = types.KeyboardButton(
        text='Название турнира'
    )

    tournament_date = types.KeyboardButton(
        text='Дата проведения'
    )

    tournament_time = types.KeyboardButton(
        text='Время проведения'
    )

    tournament_place = types.KeyboardButton(
        text='Место проведения'
    )

    tournament_description = types.KeyboardButton(
        text='Описание турнира'
    )

    end_changes = types.KeyboardButton(
        text='Завершить изменения'
    )

    markup.add(
        tournament_name,
        tournament_date,
        tournament_time,
        tournament_place,
        tournament_description,
        end_changes,
    )

    response = bot.send_message(
        message.chat.id,
        f"Изменения успешно сохранены",
        reply_markup=markup
    )

    bot.register_next_step_handler(
        response,
        change_poster_processing,
        tournament_id,
        weekday_id,
    )


def change_poster_choose_place(message, tournament_id, weekday_id, address_dict):
    """
    Меняет место проведения в афише турнира
    """
    address = message.text
    address_id = address_dict.get(address)

    poster_data = TournamentSchedule.objects.filter(
        id=tournament_id,
    ).first()

    poster_data.location_id = address_id
    poster_data.save()

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    tournament_name = types.KeyboardButton(
        text='Название турнира'
    )

    tournament_date = types.KeyboardButton(
        text='Дата проведения'
    )

    tournament_time = types.KeyboardButton(
        text='Время проведения'
    )

    tournament_place = types.KeyboardButton(
        text='Место проведения'
    )

    tournament_description = types.KeyboardButton(
        text='Описание турнира'
    )

    end_changes = types.KeyboardButton(
        text='Завершить изменения'
    )

    markup.add(
        tournament_name,
        tournament_date,
        tournament_time,
        tournament_place,
        tournament_description,
        end_changes,
    )

    response = bot.send_message(
        message.chat.id,
        f"Изменения успешно сохранены",
        reply_markup=markup
    )

    bot.register_next_step_handler(
        response,
        change_poster_processing,
        tournament_id,
        weekday_id,
    )


def change_poster_time(message, tournament_id, weekday_id):
    """
    Меняет время проведения в афише турнира
    """
    time_input = message.text
    time_pattern = r'^\d{2}:\d{2}-\d{2}:\d{2}$'
    answer_text = ""

    if not re.match(time_pattern, time_input):
        answer_text += "Неверный формат времени. Нужно было ввести время в формате ЧЧ:ММ-ЧЧ:ММ"
    else:
        start_time_str, end_time_str = time_input.split('-')
        start_time = datetime.strptime(start_time_str, "%H:%M").time()
        end_time = datetime.strptime(end_time_str, "%H:%M").time()

        if end_time <= start_time:
            answer_text += "Неверный алгоритм ввода времени. Второе время должно быть позже первого времени"
        else:
            try:
                tournament_schedule = TournamentSchedule.objects.filter(
                    id=tournament_id
                ).first()

                tournament_schedule.start_time = start_time
                tournament_schedule.end_time = end_time
                tournament_schedule.save()

                answer_text += "Время проведения турнира успешно обновлено"

            except ObjectDoesNotExist:
                answer_text += "Турнир не найден"

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    tournament_name = types.KeyboardButton(
        text='Название турнира'
    )

    tournament_date = types.KeyboardButton(
        text='Дата проведения'
    )

    tournament_time = types.KeyboardButton(
        text='Время проведения'
    )

    tournament_place = types.KeyboardButton(
        text='Место проведения'
    )

    tournament_description = types.KeyboardButton(
        text='Описание турнира'
    )

    end_changes = types.KeyboardButton(
        text='Завершить изменения'
    )

    markup.add(
        tournament_name,
        tournament_date,
        tournament_time,
        tournament_place,
        tournament_description,
        end_changes,
    )

    response = bot.send_message(
        message.chat.id,
        answer_text,
        reply_markup=markup
    )

    bot.register_next_step_handler(
        response,
        change_poster_processing,
        tournament_id,
        weekday_id,
    )


def change_poster_date(message, tournament_id, weekday_id):
    """
    Меняет дату проведения в афише турнира
    """
    poster_date = message.text
    answer_text = ""

    try:
        date_obj = datetime.strptime(poster_date, "%d.%m.%Y").date()

        if date_obj.isoweekday() != weekday_id:
            answer_text += f"Дата {poster_date} не соответствует выбранному дню недели"

        else:
            tournament_schedule = TournamentSchedule.objects.filter(
                id=tournament_id
            ).first()

            tournament_schedule.date = date_obj
            tournament_schedule.save()

            answer_text += f"Дата проведения успешно обновлена"

    except ValueError:
        answer_text += "Неверный формат даты. Пожалуйста, введите дату в формате ДД.ММ.ГГГГ"

    except ObjectDoesNotExist:
        answer_text += "Турнир не найден"

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    tournament_name = types.KeyboardButton(
        text='Название турнира'
    )

    tournament_date = types.KeyboardButton(
        text='Дата проведения'
    )

    tournament_time = types.KeyboardButton(
        text='Время проведения'
    )

    tournament_place = types.KeyboardButton(
        text='Место проведения'
    )

    tournament_description = types.KeyboardButton(
        text='Описание турнира'
    )

    end_changes = types.KeyboardButton(
        text='Завершить изменения'
    )

    markup.add(
        tournament_name,
        tournament_date,
        tournament_time,
        tournament_place,
        tournament_description,
        end_changes,
    )

    response = bot.send_message(
        message.chat.id,
        answer_text,
        reply_markup=markup
    )

    bot.register_next_step_handler(
        response,
        change_poster_processing,
        tournament_id,
        weekday_id,
    )


def change_poster_name(message, tournament_id, weekday_id):
    """
    Меняет название турнира в его афише
    """
    poster_name = message.text

    poster_data = TournamentSchedule.objects.filter(
        id=tournament_id,
    ).first()

    poster_tournament_id = poster_data.tournament_id

    tournament_data = Tournament.objects.filter(
        id=poster_tournament_id,
    ).first()

    tournament_data.tournament_name = poster_name
    tournament_data.save()

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    tournament_name = types.KeyboardButton(
        text='Название турнира'
    )

    tournament_date = types.KeyboardButton(
        text='Дата проведения'
    )

    tournament_time = types.KeyboardButton(
        text='Время проведения'
    )

    tournament_place = types.KeyboardButton(
        text='Место проведения'
    )

    tournament_description = types.KeyboardButton(
        text='Описание турнира'
    )

    end_changes = types.KeyboardButton(
        text='Завершить изменения'
    )

    markup.add(
        tournament_name,
        tournament_date,
        tournament_time,
        tournament_place,
        tournament_description,
        end_changes,
    )

    response = bot.send_message(
        message.chat.id,
        f"Изменения успешно сохранены",
        reply_markup=markup
    )

    bot.register_next_step_handler(
        response,
        change_poster_processing,
        tournament_id,
        weekday_id,
    )


def get_image(message, tournament_dict):
    """
    Запрашивает баннер турнира
    """
    if message.text not in ['Назад к регистрации', 'Главное меню']:
        user_id = message.from_user.id
        tournament_id = tournament_dict.get(message.text)

        response = bot.send_message(
            chat_id=message.chat.id,
            text=f"Прикрепите фото для баннера"
        )

        bot.register_next_step_handler(
            response,
            handle_image,
            tournament_id
        )

    else:
        auth_data = Authorization.objects.filter(
            telegram_id=message.from_user.id
        )

        custom_user = CustomUser.objects.get(
            username_id=auth_data.first().id
        )

        if not custom_user.is_authorized:
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_register = types.KeyboardButton(
                text='Регистрация'
            )

            btn_login = types.KeyboardButton(
                text='Авторизация'
            )

            btn_password = types.KeyboardButton(
                text='Забыл пароль'
            )

            mon_btn = types.KeyboardButton(
                text='пн'
            )

            tue_btn = types.KeyboardButton(
                text='вт'
            )

            wed_btn = types.KeyboardButton(
                text='ср'
            )

            thu_btn = types.KeyboardButton(
                text='чт'
            )

            fri_btn = types.KeyboardButton(
                text='пт'
            )

            sat_btn = types.KeyboardButton(
                text='сб'
            )

            sun_btn = types.KeyboardButton(
                text='вс'
            )

            markup.add(
                mon_btn,
                tue_btn,
                wed_btn,
                thu_btn,
                fri_btn,
                sat_btn,
                sun_btn,
                btn_register,
                btn_login,
                btn_password
            )

            bot.send_message(
                chat_id=message.chat.id,
                text="Меню регистрации",
                reply_markup=markup
            )

        else:
            main_menu(message)


def handle_image(message, tournament_id):
    """
    Фиксирует новый/обновленный баннер турнира в БД
    """
    user_id = message.from_user.id

    if message.content_type == 'photo':
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        file_path = f'questions_images/tournament_image_{user_id}_{tournament_id}.jpg'

        with open('./media/' + file_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        tournament_schedule = TournamentSchedule.objects.filter(
            id=tournament_id
        ).first()

        if tournament_schedule:
            tournament_schedule.image = file_path
            tournament_schedule.save()

            bot.send_message(
                chat_id=message.chat.id,
                text=f"Баннер успешно обновлен для турнира {tournament_id}"
            )

        else:
            bot.send_message(
                chat_id=message.chat.id,
                text='Не удалось найти турнир.'
            )

    else:
        bot.send_message(
            chat_id=message.chat.id,
            text="Отправленное сообщение не является изображением."
        )

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    btn_register = types.KeyboardButton(
        text='Регистрация'
    )

    btn_login = types.KeyboardButton(
        text='Авторизация'
    )

    btn_password = types.KeyboardButton(
        text='Забыл пароль'
    )

    user_auth = Authorization.objects.filter(
        telegram_id=message.from_user.id
    )

    if user_auth.exists():
        user_id = user_auth.first().id
        custom_user = CustomUser.objects.filter(
            id=user_id
        ).first()

        mon_btn = types.KeyboardButton(
            text='пн'
        )

        tue_btn = types.KeyboardButton(
            text='вт'
        )

        wed_btn = types.KeyboardButton(
            text='ср'
        )

        thu_btn = types.KeyboardButton(
            text='чт'
        )

        fri_btn = types.KeyboardButton(
            text='пт'
        )

        sat_btn = types.KeyboardButton(
            text='сб'
        )

        sun_btn = types.KeyboardButton(
            text='вс'
        )

        if custom_user.role_id in [1, 2]:
            markup.add(
                mon_btn,
                tue_btn,
                wed_btn,
                thu_btn,
                fri_btn,
                sat_btn,
                sun_btn
            )

    auth_data = Authorization.objects.filter(
        telegram_id=message.from_user.id
    )

    custom_user = CustomUser.objects.get(
        username_id=auth_data.first().id
    )

    if not custom_user.is_authorized:
        markup.add(
            btn_register,
            btn_login,
            btn_password
        )

        bot.send_message(
            chat_id=message.chat.id,
            text="Меню регистрации",
            reply_markup=markup
        )

    else:
        main_menu(message)


@bot.message_handler(func=lambda message: "Регистрация" in message.text or message.text == "/register")
def register(message):
    """
    Проверяет зарегистрирован ли пользователь. Если нет, то начинает серию вопросов
    """
    chat_id = message.chat.id
    uid = message.from_user.id

    if Authorization.objects.filter(telegram_id=uid).exists():
        response = bot.reply_to(
            message=message,
            text="Вы уже зарегистрированы!"
        )

    else:
        response = bot.reply_to(
            message=message,
            text="Введите ваше ФИО (пример - Иванов Иван Иванович):"
        )
        bot.register_next_step_handler(
            response,
            process_full_name
        )


def process_full_name(message):
    """
    Получает информацию о ФИО пользователя, запрашивает дату рождения
    """
    full_name = message.text

    response = bot.reply_to(
        message=message,
        text="Введите вашу дату рождения в формате ДД.ММ.ГГГГ (пример - 07.07.2007):"
    )

    bot.register_next_step_handler(
        response,
        process_date_of_birth,
        full_name=full_name
    )


def process_date_of_birth(message, full_name):
    """
    Получает информацию о дате рождения, запрашивает номер телефона
    """
    date_of_birth = message.text
    date_pattern = re.compile(r'\d{2}.\d{2}.\d{4}')

    if date_pattern.fullmatch(date_of_birth):
        date_of_birth = '-'.join(date_of_birth.split('.')[::-1])

        response = bot.reply_to(
            message=message,
            text="Введите ваш номер телефона в формате 8xxxxxxxxxx (пример - 89053743009):"
        )
        bot.register_next_step_handler(
            response,
            process_phone_number,
            full_name=full_name,
            date_of_birth=date_of_birth
        )

    else:
        bot.reply_to(
            message=message,
            text="Введенная дата рождения некорректна"
        )


def process_phone_number(message, full_name, date_of_birth):
    """
    Получает информацию о номере телефона, запрашивает будущий пароль пользователя
    """
    phone_number = message.text
    phone_pattern = re.compile(r'^[8-9]\d{10}$')

    if phone_pattern.match(phone_number):
        response = bot.reply_to(
            message=message,
            text="Введите ваш пароль для авторизации:"
        )
        bot.register_next_step_handler(
            response,
            process_password_registration,
            full_name=full_name,
            date_of_birth=date_of_birth,
            phone_number=phone_number
        )

    else:
        bot.reply_to(
            message=message,
            text="Введенный номер телефона некорректен"
        )


def process_password_registration(message, full_name, date_of_birth, phone_number):
    """
    Получает информацию о пароле пользователя, создает запись о пользователе в таблице Authorization
    """
    password = message.text
    hashed_password = make_password(password)
    uid = message.from_user.id
    telegram_nickname = message.from_user.username

    if telegram_nickname:
        auth_nickname = Authorization.objects.filter(
                telegram_nickname=telegram_nickname
        ).exclude(
            pk=message.from_user.id
        )

        if auth_nickname.exists():
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_register = types.KeyboardButton(
                text='Регистрация'
            )

            btn_login = types.KeyboardButton(
                text='Авторизация'
            )

            btn_password = types.KeyboardButton(
                text='Забыл пароль'
            )

            mon_btn = types.KeyboardButton(
                text='пн'
            )

            tue_btn = types.KeyboardButton(
                text='вт'
            )

            wed_btn = types.KeyboardButton(
                text='ср'
            )

            thu_btn = types.KeyboardButton(
                text='чт'
            )

            fri_btn = types.KeyboardButton(
                text='пт'
            )

            sat_btn = types.KeyboardButton(
                text='сб'
            )

            sun_btn = types.KeyboardButton(
                text='вс'
            )

            markup.add(
                mon_btn,
                tue_btn,
                wed_btn,
                thu_btn,
                fri_btn,
                sat_btn,
                sun_btn,
                btn_register,
                btn_login,
                btn_password
            )

            bot.reply_to(
                message,
                "Пользователь с текущим никнеймом Telegram уже зарегистрирован.",
                reply_markup=markup,
            )

    authorization = Authorization.objects.filter(
        telegram_id=str(uid)
    )

    if not authorization.exists():
        auth_user = Authorization.objects.create(
            uid=message.from_user.id,
            registration_datetime=timezone.now(),
            full_name=full_name,
            date_of_birth=date_of_birth,
            phone_number=phone_number,
            telegram_nickname=telegram_nickname if telegram_nickname else None,
            telegram_id=message.from_user.id,
            role_id=3
        )

        standings_entry = Standings.objects.filter(
            participant_telegram=auth_user,
            full_name=auth_user.full_name
        )

        CustomUser.objects.filter(
            username_id=auth_user.id
        ).update(
            password=hashed_password
        )

        if not standings_entry.exists():
            Standings.objects.create(
                participant_telegram=auth_user,
                full_name=auth_user.full_name
            )

        bot.reply_to(
            message=message,
            text="Регистрация прошла успешно. Авторизируйтесь через команду /login"
        )

    else:
        bot.reply_to(
            message,
            "Пользователь уже существует"
        )


@bot.message_handler(func=lambda message: "Авторизация" in message.text or message.text == "/login")
def login(message):
    """
    Начинает процесс авторизации пользователя
    """
    uid = message.from_user.id
    auth_data = Authorization.objects.filter(
        telegram_id=str(uid)
    )

    if not auth_data.exists():
        bot.reply_to(
            message=message,
            text="Вы не зарегистрированы. Для регистрации введите /register"
        )

    else:
        auth_obj = auth_data.first()
        custom_user = CustomUser.objects.filter(
            username_id=auth_obj.id
        ).first()

        if custom_user.is_authorized:
            bot.reply_to(
                message,
                "Вы уже авторизованы."
            )
        else:
            process_login_data(
                message,
                custom_user
            )


def process_login_data(message, custom_user):
    """
    Просит пользователю ввести пароль для авторизации, если он не авторизован
    """
    response = bot.reply_to(
        message,
        "Введите ваш пароль:"
    )

    bot.register_next_step_handler(
        response,
        process_password,
        custom_user=custom_user
    )


def process_password(message, custom_user):
    """
    Осуществляет вход пользователя в приложение, если пароль верный
    """
    input_password = message.text
    actual_password = custom_user.password

    if check_password(input_password, actual_password):
        custom_user.last_login = timezone.now()
        custom_user.is_authorized = True
        custom_user.save()

        main_menu(message)

    else:
        bot.reply_to(
            message,
            "Неправильный пароль"
        )


@bot.message_handler(func=lambda message: "Забыл пароль" in message.text or message.text == "/password")
def change_password(message):
    """
    Меняет пароль в случае, если пользователь забыл его
    """
    uid = message.from_user.id
    auth_data = Authorization.objects.filter(
        telegram_id=str(uid)
    )

    if not auth_data.exists():
        bot.reply_to(
            message=message,
            text="Вы не зарегистрированы. Для регистрации введите /register"
        )

    else:
        custom_user = CustomUser.objects.get(
            username_id=auth_data.first().id
        )

        if custom_user:
            if custom_user.is_authorized == False:
                response = bot.reply_to(
                    message,
                    "Введите ваш новый пароль:"
                )

                bot.register_next_step_handler(
                    response,
                    callback=get_new_password,
                )

            else:
                bot.reply_to(
                    message,
                    "Вы авторизованы. Разавторизируйтесь для получения нового пароля: /logout"
                )


def get_new_password(message):
    """
    Позволяет получить новый пароль
    """
    new_password = message.text

    hashed_password = make_password(new_password)
    uid = message.from_user.id

    auth_user = Authorization.objects.filter(
        telegram_id=str(uid)
    )

    if auth_user.exists():
        CustomUser.objects.filter(
            username_id=auth_user.first().id
        ).update(
            password=hashed_password
        )

        bot.reply_to(
            message=message,
            text="Изменение пароля прошло успешно. Авторизируйтесь через команду /login"
        )


@bot.message_handler(func=lambda message: "Главное меню" in message.text or message.text == "/main_menu")
def main_menu(message):
    """
    Отображает главное меню пользователя
    """
    uid = message.from_user.id
    auth_data = Authorization.objects.filter(
        telegram_id=str(uid)
    )

    if not auth_data.exists():
        bot.reply_to(
            message=message,
            text="Вы не зарегистрированы. Для регистрации введите /register"
        )

    else:
        auth_obj = auth_data.first()
        custom_user = CustomUser.objects.filter(
            username_id=auth_obj.id
        ).first()

        if not custom_user.is_authorized:
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_register = types.KeyboardButton(
                text='Регистрация'
            )

            btn_login = types.KeyboardButton(
                text='Авторизация'
            )

            btn_password = types.KeyboardButton(
                text='Забыл пароль'
            )

            mon_btn = types.KeyboardButton(
                text='пн'
            )

            tue_btn = types.KeyboardButton(
                text='вт'
            )

            wed_btn = types.KeyboardButton(
                text='ср'
            )

            thu_btn = types.KeyboardButton(
                text='чт'
            )

            fri_btn = types.KeyboardButton(
                text='пт'
            )

            sat_btn = types.KeyboardButton(
                text='сб'
            )

            sun_btn = types.KeyboardButton(
                text='вс'
            )

            markup.add(
                mon_btn,
                tue_btn,
                wed_btn,
                thu_btn,
                fri_btn,
                sat_btn,
                sun_btn,
                btn_register,
                btn_login,
                btn_password
            )

            bot.reply_to(
                message,
                "Вы не авторизованы. Для авторизации введите /login",
                reply_markup=markup,
            )

        else:
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_logout = types.KeyboardButton(
                text='Выход'
            )

            btn_start_quiz = types.KeyboardButton(
                text='Начать викторину'
            )

            btn_tournam_schedule = types.KeyboardButton(
                text='Расписание'
            )

            btn_ranking = types.KeyboardButton(
                text='Рейтинг'
            )

            btn_add_points = types.KeyboardButton(
                text='Начисление'
            )

            # btn_start_tournam = types.KeyboardButton(
            #     text='Турнир'
            # )

            btn_get_remains = types.KeyboardButton(
                text='Остаток'
            )

            if custom_user.role_id in [1, 2]:
                markup.add(
                    btn_logout,
                    btn_tournam_schedule,
                    btn_add_points,
                    btn_ranking,
                )

            else:
                markup.add(
                    btn_logout,
                    btn_tournam_schedule,
                    btn_start_quiz,
                    btn_ranking,
                    btn_get_remains,
                )

            bot.reply_to(
                message,
                "Главное меню",
                reply_markup=markup,
            )


@bot.message_handler(func=lambda message: 'Начисление' == message.text or message.text == '/add_points')
def add_points_menu(message):
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    btn_add_points1 = types.KeyboardButton(
        text='Начисление (квиз)',
    )

    btn_add_points2 = types.KeyboardButton(
        text='Начисление (турнир)',
    )

    main_menu_btn = types.KeyboardButton(
        text='Главное меню',
    )

    markup.add(
        btn_add_points1,
        btn_add_points2,
        main_menu_btn
    )

    bot.send_message(
        message.chat.id,
        "Выберите способ начисления баллов",
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: 'Рейтинг' == message.text or message.text == '/get_rating')
def display_rating(message):
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    total_rating_btn = types.KeyboardButton(
        text='Общий рейтинг',
    )

    individual_rating_btn = types.KeyboardButton(
        text='Мой рейтинг',
    )

    main_menu_btn = types.KeyboardButton(
        text='Главное меню',
    )

    markup.add(
        total_rating_btn,
        individual_rating_btn,
        main_menu_btn,
    )

    bot.send_message(
        message.chat.id,
        "Выберите формат просмотра рейтинга",
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: 'Мой рейтинг' == message.text or message.text == '/get_my_rating')
def display_individual_rating(message):
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    btn_participant_rating2 = types.KeyboardButton(
        text='Личный рейтинг (баллы, турнир)'
    )

    btn_participant_rating1 = types.KeyboardButton(
        text='Личный рейтинг (баллы, квиз)'
    )

    main_menu_btn = types.KeyboardButton(
        text='Главное меню',
    )

    markup.add(
        btn_participant_rating2,
        btn_participant_rating1,
        main_menu_btn,
    )

    bot.send_message(
        message.chat.id,
        "Выберите формат просмотра личного рейтинга",
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: 'Общий рейтинг' in message.text or message.text == '/get_total_rating')
def display_total_rating(message):
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    btn_total_rating = types.KeyboardButton(
        text='Общая таблица по баллам'
    )

    btn_total_tournam_rating = types.KeyboardButton(
        text='Турнир'
    )

    btn_total_quiz_rating = types.KeyboardButton(
        text='Викторина'
    )

    main_menu_btn = types.KeyboardButton(
        text='Главное меню',
    )

    markup.add(
        btn_total_rating,
        btn_total_tournam_rating,
        btn_total_quiz_rating,
        main_menu_btn,
    )

    bot.send_message(
        message.chat.id,
        "Выберите формат просмотра общего рейтинга",
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: 'Общая таблица по баллам' == message.text or message.text == '/get_total_points_rating')
def display_total_rating(message):
    text_answer = ""
    standings = Standings.objects.all()

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    main_menu_btn = types.KeyboardButton(
        text='Главное меню',
    )

    markup.add(
        main_menu_btn,
    )

    if standings:

        data = []
        for standing in standings:
            data.append({
                "ФИО": standing.full_name,
                "Общий итог": standing.total_points,
                "Итоговое место": standing.final_place,
                "Итог по турниру": standing.tournament_points,
                "Итоговое место по турниру": standing.tournament_place,
                "Итог по викторине": standing.quiz_points,
                "Итоговое место по викторине": standing.quiz_place,
            })

        df = pd.DataFrame(data)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Standings', index=False)
        output.seek(0)

        filename = "tournament_standings.xlsx"

        bot.send_document(
            chat_id=message.chat.id,
            document=output,
            caption="Вывожу общую турнирную таблицу",
            reply_markup=markup,
            visible_file_name=filename,
        )

    else:
        bot.send_message(
            message.chat.id,
            "Данные по общей турнирной таблице остутствуют",
            reply_markup=markup
        )


@bot.message_handler(func=lambda message: 'Турнир' == message.text or message.text == '/get_total_tournament_rating')
def display_total_tournament_rating(message):
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    btn_tournament_rating2 = types.KeyboardButton(
        text='Рейтинг (баллы, турнир)'
    )

    btn_tour_statistics2 = types.KeyboardButton(
        text='Рейтинг (тур, турнир)'
    )

    btn_tours_statistics2 = types.KeyboardButton(
        text='Рейтинг (туры, турнир)'
    )

    main_menu_btn = types.KeyboardButton(
        text='Главное меню',
    )

    markup.add(
        btn_tournament_rating2,
        btn_tour_statistics2,
        btn_tours_statistics2,
        main_menu_btn,
    )

    bot.send_message(
        message.chat.id,
        "Выберите формат просмотра общего рейтинга в разрезе турниров",
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: 'Викторина' == message.text or message.text == '/get_total_quiz_rating')
def display_total_quiz_rating(message):
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    btn_tournament_rating1 = types.KeyboardButton(
        text='Рейтинг (баллы, квиз)'
    )

    btn_answers_rating = types.KeyboardButton(
        text='Рейтинг (ответы, квиз)'
    )

    btn_tour_statistics1 = types.KeyboardButton(
        text='Рейтинг (тур, квиз)'
    )

    btn_tours_statistics1 = types.KeyboardButton(
        text='Рейтинг (туры, квиз)'
    )

    main_menu_btn = types.KeyboardButton(
        text='Главное меню',
    )

    markup.add(
        btn_tournament_rating1,
        btn_answers_rating,
        btn_tour_statistics1,
        btn_tours_statistics1,
        main_menu_btn,
    )

    bot.send_message(
        message.chat.id,
        "Выберите формат просмотра общего рейтинга в разрезе викторин",
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: 'Расписание' in message.text or message.text == '/tournam_schedule')
def display_tournam_schedule(message):
    uid = message.from_user.id
    auth_data = Authorization.objects.filter(
        telegram_id=str(uid)
    )

    if auth_data.exists():
        username_id = auth_data.first().id

        custom_user = CustomUser.objects.get(
            username_id=username_id
        )

        if custom_user.is_authorized:
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            mon_btn = types.KeyboardButton(
                text='пн'
            )

            tue_btn = types.KeyboardButton(
                text='вт'
            )

            wed_btn = types.KeyboardButton(
                text='ср'
            )

            thu_btn = types.KeyboardButton(
                text='чт'
            )

            fri_btn = types.KeyboardButton(
                text='пт'
            )

            sat_btn = types.KeyboardButton(
                text='сб'
            )

            sun_btn = types.KeyboardButton(
                text='вс'
            )

            btn_main_menu = types.KeyboardButton(
                text='Главное меню'
            )

            markup.add(
                mon_btn,
                tue_btn,
                wed_btn,
                thu_btn,
                fri_btn,
                sat_btn,
                sun_btn,
                btn_main_menu
            )

            response = bot.reply_to(
                message,
                "Выберите день недели для просмотра расписания турниров",
                reply_markup=markup,
            )

            bot.register_next_step_handler(
                response,
                test_function_text,
            )

        else:
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_register = types.KeyboardButton(
                text='Регистрация'
            )

            btn_login = types.KeyboardButton(
                text='Авторизация'
            )

            btn_password = types.KeyboardButton(
                text='Забыл пароль'
            )

            mon_btn = types.KeyboardButton(
                text='пн'
            )

            tue_btn = types.KeyboardButton(
                text='вт'
            )

            wed_btn = types.KeyboardButton(
                text='ср'
            )

            thu_btn = types.KeyboardButton(
                text='чт'
            )

            fri_btn = types.KeyboardButton(
                text='пт'
            )

            sat_btn = types.KeyboardButton(
                text='сб'
            )

            sun_btn = types.KeyboardButton(
                text='вс'
            )

            markup.add(
                mon_btn,
                tue_btn,
                wed_btn,
                thu_btn,
                fri_btn,
                sat_btn,
                sun_btn,
                btn_register,
                btn_login,
                btn_password
            )

            bot.reply_to(
                message,
                "Вы не авторизованы. Для авторизации введите /login",
                reply_markup=markup,
            )

    else:
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        btn_register = types.KeyboardButton(
            text='Регистрация'
        )

        btn_login = types.KeyboardButton(
            text='Авторизация'
        )

        btn_password = types.KeyboardButton(
            text='Забыл пароль'
        )

        mon_btn = types.KeyboardButton(
            text='пн'
        )

        tue_btn = types.KeyboardButton(
            text='вт'
        )

        wed_btn = types.KeyboardButton(
            text='ср'
        )

        thu_btn = types.KeyboardButton(
            text='чт'
        )

        fri_btn = types.KeyboardButton(
            text='пт'
        )

        sat_btn = types.KeyboardButton(
            text='сб'
        )

        sun_btn = types.KeyboardButton(
            text='вс'
        )

        markup.add(
            mon_btn,
            tue_btn,
            wed_btn,
            thu_btn,
            fri_btn,
            sat_btn,
            sun_btn,
            btn_register,
            btn_login,
            btn_password
        )

        bot.reply_to(
            message,
            "Вы не зарегистрированы. Для регистрации введите /register",
            reply_markup=markup,
        )


@bot.message_handler(func=lambda message: 'Выход' in message.text or message.text == '/logout')
def logout(message):
    """
    Осуществляет выход пользователя из приложения, если он авторизован
    """
    uid = message.from_user.id
    auth_data = Authorization.objects.filter(
        telegram_id=str(uid)
    )

    if auth_data.exists():
        username_id = auth_data.first().id

        custom_user = CustomUser.objects.get(
            username_id=username_id
        )

        if custom_user.is_authorized:
            custom_user.is_authorized = False
            custom_user.save()

            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_register = types.KeyboardButton(
                text='Регистрация'
            )

            btn_login = types.KeyboardButton(
                text='Авторизация'
            )

            btn_password = types.KeyboardButton(
                text='Забыл пароль'
            )

            mon_btn = types.KeyboardButton(
                text='пн'
            )

            tue_btn = types.KeyboardButton(
                text='вт'
            )

            wed_btn = types.KeyboardButton(
                text='ср'
            )

            thu_btn = types.KeyboardButton(
                text='чт'
            )

            fri_btn = types.KeyboardButton(
                text='пт'
            )

            sat_btn = types.KeyboardButton(
                text='сб'
            )

            sun_btn = types.KeyboardButton(
                text='вс'
            )

            markup.add(
                mon_btn,
                tue_btn,
                wed_btn,
                thu_btn,
                fri_btn,
                sat_btn,
                sun_btn,
                btn_register,
                btn_login,
                btn_password
            )

            bot.reply_to(
                message,
                "Вы успешно вышли из аккаунта.",
                reply_markup=markup,
            )

        else:
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_register = types.KeyboardButton(
                text='Регистрация'
            )

            btn_login = types.KeyboardButton(
                text='Авторизация'
            )

            btn_password = types.KeyboardButton(
                text='Забыл пароль'
            )

            mon_btn = types.KeyboardButton(
                text='пн'
            )

            tue_btn = types.KeyboardButton(
                text='вт'
            )

            wed_btn = types.KeyboardButton(
                text='ср'
            )

            thu_btn = types.KeyboardButton(
                text='чт'
            )

            fri_btn = types.KeyboardButton(
                text='пт'
            )

            sat_btn = types.KeyboardButton(
                text='сб'
            )

            sun_btn = types.KeyboardButton(
                text='вс'
            )

            markup.add(
                mon_btn,
                tue_btn,
                wed_btn,
                thu_btn,
                fri_btn,
                sat_btn,
                sun_btn,
                btn_register,
                btn_login,
                btn_password
            )

            bot.reply_to(
                message,
                "Вы не авторизованы. Для авторизации введите /login",
                reply_markup=markup,
            )

    else:
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        btn_register = types.KeyboardButton(
            text='Регистрация'
        )

        btn_login = types.KeyboardButton(
            text='Авторизация'
        )

        btn_password = types.KeyboardButton(
            text='Забыл пароль'
        )

        mon_btn = types.KeyboardButton(
            text='пн'
        )

        tue_btn = types.KeyboardButton(
            text='вт'
        )

        wed_btn = types.KeyboardButton(
            text='ср'
        )

        thu_btn = types.KeyboardButton(
            text='чт'
        )

        fri_btn = types.KeyboardButton(
            text='пт'
        )

        sat_btn = types.KeyboardButton(
            text='сб'
        )

        sun_btn = types.KeyboardButton(
            text='вс'
        )

        markup.add(
            mon_btn,
            tue_btn,
            wed_btn,
            thu_btn,
            fri_btn,
            sat_btn,
            sun_btn,
            btn_register,
            btn_login,
            btn_password
        )

        bot.reply_to(
            message,
            "Вы не зарегистрированы. Для регистрации введите /register",
            reply_markup=markup,
        )


@bot.message_handler(func=lambda message: 'Начисление (квиз)' in message.text or message.text == '/add_quiz_points')
def add_points_check_quiz(message):
    """
    Проверяет, является ли пользователь директором. Если директор, то запрашивает тип начисления баллов участнику
    """
    is_AttributeError = False
    uid = message.from_user.id

    user_auth_data = Authorization.objects.filter(
        telegram_id=uid
    )

    try:
        username_id = user_auth_data.first().id
        custom_user = CustomUser.objects.get(
            username_id=username_id
        )

    except AttributeError:
        is_AttributeError = True

    if user_auth_data.exists() and not is_AttributeError:
        if custom_user.is_authorized:
            user_auth_data = user_auth_data.first()

            if user_auth_data.role_id in [1, 2]:
                markup = types.ReplyKeyboardMarkup(
                    resize_keyboard=True
                )

                btn_main_menu = types.KeyboardButton(
                    text='Главное меню'
                )

                btn_logout = types.KeyboardButton(
                    text='Выход'
                )

                markup.add(
                    btn_main_menu,
                    btn_logout
                )

                text = '\n'.join([
                    'Введдите тип начисления баллов в виде числа:',
                    '1 - порядковый номер занятого места',
                    '2 - РОТ (ПОТ) [указываем общую цифру, делим на /50 и зачисляем полученные баллы]',
                    '3 - произвольная цифра (бонусы)',
                    '4 - перевод баллов между участниками'
                ])

                response = bot.reply_to(
                    message,
                    text,
                    reply_markup=markup,
                )

                bot.register_next_step_handler(
                    response,
                    process_add_tour_quiz,
                    uid=uid
                )

            else:
                bot.reply_to(
                    message,
                    "Вы не являетесь директором. Вы не можете начислять баллы"
                )

        else:
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_register = types.KeyboardButton(
                text='Регистрация'
            )

            btn_login = types.KeyboardButton(
                text='Авторизация'
            )

            btn_password = types.KeyboardButton(
                text='Забыл пароль'
            )

            mon_btn = types.KeyboardButton(
                text='пн'
            )

            tue_btn = types.KeyboardButton(
                text='вт'
            )

            wed_btn = types.KeyboardButton(
                text='ср'
            )

            thu_btn = types.KeyboardButton(
                text='чт'
            )

            fri_btn = types.KeyboardButton(
                text='пт'
            )

            sat_btn = types.KeyboardButton(
                text='сб'
            )

            sun_btn = types.KeyboardButton(
                text='вс'
            )

            markup.add(
                mon_btn,
                tue_btn,
                wed_btn,
                thu_btn,
                fri_btn,
                sat_btn,
                sun_btn,
                btn_register,
                btn_login,
                btn_password
            )

            bot.reply_to(
                message,
                "Вы не авторизованы. Для авторизации введите /login",
                reply_markup=markup,
            )

    else:
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        btn_register = types.KeyboardButton(
            text='Регистрация'
        )

        btn_login = types.KeyboardButton(
            text='Авторизация'
        )

        btn_password = types.KeyboardButton(
            text='Забыл пароль'
        )

        mon_btn = types.KeyboardButton(
            text='пн'
        )

        tue_btn = types.KeyboardButton(
            text='вт'
        )

        wed_btn = types.KeyboardButton(
            text='ср'
        )

        thu_btn = types.KeyboardButton(
            text='чт'
        )

        fri_btn = types.KeyboardButton(
            text='пт'
        )

        sat_btn = types.KeyboardButton(
            text='сб'
        )

        sun_btn = types.KeyboardButton(
            text='вс'
        )

        markup.add(
            mon_btn,
            tue_btn,
            wed_btn,
            thu_btn,
            fri_btn,
            sat_btn,
            sun_btn,
            btn_register,
            btn_login,
            btn_password
        )

        bot.reply_to(
            message,
            "Вы не зарегистрированы. Для регистрации введите /register",
            reply_markup=markup,
        )


def process_add_tour_quiz(message, **kwargs):
    """"
    Запрашивает у директора номер тура
    """
    uid = kwargs.get('uid')
    points_type = message.text

    if points_type == "Главное меню":
        main_menu(message)

    elif points_type == "Выход":
        logout(message)

    else:
        reply = bot.reply_to(
            message,
            "Введите номер тура:"
        )

        bot.register_next_step_handler(
            reply,
            process_add_question_number_quiz,
            uid=uid,
            points_type=points_type
        )


def process_add_question_number_quiz(message, **kwargs):
    """"
    Запрашивает у директора номер вопроса в рамках выбранного тура
    """
    points_type = kwargs.get('points_type')
    uid = kwargs.get('uid')
    tour = message.text

    if tour == "Главное меню":
        main_menu(message)

    elif tour == "Выход":
        logout(message)

    else:
        if tour.isdigit():
            if int(tour) > 0:
                reply = bot.reply_to(
                    message,
                    "Введите номер вопроса:"
                )

                bot.register_next_step_handler(
                    reply,
                    process_add_points_type_quiz,
                    uid=uid,
                    tour=tour,
                    points_type=points_type
                )

            else:
                bot.reply_to(
                    message,
                    "Некорректный ввод номера тура (число должно быть больше нуля)"
                )

        else:
            bot.reply_to(
                message,
                "Некорректный ввод номера тура (должно быть число)"
            )


def process_add_points_type_quiz(message, **kwargs):
    """"
    Проверяет корректность введенного типа начисления баллов и в зависимости от него запрашивает у директора информацию
    """
    add_points_type = kwargs.get('points_type')
    uid = kwargs.get('uid')
    tour = kwargs.get('tour')
    question_number = message.text

    if question_number == "Главное меню":
        main_menu(message)

    elif question_number == "Выход":
        logout(message)

    else:
        if question_number.isdigit():
            if int(question_number) > 0:
                if add_points_type in ('1', '2', '3', '4'):
                    participants = Authorization.objects.all().filter(
                        role=3
                    )

                    participants_list = []
                    if participants:
                        for participant in participants:
                            part_id = participant.id
                            part_name = participant.full_name
                            part_nick = participant.telegram_nickname
                            part_tel_id = participant.telegram_id

                            participants_list.append({
                                'id': part_id,
                                'name': part_name,
                                'nick': part_nick,
                                'tel_id': part_tel_id,
                            })

                        total_participants = len(participants_list)

                        if len(participants_list) >= 1:
                            markup = types.ReplyKeyboardMarkup(
                                resize_keyboard=True
                            )

                            btn_register = types.KeyboardButton(
                                text='Главное меню'
                            )

                            btn_login = types.KeyboardButton(
                                text='Выход'
                            )

                            markup.add(
                                btn_register,
                                btn_login,
                            )

                            for idx, _dict in enumerate(participants_list):
                                markup.add(
                                    types.KeyboardButton(
                                        text=str(idx+1) + '. ' + _dict.get('name'),
                                    )
                                )

                            """
                            Реконструкция
                            """
                            if add_points_type == '1':
                                response = bot.reply_to(
                                    message,
                                    "Выберите ФИО участника",
                                    reply_markup=markup,
                                )

                                bot.register_next_step_handler(
                                    response,
                                    process_points_type_1_place_quiz,
                                    tour=tour,
                                    question_number=question_number,
                                    uid=uid,
                                    total_participants=total_participants,
                                    participants_list=participants_list,
                                )

                            elif add_points_type == '2':
                                response = bot.reply_to(
                                    message,
                                    "Выберите ФИО участника",
                                    reply_markup=markup,
                                )

                                bot.register_next_step_handler(
                                    response,
                                    process_points_type_2_digit_quiz,
                                    tour=tour,
                                    question_number=question_number,
                                    uid=uid,
                                    participants_list=participants_list,
                                )

                            elif add_points_type == '3':
                                response = bot.reply_to(
                                    message,
                                    "Выберите ФИО участника",
                                    reply_markup=markup,
                                )

                                bot.register_next_step_handler(
                                    response,
                                    process_points_type_3_bonuses_quiz,
                                    tour=tour,
                                    question_number=question_number,
                                    uid=uid,
                                    participants_list=participants_list,
                                )

                            elif add_points_type == '4':
                                if len(participants_list) >= 2:
                                    response = bot.reply_to(
                                        message,
                                        "Выберите ФИО участника, у которого забираем баллы",
                                        reply_markup=markup,
                                    )

                                    bot.register_next_step_handler(
                                        response,
                                        process_points_type_4_receiver_quiz,
                                        tour=tour,
                                        question_number=question_number,
                                        uid=uid,
                                        participants_list=participants_list,
                                    )

                                else:
                                    bot.reply_to(
                                        message,
                                        "Недостаточное количество участников для начисления баллов"
                                    )

                    else:
                        bot.reply_to(
                            message,
                            "У вас отсутствуют участники"
                        )

                else:
                    bot.reply_to(
                        message,
                        "Некорректный тип начисления баллов. Пожалуйста, выберите один из предложенных вариантов"
                    )

            else:
                bot.reply_to(
                    message,
                    "Некорректный ввод номера вопроса (число должно быть больше нуля)"
                )

        else:
            bot.reply_to(
                message,
                "Некорректный ввод номера вопроса (должно быть число)"
            )


def process_points_type_1_place_quiz(message, **kwargs):
    """
    Запрашивает у директора место в рейтинге, за которое он будем начислять баллы (1-й тип начисления баллов)
    """
    uid = kwargs.get('uid')
    tour = kwargs.get('tour')
    question_number = kwargs.get('question_number')
    total_participants = kwargs.get('total_participants')
    participants_list = kwargs.get('participants_list')

    if message.text == "Главное меню":
        main_menu(message)

    elif message.text == "Выход":
        logout(message)

    else:
        number = re.search(r'\d+', message.text)
        extracted_number = number.group()
        participant_id = participants_list[int(extracted_number) - 1].get('tel_id')

        if participant_id.isdigit():
            if int(participant_id) > 0:
                participant = Authorization.objects.get(
                    telegram_id=participant_id
                )

                if participant:
                    text1 = 'Введите номер места в рейтинге для следующего участника:'
                    text2 = 'На текущий момент можно ввести место в диапазоне от 1 до'
                    part_name = participant.full_name

                    response = bot.reply_to(
                        message,
                        f"{text1} {part_name}. {text2} {total_participants}"
                    )

                    bot.register_next_step_handler(
                        response,
                        process_points_type_1_place_points_quiz,
                        uid=uid,
                        tour=tour,
                        question_number=question_number,
                        participant=participant,
                        total_participants=total_participants
                    )

                else:
                    bot.reply_to(
                        message,
                        "Участника не существует в БД"
                    )

            else:
                bot.reply_to(
                    message,
                    "ID должен быть больше нуля"
                )

        else:
            bot.reply_to(
                message,
                "ID должно быть числом"
            )


def process_points_type_1_place_points_quiz(message, **kwargs):
    """
    Добавляет баллы участнику и заносит их в таблицу PointsTransaction (1-й тип начисления баллов)
    """

    def create_points_dict():
        """
        Создает словарь с баллами в соответствии с критериями модели PlacePoints
        """
        place_points = PlacePoints.objects.all()

        if not place_points.exists():
            ready_points_dict = {
                1: 500,
                2: 400,
                3: 350,
                4: 300,
                5: 250,
                6: 225,
                7: 200,
                8: 175,
                9: 150,
                10: 100,
                11: 90,
                12: 80,
                13: 70,
                14: 60,
                15: 50,
                16: 45,
                17: 40,
                18: 35,
                19: 30,
                20: 25,
                21: 20,
                22: 19,
                23: 18,
                24: 17,
                25: 16,
                26: 15,
                27: 14,
                28: 13,
                29: 12,
                30: 11,
                31: 10,
                32: 9,
                33: 8,
                34: 7,
                35: 6,
                36: 5,
                37: 4,
                38: 3,
                39: 2,
                40: 1,
            }

            for my_place, my_points in ready_points_dict.items():
                PlacePoints.objects.get_or_create(
                    place=my_place,
                    points=my_points,
                )

        my_points_dict = {}
        for my_place in range(1, total_participants + 1):
            my_points_dict[my_place] = PlacePoints.objects.filter(
                place=my_place
            ).first().points

        return my_points_dict

    def calculate_points(points_dict, place):
        """
        Выводит очки за конкретно занятое место.
        В случае отсутствия места вводим единицу
        """
        return points_dict.get(place, 1)

    uid = kwargs.get('uid')
    tour = kwargs.get('tour')
    question_number = kwargs.get('question_number')
    participant = kwargs.get('participant')
    total_participants = kwargs.get('total_participants')
    place = message.text

    if place == "Главное меню":
        main_menu(message)

    elif place == "Выход":
        logout(message)

    else:
        if place.isdigit():
            if int(place) > 0:
                if int(place) <= total_participants:
                    points_dict = create_points_dict()

                    points = calculate_points(
                        points_dict,
                        int(place)
                    )

                    transferor = Authorization.objects.get(
                        telegram_id=uid
                    )

                    question = Question.objects.get(
                        tour_id=int(tour),
                        tour_question_number_id=int(question_number)
                    )

                    if question:
                        participant_row = PointsTransaction.objects.filter(
                            sender_telegram_id=participant.telegram_id,
                            transferor_telegram_id=transferor.telegram_id,
                            question_id=question.id,
                        )

                        if not participant_row.exists():
                            PointsTransaction.objects.create(
                                sender_telegram_id=participant.telegram_id,
                                transferor_telegram_id=transferor.telegram_id,
                                question_id=question.id,
                                tournament_points=points,
                            )

                            update_quiz_points(
                                telegram_id=participant.telegram_id,
                            )

                        else:
                            participant_row.update(
                                tournament_points=points,
                                points_received_or_transferred=0,
                                bonuses=0,
                                points_transferred=0,
                                receiver_telegram_id=None,
                                transfer_datetime=None,
                                points_datetime=timezone.now(),
                            )

                            update_quiz_points(
                                telegram_id=participant.telegram_id,
                            )

                        bot.reply_to(
                            message,
                            f"Участник {participant.full_name} получил {points} баллов за {place} место в рейтине"
                        )

                    else:
                        bot.reply_to(
                            message,
                            "Пара 'тур-вопрос' не существует в БД"
                        )

                else:
                    bot.reply_to(
                        message,
                        f"Место в рейтинге должно быть в диапазоне от 1 до {total_participants}"
                    )

            else:
                bot.reply_to(
                    message,
                    "Некорректный ввод места в рейтинге (число должно быть больше нуля)"
                )

        else:
            bot.reply_to(
                message,
                "Некорректный ввод места в рейтинге (число должно быть числом)"
            )


def process_points_type_2_digit_quiz(message, **kwargs):
    """
    Запрашивает общую цифру для начисления баллов (2-й тип начисления баллов)
    """
    uid = kwargs.get('uid')
    tour = kwargs.get('tour')
    question_number = kwargs.get('question_number')
    participants_list = kwargs.get('participants_list')

    if message.text == "Главное меню":
        main_menu(message)

    elif message.text == "Выход":
        logout(message)

    else:
        number = re.search(r'\d+', message.text)
        extracted_number = number.group()
        participant_id = participants_list[int(extracted_number) - 1].get('tel_id')

        if participant_id.isdigit():
            if int(participant_id) > 0:
                participant = Authorization.objects.get(
                    telegram_id=participant_id
                )

                if participant:
                    response = bot.reply_to(
                        message,
                        "Введите общую цифру для начисления баллов:"
                    )

                    bot.register_next_step_handler(
                        response,
                        process_points_type_2_pot_quiz,
                        uid=uid,
                        tour=tour,
                        question_number=question_number,
                        participant=participant,
                    )

                else:
                    bot.reply_to(
                        message,
                        "Участника не существует в БД"
                    )

            else:
                bot.reply_to(
                    message,
                    "ID должен быть больше нуля"
                )

        else:
            bot.reply_to(
                message,
                "ID должно быть числом"
            )


def process_points_type_2_pot_quiz(message, **kwargs):
    """
    Делим цифру на 50 и начисляем баллы. Фиксируем баллы в таблице PointsTransaction (2-й тип начисления баллов)
    """
    uid = kwargs.get('uid')
    tour = kwargs.get('tour')
    question_number = kwargs.get('question_number')
    participant = kwargs.get('participant')
    digit = message.text

    if digit == "Главное меню":
        main_menu(message)

    elif digit == "Выход":
        logout(message)

    else:
        if digit.isdigit():
            if int(digit) > 0:
                points = int(digit) / 50
                transferor = Authorization.objects.get(
                    telegram_id=uid
                )

                question = Question.objects.get(
                    tour_id=int(tour),
                    tour_question_number_id=int(question_number)
                )

                if question:
                    participant_row = PointsTransaction.objects.filter(
                        sender_telegram_id=participant.telegram_id,
                        transferor_telegram_id=transferor.telegram_id,
                        question_id=question.id,
                    )

                    if not participant_row.exists():
                        PointsTransaction.objects.create(
                            sender_telegram_id=participant.telegram_id,
                            transferor_telegram_id=transferor.telegram_id,
                            question_id=question.id,
                            points_received_or_transferred=points,
                        )

                        update_quiz_points(
                            telegram_id=participant.telegram_id,
                        )

                    else:
                        participant_row.update(
                            tournament_points=0,
                            points_received_or_transferred=points,
                            bonuses=0,
                            points_transferred=0,
                            receiver_telegram_id=None,
                            transfer_datetime=None,
                            points_datetime=timezone.now(),
                        )

                        update_quiz_points(
                            telegram_id=participant.telegram_id,
                        )

                    bot.reply_to(
                        message,
                        f"Участник {participant.full_name} получил {int(points)} баллов"
                    )

            else:
                bot.reply_to(
                    message,
                    "Некорректный ввод общей цифры (число должно быть больше нуля)"
                )

        else:
            bot.reply_to(
                message,
                "Некорректный ввод общей цифры (нужно именно число)"
            )


def process_points_type_3_bonuses_quiz(message, **kwargs):
    """
    Запрашивает размер бонуса для начисления баллов (3-й тип начисления баллов)
    """
    uid = kwargs.get('uid')
    tour = kwargs.get('tour')
    question_number = kwargs.get('question_number')
    participants_list = kwargs.get('participants_list')

    if message.text == "Главное меню":
        main_menu(message)

    elif message.text == "Выход":
        logout(message)

    else:
        number = re.search(r'\d+', message.text)
        extracted_number = number.group()
        participant_id = participants_list[int(extracted_number) - 1].get('tel_id')

        if participant_id.isdigit():
            if int(participant_id) > 0:
                participant = Authorization.objects.get(
                    telegram_id=participant_id
                )

                if participant:
                    response = bot.reply_to(
                        message,
                        f"Введите размер бонуса (если хотите автоматом задать рандомное число введите 'random'):"
                    )

                    bot.register_next_step_handler(
                        response,
                        process_points_type_3_random_quiz,
                        uid=uid,
                        tour=tour,
                        question_number=question_number,
                        participant=participant
                    )

                else:
                    bot.reply_to(
                        message,
                        "Участника не существует в БД"
                    )

            else:
                bot.reply_to(
                    message,
                    "ID должен быть больше нуля"
                )

        else:
            bot.reply_to(
                message,
                "ID должно быть числом"
            )


def process_points_type_3_random_quiz(message, **kwargs):
    """
    Запрашивает диапазон для рандомного бонуса, если пользователь ввел 'random' (3-й тип начисления баллов)
    """
    uid = kwargs.get('uid')
    tour = kwargs.get('tour')
    question_number = kwargs.get('question_number')
    participant = kwargs.get('participant')
    bonuses = message.text

    if bonuses == "Главное меню":
        main_menu(message)

    elif bonuses == "Выход":
        logout(message)

    else:
        if bonuses.isdigit():
            if int(bonuses) > 0:
                bonuses = int(bonuses)

                process_points_type_3_result_quiz(
                    message,
                    uid=uid,
                    tour=tour,
                    question_number=question_number,
                    participant=participant,
                    bonuses=bonuses
                )

            else:
                bot.reply_to(
                    message,
                    "Размер бонуса должен быть больше нуля"
                )

        else:
            if bonuses == 'random':
                response = bot.reply_to(
                    message,
                    'Введите минимальный и максимальный возможный размер бонуса через запятую (пример - 1, 100):'
                )

                bot.register_next_step_handler(
                    response,
                    process_points_type_3_result_quiz,
                    uid=uid,
                    tour=tour,
                    question_number=question_number,
                    participant=participant,
                    bonuses=None
                )

            else:
                bot.reply_to(
                    message,
                    "Некорректный ввод размера бонуса"
                )


def process_points_type_3_result_quiz(message, **kwargs):
    """
    Заносит бонусы в таблицу PointsTransaction (3-й тип начисления баллов)
    """
    uid = kwargs.get('uid')
    tour = kwargs.get('tour')
    question_number = kwargs.get('question_number')
    participant = kwargs.get('participant')
    bonuses = kwargs.get('bonuses')

    if bonuses is None:
        random_bonuses = message.text

        if random_bonuses == "Главное меню":
            main_menu(message)

        elif random_bonuses == "Выход":
            logout(message)

        else:
            random_bonuses = random_bonuses.replace(' ', '').split(',')
            a = random_bonuses[0]
            b = random_bonuses[1]

            if a.isdigit() and b.isdigit():
                a = int(a)
                b = int(b)

                if a > 0 and b > 0:
                    if b > a:
                        bonuses = random.randint(a=a, b=b)

                    else:
                        bot.reply_to(
                            message,
                            "Диапазон бонуса должен быть указан от меньшего к большему в формате 'a, b'"
                        )

                else:
                    bot.reply_to(
                        message,
                        "Принимаются только положительные числа"
                    )

            else:
                bot.reply_to(
                    message,
                    "Некорректный ввод диапазона бонуса"
                )

    if bonuses:
        transferor = Authorization.objects.get(
            telegram_id=uid
        )

        question = Question.objects.get(
            tour_id=int(tour),
            tour_question_number_id=int(question_number)
        )

        if question and transferor:
            participant_row = PointsTransaction.objects.filter(
                sender_telegram_id=participant.telegram_id,
                transferor_telegram_id=transferor.telegram_id,
                question_id=question.id
            )

            if not participant_row.exists():
                PointsTransaction.objects.create(
                    sender_telegram_id=participant.telegram_id,
                    transferor_telegram_id=transferor.telegram_id,
                    question_id=question.id,
                    bonuses=bonuses
                )

                update_quiz_points(
                    telegram_id=participant.telegram_id,
                )

            else:
                participant_row.update(
                    tournament_points=0,
                    points_received_or_transferred=0,
                    bonuses=bonuses,
                    points_transferred=0,
                    points_datetime=timezone.now(),
                    transfer_datetime=None,
                    receiver_telegram_id=None,
                )

                update_quiz_points(
                    telegram_id=participant.telegram_id,
                )

            bot.reply_to(
                message,
                f"Баллы начислены участнику {participant.full_name} в размере {bonuses} баллов/балла"
            )


def process_points_type_4_receiver_quiz(message, **kwargs):
    """
    Запрашивает ID участника, которому начисляем баллы (4-й тип начисления баллов)
    """
    uid = kwargs.get('uid')
    tour = kwargs.get('tour')
    question_number = kwargs.get('question_number')
    participants_list = kwargs.get('participants_list')

    if message.text == "Главное меню":
        main_menu(message)

    elif message.text == "Выход":
        logout(message)

    else:
        number = re.search(r'\d+', message.text)
        extracted_number = number.group()
        sender_id = participants_list.pop(int(extracted_number) - 1)
        sender_id = sender_id.get('tel_id')

        if sender_id.isdigit():
            if int(sender_id) > 0:
                sender = Authorization.objects.get(
                    telegram_id=sender_id
                )

                if sender:
                    markup = types.ReplyKeyboardMarkup(
                        resize_keyboard=True
                    )

                    btn_register = types.KeyboardButton(
                        text='Главное меню'
                    )

                    btn_login = types.KeyboardButton(
                        text='Выход'
                    )

                    markup.add(
                        btn_register,
                        btn_login,
                    )

                    for idx, _dict in enumerate(participants_list):
                        markup.add(
                            types.KeyboardButton(
                                text=str(idx + 1) + '. ' + _dict.get('name'),
                            )
                        )

                    response_receiver = bot.reply_to(
                        message,
                        "Выберите ФИО укстника, которому начисляем баллы",
                        reply_markup=markup,
                    )

                    bot.register_next_step_handler(
                        response_receiver,
                        process_points_type_4_amount_quiz,
                        tour=tour,
                        question_number=question_number,
                        uid=uid,
                        sender=sender,
                        participants_list=participants_list,
                    )

                else:
                    bot.reply_to(
                        message,
                        "Участника не существует в БД"
                    )

            else:
                bot.reply_to(
                    message,
                    "ID должен быть больше нуля"
                )

        else:
            bot.reply_to(
                message,
                "ID должно быть числом"
            )


def process_points_type_4_amount_quiz(message, **kwargs):
    """
    Запрашивает количество начисляемых баллов (4-й тип начисления баллов)
    """
    uid = kwargs.get('uid')
    tour = kwargs.get('tour')
    question_number = kwargs.get('question_number')
    sender = kwargs.get('sender')
    participants_list = kwargs.get('participants_list')

    if message.text == "Главное меню":
        main_menu(message)

    elif message.text == "Выход":
        logout(message)

    else:
        number = re.search(r'\d+', message.text)
        extracted_number = number.group()
        receiver_id = participants_list[int(extracted_number) - 1].get('tel_id')

        receiver = Authorization.objects.get(
            telegram_id=receiver_id
        )

        if int(receiver.telegram_id) != int(sender.telegram_id):
            if receiver:
                if receiver.role_id == 3:
                    response = bot.reply_to(
                        message,
                        f"Введите количество начисляемых баллов:"
                    )

                    bot.register_next_step_handler(
                        response,
                        process_points_type_4_result_quiz,
                        tour=tour,
                        question_number=question_number,
                        uid=uid,
                        sender=sender,
                        receiver=receiver,
                    )

                else:
                    bot.reply_to(
                        message,
                        "Я принимаю только участников"
                    )

            else:
                bot.reply_to(
                    message,
                    "Некорректный ID участника"
                )

        else:
            bot.reply_to(
                message,
                "Нельзя переводить баллы самому себе"
            )


def process_points_type_4_result_quiz(message, **kwargs):
    """
    Фиксирует факт перевода баллов в таблицу PointsTransaction (4-й тип начисления баллов)
    """
    uid = kwargs.get('uid')
    tour = kwargs.get('tour')
    question_number = kwargs.get('question_number')
    sender = kwargs.get('sender')
    receiver = kwargs.get('receiver')
    amount = message.text

    if amount == "Главное меню":
        main_menu(message)

    elif amount == "Выход":
        logout(message)

    else:
        if amount.isdigit():
            amount = int(amount)
            if amount > 0:
                transferor = Authorization.objects.get(
                    telegram_id=uid
                )

                question = Question.objects.get(
                    tour_id=int(tour),
                    tour_question_number_id=int(question_number)
                )

                if question:
                    transaction_row11 = PointsTransaction.objects.filter(
                        sender_telegram_id=sender.telegram_id,
                        transferor_telegram_id=transferor.telegram_id,
                        question_id=question.id,
                    )

                    transaction_row12 = PointsTransaction.objects.filter(
                        sender_telegram_id=sender.telegram_id,
                        receiver_telegram_id=receiver.telegram_id,
                        transferor_telegram_id=transferor.telegram_id,
                        question_id=question.id,
                    )

                    if not transaction_row11.exists():
                        PointsTransaction.objects.create(
                            transfer_datetime=timezone.now(),
                            sender_telegram_id=sender.telegram_id,
                            receiver_telegram_id=receiver.telegram_id,
                            points_transferred=amount,
                            transferor_telegram_id=transferor.telegram_id,
                            question_id=question.id,
                        )

                        update_quiz_points(
                            telegram_id=sender.telegram_id,
                        )

                        update_quiz_points(
                            telegram_id=receiver.telegram_id,
                        )

                    else:
                        if not transaction_row12.exists():
                            transaction_row11.update(
                                receiver_telegram_id=receiver.telegram_id,
                            )

                        transaction_row12.update(
                            tournament_points=0,
                            points_received_or_transferred=0,
                            bonuses=0,
                            points_transferred=amount,
                            transfer_datetime=timezone.now(),
                            points_datetime=timezone.now(),
                        )

                        update_quiz_points(
                            telegram_id=sender.telegram_id,
                        )

                        update_quiz_points(
                            telegram_id=receiver.telegram_id,
                        )

                    bot.reply_to(
                        message,
                        f"Баллы начислены участнику {receiver.full_name} в размере {amount} баллов/балла"
                    )

            else:
                bot.reply_to(
                    message,
                    "Количество начисляемых баллов должно быть больше 0"
                )

        else:
            bot.reply_to(
                message,
                "Количество начисляемых баллов должно быть числом"
            )


@bot.message_handler(func=lambda message: 'Начисление (турнир)' in message.text or message.text == '/add_tournam_points')
def add_points_check(message):
    """
    Проверяет, является ли пользователь директором. Если директор, то запрашивает тип начисления баллов участнику
    """
    is_AttributeError = False
    uid = message.from_user.id

    user_auth_data = Authorization.objects.filter(
        telegram_id=uid
    )

    try:
        username_id = user_auth_data.first().id
        custom_user = CustomUser.objects.get(
            username_id=username_id
        )

    except AttributeError as e:
        is_AttributeError = True

    if user_auth_data.exists() and not is_AttributeError:
        if custom_user.is_authorized:
            user_auth_data = user_auth_data.first()

            if user_auth_data.role_id in [1, 2]:
                markup = types.ReplyKeyboardMarkup(
                    resize_keyboard=True
                )

                btn_main_menu = types.KeyboardButton(
                    text='Главное меню'
                )

                btn_logout = types.KeyboardButton(
                    text='Выход'
                )

                markup.add(
                    btn_main_menu,
                    btn_logout
                )

                text = '\n'.join([
                    'Введдите тип начисления баллов в виде числа:',
                    '1 - начисление баллов на основе занятого места',
                    '2 - РОТ (ПОТ) [указываем общую цифру, делим на /50 и зачисляем полученные баллы]',
                    '3 - произвольная цифра (бонусы)',
                    '4 - перевод баллов между участниками'
                ])

                response = bot.reply_to(
                    message,
                    text,
                    reply_markup=markup,
                )

                bot.register_next_step_handler(
                    response,
                    process_add_tournament,
                    uid=uid
                )

            else:
                bot.reply_to(
                    message,
                    "Вы не являетесь директором. Вы не можете начислять баллы"
                )

        else:
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_register = types.KeyboardButton(
                text='Регистрация'
            )

            btn_login = types.KeyboardButton(
                text='Авторизация'
            )

            btn_password = types.KeyboardButton(
                text='Забыл пароль'
            )

            mon_btn = types.KeyboardButton(
                text='пн'
            )

            tue_btn = types.KeyboardButton(
                text='вт'
            )

            wed_btn = types.KeyboardButton(
                text='ср'
            )

            thu_btn = types.KeyboardButton(
                text='чт'
            )

            fri_btn = types.KeyboardButton(
                text='пт'
            )

            sat_btn = types.KeyboardButton(
                text='сб'
            )

            sun_btn = types.KeyboardButton(
                text='вс'
            )

            markup.add(
                mon_btn,
                tue_btn,
                wed_btn,
                thu_btn,
                fri_btn,
                sat_btn,
                sun_btn,
                btn_register,
                btn_login,
                btn_password
            )

            bot.reply_to(
                message,
                "Вы не авторизованы. Для авторизации введите /login",
                reply_markup=markup,
            )

    else:
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        btn_register = types.KeyboardButton(
            text='Регистрация'
        )

        btn_login = types.KeyboardButton(
            text='Авторизация'
        )

        btn_password = types.KeyboardButton(
            text='Забыл пароль'
        )

        mon_btn = types.KeyboardButton(
            text='пн'
        )

        tue_btn = types.KeyboardButton(
            text='вт'
        )

        wed_btn = types.KeyboardButton(
            text='ср'
        )

        thu_btn = types.KeyboardButton(
            text='чт'
        )

        fri_btn = types.KeyboardButton(
            text='пт'
        )

        sat_btn = types.KeyboardButton(
            text='сб'
        )

        sun_btn = types.KeyboardButton(
            text='вс'
        )

        markup.add(
            mon_btn,
            tue_btn,
            wed_btn,
            thu_btn,
            fri_btn,
            sat_btn,
            sun_btn,
            btn_register,
            btn_login,
            btn_password
        )

        bot.reply_to(
            message,
            "Вы не зарегистрированы. Для регистрации введите /register",
            reply_markup=markup,
        )


def process_add_tournament(message, **kwargs):
    """"
    Запрашивает у директора номер тура
    """
    uid = kwargs.get('uid')
    points_type = message.text

    if points_type == "Главное меню":
        main_menu(message)

    elif points_type == "Выход":
        logout(message)

    else:
        reply = bot.reply_to(
            message,
            "Введите номер турнира:"
        )

        bot.register_next_step_handler(
            reply,
            process_add_points_type,
            uid=uid,
            points_type=points_type
        )


def process_add_points_type(message, **kwargs):
    """"
    Проверяет корректность введенного типа начисления баллов и в зависимости от него запрашивает у директора информацию
    """
    add_points_type = kwargs.get('points_type')
    uid = kwargs.get('uid')
    tournament_number = message.text

    if tournament_number == "Главное меню":
        main_menu(message)

    elif tournament_number == "Выход":
        logout(message)

    else:
        if tournament_number.isdigit():
            if int(tournament_number) > 0:
                if add_points_type in ('1', '2', '3', '4'):
                    participants = Authorization.objects.all().filter(
                        role=3
                    )

                    participants_list = []
                    if participants:
                        for participant in participants:
                            part_id = participant.id
                            part_name = participant.full_name
                            part_nick = participant.telegram_nickname
                            part_tel_id = participant.telegram_id

                            participants_list.append({
                                'id': part_id,
                                'name': part_name,
                                'nick': part_nick,
                                'tel_id': part_tel_id,
                            })

                        total_participants = len(participants_list)

                        if len(participants_list) >= 1:
                            markup = types.ReplyKeyboardMarkup(
                                resize_keyboard=True
                            )

                            btn_register = types.KeyboardButton(
                                text='Главное меню'
                            )

                            btn_login = types.KeyboardButton(
                                text='Выход'
                            )

                            markup.add(
                                btn_register,
                                btn_login,
                            )

                            for idx, _dict in enumerate(participants_list):
                                markup.add(
                                    types.KeyboardButton(
                                        text=str(idx + 1) + '. ' + _dict.get('name'),
                                    )
                                )

                            if add_points_type == '1':
                                response = bot.reply_to(
                                    message,
                                    "Выберите ФИО участника",
                                    reply_markup=markup,
                                )

                                bot.register_next_step_handler(
                                    response,
                                    process_points_type_1_place,
                                    tournament_number=tournament_number,
                                    uid=uid,
                                    total_participants=total_participants,
                                    participants_list=participants_list,
                                )

                            elif add_points_type == '2':
                                response = bot.reply_to(
                                    message,
                                    "Выберите ФИО участника",
                                    reply_markup=markup,
                                )

                                bot.register_next_step_handler(
                                    response,
                                    process_points_type_2_digit,
                                    tournament_number=tournament_number,
                                    uid=uid,
                                    participants_list=participants_list,
                                )

                            elif add_points_type == '3':
                                response = bot.reply_to(
                                    message,
                                    "Выберите ФИО участника",
                                    reply_markup=markup,
                                )

                                bot.register_next_step_handler(
                                    response,
                                    process_points_type_3_bonuses,
                                    tournament_number=tournament_number,
                                    uid=uid,
                                    participants_list=participants_list,
                                )

                            elif add_points_type == '4':
                                if len(participants_list) >= 2:
                                    response = bot.reply_to(
                                        message,
                                        "Выберите ФИО участника, у которого забираем баллы",
                                        reply_markup=markup,
                                    )

                                    bot.register_next_step_handler(
                                        response,
                                        process_points_type_4_receiver,
                                        tournament_number=tournament_number,
                                        uid=uid,
                                        participants_list=participants_list,
                                    )

                                else:
                                    bot.reply_to(
                                        message,
                                        "Недостаточное количество участников для начисления баллов"
                                    )

                    else:
                        bot.reply_to(
                            message,
                            "У вас отсутствуют участники"
                        )

                else:
                    bot.reply_to(
                        message,
                        "Некорректный тип начисления баллов. Пожалуйста, выберите один из предложенных вариантов"
                    )

            else:
                bot.reply_to(
                    message,
                    "Некорректный ввод номера вопроса (число должно быть больше нуля)"
                )

        else:
            bot.reply_to(
                message,
                "Некорректный ввод номера вопроса (должно быть число)"
            )


def process_points_type_1_place(message, **kwargs):
    """
    Запрашивает у директора место в рейтинге, за которое он будем начислять баллы (1-й тип начисления баллов)
    """
    uid = kwargs.get('uid')
    tournament_number = kwargs.get('tournament_number')
    total_participants = kwargs.get('total_participants')
    participants_list = kwargs.get('participants_list')

    if message.text == "Главное меню":
        main_menu(message)

    elif message.text == "Выход":
        logout(message)

    else:
        number = re.search(r'\d+', message.text)
        extracted_number = number.group()
        participant_id = participants_list[int(extracted_number) - 1].get('tel_id')

        if participant_id.isdigit():
            if int(participant_id) > 0:
                participant = Authorization.objects.get(
                    telegram_id=participant_id,
                )

                if participant:
                    text1 = 'Введите номер места в рейтинге для следующего участника:'
                    text2 = 'На текущий момент можно ввести место в диапазоне от 1 до'
                    part_name = participant.full_name
                    part_nick = participant.telegram_nickname
                    part_tel_id = participant.telegram_id

                    response = bot.reply_to(
                        message,
                        f"{text1} {part_name}. {text2} {total_participants}"
                    )

                    bot.register_next_step_handler(
                        response,
                        process_points_type_1_place_points,
                        uid=uid,
                        tournament_number=tournament_number,
                        participant=participant,
                        total_participants=total_participants
                    )

                else:
                    bot.reply_to(
                        message,
                        "Участника не существует в БД"
                    )

            else:
                bot.reply_to(
                    message,
                    "ID должен быть больше нуля"
                )

        else:
            bot.reply_to(
                message,
                "ID должно быть числом"
            )


def process_points_type_1_place_points(message, **kwargs):
    """
    Добавляет баллы участнику и заносит их в таблицу PointsTournament (1-й тип начисления баллов)
    """
    def create_points_dict():
        """
        Создает словарь с баллами в соответствии с критериями модели PlacePoints
        """
        place_points = PlacePoints.objects.all()

        if not place_points.exists():
            ready_points_dict = {
                1: 500,
                2: 400,
                3: 350,
                4: 300,
                5: 250,
                6: 225,
                7: 200,
                8: 175,
                9: 150,
                10: 100,
                11: 90,
                12: 80,
                13: 70,
                14: 60,
                15: 50,
                16: 45,
                17: 40,
                18: 35,
                19: 30,
                20: 25,
                21: 20,
                22: 19,
                23: 18,
                24: 17,
                25: 16,
                26: 15,
                27: 14,
                28: 13,
                29: 12,
                30: 11,
                31: 10,
                32: 9,
                33: 8,
                34: 7,
                35: 6,
                36: 5,
                37: 4,
                38: 3,
                39: 2,
                40: 1,
            }

            for my_place, my_points in ready_points_dict.items():
                PlacePoints.objects.get_or_create(
                    place=my_place,
                    points=my_points,
                )

        my_points_dict = {}
        for my_place in range(1, total_participants + 1):
            my_points_dict[my_place] = PlacePoints.objects.filter(
                place=my_place
            ).first().points

        return my_points_dict

    def calculate_points(points_dict, place):
        """
        Выводит баллы в зависимости от конкретно занятого места
        """
        return points_dict.get(place, 1)

    uid = kwargs.get('uid')
    tournament_number = kwargs.get('tournament_number')
    participant = kwargs.get('participant')
    total_participants = kwargs.get('total_participants')
    place = message.text

    if place == "Главное меню":
        main_menu(message)

    elif place == "Выход":
        logout(message)

    else:
        if place.isdigit():
            if int(place) > 0:
                if int(place) <= total_participants:
                    points_dict = create_points_dict()

                    points = calculate_points(
                        points_dict,
                        int(place)
                    )

                    transferor = Authorization.objects.get(
                        telegram_id=uid
                    )

                    tournament = Tournament.objects.get(
                        id=int(tournament_number)
                    )

                    if tournament:
                        participant_row = PointsTournament.objects.filter(
                            sender_telegram_id=participant.telegram_id,
                            transferor_telegram_id=transferor.telegram_id,
                            tournament_id=tournament.id,
                        )

                        tournament_schedule = TournamentSchedule.objects.filter(
                            tournament_id=tournament.id,
                        )

                        if tournament_schedule:
                            tournament_schedule_data = tournament_schedule.first()
                            if tournament_schedule_data.weekday_id == 7:
                                points = points * 2

                        if not participant_row.exists():
                            PointsTournament.objects.create(
                                sender_telegram_id=participant.telegram_id,
                                transferor_telegram_id=transferor.telegram_id,
                                tournament_id=tournament.id,
                                tournament_points=points,
                            )

                            update_tournament_points(
                                telegram_id=participant.telegram_id,
                            )

                        else:
                            participant_row.update(
                                tournament_points=points,
                                points_received_or_transferred=0,
                                bonuses=0,
                                points_transferred=0,
                                receiver_telegram_id=None,
                                transfer_datetime=None,
                                points_datetime=timezone.now(),
                            )

                            update_tournament_points(
                                telegram_id=participant.telegram_id,
                            )

                        bot.reply_to(
                            message,
                            f"Участник {participant.full_name} получил {points} баллов за {place} место в рейтине"
                        )

                    else:
                        bot.reply_to(
                            message,
                            "Пара 'тур-вопрос' не существует в БД"
                        )

                else:
                    bot.reply_to(
                        message,
                        f"Место в рейтинге должно быть в диапазоне от 1 до {total_participants}"
                    )

            else:
                bot.reply_to(
                    message,
                    "Некорректный ввод места в рейтинге (число должно быть больше нуля)"
                )

        else:
            bot.reply_to(
                message,
                "Некорректный ввод места в рейтинге (число должно быть числом)"
            )


def process_points_type_2_digit(message, **kwargs):
    """
    Запрашивает общую цифру для начисления баллов (2-й тип начисления баллов)
    """
    uid = kwargs.get('uid')
    tournament_number = kwargs.get('tournament_number')
    participants_list = kwargs.get('participants_list')

    if message.text == "Главное меню":
        main_menu(message)

    elif message.text == "Выход":
        logout(message)

    else:
        number = re.search(r'\d+', message.text)
        extracted_number = number.group()
        participant_id = participants_list[int(extracted_number) - 1].get('tel_id')

        if participant_id.isdigit():
            if int(participant_id) > 0:
                participant = Authorization.objects.get(
                    telegram_id=participant_id,
                )

                if participant:
                    response = bot.reply_to(
                        message,
                        "Введите общую цифру для начисления баллов:"
                    )

                    bot.register_next_step_handler(
                        response,
                        process_points_type_2_pot,
                        uid=uid,
                        tournament_number=tournament_number,
                        participant=participant,
                    )

                else:
                    bot.reply_to(
                        message,
                        "Участника не существует в БД"
                    )

            else:
                bot.reply_to(
                    message,
                    "ID должен быть больше нуля"
                )

        else:
            bot.reply_to(
                message,
                "ID должно быть числом"
            )


def process_points_type_2_pot(message, **kwargs):
    """
    Делим цифру на 50 и начисляем баллы. Фиксируем баллы в таблице PointsTournament (2-й тип начисления баллов)
    """
    uid = kwargs.get('uid')
    tournament_number = kwargs.get('tournament_number')
    participant = kwargs.get('participant')
    digit = message.text

    if digit == "Главное меню":
        main_menu(message)

    elif digit == "Выход":
        logout(message)

    else:
        if digit.isdigit():
            if int(digit) > 0:
                points = int(digit) / 50
                transferor = Authorization.objects.get(
                    telegram_id=uid
                )

                tournament = Tournament.objects.get(
                    id=int(tournament_number)
                )

                if tournament:
                    participant_row = PointsTournament.objects.filter(
                        sender_telegram_id=participant.telegram_id,
                        transferor_telegram_id=transferor.telegram_id,
                        tournament_id=tournament.id,
                    )

                    if not participant_row.exists():
                        PointsTournament.objects.create(
                            sender_telegram_id=participant.telegram_id,
                            transferor_telegram_id=transferor.telegram_id,
                            tournament_id=tournament.id,
                            points_received_or_transferred=points,
                        )

                        update_tournament_points(
                            telegram_id=participant.telegram_id,
                        )

                    else:
                        participant_row.update(
                            tournament_points=0,
                            points_received_or_transferred=points,
                            bonuses=0,
                            points_transferred=0,
                            receiver_telegram_id=None,
                            transfer_datetime=None,
                            points_datetime=timezone.now(),
                        )

                        update_tournament_points(
                            telegram_id=participant.telegram_id,
                        )

                    bot.reply_to(
                        message,
                        f"Участник {participant.full_name} получил {int(points)} баллов"
                    )

            else:
                bot.reply_to(
                    message,
                    "Некорректный ввод общей цифры (число должно быть больше нуля)"
                )

        else:
            bot.reply_to(
                message,
                "Некорректный ввод общей цифры (нужно именно число)"
            )


def process_points_type_3_bonuses(message, **kwargs):
    """
    Запрашивает размер бонуса для начисления баллов (3-й тип начисления баллов)
    """
    uid = kwargs.get('uid')
    tournament_number = kwargs.get('tournament_number')
    participants_list = kwargs.get('participants_list')

    if message.text == "Главное меню":
        main_menu(message)

    elif message.text == "Выход":
        logout(message)

    else:
        number = re.search(r'\d+', message.text)
        extracted_number = number.group()
        participant_id = participants_list[int(extracted_number) - 1].get('tel_id')

        if participant_id.isdigit():
            if int(participant_id) > 0:
                participant = Authorization.objects.get(
                    telegram_id=participant_id
                )

                if participant:
                    response = bot.reply_to(
                        message,
                        f"Введите размер бонуса (если хотите автоматом задать рандомное число введите 'random'):"
                    )

                    bot.register_next_step_handler(
                        response,
                        process_points_type_3_random,
                        uid=uid,
                        tournament_number=tournament_number,
                        participant=participant
                    )

                else:
                    bot.reply_to(
                        message,
                        "Участника не существует в БД"
                    )

            else:
                bot.reply_to(
                    message,
                    "ID должен быть больше нуля"
                )

        else:
            bot.reply_to(
                message,
                "ID должно быть числом"
            )


def process_points_type_3_random(message, **kwargs):
    """
    Запрашивает диапазон для рандомного бонуса, если пользователь ввел 'random' (3-й тип начисления баллов)
    """
    uid = kwargs.get('uid')
    tournament_number = kwargs.get('tournament_number')
    participant = kwargs.get('participant')
    bonuses = message.text

    if bonuses == "Главное меню":
        main_menu(message)

    elif bonuses == "Выход":
        logout(message)

    else:
        if bonuses.isdigit():
            if int(bonuses) > 0:
                bonuses = int(bonuses)

                process_points_type_3_result(
                    message,
                    uid=uid,
                    tournament_number=tournament_number,
                    participant=participant,
                    bonuses=bonuses
                )

            else:
                bot.reply_to(
                    message,
                    "Размер бонуса должен быть больше нуля"
                )

        else:
            if bonuses == 'random':
                response = bot.reply_to(
                    message,
                    'Введите минимальный и максимальный возможный размер бонуса через запятую (пример - 1, 100):'
                )

                bot.register_next_step_handler(
                    response,
                    process_points_type_3_result,
                    uid=uid,
                    tournament_number=tournament_number,
                    participant=participant,
                    bonuses=None
                )

            else:
                bot.reply_to(
                    message,
                    "Некорректный ввод размера бонуса"
                )


def process_points_type_3_result(message, **kwargs):
    """
    Заносит бонусы в таблицу PointsTournament (3-й тип начисления баллов)
    """
    uid = kwargs.get('uid')
    tournament_number = kwargs.get('tournament_number')
    participant = kwargs.get('participant')
    bonuses = kwargs.get('bonuses')

    if bonuses is None:
        random_bonuses = message.text

        if random_bonuses == "Главное меню":
            main_menu(message)

        elif random_bonuses == "Выход":
            logout(message)

        else:
            random_bonuses = random_bonuses.replace(' ', '').split(',')
            a = random_bonuses[0]
            b = random_bonuses[1]

            if a.isdigit() and b.isdigit():
                a = int(a)
                b = int(b)

                if a > 0 and b > 0:
                    if b > a:
                        bonuses = random.randint(a=a, b=b)

                    else:
                        bot.reply_to(
                            message,
                            "Диапазон бонуса должен быть указан от меньшего к большему в формате 'a, b'"
                        )

                else:
                    bot.reply_to(
                        message,
                        "Принимаются только положительные числа"
                    )

            else:
                bot.reply_to(
                    message,
                    "Некорректный ввод диапазона бонуса"
                )

    if bonuses and tournament_number:
        transferor = Authorization.objects.get(
            telegram_id=uid
        )

        tournament = Tournament.objects.get(
            id=int(tournament_number[0])
        )

        if tournament and transferor:
            participant_row = PointsTournament.objects.filter(
                sender_telegram_id=participant.telegram_id,
                transferor_telegram_id=transferor.telegram_id,
                tournament_id=tournament.id
            )

            if not participant_row:
                PointsTournament.objects.create(
                    sender_telegram_id=participant.telegram_id,
                    transferor_telegram_id=transferor.telegram_id,
                    tournament_id=tournament.id,
                    bonuses=bonuses
                )

                update_tournament_points(
                    telegram_id=participant.telegram_id,
                )

            else:
                participant_row.update(
                    tournament_points=0,
                    points_received_or_transferred=0,
                    bonuses=bonuses,
                    points_transferred=0,
                    points_datetime=timezone.now(),
                    transfer_datetime=None,
                    receiver_telegram_id=None,
                )

                update_tournament_points(
                    telegram_id=participant.telegram_id,
                )

            bot.reply_to(
                message,
                f"Баллы начислены участнику {participant.full_name} в размере {bonuses} баллов/балла"
            )


def process_points_type_4_receiver(message, **kwargs):
    """
    Запрашивает ID участника, которому начисляем баллы (4-й тип начисления баллов)
    """
    uid = kwargs.get('uid')
    tournament_number = kwargs.get('tournament_number')
    participants_list = kwargs.get('participants_list')

    if message.text == "Главное меню":
        main_menu(message)

    elif message.text == "Выход":
        logout(message)

    else:
        number = re.search(r'\d+', message.text)
        extracted_number = number.group()
        sender_id = participants_list.pop(int(extracted_number) - 1)
        sender_id = sender_id.get('tel_id')

        if sender_id.isdigit():
            if int(sender_id) > 0:
                sender = Authorization.objects.get(
                    telegram_id=sender_id
                )

                if sender:
                    markup = types.ReplyKeyboardMarkup(
                        resize_keyboard=True
                    )

                    btn_register = types.KeyboardButton(
                        text='Главное меню'
                    )

                    btn_login = types.KeyboardButton(
                        text='Выход'
                    )

                    markup.add(
                        btn_register,
                        btn_login,
                    )

                    for idx, _dict in enumerate(participants_list):
                        markup.add(
                            types.KeyboardButton(
                                text=str(idx + 1) + '. ' + _dict.get('name'),
                            )
                        )

                    response_receiver = bot.reply_to(
                        message,
                        "Выберите ФИО укстника, которому начисляем баллы",
                        reply_markup=markup,
                    )

                    bot.register_next_step_handler(
                        response_receiver,
                        process_points_type_4_amount,
                        tournament_number=tournament_number,
                        uid=uid,
                        sender=sender,
                        participants_list=participants_list,
                    )

                else:
                    bot.reply_to(
                        message,
                        "Участника не существует в БД"
                    )

            else:
                bot.reply_to(
                    message,
                    "ID должен быть больше нуля"
                )

        else:
            bot.reply_to(
                message,
                "ID должно быть числом"
            )


def process_points_type_4_amount(message, **kwargs):
    """
    Запрашивает количество начисляемых баллов (4-й тип начисления баллов)
    """
    uid = kwargs.get('uid')
    tournament_number = kwargs.get('tournament_number')
    sender = kwargs.get('sender')
    participants_list = kwargs.get('participants_list')

    if message.text == "Главное меню":
        main_menu(message)

    elif message.text == "Выход":
        logout(message)

    else:
        number = re.search(r'\d+', message.text)
        extracted_number = number.group()
        receiver_id = participants_list[int(extracted_number) - 1].get('tel_id')

        receiver = Authorization.objects.get(
            telegram_id=receiver_id
        )

        if int(receiver.telegram_id) != int(sender.telegram_id):
            if receiver:
                if receiver.role_id == 3:
                    response = bot.reply_to(
                        message,
                        f"Введите количество начисляемых баллов:"
                    )

                    bot.register_next_step_handler(
                        response,
                        process_points_type_4_result,
                        tournament_number=tournament_number,
                        uid=uid,
                        sender=sender,
                        receiver=receiver,
                    )

                else:
                    bot.reply_to(
                        message,
                        "Я принимаю только участников"
                    )

            else:
                bot.reply_to(
                    message,
                    "Некорректный ID участника"
                )

        else:
            bot.reply_to(
                message,
                "Нельзя переводить баллы самому себе"
            )


def process_points_type_4_result(message, **kwargs):
    """
    Фиксирует факт перевода баллов в таблицу PointsTournament (4-й тип начисления баллов)
    """
    uid = kwargs.get('uid')
    tournament_number = kwargs.get('tournament_number')
    sender = kwargs.get('sender')
    receiver = kwargs.get('receiver')
    amount = message.text

    if amount == "Главное меню":
        main_menu(message)

    elif amount == "Выход":
        logout(message)

    else:
        if amount.isdigit():
            amount = int(amount)
            if amount > 0:
                transferor = Authorization.objects.get(
                    telegram_id=uid
                )

                tournament = Tournament.objects.get(
                    id=int(tournament_number)
                )

                if tournament:
                    transaction_row11 = PointsTournament.objects.filter(
                        sender_telegram_id=sender.telegram_id,
                        transferor_telegram_id=transferor.telegram_id,
                        tournament_id=tournament.id,
                    )

                    transaction_row12 = PointsTournament.objects.filter(
                        sender_telegram_id=sender.telegram_id,
                        receiver_telegram_id=receiver.telegram_id,
                        transferor_telegram_id=transferor.telegram_id,
                        tournament_id=tournament.id,
                    )

                    if not transaction_row11.exists():
                        PointsTournament.objects.create(
                            transfer_datetime=timezone.now(),
                            sender_telegram=sender.telegram_id,
                            receiver_telegram=receiver.telegram_id,
                            points_transferred=amount,
                            transferor_telegram=transferor.telegram_id,
                            tournament_id=tournament.id,
                        )

                        update_tournament_points(
                            telegram_id=sender.telegram_id,
                        )

                        update_tournament_points(
                            telegram_id=receiver.telegram_id,
                        )

                    else:
                        if not transaction_row12.exists():
                            transaction_row11.update(
                                receiver_telegram_id=receiver.telegram_id,
                            )

                        transaction_row12.update(
                            tournament_points=0,
                            points_received_or_transferred=0,
                            bonuses=0,
                            points_transferred=amount,
                            transfer_datetime=timezone.now(),
                            points_datetime=timezone.now(),
                        )

                        update_tournament_points(
                            telegram_id=sender.telegram_id,
                        )

                        update_tournament_points(
                            telegram_id=receiver.telegram_id,
                        )

                    bot.reply_to(
                        message,
                        f"Баллы начислены участнику {receiver.full_name} в размере {amount} баллов/балла"
                    )

            else:
                bot.reply_to(
                    message,
                    "Количество начисляемых баллов должно быть больше 0"
                )

        else:
            bot.reply_to(
                message,
                "Количество начисляемых баллов должно быть числом"
            )


def tournament_rating(message, tour_number=None, my_telegram_id=None, sort_param="total_points"):
    """
    В целом отвечает за рейтинг участников в рамках викторины
    tour_number - номер тура
    my_telegram_id - Telegram ID участника
    sort_param - параметр сортировки рейтинга (по умолчанию total_points, отражающее суммарное количество баллов)
       * sort_param='total_points' - сортировка по суммарному количеству баллов
       * sort_param='total_right_answers' - сортировка по количеству правильных ответов

    Итоговое количество баллов рассчитывается относительно sender_telegram_id из таблицы PointsTransaction
    ИТОГ = total_tournament_points + total_rot_pot + total_bonuses + total_transfer_profit
        * total_tournament_points - общее количество баллов, начисленных участнику по занятому месту (тип 1)
        * total_rot_pot - общее количество баллов, начисленных участнику по принципу "РОТ/ПОТ" (тип 2)
        * total_bonuses - общее количество баллов, начисленных участнику в виде бонусов (тип 3)
        * total_transfer_profit - общий выигрыш участника, полученный в результате перевода баллов (тип 4)
            * total_transfer_profit = total_transfer_income - total_transfer_loss
            * total_transfer_income - общее количество баллов, начисленных участнику в результате перевода баллов
            * total_transfer_loss - общее количество баллов, списанных у участника в результате перевода баллов
    """
    telegram_ids = []
    participants = Authorization.objects.filter(role_id=3)

    if participants.exists():
        if participants.count() >= 1:
            for participant in participants:
                telegram_ids.append(
                    participant.telegram_id
                )

    if telegram_ids:
        participants_dict = {}
        senders = None
        question_ids = []
        tour_error = True

        if tour_number:
            if str(tour_number).isdigit():
                if int(tour_number) > 0:
                    questions = Question.objects.filter(
                        tour_id=int(tour_number)
                    )

                    if questions.exists():
                        tour_error = False

                        question_ids = [
                            question.id for question in questions
                        ]

                        senders = PointsTransaction.objects.filter(
                            sender_telegram_id__in=telegram_ids,
                            question_id__in=question_ids
                        )

                    else:
                        bot.reply_to(
                            message,
                            "Номера тура не существует"
                        )

                else:
                    bot.reply_to(
                        message,
                        "Нужно именно положительное число"
                    )

            else:
                bot.reply_to(
                    message,
                    "Нужен именно номер турнира"
                )

        else:
            senders = PointsTransaction.objects.filter(
                sender_telegram_id__in=telegram_ids
            )

        if senders:
            if senders.count() >= 1:
                for telegram_id in telegram_ids:
                    if question_ids:
                        sender_data = PointsTransaction.objects.filter(
                            sender_telegram_id=telegram_id,
                            question_id__in=question_ids
                        )

                    else:
                        sender_data = PointsTransaction.objects.filter(
                            sender_telegram_id=telegram_id
                        )

                    total_tournament_points = 0
                    total_bonuses = 0
                    total_rot_pot = 0
                    total_transfer_loss = 0
                    total_right_answers = 0
                    question_count = 0
                    tours_list = []

                    if sender_data.exists():
                        for item in sender_data:
                            total_tournament_points += item.tournament_points if item.tournament_points else 0
                            total_bonuses += item.bonuses if item.bonuses else 0
                            total_rot_pot += item.points_received_or_transferred if item.points_received_or_transferred else 0
                            total_transfer_loss += item.points_transferred if item.points_transferred else 0
                            total_right_answers += item.is_answered if item.is_answered else 0
                            question_count += item.is_done if item.is_done else 0

                            question_data = Question.objects.filter(
                                id=item.question_id
                            )

                            if question_data.exists():
                                question_data = question_data.first()

                                tours_list.append(
                                    question_data.tour_id
                                )

                        participants_dict[telegram_id] = {
                            'total_tournament_points': total_tournament_points,
                            'total_bonuses': total_bonuses,
                            'total_rot_pot': total_rot_pot,
                            'total_transfer_loss': total_transfer_loss,
                            'total_right_answers': total_right_answers,
                            'question_count': question_count,
                            'tour_count': len(set(tours_list)) if tours_list else 0,
                        }

        if question_ids:
            receivers = PointsTransaction.objects.filter(
                receiver_telegram_id__in=telegram_ids,
                question_id__in=question_ids
            )

        else:
            receivers = PointsTransaction.objects.filter(
                receiver_telegram_id__in=telegram_ids
            )

        if receivers:
            if receivers.count() >= 1:
                for telegram_id in telegram_ids:
                    if question_ids:
                        receiver_data = PointsTransaction.objects.filter(
                            receiver_telegram_id=telegram_id,
                            question_id__in=question_ids
                        )

                    else:
                        receiver_data = PointsTransaction.objects.filter(
                            receiver_telegram_id=telegram_id
                        )

                    total_transfer_income = 0

                    for item in receiver_data:
                        total_transfer_income += item.points_transferred if item.points_transferred else 0

                    if telegram_id in participants_dict:
                        participants_dict[telegram_id]['total_transfer_income'] = total_transfer_income

                    else:
                        participants_dict[telegram_id] = {
                            'total_transfer_income': total_transfer_income,
                        }

        if participants_dict:
            for _, telegram_id_dict in participants_dict.items():
                telegram_id_dict['total_transfer_profit'] = telegram_id_dict.get('total_transfer_income', 0) - \
                                                            telegram_id_dict.get('total_transfer_loss', 0)

                telegram_id_dict['total_points'] = telegram_id_dict.get('total_tournament_points', 0) + \
                                                   telegram_id_dict.get('total_bonuses', 0) + \
                                                   telegram_id_dict.get('total_rot_pot', 0) + \
                                                   telegram_id_dict.get('total_transfer_profit', 0)

            sorted_data = dict(
                sorted(
                    participants_dict.items(), key=lambda x: x[1][sort_param],
                    reverse=True
                )
            )

            ranked_data = {
                key: {**value, 'rank': i + 1} for i, (key, value) in enumerate(sorted_data.items())
            }

            data_list = []
            if ranked_data:
                for telegram_id, rank_data in ranked_data.items():
                    participant = participants.get(
                        telegram_id=telegram_id
                    )

                    data_list.append([
                        rank_data.get('rank', 0),
                        participant.full_name,
                        rank_data.get('total_points', 0),
                        rank_data.get('total_tournament_points', 0),
                        rank_data.get('total_rot_pot', 0),
                        rank_data.get('total_bonuses', 0),
                        rank_data.get('total_transfer_profit', 0),
                        rank_data.get('total_transfer_income', 0),
                        rank_data.get('total_transfer_loss', 0),
                        rank_data.get('total_right_answers', 0),
                        rank_data.get('question_count', 0),
                        rank_data.get('tour_count', 0),
                    ])

            if data_list:
                result_list = [[
                    'Место',
                    'ФИО',
                    'Общее количество баллов',
                    'Баллы, начисленные по типу 1 (рейтинг)',
                    'Баллы, начисленные по типу 2 (РОТ/ПОТ)',
                    'Баллы, начисленные по типу 3 (бонусы)',
                    'Баллы, начисленные по типу 4 (прибыль от трансфера)',
                    'Суммарный доход от трансфера',
                    'Суммарный убыток от трансфера',
                    'Количество правильных ответов',
                    'Количество вопросов',
                    'Количество туров',
                ]] + data_list

                wb = Workbook()
                ws = wb.active

                for idx, row in enumerate(result_list):
                    if not my_telegram_id:
                        ws.append(
                            row
                        )

                    else:
                        if my_telegram_id == row[3] or idx == 0:
                            ws.append(
                                row
                            )

                if my_telegram_id or question_ids:
                    if not len(data_list) >= 1:
                        bot.reply_to(
                            message,
                            "Нет результатов"
                        )

                wb.save("results.xlsx")

                if not tour_number:
                    if not my_telegram_id:
                        bot.send_document(
                            message.chat.id,
                            document=open('results.xlsx', 'rb'),
                            caption='Рейтинг участников турнира'
                        )

                        message_text = 'Список участников в рейтинге:\n\n'
                        for participant in data_list:

                            text_info = '\n'.join([
                                f'Место: {participant[0]}',
                                f'ФИО: {participant[1]}',
                                # f'Общее количество баллов: {participant[2]}',
                                # f'Баллы, начисленные по рейтингу: {participant[3]}',
                                # f'Баллы, начисленные по РОТ/ПОТ: {participant[4]}',
                                # f'Баллы, начисленные по бонусам: {participant[5]}',
                                # f'Прибыль от трансфера баллов: {participant[6]}',
                                # f'Суммарный доход от трансфера: {participant[7]}',
                                # f'Суммарный убыток от трансфера: {participant[8]}',
                                f'Количество правильных ответов: {participant[9]}',
                                f'Количество пройденных вопросов: {participant[10]}\n\n',
                                # f'Количество туров: {participant[11]}\n\n',
                            ])

                            message_text += text_info

                        bot.reply_to(
                            message,
                            message_text
                        )

                    else:
                        try:
                            idx = list(ranked_data.keys()).index(my_telegram_id)
                            participant_data = result_list[idx + 1]
                            full_name = participant_data[1]

                            df = pd.DataFrame([{
                                "Место": participant_data[0],
                                "ФИО": participant_data[1],
                                'Общее количество баллов': participant_data[2],
                                'Баллы, начисленные по рейтингу': participant_data[3],
                                'Баллы, начисленные по РОТ/ПОТ': participant_data[4],
                                'Баллы, начисленные по бонусам': participant_data[5],
                                'Прибыль от трансфера баллов': participant_data[6],
                                'Суммарный доход от трансфера': participant_data[7],
                                'Суммарный убыток от трансфера': participant_data[8],
                                'Количество правильных ответов': participant_data[9],
                                'Количество вопросов': participant_data[10],
                                'Количество туров': participant_data[11]
                            }])

                            output = BytesIO()
                            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                                df.to_excel(writer, sheet_name='Standings', index=False)
                            output.seek(0)

                            filename = "results.xlsx"

                            bot.send_document(
                                chat_id=message.chat.id,
                                document=output,
                                caption=f'Рейтинг участника ({full_name})',
                                visible_file_name=filename,
                            )

                            message_text = 'Положение участника в рейтинге:\n\n'

                            text_info = '\n'.join([
                                f'Место: {participant_data[0]}',
                                f'ФИО: {participant_data[1]}',
                                f'Общее количество баллов: {participant_data[2]}',
                                f'Баллы, начисленные по рейтингу: {participant_data[3]}',
                                f'Баллы, начисленные по РОТ/ПОТ: {participant_data[4]}',
                                f'Баллы, начисленные по бонусам: {participant_data[5]}',
                                f'Прибыль от трансфера баллов: {participant_data[6]}',
                                f'Суммарный доход от трансфера: {participant_data[7]}',
                                f'Суммарный убыток от трансфера: {participant_data[8]}',
                                f'Количество правильных ответов: {participant_data[9]}',
                                f'Количество вопросов: {participant_data[10]}',
                                f'Количество туров: {participant_data[11]}\n\n',
                            ])

                            bot.reply_to(
                                message,
                                message_text + text_info
                            )

                        except ValueError:
                            bot.reply_to(
                                message,
                                'Не удалось найти ваш результат в рейтинге'
                            )

                else:
                    if not tour_error:
                        bot.send_document(
                            message.chat.id,
                            document=open('results.xlsx', 'rb'),
                            caption='Рейтинг участников тура №' + str(tour_number)
                        )

                        message_text = f'Список участников в рейтинге по туру № {tour_number}:\n\n'

                        for participant in data_list:
                            text_info = '\n'.join([
                                f'Место: {participant[0]}',
                                f'ФИО: {participant[1]}',
                                # f'Общее количество баллов: {participant[2]}',
                                # f'Баллы, начисленные по рейтингу: {participant[3]}',
                                # f'Баллы, начисленные по РОТ/ПОТ: {participant[4]}',
                                # f'Баллы, начисленные по бонусам: {participant[5]}',
                                # f'Прибыль от трансфера баллов: {participant[6]}',
                                # f'Суммарный доход от трансфера: {participant[7]}',
                                # f'Суммарный убыток от трансфера: {participant[8]}',
                                f'Количество правильных ответов: {participant[9]}',
                                f'Количество пройденных вопросов: {participant[10]}\n\n',
                                # f'Количество туров: {participant[11]}\n\n',
                            ])

                            message_text += text_info

                        bot.reply_to(
                            message,
                            message_text
                        )

    else:
        bot.reply_to(
            message,
            "Нет участников в турнире"
        )


def points_tournament_rating(message, tour_number=None, my_telegram_id=None):
    """
    В целом отвечает за рейтинг участников в разрезе турнира
    tour_number - номер турнира
    my_telegram_id - Telegram ID участника

    Итоговое количество баллов рассчитывается относительно sender_telegram_id из таблицы PointsTransaction
    ИТОГ = total_tournament_points + total_rot_pot + total_bonuses + total_transfer_profit
        * total_tournament_points - общее количество баллов, начисленных участнику по занятому месту (тип 1)
        * total_rot_pot - общее количество баллов, начисленных участнику по принципу "РОТ/ПОТ" (тип 2)
        * total_bonuses - общее количество баллов, начисленных участнику в виде бонусов (тип 3)
        * total_transfer_profit - общий выигрыш участника, полученный в результате перевода баллов (тип 4)
            * total_transfer_profit = total_transfer_income - total_transfer_loss
            * total_transfer_income - общее количество баллов, начисленных участнику в результате перевода баллов
            * total_transfer_loss - общее количество баллов, списанных у участника в результате перевода баллов
    """
    participants = Authorization.objects.filter(
        role_id=3
    )

    telegram_ids = []
    if participants.exists():
        if participants.count() >= 1:
            for participant in participants:
                telegram_ids.append(
                    participant.telegram_id
                )

    if telegram_ids:
        participants_dict = {}
        senders = None
        tournament_ids = []
        tour_error = True

        if tour_number:
            if str(tour_number).isdigit():
                if int(tour_number) > 0:

                    tournament = Tournament.objects.filter(
                        id=int(tour_number)
                    )

                    if tournament.exists():
                        tour_error = False

                        tournament_ids = [
                            tournament_obj.id for tournament_obj in tournament
                        ]

                        senders = PointsTournament.objects.filter(
                            sender_telegram_id__in=telegram_ids,
                            tournament_id__in=tournament_ids
                        )

                    else:
                        bot.reply_to(
                            message,
                            "Номера турнира не существует"
                        )

                else:
                    bot.reply_to(
                        message,
                        "Нужно именно положительное число"
                    )

            else:
                bot.reply_to(
                    message,
                    "Нужен именно номер турнира"
                )

        else:
            senders = PointsTournament.objects.filter(
                sender_telegram_id__in=telegram_ids
            )

        if senders:
            if senders.count() >= 1:
                for telegram_id in telegram_ids:
                    if tournament_ids:
                        sender_data = PointsTournament.objects.filter(
                            sender_telegram_id=telegram_id,
                            tournament_id__in=tournament_ids
                        )

                    else:
                        sender_data = PointsTournament.objects.filter(
                            sender_telegram_id=telegram_id
                        )

                    total_tournament_points = 0
                    total_bonuses = 0
                    total_rot_pot = 0
                    total_transfer_loss = 0
                    tours_list = []

                    if sender_data.exists():
                        for item in sender_data:
                            total_tournament_points += item.tournament_points if item.tournament_points else 0
                            total_bonuses += item.bonuses if item.bonuses else 0
                            total_rot_pot += item.points_received_or_transferred if item.points_received_or_transferred else 0
                            total_transfer_loss += item.points_transferred if item.points_transferred else 0

                            tournament_data = Tournament.objects.filter(
                                id=item.tournament_id
                            )

                            if tournament_data.exists():
                                tournament_data = tournament_data.first()

                                tours_list.append(
                                    tournament_data.id
                                )

                        participants_dict[telegram_id] = {
                            'total_tournament_points': total_tournament_points,
                            'total_bonuses': total_bonuses,
                            'total_rot_pot': total_rot_pot,
                            'total_transfer_loss': total_transfer_loss,
                            'tour_count': len(set(tours_list)) if tours_list else 0,
                        }

        if tournament_ids:
            receivers = PointsTournament.objects.filter(
                receiver_telegram_id__in=telegram_ids,
                tournament_id__in=tournament_ids
            )

        else:
            receivers = PointsTournament.objects.filter(
                receiver_telegram_id__in=telegram_ids
            )

        if receivers:
            if receivers.count() >= 1:
                for telegram_id in telegram_ids:

                    if tournament_ids:
                        receiver_data = PointsTournament.objects.filter(
                            receiver_telegram_id=telegram_id,
                            tournament_id__in=tournament_ids
                        )

                    else:
                        receiver_data = PointsTournament.objects.filter(
                            receiver_telegram_id=telegram_id
                        )

                    total_transfer_income = 0

                    for item in receiver_data:
                        total_transfer_income += item.points_transferred if item.points_transferred else 0

                    if telegram_id in participants_dict:
                        participants_dict[telegram_id]['total_transfer_income'] = total_transfer_income

                    else:
                        participants_dict[telegram_id] = {
                            'total_transfer_income': total_transfer_income,
                        }

        if participants_dict:
            for _, telegram_id_dict in participants_dict.items():
                telegram_id_dict['total_transfer_profit'] = telegram_id_dict.get('total_transfer_income', 0) - \
                                                            telegram_id_dict.get('total_transfer_loss', 0)

                telegram_id_dict['total_points'] = telegram_id_dict.get('total_tournament_points', 0) + \
                                                   telegram_id_dict.get('total_bonuses', 0) + \
                                                   telegram_id_dict.get('total_rot_pot', 0) + \
                                                   telegram_id_dict.get('total_transfer_profit', 0)

            sorted_data = dict(
                sorted(
                    participants_dict.items(), key=lambda x: x[1]['total_points'],
                    reverse=True
                )
            )

            ranked_data = {
                key: {**value, 'rank': i + 1} for i, (key, value) in enumerate(sorted_data.items())
            }

            data_list = []
            if ranked_data:
                for telegram_id, rank_data in ranked_data.items():
                    participant = participants.get(
                        telegram_id=telegram_id
                    )

                    data_list.append([
                        rank_data.get('rank', 0),
                        participant.full_name,
                        rank_data.get('total_points', 0),
                        rank_data.get('total_tournament_points', 0),
                        rank_data.get('total_rot_pot', 0),
                        rank_data.get('total_bonuses', 0),
                        rank_data.get('total_transfer_profit', 0),
                        rank_data.get('total_transfer_income', 0),
                        rank_data.get('total_transfer_loss', 0),
                        rank_data.get('tour_count', 0),
                    ])

            if data_list:
                result_list = [[
                    'Место',
                    'ФИО',
                    'Общее количество баллов',
                    'Баллы, начисленные по типу 1 (рейтинг)',
                    'Баллы, начисленные по типу 2 (РОТ/ПОТ)',
                    'Баллы, начисленные по типу 3 (бонусы)',
                    'Баллы, начисленные по типу 4 (прибыль от трансфера)',
                    'Суммарный доход от трансфера',
                    'Суммарный убыток от трансфера',
                    'Количество турниров',
                ]] + data_list

                wb = Workbook()
                ws = wb.active

                for idx, row in enumerate(result_list):
                    if not my_telegram_id:
                        ws.append(
                            row
                        )

                    else:
                        if my_telegram_id == row[3] or idx == 0:
                            ws.append(
                                row
                            )

                if my_telegram_id or tournament_ids:
                    if not len(data_list) >= 1:
                        bot.reply_to(
                            message,
                            "Нет результатов"
                        )

                wb.save("results.xlsx")

                if not tour_number:
                    if not my_telegram_id:
                        bot.send_document(
                            message.chat.id,
                            document=open('results.xlsx', 'rb'),
                            caption='Рейтинг участников турнира'
                        )

                        message_text = 'Список участников в рейтинге:\n\n'
                        for participant in data_list:

                            text_info = '\n'.join([
                                f'Место: {participant[0]}',
                                f'ФИО: {participant[1]}',
                                f'Общее количество баллов: {participant[2]}\n\n',
                                # f'Баллы, начисленные по рейтингу: {participant[3]}',
                                # f'Баллы, начисленные по РОТ/ПОТ: {participant[4]}',
                                # f'Баллы, начисленные по бонусам: {participant[5]}',
                                # f'Прибыль от трансфера баллов: {participant[6]}',
                                # f'Суммарный доход от трансфера: {participant[7]}',
                                # f'Суммарный убыток от трансфера: {participant[8]}',
                                # f'Количество турниров: {participant[9]}\n\n',
                            ])

                            message_text += text_info

                        bot.reply_to(
                            message,
                            message_text
                        )

                    else:
                        try:
                            idx = list(ranked_data.keys()).index(my_telegram_id)
                            participant_data = result_list[idx + 1]
                            full_name = participant_data[1]

                            df = pd.DataFrame([{
                                'Место': participant_data[0],
                                'ФИО': participant_data[1],
                                'Общее количество баллов': participant_data[2],
                                'Баллы, начисленные по рейтингу': participant_data[3],
                                'Баллы, начисленные по РОТ/ПОТ': participant_data[4],
                                'Баллы, начисленные по бонусам': participant_data[5],
                                'Прибыль от трансфера баллов': participant_data[6],
                                'Суммарный доход от трансфера': participant_data[7],
                                'Суммарный убыток от трансфера': participant_data[8],
                                'Количество турниров': participant_data[9],
                            }])

                            output = BytesIO()
                            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                                df.to_excel(writer, sheet_name='Standings', index=False)
                            output.seek(0)

                            filename = "results.xlsx"

                            bot.send_document(
                                chat_id=message.chat.id,
                                document=output,
                                caption=f'Рейтинг участника ({full_name})',
                                visible_file_name=filename,
                            )

                            message_text = 'Положение участника в рейтинге:\n\n'

                            text_info = '\n'.join([
                                f'Место: {participant_data[0]}',
                                f'ФИО: {participant_data[1]}',
                                f'Общее количество баллов: {participant_data[2]}',
                                f'Баллы, начисленные по рейтингу: {participant_data[3]}',
                                f'Баллы, начисленные по РОТ/ПОТ: {participant_data[4]}',
                                f'Баллы, начисленные по бонусам: {participant_data[5]}',
                                f'Прибыль от трансфера баллов: {participant_data[6]}',
                                f'Суммарный доход от трансфера: {participant_data[7]}',
                                f'Суммарный убыток от трансфера: {participant_data[8]}',
                                f'Количество турниров: {participant_data[9]}\n\n',
                            ])

                            bot.reply_to(
                                message,
                                message_text + text_info
                            )

                        except ValueError:
                            bot.reply_to(
                                message,
                                'Не удалось найти ваш результат в рейтинге'
                            )

                else:
                    if not tour_error:
                        bot.send_document(
                            message.chat.id,
                            document=open('results.xlsx', 'rb'),
                            caption='Рейтинг участников турнира №' + str(tour_number)
                        )

                        message_text = f'Список участников в рейтинге по турниру № {tour_number}:\n\n'

                        for participant in data_list:
                            text_info = '\n'.join([
                                f'Место: {participant[0]}',
                                f'ФИО: {participant[1]}',
                                f'Общее количество баллов: {participant[2]}\n\n',
                                # f'Баллы, начисленные по рейтингу: {participant[3]}',
                                # f'Баллы, начисленные по РОТ/ПОТ: {participant[4]}',
                                # f'Баллы, начисленные по бонусам: {participant[5]}',
                                # f'Прибыль от трансфера баллов: {participant[6]}',
                                # f'Суммарный доход от трансфера: {participant[7]}',
                                # f'Суммарный убыток от трансфера: {participant[8]}',
                                # f'Количество турниров: {participant[9]}\n\n',
                            ])

                            message_text += text_info

                        bot.reply_to(
                            message,
                            message_text
                        )

    else:
        bot.reply_to(
            message,
            "Нет участников в турнире"
        )


@bot.message_handler(func=lambda message: 'Рейтинг (баллы, квиз)' in message.text or message.text == '/quiz_rating')
def tournament_rating_realization(message):
    """"
    Выводит общий рейтинг турнира в виде Excel-файла
    """
    is_AttributeError = False
    uid = message.from_user.id

    user_auth_data = Authorization.objects.filter(
        telegram_id=uid
    )

    try:
        custom_user = CustomUser.objects.get(
            username_id=user_auth_data.first().id
        )
    except AttributeError as e:
        is_AttributeError = True

    if user_auth_data.exists() and not is_AttributeError:
        if custom_user.is_authorized:

            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_main_menu = types.KeyboardButton(
                text='Главное меню'
            )

            btn_logout = types.KeyboardButton(
                text='Выход'
            )

            markup.add(
                btn_main_menu,
                btn_logout
            )

            bot.send_message(
                message.chat.id,
                "Общий рейтинг по баллам",
                reply_markup=markup
            )

            tournament_rating(
                message=message
            )

        else:
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_register = types.KeyboardButton(
                text='Регистрация'
            )

            btn_login = types.KeyboardButton(
                text='Авторизация'
            )

            btn_password = types.KeyboardButton(
                text='Забыл пароль'
            )

            mon_btn = types.KeyboardButton(
                text='пн'
            )

            tue_btn = types.KeyboardButton(
                text='вт'
            )

            wed_btn = types.KeyboardButton(
                text='ср'
            )

            thu_btn = types.KeyboardButton(
                text='чт'
            )

            fri_btn = types.KeyboardButton(
                text='пт'
            )

            sat_btn = types.KeyboardButton(
                text='сб'
            )

            sun_btn = types.KeyboardButton(
                text='вс'
            )

            markup.add(
                mon_btn,
                tue_btn,
                wed_btn,
                thu_btn,
                fri_btn,
                sat_btn,
                sun_btn,
                btn_register,
                btn_login,
                btn_password
            )

            bot.reply_to(
                message,
                "Вы не авторизованы. Для авторизации введите /login",
                reply_markup=markup,
            )

    else:
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        btn_register = types.KeyboardButton(
            text='Регистрация'
        )

        btn_login = types.KeyboardButton(
            text='Авторизация'
        )

        btn_password = types.KeyboardButton(
            text='Забыл пароль'
        )

        mon_btn = types.KeyboardButton(
            text='пн'
        )

        tue_btn = types.KeyboardButton(
            text='вт'
        )

        wed_btn = types.KeyboardButton(
            text='ср'
        )

        thu_btn = types.KeyboardButton(
            text='чт'
        )

        fri_btn = types.KeyboardButton(
            text='пт'
        )

        sat_btn = types.KeyboardButton(
            text='сб'
        )

        sun_btn = types.KeyboardButton(
            text='вс'
        )

        markup.add(
            mon_btn,
            tue_btn,
            wed_btn,
            thu_btn,
            fri_btn,
            sat_btn,
            sun_btn,
            btn_register,
            btn_login,
            btn_password
        )

        bot.reply_to(
            message,
            "Вы не зарегистрированы. Для регистрации введите /register",
            reply_markup=markup
        )


@bot.message_handler(func=lambda message: 'Личный рейтинг (баллы, квиз)' in message.text or message.text=='/my_quiz_rating')
def participant_question(message):
    """"
    Фиксирует Telegram ID участника для вывода индивидуального рейтинга
    """
    is_AttributeError = False
    uid = message.from_user.id
    user_auth_data = Authorization.objects.filter(
        telegram_id=uid
    )

    try:
        custom_user = CustomUser.objects.get(
            username_id=user_auth_data.first().id
        )
    except AttributeError as e:
        is_AttributeError = True

    participants = Authorization.objects.all().filter(
        role=3
    )

    participants_list = []
    if user_auth_data.exists() and not is_AttributeError:
        if custom_user.is_authorized:
            tournament_rating(
                message=message,
                my_telegram_id=str(message.from_user.id)
            )

            main_menu(message)

        else:
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_register = types.KeyboardButton(
                text='Регистрация'
            )

            btn_login = types.KeyboardButton(
                text='Авторизация'
            )

            btn_password = types.KeyboardButton(
                text='Забыл пароль'
            )

            mon_btn = types.KeyboardButton(
                text='пн'
            )

            tue_btn = types.KeyboardButton(
                text='вт'
            )

            wed_btn = types.KeyboardButton(
                text='ср'
            )

            thu_btn = types.KeyboardButton(
                text='чт'
            )

            fri_btn = types.KeyboardButton(
                text='пт'
            )

            sat_btn = types.KeyboardButton(
                text='сб'
            )

            sun_btn = types.KeyboardButton(
                text='вс'
            )

            markup.add(
                mon_btn,
                tue_btn,
                wed_btn,
                thu_btn,
                fri_btn,
                sat_btn,
                sun_btn,
                btn_register,
                btn_login,
                btn_password
            )

            bot.reply_to(
                message,
                "Вы не авторизованы. Для авторизации введите /login",
                reply_markup=markup,
            )

    else:
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        btn_register = types.KeyboardButton(
            text='Регистрация'
        )

        btn_login = types.KeyboardButton(
            text='Авторизация'
        )

        btn_password = types.KeyboardButton(
            text='Забыл пароль'
        )

        mon_btn = types.KeyboardButton(
            text='пн'
        )

        tue_btn = types.KeyboardButton(
            text='вт'
        )

        wed_btn = types.KeyboardButton(
            text='ср'
        )

        thu_btn = types.KeyboardButton(
            text='чт'
        )

        fri_btn = types.KeyboardButton(
            text='пт'
        )

        sat_btn = types.KeyboardButton(
            text='сб'
        )

        sun_btn = types.KeyboardButton(
            text='вс'
        )

        markup.add(
            mon_btn,
            tue_btn,
            wed_btn,
            thu_btn,
            fri_btn,
            sat_btn,
            sun_btn,
            btn_register,
            btn_login,
            btn_password
        )

        bot.reply_to(
            message,
            "Вы не зарегистрированы. Для регистрации введите /register",
            reply_markup=markup
        )


@bot.message_handler(func=lambda message: 'Рейтинг (тур, квиз)' in message.text or message.text == '/quiz_tour_stat')
def tour_question(message):
    """"
    Фиксирует номер тура для вывода рейтинга участников в разрезе тура
    """
    is_AttributeError = False
    uid = message.from_user.id
    user_auth_data = Authorization.objects.filter(
        telegram_id=uid
    )

    try:
        custom_user = CustomUser.objects.get(
            username_id=user_auth_data.first().id
        )
    except AttributeError as e:
        is_AttributeError = True

    if user_auth_data.exists() and not is_AttributeError:
        if custom_user.is_authorized:
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_main_menu = types.KeyboardButton(
                text='Главное меню'
            )

            btn_logout = types.KeyboardButton(
                text='Выход'
            )

            markup.add(
                btn_main_menu,
                btn_logout
            )

            response = bot.reply_to(
                message,
                "Введите номер тура по которому хотите получить статистику",
                reply_markup=markup,
            )

            bot.register_next_step_handler(
                response,
                process_tour_question,
            )

        else:
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_register = types.KeyboardButton(
                text='Регистрация'
            )

            btn_login = types.KeyboardButton(
                text='Авторизация'
            )

            btn_password = types.KeyboardButton(
                text='Забыл пароль'
            )

            mon_btn = types.KeyboardButton(
                text='пн'
            )

            tue_btn = types.KeyboardButton(
                text='вт'
            )

            wed_btn = types.KeyboardButton(
                text='ср'
            )

            thu_btn = types.KeyboardButton(
                text='чт'
            )

            fri_btn = types.KeyboardButton(
                text='пт'
            )

            sat_btn = types.KeyboardButton(
                text='сб'
            )

            sun_btn = types.KeyboardButton(
                text='вс'
            )

            markup.add(
                mon_btn,
                tue_btn,
                wed_btn,
                thu_btn,
                fri_btn,
                sat_btn,
                sun_btn,
                btn_register,
                btn_login,
                btn_password
            )

            bot.reply_to(
                message,
                "Вы не авторизованы. Для авторизации введите /login",
                reply_markup=markup,
            )

    else:
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        btn_register = types.KeyboardButton(
            text='Регистрация'
        )

        btn_login = types.KeyboardButton(
            text='Авторизация'
        )

        btn_password = types.KeyboardButton(
            text='Забыл пароль'
        )

        mon_btn = types.KeyboardButton(
            text='пн'
        )

        tue_btn = types.KeyboardButton(
            text='вт'
        )

        wed_btn = types.KeyboardButton(
            text='ср'
        )

        thu_btn = types.KeyboardButton(
            text='чт'
        )

        fri_btn = types.KeyboardButton(
            text='пт'
        )

        sat_btn = types.KeyboardButton(
            text='сб'
        )

        sun_btn = types.KeyboardButton(
            text='вс'
        )

        markup.add(
            mon_btn,
            tue_btn,
            wed_btn,
            thu_btn,
            fri_btn,
            sat_btn,
            sun_btn,
            btn_register,
            btn_login,
            btn_password
        )

        markup.add(
            btn_register,
            btn_login,
            btn_password
        )

        bot.reply_to(
            message,
            "Вы не зарегистрированы. Для регистрации введите /register",
            reply_markup=markup
        )


def process_tour_question(message):
    """"
    Выводит рейтинг тура в виде Excel-файла
    """
    tour_number = message.text

    if tour_number == "Главное меню":
        main_menu(message)

    elif tour_number == "Выход":
        logout(message)

    else:
        tournament_rating(
            message,
            tour_number
        )


@bot.message_handler(func=lambda message: 'Рейтинг (туры, квиз)' in message.text or message.text == '/quiz_tours_stat')
def tours_output(message):
    """"
    Выводит рейтинг всех туров сразу в виде Excel-файла
    """
    is_AttributeError = False
    uid = message.from_user.id
    user_auth_data = Authorization.objects.filter(
        telegram_id=uid
    )

    try:
        custom_user = CustomUser.objects.get(
            username_id=user_auth_data.first().id
        )
    except AttributeError as e:
        is_AttributeError = True

    if user_auth_data.exists() and not is_AttributeError:
        if custom_user.is_authorized:

            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_main_menu = types.KeyboardButton(
                text='Главное меню'
            )

            btn_logout = types.KeyboardButton(
                text='Выход'
            )

            markup.add(
                btn_main_menu,
                btn_logout
            )

            tours = Question.objects.all().values_list(
                'tour_id',
                flat=True
            ).distinct()

            if tours.exists():
                bot.reply_to(
                     message,
                    'Вывожу результаты туров',
                    reply_markup=markup
                )

                for tour in tours:
                    tournament_rating(
                        message,
                        tour_number=tour,
                    )

            else:
                bot.reply_to(
                    message,
                    "Нет туров для получения статистики"
                )

        else:
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_register = types.KeyboardButton(
                text='Регистрация'
            )

            btn_login = types.KeyboardButton(
                text='Авторизация'
            )

            btn_password = types.KeyboardButton(
                text='Забыл пароль'
            )

            mon_btn = types.KeyboardButton(
                text='пн'
            )

            tue_btn = types.KeyboardButton(
                text='вт'
            )

            wed_btn = types.KeyboardButton(
                text='ср'
            )

            thu_btn = types.KeyboardButton(
                text='чт'
            )

            fri_btn = types.KeyboardButton(
                text='пт'
            )

            sat_btn = types.KeyboardButton(
                text='сб'
            )

            sun_btn = types.KeyboardButton(
                text='вс'
            )

            markup.add(
                mon_btn,
                tue_btn,
                wed_btn,
                thu_btn,
                fri_btn,
                sat_btn,
                sun_btn,
                btn_register,
                btn_login,
                btn_password
            )

            bot.reply_to(
                message,
                "Вы не авторизованы. Для авторизации введите /login",
                reply_markup=markup,
            )

    else:
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        btn_register = types.KeyboardButton(
            text='Регистрация'
        )

        btn_login = types.KeyboardButton(
            text='Авторизация'
        )

        btn_password = types.KeyboardButton(
            text='Забыл пароль'
        )

        mon_btn = types.KeyboardButton(
            text='пн'
        )

        tue_btn = types.KeyboardButton(
            text='вт'
        )

        wed_btn = types.KeyboardButton(
            text='ср'
        )

        thu_btn = types.KeyboardButton(
            text='чт'
        )

        fri_btn = types.KeyboardButton(
            text='пт'
        )

        sat_btn = types.KeyboardButton(
            text='сб'
        )

        sun_btn = types.KeyboardButton(
            text='вс'
        )

        markup.add(
            mon_btn,
            tue_btn,
            wed_btn,
            thu_btn,
            fri_btn,
            sat_btn,
            sun_btn,
            btn_register,
            btn_login,
            btn_password
        )

        bot.reply_to(
            message,
            "Вы не зарегистрированы. Для регистрации введите /register",
            reply_markup=markup,
        )


@bot.message_handler(func=lambda message: 'Рейтинг (ответы, квиз)' in message.text or message.text=='/quiz_answers_rating')
def answers_rating(message):
    """"
    Выводит рейтинг участников с сортированием по количеству правильных ответов
    """
    is_AttributeError = False
    uid = message.from_user.id
    user_auth_data = Authorization.objects.filter(
        telegram_id=uid
    )

    try:
        custom_user = CustomUser.objects.get(
            username_id=user_auth_data.first().id
        )
    except AttributeError as e:
        is_AttributeError = True

    if user_auth_data.exists() and not is_AttributeError:
        if custom_user.is_authorized:

            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_main_menu = types.KeyboardButton(
                text='Главное меню'
            )

            btn_logout = types.KeyboardButton(
                text='Выход'
            )

            markup.add(
                btn_main_menu,
                btn_logout
            )

            bot.reply_to(
                message,
                'Вывожу рейтинг участников с сортировкой по количеству правильных ответов',
                reply_markup=markup
            )

            tournament_rating(
                message,
                sort_param='total_right_answers'
            )

        else:
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_register = types.KeyboardButton(
                text='Регистрация'
            )

            btn_login = types.KeyboardButton(
                text='Авторизация'
            )

            btn_password = types.KeyboardButton(
                text='Забыл пароль'
            )

            mon_btn = types.KeyboardButton(
                text='пн'
            )

            tue_btn = types.KeyboardButton(
                text='вт'
            )

            wed_btn = types.KeyboardButton(
                text='ср'
            )

            thu_btn = types.KeyboardButton(
                text='чт'
            )

            fri_btn = types.KeyboardButton(
                text='пт'
            )

            sat_btn = types.KeyboardButton(
                text='сб'
            )

            sun_btn = types.KeyboardButton(
                text='вс'
            )

            markup.add(
                btn_register,
                btn_login,
                btn_password,
                mon_btn,
                tue_btn,
                wed_btn,
                thu_btn,
                fri_btn,
                sat_btn,
                sun_btn,
            )

            bot.reply_to(
                message,
                "Вы не авторизованы. Для авторизации введите /login",
                reply_markup=markup,
            )

    else:
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        btn_register = types.KeyboardButton(
            text='Регистрация'
        )

        btn_login = types.KeyboardButton(
            text='Авторизация'
        )

        btn_password = types.KeyboardButton(
            text='Забыл пароль'
        )

        mon_btn = types.KeyboardButton(
            text='пн'
        )

        tue_btn = types.KeyboardButton(
            text='вт'
        )

        wed_btn = types.KeyboardButton(
            text='ср'
        )

        thu_btn = types.KeyboardButton(
            text='чт'
        )

        fri_btn = types.KeyboardButton(
            text='пт'
        )

        sat_btn = types.KeyboardButton(
            text='сб'
        )

        sun_btn = types.KeyboardButton(
            text='вс'
        )

        markup.add(
            mon_btn,
            tue_btn,
            wed_btn,
            thu_btn,
            fri_btn,
            sat_btn,
            sun_btn,
            btn_register,
            btn_login,
            btn_password
        )

        bot.reply_to(
            message,
            "Вы не зарегистрированы. Для регистрации введите /register",
            reply_markup=markup,
        )


@bot.message_handler(func=lambda message: 'Рейтинг (баллы, турнир)' in message.text or message.text == '/tournament_rating')
def tournament_rating_realization2(message):
    """"
    Выводит общий рейтинг турнира в виде Excel-файла
    """
    is_AttributeError = False
    uid = message.from_user.id

    user_auth_data = Authorization.objects.filter(
        telegram_id=uid
    )

    try:
        custom_user = CustomUser.objects.get(
            username_id=user_auth_data.first().id
        )
    except AttributeError as e:
        is_AttributeError = True

    if user_auth_data.exists() and not is_AttributeError:
        if custom_user.is_authorized:

            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_main_menu = types.KeyboardButton(
                text='Главное меню'
            )

            btn_logout = types.KeyboardButton(
                text='Выход'
            )

            markup.add(
                btn_main_menu,
                btn_logout
            )

            bot.send_message(
                message.chat.id,
                "Общий рейтинг по баллам",
                reply_markup=markup
            )

            points_tournament_rating(
                message=message
            )

        else:
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_register = types.KeyboardButton(
                text='Регистрация'
            )

            btn_login = types.KeyboardButton(
                text='Авторизация'
            )

            btn_password = types.KeyboardButton(
                text='Забыл пароль'
            )

            mon_btn = types.KeyboardButton(
                text='пн'
            )

            tue_btn = types.KeyboardButton(
                text='вт'
            )

            wed_btn = types.KeyboardButton(
                text='ср'
            )

            thu_btn = types.KeyboardButton(
                text='чт'
            )

            fri_btn = types.KeyboardButton(
                text='пт'
            )

            sat_btn = types.KeyboardButton(
                text='сб'
            )

            sun_btn = types.KeyboardButton(
                text='вс'
            )

            markup.add(
                mon_btn,
                tue_btn,
                wed_btn,
                thu_btn,
                fri_btn,
                sat_btn,
                sun_btn,
                btn_register,
                btn_login,
                btn_password
            )

            bot.reply_to(
                message,
                "Вы не авторизованы. Для авторизации введите /login",
                reply_markup=markup,
            )

    else:
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        btn_register = types.KeyboardButton(
            text='Регистрация'
        )

        btn_login = types.KeyboardButton(
            text='Авторизация'
        )

        btn_password = types.KeyboardButton(
            text='Забыл пароль'
        )

        mon_btn = types.KeyboardButton(
            text='пн'
        )

        tue_btn = types.KeyboardButton(
            text='вт'
        )

        wed_btn = types.KeyboardButton(
            text='ср'
        )

        thu_btn = types.KeyboardButton(
            text='чт'
        )

        fri_btn = types.KeyboardButton(
            text='пт'
        )

        sat_btn = types.KeyboardButton(
            text='сб'
        )

        sun_btn = types.KeyboardButton(
            text='вс'
        )

        markup.add(
            mon_btn,
            tue_btn,
            wed_btn,
            thu_btn,
            fri_btn,
            sat_btn,
            sun_btn,
            btn_register,
            btn_login,
            btn_password
        )

        bot.reply_to(
            message,
            "Вы не зарегистрированы. Для регистрации введите /register",
            reply_markup=markup
        )


@bot.message_handler(func=lambda message: 'Личный рейтинг (баллы, турнир)' in message.text or message.text == '/my_tournam_rating')
def participant_question2(message):
    """"
    Фиксирует Telegram ID участника для вывода индивидуального рейтинга
    """
    is_AttributeError = False
    uid = message.from_user.id

    user_auth_data = Authorization.objects.filter(
        telegram_id=uid
    )

    try:
        custom_user = CustomUser.objects.get(
            username_id=user_auth_data.first().id
        )
    except AttributeError as e:
        is_AttributeError = True

    participants = Authorization.objects.all().filter(
        role=3
    )

    participants_list = []
    if user_auth_data.exists() and not is_AttributeError:
        if custom_user.is_authorized:
            points_tournament_rating(
                message=message,
                my_telegram_id=str(message.from_user.id),
            )

            main_menu(message)

        else:
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_register = types.KeyboardButton(
                text='Регистрация'
            )

            btn_login = types.KeyboardButton(
                text='Авторизация'
            )

            btn_password = types.KeyboardButton(
                text='Забыл пароль'
            )

            mon_btn = types.KeyboardButton(
                text='пн'
            )

            tue_btn = types.KeyboardButton(
                text='вт'
            )

            wed_btn = types.KeyboardButton(
                text='ср'
            )

            thu_btn = types.KeyboardButton(
                text='чт'
            )

            fri_btn = types.KeyboardButton(
                text='пт'
            )

            sat_btn = types.KeyboardButton(
                text='сб'
            )

            sun_btn = types.KeyboardButton(
                text='вс'
            )

            markup.add(
                mon_btn,
                tue_btn,
                wed_btn,
                thu_btn,
                fri_btn,
                sat_btn,
                sun_btn,
                btn_register,
                btn_login,
                btn_password
            )

            bot.reply_to(
                message,
                "Вы не авторизованы. Для авторизации введите /login",
                reply_markup=markup,
            )

    else:
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        btn_register = types.KeyboardButton(
            text='Регистрация'
        )

        btn_login = types.KeyboardButton(
            text='Авторизация'
        )

        btn_password = types.KeyboardButton(
            text='Забыл пароль'
        )

        mon_btn = types.KeyboardButton(
            text='пн'
        )

        tue_btn = types.KeyboardButton(
            text='вт'
        )

        wed_btn = types.KeyboardButton(
            text='ср'
        )

        thu_btn = types.KeyboardButton(
            text='чт'
        )

        fri_btn = types.KeyboardButton(
            text='пт'
        )

        sat_btn = types.KeyboardButton(
            text='сб'
        )

        sun_btn = types.KeyboardButton(
            text='вс'
        )

        markup.add(
            mon_btn,
            tue_btn,
            wed_btn,
            thu_btn,
            fri_btn,
            sat_btn,
            sun_btn,
            btn_register,
            btn_login,
            btn_password
        )

        bot.reply_to(
            message,
            "Вы не зарегистрированы. Для регистрации введите /register",
            reply_markup=markup
        )


def process_participant_rating_question2(message, participants_list):
    """"
    Выводит индивидуальный рейтинг турнира в виде Excel-файла
    """
    participant_full_name = message.text

    if participant_full_name == "Главное меню":
        main_menu(message)

    elif participant_full_name == "Выход":
        logout(message)

    if participant_full_name[3:] in [_dict.get("participant_full_name") for _dict in participants_list]:
        number = re.search(r'\d+', participant_full_name)
        idx = int(number.group())

        telegram_id = participants_list[idx - 1].get('part_tel_id')

        tournament_rating(
            message=message,
            my_telegram_id=telegram_id
        )


@bot.message_handler(func=lambda message: 'Рейтинг (тур, турнир)' in message.text or message.text == '/tournam_stat')
def tour_question2(message):
    """"
    Фиксирует номер тура для вывода рейтинга участников в разрезе турнира
    """
    is_AttributeError = False
    uid = message.from_user.id
    user_auth_data = Authorization.objects.filter(
        telegram_id=uid
    )

    try:
        custom_user = CustomUser.objects.get(
            username_id=user_auth_data.first().id
        )
    except AttributeError as e:
        is_AttributeError = True

    if user_auth_data.exists() and not is_AttributeError:
        if custom_user.is_authorized:
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_main_menu = types.KeyboardButton(
                text='Главное меню'
            )

            btn_logout = types.KeyboardButton(
                text='Выход'
            )

            markup.add(
                btn_main_menu,
                btn_logout
            )

            response = bot.reply_to(
                message,
                "Введите номер турнира по которому хотите получить статистику",
                reply_markup=markup,
            )

            bot.register_next_step_handler(
                response,
                process_tour_question2,
            )

        else:
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_register = types.KeyboardButton(
                text='Регистрация'
            )

            btn_login = types.KeyboardButton(
                text='Авторизация'
            )

            btn_password = types.KeyboardButton(
                text='Забыл пароль'
            )

            mon_btn = types.KeyboardButton(
                text='пн'
            )

            tue_btn = types.KeyboardButton(
                text='вт'
            )

            wed_btn = types.KeyboardButton(
                text='ср'
            )

            thu_btn = types.KeyboardButton(
                text='чт'
            )

            fri_btn = types.KeyboardButton(
                text='пт'
            )

            sat_btn = types.KeyboardButton(
                text='сб'
            )

            sun_btn = types.KeyboardButton(
                text='вс'
            )

            markup.add(
                mon_btn,
                tue_btn,
                wed_btn,
                thu_btn,
                fri_btn,
                sat_btn,
                sun_btn,
                btn_register,
                btn_login,
                btn_password
            )

            bot.reply_to(
                message,
                "Вы не авторизованы. Для авторизации введите /login",
                reply_markup=markup,
            )

    else:
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        btn_register = types.KeyboardButton(
            text='Регистрация'
        )

        btn_login = types.KeyboardButton(
            text='Авторизация'
        )

        btn_password = types.KeyboardButton(
            text='Забыл пароль'
        )

        mon_btn = types.KeyboardButton(
            text='пн'
        )

        tue_btn = types.KeyboardButton(
            text='вт'
        )

        wed_btn = types.KeyboardButton(
            text='ср'
        )

        thu_btn = types.KeyboardButton(
            text='чт'
        )

        fri_btn = types.KeyboardButton(
            text='пт'
        )

        sat_btn = types.KeyboardButton(
            text='сб'
        )

        sun_btn = types.KeyboardButton(
            text='вс'
        )

        markup.add(
            mon_btn,
            tue_btn,
            wed_btn,
            thu_btn,
            fri_btn,
            sat_btn,
            sun_btn,
            btn_register,
            btn_login,
            btn_password
        )

        bot.reply_to(
            message,
            "Вы не зарегистрированы. Для регистрации введите /register",
            reply_markup=markup
        )


def process_tour_question2(message):
    """"
    Выводит рейтинг тура в виде Excel-файла
    """
    tour_number = message.text

    if tour_number == "Главное меню":
        main_menu(message)

    elif tour_number == "Выход":
        logout(message)

    else:
        points_tournament_rating(
            message,
            tour_number
        )


@bot.message_handler(func=lambda message: 'Рейтинг (туры, турнир)' in message.text or message.text == '/tournams_stat')
def tours_output2(message):
    """"
    Выводит рейтинг всех туров сразу в виде Excel-файла
    """
    is_AttributeError = False
    uid = message.from_user.id
    user_auth_data = Authorization.objects.filter(
        telegram_id=uid
    )

    try:
        custom_user = CustomUser.objects.get(
            username_id=user_auth_data.first().id
        )
    except AttributeError as e:
        is_AttributeError = True

    if user_auth_data.exists() and not is_AttributeError:
        if custom_user.is_authorized:

            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_main_menu = types.KeyboardButton(
                text='Главное меню'
            )

            btn_logout = types.KeyboardButton(
                text='Выход'
            )

            markup.add(
                btn_main_menu,
                btn_logout
            )

            tours = Tournament.objects.all().values_list(
                'id',
                flat=True
            ).distinct()

            if tours.exists():
                bot.reply_to(
                     message,
                    'Вывожу результаты туров',
                    reply_markup=markup
                )

                for tour in tours:
                    points_tournament_rating(
                        message,
                        tour_number=tour
                    )

            else:
                bot.reply_to(
                    message,
                    "Нет туров для получения статистики"
                )

        else:
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_register = types.KeyboardButton(
                text='Регистрация'
            )

            btn_login = types.KeyboardButton(
                text='Авторизация'
            )

            btn_password = types.KeyboardButton(
                text='Забыл пароль'
            )

            mon_btn = types.KeyboardButton(
                text='пн'
            )

            tue_btn = types.KeyboardButton(
                text='вт'
            )

            wed_btn = types.KeyboardButton(
                text='ср'
            )

            thu_btn = types.KeyboardButton(
                text='чт'
            )

            fri_btn = types.KeyboardButton(
                text='пт'
            )

            sat_btn = types.KeyboardButton(
                text='сб'
            )

            sun_btn = types.KeyboardButton(
                text='вс'
            )

            markup.add(
                mon_btn,
                tue_btn,
                wed_btn,
                thu_btn,
                fri_btn,
                sat_btn,
                sun_btn,
                btn_register,
                btn_login,
                btn_password
            )

            bot.reply_to(
                message,
                "Вы не авторизованы. Для авторизации введите /login",
                reply_markup=markup,
            )

    else:
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        btn_register = types.KeyboardButton(
            text='Регистрация'
        )

        btn_login = types.KeyboardButton(
            text='Авторизация'
        )

        btn_password = types.KeyboardButton(
            text='Забыл пароль'
        )

        mon_btn = types.KeyboardButton(
            text='пн'
        )

        tue_btn = types.KeyboardButton(
            text='вт'
        )

        wed_btn = types.KeyboardButton(
            text='ср'
        )

        thu_btn = types.KeyboardButton(
            text='чт'
        )

        fri_btn = types.KeyboardButton(
            text='пт'
        )

        sat_btn = types.KeyboardButton(
            text='сб'
        )

        sun_btn = types.KeyboardButton(
            text='вс'
        )

        markup.add(
            mon_btn,
            tue_btn,
            wed_btn,
            thu_btn,
            fri_btn,
            sat_btn,
            sun_btn,
            btn_register,
            btn_login,
            btn_password
        )

        bot.reply_to(
            message,
            "Вы не зарегистрированы. Для регистрации введите /register",
            reply_markup=markup,
        )


@bot.message_handler(func=lambda message: 'Начать викторину' in message.text or message.text == '/start_quiz')
def tour_question(message):
    """
    Запускает викторину
    """
    questions = Question.objects.all()

    if questions.exists():
        tours = questions.values_list(
            'tour_id',
            flat=True
        ).distinct()

        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        for tour in tours:
            markup.add(types.KeyboardButton(
                text=str(tour)
                )
            )

        reply = bot.reply_to(
            message,
            'Выберите тур для начала викторины:',
            reply_markup=markup,
        )

        bot.register_next_step_handler(
            reply,
            start_quiz,
            tours=[str(tour) for tour in tours],
        )

    else:
        bot.reply_to(
            message,
            "Нет доступных туров для викторины"
        )


def start_quiz(message, tours, question_number=None, tour_id=None, question_id=None):
    """"
    Начинает викторину или продолжает ее в зависимости от question_number
    question_number - номер вопроса в турнире (ID из таблицы Question)
    """

    is_AttributeError = False
    is_tour_number = False
    is_over = False
    is_repeat = False

    uid = message.from_user.id

    if not tour_id:
        tour_input = message.text

        if tour_input in tours:
            is_tour_number = True

    else:
        if tour_id in tours:
            is_tour_number = True

    user_auth_data = Authorization.objects.filter(
        telegram_id=uid
    )

    try:
        custom_user = CustomUser.objects.get(
            username_id=user_auth_data.first().id
        )
    except AttributeError as e:
        is_AttributeError = True

    if is_tour_number:
        if user_auth_data.exists() and not is_AttributeError:
            if custom_user.is_authorized:
                if custom_user.role_id == 3:
                    markup = types.ReplyKeyboardMarkup(
                        resize_keyboard=True
                    )

                    btn_main_menu = types.KeyboardButton(
                        text='Главное меню'
                    )

                    btn_logout = types.KeyboardButton(
                        text='Выход'
                    )

                    markup.add(
                        btn_main_menu,
                        btn_logout
                    )

                    questions = Question.objects.filter(
                        tour_id=tour_input if not tour_id else tour_id
                    )

                    if questions.exists():

                        if not question_id:
                            question_ids = [
                                question.id for question in questions
                            ]
                            question_id = min(question_ids)

                        if not question_number:
                            question_number = 1

                            participant = PointsTransaction.objects.filter(
                                sender_telegram_id=message.from_user.id,
                                question_id__in=question_ids
                            )

                            if participant.exists():
                                is_done_list = participant.values_list(
                                    'is_done',
                                    flat=True
                                )

                                sum_is_done = len(
                                    is_done_list
                                )

                                if sum_is_done == questions.count():
                                    is_over = True
                                    is_repeat = True
                                    question = None

                                    markup = types.ReplyKeyboardMarkup(
                                        resize_keyboard=True
                                    )

                                    btn_main_menu = types.KeyboardButton(
                                        text='Главное меню'
                                    )

                                    btn_logout = types.KeyboardButton(
                                        text='Выход'
                                    )

                                    markup.add(
                                        btn_main_menu,
                                        btn_logout
                                    )

                                    bot.reply_to(
                                        message,
                                        'Викторина уже завершена',
                                        reply_markup=markup,
                                    )

                            else:
                                bot.reply_to(
                                    message,
                                    'Начинаем викторину'
                                )

                            if not is_over:
                                question = Question.objects.filter(
                                    tour_question_number_id=question_number,
                                    tour_id=tour_input if not tour_id else tour_id
                                )

                        else:
                            question = Question.objects.filter(
                                tour_question_number_id=question_number,
                                tour_id=tour_input if not tour_id else tour_id
                            )

                    else:
                        question = None

                        bot.reply_to(
                            message,
                            'Нет вопросов для викторины'
                        )

                    if question:
                        tour = question.first().tour_id
                        tour_question_number_id = question.first().tour_question_number_id
                        question_text = question.first().question_text
                        answer_explanation = question.first().explanation

                        answer_dict = {
                            'A': question.first().answer_a,
                            'B': question.first().answer_b,
                            'C': question.first().answer_c,
                            'D': question.first().answer_d,
                        }

                        correct_answer = answer_dict.get(question.first().correct_answer)

                        participant = PointsTransaction.objects.filter(
                            sender_telegram_id=message.from_user.id,
                            question_id=question_number,
                        )

                        if not participant.exists() or participant.first().is_done == 0:
                            bot.reply_to(
                                message,
                                text=f"### Тур № {tour} ### Вопрос № {tour_question_number_id} ###",
                            )

                        markup = types.ReplyKeyboardMarkup(row_width=2)
                        for option in list(answer_dict.values()):
                            button = types.KeyboardButton(option)
                            markup.add(button)

                        bot.send_message(
                            message.chat.id,
                            text=question_text,
                            reply_markup=markup,
                        )

                        image_path = ""

                        try:
                            image_path += str(question.first().image.path)
                        except ValueError:
                            pass

                        if image_path:
                            try:
                                with open(image_path, 'rb') as photo:
                                    bot.send_photo(chat_id=message.chat.id, photo=photo)
                            except Exception as e:
                                print(f"Ошибка при отправке фото: {e}")

                        try:
                            bot.register_next_step_handler(
                                message,
                                handle_answer,
                                correct_answer=correct_answer,
                                question_number=question_number,
                                answer_explanation=answer_explanation,
                                tours=tours,
                                tour_id=tour_input if not tour_id else tour_id,
                                question_id=question_id
                            )
                        except TypeError:
                            pass

                    else:
                        if not is_repeat:
                            markup = types.ReplyKeyboardMarkup(
                                resize_keyboard=True
                            )

                            btn_main_menu = types.KeyboardButton(
                                text='Главное меню'
                            )

                            btn_logout = types.KeyboardButton(
                                text='Выход'
                            )

                            markup.add(
                                btn_main_menu,
                                btn_logout
                            )

                            bot.reply_to(
                                message,
                                "На этом викторина тура окончена",
                                reply_markup=markup,
                            )

                else:
                    bot.reply_to(
                        message,
                        "Вы не являетесь участником турнира"
                    )

            else:
                markup = types.ReplyKeyboardMarkup(
                    resize_keyboard=True
                )

                btn_register = types.KeyboardButton(
                    text='Регистрация'
                )

                btn_login = types.KeyboardButton(
                    text='Авторизация'
                )

                btn_password = types.KeyboardButton(
                    text='Забыл пароль'
                )

                user_auth = Authorization.objects.filter(
                    telegram_id=message.from_user.id
                )

                if user_auth.exists():
                    user_id = user_auth.first().id
                    custom_user = CustomUser.objects.filter(id=user_id).first()

                    mon_btn = types.KeyboardButton(
                        text='пн'
                    )

                    tue_btn = types.KeyboardButton(
                        text='вт'
                    )

                    wed_btn = types.KeyboardButton(
                        text='ср'
                    )

                    thu_btn = types.KeyboardButton(
                        text='чт'
                    )

                    fri_btn = types.KeyboardButton(
                        text='пт'
                    )

                    sat_btn = types.KeyboardButton(
                        text='сб'
                    )

                    sun_btn = types.KeyboardButton(
                        text='вс'
                    )

                    if custom_user.role_id in [1, 2]:
                        markup.add(
                            mon_btn,
                            tue_btn,
                            wed_btn,
                            thu_btn,
                            fri_btn,
                            sat_btn,
                            sun_btn
                        )

                markup.add(
                    btn_register,
                    btn_login,
                    btn_password
                )

                bot.reply_to(
                    message,
                    "Вы не авторизованы. Для авторизации введите /login",
                    reply_markup=markup,
                )

        else:
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            btn_register = types.KeyboardButton(
                text='Регистрация'
            )

            btn_login = types.KeyboardButton(
                text='Авторизация'
            )

            btn_password = types.KeyboardButton(
                text='Забыл пароль'
            )

            mon_btn = types.KeyboardButton(
                text='пн'
            )

            tue_btn = types.KeyboardButton(
                text='вт'
            )

            wed_btn = types.KeyboardButton(
                text='ср'
            )

            thu_btn = types.KeyboardButton(
                text='чт'
            )

            fri_btn = types.KeyboardButton(
                text='пт'
            )

            sat_btn = types.KeyboardButton(
                text='сб'
            )

            sun_btn = types.KeyboardButton(
                text='вс'
            )

            markup.add(
                mon_btn,
                tue_btn,
                wed_btn,
                thu_btn,
                fri_btn,
                sat_btn,
                sun_btn,
                btn_register,
                btn_login,
                btn_password
            )

            bot.reply_to(
                message,
                "Вы не зарегистрированы. Для регистрации введите /register",
                reply_markup=markup
            )

    else:
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        btn_main_menu = types.KeyboardButton(
            text='Главное меню'
        )

        btn_logout = types.KeyboardButton(
            text='Выход'
        )

        markup.add(
            btn_main_menu,
            btn_logout
        )

        bot.reply_to(
            message,
            "Тур завершен",
            reply_markup=markup,
        )


@bot.message_handler(func=lambda message: True)
def handle_answer(message, correct_answer=None, answer_explanation=None, question_number=None, tours=None, tour_id=None, question_id=None):
    """"
    Фиксирует ответ участника и переходит к следующему вопросу, если он есть
    """
    uid = message.from_user.id
    correct_text = True

    participant = PointsTransaction.objects.filter(
        sender_telegram_id=uid,
        question_id=question_id,
    )

    if message.text == 'Главное меню':
        main_menu(message)
        correct_text = False

    elif message.text == 'Назад к регистрации':
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        btn_register = types.KeyboardButton(
            text='Регистрация'
        )

        btn_login = types.KeyboardButton(
            text='Авторизация'
        )

        btn_password = types.KeyboardButton(
            text='Забыл пароль'
        )

        mon_btn = types.KeyboardButton(
            text='пн'
        )

        tue_btn = types.KeyboardButton(
            text='вт'
        )

        wed_btn = types.KeyboardButton(
            text='ср'
        )

        thu_btn = types.KeyboardButton(
            text='чт'
        )

        fri_btn = types.KeyboardButton(
            text='пт'
        )

        sat_btn = types.KeyboardButton(
            text='сб'
        )

        sun_btn = types.KeyboardButton(
            text='вс'
        )

        markup.add(
            mon_btn,
            tue_btn,
            wed_btn,
            thu_btn,
            fri_btn,
            sat_btn,
            sun_btn,
            btn_register,
            btn_login,
            btn_password
        )

        bot.send_message(
            chat_id=message.chat.id,
            text="Меню регистрации",
            reply_markup=markup
        )

        correct_text = False

    elif message.text == 'Выход':
        logout(message)
        correct_text = False

    if correct_text:
        if message.text == correct_answer:
            bot.send_message(
                message.chat.id,
                f"Верно! \n{answer_explanation}", reply_markup=types.ReplyKeyboardRemove()
            )

            if not participant.exists():
                PointsTransaction.objects.create(
                    sender_telegram_id=uid,
                    question_id=question_id,
                    is_answered=1,
                    is_done=1,
                )

            else:
                if participant.first().is_done == 0:
                    PointsTransaction.objects.filter(
                        sender_telegram_id=uid,
                        question_id=question_id,
                    ).update(
                        is_answered=1,
                        is_done=1,
                    )

            start_quiz(
                message,
                tours=tours,
                tour_id=tour_id,
                question_number=question_number+1,
                question_id=question_id+1
            )

        else:
            if correct_answer:
                bot.send_message(
                    message.chat.id,
                    f"Неверно! \n{answer_explanation}", reply_markup=types.ReplyKeyboardRemove()
                )

                if not participant.exists():
                    PointsTransaction.objects.create(
                        sender_telegram_id=uid,
                        question_id=question_id,
                        is_answered=0,
                        is_done=1,
                    )

                else:
                    PointsTransaction.objects.filter(
                        sender_telegram_id=uid,
                        question_id=question_id,
                    ).update(
                        is_answered=0,
                        is_done=1,
                    )

                start_quiz(
                    message,
                    tours=tours,
                    tour_id=tour_id,
                    question_number=question_number+1,
                    question_id=question_id + 1
                )

            else:
                markup = types.ReplyKeyboardMarkup(
                    resize_keyboard=True
                )

                btn_main_menu = types.KeyboardButton(
                    text='Главное меню'
                )

                btn_logout = types.KeyboardButton(
                    text='Выход'
                )

                markup.add(
                    btn_main_menu,
                    btn_logout
                )

                bot.reply_to(
                    message,
                    "Некорректный ввод информации. Пожалуйста, вернитесь в главное меню",
                    reply_markup=markup,
                )


if __name__ == "__main__":
    bot.polling()
