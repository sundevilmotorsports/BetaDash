"""
Portrait 2‑column PDF

LEFT column (top➜bottom)
 1. CSV File Details  (font 7 pt, taller)
 2. Session Summary   (font 7 pt, taller)
 3. Track Conditions  (font 7 pt, taller)
 4. Tire Data         (slightly shorter)
 5. Detailed Tyre Table (slightly shorter)

RIGHT column
 1. Ride Height vs Speed graph
 2. Lap Time per Lap graph

Output → <output_dir>/combined_output.pdf
"""

import os, glob, pandas as pd, matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame,
                                Table, TableStyle, KeepInFrame,
                                Image, Spacer)

# ────────────────────────────────────────────────
# 0. Paths
csv_dir = r"C:\Users\adams\OneDrive\Documents\GitHub\BetaDash\CSVs"
out_dir = r"C:\Users\adams\OneDrive\Documents\GitHub\BetaDash\pdf_export"
os.makedirs(out_dir, exist_ok=True)

# ────────────────────────────────────────────────
# 1. CSV
csv = glob.glob(os.path.join(csv_dir, "*.csv"))[0]
df  = pd.read_csv(csv)
parts = os.path.splitext(os.path.basename(csv))[0].split("_")
if len(parts) >= 6:
    date_str, hm, driver_str, racecar_str, location_str = parts[1:6]
    time_str = f"{hm[:2]}:{hm[2:]}"
else:
    date_str = time_str = driver_str = racecar_str = location_str = "?"

# ────────────────────────────────────────────────
# 2. Sizing
INCH = 72
PAGE_W, PAGE_H = letter
MARGIN = 18
COL_W  = (PAGE_W - 3*MARGIN) / 2
GRAPH_H = 110

def save_graph(path, fn, w_pt=COL_W, h_pt=GRAPH_H):
    plt.rcParams.update({"font.size":6,"axes.labelsize":6,
                         "xtick.labelsize":5,"ytick.labelsize":5,
                         "axes.titlesize":7})
    plt.figure(figsize=(w_pt/INCH, h_pt/INCH), dpi=300)
    fn(); plt.tight_layout(pad=0.2); plt.savefig(path,dpi=300); plt.close()

# ────────────────────────────────────────────────
# 3. Graphs
p_lap = os.path.join(out_dir, "lap_time.png")
save_graph(p_lap, lambda: (
    plt.plot(df.groupby('Lap (#)')['Time (s)']
               .agg(lambda x:x.max()-x.min()), marker='o'),
    plt.xlabel('Lap'), plt.ylabel('Time (s)'), plt.title('Lap Time per Lap')
))

p_rh  = os.path.join(out_dir, "ride_height.png")
def g_rh():
    f=["LF shock defl (mm)","RF shock defl (mm)"]
    r=["LR shock defl (mm)","RR shock defl (mm)"]
    if all(c in df.columns for c in f+r):
        df['FrontRH']=df[f].mean(axis=1); df['RearRH']=df[r].mean(axis=1)
    else: df['FrontRH']=df['RearRH']=0
    df['SpeedK']=df.get('Speed (m/s)',pd.Series([0]*len(df)))*3.6
    plt.plot(df['SpeedK'],df['FrontRH'],label='Front')
    plt.plot(df['SpeedK'],df['RearRH'], label='Rear')
    plt.xlabel('Speed (kph)'); plt.ylabel('Ride Height (mm)')
    plt.title('Ride Height vs Speed'); plt.legend()
save_graph(p_rh,g_rh)

# ────────────────────────────────────────────────
# 4. ReportLab helpers
def img(path,w=COL_W,h=GRAPH_H): return Image(path,width=w,height=h)
def box(items,w,h): return KeepInFrame(w,h,items,hAlign='LEFT',vAlign='TOP',
                                       fakeWidth=True)

def _tbl(title,data,col_w,font_sz):
    t=Table([[title]+['']*(len(data[0])-1)]+data,colWidths=col_w)
    st=TableStyle([('GRID',(0,0),(-1,-1),0.25,colors.black),
                   ('BACKGROUND',(0,0),(-1,0),colors.lightgrey),
                   ('SPAN',(0,0),(-1,0)),
                   ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
                   ('FONTSIZE',(0,0),(-1,-1),font_sz),
                   ('LEFTPADDING',(0,0),(-1,-1),1),
                   ('RIGHTPADDING',(0,0),(-1,-1),1)])
    t.setStyle(st); return t
def big_table(title,data,col_w):   return _tbl(title,data,col_w,7)
def small_table(title,data,col_w): return _tbl(title,data,col_w,6)

