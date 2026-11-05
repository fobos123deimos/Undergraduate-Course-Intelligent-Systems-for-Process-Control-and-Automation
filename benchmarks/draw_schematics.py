"""Draw original conceptual equipment diagrams with editable vector output."""
from pathlib import Path
import os
import numpy as np

HERE=Path(__file__).resolve().parent
os.environ.setdefault('MPLCONFIGDIR',str(HERE/'results/.mplconfig'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon, FancyBboxPatch, Arc

INK='#16324f'; INPUT='#00866b'; OUTPUT='#8055ad'; WATER='#d9edf6'; GRAY='#596b7b'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none'})


def canvas(title,subtitle):
    fig,ax=plt.subplots(figsize=(12,7))
    fig.subplots_adjust(left=.035,right=.965,bottom=.09,top=.80)
    ax.set(xlim=(0,12),ylim=(0,7)); ax.set_aspect('equal'); ax.axis('off')
    fig.suptitle(title,x=.055,y=.95,ha='left',fontsize=21,color=INK,fontweight='bold')
    fig.text(.055,.885,subtitle,fontsize=11,color=GRAY,ha='left')
    fig.text(.055,.035,'Conceptual equipment schematic • topology and model variables, not a detailed P&ID',
             fontsize=9,color=GRAY)
    return fig,ax


def txt(ax,x,y,s,size=11,color=INK,ha='center',va='center',**kw):
    return ax.text(x,y,s,fontsize=size,color=color,ha=ha,va=va,**kw)


def line(ax,points,color=INK,lw=2,**kw):
    a=np.asarray(points); ax.plot(a[:,0],a[:,1],color=color,lw=lw,**kw)


def arrow(ax,start,end,label=None,offset=(0,.25),color=INPUT,style='-|>'):
    ax.annotate('',xy=end,xytext=start,arrowprops=dict(arrowstyle=style,color=color,lw=2,mutation_scale=15))
    if label: txt(ax,(start[0]+end[0])/2+offset[0],(start[1]+end[1])/2+offset[1],label,color=color)


def box(ax,x,y,w,h,label,fill='white',color=INK,size=12):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.02,rounding_size=0.12',
                               fc=fill,ec=color,lw=2))
    txt(ax,x+w/2,y+h/2,label,size,color)


def tank(ax,x,y,w,h,level=.65,label=None):
    ax.add_patch(Rectangle((x+.025,y+.025),w-.05,h*level-.025,fc=WATER,ec='none'))
    line(ax,[(x,y+h),(x,y),(x+w,y),(x+w,y+h)])
    line(ax,[(x+.03,y+h*level),(x+w-.03,y+h*level)],color='#6ba8c4',lw=1.5)
    if label: txt(ax,x+w/2,y+h+.3,label,size=12)


def save(fig,name):
    dest=HERE/'figures'; dest.mkdir(exist_ok=True)
    fig.savefig(dest/(name+'.svg'),metadata={'Title':name,'Description':'Original conceptual scientific equipment diagram'})
    fig.savefig(dest/(name+'.png'),dpi=150)
    plt.close(fig)


def pendulum():
    f,a=canvas('Cart and inverted pendulum','Section 3.3 • upright angle convention and force-limited actuation')
    line(a,[(.9,1.6),(10.9,1.6)],lw=3)
    box(a,4.2,1.95,2.1,.85,'Cart  M = 4.8 kg',WATER,size=10)
    for x in [4.55,5.95]: a.add_patch(Circle((x,1.83),.18,fc='white',ec=INK,lw=2))
    pivot=(5.25,2.85); bob=(6.35,5.9)
    line(a,[pivot,bob],lw=4); a.add_patch(Circle(pivot,.09,fc=INK)); a.add_patch(Circle(bob,.22,fc=INK))
    line(a,[pivot,(5.25,6.3)],ls='--',lw=1,color=GRAY)
    a.add_patch(Arc(pivot,1.8,1.8,theta1=70,theta2=90,color=OUTPUT,lw=2))
    txt(a,5.55,4.05,r'$\theta$',16,OUTPUT)
    txt(a,7.55,5.9,'m = 0.356 kg',ha='left')
    txt(a,7.05,4.7,'l = 0.56 m',ha='left')
    arrow(a,(6.4,2.35),(9.4,2.35),'u = F,  |F| ≤ 120 N',offset=(0,.4))
    arrow(a,(4.2,.8),(6.4,.8),'x (m)',offset=(0,-.3),color=OUTPUT)
    arrow(a,(2,5.8),(2,4.6),'g',offset=(-.4,0),color=GRAY)
    txt(a,6,.1,r'State: $[\theta,\dot\theta,x,\dot x]$ • joint friction and cart friction act on the motion',10)
    save(f,'03-pendulum')


