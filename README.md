
# 📘 Software Requirement Specification (SRS)
### For: AI-Based Face Recognition Attendance System

---

## 📖 Introduction

### 🎯 Purpose
The system provides rural schools with a **low-cost, AI-powered attendance tracking solution**.  
It reduces manual work, eliminates paper registers, and provides real-time attendance data.  
Teachers and administrators can securely view, manage, and report attendance records.

### 📌 Scope
- Uses a single camera in each classroom to recognize students in real time.  
- Students recognized are marked **present**; those not detected are **absent**.  
- Teachers and administrators access attendance records via a **web-based dashboard**.  
- Removes the need for costly RFID/biometric devices, ensuring affordability and scalability.  

### 👥 Stakeholders
- **Students** – Attendance tracked automatically.  
- **Teachers/Class Teachers** – Manage and view class attendance.  
- **School Administrators** – Access and monitor school-wide attendance reports.  

### 🔑 Definitions
- **AI** – Artificial Intelligence.  
- **Dashboard** – Web interface for monitoring/managing attendance.  
- **Recognition Model** – AI algorithm trained with student images.  

---

## 📝 Overall Description

### 📷 Product Perspective
- Integrated camera + AI face recognition model.  
- Data securely stored in a database.  
- Accessible via a lightweight web interface.  

### ⚡ Product Functions
- Automatic attendance marking.  
- Role-based dashboards.  
- Daily/Monthly reports.  
- Export to Excel/PDF.  
- Secure storage & retrieval.  

### 👩‍🏫 User Classes
- **Teachers** – Non-technical, simple UI required.  
- **Administrators** – Need both detailed and summary reports.  

### 💻 Operating Environment
- **Hardware**: Low-cost PC with camera.  
- **Software**: Browser-based web app.  
- **Database**: Secure attendance log storage.  

### 🔒 Constraints
- Must work on affordable hardware with limited internet.  
- Ensure privacy and data security.  
- Handle multiple classrooms simultaneously.  

### 📌 Assumptions
- Reliable camera setup in classrooms.  
- Student image dataset available for AI training.  
- Basic internet/computer availability.  

---

## ⚙️ Functional Requirements

1. **User Authentication**
   - Secure login for teachers & administrators.  
   - Role-based access (teacher → class only, admin → all).  

2. **Attendance Management**
   - AI marks present/absent automatically.  
   - Secure database logging.  

3. **Dashboard**
   - Teachers → class attendance view.  
   - Admins → school-wide attendance view.  
   - Attendance summaries in percentages.  

4. **Reporting**
   - Generate daily/weekly/monthly reports.  
   - Export to Excel/PDF.  
   - Graphical trend summaries.  

5. **Student Data Management**
   - Add/update student images for AI training.  
   - Update records as appearance changes.  
   - Maintain historical logs.  

---

## 📊 Non-Functional Requirements
- **Performance**: Real-time recognition during school hours.  
- **Scalability**: Support multiple classes & hundreds of students.  
- **Usability**: Teacher-friendly dashboard.  
- **Security**: Encrypted storage, role-based access.  
- **Cost Efficiency**: Runs on affordable hardware.  
- **Reliability**: Continuous operation throughout the day.  
- **Maintainability**: Easy retraining and updates.  

---

## 🔄 System Models

- **Use Case Diagram** → Teacher/Admin interactions with system.  
- **Data Flow Diagram** → Camera → AI Recognition → Database → Dashboard.  

---

## 🚀 Future Enhancements
- Mobile app integration.  
- SMS alerts for absentees.  
- Cloud-based multi-school dashboards.  

---

## 📝 License
This project is available under the **MIT License**.
