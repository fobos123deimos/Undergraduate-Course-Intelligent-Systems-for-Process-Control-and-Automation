"""Draw editable teaching diagrams; plotted curves are schematic, not results."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Circle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "course" / "figures" / "learning"
INK, BLUE, TEAL, ORANGE, PALE = "#173b4d", "#246da0", "#16877b", "#d78b28", "#e7f1f5"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "text.color": INK,
                     "axes.labelcolor": INK, "svg.fonttype": "none", "svg.hashsalt": "intelligent-course-learning"})


def canvas(unit, title, subtitle):
    fig, ax = plt.subplots(figsize=(14, 6.6))
    fig.subplots_adjust(left=.035, right=.97, top=.80, bottom=.15)
    fig.text(.04, .94, f"{unit:02d}  /  {title}", fontsize=22, weight="bold", color=INK)
    fig.text(.04, .88, subtitle, fontsize=12, color=INK)
    fig.text(.04, .04, "Concept diagram  |  Curves and signals are illustrative; computed evidence is shown separately.", fontsize=10, color="#596e78")
    ax.set(xlim=(0, 14), ylim=(0, 6)); ax.axis("off")
    return fig, ax


def box(ax, x, y, text, width=2.5, height=1, color=PALE):
    ax.add_patch(FancyBboxPatch((x, y), width, height, boxstyle="round,pad=0.08,rounding_size=.12", ec=INK, fc=color, lw=1.4))
    ax.text(x+width/2, y+height/2, text, ha="center", va="center", fontsize=11)


def arrow(ax, a, b, label=None, color=BLUE):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle="-|>",mutation_scale=15,lw=1.8,color=color))
    if label:
        vertical=abs(a[0]-b[0])<.1
        ax.text((a[0]+b[0])/2+(.15 if vertical else 0),(a[1]+b[1])/2+(.05 if vertical else .2),label,ha="left" if vertical else "center",va="bottom",fontsize=10,color=color)


def save(fig, unit):
    OUT.mkdir(parents=True,exist_ok=True)
    for suffix in ("png","svg"):
        options={"metadata":{"Date":None}} if suffix=='svg' else {}
        fig.savefig(OUT/f"unit-{unit:02d}.{suffix}",dpi=160,facecolor="white",**options)
    plt.close(fig)


def main():
    fig, ax = canvas(1,"From a boundary to a predictor","Balance first; choose excitation and keep the validation trajectory independent.")
    ax.add_patch(Rectangle((1.3,1.3),3.4,2.7,ec=INK,fc=PALE,lw=2))
    ax.plot([1.3,4.7],[3.3,3.3],color=BLUE,ls="--")
    ax.text(3,2.35,"Perfectly mixed tank\nV = 100 L\nconcentration c(t)",ha="center",va="center")
    arrow(ax,(.1,4.7),(2,4.7),"q u"); arrow(ax,(2,4.7),(2,3.5))
    arrow(ax,(6,4.7),(4,4.7),"q (1-u)"); arrow(ax,(4,4.7),(4,3.5))
    arrow(ax,(4.7,1.7),(6.1,1.7),"q, c")
    ax.text(3,.6,r"$V\dot c=q(u-c)$",ha="center",fontsize=17)
    box(ax,7,4.3,"Bounded training input",5,.8); box(ax,7,2.8,"Fit ARX on training only",5,.8)
    box(ax,7,1.1,"Fresh input: one-step prediction\nand recursive free-run",5,1.1)
    arrow(ax,(9.5,4.2),(9.5,3.65)); arrow(ax,(9.5,2.7),(9.5,2.25))
    save(fig,1)

    fig,ax=canvas(2,"Feedback, tuning and saturation","The integral state needs its own protection when an actuator reaches a bound.")
    box(ax,1,3.1,"PI / filtered PID",2.5); box(ax,4.8,3.1,"Saturation",2); box(ax,8.2,3.1,"Tank dynamics",2.6)
    arrow(ax,(.1,3.6),(1,3.6),"error"); arrow(ax,(3.6,3.6),(4.7,3.6),"command")
    arrow(ax,(6.9,3.6),(8.1,3.6),"applied u"); arrow(ax,(10.9,3.6),(13.2,3.6),"measured y")
    ax.plot([12,12,1.9],[3.6,1.7,1.7],color=BLUE,lw=1.8); arrow(ax,(1.9,1.7),(1.9,3))
    ax.text(7,1.2,"Negative feedback: e = r - y",ha="center")
    box(ax,4.8,4.9,"Stop integration when it drives\nthe saturated command outward",6,.8,color="#fff0d7")
    arrow(ax,(5.8,4.2),(5.8,4.8),color=ORANGE)
    ax.text(7,.35,r"$K_p=\tau/[K(\lambda+\theta)],\qquad K_i=K_p/\tau$",ha="center",fontsize=17)
    save(fig,2)

    fig,ax=canvas(3,"Cascade separates fast and slow feedback","Inner flow feedback can correct an actuator disturbance before the slower concentration loop.")
    for x,text in [(1,"Outer controller\nconcentration"),(4.5,"Inner controller\nflow"),(8,"Actuator"),(11,"Tank")]:box(ax,x,3.7,text,2 if x>7 else 2.5)
    arrow(ax,(.1,4.2),(1,4.2),"r"); arrow(ax,(3.6,4.2),(4.4,4.2),"flow target"); arrow(ax,(7.1,4.2),(7.9,4.2)); arrow(ax,(10.1,4.2),(10.9,4.2)); arrow(ax,(13.1,4.2),(13.8,4.2))
    arrow(ax,(9,5.8),(9,4.8),"supply disturbance",color=ORANGE)
    ax.plot([10.4,10.4,5.7],[4.2,2.6,2.6],color=TEAL,lw=1.8);arrow(ax,(5.7,2.6),(5.7,3.6),color=TEAL)
    ax.text(8.3,2.1,"Measured flow: fast inner feedback",ha="center",color=TEAL)
    ax.plot([13.5,13.5,2.2],[4.2,.9,.9],color=BLUE,lw=1.8);arrow(ax,(2.2,.9),(2.2,3.6))
    ax.text(7.4,.4,"Measured concentration: slower outer feedback",ha="center")
    save(fig,3)

    fig,ax=canvas(4,"Receding-horizon decisions","Predict several future outputs, constrain planned inputs, apply one action and remeasure.")
    fig.subplots_adjust(left=.095, bottom=.19)
    ax.set_axis_on();ax.set(xlim=(-4,10),ylim=(0,1.15),xlabel="Samples relative to the current decision",ylabel="Normalized output (schematic)")
    x=np.arange(-4,1);ax.plot(x,[.1,.18,.22,.30,.38],"o-",color=INK,label="past measurements")
    future=np.arange(0,11);ax.plot(future,.9-(.9-.38)*np.exp(-future/3),"o--",color=BLUE,label="model prediction")
    ax.axhline(.9,color=TEAL,ls=":",label="target");ax.axvline(0,color=INK,lw=1)
    ax.axvspan(0,1,color=ORANGE,alpha=.15,label="first applied action")
    ax.annotate("At the next sample:\nupdate state and optimize again",xy=(1,.52),xytext=(3,.23),arrowprops={"arrowstyle":"->","color":ORANGE},color=INK)
    ax.grid(alpha=.18);ax.legend(loc="upper left",ncol=2,fontsize=9)
    save(fig,4)

    fig,ax=canvas(5,"From fuzzy membership to an applied action","Membership is a degree of rule activation, not a probability of closed-loop success.")
    x=np.linspace(-1,1,201)
    for center,color,label in [(-1,BLUE,"negative"),(0,TEAL,"zero"),(1,ORANGE,"positive")]:
        y=np.maximum(0,1-np.abs(x-center));ax.plot(1+3.8*(x+1)/2,2.8+2*y,color=color,lw=2.4)
        ax.text(1+3.8*(center+1)/2,5.1,label,ha="center",color=color)
    ax.plot([1,4.8],[2.8,2.8],color=INK);ax.text(2.9,2.2,"Scaled error or error change",ha="center")
    box(ax,6.4,3.4,"Rule firing\nAND / aggregation",2.5,1.2);box(ax,10.3,3.4,"Defuzzification\nand bounded action",2.8,1.2)
    arrow(ax,(4.9,3.9),(6.3,3.9));arrow(ax,(9,3.9),(10.2,3.9))
    ax.text(7,1.1,"Mamdani: centroid of an aggregated output set\nSugeno: normalized weighted average of consequents",ha="center",fontsize=13)
    save(fig,5)

    fig,ax=canvas(6,"Separate learning from evaluation","Normalization, features and weights are fitted before the test trajectory is exposed.")
    for x,label,col in [(1,"Training",TEAL),(5.3,"Validation",ORANGE),(9.6,"Final test",BLUE)]:
        box(ax,x,4,label,3.3,.8,color=PALE);ax.plot([x,x+3.3],[5.3,5.3],lw=8,color=col,solid_capstyle="butt")
    box(ax,1,2,"Fit normalization\nand MLP / RBF",3.3,1.1);box(ax,5.3,2,"Choose architecture\nthen freeze settings",3.3,1.1)
    box(ax,9.6,2,"One-step, free-run\nand out-of-domain",3.3,1.1)
    for x in (2.65,6.95,11.25):arrow(ax,(x,3.9),(x,3.2))
    arrow(ax,(4.4,2.55),(5.2,2.55));arrow(ax,(8.7,2.55),(9.5,2.55))
    ax.text(7,.8,"One-step uses measured history; free-run feeds predictions back into the regressor.",ha="center",fontsize=12)
    save(fig,6)

    fig,ax=canvas(7,"Evolutionary tuning is an experiment","Respect the search budget and test the winning candidate on a fresh scenario.")
    for x,label in [(1,"Bounded population\nreal or binary"),(5.2,"Simulate candidates\nand score objective"),(9.4,"Selection, crossover\nmutation + elitism")]:box(ax,x,3.6,label,3.3,1.2)
    arrow(ax,(4.4,4.2),(5.1,4.2));arrow(ax,(8.6,4.2),(9.3,4.2))
    ax.plot([11,11,2.65],[3.5,2.4,2.4],color=BLUE,lw=1.8);arrow(ax,(2.65,2.4),(2.65,3.5))
    ax.text(7,3.0,"Repeat a fixed number of generations;\nretain the best feasible candidate.",ha="center",va="center")
    box(ax,4.3,.2,"Freeze gains; evaluate changed residence time",5.4,.9,color="#fff0d7")
    arrow(ax,(7,2.3),(7,1.2),color=ORANGE)
    save(fig,7)

    fig,ax=canvas(8,"A comparison is a matrix of matched experiments","Use identical targets, disturbances and noise within each scenario; disclose extra information.")
    columns=["PI","Fuzzy gain PID","Feedforward PI"]
    for j,label in enumerate(columns):ax.text(4.2+j*3.1,5.3,label,ha="center",weight="bold")
    for i,tau in enumerate([7,10,14]):
        y=3.8-i*1.35;ax.text(.7,y+.45,f"tau = {tau} min",va="center")
        for j in range(3):box(ax,2.8+j*3.1,y,"Same scenario\nrecord all metrics",2.8,.9)
    ax.text(7,-.05,"Track error + actuator effort + constraints; no single score establishes general superiority.",ha="center",fontsize=11)
    save(fig,8)

    fig,ax=canvas(9,"Hidden states, observations and causal decisions","The filter uses the present and past; smoothing and Viterbi use the full record.")
    for i,label in enumerate([r"$z_{k-1}$",r"$z_k$",r"$z_{k+1}$"]):
        x=2.3+i*4.2;ax.add_patch(Circle((x,4.8),.52,ec=INK,fc=PALE,lw=1.7));ax.text(x,4.8,label,ha="center",va="center",fontsize=17)
        box(ax,x-1.05,2.4,rf"Observation $o_{{{['k-1','k','k+1'][i]}}}$",2.1,.8)
        arrow(ax,(x,4.2),(x,3.3),"emission B")
        if i<2:arrow(ax,(x+.6,4.8),(x+3.6,4.8),"transition P")
    box(ax,2.1,.3,"Past + present observations",4.3,.9);box(ax,8,.3,"Causal posterior -> PI compensation",5.2,.9)
    arrow(ax,(6.5,.75),(7.9,.75));ax.plot([8.4,8.4],[2,4.6],color=ORANGE,ls="--")
    ax.text(10.7,1.75,"Future observation unavailable online",color=ORANGE,ha="center",fontsize=10)
    save(fig,9)
    print("Built nine conceptual diagrams in PNG and editable SVG.")


if __name__ == "__main__":main()
