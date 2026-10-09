"""Per-customer settings layered over the system-wide SystemSetting.

A customer admin edits the CustomerSetting row of its ERP customer ID. Users who share
that ID see those values; any field left empty falls back to the super admin's value.
"""
from types import SimpleNamespace

from app import db
from app.access import group_ids, is_super_admin
from app.models.models import CustomerSetting, SystemSetting

BRANDING_FIELDS = ('theme_color', 'logo_path', 'company_name', 'company_address', 'company_phone',
                   'default_layout', 'typography', 'terms_conditions_url', 'incoterm_rules', 'door_countries')
SMTP_FIELDS = ('smtp_server', 'smtp_port', 'smtp_user', 'smtp_sender_name', 'smtp_password')
SYSTEM_ONLY_FIELDS = ('login_banner_path',)  # the sign-in page is shown before we know the customer


def system_settings():
    s = SystemSetting.query.first()
    if not s:
        s = SystemSetting(theme_color='blue', logo_path='img/logo.png', default_layout='sidebar', typography='Inter')
        db.session.add(s)
        db.session.commit()
    return s


def customer_setting_for(user, create=False):
    """The CustomerSetting row that applies to `user`, or None.

    Uses the first of the user's customer IDs that has a row; with create=True a row is
    made for the user's first customer ID. Super admins never have one.
    """
    if user is None or not getattr(user, 'is_authenticated', False) or is_super_admin(user):
        return None
    ids = sorted(group_ids(user))
    if not ids:
        return None
    rows = {r.group_id: r for r in CustomerSetting.query.filter(CustomerSetting.group_id.in_(ids)).all()}
    for gid in ids:
        if gid in rows:
            return rows[gid]
    if create:
        row = CustomerSetting(group_id=ids[0])
        db.session.add(row)
        db.session.flush()
        return row
    return None


def effective_settings(user):
    """System settings with the user's customer overrides applied.

    Mail settings are taken as a block: a customer's own SMTP server is only used
    together with its own credentials, never mixed with the system's.
    """
    base = system_settings()
    merged = {c.name: getattr(base, c.name) for c in SystemSetting.__table__.columns}
    row = customer_setting_for(user)
    if row is not None:
        for field in BRANDING_FIELDS:
            value = getattr(row, field)
            if value not in (None, ''):
                merged[field] = value
        if row.smtp_server:
            for field in SMTP_FIELDS:
                merged[field] = getattr(row, field)
            merged['smtp_port'] = row.smtp_port or 587
        if row.receiver_email:
            merged['receiver_email'] = row.receiver_email
    merged['customer_group_id'] = row.group_id if row is not None else None
    return SimpleNamespace(**merged)
