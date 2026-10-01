from __future__ import annotations

from datetime import datetime, date

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ...services.data_service import DataService
from ...theme import tokens
from ...i18n import tr, format_weekday
from ..icons import icon
from ..widgets import Card, StatCard


class HoursChart(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent);self.data=[];self.setMinimumHeight(300)

    def set_data(self,data):self.data=data;self.update()

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing);r=self.rect().adjusted(48,24,-22,-40)
        p.setPen(QPen(QColor(255,255,255,14),1))
        for i in range(5):
            y=r.top()+r.height()*i/4;p.drawLine(r.left(),int(y),r.right(),int(y))
        if not self.data:p.end();return
        maxv=max([v for _,v in self.data]+[1]);gap=r.width()/len(self.data);bw=min(46,gap*.48)
        for i,(d,v) in enumerate(self.data):
            h=(v/maxv)*r.height();x=r.left()+i*gap+(gap-bw)/2;bar=QRectF(x,r.bottom()-h,bw,max(3,h))
            grad=QLinearGradient(bar.topLeft(),bar.bottomLeft());grad.setColorAt(0,QColor(tokens.ACCENT_BRIGHT));grad.setColorAt(1,QColor(tokens.ACCENT_DARK))
            p.setPen(Qt.NoPen);p.setBrush(grad);p.drawRoundedRect(bar,7,7)
            p.setPen(QColor(tokens.TEXT2));day=format_weekday(date.fromisoformat(d));p.drawText(QRectF(r.left()+i*gap,r.bottom()+9,gap,22),Qt.AlignCenter,day)
            if v>0:
                p.setPen(QColor(tokens.TEXT));p.drawText(QRectF(x-8,r.bottom()-h-24,bw+16,20),Qt.AlignCenter,f"{v:.1f}h")
        p.end()


class StatisticsPage(QWidget):
    def __init__(self,service:DataService,parent=None):
        super().__init__(parent);self.service=service
        root=QVBoxLayout(self);root.setContentsMargins(26,14,26,115);root.setSpacing(18)
        head=QVBoxLayout();head.setSpacing(2);title=QLabel(tr("Statistics"));title.setObjectName("pageTitle");sub=QLabel(tr("Useful signals, not a wall of analytics."));sub.setObjectName("secondary");head.addWidget(title);head.addWidget(sub);root.addLayout(head)
        grid=QGridLayout();grid.setSpacing(14);self.hours=StatCard("clock",tr("Teaching Hours"),interactive=False);self.sessions=StatCard("check",tr("Lessons Completed"),interactive=False);self.students=StatCard("people",tr("Students Taught"),interactive=False);self.attendance=StatCard("circle_check",tr("Attendance"),interactive=False);self.tasks=StatCard("task",tr("Tasks Completed"),interactive=False);[grid.addWidget(w,0,i) for i,w in enumerate([self.hours,self.sessions,self.students,self.attendance,self.tasks])];root.addLayout(grid)
        card=Card();l=QVBoxLayout(card);l.setContentsMargins(19,17,19,17);l.setSpacing(8)
        hr=QHBoxLayout();ico=QLabel();ico.setPixmap(icon("stats",tokens.ACCENT,19).pixmap(19,19));head=QLabel(tr("Weekly Teaching Hours"));head.setObjectName("sectionTitle");self.week_summary=QLabel();self.week_summary.setObjectName("secondary");hr.addWidget(ico);hr.addWidget(head);hr.addStretch();hr.addWidget(self.week_summary);l.addLayout(hr)
        self.chart=HoursChart();l.addWidget(self.chart);root.addWidget(card,1)

    def refresh(self):
        s=self.service.statistics();week_total=sum(v for _,v in s["weekly_hours"])
        self.hours.set_data(str(s["teaching_hours"]),tr("Completed lesson hours"));self.sessions.set_data(str(s["completed_sessions"]),tr("All time"));self.students.set_data(str(s["students_taught"]),tr("Unique learners"))
        rate=s.get("attendance_rate");self.attendance.set_data(f"{rate}%" if rate is not None else "—",f"{s.get('attendance_marked',0)} {tr('marked lessons')}")
        self.tasks.set_data(str(s["tasks_completed"]),f"{s.get('assignments_completed',0)} {tr('homework completed')}")
        self.week_summary.setText(f"{week_total:.1f}h · {tr('last 7 days')}");self.chart.set_data(s["weekly_hours"])