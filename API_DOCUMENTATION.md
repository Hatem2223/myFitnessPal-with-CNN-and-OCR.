# Student CRM System - API Documentation

## Overview

This document provides comprehensive API documentation for the Student Registration CRM System. All endpoints use JSON for request and response bodies unless otherwise specified.

## Base URL

```
http://localhost:5000/api
```

## Authentication

Most endpoints require authentication using JWT tokens. Tokens are automatically included via HttpOnly cookies after login.

### Headers

For manual API testing, you can include the token in the Authorization header:

```
Authorization: Bearer <access_token>
```

## Response Format

All responses follow this general structure:

### Success Response
```json
{
    "message": "Operation successful",
    "data": { ... }
}
```

### Error Response
```json
{
    "error": "Error message",
    "code": "ERROR_CODE"
}
```

## Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required or failed
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Authentication Endpoints

### POST /auth/login

Login to the system and receive JWT tokens.

**Request Body:**
```json
{
    "email": "admin@studentcrm.com",
    "password": "admin123"
}
```

**Response (200):**
```json
{
    "message": "Login successful",
    "user": {
        "id": 1,
        "email": "admin@studentcrm.com",
        "full_name": "System Administrator",
        "role": "super_admin",
        "is_active": true
    },
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbG...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbG..."
}
```

### POST /auth/logout

Logout and clear authentication cookies.

**Response (200):**
```json
{
    "message": "Logout successful"
}
```

### POST /auth/refresh

Refresh access token using refresh token.

**Request Body:**
```json
{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbG..."
}
```

**Response (200):**
```json
{
    "message": "Token refreshed",
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbG..."
}
```

### GET /auth/me

Get current user information.

**Response (200):**
```json
{
    "user": {
        "id": 1,
        "email": "admin@studentcrm.com",
        "full_name": "System Administrator",
        "role": "super_admin",
        "department": null,
        "is_active": true,
        "created_at": "2024-01-01T00:00:00"
    }
}
```

### POST /auth/change-password

Change user password.

**Request Body:**
```json
{
    "current_password": "old_password",
    "new_password": "new_password"
}
```

**Response (200):**
```json
{
    "message": "Password changed successfully"
}
```

---

## Student Endpoints

### GET /students

Get list of students with role-based filtering.

**Query Parameters:**
- `page` (integer) - Page number (default: 1)
- `per_page` (integer) - Results per page (default: 20)
- `search` (string) - Search by name, email, or student number
- `stage` (string) - Filter by application stage
- `department` (string) - Filter by department

**Response (200):**
```json
{
    "students": [
        {
            "id": 1,
            "student_number": "STU2024000001",
            "full_name": "Ali bin Mohamed",
            "email": "ali.mohamed@email.com",
            "phone": "+60123000001",
            "nationality": "Malaysia",
            "current_stage": "documents_collection",
            "department": "Engineering",
            "created_at": "2024-01-01T00:00:00"
        }
    ],
    "total": 100,
    "pages": 5,
    "current_page": 1
}
```

### GET /students/{id}

Get detailed student information.

**Path Parameters:**
- `id` (integer) - Student ID

**Response (200):**
```json
{
    "id": 1,
    "student_number": "STU2024000001",
    "full_name": "Ali bin Mohamed",
    "email": "ali.mohamed@email.com",
    "phone": "+60123000001",
    "nationality": "Malaysia",
    "passport_number": "A12345678",
    "passport_expiry": "2030-12-31",
    "current_stage": "documents_collection",
    "department": "Engineering",
    "applications": [...],
    "counsellors": [...],
    "created_at": "2024-01-01T00:00:00"
}
```

### POST /students

Create new student profile.

**Required Roles:** super_admin, admin, counsellor

**Request Body:**
```json
{
    "full_name": "John Doe",
    "email": "john@example.com",
    "phone": "+60123456789",
    "nationality": "Malaysia",
    "date_of_birth": "2000-01-01",
    "gender": "male",
    "passport_number": "A12345678",
    "passport_expiry": "2030-12-31",
    "address": "123 Main St",
    "emergency_contact_name": "Jane Doe",
    "emergency_contact_phone": "+60987654321",
    "emergency_contact_relationship": "Mother",
    "department": "Engineering"
}
```

**Response (201):**
```json
{
    "message": "Student created successfully",
    "student": { ... }
}
```

### PUT /students/{id}

Update student profile.

**Path Parameters:**
- `id` (integer) - Student ID

**Request Body:** (all fields optional)
```json
{
    "full_name": "John Doe Updated",
    "phone": "+60123456789",
    "address": "456 New St"
}
```

**Response (200):**
```json
{
    "message": "Student updated successfully",
    "student": { ... }
}
```

### PUT /students/{id}/stage

Update student application stage.

**Required Roles:** super_admin, admin, counsellor

**Request Body:**
```json
{
    "stage": "offer_received"
}
```

