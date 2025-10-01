"""
Logistics Management Routes
Airport pickup, housing, and medical screening management
"""
from flask import Blueprint, request, jsonify
from app import db
from app.models import LogisticsArrangement, Student, User, UserRole
from app.services.auth import login_required, role_required
from app.services.audit import AuditService
from datetime import datetime

bp = Blueprint('logistics', __name__, url_prefix='/api/logistics')

@bp.route('', methods=['GET'])
@role_required(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.LOGISTICS_TEAM)
def get_logistics_list(current_user):
    """
    Get list of logistics arrangements
    
    Query parameters:
        - status: Filter by status (pending, assigned, completed)
        - arrival_date_from: Filter by arrival date (from)
        - arrival_date_to: Filter by arrival date (to)
    """
    query = LogisticsArrangement.query
    
    # Apply filters
    status = request.args.get('status')
    if status:
        query = query.filter_by(pickup_status=status)
    
    arrival_from = request.args.get('arrival_date_from')
    if arrival_from:
        query = query.filter(LogisticsArrangement.arrival_date >= datetime.fromisoformat(arrival_from))
    
    arrival_to = request.args.get('arrival_date_to')
    if arrival_to:
        query = query.filter(LogisticsArrangement.arrival_date <= datetime.fromisoformat(arrival_to))
    
    arrangements = query.join(Student).order_by(LogisticsArrangement.arrival_date).all()
    
    result = []
    for arr in arrangements:
        data = arr.to_dict()
        data['student'] = arr.student.to_dict()
        result.append(data)
    
    return jsonify({'arrangements': result}), 200

@bp.route('/student/<int:student_id>', methods=['GET'])
@login_required
def get_student_logistics(current_user, student_id):
    """Get logistics arrangement for a student"""
    student = db.session.get(Student, student_id)
    
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    if not student.logistics:
        return jsonify({'error': 'No logistics arrangement found'}), 404
    
    return jsonify(student.logistics.to_dict()), 200

@bp.route('/student/<int:student_id>', methods=['POST'])
@role_required(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.COUNSELLOR)
def create_logistics_arrangement(current_user, student_id):
    """
    Create logistics arrangement for a student
    
    Request body:
        {
            "arrival_date": "2024-09-01T10:00:00",
            "arrival_flight": "MH123",
            "arrival_airport": "KLIA",
            "pickup_required": true,
            "housing_required": true,
            "housing_address": "123 University St",
            "housing_checkin_date": "2024-09-01",
            "medical_screening_required": true,
            "medical_appointment_date": "2024-09-05T14:00:00"
        }
    """
    student = db.session.get(Student, student_id)
    
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    if student.logistics:
        return jsonify({'error': 'Logistics arrangement already exists'}), 400
    
    data = request.get_json()
    
    arrangement = LogisticsArrangement(
        student_id=student_id,
        arrival_date=datetime.fromisoformat(data['arrival_date']) if data.get('arrival_date') else None,
        arrival_flight=data.get('arrival_flight'),
        arrival_airport=data.get('arrival_airport'),
        pickup_required=data.get('pickup_required', False),
        housing_required=data.get('housing_required', False),
        housing_address=data.get('housing_address'),
        housing_checkin_date=datetime.fromisoformat(data['housing_checkin_date']).date() if data.get('housing_checkin_date') else None,
        medical_screening_required=data.get('medical_screening_required', True),
        medical_appointment_date=datetime.fromisoformat(data['medical_appointment_date']) if data.get('medical_appointment_date') else None
    )
    
    db.session.add(arrangement)
    db.session.commit()
    
    # Log event
    AuditService.log_event(
        event_type='logistics_created',
        description=f"Logistics arrangement created for {student.full_name}",
        user_id=current_user.id,
        student_id=student_id,
        category='workflow'
    )
    
    return jsonify({
        'message': 'Logistics arrangement created successfully',
        'arrangement': arrangement.to_dict()
    }), 201

