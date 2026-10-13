from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Property, TenantBooking, OfficeApplication


class Command(BaseCommand):
    help = (
        'Cross-checks reserved properties by category (7 days for Sale properties, '
        '24 hours for Rental properties, 2 days for Offices) and releases expired reservations at midnight EAT'
    )

    def handle(self, *args, **options):
        now = timezone.now()
        self.stdout.write(f"[{now.strftime('%Y-%m-%d %H:%M:%S %Z')}] Starting Category-Aware Reserved Properties Audit...")

        expired_bookings_count = 0
        active_holds_count = 0
        released_properties_count = 0

        # -------------------------------------------------------------
        # 1. Audit Active & Reserved TenantBookings
        # -------------------------------------------------------------
        active_bookings = TenantBooking.objects.filter(
            status__in=['active', 'reserved']
        ).select_related('property')

        affected_properties = set()

        for booking in active_bookings:
            prop = booking.property
            if not prop:
                continue

            # Determine reservation category and duration
            # Sale properties: 7 days (168 hours)
            # Rental properties: 24 hours (1 day)
            is_sale = prop.is_for_sale or prop.listing_type == 'sale'
            required_duration = timedelta(days=7) if is_sale else timedelta(hours=24)
            category_label = "Sale (7-Day Hold)" if is_sale else "Rental (24-Hour Hold)"

            # Determine effective expiry date
            if booking.expires_at:
                expiry_time = booking.expires_at
            elif booking.booked_at:
                expiry_time = booking.booked_at + required_duration
            else:
                expiry_time = now  # Fallback only if no booking date exists

            # Exact date/time math
            if now < expiry_time:
                # Still within the valid reservation window - DO NOT CLEAR!
                remaining = expiry_time - now
                hours_left = int(remaining.total_seconds() // 3600)
                days_left = hours_left // 24
                rem_hours = hours_left % 24
                active_holds_count += 1
                self.stdout.write(
                    f"  [VALID HOLD] Property #{prop.id} '{prop.title}' | {category_label} | "
                    f"Booked: {booking.booked_at.strftime('%Y-%m-%d %H:%M')} | "
                    f"Remaining: {days_left}d {rem_hours}h. Hold is active."
                )
            else:
                # Reservation duration has fully elapsed
                booking.status = 'expired'
                booking.save(update_fields=['status'])
                expired_bookings_count += 1
                affected_properties.add(prop)
                self.stdout.write(
                    f"  [EXPIRED] Property #{prop.id} '{prop.title}' | {category_label} | "
                    f"Duration of {required_duration.days if is_sale else 1} day(s) elapsed on {expiry_time.strftime('%Y-%m-%d %H:%M')}."
                )

        # -------------------------------------------------------------
        # 2. Audit Corporate Office Reservations (OfficeApplication)
        # -------------------------------------------------------------
        active_offices = OfficeApplication.objects.filter(
            payment_status='paid'
        ).select_related('property')

        for app in active_offices:
            prop = app.property
            if not prop:
                continue

            # Office reservations have a 2-day (48-hour) exclusive lock
            required_duration = timedelta(days=2)
            if app.expires_at:
                expiry_time = app.expires_at
            elif hasattr(app, 'created_at') and app.created_at:
                expiry_time = app.created_at + required_duration
            else:
                expiry_time = now

            if now < expiry_time:
                remaining = expiry_time - now
                hours_left = int(remaining.total_seconds() // 3600)
                active_holds_count += 1
                self.stdout.write(
                    f"  [VALID HOLD] Corporate Office #{prop.id} '{prop.title}' ({app.company_name}) | "
                    f"Expires: {expiry_time.strftime('%Y-%m-%d %H:%M')} | Remaining: {hours_left}h."
                )
            else:
                app.payment_status = 'expired'
                app.save(update_fields=['payment_status'])
                affected_properties.add(prop)
                self.stdout.write(
                    f"  [EXPIRED] Corporate Office #{prop.id} '{prop.title}' | 2-Day Lock elapsed on {expiry_time.strftime('%Y-%m-%d %H:%M')}."
                )

        # -------------------------------------------------------------
        # 3. Clean up stale unpaid pending reservations older than 24h
        # -------------------------------------------------------------
        stale_pending = TenantBooking.objects.filter(
            status='pending_payment',
            booked_at__lte=now - timedelta(hours=24)
        )
        for p_booking in stale_pending:
            p_booking.status = 'expired'
            p_booking.save(update_fields=['status'])

        # -------------------------------------------------------------
        # 4. Release Properties Back to Available if No Active Locks
        # -------------------------------------------------------------
        locked_properties = Property.objects.filter(status__in=['under_inspection', 'reserved'])
        properties_to_evaluate = affected_properties.union(set(locked_properties))

        for prop in properties_to_evaluate:
            # Never modify rented, maintenance, or unverified properties
            if prop.status in ['rented', 'under_maintenance', 'pending_verification']:
                continue

            # Check if there is any remaining unexpired booking on this property
            has_active_tenant_booking = False
            for b in TenantBooking.objects.filter(property=prop, status__in=['active', 'reserved']):
                is_sale = prop.is_for_sale or prop.listing_type == 'sale'
                dur = timedelta(days=7) if is_sale else timedelta(hours=24)
                exp = b.expires_at or (b.booked_at + dur)
                if now < exp:
                    has_active_tenant_booking = True
                    break

            has_active_office_lock = OfficeApplication.objects.filter(
                property=prop,
                payment_status='paid',
                expires_at__gt=now
            ).exists()

            if not has_active_tenant_booking and not has_active_office_lock:
                prop.status = 'available'
                prop.save(update_fields=['status'])
                released_properties_count += 1
                self.stdout.write(
                    f"  -> Property #{prop.id} ('{prop.title}') restored to 'available' (all reservation holds completed)."
                )

        self.stdout.write(self.style.SUCCESS(
            f"\nCategory-Aware Audit Complete:\n"
            f" - Active holds retained (within valid window): {active_holds_count}\n"
            f" - Reservations legitimately expired: {expired_bookings_count}\n"
            f" - Properties restored to available: {released_properties_count}\n"
        ))