def throttle():
    f,a=canvas('Electromechanical throttle','Section 3.4 • measured voltage-duty-to-angle identification problem')
    box(a,1,3.25,2.1,1.25,'DC motor',WATER)
    box(a,4.0,3.25,1.8,1.25,'Gearbox',WATER)
    line(a,[(3.1,3.87),(4,3.87)]); line(a,[(5.8,3.87),(7.2,3.87)])
    a.add_patch(Circle((8.1,3.87),.95,fc='white',ec=INK,lw=2))
    line(a,[(7.65,3.04),(8.55,4.70)],lw=6,color=OUTPUT)
    a.add_patch(Arc((8.1,3.87),1.25,1.25,theta1=0,theta2=62,color=OUTPUT,lw=2))
    txt(a,8.72,4.1,r'$\varphi$',15,OUTPUT)
    arrow(a,(.0,3.87),(1,3.87),color=INPUT)
    txt(a,2,5.4,'Input: PWM duty u (%)',color=INPUT)
    arrow(a,(2,5.05),(2,4.52),color=INPUT)
    txt(a,8.1,5.5,'Throttle plate',size=13)
    txt(a,8.1,2.1,'Output: angle y = φ (degrees)\n10° closed → 90° open',color=OUTPUT)
    # Spring symbol conveys restoring torque without assuming an identified law.
    line(a,[(4.8,3.25),(4.8,2.65)])
    line(a,[(4.8,2.65),(4.55,2.5),(5.05,2.3),(4.55,2.1),(5.05,1.9),(4.8,1.75),(4.8,1.45)])
    line(a,[(4.2,1.45),(5.4,1.45)])
    txt(a,3.15,1.95,'Return spring\nand friction',size=10)
    txt(a,6,.45,'Measured datasets: 0.01 s sampling • 10000 train / 2500 validation observations',11)
    save(f,'04-throttle')


def pneumatic():
    f,a=canvas('Servo-pneumatic actuator','Section 3.5 • chamber balances and an externally specified valve-flow closure')
    a.add_patch(Rectangle((2.2,3.1),6.1,2,fc=WATER,ec=INK,lw=2))
    a.add_patch(Rectangle((5.15,3.1),.35,2,fc=GRAY,ec=INK,lw=1))
    line(a,[(5.5,4.1),(9.7,4.1)],lw=7)
    box(a,9.7,3.35,1.55,1.45,'Load\n3–9 kg',size=11)
    txt(a,3.6,4.45,'Chamber I\npI (Pa)',color=OUTPUT)
    txt(a,6.85,4.45,'Chamber II\npII (Pa)',color=OUTPUT)
    txt(a,3.65,3.6,'V₀ + Aₖx',size=11)
    txt(a,6.8,3.6,'V₀ − Aₖx',size=11)
    box(a,4.2,.9,3,1.1,'Four-way valve',WATER)
    arrow(a,(4.7,2),(3.1,3.1),color=INPUT)
    arrow(a,(6.7,2),(7.6,3.1),color=INPUT)
    arrow(a,(1.1,1.45),(4.2,1.45),'pₛ = 9 × 10⁵ Pa',offset=(0,.4))
    arrow(a,(7.2,1.45),(10.5,1.45),'pₑ = 1 × 10⁵ Pa',offset=(0,.4),color=GRAY)
    txt(a,5.7,.4,'uᵥ ∈ [−10,10] V',color=INPUT)
    arrow(a,(5.3,5.8),(7.1,5.8),'x (m), |x| ≤ 0.125',offset=(0,.4),color=OUTPUT)
    txt(a,5.4,6.65,'Aₖ = 2.8 × 10⁻³ m² • V₀ = 5 × 10⁻⁴ m³',size=11)
    save(f,'05-pneumatic')


