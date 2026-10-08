"""Role hierarchy and data scoping.

super_admin     -> everything
customer_admin  -> back-office pages, limited to users who share one of its ERP customer IDs
customer        -> own data only
"""
from app import db
from app.models.models import User, Booking, UserAccountMapping

SUPER_ADMIN = 'super_admin'
CUSTOMER_ADMIN = 'customer_admin'
CUSTOMER = 'customer'
STAFF_ROLES = (SUPER_ADMIN, CUSTOMER_ADMIN)
ALL_ROLES = (SUPER_ADMIN, CUSTOMER_ADMIN, CUSTOMER)

# A customer admin manages users who share one of its ERP customer IDs
# (user_account_mapping.account_id). To group by ERP branch instead, point these
# at UserBranchMapping / UserBranchMapping.branch_id / 'branches'.
GroupMapping = UserAccountMapping
GROUP_KEY = UserAccountMapping.account_id


def is_staff(user):
    return user.is_authenticated and user.role in STAFF_ROLES


def is_super_admin(user):
    return user.is_authenticated and user.role == SUPER_ADMIN


def group_ids(user):
    """ERP customer IDs the user belongs to."""
    return [row[0] for row in db.session.query(GROUP_KEY).filter(GroupMapping.user_id == user.id).all()]


def scoped_user_ids_query(user):
    """Subquery of user ids visible to `user`, or None for unrestricted."""
    if is_super_admin(user):
        return None
    ids = group_ids(user)
    if not ids:
        return db.session.query(User.id).filter(User.id == user.id)
    return db.session.query(GroupMapping.user_id).filter(GROUP_KEY.in_(ids))


def scope_users(query, user):
    sub = scoped_user_ids_query(user)
    return query if sub is None else query.filter(User.id.in_(sub))


def scope_bookings(query, user):
    sub = scoped_user_ids_query(user)
    return query if sub is None else query.filter(Booking.user_id.in_(sub))


def can_access_user(user, target):
    if is_super_admin(user) or target.id == user.id:
        return True
    return bool(set(group_ids(user)) & set(group_ids(target)))


def can_access_booking(user, booking):
    if booking is None:
        return False
    if booking.user_id == user.id or is_super_admin(user):
        return True
    return user.role == CUSTOMER_ADMIN and can_access_user(user, booking.customer)
