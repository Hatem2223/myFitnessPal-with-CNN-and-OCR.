"""
Database Initialization Script
Creates tables and seeds initial data
"""
from app import create_app, db
from app.models import User, UserRole, University, Student, ApplicationStage
from datetime import datetime
import os

def init_database():
    """Initialize database with tables and seed data"""
    app = create_app()
    
    with app.app_context():
        print("🔄 Creating database tables...")
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Check if data already exists
        if User.query.first():
            print("⚠️  Database already contains data. Skipping seed data.")
            return
        
        print("\n🌱 Seeding initial data...")
        
        # Create Super Admin
        super_admin = User(
            email='admin@studentcrm.com',
            full_name='System Administrator',
            role=UserRole.SUPER_ADMIN,
            phone='+60123456789'
        )
        super_admin.set_password('admin123')
        db.session.add(super_admin)
        
        # Create Department Admin
        dept_admin = User(
            email='dept.admin@studentcrm.com',
            full_name='Department Admin',
            role=UserRole.ADMIN,
            department='Engineering',
            phone='+60123456790'
        )
        dept_admin.set_password('admin123')
        db.session.add(dept_admin)
        
        # Create Counsellors
        counsellor1 = User(
            email='counsellor1@studentcrm.com',
            full_name='Sarah Johnson',
            role=UserRole.COUNSELLOR,
            department='Engineering',
            phone='+60123456791'
        )
        counsellor1.set_password('counsellor123')
        db.session.add(counsellor1)
        
        counsellor2 = User(
            email='counsellor2@studentcrm.com',
            full_name='Ahmad Rahman',
            role=UserRole.COUNSELLOR,
            department='Business',
            phone='+60123456792'
        )
        counsellor2.set_password('counsellor123')
        db.session.add(counsellor2)
        
        # Create Logistics Staff
        logistics = User(
            email='logistics@studentcrm.com',
            full_name='Logistics Coordinator',
            role=UserRole.LOGISTICS_TEAM,
            phone='+60123456793'
        )
        logistics.set_password('logistics123')
        db.session.add(logistics)
        
        # Create Universities
        universities = [
            University(
                name='University of Malaya',
                code='UM',
                location='Kuala Lumpur',
                contact_email='admissions@um.edu.my',
                contact_phone='+60379676000'
            ),
            University(
                name='Universiti Teknologi Malaysia',
                code='UTM',
                location='Johor Bahru',
                contact_email='admission@utm.my',
                contact_phone='+60755321010'
            ),
            University(
                name='Universiti Kebangsaan Malaysia',
                code='UKM',
                location='Bangi, Selangor',
                contact_email='admission@ukm.edu.my',
                contact_phone='+60389216000'
            ),
            University(
                name='Universiti Putra Malaysia',
                code='UPM',
                location='Serdang, Selangor',
                contact_email='admission@upm.edu.my',
                contact_phone='+60397691000'
            )
        ]
        
        for uni in universities:
            db.session.add(uni)
        
        db.session.commit()
        
        # Create University Staff
        uni_staff = User(
            email='uni.staff@um.edu.my',
            full_name='University Staff',
            role=UserRole.UNIVERSITY_STAFF,
            university_id=1,
            phone='+60123456794'
        )
        uni_staff.set_password('university123')
        db.session.add(uni_staff)
        
        # Create Sample Students
        students_data = [
            {
                'full_name': 'Ali bin Mohamed',
                'email': 'ali.mohamed@email.com',
                'nationality': 'Malaysia',
                'phone': '+60123000001',
                'department': 'Engineering',
                'current_stage': ApplicationStage.DOCUMENTS_COLLECTION
            },
            {
                'full_name': 'Wei Chen',
                'email': 'wei.chen@email.com',
                'nationality': 'China',
                'phone': '+86138000001',
                'department': 'Engineering',
                'current_stage': ApplicationStage.APPLICATION_SUBMITTED
            },
            {
                'full_name': 'Priya Sharma',
                'email': 'priya.sharma@email.com',
                'nationality': 'India',
                'phone': '+91987654321',
                'department': 'Business',
                'current_stage': ApplicationStage.OFFER_RECEIVED
            },
            {
                'full_name': 'Ahmed Al-Rashid',
                'email': 'ahmed.rashid@email.com',
                'nationality': 'Saudi Arabia',
                'phone': '+966500000001',
                'department': 'Engineering',
                'current_stage': ApplicationStage.VISA_PROCESSING
            },
            {
                'full_name': 'Maria Santos',
                'email': 'maria.santos@email.com',
                'nationality': 'Philippines',
                'phone': '+63917000001',
                'department': 'Business',
                'current_stage': ApplicationStage.INQUIRY
            }
        ]
        
        for i, student_data in enumerate(students_data, start=1):
            student = Student(
                student_number=f'STU2024{str(i).zfill(6)}',
                full_name=student_data['full_name'],
                email=student_data['email'],
                nationality=student_data['nationality'],
                phone=student_data['phone'],
                department=student_data['department'],
                current_stage=student_data['current_stage'],
                created_by_id=counsellor1.id if student_data['department'] == 'Engineering' else counsellor2.id
            )
            db.session.add(student)
            
            # Assign to counsellor
            if student_data['department'] == 'Engineering':
                student.assigned_counsellors.append(counsellor1)
            else:
                student.assigned_counsellors.append(counsellor2)
        
        db.session.commit()
        
        print("\n✅ Database initialization complete!")
        print("\n" + "="*60)
        print("📋 Default Credentials:")
        print("="*60)
        print("\n🔐 Super Admin:")
        print("   Email: admin@studentcrm.com")
        print("   Password: admin123")
        print("\n🔐 Department Admin:")
        print("   Email: dept.admin@studentcrm.com")
        print("   Password: admin123")
        print("\n🔐 Counsellor:")
        print("   Email: counsellor1@studentcrm.com")
        print("   Password: counsellor123")
        print("\n🔐 Logistics Staff:")
        print("   Email: logistics@studentcrm.com")
        print("   Password: logistics123")
        print("\n🔐 University Staff:")
        print("   Email: uni.staff@um.edu.my")
        print("   Password: university123")
        print("\n" + "="*60)
        print(f"\n✨ Created {len(students_data)} sample students")
        print(f"✨ Created {len(universities)} partner universities")
        print("\n🚀 You can now run the application with: python run.py")
        print("="*60 + "\n")

if __name__ == '__main__':
    init_database()
