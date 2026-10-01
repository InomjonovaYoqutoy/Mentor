"""Lightweight localization and region helpers for Mentor.

Mentor keeps database enum values in English for compatibility.  The UI translates
those values at the boundary so switching language never mutates user data.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

try:
    from PySide6.QtCore import QDate, QLocale
except ModuleNotFoundError:  # lets database-only tests import helpers without Qt
    QDate = None  # type: ignore[assignment]
    QLocale = None  # type: ignore[assignment]


LANGUAGES = {
    "en": "English",
    "uz": "O‘zbekcha",
    "ru": "Русский",
}

_current_language = "en"
_time_24h = True
_week_start = "monday"

# English source strings are intentionally the keys.  It keeps call sites readable
# while the catalog stays centralized and testable.
UZ = {
    "Home": "Bosh sahifa", "Schedule": "Jadval", "Notes": "Qaydlar", "Materials": "Materiallar", "Stats": "Statistika",
    "Settings": "Sozlamalar", "General": "Umumiy", "Appearance": "Ko‘rinish", "Language & Region": "Til va hudud",
    "Notifications": "Bildirishnomalar", "Data & Backup": "Ma’lumotlar va zaxira", "About": "Dastur haqida",
    "Personalize Mentor and keep your local data safe.": "Mentorni o‘zingizga moslang va mahalliy ma’lumotlaringizni xavfsiz saqlang.",
    "Display name": "Ko‘rinadigan ism", "Enable in-app reminders": "Dastur ichidagi eslatmalarni yoqish", "Language": "Til",
    "Accent": "Aksent", "Glass intensity": "Shisha effekti", "Motion": "Animatsiya", "Interface density": "Interfeys zichligi",
    "Atmospheric glow": "Fon nuri", "Time format": "Vaqt formati", "Week starts on": "Hafta boshlanishi", "Default schedule view": "Standart jadval ko‘rinishi",
    "Standard": "Standart", "Subtle": "Yengil", "Strong": "Kuchli", "Full": "To‘liq", "Reduced": "Kamaytirilgan", "Off": "O‘chiq",
    "Comfortable": "Qulay", "Compact": "Ixcham", "Monday": "Dushanba", "Sunday": "Yakshanba", "Day": "Kun", "Week": "Hafta",
    "Mentor Orange": "Mentor to‘q sariq", "Warm Amber": "Iliq amber", "Graphite": "Grafit", "Deep Blue": "Chuqur ko‘k", "Violet": "Binafsha",
    "Save Settings": "Sozlamalarni saqlash", "Backup": "Zaxira nusxa", "Restore": "Tiklash", "Export JSON": "JSON eksport", "Students CSV": "Talabalar CSV",
    "App version": "Dastur versiyasi", "Database schema": "Baza sxemasi", "App data": "Dastur ma’lumotlari", "Local-first teaching productivity for Windows.": "Windows uchun mahalliy ishlaydigan o‘qituvchi yordamchisi.",
    "Better planning. Better teaching. Better results.": "Yaxshi reja. Yaxshi dars. Yaxshi natija.",
    "“Progress isn’t about being perfect,\nit’s about being consistent.”": "“Taraqqiyot mukammallik emas,\nbalki izchillikdir.”",
    "Total Students": "Jami talabalar", "Upcoming Lessons": "Yaqin darslar", "Tasks Due": "Vazifalar", "Goals Progress": "Maqsadlar",
    "Today's Schedule": "Bugungi jadval", "View all": "Barchasini ko‘rish", "Quick Actions": "Tezkor amallar", "Recent Activity": "So‘nggi faollik",
    "Homework & Assignments": "Uy vazifalari", "Add Lesson": "Dars qo‘shish", "Add Note": "Qayd qo‘shish", "Homework": "Uy vazifasi", "Add Material": "Material qo‘shish",
    "Add Student": "Talaba qo‘shish", "New Task": "Yangi vazifa", "Active learners": "Faol o‘quvchilar", "Nothing scheduled": "Reja yo‘q",
    "Need attention": "E’tibor kerak", "You're clear": "Hammasi joyida", "Across active goals": "Faol maqsadlar bo‘yicha", "this week": "shu hafta",
    "No lessons today": "Bugun dars yo‘q", "Your schedule is clear.": "Jadvalingiz bo‘sh.", "Schedule a lesson": "Dars rejalashtirish",
    "No recent activity yet.": "Hozircha faollik yo‘q.", "No homework due soon.": "Yaqin muddatli uy vazifasi yo‘q.", "View homework": "Uy vazifalarini ko‘rish",
    "Good morning": "Xayrli tong", "Good afternoon": "Xayrli kun", "Good evening": "Xayrli kech",
    "MENTOR INSIGHT": "MENTOR MASLAHATI", "A good teacher\ncan change the world\none student at a time.": "Yaxshi ustoz\ndunyoni o‘zgartiradi —\nbir o‘quvchidan boshlab.",
    "New Lesson": "Yangi dars", "New Student": "Yangi talaba", "New Note": "Yangi qayd", "Assign Homework": "Uy vazifa berish", "New Goal": "Yangi maqsad",
    "Focus Timer": "Fokus taymeri", "QUICK CREATE": "TEZKOR YARATISH", "Open Lesson": "Darsni ochish", "Complete / Wrap Up": "Darsni yakunlash",
    "Duplicate": "Nusxalash", "Cancel Lesson": "Darsni bekor qilish", "Delete": "O‘chirish", "Needs review": "Ko‘rib chiqish kerak", "REVIEW": "TEKSHIRISH", "LIVE": "JONLI",
    "Unassigned": "Biriktirilmagan", "Lesson": "Dars", "Review": "Takrorlash", "Consultation": "Maslahat", "Exam Prep": "Imtihonga tayyorgarlik", "Assessment": "Baholash",
    "Upcoming": "Kutilmoqda", "In Progress": "Jarayonda", "Completed": "Yakunlangan", "Cancelled": "Bekor qilingan",
    "Not marked": "Belgilanmagan", "Present": "Qatnashdi", "Late": "Kechikdi", "Absent": "Qatnashmadi", "Excused": "Sababli",
    "Active": "Faol", "Inactive": "Nofaol", "Archived": "Arxivlangan", "None": "Yo‘q", "Every day": "Har kuni", "Every week": "Har hafta", "Every 2 weeks": "Har 2 haftada",
    "Assigned": "Berilgan", "Submitted": "Topshirilgan", "Skipped": "O‘tkazib yuborilgan", "Low": "Past", "Medium": "O‘rta", "High": "Yuqori",
    "Search Mentor": "Mentorda qidirish", "Search Mentor…": "Mentorda qidirish…", "Search": "Qidirish", "Close": "Yopish", "Cancel": "Bekor qilish", "Save": "Saqlash", "Edit": "Tahrirlash",
    "Profile and settings": "Profil va sozlamalar", "Quick create (Ctrl+N)": "Tezkor yaratish (Ctrl+N)", "Search Mentor (Ctrl+K)": "Mentorda qidirish (Ctrl+K)", "Upcoming reminders": "Yaqin eslatmalar",
    "About Mentor": "Mentor haqida", "Backup & Data": "Zaxira va ma’lumotlar", "Quit": "Chiqish",
    "Welcome to Mentor": "Mentorga xush kelibsiz", "Your teaching, organized.": "Darslaringiz — tartibda.", "Start Empty": "Bo‘sh boshlash", "Load Sample Workspace": "Namuna yuklash",
    "Sample workspace loaded": "Namuna muhiti yuklandi", "Settings saved": "Sozlamalar saqlandi", "Note saved": "Qayd saqlandi", "Student added": "Talaba qo‘shildi",
    "Task created": "Vazifa yaratildi", "Homework assigned": "Uy vazifasi berildi", "Homework saved": "Uy vazifasi saqlandi", "Goal created": "Maqsad yaratildi", "Lesson completed": "Dars yakunlandi",
    "Lesson duplicated": "Dars nusxalandi", "Lesson saved": "Dars saqlandi", "Lesson scheduled": "Dars rejalashtirildi",
    "Upcoming lessons": "Yaqin darslar", "No lessons in the next 3 hours.": "Keyingi 3 soatda dars yo‘q.", "Coming up:": "Yaqinlashmoqda:", "starts in": "boshlanishiga",
    "Add Student": "Talaba qo‘shish", "Edit Student": "Talabani tahrirlash", "New student": "Yangi talaba", "Edit student": "Talabani tahrirlash",
    "Keep only the details that are actually useful to you.": "Faqat sizga foydali ma’lumotlarni saqlang.", "Student name": "Talaba ismi", "Optional": "Ixtiyoriy", "Primary subject": "Asosiy fan",
    "Phone, Telegram, email…": "Telefon, Telegram, email…", "Optional student notes": "Ixtiyoriy qaydlar", "Full name": "To‘liq ism", "Age": "Yosh", "Class / grade": "Sinf", "Subject": "Fan", "Contact": "Aloqa", "Status": "Holat",
    "Schedule Lesson": "Dars rejalashtirish", "Edit Lesson": "Darsni tahrirlash", "Edit lesson": "Darsni tahrirlash", "Choose who, when, and where. Mentor will warn you about overlaps before saving.": "Kim, qachon va qayerda ekanini tanlang. Mentor vaqt to‘qnashuvlarini saqlashdan oldin ko‘rsatadi.",
    "Lesson template": "Dars shabloni", "Start fresh": "Yangidan boshlash", "Save current as template": "Shablon sifatida saqlash", "Student": "Talaba", "Type": "Turi", "Date": "Sana", "Start": "Boshlanish", "End": "Tugash", "Length": "Davomiylik",
    "Attendance": "Davomat", "Location": "Joy", "Meeting link": "Uchrashuv havolasi", "Repeat": "Takrorlash", "Series": "Seriya", "Reminder": "Eslatma", "Notes": "Qaydlar",
    "Classroom, address, or Online": "Xona, manzil yoki Onlayn", "Optional meeting link": "Ixtiyoriy uchrashuv havolasi", "Preparation notes, homework, lesson focus…": "Tayyorgarlik, uy vazifasi, dars mavzusi…",
    "Save Changes": "O‘zgarishlarni saqlash", "Missing subject": "Fan kiritilmagan", "Add a subject before scheduling the lesson.": "Darsni rejalashtirishdan oldin fan kiriting.", "Invalid time": "Vaqt noto‘g‘ri", "End time must be later than start time.": "Tugash vaqti boshlanish vaqtidan keyin bo‘lishi kerak.", "Schedule overlap": "Jadval to‘qnashuvi", "Schedule it anyway?": "Baribir rejalashtirilsinmi?",
    "Students": "Talabalar", "Tasks": "Vazifalar", "Goals": "Maqsadlar", "Statistics": "Statistika", "Homework": "Uy vazifasi",
    "Today": "Bugun", "Open student profile": "Talaba profilini ochish", "Saved immediately": "Darhol saqlanadi", "Assign a student to track attendance": "Davomat uchun talaba biriktiring",
    "Lesson notes": "Dars qaydlari", "No lesson notes yet.": "Hozircha dars qaydi yo‘q.", "Homework from this lesson": "Shu darsdan uy vazifasi", "Nothing assigned from this lesson yet.": "Bu darsdan hali uy vazifasi berilmagan.",
    "Review Completion": "Yakunlashni ko‘rish", "Complete Lesson": "Darsni yakunlash", "Open meeting link": "Uchrashuv havolasini ochish",
    "Focus": "Fokus", "Start": "Boshlash", "Pause": "Pauza", "Reset": "Qayta boshlash",
    "Only this lesson": "Faqat shu dars", "This and future lessons": "Shu va keyingi darslar", "Entire series": "Butun seriya",
    "Russian": "Ruscha", "Uzbek": "O‘zbekcha", "English": "Inglizcha",
}

RU = {
    "Home": "Главная", "Schedule": "Расписание", "Notes": "Заметки", "Materials": "Материалы", "Stats": "Статистика",
    "Settings": "Настройки", "General": "Основные", "Appearance": "Оформление", "Language & Region": "Язык и регион",
    "Notifications": "Уведомления", "Data & Backup": "Данные и резервные копии", "About": "О приложении",
    "Personalize Mentor and keep your local data safe.": "Настройте Mentor под себя и храните локальные данные безопасно.",
    "Display name": "Отображаемое имя", "Enable in-app reminders": "Включить напоминания в приложении", "Language": "Язык",
    "Accent": "Акцент", "Glass intensity": "Интенсивность стекла", "Motion": "Анимации", "Interface density": "Плотность интерфейса",
    "Atmospheric glow": "Фоновое свечение", "Time format": "Формат времени", "Week starts on": "Начало недели", "Default schedule view": "Вид расписания по умолчанию",
    "Standard": "Стандарт", "Subtle": "Лёгкое", "Strong": "Сильное", "Full": "Полные", "Reduced": "Уменьшенные", "Off": "Выкл.",
    "Comfortable": "Комфортный", "Compact": "Компактный", "Monday": "Понедельник", "Sunday": "Воскресенье", "Day": "День", "Week": "Неделя",
    "Mentor Orange": "Mentor Orange", "Warm Amber": "Тёплый янтарь", "Graphite": "Графит", "Deep Blue": "Глубокий синий", "Violet": "Фиолетовый",
    "Save Settings": "Сохранить настройки", "Backup": "Резервная копия", "Restore": "Восстановить", "Export JSON": "Экспорт JSON", "Students CSV": "CSV учеников",
    "App version": "Версия приложения", "Database schema": "Схема базы", "App data": "Данные приложения", "Local-first teaching productivity for Windows.": "Локальный помощник преподавателя для Windows.",
    "Better planning. Better teaching. Better results.": "Лучше планирование. Лучше обучение. Лучше результаты.",
    "“Progress isn’t about being perfect,\nit’s about being consistent.”": "«Прогресс — не идеальность,\nа постоянство.»",
    "Total Students": "Всего учеников", "Upcoming Lessons": "Ближайшие уроки", "Tasks Due": "Задачи", "Goals Progress": "Цели",
    "Today's Schedule": "Расписание на сегодня", "View all": "Показать все", "Quick Actions": "Быстрые действия", "Recent Activity": "Недавняя активность",
    "Homework & Assignments": "Домашние задания", "Add Lesson": "Добавить урок", "Add Note": "Добавить заметку", "Homework": "Домашнее задание", "Add Material": "Добавить материал",
    "Add Student": "Добавить ученика", "New Task": "Новая задача", "Active learners": "Активные ученики", "Nothing scheduled": "Ничего не запланировано",
    "Need attention": "Требует внимания", "You're clear": "Всё чисто", "Across active goals": "По активным целям", "this week": "на этой неделе",
    "No lessons today": "Сегодня уроков нет", "Your schedule is clear.": "Расписание свободно.", "Schedule a lesson": "Запланировать урок",
    "No recent activity yet.": "Пока нет недавней активности.", "No homework due soon.": "Скоро нет домашних заданий.", "View homework": "Открыть домашние задания",
    "Good morning": "Доброе утро", "Good afternoon": "Добрый день", "Good evening": "Добрый вечер",
    "MENTOR INSIGHT": "СОВЕТ MENTOR", "A good teacher\ncan change the world\none student at a time.": "Хороший учитель\nменяет мир —\nпо одному ученику.",
    "New Lesson": "Новый урок", "New Student": "Новый ученик", "New Note": "Новая заметка", "Assign Homework": "Задать домашнее", "New Goal": "Новая цель",
    "Focus Timer": "Таймер фокуса", "QUICK CREATE": "БЫСТРОЕ СОЗДАНИЕ", "Open Lesson": "Открыть урок", "Complete / Wrap Up": "Завершить урок",
    "Duplicate": "Дублировать", "Cancel Lesson": "Отменить урок", "Delete": "Удалить", "Needs review": "Нужно проверить", "REVIEW": "ПРОВЕРИТЬ", "LIVE": "ИДЁТ",
    "Unassigned": "Не назначено", "Lesson": "Урок", "Review": "Повторение", "Consultation": "Консультация", "Exam Prep": "Подготовка к экзамену", "Assessment": "Проверка",
    "Upcoming": "Предстоящий", "In Progress": "Идёт", "Completed": "Завершён", "Cancelled": "Отменён",
    "Not marked": "Не отмечено", "Present": "Присутствовал", "Late": "Опоздал", "Absent": "Отсутствовал", "Excused": "Уважительная причина",
    "Active": "Активен", "Inactive": "Неактивен", "Archived": "В архиве", "None": "Нет", "Every day": "Каждый день", "Every week": "Каждую неделю", "Every 2 weeks": "Раз в 2 недели",
    "Assigned": "Назначено", "Submitted": "Сдано", "Skipped": "Пропущено", "Low": "Низкий", "Medium": "Средний", "High": "Высокий",
    "Search Mentor": "Поиск в Mentor", "Search Mentor…": "Поиск в Mentor…", "Search": "Поиск", "Close": "Закрыть", "Cancel": "Отмена", "Save": "Сохранить", "Edit": "Изменить",
    "Profile and settings": "Профиль и настройки", "Quick create (Ctrl+N)": "Быстрое создание (Ctrl+N)", "Search Mentor (Ctrl+K)": "Поиск в Mentor (Ctrl+K)", "Upcoming reminders": "Ближайшие напоминания",
    "About Mentor": "О Mentor", "Backup & Data": "Резервные копии и данные", "Quit": "Выйти",
    "Welcome to Mentor": "Добро пожаловать в Mentor", "Your teaching, organized.": "Ваше преподавание — в порядке.", "Start Empty": "Начать с пустого", "Load Sample Workspace": "Загрузить пример",
    "Sample workspace loaded": "Пример загружен", "Settings saved": "Настройки сохранены", "Note saved": "Заметка сохранена", "Student added": "Ученик добавлен",
    "Task created": "Задача создана", "Homework assigned": "Домашнее задание назначено", "Homework saved": "Домашнее задание сохранено", "Goal created": "Цель создана", "Lesson completed": "Урок завершён",
    "Lesson duplicated": "Урок дублирован", "Lesson saved": "Урок сохранён", "Lesson scheduled": "Урок запланирован",
    "Upcoming lessons": "Ближайшие уроки", "No lessons in the next 3 hours.": "В ближайшие 3 часа уроков нет.", "Coming up:": "Скоро:", "starts in": "начнётся через",
    "Edit Student": "Изменить ученика", "New student": "Новый ученик", "Edit student": "Изменить ученика", "Keep only the details that are actually useful to you.": "Храните только действительно полезные данные.",
    "Student name": "Имя ученика", "Optional": "Необязательно", "Primary subject": "Основной предмет", "Phone, Telegram, email…": "Телефон, Telegram, email…", "Optional student notes": "Необязательные заметки",
    "Full name": "Полное имя", "Age": "Возраст", "Class / grade": "Класс", "Subject": "Предмет", "Contact": "Контакт", "Status": "Статус",
    "Schedule Lesson": "Запланировать урок", "Edit Lesson": "Изменить урок", "Edit lesson": "Изменить урок", "Choose who, when, and where. Mentor will warn you about overlaps before saving.": "Выберите ученика, время и место. Mentor предупредит о пересечениях до сохранения.",
    "Lesson template": "Шаблон урока", "Start fresh": "Начать с нуля", "Save current as template": "Сохранить как шаблон", "Student": "Ученик", "Type": "Тип", "Date": "Дата", "Start": "Начало", "End": "Конец", "Length": "Длительность",
    "Attendance": "Посещаемость", "Location": "Место", "Meeting link": "Ссылка на встречу", "Repeat": "Повтор", "Series": "Серия", "Reminder": "Напоминание", "Notes": "Заметки",
    "Classroom, address, or Online": "Кабинет, адрес или Онлайн", "Optional meeting link": "Необязательная ссылка", "Preparation notes, homework, lesson focus…": "Подготовка, домашнее задание, фокус урока…",
    "Save Changes": "Сохранить изменения", "Missing subject": "Нет предмета", "Add a subject before scheduling the lesson.": "Укажите предмет перед сохранением урока.", "Invalid time": "Неверное время", "End time must be later than start time.": "Время окончания должно быть позже начала.", "Schedule overlap": "Пересечение расписания", "Schedule it anyway?": "Всё равно запланировать?",
    "Students": "Ученики", "Tasks": "Задачи", "Goals": "Цели", "Statistics": "Статистика",
    "Today": "Сегодня", "Open student profile": "Открыть профиль ученика", "Saved immediately": "Сохраняется сразу", "Assign a student to track attendance": "Назначьте ученика для учёта посещаемости",
    "Lesson notes": "Заметки урока", "No lesson notes yet.": "Заметок к уроку пока нет.", "Homework from this lesson": "Домашнее задание с урока", "Nothing assigned from this lesson yet.": "С этого урока ничего не задано.",
    "Review Completion": "Проверить завершение", "Complete Lesson": "Завершить урок", "Open meeting link": "Открыть ссылку встречи",
    "Focus": "Фокус", "Start": "Старт", "Pause": "Пауза", "Reset": "Сброс",
    "Only this lesson": "Только этот урок", "This and future lessons": "Этот и будущие уроки", "Entire series": "Вся серия",
    "Russian": "Русский", "Uzbek": "Узбекский", "English": "Английский",
}

# Extended 1.4 localization coverage.
UZ.update({'A quiet timer for lesson prep, marking, or planning.': 'Darsga tayyorgarlik, tekshirish yoki rejalash uchun sokin taymer.', 'A quiet workspace for teaching notes and ideas.': 'Dars qaydlari va g‘oyalar uchun sokin ish maydoni.', 'Add': 'Qo‘shish', 'Add a homework title or turn off homework for this lesson.': 'Uy vazifasiga nom bering yoki bu dars uchun uy vazifasini o‘chirib qo‘ying.', 'Add a subject before saving this lesson as a template.': 'Darsni shablon sifatida saqlashdan oldin fan kiriting.', 'Add teaching material': 'O‘quv materialini qo‘shish', 'All time': 'Barcha vaqt', 'Assign homework': 'Uy vazifa berish', 'Assign homework before finishing': 'Yakunlashdan oldin uy vazifa berish', 'Attendance is only used when a student is assigned to this lesson.': 'Davomat faqat darsga o‘quvchi biriktirilganda ishlatiladi.', 'Attendance not saved': 'Davomat saqlanmadi', 'Available': 'Mavjud', 'Browse…': 'Tanlash…', 'Category': 'Toifa', 'Choose exactly how much of this series should change.': 'Seriyaning qaysi qismi o‘zgarishini tanlang.', 'Click a lesson to edit it, or add another one at any time.': 'Tahrirlash uchun darsni bosing yoki istalgan payt yangi dars qo‘shing.', 'Completed lesson hours': 'Yakunlangan dars soatlari', 'Completed lessons': 'Yakunlangan darslar', 'Completing the lesson updates attendance, keeps your notes, and records the activity in Statistics.': 'Darsni yakunlash davomatni yangilaydi, qaydlarni saqlaydi va faollikni Statistikaga yozadi.', 'Create Goal': 'Maqsad yaratish', 'Create Task': 'Vazifa yaratish', 'Ctrl+S to save': 'Saqlash uchun Ctrl+S', 'Delete homework': 'Uy vazifasini o‘chirish', 'Delete note': 'Qaydni o‘chirish', 'Delete this note? This cannot be undone.': 'Bu qayd o‘chirilsinmi? Buni ortga qaytarib bo‘lmaydi.', 'Drop a file anywhere on this page': 'Faylni shu sahifaning istalgan joyiga tashlang', 'Due': 'Muddat', 'Edit Goal': 'Maqsadni tahrirlash', 'Edit Homework': 'Uy vazifasini tahrirlash', 'Edit Material': 'Materialni tahrirlash', 'Edit Task': 'Vazifani tahrirlash', 'Edit goal': 'Maqsadni tahrirlash', 'Edit homework': 'Uy vazifasini tahrirlash', 'Edit material': 'Materialni tahrirlash', 'Edit task': 'Vazifani tahrirlash', 'Focus complete': 'Fokus tugadi', 'Focus mode': 'Fokus rejimi', 'Give this note a title before saving.': 'Saqlashdan oldin qaydga nom bering.', 'Give this template a short name.': 'Shablonga qisqa nom bering.', 'Homework needs a title': 'Uy vazifasiga nom kerak', 'Homework needs a title.': 'Uy vazifasiga nom kerak.', 'Homework title': 'Uy vazifasi nomi', 'Instructions': 'Ko‘rsatmalar', 'Instructions, questions, links, expectations…': 'Ko‘rsatmalar, savollar, havolalar, kutilmalar…', 'Keep teaching files findable without duplicating them.': 'O‘quv fayllarini nusxalamasdan tartibli va topish oson holda saqlang.', 'Keep the next action clear and lightweight.': 'Keyingi amalni sodda va aniq saqlang.', 'Keep the task clear, connect it to the right learner, and optionally link a lesson or material.': 'Vazifani aniq yozing, kerakli o‘quvchiga biriktiring va xohlasangiz dars yoki material bilan bog‘lang.', 'Lesson Details': 'Dars tafsilotlari', 'Lesson history': 'Darslar tarixi', 'Lesson unavailable': 'Dars mavjud emas', 'Lessons': 'Darslar', 'Lessons Completed': 'Yakunlangan darslar', 'Linked work': 'Bog‘langan ishlar', 'Mark attendance directly here': 'Davomatni shu yerning o‘zida belgilang', 'Mentor stores its path locally — your original file stays where it is.': 'Mentor faqat fayl yo‘lini saqlaydi — asl fayl o‘z joyida qoladi.', 'Mentor stores the reference to your file, not another heavy copy.': 'Mentor faylning nusxasini emas, unga havolani saqlaydi.', 'Missing': 'Topilmadi', 'Missing file': 'Fayl topilmadi', 'Missing homework': 'Uy vazifasi topilmadi', 'Missing name': 'Nom kiritilmagan', 'Missing title': 'Sarlavha kiritilmagan', 'Name': 'Nomi', 'New goal': 'Yangi maqsad', 'New note for this student': 'Bu o‘quvchi uchun yangi qayd', 'New note · Ctrl+S to save': 'Yangi qayd · saqlash uchun Ctrl+S', 'New task': 'Yangi vazifa', 'Next lesson': 'Keyingi dars', 'No homework assigned yet.': 'Hali uy vazifasi berilmagan.', 'No lessons': 'Darslar yo‘q', 'No lessons scheduled': 'Rejalashtirilgan darslar yo‘q', 'No lessons with this student yet.': 'Bu o‘quvchi bilan hali dars bo‘lmagan.', 'No linked lesson': 'Bog‘langan dars yo‘q', 'No linked material': 'Bog‘langan material yo‘q', 'No marked attendance yet': 'Hali davomat belgilanmagan', 'No student': 'O‘quvchi yo‘q', 'Note': 'Qayd', 'Nothing scheduled yet.': 'Hali hech narsa rejalashtirilmagan.', 'Open': 'Ochish', 'Open homework': 'Uy vazifasini ochish', 'Open lesson': 'Darsni ochish', 'Open tasks': 'Vazifalarni ochish', 'Optional details': 'Ixtiyoriy tafsilotlar', 'Optional instructions': 'Ixtiyoriy ko‘rsatmalar', 'Optional · e.g. 18/20 or A': 'Ixtiyoriy · masalan 18/20 yoki A', 'Paused': 'Pauzada', 'Pinned': 'Mahkamlangan', 'Plan lessons without losing sight of the week.': 'Haftani ko‘zdan qochirmasdan darslarni rejalang.', 'Press Enter to open a result · Esc to close': 'Natijani ochish uchun Enter · yopish uchun Esc', 'Ready when you are': 'Tayyor bo‘lsangiz boshlang', 'Recurring Lesson': 'Takrorlanuvchi dars', 'Remove': 'Olib tashlash', 'Remove material': 'Materialni olib tashlash', 'Remove this material from Mentor? The original file will not be deleted.': 'Material Mentor’dan olib tashlansinmi? Asl fayl o‘chirilmaydi.', 'Restart': 'Qayta boshlash', 'Resume': 'Davom ettirish', 'Reuse the student, subject, duration, location, reminder, and repeat settings.': 'O‘quvchi, fan, davomiylik, joy, eslatma va takrorlash sozlamalarini qayta ishlating.', 'Reveal in Explorer': 'Explorer’da ko‘rsatish', 'Save Lesson Template': 'Dars shablonini saqlash', 'Save Note': 'Qaydni saqlash', 'Save as template': 'Shablon sifatida saqlash', 'Saved': 'Saqlandi', 'Saved note · Ctrl+S to save changes': 'Qayd saqlandi · o‘zgarishlar uchun Ctrl+S', 'Scheduled ahead': 'Oldindan rejalangan', 'Score': 'Baho', 'Search materials…': 'Materiallarni qidirish…', 'Search notes…': 'Qaydlarni qidirish…', 'Search students, lessons, notes, materials, tasks…': 'O‘quvchilar, darslar, qaydlar, materiallar, vazifalarni qidirish…', 'See what is assigned, overdue, submitted, or completed without mixing it into ordinary tasks.': 'Berilgan, muddati o‘tgan, topshirilgan va yakunlangan uy vazifalarini oddiy vazifalardan alohida kuzating.', 'Show completed': 'Yakunlanganlarni ko‘rsatish', 'Student Profile': 'O‘quvchi profili', 'Student name is required.': 'O‘quvchi ismi kiritilishi shart.', 'Student not saved': 'O‘quvchi saqlanmadi', 'Student notes': 'O‘quvchi qaydlari', 'Student unavailable': 'O‘quvchi mavjud emas', 'Students Taught': 'O‘qitilgan o‘quvchilar', 'Tags · comma separated': 'Teglar · vergul bilan ajrating', 'Task title is required.': 'Vazifa nomi kiritilishi shart.', 'Tasks Completed': 'Yakunlangan vazifalar', 'Teaching Hours': 'Dars soatlari', 'Teaching plan': 'Dars rejasi', 'Teaching time': 'Dars vaqti', 'Template needs a subject': 'Shablon uchun fan kerak', 'Template not saved': 'Shablon saqlanmadi', 'This file no longer exists at the saved location.': 'Fayl saqlangan manzilda endi mavjud emas.', 'This file was moved or deleted outside Mentor.': 'Fayl Mentor’dan tashqarida ko‘chirilgan yoki o‘chirilgan.', 'This lesson no longer exists.': 'Bu dars endi mavjud emas.', "Today's teaching plan": 'Bugungi dars rejasi', 'Track a teaching target without turning Mentor into a project manager.': 'Mentorni loyiha boshqaruvchisiga aylantirmasdan dars maqsadlarini kuzating.', 'Unique learners': 'Noyob o‘quvchilar', 'Untitled note': 'Nomsiz qayd', 'Useful signals, not a wall of analytics.': 'Foydali ko‘rsatkichlar — ortiqcha analitikasiz.', 'Weekly Teaching Hours': 'Haftalik dars soatlari', 'What needs to be done?': 'Nima qilish kerak?', 'What was covered? What should you remember next time?': 'Nimalar o‘tildi? Keyingi safar nimani eslab qolish kerak?', 'Wrap up lesson': 'Darsni yakunlash', 'Write your teaching note…': 'Dars qaydingizni yozing…', "Your day is clear. Add a lesson when you're ready.": 'Bugungi reja bo‘sh. Tayyor bo‘lsangiz dars qo‘shing.', 'completed': 'yakunlangan', 'e.g. Complete questions 1–10': 'masalan, 1–10 savollarni bajarish', 'e.g. Grade 10': 'masalan, 10-sinf', 'homework completed': 'uy vazifasi yakunlandi', 'last 7 days': 'so‘nggi 7 kun', 'late': 'kechikdi', 'marked lessons': 'belgilangan darslar', 'occurrences': 'takrorlanish', 'present': 'qatnashdi', 'Changes preview immediately. Cancel restores your previous appearance.': 'O‘zgarishlar darhol ko‘rinadi. Bekor qilish avvalgi ko‘rinishni qaytaradi.', 'Mentor · Live Preview': 'Mentor · Jonli ko‘rinish', 'Language changes apply to the whole interface as soon as you save — no restart required.': 'Til saqlangan zahoti butun interfeysga qo‘llanadi — qayta ishga tushirish shart emas.', 'Your workspace remains local. Backups are standard SQLite database files.': 'Ish maydoningiz kompyuterda qoladi. Zaxiralar standart SQLite baza fayllaridir.', 'Start empty or load a small sample workspace to explore the app.': 'Bo‘sh boshlang yoki dasturni ko‘rish uchun kichik namuna muhitini yuklang.'})
RU.update({'A quiet timer for lesson prep, marking, or planning.': 'Спокойный таймер для подготовки, проверки и планирования.', 'A quiet workspace for teaching notes and ideas.': 'Спокойное пространство для заметок и идей преподавателя.', 'Add': 'Добавить', 'Add a homework title or turn off homework for this lesson.': 'Добавьте название домашнего задания или отключите его для этого урока.', 'Add a subject before saving this lesson as a template.': 'Укажите предмет перед сохранением урока как шаблона.', 'Add teaching material': 'Добавить учебный материал', 'All time': 'За всё время', 'Assign homework': 'Задать домашнее', 'Assign homework before finishing': 'Задать домашнее перед завершением', 'Attendance is only used when a student is assigned to this lesson.': 'Посещаемость доступна только если к уроку назначен ученик.', 'Attendance not saved': 'Посещаемость не сохранена', 'Available': 'Доступен', 'Browse…': 'Обзор…', 'Category': 'Категория', 'Choose exactly how much of this series should change.': 'Выберите, какую часть серии нужно изменить.', 'Click a lesson to edit it, or add another one at any time.': 'Нажмите на урок для редактирования или добавьте новый в любое время.', 'Completed lesson hours': 'Часы завершённых уроков', 'Completed lessons': 'Завершённые уроки', 'Completing the lesson updates attendance, keeps your notes, and records the activity in Statistics.': 'Завершение урока обновит посещаемость, сохранит заметки и запишет активность в Статистику.', 'Create Goal': 'Создать цель', 'Create Task': 'Создать задачу', 'Ctrl+S to save': 'Ctrl+S для сохранения', 'Delete homework': 'Удалить домашнее', 'Delete note': 'Удалить заметку', 'Delete this note? This cannot be undone.': 'Удалить эту заметку? Действие нельзя отменить.', 'Drop a file anywhere on this page': 'Перетащите файл в любое место этой страницы', 'Due': 'Срок', 'Edit Goal': 'Изменить цель', 'Edit Homework': 'Изменить домашнее', 'Edit Material': 'Изменить материал', 'Edit Task': 'Изменить задачу', 'Edit goal': 'Изменить цель', 'Edit homework': 'Изменить домашнее', 'Edit material': 'Изменить материал', 'Edit task': 'Изменить задачу', 'Focus complete': 'Фокус завершён', 'Focus mode': 'Режим фокуса', 'Give this note a title before saving.': 'Перед сохранением дайте заметке название.', 'Give this template a short name.': 'Дайте шаблону короткое название.', 'Homework needs a title': 'Нужно название домашнего задания', 'Homework needs a title.': 'Нужно название домашнего задания.', 'Homework title': 'Название домашнего задания', 'Instructions': 'Инструкции', 'Instructions, questions, links, expectations…': 'Инструкции, вопросы, ссылки, ожидания…', 'Keep teaching files findable without duplicating them.': 'Храните учебные файлы организованно без создания копий.', 'Keep the next action clear and lightweight.': 'Пусть следующий шаг остаётся простым и понятным.', 'Keep the task clear, connect it to the right learner, and optionally link a lesson or material.': 'Сформулируйте задачу ясно, привяжите к ученику и при необходимости к уроку или материалу.', 'Lesson Details': 'Детали урока', 'Lesson history': 'История уроков', 'Lesson unavailable': 'Урок недоступен', 'Lessons': 'Уроки', 'Lessons Completed': 'Завершённые уроки', 'Linked work': 'Связанные материалы', 'Mark attendance directly here': 'Отмечайте посещаемость прямо здесь', 'Mentor stores its path locally — your original file stays where it is.': 'Mentor хранит только путь к файлу — оригинал остаётся на месте.', 'Mentor stores the reference to your file, not another heavy copy.': 'Mentor хранит ссылку на файл, а не тяжёлую копию.', 'Missing': 'Не найден', 'Missing file': 'Файл не найден', 'Missing homework': 'Домашнее задание не найдено', 'Missing name': 'Нет названия', 'Missing title': 'Нет заголовка', 'Name': 'Название', 'New goal': 'Новая цель', 'New note for this student': 'Новая заметка для ученика', 'New note · Ctrl+S to save': 'Новая заметка · Ctrl+S для сохранения', 'New task': 'Новая задача', 'Next lesson': 'Следующий урок', 'No homework assigned yet.': 'Домашнее задание ещё не назначено.', 'No lessons': 'Уроков нет', 'No lessons scheduled': 'Уроки не запланированы', 'No lessons with this student yet.': 'С этим учеником уроков пока не было.', 'No linked lesson': 'Нет связанного урока', 'No linked material': 'Нет связанного материала', 'No marked attendance yet': 'Посещаемость ещё не отмечалась', 'No student': 'Без ученика', 'Note': 'Заметка', 'Nothing scheduled yet.': 'Пока ничего не запланировано.', 'Open': 'Открыть', 'Open homework': 'Открыть домашнее', 'Open lesson': 'Открыть урок', 'Open tasks': 'Открыть задачи', 'Optional details': 'Необязательные детали', 'Optional instructions': 'Необязательные инструкции', 'Optional · e.g. 18/20 or A': 'Необязательно · например 18/20 или A', 'Paused': 'На паузе', 'Pinned': 'Закреплено', 'Plan lessons without losing sight of the week.': 'Планируйте уроки, сохраняя обзор всей недели.', 'Press Enter to open a result · Esc to close': 'Enter — открыть результат · Esc — закрыть', 'Ready when you are': 'Готово к запуску', 'Recurring Lesson': 'Повторяющийся урок', 'Remove': 'Удалить', 'Remove material': 'Удалить материал', 'Remove this material from Mentor? The original file will not be deleted.': 'Удалить материал из Mentor? Оригинальный файл останется на диске.', 'Restart': 'Начать заново', 'Resume': 'Продолжить', 'Reuse the student, subject, duration, location, reminder, and repeat settings.': 'Повторно используйте ученика, предмет, длительность, место, напоминание и повтор.', 'Reveal in Explorer': 'Показать в Проводнике', 'Save Lesson Template': 'Сохранить шаблон урока', 'Save Note': 'Сохранить заметку', 'Save as template': 'Сохранить как шаблон', 'Saved': 'Сохранено', 'Saved note · Ctrl+S to save changes': 'Заметка сохранена · Ctrl+S для изменений', 'Scheduled ahead': 'Запланировано', 'Score': 'Оценка', 'Search materials…': 'Поиск материалов…', 'Search notes…': 'Поиск заметок…', 'Search students, lessons, notes, materials, tasks…': 'Поиск учеников, уроков, заметок, материалов, задач…', 'See what is assigned, overdue, submitted, or completed without mixing it into ordinary tasks.': 'Отслеживайте назначенные, просроченные, сданные и завершённые домашние задания отдельно от обычных задач.', 'Show completed': 'Показывать завершённые', 'Student Profile': 'Профиль ученика', 'Student name is required.': 'Имя ученика обязательно.', 'Student not saved': 'Ученик не сохранён', 'Student notes': 'Заметки об ученике', 'Student unavailable': 'Ученик недоступен', 'Students Taught': 'Ученики', 'Tags · comma separated': 'Теги · через запятую', 'Task title is required.': 'Название задачи обязательно.', 'Tasks Completed': 'Завершённые задачи', 'Teaching Hours': 'Учебные часы', 'Teaching plan': 'План занятий', 'Teaching time': 'Время занятий', 'Template needs a subject': 'Для шаблона нужен предмет', 'Template not saved': 'Шаблон не сохранён', 'This file no longer exists at the saved location.': 'Файла больше нет по сохранённому пути.', 'This file was moved or deleted outside Mentor.': 'Файл был перемещён или удалён вне Mentor.', 'This lesson no longer exists.': 'Этот урок больше не существует.', "Today's teaching plan": 'План занятий на сегодня', 'Track a teaching target without turning Mentor into a project manager.': 'Отслеживайте учебную цель, не превращая Mentor в менеджер проектов.', 'Unique learners': 'Уникальные ученики', 'Untitled note': 'Без названия', 'Useful signals, not a wall of analytics.': 'Полезные показатели без стены из графиков.', 'Weekly Teaching Hours': 'Учебные часы за неделю', 'What needs to be done?': 'Что нужно сделать?', 'What was covered? What should you remember next time?': 'Что прошли? Что важно помнить к следующему уроку?', 'Wrap up lesson': 'Завершение урока', 'Write your teaching note…': 'Напишите заметку об уроке…', "Your day is clear. Add a lesson when you're ready.": 'Сегодня свободно. Добавьте урок, когда будете готовы.', 'completed': 'завершено', 'e.g. Complete questions 1–10': 'например, выполнить вопросы 1–10', 'e.g. Grade 10': 'например, 10 класс', 'homework completed': 'домашнее выполнено', 'last 7 days': 'последние 7 дней', 'late': 'опоздал', 'marked lessons': 'отмеченных уроков', 'occurrences': 'повторов', 'present': 'присутствовал', 'Changes preview immediately. Cancel restores your previous appearance.': 'Изменения видны сразу. Отмена вернёт прежний вид.', 'Mentor · Live Preview': 'Mentor · Предпросмотр', 'Language changes apply to the whole interface as soon as you save — no restart required.': 'Язык применяется ко всему интерфейсу сразу после сохранения — перезапуск не нужен.', 'Your workspace remains local. Backups are standard SQLite database files.': 'Рабочее пространство остаётся на компьютере. Резервные копии — обычные файлы SQLite.', 'Start empty or load a small sample workspace to explore the app.': 'Начните с пустого пространства или загрузите небольшой пример для знакомства с приложением.'})

UZ.update({'Backup Mentor database': 'Mentor bazasini zaxiralash', 'Backup created': 'Zaxira yaratildi', 'Backup saved to:': 'Zaxira saqlandi:', 'Choose teaching material': 'O‘quv materialini tanlang', 'Data exported to:': 'Ma’lumotlar eksport qilindi:', 'Database restored. Close settings to refresh the workspace.': 'Baza tiklandi. Ish maydonini yangilash uchun sozlamalarni yoping.', 'Delete goal': 'Maqsadni o‘chirish', 'Delete named item': '“{name}” o‘chirilsinmi?', 'Delete student': 'O‘quvchini o‘chirish', 'Delete student confirmation': '{name} o‘chirilsinmi? Bog‘langan ma’lumotlar saqlanadi, lekin biriktirilmagan bo‘ladi.', 'Delete task': 'Vazifani o‘chirish', 'Export Mentor data': 'Mentor ma’lumotlarini eksport qilish', 'Export complete': 'Eksport tugadi', 'Export students': 'O‘quvchilarni eksport qilish', 'Grade': 'Sinf', 'Learners count': '{count} ta o‘quvchi', 'OVERDUE': 'MUDDATI O‘TGAN', 'Open Profile': 'Profilni ochish', 'Open a learner profile for lesson history, attendance, and linked work.': 'Darslar tarixi, davomat va bog‘langan ishlarni ko‘rish uchun o‘quvchi profilini oching.', 'Restore Mentor database': 'Mentor bazasini tiklash', 'Restore complete': 'Tiklash tugadi', 'Restore database': 'Bazani tiklash', 'Search students…': 'O‘quvchilarni qidirish…', 'Simple targets, visible progress.': 'Oddiy maqsadlar, ko‘rinadigan taraqqiyot.', 'Small actions that keep teaching work moving.': 'Dars ishlarini oldinga siljitadigan kichik vazifalar.', 'Students exported to:': 'O‘quvchilar eksport qilindi:', 'This replaces the current Mentor database contents. Continue?': 'Bu amaldagi Mentor bazasi ma’lumotlarini almashtiradi. Davom etilsinmi?', 'Toggle complete': 'Yakunlangan holatini almashtirish'})
RU.update({'Backup Mentor database': 'Резервная копия базы Mentor', 'Backup created': 'Резервная копия создана', 'Backup saved to:': 'Копия сохранена:', 'Choose teaching material': 'Выберите учебный материал', 'Data exported to:': 'Данные экспортированы:', 'Database restored. Close settings to refresh the workspace.': 'База восстановлена. Закройте настройки, чтобы обновить рабочее пространство.', 'Delete goal': 'Удалить цель', 'Delete named item': 'Удалить «{name}»?', 'Delete student': 'Удалить ученика', 'Delete student confirmation': 'Удалить {name}? Связанные данные сохранятся, но будут без ученика.', 'Delete task': 'Удалить задачу', 'Export Mentor data': 'Экспорт данных Mentor', 'Export complete': 'Экспорт завершён', 'Export students': 'Экспорт учеников', 'Grade': 'Класс', 'Learners count': 'Учеников: {count}', 'OVERDUE': 'ПРОСРОЧЕНО', 'Open Profile': 'Открыть профиль', 'Open a learner profile for lesson history, attendance, and linked work.': 'Откройте профиль ученика, чтобы увидеть историю уроков, посещаемость и связанные записи.', 'Restore Mentor database': 'Восстановить базу Mentor', 'Restore complete': 'Восстановление завершено', 'Restore database': 'Восстановить базу', 'Search students…': 'Поиск учеников…', 'Simple targets, visible progress.': 'Простые цели и наглядный прогресс.', 'Small actions that keep teaching work moving.': 'Небольшие задачи, которые помогают двигать преподавание вперёд.', 'Students exported to:': 'Ученики экспортированы:', 'This replaces the current Mentor database contents. Continue?': 'Текущие данные базы Mentor будут заменены. Продолжить?', 'Toggle complete': 'Изменить статус выполнения'})

UZ.update({'Mark Complete': 'Yakunlangan deb belgilash', 'Assignments': 'Uy vazifalari', 'Material': 'Material', 'Task': 'Vazifa', 'Priority': 'Muhimlik', 'Title': 'Sarlavha', 'Description': 'Tavsif', 'Target': 'Maqsad', 'Progress': 'Taraqqiyot', 'Deadline': 'Muddat', 'File / URL': 'Fayl / URL', 'Save Student': 'O‘quvchini saqlash', 'Save Task': 'Vazifani saqlash', 'Save Goal': 'Maqsadni saqlash', 'Save Material': 'Materialni saqlash', 'Save Homework': 'Uy vazifasini saqlash', 'Save Template': 'Shablonni saqlash', 'Score / result': 'Baho / natija', 'Math': 'Matematika', 'Physics': 'Fizika', 'Computer Science': 'Informatika', 'Other': 'Boshqa', '5 minutes before': '5 daqiqa oldin', '10 minutes before': '10 daqiqa oldin', '15 minutes before': '15 daqiqa oldin', '30 minutes before': '30 daqiqa oldin', '1 hour before': '1 soat oldin', 'Off': 'O‘chiq', 'No reminder': 'Eslatma yo‘q', 'Save Lesson': 'Darsni saqlash', 'Lesson': 'Dars', 'Private': 'Individual'})
RU.update({'Mark Complete': 'Отметить выполненным', 'Assignments': 'Домашние задания', 'Material': 'Материал', 'Task': 'Задача', 'Priority': 'Приоритет', 'Title': 'Название', 'Description': 'Описание', 'Target': 'Цель', 'Progress': 'Прогресс', 'Deadline': 'Срок', 'File / URL': 'Файл / URL', 'Save Student': 'Сохранить ученика', 'Save Task': 'Сохранить задачу', 'Save Goal': 'Сохранить цель', 'Save Material': 'Сохранить материал', 'Save Homework': 'Сохранить домашнее', 'Save Template': 'Сохранить шаблон', 'Score / result': 'Оценка / результат', 'Math': 'Математика', 'Physics': 'Физика', 'Computer Science': 'Информатика', 'Other': 'Другое', '5 minutes before': 'За 5 минут', '10 minutes before': 'За 10 минут', '15 minutes before': 'За 15 минут', '30 minutes before': 'За 30 минут', '1 hour before': 'За 1 час', 'Off': 'Выключено', 'No reminder': 'Без напоминания', 'Save Lesson': 'Сохранить урок', 'Private': 'Индивидуально'})

UZ.update({"Mark Complete":"Yakunlangan deb belgilash"})
RU.update({"Mark Complete":"Отметить выполненным"})

UZ.update({'Could not save student': 'O‘quvchi saqlanmadi', 'Could not save task': 'Vazifa saqlanmadi', 'Homework not saved': 'Uy vazifasi saqlanmadi', 'Could not save goal': 'Maqsad saqlanmadi', 'Lesson not completed': 'Dars yakunlanmadi', 'Could not duplicate lesson': 'Dars nusxalanmadi', 'Could not cancel lesson': 'Dars bekor qilinmadi', 'Could not delete lesson': 'Dars o‘chirilmadi', 'Could not schedule lesson': 'Dars rejalashtirilmadi', "Mentor couldn't save this lesson.": 'Mentor bu darsni saqlay olmadi.', 'Lesson update failed': 'Darsni yangilashda xato', 'Lesson saved': 'Dars saqlandi', 'Lessons updated': '{count} ta dars yangilandi', 'Cancel lesson': 'Darsni bekor qilish', 'Cancel one lesson': '{subject} darsi ({date}) bekor qilinsinmi?', 'Cancel lesson series part': '{subject} seriyasining tanlangan qismi bekor qilinsinmi?', 'Lessons cancelled': '{count} ta dars bekor qilindi', 'Delete lesson': 'Darsni o‘chirish', 'Delete one lesson': '{subject} darsi o‘chirilsinmi?', 'Delete lesson series part': '{subject} seriyasining tanlangan qismi o‘chirilsinmi?', 'This cannot be undone.': 'Buni ortga qaytarib bo‘lmaydi.', 'Lessons deleted': '{count} ta dars o‘chirildi'})
RU.update({'Could not save student': 'Не удалось сохранить ученика', 'Could not save task': 'Не удалось сохранить задачу', 'Homework not saved': 'Домашнее задание не сохранено', 'Could not save goal': 'Не удалось сохранить цель', 'Lesson not completed': 'Урок не завершён', 'Could not duplicate lesson': 'Не удалось дублировать урок', 'Could not cancel lesson': 'Не удалось отменить урок', 'Could not delete lesson': 'Не удалось удалить урок', 'Could not schedule lesson': 'Не удалось запланировать урок', "Mentor couldn't save this lesson.": 'Mentor не смог сохранить этот урок.', 'Lesson update failed': 'Не удалось обновить урок', 'Lesson saved': 'Урок сохранён', 'Lessons updated': 'Обновлено уроков: {count}', 'Cancel lesson': 'Отменить урок', 'Cancel one lesson': 'Отменить урок {subject} ({date})?', 'Cancel lesson series part': 'Отменить выбранную часть серии {subject}?', 'Lessons cancelled': 'Отменено уроков: {count}', 'Delete lesson': 'Удалить урок', 'Delete one lesson': 'Удалить урок {subject}?', 'Delete lesson series part': 'Удалить выбранную часть серии {subject}?', 'This cannot be undone.': 'Это действие нельзя отменить.', 'Lessons deleted': 'Удалено уроков: {count}'})

UZ.update({"Homework overdue and due":"{overdue} ta muddati o‘tgan · {due} ta bugun","Homework due today":"Bugun {count} ta"})
RU.update({"Homework overdue and due":"Просрочено: {overdue} · сегодня: {due}","Homework due today":"Сегодня: {count}"})

UZ.update({'Student updated': 'O‘quvchi yangilandi', 'Student deleted': 'O‘quvchi o‘chirildi', 'Lesson updated': 'Dars yangilandi', 'Lesson deleted': 'Dars o‘chirildi', 'Lesson series edited': 'Darslar seriyasi tahrirlandi', 'Lesson series updated': 'Darslar seriyasi yangilandi', 'Note created': 'Qayd yaratildi', 'Note saved': 'Qayd saqlandi', 'Note deleted': 'Qayd o‘chirildi', 'Material added': 'Material qo‘shildi', 'Material updated': 'Material yangilandi', 'Material removed': 'Material olib tashlandi', 'Task updated': 'Vazifa yangilandi', 'Task created': 'Vazifa yaratildi', 'Task completed': 'Vazifa yakunlandi', 'Task reopened': 'Vazifa qayta ochildi', 'Homework updated': 'Uy vazifasi yangilandi', 'Homework assigned': 'Uy vazifasi berildi', 'Homework deleted': 'Uy vazifasi o‘chirildi', 'Goal updated': 'Maqsad yangilandi', 'Goal created': 'Maqsad yaratildi', 'Attendance: {status}': 'Davomat: {status}', 'Lesson status changed': 'Dars: {status}', 'Homework status changed': 'Uy vazifasi: {status}', 'Lesson series status changed': 'Darslar seriyasi: {status}'})
RU.update({'Student updated': 'Ученик обновлён', 'Student deleted': 'Ученик удалён', 'Lesson updated': 'Урок обновлён', 'Lesson deleted': 'Урок удалён', 'Lesson series edited': 'Серия уроков изменена', 'Lesson series updated': 'Серия уроков обновлена', 'Note created': 'Заметка создана', 'Note saved': 'Заметка сохранена', 'Note deleted': 'Заметка удалена', 'Material added': 'Материал добавлен', 'Material updated': 'Материал обновлён', 'Material removed': 'Материал удалён', 'Task updated': 'Задача обновлена', 'Task created': 'Задача создана', 'Task completed': 'Задача выполнена', 'Task reopened': 'Задача снова открыта', 'Homework updated': 'Домашнее обновлено', 'Homework assigned': 'Домашнее назначено', 'Homework deleted': 'Домашнее удалено', 'Goal updated': 'Цель обновлена', 'Goal created': 'Цель создана', 'Attendance: {status}': 'Посещаемость: {status}', 'Lesson status changed': 'Урок: {status}', 'Homework status changed': 'Домашнее: {status}', 'Lesson series status changed': 'Серия уроков: {status}'})

UZ.update({"Global & Personal":"Global va shaxsiy"})
RU.update({"Global & Personal":"Язык и персонализация"})

UZ.update({"Something went wrong. The technical details were written to the Mentor log.":"Nimadir xato ketdi. Texnik tafsilotlar Mentor jurnaliga yozildi."})
RU.update({"Something went wrong. The technical details were written to the Mentor log.":"Что-то пошло не так. Технические сведения записаны в журнал Mentor."})

CATALOGS = {"en": {}, "uz": UZ, "ru": RU}

# Values persisted in SQLite. Never store their translated labels.
ENUM_VALUES = {
    "Active", "Inactive", "Archived", "Upcoming", "In Progress", "Completed", "Cancelled",
    "Not marked", "Present", "Late", "Absent", "Excused", "Lesson", "Review", "Consultation",
    "Exam Prep", "Assessment", "None", "Every day", "Every week", "Every 2 weeks",
    "Assigned", "Submitted", "Skipped", "Low", "Medium", "High", "Paused",
}


def set_language(language: str) -> None:
    global _current_language
    _current_language = language if language in LANGUAGES else "en"
    if QLocale is not None:
        locale_name = {"en": "en_US", "uz": "uz_UZ", "ru": "ru_RU"}[_current_language]
        QLocale.setDefault(QLocale(locale_name))


def language() -> str:
    return _current_language


def configure_region(*, use_24h: bool = True, week_start: str = "monday") -> None:
    global _time_24h, _week_start
    _time_24h = bool(use_24h)
    _week_start = "sunday" if week_start == "sunday" else "monday"


def tr(text: str, **kwargs: Any) -> str:
    translated = CATALOGS.get(_current_language, {}).get(text, text)
    if kwargs:
        try:
            return translated.format(**kwargs)
        except (KeyError, ValueError):
            return translated
    return translated


def enum_display(value: str | None) -> str:
    return tr(str(value or ""))


def enum_canonical(display: str | None) -> str:
    value = str(display or "")
    if value in ENUM_VALUES:
        return value
    for canonical in ENUM_VALUES:
        for lang in CATALOGS:
            translated = CATALOGS[lang].get(canonical, canonical)
            if value == translated:
                return canonical
    return value


def format_date(value: date | str | None, *, compact: bool = False, relative: bool = True) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            parsed = date.fromisoformat(value)
        except ValueError:
            return value
    else:
        parsed = value
    if relative and parsed == date.today():
        return tr("Today")
    if QLocale is not None and QDate is not None:
        qd = QDate(parsed.year, parsed.month, parsed.day)
        pattern = "ddd, d MMM" if compact else "dddd, d MMMM yyyy"
        return QLocale().toString(qd, pattern)
    return parsed.strftime("%Y-%m-%d")



def format_weekday(value: date, *, short: bool = True) -> str:
    if QLocale is not None and QDate is not None:
        qd = QDate(value.year, value.month, value.day)
        return QLocale().toString(qd, "ddd" if short else "dddd")
    return value.strftime("%a" if short else "%A")


def format_time(value: str | None) -> str:
    raw = str(value or "")
    if _time_24h:
        return raw
    try:
        return datetime.strptime(raw, "%H:%M").strftime("%I:%M %p").lstrip("0")
    except ValueError:
        return raw



def format_duration(minutes: int) -> str:
    minutes = max(0, int(minutes))
    hours, mins = divmod(minutes, 60)
    if _current_language == "uz":
        parts = []
        if hours: parts.append(f"{hours} soat")
        if mins or not parts: parts.append(f"{mins} daq")
        return " ".join(parts)
    if _current_language == "ru":
        parts = []
        if hours: parts.append(f"{hours} ч")
        if mins or not parts: parts.append(f"{mins} мин")
        return " ".join(parts)
    parts = []
    if hours: parts.append(f"{hours}h")
    if mins or not parts: parts.append(f"{mins}m")
    return " ".join(parts)


def lesson_count(count: int) -> str:
    count = int(count)
    if _current_language == "uz":
        return f"{count} ta dars"
    if _current_language == "ru":
        mod10, mod100 = count % 10, count % 100
        if mod10 == 1 and mod100 != 11:
            word = "урок"
        elif mod10 in {2, 3, 4} and mod100 not in {12, 13, 14}:
            word = "урока"
        else:
            word = "уроков"
        return f"{count} {word}"
    return f"{count} lesson{'s' if count != 1 else ''}"


def week_starts_monday() -> bool:
    return _week_start == "monday"



def localize_activity_title(title: str) -> str:
    if title.startswith("Attendance: "):
        return tr("Attendance: {status}", status=enum_display(title.split(": ", 1)[1]))
    if title.startswith("Lesson series ") and title not in {"Lesson series edited", "Lesson series updated"}:
        raw = title.removeprefix("Lesson series ").strip().title()
        return tr("Lesson series status changed", status=enum_display(raw))
    if title.startswith("Lesson ") and title not in {"Lesson updated", "Lesson scheduled", "Lesson deleted", "Lesson completed"}:
        raw = title.removeprefix("Lesson ").strip().title()
        return tr("Lesson status changed", status=enum_display(raw))
    if title.startswith("Homework ") and title not in {"Homework updated", "Homework assigned", "Homework deleted"}:
        raw = title.removeprefix("Homework ").strip().title()
        return tr("Homework status changed", status=enum_display(raw))
    return tr(title)


def localized_insight(data: dict[str, Any]) -> str:
    if data.get("assignments_overdue"):
        n = int(data["assignments_overdue"])
        if _current_language == "uz": return f"{n} ta uy vazifasi muddati o‘tgan — qisqa nazorat foydali bo‘ladi."
        if _current_language == "ru": return f"Просрочено домашних заданий: {n}. Стоит быстро проверить."
        return f"{n} homework item{'s' if n != 1 else ''} overdue — worth a quick follow-up."
    if data.get("lesson_review_count"):
        n = int(data["lesson_review_count"])
        if _current_language == "uz": return f"{n} ta o‘tgan dars hali ko‘rib chiqilishi yoki yakunlanishi kerak."
        if _current_language == "ru": return f"Прошлых уроков для проверки или завершения: {n}."
        return f"{n} past lesson{'s' if n != 1 else ''} still need review or completion."
    if data.get("tasks_due"):
        n = int(data["tasks_due"])
        if _current_language == "uz": return f"Bugun {n} ta vazifa e’tiboringizni kutmoqda."
        if _current_language == "ru": return f"Сегодня требуют внимания задач: {n}."
        return f"{n} task{'s' if n != 1 else ''} need your attention today."
    if data.get("attendance_pending"):
        n = int(data["attendance_pending"])
        if _current_language == "uz": return f"{n} ta yakunlangan dars uchun davomat hali belgilanmagan."
        if _current_language == "ru": return f"Для завершённых уроков без отметки посещаемости: {n}."
        return f"Attendance still needs marking for {n} completed lesson{'s' if n != 1 else ''}."
    if data.get("upcoming", 0) >= 4:
        n = int(data["upcoming"])
        if _current_language == "uz": return f"Band kun — jadvalingizda yana {n} ta dars bor."
        if _current_language == "ru": return f"Насыщенный день — в расписании ещё {n} уроков."
        return f"Busy day ahead — {n} lessons still on your schedule."
    if data.get("next_session"):
        nxt = data["next_session"]
        tm = format_time(nxt.get("start_time"))
        if _current_language == "uz": return f"Keyingi: {nxt['subject']} soat {tm}. Keyingi qadamni sodda qiling."
        if _current_language == "ru": return f"Далее: {nxt['subject']} в {tm}. Сосредоточьтесь на следующем шаге."
        return f"Next up: {nxt['subject']} at {tm}. Keep the next step simple."
    if data.get("today_sessions"):
        if _current_language == "uz": return "Bugungi darslar tugadi. Eslab qolishga arzigulik narsani qayd eting."
        if _current_language == "ru": return "Учебный день завершён. Запишите то, что стоит сохранить."
        return "Your teaching day is wrapped up. Capture anything worth remembering."
    if _current_language == "uz": return "Jadvalingiz bo‘sh. Hozirgi ozgina tayyorgarlik ertangi kunni yengillashtiradi."
    if _current_language == "ru": return "Расписание свободно. Небольшая подготовка сейчас облегчит завтра."
    return "Your schedule is clear. A little preparation now can make tomorrow lighter."