def hydrostatic():
    f,a=canvas('Hydrostatic transmission','Section 3.6 • hydraulic coupling with pump and motor displacement control')
    for x,label in [(3,'Pump'),(8.5,'Motor')]:
        a.add_patch(Circle((x,3.5),.85,fc=WATER,ec=INK,lw=2)); txt(a,x,3.5,label)
    line(a,[(3,4.35),(3,5.35),(8.5,5.35),(8.5,4.35)])
    line(a,[(8.5,2.65),(8.5,1.65),(3,1.65),(3,2.65)])
    arrow(a,(4.6,5.35),(6.5,5.35),color=INPUT)
    arrow(a,(6.5,1.65),(4.6,1.65),color=INPUT)
    txt(a,5.7,5.85,'pA'); txt(a,5.7,1.1,'pB')
    txt(a,5.7,3.65,'Δp = pA − pB',color=OUTPUT)
    arrow(a,(.4,3.5),(2.15,3.5),'ωP',offset=(0,.45),color=GRAY)
    arrow(a,(9.35,3.5),(11.35,3.5),'ωM , TLw',offset=(0,.45),color=OUTPUT)
    arrow(a,(1.3,6.3),(2.55,4.15),'uP',offset=(-.35,0))
    arrow(a,(10.4,6.3),(8.9,4.15),'uM',offset=(.35,0))
    txt(a,6,.2,'States: pump angle, motor angle, pressure difference, motor speed\nPublished angle gains and unit scalings require reconciliation before SI simulation.',10)
    save(f,'06-hydrostatic')


def three_tanks():
    f,a=canvas('Three interacting tanks','Section 3.7 • T1 ↔ T3 ↔ T2 connectivity; nominal outlet valves closed')
    for x,lev,name,state in [(1,.78,'T1','h₁'),(5,.60,'T3','h₃'),(9,.42,'T2','h₂')]:
        tank(a,x,2,1.9,3,lev,name)
        arrow(a,(x+.35,2.1),(x+.35,2+3*lev),color=OUTPUT,style='<->')
        txt(a,x+1.15,2+1.5*lev,state+' (m)',size=11,color=OUTPUT)
    arrow(a,(2.9,2.65),(5,2.65),'q₁₃',offset=(0,.3))
    arrow(a,(6.9,2.65),(9,2.65),'q₃₂',offset=(0,.3))
    arrow(a,(1.95,6.2),(1.95,5),'q₁',offset=(-.5,0))
    arrow(a,(9.95,6.2),(9.95,5),'q₂',offset=(.5,0))
    txt(a,6,6.35,'0 ≤ q₁,q₂ ≤ 10⁻⁴ m³/s',color=INPUT)
    txt(a,6,1,'Aₜ = 0.0154 m² • 0 ≤ hᵢ ≤ 0.62 m',size=12)
    txt(a,6,.3,'Internal flows are signed: they reverse when the level difference changes sign.',10)
    save(f,'07-three-tanks')


def bioreactor():
    f,a=canvas('Continuously operated bioreactor','Section 3.8 • dimensionless biomass and substrate-conversion states')
    tank(a,4.3,1.9,3.5,3.6,.72)
    arrow(a,(.5,4.6),(4.3,4.6),'Feed flow u',offset=(0,.4))
    arrow(a,(7.8,2.65),(11.3,2.65),'Equal outflow u',offset=(0,.4))
    line(a,[(6.05,6.05),(6.05,3.4)],lw=2)
    line(a,[(5.45,3.4),(6.65,3.4)],lw=4)
    box(a,5.45,6.05,1.2,.5,'Mixing',size=9)
    txt(a,6.05,2.65,'C₁: biomass\nC₂: conversion',size=12,color=OUTPUT)
    txt(a,6.05,1.05,'Γ = 0.4 • β = 0.02\n0 ≤ C₁,C₂ ≤ 1',size=12)
    txt(a,6,.15,'Control hold: 0.5 time units = 50 Euler substeps of 0.01',size=11)
    save(f,'08-bioreactor')


