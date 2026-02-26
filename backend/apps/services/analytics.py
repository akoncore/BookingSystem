"""
AnalyticsService — сервис аналитики и статистики.

Отвечает исключительно за бизнес-логику расчётов.
Не содержит HTTP-логики — только работа с Django ORM.
Используется из AnalyticsViewSet.

Комиссионные ставки:
    Мастер получает 70% от суммы каждого завершённого бронирования.
    Салон получает 30% как комиссию за площадку.
"""

from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q


class AnalyticsService:
    """
    Сервис аналитики — все расчёты статистики и отчётов.

    Методы:
        get_top_masters()        — топ мастеров по количеству бронирований
        get_top_services()       — топ услуг по количеству заказов
        get_revenue_statistics() — общая и дневная статистика выручки
        get_salon_performance()  — KPI салона за период
        get_master_earnings()    — заработок конкретного мастера
        get_dashboard_summary()  — персональный дашборд по роли пользователя
    """

    # Доля мастера от суммы бронирования — 70%
    MASTER_SHARE = 0.70

    # Доля салона от суммы бронирования — 30%
    SALON_SHARE = 0.30

    @staticmethod
    def get_top_masters(salon_id=None, limit=10, period_days=30):
        """
        Возвращает рейтинг мастеров по количеству завершённых бронирований.

        Для каждого мастера рассчитывается:
        - общее число завершённых бронирований за период
        - суммарная выручка
        - заработок мастера (70%) и доля салона (30%)

        Args:
            salon_id (int|None): ID салона для фильтрации. None — все салоны.
            limit (int): Максимальное количество мастеров в топе. По умолчанию 10.
            period_days (int): Глубина анализа в днях. По умолчанию 30.

        Returns:
            list[dict]: Список мастеров со статистикой, отсортированный по убыванию.
        """
        # Импорт внутри метода — избегаем циклических зависимостей при старте Django
        from apps.main.models import Booking

        # Дата начала анализируемого периода
        date_from = timezone.now().date() - timedelta(days=period_days)

        # Базовый queryset — только завершённые бронирования за нужный период
        queryset = Booking.objects.filter(
            status='completed',
            appointment_date__gte=date_from,
        )

        # Если передан salon_id — показываем топ только по этому салону
        if salon_id:
            queryset = queryset.filter(salon_id=salon_id)

        # Группируем по мастеру, считаем количество записей и суммарную выручку
        top = (
            queryset
            .values('master__id', 'master__full_name', 'master__email')
            .annotate(
                total_bookings=Count('id'),        # количество выполненных записей
                total_revenue=Sum('total_price'),  # общая сумма по этим записям
            )
            .order_by('-total_bookings')[:limit]   # топ N по убыванию записей
        )

        # Строим итоговый список с расчётом долей мастера и салона
        result = []
        for item in top:
            revenue = float(item['total_revenue'] or 0)
            result.append({
                'master_id': item['master__id'],
                'master_name': item['master__full_name'],
                'email': item['master__email'],
                'total_bookings': item['total_bookings'],
                'total_revenue_kzt': revenue,
                # Сколько заработал мастер лично (70% от выручки)
                'master_earnings_kzt': round(revenue * AnalyticsService.MASTER_SHARE, 2),
                # Сколько получил салон как комиссию (30% от выручки)
                'salon_share_kzt': round(revenue * AnalyticsService.SALON_SHARE, 2),
            })

        return result

    @staticmethod
    def get_top_services(salon_id=None, limit=10, period_days=30):
        """
        Возвращает рейтинг услуг по количеству заказов за период.

        Подсчёт ведётся через ManyToMany-связь Booking → Service.
        Учитываются только завершённые бронирования — реально оказанные услуги.

        Args:
            salon_id (int|None): ID салона для фильтрации. None — все салоны.
            limit (int): Максимальное количество услуг в топе. По умолчанию 10.
            period_days (int): Глубина анализа в днях. По умолчанию 30.

        Returns:
            list[dict]: Список услуг со статистикой, отсортированный по убыванию заказов.
        """
        from apps.main.models import Booking

        # Дата начала периода
        date_from = timezone.now().date() - timedelta(days=period_days)

        # Только завершённые бронирования — услуга действительно была оказана
        queryset = Booking.objects.filter(
            status='completed',
            appointment_date__gte=date_from,
        )

        # Фильтр по салону, если передан
        if salon_id:
            queryset = queryset.filter(salon_id=salon_id)

        # Разворачиваем M2M-связь booking → services и группируем по услуге
        top = (
            queryset
            .values('services__id', 'services__name', 'services__price')
            .annotate(order_count=Count('id'))     # сколько раз услуга была заказана
            .order_by('-order_count')[:limit]
        )

        return [
            {
                'service_id': item['services__id'],
                'service_name': item['services__name'],
                'price_kzt': item['services__price'],
                'order_count': item['order_count'],
                # Примерная выручка по услуге: цена × количество заказов
                'total_revenue_kzt': round(
                    float(item['services__price'] or 0) * item['order_count'], 2
                ),
            }
            for item in top
            if item['services__id']  # исключаем NULL-строки, возникающие при LEFT JOIN
        ]

    @staticmethod
    def get_revenue_statistics(salon_id=None, period_days=30):
        """
        Возвращает общую и дневную статистику выручки за период.

        Ответ содержит:
        - сводку (total, avg_check, доли мастера и салона)
        - разбивку по каждому дню периода для построения графика

        Args:
            salon_id (int|None): ID салона для фильтрации. None — все салоны.
            period_days (int): Глубина анализа в днях. По умолчанию 30.

        Returns:
            dict: Сводка и дневная разбивка выручки с долями.
        """
        from apps.main.models import Booking

        # Начало анализируемого периода
        date_from = timezone.now().date() - timedelta(days=period_days)

        # Только завершённые бронирования — фактически полученная выручка
        queryset = Booking.objects.filter(
            status='completed',
            appointment_date__gte=date_from,
        )

        # Фильтр по конкретному салону, если указан
        if salon_id:
            queryset = queryset.filter(salon_id=salon_id)

        # Агрегируем итоговые показатели за весь период одним запросом
        totals = queryset.aggregate(
            total_revenue=Sum('total_price'),   # общая выручка за период
            total_bookings=Count('id'),         # количество выполненных бронирований
            avg_check=Avg('total_price'),       # средний чек одного бронирования
        )

        total_revenue = float(totals['total_revenue'] or 0)

        # Группируем по дате — для отображения динамики на графике
        daily = (
            queryset
            .values('appointment_date')
            .annotate(
                bookings=Count('id'),
                revenue=Sum('total_price'),
            )
            .order_by('appointment_date')   # хронологический порядок для графика
        )

        # Формируем дневную разбивку с расчётом долей для каждого дня
        daily_breakdown = [
            {
                'date': str(item['appointment_date']),
                'bookings': item['bookings'],
                'revenue_kzt': float(item['revenue'] or 0),
                # Суммарный заработок мастеров за этот день
                'master_earnings_kzt': round(
                    float(item['revenue'] or 0) * AnalyticsService.MASTER_SHARE, 2
                ),
                # Доход салона за этот день
                'salon_share_kzt': round(
                    float(item['revenue'] or 0) * AnalyticsService.SALON_SHARE, 2
                ),
            }
            for item in daily
        ]

        return {
            'period_days': period_days,
            'date_from': str(date_from),
            'date_to': str(timezone.now().date()),
            'summary': {
                'total_revenue_kzt': total_revenue,
                'total_bookings': totals['total_bookings'] or 0,
                'avg_check_kzt': round(float(totals['avg_check'] or 0), 2),
                # Суммарный заработок всех мастеров за период
                'master_earnings_kzt': round(total_revenue * AnalyticsService.MASTER_SHARE, 2),
                # Суммарный доход салона за период
                'salon_share_kzt': round(total_revenue * AnalyticsService.SALON_SHARE, 2),
            },
            'daily_breakdown': daily_breakdown,
        }

    @staticmethod
    def get_salon_performance(salon_id, period_days=30):
        """
        Возвращает KPI-показатели работы конкретного салона за период.

        Включает:
        - статистику бронирований (всего, завершено, отменено, в ожидании)
        - финансовые показатели (выручка, средний чек, доли мастеров и салона)
        - процентные показатели (конверсия и процент отмен)

        Args:
            salon_id (int): ID салона (обязательно).
            period_days (int): Глубина анализа в днях. По умолчанию 30.

        Returns:
            dict: KPI и показатели производительности салона.
                  При отсутствии салона — {'error': 'Salon not found'}.
        """
        from apps.main.models import Booking, Salon

        # Начало анализируемого периода
        date_from = timezone.now().date() - timedelta(days=period_days)

        # Проверяем, существует ли такой салон в базе
        try:
            salon = Salon.objects.get(id=salon_id)
        except Salon.DoesNotExist:
            return {'error': 'Salon not found'}

        # Все бронирования салона за период — включая все статусы
        all_bookings = Booking.objects.filter(
            salon_id=salon_id,
            appointment_date__gte=date_from,
        )

        # Подзапросы по статусам для подсчёта каждого отдельно
        completed = all_bookings.filter(status='completed')
        cancelled = all_bookings.filter(status='cancelled')

        # Финансовые агрегаты только по завершённым — фактически заработанные деньги
        totals = completed.aggregate(
            total_revenue=Sum('total_price'),
            total_count=Count('id'),
            avg_check=Avg('total_price'),
        )

        total_count = all_bookings.count()
        completed_count = totals['total_count'] or 0
        cancelled_count = cancelled.count()
        total_revenue = float(totals['total_revenue'] or 0)

        # Конверсия: процент бронирований, которые реально завершились
        conversion_rate = round(
            (completed_count / total_count * 100) if total_count > 0 else 0, 1
        )

        # Процент отмен: насколько часто клиенты отменяют записи
        cancellation_rate = round(
            (cancelled_count / total_count * 100) if total_count > 0 else 0, 1
        )

        return {
            'salon': {'id': salon.id, 'name': salon.name},
            'period_days': period_days,
            'bookings': {
                'total': total_count,
                'completed': completed_count,
                'cancelled': cancelled_count,
                # Активные: pending + confirmed — ещё не закрытые записи
                'pending_confirmed': total_count - completed_count - cancelled_count,
            },
            'revenue': {
                'total_kzt': total_revenue,
                'avg_check_kzt': round(float(totals['avg_check'] or 0), 2),
                # Суммарный заработок всех мастеров этого салона
                'master_earnings_kzt': round(total_revenue * AnalyticsService.MASTER_SHARE, 2),
                # Чистый доход салона как площадки
                'salon_share_kzt': round(total_revenue * AnalyticsService.SALON_SHARE, 2),
            },
            'rates': {
                'conversion_rate_pct': conversion_rate,
                'cancellation_rate_pct': cancellation_rate,
            },
        }

    @staticmethod
    def get_master_earnings(master_id, period_days=30):
        """
        Возвращает детальную статистику заработка мастера (для Admin аналитики).

        Отличие от /master/my-earnings/:
        - принимает произвольный master_id (Admin анализирует любого мастера)
        - не требует, чтобы запрашивающий пользователь был самим мастером

        Args:
            master_id (int): ID пользователя с ролью 'master' (обязательно).
            period_days (int): Глубина анализа в днях. По умолчанию 30.

        Returns:
            dict: Профиль мастера, финансовая сводка и дневная разбивка заработка.
                  При отсутствии мастера — {'error': 'Master not found'}.
        """
        from apps.main.models import Booking
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Начало анализируемого периода
        date_from = timezone.now().date() - timedelta(days=period_days)

        # Ищем именно мастера — пользователь с ролью 'master'
        try:
            user = User.objects.get(id=master_id, role='master')
        except User.DoesNotExist:
            return {'error': 'Master not found'}

        # Профиль мастера (Master модель) — может отсутствовать если не подтверждён
        master_profile = getattr(user, 'master_profile', None)

        # Только завершённые бронирования — только реально заработанные деньги
        bookings = Booking.objects.filter(
            master=user,
            status='completed',
            appointment_date__gte=date_from,
        )

        # Итоговые финансовые показатели за весь период
        totals = bookings.aggregate(
            total_revenue=Sum('total_price'),
            total_bookings=Count('id'),
        )

        total_revenue = float(totals['total_revenue'] or 0)

        # Группируем по дням для построения графика динамики заработка
        daily = (
            bookings
            .values('appointment_date')
            .annotate(bookings=Count('id'), revenue=Sum('total_price'))
            .order_by('appointment_date')
        )

        return {
            'master': {
                'id': user.id,
                'full_name': user.full_name,
                'email': user.email,
                # Данные профиля мастера — None если профиль ещё не создан
                'salon': master_profile.salon.name if master_profile else None,
                'specialization': master_profile.specialization if master_profile else None,
            },
            'period_days': period_days,
            'date_from': str(date_from),
            'date_to': str(timezone.now().date()),
            'summary': {
                'total_bookings': totals['total_bookings'] or 0,
                'total_revenue_kzt': total_revenue,
                # Личный заработок мастера: 70% от всей выручки за период
                'master_earnings_kzt': round(
                    total_revenue * AnalyticsService.MASTER_SHARE, 2
                ),
                # Доля салона: 30% от всей выручки за период
                'salon_share_kzt': round(
                    total_revenue * AnalyticsService.SALON_SHARE, 2
                ),
            },
            # Дневная разбивка для фронтенд-графика
            'daily_breakdown': [
                {
                    'date': str(item['appointment_date']),
                    'bookings': item['bookings'],
                    'revenue_kzt': float(item['revenue'] or 0),
                    # Заработок мастера за конкретный день
                    'earnings_kzt': round(
                        float(item['revenue'] or 0) * AnalyticsService.MASTER_SHARE, 2
                    ),
                }
                for item in daily
            ],
        }

    @staticmethod
    def get_dashboard_summary(user):
        """
        Возвращает персональный дашборд, адаптированный под роль пользователя.

        Каждая роль получает только свои данные:
        - Admin:  KPI салонов — выручка месяца, записи сегодня
        - Master: заработок за текущий месяц, записи сегодня
        - Client: история бронирований, предстоящие записи

        Args:
            user: Текущий пользователь (request.user).

        Returns:
            dict: Данные дашборда, специфичные для роли пользователя.
        """
        from apps.main.models import Booking, Salon

        today = timezone.now().date()
        # Первый день текущего месяца — граница для месячной статистики
        month_start = today.replace(day=1)

        if user.is_admin:
            # ── Дашборд Admin ──────────────────────────────────────────────
            # Получаем все салоны этого администратора
            salons = Salon.objects.filter(owner=user)
            salon = salons.first()

            # Нет ни одного салона — подсказываем создать первый
            if not salon:
                return {'message': 'No salons found. Create a salon first.'}

            # Бронирования по всем салонам Admin
            bookings = Booking.objects.filter(salon__in=salons)

            # Только завершённые за текущий месяц — реальная выручка
            month_bookings = bookings.filter(
                appointment_date__gte=month_start, status='completed'
            )
            totals = month_bookings.aggregate(
                revenue=Sum('total_price'), count=Count('id')
            )

            return {
                'role': 'admin',
                'salons_count': salons.count(),
                'this_month': {
                    'completed_bookings': totals['count'] or 0,
                    'revenue_kzt': float(totals['revenue'] or 0),
                    # Чистый доход салона (30%) за месяц
                    'salon_share_kzt': round(
                        float(totals['revenue'] or 0) * AnalyticsService.SALON_SHARE, 2
                    ),
                },
                'today': {
                    # Все записи в салонах Admin сегодня
                    'bookings': bookings.filter(appointment_date=today).count(),
                    # Записи, ждущие подтверждения мастером
                    'pending': bookings.filter(
                        appointment_date=today, status='pending'
                    ).count(),
                },
            }

        elif user.is_master:
            # ── Дашборд Master ─────────────────────────────────────────────
            # Все бронирования к этому мастеру
            bookings = Booking.objects.filter(master=user)

            # Завершённые за текущий месяц — фактически заработанные деньги
            month_completed = bookings.filter(
                appointment_date__gte=month_start, status='completed'
            )
            totals = month_completed.aggregate(
                revenue=Sum('total_price'), count=Count('id')
            )
            revenue = float(totals['revenue'] or 0)

            return {
                'role': 'master',
                'this_month': {
                    'completed_bookings': totals['count'] or 0,
                    # Личный заработок мастера (70%) за текущий месяц
                    'my_earnings_kzt': round(
                        revenue * AnalyticsService.MASTER_SHARE, 2
                    ),
                },
                'today': {
                    # Все записи мастера сегодня
                    'bookings': bookings.filter(appointment_date=today).count(),
                    # Записи, ожидающие подтверждения от мастера
                    'pending': bookings.filter(
                        appointment_date=today, status='pending'
                    ).count(),
                },
            }

        else:
            # ── Дашборд Client ─────────────────────────────────────────────
            # Все бронирования этого клиента (история)
            bookings = Booking.objects.filter(client=user)
            return {
                'role': 'client',
                'total_bookings': bookings.count(),
                'completed': bookings.filter(status='completed').count(),
                # Предстоящие активные записи (pending или confirmed)
                'upcoming': bookings.filter(
                    appointment_date__gte=today,
                    status__in=['pending', 'confirmed'],
                ).count(),
                'cancelled': bookings.filter(status='cancelled').count(),
            }