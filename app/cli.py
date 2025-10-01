import click
from flask import current_app
from flask.cli import with_appcontext

from .extensions import db
from .models import User, UserRole


@click.command("seed-admin")
@click.option("--email", required=True)
@click.option("--password", required=True)
@with_appcontext
def seed_admin(email: str, password: str):
    if User.query.filter_by(email=email.lower()).first():
        click.echo("Admin already exists")
        return
    user = User(email=email.lower(), full_name="Super Admin", role=UserRole.SUPER_ADMIN, is_active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo("Seeded super admin")