# ── Tire Data table (two values/tyre) ────────────────────────
def tire_data_table(comp="Soft",
                    cold_FL=("",""), cold_RL=("",""),
                    hot_FR=("",""),  hot_RR=("","")):
    col_w=[COL_W/6]*6
    rows=[["Compound:", "", "", comp, "", ""],
          ["Cold Press.", "", "", "Hot Press.", "", ""],
          ["FL", *cold_FL, "FR", *hot_FR],
          ["RL", *cold_RL, "RR", *hot_RR]]
    t=Table(rows,colWidths=col_w,hAlign='LEFT')
    st=TableStyle([('GRID',(0,0),(-1,-1),0.6,colors.black),
                   ('FONTNAME',(0,0),(-1,-1),'Helvetica'),
                   ('FONTSIZE',(0,0),(-1,-1),6),
                   ('ALIGN',(0,0),(-1,-1),'CENTER'),
                   ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                   ('BACKGROUND',(3,0),(5,0),colors.red),
                   ('TEXTCOLOR',(3,0),(5,0),colors.white),
                   ('FONTNAME',(3,0),(5,0),'Helvetica-Bold'),
                   ('FONTNAME',(0,0),(2,0),'Helvetica-Bold'),
                   ('FONTNAME',(0,1),(2,1),'Helvetica-Bold'),
                   ('FONTNAME',(3,1),(5,1),'Helvetica-Bold'),
                   ('SPAN',(0,0),(2,0)), ('SPAN',(3,0),(5,0)),
                   ('SPAN',(0,1),(2,1)), ('SPAN',(3,1),(5,1))])
    t.setStyle(st)
    hdr=Table([["Tire Data"]],[COL_W],style=[
        ('GRID',(0,0),(-1,-1),0.6,colors.black),
        ('BACKGROUND',(0,0),(-1,0),colors.lightgrey),
        ('ALIGN',(0,0),(-1,0),'CENTER'),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,0),7)])
    return [hdr, Spacer(1,2), t]

# ── Detailed Tyre Table (restored good version) ──────────────
def tyre_block_table():
    sec_titles=["Tread Remaining","Wear Rate (%/Lap)",
                "Average Temps","Peak Temps"]
    rows,spans,reds=[],[],[]
    for sec in sec_titles:
        base=len(rows)
        rows.append([sec]+['']*5); spans.append(('SPAN',(0,base),(-1,base)))
        rows.append(['FL','','','FR','',''])
        spans.extend([('SPAN',(0,base+1),(2,base+1)),
                      ('SPAN',(3,base+1),(5,base+1))])
        rows.append(['']*6); reds.append(base+2)
        rows.append(['RL','','','RR','',''])
        spans.extend([('SPAN',(0,base+3),(2,base+3)),
                      ('SPAN',(3,base+3),(5,base+3))])
        rows.append(['']*6); reds.append(base+4)
    t=Table(rows,colWidths=[COL_W/6]*6)
    st=TableStyle([('GRID',(0,0),(-1,-1),0.6,colors.black),
                   ('FONTNAME',(0,0),(-1,-1),'Helvetica'),
                   ('FONTSIZE',(0,0),(-1,-1),6),
                   ('ALIGN',(0,0),(-1,-1),'CENTER'),
                   ('VALIGN',(0,0),(-1,-1),'MIDDLE')])
    for r in range(0,len(rows),5):
        st.add('BACKGROUND',(0,r),(-1,r),colors.lightgrey)
        st.add('FONTNAME',(0,r),(-1,r),'Helvetica-Bold')
    for sp in spans: st.add(*sp)
    for r in reds:   st.add('BACKGROUND',(0,r),(-1,r),
                            colors.HexColor('#f7b2b2'))
    t.setStyle(st); return t

# ────────────────────────────────────────────────
# 5. Data
lap_span = df.groupby('Lap (#)')['Time (s)'].agg(lambda x:x.max()-x.min())
tot_laps = df['Lap (#)'].max()
csv_details=[["Date",date_str],["Time",time_str],["Location",location_str],
             ["Racecar",racecar_str],["Driver",driver_str]]
session_summary=[
 ["Total Laps", tot_laps],
 ["Fastest Lap", lap_span.idxmin() if not lap_span.empty else ""],
 ["Fastest Lap Time (s)", lap_span.min() if not lap_span.empty else ""],
 ["Top Speed (kph)", df['Speed (m/s)'].max()*3.6
                       if 'Speed (m/s)' in df.columns else ""],
 ["Peak Accel (g)",""],["Peak Braking (g)",""],["Peak Cornering (g)",""],
 ["Fuel Consumption (kg/lap)",""],["% Time WOT",""],
 ["Tools Pre (F/R/WJ/BB)",""],["Tools Post",""]]
track_conditions=[["Ambient Temp (°C)",""],["Track Temp (°C)",""],
                  ["Wind Speed (kph)",""]]

# ────────────────────────────────────────────────
# 6. Frames
doc=BaseDocTemplate(os.path.join(out_dir,"combined_output.pdf"),
                    pagesize=letter,
                    leftMargin=MARGIN,rightMargin=MARGIN,
                    topMargin=MARGIN,bottomMargin=MARGIN)
frame_L=Frame(MARGIN,MARGIN,COL_W,PAGE_H-2*MARGIN,id='L')
frame_R=Frame(2*MARGIN+COL_W,MARGIN,COL_W,PAGE_H-2*MARGIN,id='R')
doc.addPageTemplates(PageTemplate(id='TwoCol',frames=[frame_L,frame_R]))

# ────────────────────────────────────────────────
# 7. Story
left=[
 box([big_table("CSV File Details",csv_details,[90,COL_W-90])],COL_W,100),
 Spacer(1,6),
 box([big_table("Session Summary",session_summary,
                [COL_W*0.45,COL_W*0.55])],COL_W,170),
 Spacer(1,6),
 box([big_table("Track Conditions",track_conditions,
                [110,COL_W-110])],COL_W,60),
 Spacer(1,6),
 box(tire_data_table(comp="Soft",
                     cold_FL=("16","16"),  cold_RL=("14.5","14.5"),
                     hot_FR=("21.4","21.1"), hot_RR=("20","19.6")),
     COL_W,80),
 Spacer(1,6),
 box([tyre_block_table()],COL_W,280),
]

right=[img(p_rh),Spacer(1,4),img(p_lap),Spacer(1,4)]
doc.build(left+right)
print("PDF saved →", os.path.join(out_dir,"combined_output.pdf"))
