"""
PaymentService и CancellationPolicy — сервис обработки платежей.

Отвечает за бизнес-логику финансовых расчётов:
- PaymentService: расчёт и распределение оплаты между мастером и салоном
- CancellationPolicy: проверка возможности отмены и расчёт суммы возврата

Комиссионные ставки:
    Мастер получает 70% от суммы каждого завершённого бронирования.
    Салон получает 30% как комиссию за площадку.
"""

from datetime import datetime, timedelta
from django.utils import timezone


# Доля мастера от суммы бронирования — 70%
MASTER_SHARE = 0.70

# Доля салона от суммы бронирования — 30%
SALON_SHARE = 0.30


class PaymentService:
    """
    Сервис расчёта и распределения платежей.

    Методы:
        calculate_split()    — детальный расчёт распределения оплаты по бронированию
        process_payment()    — обработка оплаты при завершении бронирования
        get_master_balance() — накопленный баланс мастера за период
        get_salon_balance()  — доходы салона с разбивкой по мастерам
    """

    @staticmethod
    def calculate_split(booking):
        """
        """
        total = float(booking.total_price)

        return {
            'booking_code': booking.booking_code,
            'total_kzt': total,
            'master': {
                'id': booking.master.id,
                'full_name': booking.master.full_name,
                'share_pct': int(MASTER_SHARE * 100),              # процент мастера
                'amount_kzt': round(total * MASTER_SHARE, 2),      # сумма мастеру
            },
            'salon': {
                'id': booking.salon.id,
                'name': booking.salon.name,
                'share_pct': int(SALON_SHARE * 100),               # процент салона
                'amount_kzt': round(total * SALON_SHARE, 2),       # комиссия салона
            },
        }

    @staticmethod
    def process_payment(booking):
        """
        Обрабатывает оплату при завершении бронирования (статус → completed).

        Сейчас выполняет только расчёт распределения. При подключении
        платёжного шлюза здесь будет фактическое списание/зачисление.

        Args:
            booking: Объект бронирования в статусе 'completed'.

        Returns:
            dict: Результат обработки платежа с суммами для мастера и салона.
        """
        total = float(booking.total_price)

        return {
            'status': 'processed',
            'booking_code': booking.booking_code,
            'total_kzt': total,
            # Сумма, которую получает мастер (70%)
            'master_earnings_kzt': round(total * MASTER_SHARE, 2),
            # Комиссия, которую оставляет себе салон (30%)
            'salon_share_kzt': round(total * SALON_SHARE, 2),
        }

    @staticmethod
    def get_master_balance(master_id, period_days=30):
        """
        Возвращает накопленный баланс мастера по завершённым бронированиям.

        Включает сводку и список последних 20 транзакций для истории выплат.

        Args:
            master_id (int): ID пользователя с ролью 'master'.
            period_days (int): Период анализа в днях. По умолчанию 30.

        Returns:
            dict: Профиль мастера, финансовая сводка и список транзакций.
                  При отсутствии мастера — {'error': 'Master not found'}.
        """
        from apps.main.models import Booking
        from django.db.models import Sum, Count
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Дата начала анализируемого периода
        date_from = timezone.now().date() - timedelta(days=period_days)

        # Проверяем, что пользователь существует и имеет роль мастера
        try:
            master = User.objects.get(id=master_id, role='master')
        except User.DoesNotExist:
            return {'error': 'Master not found'}

        # Только завершённые бронирования — деньги, которые уже заработаны
        bookings = Booking.objects.filter(
            master=master,
            status='completed',
            appointment_date__gte=date_from,
        )

        # Агрегируем финансовые итоги за период
        totals = bookings.aggregate(
            total_revenue=Sum('total_price'),
            total_count=Count('id'),
        )

        total_revenue = float(totals['total_revenue'] or 0)

        # Последние 20 бронирований для отображения истории транзакций
        recent = bookings.order_by('-appointment_date', '-appointment_time')[:20]

        return {
            'master': {
                'id': master.id,
                'full_name': master.full_name,
            },
            'period_days': period_days,
            'summary': {
                'total_bookings': totals['total_count'] or 0,
                'total_revenue_kzt': total_revenue,
                # Личный заработок мастера (70%) за весь период
                'my_earnings_kzt': round(total_revenue * MASTER_SHARE, 2),
            },
            # История транзакций — для отображения в личном кабинете
            'recent_transactions': [
                {
                    'booking_code': b.booking_code,
                    'date': str(b.appointment_date),
                    'total_kzt': float(b.total_price),
                    # Сколько мастер получил с конкретного бронирования
                    'my_earnings_kzt': round(float(b.total_price) * MASTER_SHARE, 2),
                }
                for b in recent
            ],
        }

    @staticmethod
    def get_salon_balance(salon_id, period_days=30):
        """
        Возвращает доходы салона с детальной разбивкой по каждому мастеру.

        Позволяет Admin-у видеть, кто из мастеров приносит наибольшую выручку,
        и рассчитать итоговую комиссию салона за период.

        Args:
            salon_id (int): ID салона.
            period_days (int): Период анализа в днях. По умолчанию 30.

        Returns:
            dict: Сводка доходов салона и разбивка по мастерам.
                  При отсутствии салона — {'error': 'Salon not found'}.
        """
        from apps.main.models import Booking, Salon
        from django.db.models import Sum, Count

        # Дата начала анализируемого периода
        date_from = timezone.now().date() - timedelta(days=period_days)

        # Проверяем существование салона в базе
        try:
            salon = Salon.objects.get(id=salon_id)
        except Salon.DoesNotExist:
            return {'error': 'Salon not found'}

        # Все завершённые бронирования этого салона за период
        bookings = Booking.objects.filter(
            salon_id=salon_id,
            status='completed',
            appointment_date__gte=date_from,
        )

        # Общие финансовые итоги по салону
        totals = bookings.aggregate(
            total_revenue=Sum('total_price'),
            total_count=Count('id'),
        )
        total_revenue = float(totals['total_revenue'] or 0)

        # Разбивка по мастерам: кто сколько принёс выручки
        by_master = (
            bookings
            .values('master__id', 'master__full_name')
            .annotate(bookings=Count('id'), revenue=Sum('total_price'))
            .order_by('-revenue')   # сортируем по выручке — самые прибыльные первые
        )

        return {
            'salon': {'id': salon.id, 'name': salon.name},
            'period_days': period_days,
            'summary': {
                'total_bookings': totals['total_count'] or 0,
                'total_revenue_kzt': total_revenue,
                # Итоговая комиссия салона за период (30% от общей выручки)
                'salon_share_kzt': round(total_revenue * SALON_SHARE, 2),
            },
            # Разбивка по каждому мастеру — для анализа эффективности
            'by_master': [
                {
                    'master_id': item['master__id'],
                    'master_name': item['master__full_name'],
                    'bookings': item['bookings'],
                    'revenue_kzt': float(item['revenue'] or 0),
                    # Сколько заработал этот мастер (70%)
                    'master_earnings_kzt': round(
                        float(item['revenue'] or 0) * MASTER_SHARE, 2
                    ),
                    # Сколько этот мастер принёс салону (30%)
                    'salon_share_kzt': round(
                        float(item['revenue'] or 0) * SALON_SHARE, 2
                    ),
                }
                for item in by_master
            ],
        }


