# Smart Clinic Portal — Project Specification

> **⚠️ AI-generated draft — requires human review before use.**  
> **Status:** APPROVED (Reviewed by Human Tech Lead)  
> **Generated:** 2026-11-18 16:50 UTC

---

## Project Summary
Online medical clinic booking interface allowing patients to schedule 30-minute consultations with available doctors.

---

## Features

### 1. Doctor Calendar View
Weekly calendar displaying available 30-minute appointment slots for doctors.
- **Priority:** High
- **Source:** client_text

### 2. Appointment Booking Form
Patient inputs personal details and confirms selection of available appointment slot.
- **Priority:** High
- **Source:** client_text

### 3. Confidential Medical Notes
Secure text area allowing patient to provide consultation notes prior to visit.
- **Priority:** Medium
- **Source:** client_text

---

## User Stories

### US-001
- **As a** patient  
- **I want** view doctor availability on a weekly calendar  
- **So that** select a time slot that matches my schedule

### US-002
- **As a** patient  
- **I want** book a 30-minute consultation slot  
- **So that** confirm my appointment with the doctor

### US-003
- **As a** patient  
- **I want** submit confidential medical notes  
- **So that** provide context to the physician before the consultation

---

## Acceptance Criteria

### AC-001 (US-001)
- **Given** A patient is viewing the clinic booking page
- **When** A doctor is selected from the dropdown
- **Then** Available 30-minute slots are rendered on the weekly calendar

### AC-002 (US-002)
- **Given** A patient has selected an open slot
- **When** They submit valid contact details and click confirm
- **Then** The appointment is reserved and an appointment reference number is displayed

### AC-003 (US-003)
- **Given** A patient is confirming a booking
- **When** They enter medical symptom notes
- **Then** The notes are stored with restricted access visible only to the assigned doctor

---

## Implementation Plan

### Frontend
- Doctor selector dropdown
- Interactive weekly calendar grid component
- Booking confirmation modal with note textarea

### Backend
- `GET /api/v1/doctors/{id}/availability`
- `POST /api/v1/appointments/book`
- `POST /api/v1/appointments/{id}/notes`

### Data
- `doctors` table
- `availability_slots` table
- `appointments` table

### Risks
- Double booking of the same slot during concurrent patient submissions
- Data privacy compliance for stored medical notes

---

## QA Test Cases

### TC-001 [positive] — Successfully book an open appointment slot
1. Select Doctor Smith
2. Select Monday 10:00 AM slot
3. Enter name 'Jane Doe'
4. Click Confirm Booking  
**Expected:** System returns 200 OK, marks slot as booked, and returns confirmation code.

### TC-002 [negative] — Prevent booking an already reserved slot
1. Select a slot that was already booked by another user
2. Click Confirm Booking  
**Expected:** System returns 409 Conflict with error message 'Slot is no longer available'.

### TC-003 [edge] — Booking request during daylight saving time changeover
1. Request booking during UTC timezone shift boundary  
**Expected:** System stores appointment in unambiguous UTC ISO format without corrupting time.

---

## Developer Prompt
```
You are implementing the Smart Clinic Portal scheduling module. Constraints: Use FastAPI and SQLite with transactional row-level isolation on availability_slots to prevent double booking. Expose GET availability and POST booking endpoints conforming strictly to the defined schema. Write comprehensive unit tests.
```

---

## Assumptions
- Appointments are fixed at 30 minutes duration.
- System stores all timestamps in UTC.

---

## Open Questions (Uncertainty Surfaced)
- ❓ What is the clinic cancellation policy timeframe?
- ❓ Do patients require SMS or email confirmation notifications?

---

## Evidence Traceability
- **Doctor Appointment Booking** _(source: client_text)_ — Directly requested in client brief.
- **30-minute consultation slots** _(source: client_text)_ — Explicitly stated in client brief.