def cstr():
    f,a=canvas('Jacketed chemical reactor','Section 3.9 • Klatt–Engell reaction network and two manipulated inputs')
    a.add_patch(Rectangle((4,1.6),4,4,fc='#f0e7f7',ec=OUTPUT,lw=2))
    tank(a,4.4,1.9,3.2,3.5,.78)
    txt(a,6,4.25,'A → B → C\n2 A → D',size=15)
    txt(a,6,3.0,'cA, cB (mol/m³)\nT (°C)',size=12,color=OUTPUT)
    txt(a,8.75,4.65,'Jacket\nTc (°C)',color=OUTPUT,ha='left')
    arrow(a,(.2,4.75),(4.35,4.75),'q, cin, Tin',offset=(0,.4))
    arrow(a,(7.65,2.35),(11.2,2.35),'Product stream',offset=(0,.35),color=GRAY)
    arrow(a,(8,1.7),(10.6,.8),'Cooling u₂',offset=(.3,.1),color=INPUT)
    txt(a,2.1,3.4,'u₁ = q / VR\n5–35 h⁻¹',size=12,color=INPUT)
    txt(a,6,.55,'−8.5 ≤ u₂ ≤ 0 MJ/h • temperatures use Celsius in the kinetic model',10)
    save(f,'09-cstr')


def column():
    f,a=canvas('Binary distillation Column A','Section 3.10 • 41 stages and 82 states; only representative trays are drawn')
    a.add_patch(Rectangle((4.6,1.3),2.4,4.5,fc=WATER,ec=INK,lw=2))
    for y in np.linspace(1.9,5.2,6): line(a,[(4.65,y),(6.95,y)],lw=1)
    txt(a,5.8,3.5,'xᵢ , Mᵢ',size=13,color=OUTPUT,bbox={'fc':'white','ec':'none','pad':3})
    arrow(a,(.4,3.5),(4.6,3.5),'F, zF, qF → stage 21',offset=(0,.4))
    box(a,8.2,5.65,2.0,.8,'Condenser',size=11)
    line(a,[(6,5.8),(6,6.65),(9.2,6.65),(9.2,6.45)])
    arrow(a,(10.2,6.05),(11.7,6.05),'D',offset=(0,.35),color=OUTPUT)
    line(a,[(8.2,6.05),(7.65,6.05),(7.65,5.25)])
    arrow(a,(7.65,5.25),(7,5.25),'L',offset=(.35,.3))
    box(a,8.2,.55,2.0,.8,'Reboiler',size=11)
    line(a,[(5.8,1.3),(5.8,.35),(9.2,.35),(9.2,.55)])
    line(a,[(8.2,.95),(7.65,.95),(7.65,1.85)])
    arrow(a,(7.65,1.85),(7,1.85),'V',offset=(.35,.3))
    arrow(a,(10.2,.95),(11.7,.95),'B',offset=(0,.35),color=OUTPUT)
    txt(a,2.3,1.65,'x: mole fraction\nM: kmol\nFlows: kmol/min',size=11)
    save(f,'10-column-a')


def gasifier():
    f,a=canvas('ALSTOM gasifier: control interface','Section 3.11 • nonlinear challenge model with four independent manipulated flows')
    box(a,4.5,1.7,3,3.7,'Gasification\nprocess\n\nOfficial nonlinear\nsimulator',WATER,size=13)
    labels=['Char','Air','Coal','Steam','Limestone']
    for y,label in zip([5.0,4.3,3.6,2.9,2.2],labels):
        arrow(a,(1.7,y),(4.5,y),color=INPUT); txt(a,1.4,y,label,ha='right',color=INPUT)
    txt(a,2.9,1.2,'Limestone/coal ratio fixed',size=10,color=INPUT)
    for y,label in zip([4.85,4.0,3.15,2.3],['Calorific value','Bed mass','Gas pressure','Gas temperature']):
        arrow(a,(7.5,y),(9,y),color=OUTPUT); txt(a,9.15,y,label,ha='left',color=OUTPUT)
    txt(a,10.15,5.7,'Controlled outputs',size=11,color=OUTPUT)
    arrow(a,(6,6.35),(6,5.4),color=GRAY)
    txt(a,6,6.75,'Disturbances: sink pressure, coal quality',size=11,color=GRAY)
    txt(a,6,.3,'Numerical bounds and units must follow the installed official challenge package.',10)
    save(f,'11-gasifier')


