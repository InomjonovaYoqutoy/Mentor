from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


def icon(name: str, color: str = "#A8A8A8", size: int = 22) -> QIcon:
    """Return a tiny, dependency-free line icon drawn with Qt."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(color), max(1.5, size * 0.082), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    s = float(size)

    def line(x1: float, y1: float, x2: float, y2: float) -> None:
        p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    if name == "home":
        path = QPainterPath(QPointF(.18*s, .47*s)); path.lineTo(.5*s,.22*s); path.lineTo(.82*s,.47*s)
        p.drawPath(path); p.drawRoundedRect(QRectF(.28*s,.43*s,.44*s,.37*s),2,2)
    elif name in ("calendar", "calendar_add"):
        p.drawRoundedRect(QRectF(.18*s,.23*s,.64*s,.6*s),3,3); line(.18*s,.4*s,.82*s,.4*s); line(.34*s,.15*s,.34*s,.31*s); line(.66*s,.15*s,.66*s,.31*s)
        if name == "calendar_add":
            line(.5*s,.5*s,.5*s,.7*s); line(.4*s,.6*s,.6*s,.6*s)
    elif name == "note":
        p.drawRoundedRect(QRectF(.25*s,.16*s,.5*s,.68*s),3,3); line(.35*s,.4*s,.65*s,.4*s); line(.35*s,.52*s,.65*s,.52*s); line(.35*s,.64*s,.57*s,.64*s)
    elif name == "folder":
        path = QPainterPath(QPointF(.14*s,.34*s)); path.lineTo(.38*s,.34*s); path.lineTo(.46*s,.25*s); path.lineTo(.82*s,.25*s); path.quadTo(.88*s,.25*s,.88*s,.32*s); path.lineTo(.88*s,.76*s); path.quadTo(.88*s,.82*s,.82*s,.82*s); path.lineTo(.18*s,.82*s); path.quadTo(.12*s,.82*s,.12*s,.76*s); path.lineTo(.12*s,.4*s); path.quadTo(.12*s,.34*s,.18*s,.34*s)
        p.drawPath(path)
    elif name == "stats":
        line(.2*s,.8*s,.2*s,.55*s); line(.43*s,.8*s,.43*s,.35*s); line(.66*s,.8*s,.66*s,.2*s); line(.82*s,.8*s,.82*s,.45*s)
    elif name == "search":
        p.drawEllipse(QRectF(.2*s,.2*s,.45*s,.45*s)); line(.58*s,.58*s,.82*s,.82*s)
    elif name == "bell":
        path = QPainterPath(QPointF(.28*s,.62*s)); path.quadTo(.32*s,.54*s,.32*s,.42*s); path.quadTo(.32*s,.25*s,.5*s,.25*s); path.quadTo(.68*s,.25*s,.68*s,.42*s); path.quadTo(.68*s,.54*s,.72*s,.62*s); path.lineTo(.75*s,.68*s); path.lineTo(.25*s,.68*s); path.closeSubpath(); p.drawPath(path); p.drawArc(QRectF(.43*s,.69*s,.14*s,.12*s),180*16,180*16)
    elif name == "user":
        p.drawEllipse(QRectF(.36*s,.18*s,.28*s,.28*s)); p.drawArc(QRectF(.2*s,.42*s,.6*s,.45*s),0,180*16)
    elif name == "plus":
        line(.5*s,.22*s,.5*s,.78*s); line(.22*s,.5*s,.78*s,.5*s)
    elif name == "minus":
        line(.22*s,.5*s,.78*s,.5*s)
    elif name == "people":
        p.drawEllipse(QRectF(.22*s,.23*s,.22*s,.22*s)); p.drawEllipse(QRectF(.55*s,.27*s,.18*s,.18*s)); p.drawArc(QRectF(.12*s,.43*s,.45*s,.36*s),0,180*16); p.drawArc(QRectF(.47*s,.46*s,.38*s,.3*s),0,180*16)
    elif name in ("check", "circle_check"):
        if name == "circle_check": p.drawEllipse(QRectF(.18*s,.18*s,.64*s,.64*s))
        path=QPainterPath(QPointF(.29*s,.51*s)); path.lineTo(.44*s,.65*s); path.lineTo(.72*s,.35*s); p.drawPath(path)
    elif name == "star":
        pts=[]
        for i in range(10):
            a=-math.pi/2+i*math.pi/5; r=.34*s if i%2==0 else .15*s; pts.append(QPointF(.5*s+math.cos(a)*r,.5*s+math.sin(a)*r))
        path=QPainterPath(pts[0]); [path.lineTo(pt) for pt in pts[1:]]; path.closeSubpath(); p.drawPath(path)
    elif name in ("bolt", "sparkles"):
        if name == "bolt":
            path=QPainterPath(QPointF(.55*s,.12*s)); path.lineTo(.25*s,.55*s); path.lineTo(.46*s,.55*s); path.lineTo(.38*s,.88*s); path.lineTo(.75*s,.4*s); path.lineTo(.53*s,.4*s); path.closeSubpath(); p.drawPath(path)
        else:
            path=QPainterPath(QPointF(.5*s,.12*s)); path.lineTo(.56*s,.38*s); path.lineTo(.78*s,.5*s); path.lineTo(.56*s,.58*s); path.lineTo(.5*s,.84*s); path.lineTo(.43*s,.58*s); path.lineTo(.2*s,.5*s); path.lineTo(.43*s,.38*s); path.closeSubpath(); p.drawPath(path)
    elif name in ("clock", "timer"):
        p.drawEllipse(QRectF(.18*s,.18*s,.64*s,.64*s)); line(.5*s,.5*s,.5*s,.3*s); line(.5*s,.5*s,.66*s,.58*s)
        if name == "timer": line(.4*s,.1*s,.6*s,.1*s)
    elif name == "trash":
        p.drawRoundedRect(QRectF(.3*s,.3*s,.4*s,.5*s),2,2); line(.25*s,.3*s,.75*s,.3*s); line(.4*s,.2*s,.6*s,.2*s)
    elif name == "edit":
        line(.25*s,.72*s,.65*s,.32*s); line(.58*s,.25*s,.72*s,.39*s); line(.23*s,.75*s,.38*s,.72*s)
    elif name == "more":
        for x in (.28,.5,.72): p.drawEllipse(QRectF((x-.035)*s,.465*s,.07*s,.07*s))
    elif name == "arrow_right":
        line(.35*s,.25*s,.62*s,.5*s); line(.62*s,.5*s,.35*s,.75*s)
    elif name == "chevron_left":
        line(.62*s,.25*s,.35*s,.5*s); line(.35*s,.5*s,.62*s,.75*s)
    elif name == "chevron_right":
        line(.38*s,.25*s,.65*s,.5*s); line(.65*s,.5*s,.38*s,.75*s)
    elif name == "refresh":
        p.drawArc(QRectF(.2*s,.2*s,.6*s,.6*s),30*16,280*16); line(.7*s,.18*s,.79*s,.31*s); line(.7*s,.18*s,.57*s,.21*s)
    elif name == "settings":
        p.drawEllipse(QRectF(.38*s,.38*s,.24*s,.24*s)); p.drawEllipse(QRectF(.2*s,.2*s,.6*s,.6*s))
    elif name == "play":
        path=QPainterPath(QPointF(.37*s,.28*s)); path.lineTo(.73*s,.5*s); path.lineTo(.37*s,.72*s); path.closeSubpath(); p.drawPath(path)
    elif name == "pause":
        line(.4*s,.28*s,.4*s,.72*s); line(.6*s,.28*s,.6*s,.72*s)
    elif name == "task":
        p.drawRoundedRect(QRectF(.2*s,.18*s,.6*s,.64*s),3,3); line(.32*s,.38*s,.4*s,.46*s); line(.4*s,.46*s,.53*s,.31*s); line(.58*s,.39*s,.69*s,.39*s); line(.32*s,.62*s,.4*s,.7*s); line(.4*s,.7*s,.53*s,.55*s); line(.58*s,.63*s,.69*s,.63*s)
    elif name == "location":
        path=QPainterPath(QPointF(.5*s,.84*s)); path.cubicTo(.25*s,.6*s,.25*s,.2*s,.5*s,.18*s); path.cubicTo(.75*s,.2*s,.75*s,.6*s,.5*s,.84*s); p.drawPath(path); p.drawEllipse(QRectF(.42*s,.34*s,.16*s,.16*s))
    elif name == "link":
        p.drawArc(QRectF(.14*s,.31*s,.42*s,.34*s),45*16,210*16); p.drawArc(QRectF(.44*s,.31*s,.42*s,.34*s),225*16,210*16); line(.39*s,.5*s,.61*s,.5*s)
    elif name == "close":
        line(.28*s,.28*s,.72*s,.72*s); line(.72*s,.28*s,.28*s,.72*s)
    else:
        p.drawEllipse(QRectF(.25*s,.25*s,.5*s,.5*s))
    p.end()
    return QIcon(pm)