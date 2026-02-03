#!/usr/bin/env python3
"""
ASPIRATION BOT - Aspire Youth Academy Grade 8
Complete Attendance System with Daily Tracking
Author: System Administrator
"""

import telebot
import json
import os
import sqlite3
from datetime import datetime, timedelta
import logging

# ===================== CONFIGURATION =====================
BOT_TOKEN = "8247448831:AAHkXdidOfZGwj42SoqjNwkQiw5l4CKQmnk"
SCHOOL_NAME = "Aspire Youth Academy"
GRADE = "Grade 8"

# Files for storing dynamic admin/teacher lists
ADMINS_FILE = "admins.json"
TEACHERS_FILE = "teachers.json"
ATTENDANCE_FILE = "attendance.json"
DB_FILE = "school_bot.db"

# ===================== ATTENDANCE MANAGER =====================
class AttendanceManager:
    """Manage daily attendance"""
    
    def __init__(self):
        self.attendance = self.load_attendance()
    
    def load_attendance(self):
        """Load attendance from JSON file"""
        try:
            with open(ATTENDANCE_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_attendance(self):
        """Save attendance to JSON file"""
        with open(ATTENDANCE_FILE, 'w') as f:
            json.dump(self.attendance, f, indent=2)
    
    def mark_present(self, user_id, username, first_name, is_manual=False):
        """Mark user as present for today"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today not in self.attendance:
            self.attendance[today] = {}
        
        if str(user_id) not in self.attendance[today]:
            self.attendance[today][str(user_id)] = {
                "username": username,
                "first_name": first_name,
                "time": datetime.now().strftime("%H:%M:%S"),
                "type": "manual" if is_manual else "profile",
                "status": "present"
            }
            self.save_attendance()
            return True, "✅ You have been marked PRESENT for today!"
        else:
            return False, "📝 You are already marked present for today."
    
    def mark_absent(self, user_id, username, first_name, reason=""):
        """Mark user as absent"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today not in self.attendance:
            self.attendance[today] = {}
        
        self.attendance[today][str(user_id)] = {
            "username": username,
            "first_name": first_name,
            "time": datetime.now().strftime("%H:%M:%S"),
            "type": "absent",
            "reason": reason,
            "status": "absent"
        }
        self.save_attendance()
        return True, f"📝 Marked as ABSENT. Reason: {reason if reason else 'Not specified'}"
    
    def get_today_attendance(self):
        """Get today's attendance record"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today not in self.attendance or not self.attendance[today]:
            return None
        
        present = []
        absent = []
        
        for user_id, data in self.attendance[today].items():
            if data["status"] == "present":
                present.append(data)
            else:
                absent.append(data)
        
        return {
            "date": today,
            "present": present,
            "absent": absent,
            "total_present": len(present),
            "total_absent": len(absent),
            "total": len(present) + len(absent)
        }
    
    def get_user_attendance(self, user_id):
        """Get user's attendance record"""
        user_id = str(user_id)
        records = []
        
        for date, day_data in self.attendance.items():
            if user_id in day_data:
                records.append({
                    "date": date,
                    "status": day_data[user_id]["status"],
                    "time": day_data[user_id]["time"],
                    "type": day_data[user_id].get("type", "unknown")
                })
        
        # Sort by date (newest first)
        records.sort(key=lambda x: x["date"], reverse=True)
        
        # Calculate statistics
        total_days = len(records)
        present_days = len([r for r in records if r["status"] == "present"])
        absent_days = len([r for r in records if r["status"] == "absent"])
        
        if total_days > 0:
            attendance_rate = (present_days / total_days) * 100
        else:
            attendance_rate = 0
        
        return {
            "records": records[:30],  # Last 30 days
            "total_days": total_days,
            "present_days": present_days,
            "absent_days": absent_days,
            "attendance_rate": round(attendance_rate, 1)
        }
    
    def get_attendance_summary(self, days=7):
        """Get attendance summary for last N days"""
        summary = {}
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            if date_str in self.attendance:
                day_data = self.attendance[date_str]
                present = len([u for u in day_data.values() if u["status"] == "present"])
                absent = len([u for u in day_data.values() if u["status"] == "absent"])
                summary[date_str] = {
                    "present": present,
                    "absent": absent,
                    "total": present + absent
                }
            current_date += timedelta(days=1)
        
        return summary

# ===================== USER MANAGER =====================
class UserManager:
    """Manage admins and teachers"""
    
    def __init__(self):
        self.admins = self.load_users(ADMINS_FILE)
        self.teachers = self.load_users(TEACHERS_FILE)
        
        # Ensure super admins are always in admin list
        super_admins = ["sh3ll_3xp10it", "dagi_tariku"]
        for admin in super_admins:
            if admin not in self.admins:
                self.admins.append(admin)
        self.save_admins()
    
    def load_users(self, filename):
        """Load user list from JSON file"""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def save_users(self, users, filename):
        """Save user list to JSON file"""
        with open(filename, 'w') as f:
            json.dump(users, f, indent=2)
    
    def save_admins(self):
        self.save_users(self.admins, ADMINS_FILE)
    
    def save_teachers(self):
        self.save_users(self.teachers, TEACHERS_FILE)
    
    def is_super_admin(self, username):
        """Check if user is super admin"""
        super_admins = ["sh3ll_3xp10it", "dagi_tariku"]
        return username in super_admins if username else False
    
    def is_admin(self, username):
        """Check if user is admin"""
        return username in self.admins if username else False
    
    def is_teacher(self, username):
        """Check if user is teacher"""
        return username in self.teachers if username else False
    
    def add_admin(self, username, by_admin):
        """Add new admin"""
        username = username.lower().replace('@', '')
        
        if not username:
            return False, "❌ Invalid username"
        
        if self.is_admin(username):
            return False, f"❌ @{username} is already an admin"
        
        self.admins.append(username)
        self.save_admins()
        return True, f"✅ @{username} added as ADMIN by @{by_admin}"
    
    def remove_admin(self, username, by_admin):
        """Remove admin"""
        username = username.lower().replace('@', '')
        
        if self.is_super_admin(username):
            return False, f"❌ Cannot remove SUPER ADMIN @{username}"
        
        if username == by_admin:
            return False, "❌ You cannot remove yourself"
        
        if username not in self.admins:
            return False, f"❌ @{username} is not an admin"
        
        self.admins.remove(username)
        self.save_admins()
        return True, f"✅ @{username} removed from admins by @{by_admin}"
    
    def add_teacher(self, username, by_admin):
        """Add new teacher"""
        username = username.lower().replace('@', '')
        
        if not username:
            return False, "❌ Invalid username"
        
        if self.is_teacher(username):
            return False, f"❌ @{username} is already a teacher"
        
        self.teachers.append(username)
        self.save_teachers()
        return True, f"✅ @{username} added as TEACHER by @{by_admin}"
    
    def remove_teacher(self, username, by_admin):
        """Remove teacher"""
        username = username.lower().replace('@', '')
        
        if username not in self.teachers:
            return False, f"❌ @{username} is not a teacher"
        
        self.teachers.remove(username)
        self.save_teachers()
        return True, f"✅ @{username} removed from teachers by @{by_admin}"
    
    def list_admins(self):
        """Get admin list"""
        if not self.admins:
            return "📭 No administrators found"
        
        response = "👮 <b>ADMINISTRATORS:</b>\n\n"
        for i, admin in enumerate(self.admins, 1):
            if self.is_super_admin(admin):
                response += f"{i}. 👑 @{admin} (SUPER ADMIN)\n"
            else:
                response += f"{i}. 👨‍💼 @{admin}\n"
        
        response += f"\n📊 Total: {len(self.admins)} admins"
        return response
    
    def list_teachers(self):
        """Get teacher list"""
        if not self.teachers:
            return "📭 No teachers found"
        
        response = "👨‍🏫 <b>TEACHERS:</b>\n\n"
        for i, teacher in enumerate(self.teachers, 1):
            response += f"{i}. @{teacher}\n"
        
        response += f"\n📊 Total: {len(self.teachers)} teachers"
        return response

# ===================== MAIN BOT =====================
class AttendanceBot:
    """Main bot class with attendance system"""
    
    def __init__(self):
        self.bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')
        self.user_manager = UserManager()
        self.attendance = AttendanceManager()
        self.setup_handlers()
        
        print("=" * 60)
        print(f"🏫 {SCHOOL_NAME} - {GRADE}")
        print(f"🤖 Attendance Bot v2.0")
        print("=" * 60)
        print(f"👑 Super Admins: @sh3ll_3xp10it, @dagi_tariku")
        print(f"👨‍💼 Total Admins: {len(self.user_manager.admins)}")
        print(f"👨‍🏫 Total Teachers: {len(self.user_manager.teachers)}")
        print("=" * 60)
    
    def setup_handlers(self):
        """Setup command handlers"""
        
        # ========== BASIC COMMANDS ==========
        @self.bot.message_handler(commands=['start', 'help'])
        def help_handler(message):
            """Help command"""
            user = message.from_user
            username = user.username
            
            if self.user_manager.is_admin(username):
                response = self._get_admin_help(username)
            elif self.user_manager.is_teacher(username):
                response = self._get_teacher_help(username)
            else:
                response = self._get_student_help()
            
            self.bot.reply_to(message, response)
        
        @self.bot.message_handler(commands=['rules'])
        def rules_handler(message):
            """Rules command"""
            rules = self._get_rules()
            self.bot.reply_to(message, rules)
        
        # ========== ATTENDANCE COMMANDS ==========
        @self.bot.message_handler(commands=['present', 'attend'])
        def present_handler(message):
            """Manually mark present"""
            user = message.from_user
            success, result = self.attendance.mark_present(
                user.id, 
                user.username, 
                user.first_name,
                is_manual=True
            )
            
            response = (
                f"📋 <b>ATTENDANCE RECORDED</b>\n\n"
                f"{result}\n\n"
                f"👤 Student: {user.first_name}\n"
                f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}\n"
                f"🕐 Time: {datetime.now().strftime('%H:%M:%S')}\n\n"
                f"💡 <b>Note:</b> Your attendance is automatically recorded when you use /profile"
            )
            
            self.bot.reply_to(message, response)
        
        @self.bot.message_handler(commands=['profile'])
        def profile_handler(message):
            """Profile command - AUTO MARKS PRESENT"""
            user = message.from_user
            
            # AUTO MARK PRESENT when checking profile
            attendance_result = self.attendance.mark_present(
                user.id, 
                user.username, 
                user.first_name,
                is_manual=False
            )
            
            # Get user's attendance record
            user_attendance = self.attendance.get_user_attendance(user.id)
            
            # Get today's attendance
            today_attendance = self.attendance.get_today_attendance()
            
            # Determine role
            username = user.username
            if self.user_manager.is_super_admin(username):
                role = "👑 SUPER ADMIN"
            elif self.user_manager.is_admin(username):
                role = "👨‍💼 ADMINISTRATOR"
            elif self.user_manager.is_teacher(username):
                role = "👨‍🏫 TEACHER"
            else:
                role = "👨‍🎓 STUDENT"
            
            # Build profile response
            response = (
                f"👤 <b>STUDENT PROFILE</b>\n"
                f"🏫 {SCHOOL_NAME} - {GRADE}\n\n"
                
                f"📋 <b>PERSONAL INFORMATION:</b>\n"
                f"• Name: {user.first_name} {user.last_name or ''}\n"
                f"• Username: @{username or 'Not set'}\n"
                f"• Role: {role}\n"
                f"• Student ID: <code>{user.id}</code>\n\n"
                
                f"📊 <b>ATTENDANCE STATISTICS:</b>\n"
                f"• Total Days: {user_attendance['total_days']}\n"
                f"• Present Days: {user_attendance['present_days']}\n"
                f"• Absent Days: {user_attendance['absent_days']}\n"
                f"• Attendance Rate: {user_attendance['attendance_rate']}%\n\n"
            )
            
            # Add today's attendance status
            if today_attendance and str(user.id) in today_attendance.get('present', []):
                response += f"✅ <b>Today's Status:</b> PRESENT (Auto-recorded at {datetime.now().strftime('%H:%M:%S')})\n\n"
            
            # Add recent attendance records (last 5 days)
            if user_attendance['records']:
                response += f"📅 <b>RECENT ATTENDANCE:</b>\n"
                for record in user_attendance['records'][:5]:
                    status_icon = "✅" if record['status'] == 'present' else "❌"
                    response += f"{status_icon} {record['date']}: {record['status'].title()} ({record['time']})\n"
                response += "\n"
            
            # Add admin/teacher specific info
            if self.user_manager.is_admin(username) or self.user_manager.is_teacher(username):
                if today_attendance:
                    response += f"📈 <b>TODAY'S OVERVIEW:</b>\n"
                    response += f"• Present: {today_attendance['total_present']} students\n"
                    response += f"• Absent: {today_attendance['total_absent']} students\n"
                    response += f"• Total: {today_attendance['total']} students\n\n"
            
            response += (
                f"💡 <b>IMPORTANT:</b>\n"
                f"• Using /profile automatically marks you PRESENT for today\n"
                f"• You can also use /present to mark attendance manually\n"
                f"• Check attendance daily to maintain good record\n\n"
                
                f"👮 <b>Super Admins:</b> @sh3ll_3xp10it, @dagi_tariku"
            )
            
            self.bot.reply_to(message, response)
        
        @self.bot.message_handler(commands=['attendance', 'myattendance'])
        def attendance_handler(message):
            """View detailed attendance"""
            user = message.from_user
            user_attendance = self.attendance.get_user_attendance(user.id)
            
            if not user_attendance['records']:
                response = (
                    f"📋 <b>ATTENDANCE RECORD</b>\n\n"
                    f"👤 Student: {user.first_name}\n"
                    f"📊 Status: No attendance records yet\n\n"
                    f"💡 <b>How to record attendance:</b>\n"
                    f"1. Use /profile - Auto records attendance\n"
                    f"2. Use /present - Manually mark present\n"
                    f"3. Teachers can mark you present/absent\n\n"
                    f"🏫 Check in daily to maintain perfect attendance!"
                )
            else:
                response = (
                    f"📋 <b>ATTENDANCE DETAILS</b>\n"
                    f"👤 {user.first_name} (@{user.username or 'No username'})\n\n"
                    
                    f"📊 <b>STATISTICS:</b>\n"
                    f"• Total Days: {user_attendance['total_days']}\n"
                    f"• Present: {user_attendance['present_days']} days\n"
                    f"• Absent: {user_attendance['absent_days']} days\n"
                    f"• Rate: {user_attendance['attendance_rate']}%\n\n"
                    
                    f"📅 <b>LAST 10 RECORDS:</b>\n"
                )
                
                for i, record in enumerate(user_attendance['records'][:10], 1):
                    status_icon = "✅" if record['status'] == 'present' else "❌"
                    date_obj = datetime.strptime(record['date'], "%Y-%m-%d")
                    day_name = date_obj.strftime("%a")
                    response += f"{i}. {status_icon} {record['date']} ({day_name}): {record['status'].title()}\n"
                
                response += "\n"
                
                # Add rating based on attendance
                if user_attendance['attendance_rate'] >= 95:
                    rating = "🏆 EXCELLENT"
                    comment = "Perfect attendance! Keep it up!"
                elif user_attendance['attendance_rate'] >= 80:
                    rating = "👍 GOOD"
                    comment = "Good attendance record"
                elif user_attendance['attendance_rate'] >= 60:
                    rating = "⚠️ NEEDS IMPROVEMENT"
                    comment = "Try to improve attendance"
                else:
                    rating = "❌ POOR"
                    comment = "Attendance needs immediate improvement"
                
                response += f"⭐ <b>RATING:</b> {rating}\n"
                response += f"💡 {comment}\n\n"
                
                response += (
                    f"📝 <b>TODAY'S STATUS:</b> "
                )
                
                today = datetime.now().strftime("%Y-%m-%d")
                today_record = next((r for r in user_attendance['records'] if r['date'] == today), None)
                
                if today_record:
                    response += f"{today_record['status'].upper()} (Recorded at {today_record['time']})"
                else:
                    response += "NOT YET RECORDED\n💡 Use /profile to mark today's attendance"
            
            self.bot.reply_to(message, response)
        
        @self.bot.message_handler(commands=['todayattendance', 'today'])
        def today_attendance_handler(message):
            """View today's attendance"""
            username = message.from_user.username
            
            # Only admins and teachers can view today's full attendance
            if not (self.user_manager.is_admin(username) or self.user_manager.is_teacher(username)):
                self.bot.reply_to(message,
                    "🚫 <b>ACCESS DENIED</b>\n\n"
                    "Only administrators and teachers can view today's full attendance.\n"
                    "👨‍🎓 Students can use /attendance to view their own record."
                )
                return
            
            today_data = self.attendance.get_today_attendance()
            
            if not today_data:
                response = (
                    f"📅 <b>TODAY'S ATTENDANCE - {datetime.now().strftime('%Y-%m-%d')}</b>\n\n"
                    f"📭 No attendance records yet for today.\n\n"
                    f"👨‍🏫 <b>How to record attendance:</b>\n"
                    f"• Students use /profile (auto-records)\n"
                    f"• Students use /present (manual)\n"
                    f"• Teachers can mark attendance\n\n"
                    f"🕐 <b>Current Time:</b> {datetime.now().strftime('%H:%M:%S')}"
                )
            else:
                response = (
                    f"📅 <b>TODAY'S ATTENDANCE</b>\n"
                    f"📅 Date: {today_data['date']}\n"
                    f"🕐 Time: {datetime.now().strftime('%H:%M:%S')}\n\n"
                    
                    f"📊 <b>SUMMARY:</b>\n"
                    f"• Present: {today_data['total_present']} students\n"
                    f"• Absent: {today_data['total_absent']} students\n"
                    f"• Total: {today_data['total']} students\n\n"
                    
                    f"✅ <b>PRESENT STUDENTS ({today_data['total_present']}):</b>\n"
                )
                
                if today_data['present']:
                    for i, student in enumerate(today_data['present'][:20], 1):
                        time_str = student['time'] if 'time' in student else 'N/A'
                        response += f"{i}. {student['first_name']} (@{student['username']}) - {time_str}\n"
                    
                    if len(today_data['present']) > 20:
                        response += f"... and {len(today_data['present']) - 20} more\n"
                else:
                    response += "No students marked present yet\n"
                
                response += "\n"
                
                response += f"❌ <b>ABSENT STUDENTS ({today_data['total_absent']}):</b>\n"
                if today_data['absent']:
                    for i, student in enumerate(today_data['absent'][:10], 1):
                        reason = student.get('reason', 'No reason')
                        response += f"{i}. {student['first_name']} (@{student['username']}) - {reason}\n"
                else:
                    response += "No students marked absent\n"
                
                response += "\n"
                response += f"📈 <b>ATTENDANCE RATE:</b> {round((today_data['total_present']/max(today_data['total'],1))*100,1)}%\n"
                response += f"👮 <b>Report by:</b> @{username}"
            
            self.bot.reply_to(message, response)
        
        @self.bot.message_handler(commands=['markabsent'])
        def mark_absent_handler(message):
            """Mark student as absent (teachers/admins only)"""
            username = message.from_user.username
            
            if not (self.user_manager.is_admin(username) or self.user_manager.is_teacher(username)):
                self.bot.reply_to(message,
                    "🚫 <b>ACCESS DENIED</b>\n\n"
                    "Only teachers and administrators can mark students as absent."
                )
                return
            
            if not message.reply_to_message:
                self.bot.reply_to(message,
                    "📝 <b>MARK STUDENT ABSENT</b>\n\n"
                    "⚠️ <b>Usage:</b> Reply to student's message with:\n"
                    "<code>/markabsent [reason]</code>\n\n"
                    "<b>Example:</b>\n"
                    "<code>/markabsent Sick leave</code>\n"
                    "<code>/markabsent Family emergency</code>"
                )
                return
            
            target = message.reply_to_message.from_user
            
            reason = "Not specified"
            if len(message.text.split()) > 1:
                reason = ' '.join(message.text.split()[1:])
            
            success, result = self.attendance.mark_absent(
                target.id,
                target.username,
                target.first_name,
                reason
            )
            
            response = (
                f"📝 <b>ABSENCE RECORDED</b>\n\n"
                f"👤 Student: {target.first_name} (@{target.username or 'No username'})\n"
                f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}\n"
                f"📝 Reason: {reason}\n"
                f"👮 Marked by: @{username}\n\n"
                f"⚠️ Student has been marked ABSENT for today."
            )
            
            self.bot.reply_to(message, response)
        
        @self.bot.message_handler(commands=['weeklyreport', 'weekreport'])
        def weekly_report_handler(message):
            """Weekly attendance report"""
            username = message.from_user.username
            
            if not (self.user_manager.is_admin(username) or self.user_manager.is_teacher(username)):
                self.bot.reply_to(message,
                    "🚫 <b>ACCESS DENIED</b>\n\n"
                    "Only teachers and administrators can view weekly reports."
                )
                return
            
            summary = self.attendance.get_attendance_summary(days=7)
            
            if not summary:
                response = (
                    f"📊 <b>WEEKLY ATTENDANCE REPORT</b>\n"
                    f"📅 Period: Last 7 days\n\n"
                    f"📭 No attendance records for this period.\n\n"
                    f"💡 Start recording attendance using /profile command."
                )
            else:
                # Calculate totals
                total_present = sum(day['present'] for day in summary.values())
                total_absent = sum(day['absent'] for day in summary.values())
                total = total_present + total_absent
                
                response = (
                    f"📊 <b>WEEKLY ATTENDANCE REPORT</b>\n"
                    f"📅 Period: Last 7 days\n"
                    f"👤 Generated by: @{username}\n\n"
                    
                    f"📈 <b>OVERALL STATISTICS:</b>\n"
                    f"• Total Present: {total_present}\n"
                    f"• Total Absent: {total_absent}\n"
                    f"• Total Records: {total}\n"
                    f"• Overall Rate: {round((total_present/max(total,1))*100,1)}%\n\n"
                    
                    f"📅 <b>DAILY BREAKDOWN:</b>\n"
                )
                
                for date_str, day_data in sorted(summary.items(), reverse=True):
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    day_name = date_obj.strftime("%a")
                    day_rate = round((day_data['present']/max(day_data['total'],1))*100,1)
                    
                    response += f"• {date_str} ({day_name}): {day_data['present']} present, {day_data['absent']} absent ({day_rate}%)\n"
                
                response += "\n"
                
                # Add analysis
                if total_present == 0:
                    analysis = "⚠️ No attendance recorded this week"
                elif total_present / max(total,1) >= 0.8:
                    analysis = "✅ Good attendance rate this week"
                elif total_present / max(total,1) >= 0.5:
                    analysis = "⚠️ Moderate attendance, needs improvement"
                else:
                    analysis = "❌ Low attendance, immediate action needed"
                
                response += f"📋 <b>ANALYSIS:</b> {analysis}\n\n"
                response += f"🏫 {SCHOOL_NAME}"
            
            self.bot.reply_to(message, response)
        
        # ========== ADMIN MANAGEMENT ==========
        @self.bot.message_handler(commands=['addadmin'])
        def add_admin_handler(message):
            """Add admin command"""
            username = message.from_user.username
            
            if not self.user_manager.is_super_admin(username):
                self.bot.reply_to(message, 
                    "🚫 <b>ACCESS DENIED</b>\n\n"
                    "Only SUPER ADMINS can add new administrators.\n"
                    "👑 Super Admins: @sh3ll_3xp10it, @dagi_tariku"
                )
                return
            
            parts = message.text.split()
            if len(parts) < 2:
                self.bot.reply_to(message,
                    "📝 <b>ADD ADMIN</b>\n\n"
                    "Usage: <code>/addadmin @username</code>\n\n"
                    "Example: <code>/addadmin @newadmin</code>"
                )
                return
            
            target = parts[1]
            success, result = self.user_manager.add_admin(target, username)
            self.bot.reply_to(message, result)
        
        @self.bot.message_handler(commands=['addteacher'])
        def add_teacher_handler(message):
            """Add teacher command"""
            username = message.from_user.username
            
            if not self.user_manager.is_admin(username):
                self.bot.reply_to(message,
                    "🚫 <b>ACCESS DENIED</b>\n\n"
                    "Only ADMINISTRATORS can add teachers."
                )
                return
            
            parts = message.text.split()
            if len(parts) < 2:
                self.bot.reply_to(message,
                    "👨‍🏫 <b>ADD TEACHER</b>\n\n"
                    "Usage: <code>/addteacher @username</code>\n\n"
                    "Example: <code>/addteacher @teachername</code>"
                )
                return
            
            target = parts[1]
            success, result = self.user_manager.add_teacher(target, username)
            self.bot.reply_to(message, result)
        
        @self.bot.message_handler(commands=['listadmins'])
        def list_admins_handler(message):
            """List admins command"""
            username = message.from_user.username
            
            if not (self.user_manager.is_admin(username) or self.user_manager.is_teacher(username)):
                self.bot.reply_to(message,
                    "🚫 <b>ACCESS DENIED</b>\n\n"
                    "Only admins and teachers can view admin list."
                )
                return
            
            response = self.user_manager.list_admins()
            self.bot.reply_to(message, response)
        
        @self.bot.message_handler(commands=['listteachers'])
        def list_teachers_handler(message):
            """List teachers command"""
            username = message.from_user.username
            
            if not (self.user_manager.is_admin(username) or self.user_manager.is_teacher(username)):
                self.bot.reply_to(message,
                    "🚫 <b>ACCESS DENIED</b>\n\n"
                    "Only admins and teachers can view teacher list."
                )
                return
            
            response = self.user_manager.list_teachers()
            self.bot.reply_to(message, response)
        
        # ========== MODERATION COMMANDS ==========
        @self.bot.message_handler(commands=['warn'])
        def warn_handler(message):
            """Warn command"""
            username = message.from_user.username
            
            if not self.user_manager.is_admin(username):
                self.bot.reply_to(message,
                    "🚫 <b>ACCESS DENIED</b>\n\n"
                    "Only ADMINISTRATORS can warn users."
                )
                return
            
            if not message.reply_to_message:
                self.bot.reply_to(message,
                    "⚠️ <b>Usage:</b> Reply to a message with:\n"
                    "<code>/warn [reason]</code>\n\n"
                    "Example: <code>/warn Spamming in chat</code>"
                )
                return
            
            target = message.reply_to_message.from_user
            
            reason = "No reason provided"
            if len(message.text.split()) > 1:
                reason = ' '.join(message.text.split()[1:])
            
            response = (
                f"⚠️ <b>WARNING ISSUED</b>\n\n"
                f"👤 User: {target.first_name} (@{target.username or 'No username'})\n"
                f"📝 Reason: {reason}\n"
                f"👮 Admin: @{username}\n"
                f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"🏫 {SCHOOL_NAME}"
            )
            
            self.bot.reply_to(message, response)
        
        @self.bot.message_handler(commands=['stats'])
        def stats_handler(message):
            """Stats command"""
            username = message.from_user.username
            
            if not self.user_manager.is_admin(username):
                self.bot.reply_to(message,
                    "🚫 <b>ACCESS DENIED</b>\n\n"
                    "Only ADMINISTRATORS can view statistics."
                )
                return
            
            # Get attendance summary
            summary = self.attendance.get_attendance_summary(days=30)
            total_present = sum(day['present'] for day in summary.values())
            total_absent = sum(day['absent'] for day in summary.values())
            total = total_present + total_absent
            
            response = (
                f"📊 <b>SYSTEM STATISTICS</b>\n"
                f"🏫 {SCHOOL_NAME} - {GRADE}\n\n"
                f"👥 <b>USER STATISTICS:</b>\n"
                f"• Administrators: {len(self.user_manager.admins)}\n"
                f"• Teachers: {len(self.user_manager.teachers)}\n"
                f"• Super Admins: 2\n\n"
                f"📋 <b>ATTENDANCE (Last 30 days):</b>\n"
                f"• Present Records: {total_present}\n"
                f"• Absent Records: {total_absent}\n"
                f"• Total Records: {total}\n"
                f"• Attendance Rate: {round((total_present/max(total,1))*100,1)}%\n\n"
                f"⚙️ <b>SYSTEM INFO:</b>\n"
                f"• Bot Version: 2.0\n"
                f"• Status: ✅ Online\n\n"
                f"🔄 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            self.bot.reply_to(message, response)
        
        # ========== DEFAULT HANDLER ==========
        @self.bot.message_handler(func=lambda message: True)
        def default_handler(message):
            """Handle other messages"""
            # You can add message logging or other processing here
            pass
    
    # ===================== HELPER METHODS =====================
    
    def _get_admin_help(self, username):
        """Get admin help"""
        return (
            f"📚 <b>{SCHOOL_NAME} - {GRADE}</b>\n"
            f"🤖 <b>ATTENDANCE BOT HELP</b>\n\n"
            f"Welcome, @{username} 👮\n\n"
            
            f"👑 <b>SUPER ADMIN COMMANDS:</b>\n"
            f"<code>/addadmin @username</code> - Add admin\n"
            f"<code>/addteacher @username</code> - Add teacher\n\n"
            
            f"👨‍🏫 <b>ATTENDANCE COMMANDS:</b>\n"
            f"<code>/todayattendance</code> - Today's attendance\n"
            f"<code>/weeklyreport</code> - Weekly report\n"
            f"<code>/markabsent [reply]</code> - Mark student absent\n\n"
            
            f"📋 <b>USER COMMANDS:</b>\n"
            f"<code>/profile</code> - Your profile (auto-records attendance)\n"
            f"<code>/present</code> - Manually mark present\n"
            f"<code>/attendance</code> - View your attendance\n"
            f"<code>/rules</code> - School rules\n\n"
            
            f"⚙️ <b>SYSTEM COMMANDS:</b>\n"
            f"<code>/listadmins</code> - List admins\n"
            f"<code>/listteachers</code> - List teachers\n"
            f"<code>/stats</code> - System statistics\n"
            f"<code>/warn [reply]</code> - Warn user\n\n"
            
            f"💡 <b>ATTENDANCE SYSTEM:</b>\n"
            f"• /profile auto-records daily attendance\n"
            f"• Check /profile every day\n"
            f"• Teachers can mark students absent\n"
            f"• View reports with /todayattendance\n\n"
            
            f"👑 <b>Super Admins:</b> @sh3ll_3xp10it, @dagi_tariku"
        )
    
    def _get_teacher_help(self, username):
        """Get teacher help"""
        return (
            f"📚 <b>{SCHOOL_NAME} - {GRADE}</b>\n"
            f"🤖 <b>TEACHER HELP MENU</b>\n\n"
            f"Welcome, @{username} 👨‍🏫\n\n"
            
            f"👨‍🏫 <b>ATTENDANCE COMMANDS:</b>\n"
            f"<code>/todayattendance</code> - Today's attendance\n"
            f"<code>/weeklyreport</code> - Weekly report\n"
            f"<code>/markabsent [reply]</code> - Mark student absent\n\n"
            
            f"📋 <b>PERSONAL COMMANDS:</b>\n"
            f"<code>/profile</code> - Your profile (auto-records attendance)\n"
            f"<code>/present</code> - Manually mark present\n"
            f"<code>/attendance</code> - View your attendance\n"
            f"<code>/rules</code> - School rules\n\n"
            
            f"💡 <b>ATTENDANCE SYSTEM:</b>\n"
            f"• /profile auto-records daily attendance\n"
            f"• Check /profile every day\n"
            f"• You can mark students absent\n"
            f"• View reports with /todayattendance\n\n"
            
            f"👮 <b>Need admin help?</b> Contact:\n"
            f"• @sh3ll_3xp10it\n• @dagi_tariku"
        )
    
    def _get_student_help(self):
        """Get student help"""
        return (
            f"📚 <b>{SCHOOL_NAME} - {GRADE}</b>\n"
            f"🤖 <b>ATTENDANCE BOT HELP</b>\n\n"
            
            f"📋 <b>ATTENDANCE COMMANDS:</b>\n"
            f"<code>/profile</code> - Your profile (⭐ AUTO-RECORDS ATTENDANCE ⭐)\n"
            f"<code>/present</code> - Manually mark present\n"
            f"<code>/attendance</code> - View your attendance record\n\n"
            
            f"🏫 <b>SCHOOL COMMANDS:</b>\n"
            f"<code>/rules</code> - School rules\n"
            f"<code>/help</code> - This menu\n\n"
            
            f"⭐ <b>IMPORTANT:</b>\n"
            f"• Use <code>/profile</code> EVERY DAY to mark attendance\n"
            f"• Your attendance is automatically recorded\n"
            f"• Check your record with <code>/attendance</code>\n"
            f"• Maintain good attendance for better grades\n\n"
            
            f"👮 <b>Need help?</b> Contact:\n"
            f"• @sh3ll_3xp10it\n• @dagi_tariku\n\n"
            
            f"🏫 <i>Education for Excellence</i>"
        )
    
    def _get_rules(self):
        """Get school rules"""
        return (
            f"📜 <b>{SCHOOL_NAME} - GRADE 8 RULES</b>\n\n"
            f"1. Respect teachers and classmates\n"
            f"2. No bullying or harassment\n"
            f"3. Complete assignments on time\n"
            f"4. Follow administrator instructions\n"
            f"5. <b>MARK ATTENDANCE DAILY using /profile</b>\n\n"
            f"⚖️ <b>DISCIPLINARY SYSTEM:</b>\n"
            f"• 3 warnings = 24h mute\n"
            f"• 4 warnings = Permanent ban\n"
            f"• Poor attendance = Parent notification\n\n"
            f"📋 <b>ATTENDANCE POLICY:</b>\n"
            f"• Use /profile daily to mark attendance\n"
            f"• 80%+ attendance required\n"
            f"• Teachers can mark you absent\n"
            f"• Check /attendance for your record\n\n"
            f"👮 <b>ADMINISTRATION:</b>\n"
            f"• @sh3ll_3xp10it (Super Admin)\n"
            f"• @dagi_tariku (Super Admin)\n\n"
            f"📚 <i>Education for Excellence</i>"
        )
    
    def run(self):
        """Run the bot"""
        print("\n✅ System Components:")
        print("   • User Manager: READY")
        print("   • Attendance System: ACTIVE")
        print("   • Command System: LOADED")
        print("\n⚡ Starting Attendance Bot...")
        print("=" * 60)
        print("Press Ctrl+C to stop the bot")
        print("=" * 60)
        
        try:
            self.bot.polling(none_stop=True, interval=1, timeout=30)
        except KeyboardInterrupt:
            print("\n👋 Bot stopped by user")
            print("💾 Saving attendance data...")
            self.attendance.save_attendance()
            print("✅ Shutdown complete!")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("💡 Check your internet connection")

# ===================== MAIN EXECUTION =====================
if __name__ == "__main__":
    # Install required package if needed
    try:
        import telebot
    except ImportError:
        print("📦 Installing pyTelegramBotAPI...")
        import subprocess
        subprocess.check_call(["pip", "install", "pyTelegramBotAPI"])
    
    # Create backup of existing files
    import shutil
    for file in [ADMINS_FILE, TEACHERS_FILE, ATTENDANCE_FILE]:
        if os.path.exists(file):
            shutil.copy2(file, f"{file}.backup")
    
    # Run the bot
    bot = AttendanceBot()
    bot.run()