def wind():
    f,a=canvas('Wind turbine: reduced structural model','Section 3.12 • tower, blade, drivetrain and pitch dynamics')
    line(a,[(4.7,.7),(5.05,4.8),(5.45,4.8),(5.8,.7),(4.7,.7)],lw=3)
    box(a,4.75,4.8,1.8,.65,'Nacelle',WATER,size=10)
    hub=np.array([4.7,5.1]); a.add_patch(Circle(hub,.17,fc=INK))
    for angle in [90,210,330]:
        theta=np.deg2rad(angle); tip=hub+1.7*np.array([np.cos(theta),np.sin(theta)])
        line(a,[hub,tip],lw=5,color=OUTPUT)
    line(a,[(3.7,.65),(6.6,.65)],lw=3)
    arrow(a,(.2,5.5),(2.4,5.5),'Wind v (m/s)',offset=(0,.4))
    arrow(a,(.2,4.7),(2.4,4.7),color=INPUT)
    arrow(a,(.2,3.9),(2.4,3.9),color=INPUT)
    arrow(a,(4.7,2.2),(6.2,2.2),'yT (m)',offset=(0,.4),color=OUTPUT)
    txt(a,3.1,6.55,'Blade-tip yB (m)',color=OUTPUT,size=11)
    box(a,8.1,4.2,3.2,1.1,'Drivetrain\nθr, θg, ωr, ωg',WATER,size=12)
    arrow(a,(6.55,5.1),(8.1,4.75),'Tr',offset=(0,.4),color=GRAY)
    arrow(a,(11.3,4.75),(11.9,4.75),color=OUTPUT)
    txt(a,9.7,3.55,'Generator torque Tg (N m)',size=11,color=INPUT)
    box(a,8.1,1.2,3.2,1.1,'Pitch actuator\nβdot = (βd − β) / τ',size=11)
    txt(a,9.7,.55,'β, βd in rad • τ = 0.1 s',size=11)
    txt(a,6,0,'Reduced model: 9 states • CT/CQ maps supply aerodynamic forces and torque',10)
    save(f,'12-wind-turbine')


def tennessee():
    f,a=canvas('Tennessee Eastman: plantwide topology','Section 3.13 • conceptual unit connections; stream instrumentation is intentionally omitted')
    box(a,1.1,4.1,2.1,1.3,'Reactor',WATER)
    box(a,4.9,4.1,2.1,1.3,'Condenser',WATER)
    box(a,8.7,4.1,2.1,1.3,'Separator',WATER)
    box(a,8.7,1.3,2.1,1.3,'Stripper',WATER)
    box(a,4.9,1.3,2.1,1.3,'Recycle\ncompressor',WATER,size=11)
    arrow(a,(3.2,4.75),(4.9,4.75),color=GRAY)
    arrow(a,(7,4.75),(8.7,4.75),color=GRAY)
    arrow(a,(9.75,4.1),(9.75,2.6),'Liquid',offset=(.8,0),color=GRAY)
    line(a,[(8.7,4.45),(7.8,4.45),(7.8,1.95)])
    arrow(a,(7.8,1.95),(7,1.95),color=GRAY)
    txt(a,7.8,3.0,'Vapor',ha='right',size=10)
    line(a,[(4.9,1.95),(2.15,1.95),(2.15,4.1)])
    arrow(a,(2.15,3.25),(2.15,4.1),color=GRAY)
    txt(a,3.65,2.35,'Recycle',size=10)
    arrow(a,(.1,4.75),(1.1,4.75),color=INPUT)
    txt(a,2.15,6.05,'Reactant feeds\nA, C, D, E',color=INPUT)
    arrow(a,(2.15,5.7),(2.15,5.4),color=INPUT)
    arrow(a,(10.8,1.95),(11.9,1.95),color=OUTPUT)
    txt(a,9.8,.7,'Products G/H',color=OUTPUT)
    txt(a,6,6.4,'8 species • 12 manipulated inputs • 41 measured outputs',size=12)
    txt(a,6,.05,'Original model: 50 states • archived revised C plant: 50 states (executable NX)',10)
    save(f,'13-tennessee-eastman')


if __name__=='__main__':
    for draw in [pendulum,throttle,pneumatic,hydrostatic,three_tanks,bioreactor,cstr,column,gasifier,wind,tennessee]: draw()
    print('Saved 11 original schematics as SVG and PNG in benchmarks/figures')