class CancellationPolicy:
    """
    Политика отмены бронирований.

    Правила возврата:
    - Отмена за 24 часа и более до записи → полный возврат (100%)
    - Отмена менее чем за 24 часа → возврат не производится (0%)
    - Время записи уже прошло → возврат не производится (0%)

    Методы:
        can_cancel()            — проверяет, можно ли отменить бронирование
        get_refund_amount()     — рассчитывает сумму возврата
        process_cancellation()  — выполняет отмену и возвращает результат
    """

    # Пороговое время в часах: при отмене раньше — полный возврат
    REFUND_HOURS_THRESHOLD = 24

    @staticmethod
    def can_cancel(booking):
        """
        Проверяет, допустима ли отмена данного бронирования.

        Нельзя отменить бронирование, которое уже завершено или уже отменено.

        Args:
            booking: Объект бронирования (Booking).

        Returns:
            tuple[bool, str]: (можно_ли_отменить, причина/описание).
        """
        # Завершённое бронирование — услуга уже оказана, отмена невозможна
        if booking.status == 'completed':
            return False, 'Cannot cancel a completed booking'

        # Уже отменённое бронирование — повторная отмена бессмысленна
        if booking.status == 'cancelled':
            return False, 'Booking is already cancelled'

        # Все остальные статусы (pending, confirmed) — отмена разрешена
        return True, 'Cancellation is allowed'

    @staticmethod
    def get_refund_amount(booking):
        """
        Рассчитывает сумму возврата при отмене бронирования.

        Логика возврата:
        - 24+ часа до записи → 100% возврат
        - менее 24 часов → 0% возврат
        - время уже прошло → 0% возврат

        Args:
            booking: Объект бронирования (Booking).

        Returns:
            dict: Сумма и процент возврата с объяснением причины и временем до записи.
        """
        total = float(booking.total_price)

        # Собираем дату и время записи в единый datetime-объект
        appointment_dt = datetime.combine(
            booking.appointment_date, booking.appointment_time
        )

        # Приводим к timezone-aware формату для корректного сравнения с timezone.now()
        if timezone.is_naive(appointment_dt):
            appointment_dt = timezone.make_aware(appointment_dt)

        # Сколько часов осталось до времени записи
        hours_until = (appointment_dt - timezone.now()).total_seconds() / 3600

        if hours_until >= CancellationPolicy.REFUND_HOURS_THRESHOLD:
            # Отмена заблаговременно — полный возврат средств клиенту
            return {
                'refund_amount_kzt': total,
                'refund_percent': 100,
                'reason': (
                    f'Полный возврат — до записи более '
                    f'{CancellationPolicy.REFUND_HOURS_THRESHOLD} часов'
                ),
                'hours_until_appointment': round(hours_until, 1),
            }
        elif hours_until > 0:
            # Отмена в последний момент — возврат не производится
            return {
                'refund_amount_kzt': 0,
                'refund_percent': 0,
                'reason': (
                    f'Возврат невозможен — до записи менее '
                    f'{CancellationPolicy.REFUND_HOURS_THRESHOLD} часов'
                ),
                'hours_until_appointment': round(hours_until, 1),
            }
        else:
            # Время записи уже истекло — возврат не производится
            return {
                'refund_amount_kzt': 0,
                'refund_percent': 0,
                'reason': 'Возврат невозможен — время записи уже прошло',
                'hours_until_appointment': 0,
            }

    @staticmethod
    def process_cancellation(booking, cancelled_by='client'):
        """
        Выполняет отмену бронирования и возвращает итог с суммой возврата.

        Проверяет допустимость отмены, рассчитывает возврат,
        обновляет статус бронирования на 'cancelled'.

        Args:
            booking: Объект бронирования (Booking).
            cancelled_by (str): Инициатор отмены — 'client', 'master' или 'admin'.

        Returns:
            dict: Результат отмены.
                - success=True: отмена выполнена, содержит информацию о возврате
                - success=False: отмена невозможна, содержит причину
        """
        # Сначала проверяем, можно ли вообще отменить это бронирование
        can_cancel, reason = CancellationPolicy.can_cancel(booking)
        if not can_cancel:
            return {'success': False, 'message': reason}

        # Рассчитываем сумму возврата согласно политике
        refund_info = CancellationPolicy.get_refund_amount(booking)

        # Обновляем статус бронирования в базе данных
        booking.status = 'cancelled'
        booking.save()

        return {
            'success': True,
            'message': 'Бронирование успешно отменено',
            'cancelled_by': cancelled_by,   # кто инициировал отмену
            'refund': refund_info,          # информация о возврате средств
        }