**Valid Stages:**
- inquiry
- documents_collection
- application_submitted
- offer_received
- visa_processing
- visa_approved
- arrival_scheduled
- arrived
- enrolled
- rejected
- cancelled

**Response (200):**
```json
{
    "message": "Stage updated successfully",
    "old_stage": "documents_collection",
    "new_stage": "offer_received"
}
```

### POST /students/{id}/assign-counsellor

Assign counsellor to student.

**Required Roles:** super_admin, admin

**Request Body:**
```json
{
    "counsellor_id": 5
}
```

**Response (200):**
```json
{
    "message": "Counsellor assigned successfully"
}
```

### DELETE /students/{id}

Delete student profile.

**Required Roles:** super_admin, admin

**Response (200):**
```json
{
    "message": "Student deleted successfully"
}
```

### GET /students/dashboard

Get dashboard statistics.

**Response (200):**
```json
{
    "total_students": 150,
    "by_stage": {
        "inquiry": 20,
        "documents_collection": 30,
        "application_submitted": 25,
        "offer_received": 15,
        "visa_processing": 20,
        "visa_approved": 15,
        "arrived": 10,
        "enrolled": 15
    },
    "recent_students": [...]
}
```

---

## Document Endpoints

### POST /documents/upload

Upload encrypted document.

**Content-Type:** multipart/form-data

**Form Data:**
- `file` (file) - Document file
- `student_id` (integer) - Student ID
- `document_type` (string) - Type of document (passport, transcript, certificate, etc.)
- `expiry_date` (string, optional) - Expiry date (ISO format)
- `notes` (string, optional) - Notes about the document

**Allowed File Types:** pdf, jpg, jpeg, png, doc, docx, txt

**Response (201):**
```json
{
    "message": "Document uploaded successfully",
    "document": {
        "id": 1,
        "student_id": 1,
        "document_type": "passport",
        "original_filename": "passport.pdf",
        "file_size": 1024000,
        "status": "uploaded",
        "version": 1,
        "uploaded_at": "2024-01-01T00:00:00"
    }
}
```

### GET /documents/{id}

Get document information (not the file itself).

**Response (200):**
```json
{
    "id": 1,
    "student_id": 1,
    "document_type": "passport",
    "original_filename": "passport.pdf",
    "file_size": 1024000,
    "status": "uploaded",
    "version": 1,
    "expiry_date": "2030-12-31",
    "uploaded_by": "Sarah Johnson",
    "uploaded_at": "2024-01-01T00:00:00"
}
```

### GET /documents/{id}/download

Download and decrypt document.

**Response:** Binary file download

### GET /documents/student/{student_id}

Get all documents for a student.

**Response (200):**
```json
{
    "documents": [
        {
            "id": 1,
            "document_type": "passport",
            "status": "verified",
            "version": 1,
            "uploaded_at": "2024-01-01T00:00:00"
        }
    ]
}
```

### POST /documents/{id}/verify

Verify or reject document.

**Request Body:**
```json
{
    "status": "verified",
    "notes": "Document verified and approved"
}
```

**Valid Status Values:** verified, rejected

**Response (200):**
```json
{
    "message": "Document verified successfully",
    "document": { ... }
}
```

### DELETE /documents/{id}

Delete document.

**Response (200):**
```json
{
    "message": "Document deleted successfully"
}
```

---

## Logistics Endpoints

### GET /logistics

Get list of logistics arrangements.

**Required Roles:** super_admin, admin, logistics_team

**Query Parameters:**
- `status` (string) - Filter by status
- `arrival_date_from` (string) - Filter by arrival date (ISO format)
- `arrival_date_to` (string) - Filter by arrival date (ISO format)

**Response (200):**
```json
{
    "arrangements": [
        {
            "id": 1,
            "student_id": 1,
            "arrival_date": "2024-09-01T10:00:00",
            "arrival_flight": "MH123",
            "pickup_required": true,
            "pickup_status": "assigned",
            "housing_required": true,
            "medical_screening_required": true,
            "student": { ... }
        }
    ]
}
```

### GET /logistics/student/{student_id}

Get logistics arrangement for a student.

**Response (200):**
```json
{
    "id": 1,
    "student_id": 1,
    "arrival_date": "2024-09-01T10:00:00",
    "arrival_flight": "MH123",
    "arrival_airport": "KLIA",
    "pickup_required": true,
    "pickup_status": "assigned",
    "housing_address": "123 University St",
    "medical_appointment_date": "2024-09-05T14:00:00"
}
```

### POST /logistics/student/{student_id}

Create logistics arrangement.

**Required Roles:** super_admin, admin, counsellor

**Request Body:**
```json
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
```

**Response (201):**
```json
{
    "message": "Logistics arrangement created successfully",
    "arrangement": { ... }
}
```

### PUT /logistics/{id}

Update logistics arrangement.

