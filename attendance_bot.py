        # ========== IMPROVED: LIST STUDENTS COMMAND ==========
        @self.bot.message_handler(commands=['liststudents', 'students'])
        def list_students_handler(message):
            """List all students who have used the bot"""
            username = message.from_user.username
            
            if not (self.user_manager.is_admin(username) or self.user_manager.is_teacher(username)):
                self.bot.reply_to(message,
                    "🚫 <b>ACCESS DENIED</b>\n\n"
                    "Only teachers and administrators can view student list."
                )
                return
            
            # Get today's attendance
            today = datetime.now().strftime("%Y-%m-%d")
            today_attendance = self.attendance.get_daily_attendance(today)
            
            # Collect unique users from all attendance records
            all_users = {}
            for date, day_data in self.attendance.attendance.items():
                for user_id, user_data in day_data.items():
                    user_username = user_data.get('username', 'unknown')
                    if user_username not in all_users:
                        all_users[user_username] = user_data
            
            # Remove teachers and admins
            student_users = {}
            for username_key, user_data in all_users.items():
                if not (self.user_manager.is_admin(username_key) or 
                       self.user_manager.is_teacher(username_key) or
                       self.user_manager.is_super_admin(username_key)):
                    student_users[username_key] = user_data
            
            if not student_users:
                self.bot.reply_to(message, "📝 No students found in records.")
                return
            
            response = f"👥 <b>STUDENT LIST</b>\n"
            response += f"📅 Date: {today}\n"
            response += f"📊 Total Students: {len(student_users)}\n\n"
            
            # Today's attendance status
            present_today = []
            absent_today = []
            not_recorded = []
            
            for student_username, student_data in student_users.items():
                if today in self.attendance.attendance:
                    if student_username in [u.get('username') for u in self.attendance.attendance[today].values()]:
                        for user_id, user_data in self.attendance.attendance[today].items():
                            if user_data.get('username') == student_username:
                                if user_data.get('status') == 'present':
                                    present_today.append(f"✅ @{student_username}")
                                else:
                                    absent_today.append(f"❌ @{student_username}")
                                break
                    else:
                        not_recorded.append(f"⏳ @{student_username}")
                else:
                    not_recorded.append(f"⏳ @{student_username}")
            
            response += "<b>📊 TODAY'S STATUS:</b>\n"
            
            if present_today:
                response += "\n<b>✅ PRESENT:</b>\n"
                for student in present_today[:10]:
                    response += f"{student}\n"
                if len(present_today) > 10:
                    response += f"... and {len(present_today) - 10} more\n"
            
            if absent_today:
                response += "\n<b>❌ ABSENT:</b>\n"
                for student in absent_today[:10]:
                    response += f"{student}\n"
                if len(absent_today) > 10:
                    response += f"... and {len(absent_today) - 10} more\n"
            
            if not_recorded:
                response += "\n<b>⏳ NOT RECORDED:</b>\n"
                for student in not_recorded[:10]:
                    response += f"{student}\n"
                if len(not_recorded) > 10:
                    response += f"... and {len(not_recorded) - 10} more\n"
            
            response += "\n💡 <b>QUICK ACTIONS:</b>\n"
            response += "<code>/markabsent username</code> - Mark absent\n"
            response += "<code>/warn username reason</code> - Warn student\n"
            
            self.bot.reply_to(message, response)

        # ========== WARN SYSTEM COMMANDS ==========
        
        @self.bot.message_handler(commands=['warn'])
        def warn_handler(message):
            """Warn a student"""
            user = message.from_user
            username = user.username
            
            # Check permissions
            if not (self.user_manager.is_admin(username) or self.user_manager.is_teacher(username)):
                self.bot.reply_to(message,
                    "🚫 <b>ACCESS DENIED</b>\n\n"
                    "Only teachers and administrators can warn students."
                )
                return
            
            parts = message.text.split()
            if len(parts) < 3:
                self.bot.reply_to(message,
                    "⚠️ <b>WARN STUDENT</b>\n\n"
                    "⚠️ <b>Usage:</b> <code>/warn [username] [reason]</code>\n\n"
                    "<b>Examples:</b>\n"
                    "<code>/warn john_student Late submission</code>\n"
                    "<code>/warn jane_doe Missing assignments</code>\n"
                    "<code>/warn student123 Disruptive behavior</code>\n\n"
                    "💡 <b>Note:</b>\n"
                    "• Username without @ symbol\n"
                    "• Student will be auto-banned after 3 warnings\n"
                    "• Use /viewwarnings to check status"
                )
                return
            
            student_username = parts[1].replace("@", "")
            reason = " ".join(parts[2:])
            
            # Add warning
            success, result = self.user_manager.add_warning(student_username, reason, username)
            
            # Get updated warning info
            warnings_info = self.user_manager.get_warnings(student_username)
            
            response = f"⚠️ <b>WARNING ISSUED</b>\n\n"
            response += f"👨‍🎓 Student: @{student_username}\n"
            response += f"👨‍🏫 Warned by: @{username}\n"
            response += f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}\n"
            response += f"🕒 Time: {datetime.now().strftime('%H:%M:%S')}\n"
            response += f"📝 Reason: {reason}\n\n"
            
            if warnings_info:
                response += f"📊 <b>WARNING STATUS:</b>\n"
                response += f"• Total Warnings: {warnings_info['count']}/3\n"
                
                if warnings_info['count'] >= 3:
                    response += f"🚫 <b>STUDENT HAS BEEN BANNED!</b>\n"
                elif warnings_info['count'] == 2:
                    response += f"⚠️ <b>ALERT:</b> 1 more warning will result in ban!\n"
                elif warnings_info['count'] == 1:
                    response += f"⚠️ <b>ALERT:</b> 2 more warnings will result in ban!\n"
                
                response += f"\n📋 <b>WARNING HISTORY:</b>\n"
                for warning in warnings_info['warnings'][-3:]:  # Last 3 warnings
                    response += f"• #{warning['id']}: {warning['reason']} ({warning['date']})\n"
            
            self.bot.reply_to(message, response)
        
        @self.bot.message_handler(commands=['viewwarnings', 'checkwarnings'])
        def view_warnings_handler(message):
            """View warnings for a student"""
            user = message.from_user
            username = user.username
            
            # Check permissions
            if not (self.user_manager.is_admin(username) or self.user_manager.is_teacher(username)):
                self.bot.reply_to(message,
                    "🚫 <b>ACCESS DENIED</b>\n\n"
                    "Only teachers and administrators can view warnings."
                )
                return
            
            parts = message.text.split()
            if len(parts) < 2:
                self.bot.reply_to(message,
                    "📋 <b>VIEW WARNINGS</b>\n\n"
                    "⚠️ <b>Usage:</b> <code>/viewwarnings [username]</code>\n\n"
                    "<b>Examples:</b>\n"
                    "<code>/viewwarnings john_student</code>\n"
                    "<code>/checkwarnings jane_doe</code>\n\n"
                    "💡 <b>Note:</b> Username without @ symbol"
                )
                return
            
            student_username = parts[1].replace("@", "")
            warnings_info = self.user_manager.get_warnings(student_username)
            
            response = f"📋 <b>WARNINGS REPORT</b>\n\n"
            response += f"👨‍🎓 Student: @{student_username}\n"
            response += f"📅 Checked on: {datetime.now().strftime('%Y-%m-%d')}\n"
            response += f"👨‍🏫 Checked by: @{username}\n\n"
            
            if not warnings_info or warnings_info['count'] == 0:
                response += f"✅ <b>NO WARNINGS</b>\n\n"
                response += f"Student has a clean record."
            else:
                response += f"⚠️ <b>WARNING STATUS:</b>\n"
                response += f"• Total Warnings: {warnings_info['count']}/3\n"
                
                if warnings_info['banned']:
                    response += f"🚫 <b>STATUS: BANNED</b>\n"
                    response += f"• Ban Reason: {warnings_info['ban_reason']}\n"
                    response += f"• Banned by: {warnings_info['banned_by']}\n"
                    response += f"• Banned at: {warnings_info['banned_at']}\n"
                else:
                    status = "ACTIVE"
                    if warnings_info['count'] >= 3:
                        status = "PENDING BAN"
                    elif warnings_info['count'] == 2:
                        status = "HIGH RISK"
                    elif warnings_info['count'] == 1:
                        status = "LOW RISK"
                    response += f"• Status: {status}\n"
                
                response += f"\n📋 <b>WARNING HISTORY:</b>\n"
                for warning in warnings_info['warnings']:
                    response += f"\n<b>#{warning['id']}:</b>\n"
                    response += f"• Reason: {warning['reason']}\n"
                    response += f"• Date: {warning['date']}\n"
                    response += f"• Time: {warning['time']}\n"
                    response += f"• Warned by: {warning['warned_by']}\n"
                
                response += f"\n💡 <b>QUICK ACTIONS:</b>\n"
                response += f"<code>/removewarning {student_username} [id]</code> - Remove warning\n"
                if warnings_info['banned']:
                    response += f"<code>/unban {student_username}</code> - Unban student\n"
                else:
                    response += f"<code>/clearwarnings {student_username}</code> - Clear all warnings\n"
            
            self.bot.reply_to(message, response)
        
        @self.bot.message_handler(commands=['clearwarnings'])
        def clear_warnings_handler(message):
            """Clear all warnings for a student"""
            user = message.from_user
            username = user.username
            
            # Check permissions - only admins can clear warnings
            if not self.user_manager.is_admin(username):
                self.bot.reply_to(message,
                    "🚫 <b>ACCESS DENIED</b>\n\n"
                    "Only administrators can clear warnings."
                )
                return
            
            parts = message.text.split()
            if len(parts) < 2:
                self.bot.reply_to(message,
                    "🔄 <b>CLEAR WARNINGS</b>\n\n"
                    "⚠️ <b>Usage:</b> <code>/clearwarnings [username]</code>\n\n"
                    "<b>Examples:</b>\n"
                    "<code>/clearwarnings john_student</code>\n\n"
                    "💡 <b>Note:</b>\n"
                    "• Username without @ symbol\n"
                    "• This will remove ALL warnings and any active ban"
                )
                return
            
            student_username = parts[1].replace("@", "")
            success, result = self.user_manager.clear_warnings(student_username, username)
            
            if success:
                response = (
                    f"🔄 <b>WARNINGS CLEARED</b>\n\n"
                    f"👨‍🎓 Student: @{student_username}\n"
                    f"👨‍💼 Cleared by: @{username}\n"
                    f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}\n"
                    f"🕒 Time: {datetime.now().strftime('%H:%M:%S')}\n\n"
                    f"✅ All warnings have been removed.\n"
                    f"✅ Any active ban has been lifted.\n\n"
                    f"Student's record is now clean."
                )
            else:
                response = result
            
            self.bot.reply_to(message, response)
        
        @self.bot.message_handler(commands=['removewarning'])
        def remove_warning_handler(message):
            """Remove a specific warning"""
            user = message.from_user
            username = user.username
            
            # Check permissions - only admins can remove warnings
            if not self.user_manager.is_admin(username):
                self.bot.reply_to(message,
                    "🚫 <b>ACCESS DENIED</b>\n\n"
                    "Only administrators can remove warnings."
                )
                return
            
            parts = message.text.split()
            if len(parts) < 3:
                self.bot.reply_to(message,
                    "🗑️ <b>REMOVE WARNING</b>\n\n"
                    "⚠️ <b>Usage:</b> <code>/removewarning [username] [warning_id]</code>\n\n"
                    "<b>Examples:</b>\n"
                    "<code>/removewarning john_student 1</code>\n"
                    "<code>/removewarning jane_doe 2</code>\n\n"
                    "💡 <b>Note:</b>\n"
                    "• Username without @ symbol\n"
                    "• Use /viewwarnings to see warning IDs"
                )
                return
            
            student_username = parts[1].replace("@", "")
            warning_id = parts[2]
            
            success, result = self.user_manager.remove_warning(student_username, warning_id, username)
            
            if success:
                # Get updated warning info
                warnings_info = self.user_manager.get_warnings(student_username)
                
                response = (
                    f"🗑️ <b>WARNING REMOVED</b>\n\n"
                    f"👨‍🎓 Student: @{student_username}\n"
                    f"👨‍💼 Removed by: @{username}\n"
                    f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}\n"
                    f"🕒 Time: {datetime.now().strftime('%H:%M:%S')}\n"
                    f"🔢 Warning ID: #{warning_id}\n\n"
                )
                
                if warnings_info:
                    response += f"📊 <b>UPDATED STATUS:</b>\n"
                    response += f"• Total Warnings: {warnings_info['count']}/3\n"
                    
                    if warnings_info['banned']:
                        response += f"🚫 <b>STUDENT IS STILL BANNED</b>\n"
                        response += f"• Ban Reason: {warnings_info['ban_reason']}\n"
                    elif warnings_info['count'] >= 2:
                        response += f"⚠️ <b>ALERT:</b> {3 - warnings_info['count']} more warning(s) will result in ban!\n"
                    else:
                        response += f"✅ Warning count is now safe.\n"
                else:
                    response += f"✅ Student has no warnings remaining.\n"
            else:
                response = result
            
            self.bot.reply_to(message, response)

        # ========== BAN SYSTEM COMMANDS ==========
        
        @self.bot.message_handler(commands=['ban'])
        def ban_handler(message):
            """Ban a student immediately"""
            user = message.from_user
            username = user.username
            
            # Check permissions - only admins can ban
            if not self.user_manager.is_admin(username):
                self.bot.reply_to(message,
                    "🚫 <b>ACCESS DENIED</b>\n\n"
                    "Only administrators can ban students."
                )
                return
            
            parts = message.text.split()
            if len(parts) < 3:
                self.bot.reply_to(message,
                    "🚫 <b>BAN STUDENT</b>\n\n"
                    "⚠️ <b>Usage:</b> <code>/ban [username] [reason]</code>\n\n"
                    "<b>Examples:</b>\n"
                    "<code>/ban john_student Repeated violations</code>\n"
                    "<code>/ban jane_doe Severe misconduct</code>\n"
                    "<code>/ban student123 Academic dishonesty</code>\n\n"
                    "💡 <b>Note:</b>\n"
                    "• Username without @ symbol\n"
                    "• Student will be immediately blocked from bot\n"
                    "• Use /unban to remove ban"
                )
                return
            
            student_username = parts[1].replace("@", "")
            reason = " ".join(parts[2:])
            
            # Check if trying to ban admin/teacher
            if (self.user_manager.is_admin(student_username) or 
                self.user_manager.is_teacher(student_username) or
                self.user_manager.is_super_admin(student_username)):
                self.bot.reply_to(message,
                    "🚫 <b>CANNOT BAN ADMIN/TEACHER</b>\n\n"
                    "You cannot ban administrators or teachers.\n"
                    "Remove them from their role first."
                )
                return
            
            # Ban the user
            success, result = self.user_manager.ban_user(student_username, reason, username)
            
            response = (
                f"🚫 <b>STUDENT BANNED</b>\n\n"
                f"👨‍🎓 Student: @{student_username}\n"
                f"👨‍💼 Banned by: @{username}\n"
                f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}\n"
                f"🕒 Time: {datetime.now().strftime('%H:%M:%S')}\n"
                f"📝 Reason: {reason}\n\n"
                f"🔒 <b>EFFECTS:</b>\n"
                f"• Cannot use /profile or /start\n"
                f"• Cannot submit assignments\n"
                f"• Cannot check attendance\n"
                f"• All bot access blocked\n\n"
                f"💡 <b>To unban:</b>\n"
                f"<code>/unban {student_username}</code>"
            )
            
            self.bot.reply_to(message, response)
        
        @self.bot.message_handler(commands=['unban'])
        def unban_handler(message):
            """Unban a student"""
            user = message.from_user
            username = user.username
            
            # Check permissions - only admins can unban
            if not self.user_manager.is_admin(username):
                self.bot.reply_to(message,
                    "🚫 <b>ACCESS DENIED</b>\n\n"
                    "Only administrators can unban students."
                )
                return
            
            parts = message.text.split()
            if len(parts) < 2:
                self.bot.reply_to(message,
                    "🔓 <b>UNBAN STUDENT</b>\n\n"
                    "⚠️ <b>Usage:</b> <code>/unban [username]</code>\n\n"
                    "<b>Examples:</b>\n"
                    "<code>/unban john_student</code>\n"
                    "<code>/unban jane_doe</code>\n\n"
                    "💡 <b>Note:</b> Username without @ symbol"
                )
                return
            
            student_username = parts[1].replace("@", "")
            success, result = self.user_manager.unban_user(student_username, username)
            
            if success:
                response = (
                    f"🔓 <b>STUDENT UNBANNED</b>\n\n"
                    f"👨‍🎓 Student: @{student_username}\n"
                    f"👨‍💼 Unbanned by: @{username}\n"
                    f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}\n"
                    f"🕒 Time: {datetime.now().strftime('%H:%M:%S')}\n\n"
                    f"✅ <b>ACCESS RESTORED:</b>\n"
                    f"• Can use /profile again\n"
                    f"• Can submit assignments\n"
                    f"• Can check attendance\n"
                    f"• Full bot access restored\n\n"
                    f"⚠️ <b>Note:</b> Warnings are still on record\n"
                    f"Use /clearwarnings to remove all warnings"
                )
            else:
                response = result
            
            self.bot.reply_to(message, response)
        
        @self.bot.message_handler(commands=['bannedlist', 'bannedstudents'])
        def banned_list_handler(message):
            """List all banned students"""
            user = message.from_user
            username = user.username
            
            # Check permissions - only admins
            if not self.user_manager.is_admin(username):
                self.bot.reply_to(message,
                    "🚫 <b>ACCESS DENIED</b>\n\n"
                    "Only administrators can view banned list."
                )
                return
            
            # Find all banned students
            banned_students = []
            for student_username, warnings_info in self.user_manager.warnings.items():
                if warnings_info.get('banned', False):
                    banned_students.append({
                        'username': student_username,
                        'ban_reason': warnings_info.get('ban_reason', 'No reason'),
                        'banned_by': warnings_info.get('banned_by', 'Unknown'),
                        'banned_at': warnings_info.get('banned_at', 'Unknown'),
                        'warning_count': warnings_info.get('count', 0)
                    })
            
            if not banned_students:
                self.bot.reply_to(message,
                    "✅ <b>NO BANNED STUDENTS</b>\n\n"
                    "There are currently no banned students."
                )
                return
            
            response = f"🚫 <b>BANNED STUDENTS LIST</b>\n\n"
            response += f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}\n"
            response += f"📊 Total Banned: {len(banned_students)}\n\n"
            
            for i, student in enumerate(banned_students, 1):
                response += f"<b>{i}. @{student['username']}</b>\n"
                response += f"• Reason: {student['ban_reason'][:50]}...\n"
                response += f"• Banned by: {student['banned_by']}\n"
                response += f"• Date: {student['banned_at']}\n"
                response += f"• Warnings: {student['warning_count']}/3\n\n"
            
            response += f"💡 <b>QUICK ACTIONS:</b>\n"
            for student in banned_students[:3]:  # Show first 3
                response += f"<code>/unban {student['username']}</code>\n"
            
            if len(banned_students) > 3:
                response += f"... and {len(banned_students) - 3} more\n"
            
            self.bot.reply_to(message, response)

        # ========== ASSIGNMENT SYSTEM COMMANDS ==========
        
        @self.bot.message_handler(commands=['assign', 'createassignment'])
        def assign_handler(message):
            """Create a new assignment"""
            user = message.from_user
            username = user.username
            
            if not (self.user_manager.is_admin(username) or self.user_manager.is_teacher(username)):
                self.bot.reply_to(message,
                    "🚫 <b>ACCESS DENIED</b>\n\n"
                    "Only teachers and administrators can create assignments."
                )
                return
            
            parts = message.text.split()
            if len(parts) < 4:
                self.bot.reply_to(message,
                    "📚 <b>CREATE ASSIGNMENT</b>\n\n"
                    "⚠️ <b>Usage:</b> <code>/assign [subject] [title] [description]</code>\n\n"
                    "<b>Example:</b>\n"
                    "<code>/assign Math \"Algebra Homework\" \"Complete exercises 1-10 on page 45\"</code>\n\n"
                    "💡 <b>Note:</b>\n"
                    "• Subject: Math, Science, English, etc.\n"
                    "• Title in quotes for multi-word titles\n"
                    "• Due date will be set to 7 days from now"
                )
                return
            
            subject = parts[1]
            title = parts[2].replace('"', '') if parts[2].startswith('"') else parts[2]
            description = " ".join(parts[3:])
            
            # Set due date to 7 days from now
            due_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
            
            # Create assignment
            assignment_id, assignment = self.assignments.create_assignment(
                user.id,
                username,
                subject,
                title,
                description,
                due_date
            )
            
            response = (
                f"📚 <b>NEW ASSIGNMENT CREATED</b>\n\n"
                f"📝 <b>DETAILS:</b>\n"
                f"• ID: <code>{assignment_id}</code>\n"
                f"• Subject: {subject}\n"
                f"• Title: {title}\n"
                f"• Description: {description}\n"
                f"• Due Date: {due_date}\n"
                f"• Created by: @{username}\n\n"
                f"👨‍🎓 <b>FOR STUDENTS:</b>\n"
                f"• Use <code>/receive {assignment_id}</code> to receive assignment\n"
                f"• Use <code>/submit {assignment_id} [your_work]</code> to submit\n\n"
                f"👨‍🏫 <b>FOR TEACHERS:</b>\n"
                f"• Use <code>/inbox</code> to view submissions\n"
                f"• Use <code>/grade {assignment_id} [student_id] [grade]</code> to grade"
            )
            
            self.bot.reply_to(message, response)

        # ========== HELPER METHODS ==========
    
    def _get_admin_help(self, username):
        """Get help for admins"""
        response = (
            f"👑 <b>ADMIN COMMANDS</b>\n"
            f"🏫 {SCHOOL_NAME} - {GRADE}\n\n"
            
            f"📊 <b>USER MANAGEMENT:</b>\n"
            f"<code>/addadmin [username]</code> - Add admin\n"
            f"<code>/removeadmin [username]</code> - Remove admin\n"
            f"<code>/addteacher [username]</code> - Add teacher\n"
            f"<code>/removeteacher [username]</code> - Remove teacher\n"
            f"<code>/listadmins</code> - List all admins\n"
            f"<code>/listteachers</code> - List all teachers\n\n"
            
            f"🚫 <b>WARNING & BAN SYSTEM:</b>\n"
            f"<code>/warn [username] [reason]</code> - Warn student\n"
            f"<code>/viewwarnings [username]</code> - View warnings\n"
            f"<code>/clearwarnings [username]</code> - Clear all warnings\n"
            f"<code>/removewarning [username] [id]</code> - Remove warning\n"
            f"<code>/ban [username] [reason]</code> - Ban student\n"
            f"<code>/unban [username]</code> - Unban student\n"
            f"<code>/bannedlist</code> - List banned students\n\n"
            
            f"👨‍🏫 <b>TEACHER COMMANDS:</b>\n"
            f"<code>/markabsent [username]</code> - Mark absent\n"
            f"<code>/liststudents</code> - View all students\n"
            f"<code>/assign [subject] [title]</code> - Create assignment\n"
            f"<code>/inbox</code> - View submissions\n"
            f"<code>/grade [id] [student] [grade]</code> - Grade\n"
            f"<code>/assignmentstats</code> - View stats\n\n"
            
            f"👨‍🎓 <b>STUDENT COMMANDS:</b>\n"
            f"<code>/profile</code> - Your profile\n"
            f"<code>/attendance</code> - Your attendance\n"
            f"<code>/assignments</code> - Your assignments\n"
            f"<code>/submit</code> - Submit work\n"
            f"<code>/grades</code> - Your grades\n\n"
            
            f"📋 <b>SYSTEM COMMANDS:</b>\n"
            f"<code>/rules</code> - School rules\n"
            f"<code>/about</code> - About bot\n"
            f"<code>/help</code> - This menu\n\n"
            
            f"👮 <b>Super Admins:</b> @sh3ll_3xp10it, @dagi_tariku"
        )
        return response
    
    def _get_teacher_help(self, username):
        """Get help for teachers"""
        response = (
            f"👨‍🏫 <b>TEACHER COMMANDS</b>\n"
            f"🏫 {SCHOOL_NAME} - {GRADE}\n\n"
            
            f"📝 <b>ATTENDANCE:</b>\n"
            f"<code>/markabsent [username]</code> - Mark student absent\n"
            f"<code>/liststudents</code> - View all students\n"
            f"<code>/attendance [date]</code> - View attendance\n\n"
            
            f"📚 <b>ASSIGNMENTS:</b>\n"
            f"<code>/assign [subject] [title]</code> - Create assignment\n"
            f"<code>/inbox</code> - View submissions\n"
            f"<code>/grade [id] [student] [grade]</code> - Grade assignment\n"
            f"<code>/assignmentstats</code> - View statistics\n\n"
            
            f"⚠️ <b>DISCIPLINE:</b>\n"
            f"<code>/warn [username] [reason]</code> - Warn student\n"
            f"<code>/viewwarnings [username]</code> - Check warnings\n\n"
            
            f"👨‍🎓 <b>STUDENT COMMANDS:</b>\n"
            f"<code>/profile</code> - Your profile\n"
            f"<code>/attendance</code> - Your attendance\n"
            f"<code>/assignments</code> - Your assignments\n"
            f"<code>/submit</code> - Submit work\n"
            f"<code>/grades</code> - Your grades\n\n"
            
            f"📋 <b>SYSTEM COMMANDS:</b>\n"
            f"<code>/rules</code> - School rules\n"
            f"<code>/about</code> - About bot\n"
            f"<code>/help</code> - This menu\n\n"
            
            f"👮 <b>Admins:</b> Contact @sh3ll_3xp10it or @dagi_tariku"
        )
        return response
    
    def _get_student_help(self):
        """Get help for students"""
        response = (
            f"👨‍🎓 <b>STUDENT COMMANDS</b>\n"
            f"🏫 {SCHOOL_NAME} - {GRADE}\n\n"
            
            f"✅ <b>ATTENDANCE:</b>\n"
            f"<code>/profile</code> - Auto-mark present & view profile\n"
            f"<code>/attendance</code> - View your attendance record\n\n"
            
            f"📚 <b>ASSIGNMENTS:</b>\n"
            f"<code>/assignments</code> - View your assignments\n"
            f"<code>/receive [id]</code> - Receive an assignment\n"
            f"<code>/submit [id] [work]</code> - Submit assignment\n"
            f"<code>/grades</code> - View your grades\n\n"
            
            f"📋 <b>SYSTEM COMMANDS:</b>\n"
            f"<code>/rules</code> - School rules\n"
            f"<code>/about</code> - About the bot\n"
            f"<code>/help</code> - This menu\n\n"
            
            f"💡 <b>IMPORTANT:</b>\n"
            f"• Use /profile daily to mark attendance\n"
            f"• Submit assignments before due date\n"
            f"• Check /grades regularly\n\n"
            
            f"👮 <b>Contact Teachers:</b> Use username mentions"
        )
        return response
    
    def _get_rules(self):
        """Get school rules"""
        rules = (
            f"📜 <b>SCHOOL RULES & GUIDELINES</b>\n"
            f"🏫 {SCHOOL_NAME} - {GRADE}\n\n"
            
            f"✅ <b>ATTENDANCE POLICY:</b>\n"
            f"1. Use /profile daily to mark attendance\n"
            f"2. Attendance is auto-recorded at 00:00-23:59\n"
            f"3. Late attendance may be marked absent\n"
            f"4. Contact teacher if marked absent by mistake\n\n"
            
            f"📚 <b>ASSIGNMENT POLICY:</b>\n"
            f"1. Receive assignments using /receive [id]\n"
            f"2. Submit before due date\n"
            f"3. Late submissions may receive penalty\n"
            f"4. Plagiarism is strictly prohibited\n\n"
            
            f"⚠️ <b>CODE OF CONDUCT:</b>\n"
            f"1. Respect all teachers and students\n"
            f"2. No spam or inappropriate content\n"
            f"3. 3 warnings = automatic ban\n"
            f"4. Serious offenses = immediate ban\n\n"
            
            f"🚫 <b>GROUNDS FOR WARNING/BAN:</b>\n"
            f"• Missing multiple assignments\n"
            f"• Disruptive behavior\n"
            f"• Academic dishonesty\n"
            f"• Harassment or bullying\n"
            f"• Spamming the bot\n\n"
            
            f"📞 <b>CONTACT:</b>\n"
            f"👑 Super Admins: @sh3ll_3xp10it, @dagi_tariku\n"
            f"📧 Email: administration@aspire.edu"
        )
        return rules
    
    def run(self):
        """Start the bot"""
        print("🤖 Bot is running...")
        print("🔄 Waiting for messages...")
        self.bot.infinity_polling()

# ===================== MAIN EXECUTION =====================
if __name__ == "__main__":
    # Create necessary files if they don't exist
    for file in [ADMINS_FILE, TEACHERS_FILE, ATTENDANCE_FILE, 
                 ASSIGNMENTS_FILE, SUBMISSIONS_FILE, WARNINGS_FILE]:
        if not os.path.exists(file):
            with open(file, 'w') as f:
                json.dump({} if "warnings" in file else [], f)
    
    # Start the bot
    bot = AssignmentBot()
    bot.run()
