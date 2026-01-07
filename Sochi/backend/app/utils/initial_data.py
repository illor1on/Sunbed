from app.models import Role

def create_initial_roles():
    roles = [
        {'name': 'admin', 'description': 'Администратор системы'},
        {'name': 'owner', 'description': 'Владелец пляжа'},
        {'name': 'user', 'description': 'Клиент'}
    ]
    
    for role_data in roles:
        role = Role.query.filter_by(name=role_data['name']).first()
        if not role:
            role = Role(**role_data)
            db.session.add(role)
    
    db.session.commit()