**Request Body:** (all fields optional)
```json
{
    "pickup_status": "completed",
    "housing_status": "ready",
    "medical_status": "scheduled"
}
```

**Response (200):**
```json
{
    "message": "Logistics arrangement updated successfully",
    "arrangement": { ... }
}
```

---

## Notification Endpoints

### GET /notifications

Get notifications for current user.

**Query Parameters:**
- `unread_only` (boolean) - Get only unread notifications (true/false)
- `limit` (integer) - Number of notifications to return (default: 50)

**Response (200):**
```json
{
    "notifications": [
        {
            "id": 1,
            "title": "New Document Uploaded",
            "message": "Student Ali bin Mohamed uploaded passport",
            "priority": "medium",
            "notification_type": "document",
            "is_read": false,
            "created_at": "2024-01-01T00:00:00"
        }
    ],
    "unread_count": 5
}
```

### POST /notifications/{id}/read

Mark notification as read.

**Response (200):**
```json
{
    "message": "Notification marked as read"
}
```

### POST /notifications/mark-all-read

Mark all notifications as read.

**Response (200):**
```json
{
    "message": "All notifications marked as read"
}
```

---

## Admin Endpoints

### GET /admin/users

Get list of users.

**Required Roles:** super_admin, admin

**Response (200):**
```json
{
    "users": [
        {
            "id": 1,
            "email": "admin@studentcrm.com",
            "full_name": "System Administrator",
            "role": "super_admin",
            "is_active": true
        }
    ],
    "total": 50,
    "pages": 3,
    "current_page": 1
}
```

### POST /admin/users

Create new user.

**Required Roles:** super_admin, admin

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "password123",
    "full_name": "John Doe",
    "role": "counsellor",
    "department": "Engineering",
    "phone": "+60123456789"
}
```

**Response (201):**
```json
{
    "message": "User created successfully",
    "user": { ... }
}
```

### GET /admin/universities

Get list of partner universities.

**Response (200):**
```json
{
    "universities": [
        {
            "id": 1,
            "name": "University of Malaya",
            "code": "UM",
            "location": "Kuala Lumpur",
            "is_active": true
        }
    ]
}
```

---

## Audit Endpoints

### GET /audit/logs

Get audit logs with filtering.

**Required Roles:** super_admin, admin

**Query Parameters:**
- `page` (integer) - Page number
- `per_page` (integer) - Results per page
- `event_type` (string) - Filter by event type
- `category` (string) - Filter by category
- `user_id` (integer) - Filter by user
- `date_from` (string) - Filter by date (ISO format)
- `date_to` (string) - Filter by date (ISO format)

**Response (200):**
```json
{
    "logs": [
        {
            "id": 1,
            "user": "System Administrator",
            "event_type": "login_success",
            "event_category": "authentication",
            "description": "User login successful",
            "ip_address": "192.168.1.100",
            "timestamp": "2024-01-01T00:00:00"
        }
    ],
    "total": 500,
    "pages": 10,
    "current_page": 1
}
```

---

## Backup Endpoints

### POST /backup/create

Create system backup.

**Required Roles:** super_admin

**Request Body:**
```json
{
    "backup_type": "full",
    "upload_to_cloud": true
}
```

**Valid Backup Types:** full, incremental, documents

**Response (201):**
```json
{
    "message": "Backup created successfully",
    "backup": {
        "id": 1,
        "backup_type": "full",
        "status": "completed",
        "file_size": 10485760
    }
}
```

### GET /backup/list

Get list of all backups.

**Required Roles:** super_admin

**Response (200):**
```json
{
    "backups": [
        {
            "id": 1,
            "backup_type": "full",
            "status": "completed",
            "started_at": "2024-01-01T00:00:00",
            "completed_at": "2024-01-01T00:10:00"
        }
    ]
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| NO_TOKEN | No authentication token provided |
| INVALID_TOKEN | Token is invalid or expired |
| USER_NOT_FOUND | User account not found or inactive |
| FORBIDDEN | Insufficient permissions for this action |
| VALIDATION_ERROR | Request data validation failed |
| RESOURCE_NOT_FOUND | Requested resource not found |
| DUPLICATE_ENTRY | Resource already exists |

---

## Rate Limiting

API rate limiting may be implemented in production environments. Typical limits:
- Authentication endpoints: 10 requests per minute
- Data retrieval: 100 requests per minute
- Data modification: 50 requests per minute

---

## Testing with cURL

### Login Example
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@studentcrm.com","password":"admin123"}' \
  -c cookies.txt
```

### Authenticated Request Example
```bash
curl -X GET http://localhost:5000/api/students \
  -b cookies.txt
```

### File Upload Example
```bash
curl -X POST http://localhost:5000/api/documents/upload \
  -b cookies.txt \
  -F "file=@/path/to/document.pdf" \
  -F "student_id=1" \
  -F "document_type=passport"
```

---

For more information, refer to the main README.md file.