@bp.route('/<int:arrangement_id>', methods=['PUT'])
@login_required
def update_logistics_arrangement(current_user, arrangement_id):
    """Update logistics arrangement"""
    arrangement = db.session.get(LogisticsArrangement, arrangement_id)
    
    if not arrangement:
        return jsonify({'error': 'Logistics arrangement not found'}), 404
    
    data = request.get_json()
    
    # Update fields
    if 'arrival_date' in data:
        arrangement.arrival_date = datetime.fromisoformat(data['arrival_date']) if data['arrival_date'] else None
    
    if 'arrival_flight' in data:
        arrangement.arrival_flight = data['arrival_flight']
    
    if 'arrival_airport' in data:
        arrangement.arrival_airport = data['arrival_airport']
    
    if 'pickup_required' in data:
        arrangement.pickup_required = data['pickup_required']
    
    if 'pickup_status' in data:
        arrangement.pickup_status = data['pickup_status']
    
    if 'pickup_notes' in data:
        arrangement.pickup_notes = data['pickup_notes']
    
    if 'housing_required' in data:
        arrangement.housing_required = data['housing_required']
    
    if 'housing_address' in data:
        arrangement.housing_address = data['housing_address']
    
    if 'housing_checkin_date' in data:
        arrangement.housing_checkin_date = datetime.fromisoformat(data['housing_checkin_date']).date() if data['housing_checkin_date'] else None
    
    if 'housing_status' in data:
        arrangement.housing_status = data['housing_status']
    
    if 'medical_screening_required' in data:
        arrangement.medical_screening_required = data['medical_screening_required']
    
    if 'medical_appointment_date' in data:
        arrangement.medical_appointment_date = datetime.fromisoformat(data['medical_appointment_date']) if data['medical_appointment_date'] else None
    
    if 'medical_status' in data:
        arrangement.medical_status = data['medical_status']
    
    if 'medical_notes' in data:
        arrangement.medical_notes = data['medical_notes']
    
    db.session.commit()
    
    # Log event
    AuditService.log_event(
        event_type='logistics_updated',
        description=f"Logistics arrangement updated",
        user_id=current_user.id,
        student_id=arrangement.student_id,
        category='workflow'
    )
    
    return jsonify({
        'message': 'Logistics arrangement updated successfully',
        'arrangement': arrangement.to_dict()
    }), 200

@bp.route('/<int:arrangement_id>/assign-pickup', methods=['POST'])
@role_required(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.LOGISTICS_TEAM)
def assign_pickup(current_user, arrangement_id):
    """
    Assign logistics staff to airport pickup
    
    Request body:
        {
            "staff_id": 10
        }
    """
    arrangement = db.session.get(LogisticsArrangement, arrangement_id)
    
    if not arrangement:
        return jsonify({'error': 'Logistics arrangement not found'}), 404
    
    data = request.get_json()
    staff_id = data.get('staff_id')
    
    if not staff_id:
        return jsonify({'error': 'Staff ID is required'}), 400
    
    staff = db.session.get(User, staff_id)
    
    if not staff or staff.role != UserRole.LOGISTICS_TEAM:
        return jsonify({'error': 'Invalid logistics staff'}), 400
    
    arrangement.pickup_assigned_to_id = staff_id
    arrangement.pickup_status = 'assigned'
    db.session.commit()
    
    # Log event
    AuditService.log_event(
        event_type='pickup_assigned',
        description=f"Airport pickup assigned to {staff.full_name}",
        user_id=current_user.id,
        student_id=arrangement.student_id,
        category='workflow'
    )
    
    return jsonify({
        'message': 'Pickup staff assigned successfully',
        'arrangement': arrangement.to_dict()
    }), 200

@bp.route('/dashboard', methods=['GET'])
@role_required(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.LOGISTICS_TEAM)
def get_logistics_dashboard(current_user):
    """Get logistics dashboard statistics"""
    total_arrangements = LogisticsArrangement.query.count()
    
    pickup_stats = {
        'pending': LogisticsArrangement.query.filter_by(pickup_required=True, pickup_status='pending').count(),
        'assigned': LogisticsArrangement.query.filter_by(pickup_required=True, pickup_status='assigned').count(),
        'completed': LogisticsArrangement.query.filter_by(pickup_required=True, pickup_status='completed').count()
    }
    
    housing_stats = {
        'pending': LogisticsArrangement.query.filter_by(housing_required=True, housing_status='pending').count(),
        'ready': LogisticsArrangement.query.filter_by(housing_required=True, housing_status='ready').count()
    }
    
    medical_stats = {
        'pending': LogisticsArrangement.query.filter_by(medical_screening_required=True, medical_status='pending').count(),
        'scheduled': LogisticsArrangement.query.filter_by(medical_screening_required=True, medical_status='scheduled').count(),
        'completed': LogisticsArrangement.query.filter_by(medical_screening_required=True, medical_status='completed').count()
    }
    
    # Upcoming arrivals
    upcoming = LogisticsArrangement.query.filter(
        LogisticsArrangement.arrival_date >= datetime.utcnow()
    ).order_by(LogisticsArrangement.arrival_date).limit(10).all()
    
    upcoming_list = []
    for arr in upcoming:
        data = arr.to_dict()
        data['student_name'] = arr.student.full_name
        upcoming_list.append(data)
    
    return jsonify({
        'total_arrangements': total_arrangements,
        'pickup_stats': pickup_stats,
        'housing_stats': housing_stats,
        'medical_stats': medical_stats,
        'upcoming_arrivals': upcoming_list
    }), 200
