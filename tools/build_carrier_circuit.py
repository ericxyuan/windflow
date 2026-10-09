"""Capture the E3 carrier as editable native KiCad schematics and a checked netlist.

This first milestone is circuit capture, not a routed/fabrication PCB release.
Run with the project's portable KiCad Python, or any Python (CLI is independent).
"""
from __future__ import annotations
import collections
import hashlib
import json
from pathlib import Path
import re
import subprocess
import uuid
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware/pcb/carrier"
RUNTIME = ROOT / ".tools/kicad-10.0.6"
CLI = RUNTIME / "bin/kicad-cli.exe"
LIB = OUT / "WindflowCarrier.pretty"
NAME = "windflow-carrier"
NS = uuid.UUID("2d217faa-678f-5af0-88dd-7571a67a0eb4")
ROOT_UUID = str(uuid.uuid5(NS,"root"))
COMPONENTS = []
COMMANDS = []
FP_SOURCES = {}
SCHEMATIC_REVISION = "E3"
CAPTURE_DATE = "2026-10-05"
BOARD_SCOPE = "Board allowance90x65mm; component placement awaits pressure hose and harness keepouts."
FLAG_NETS = ["RAW_FUSED","REG12V","REG5_LOGIC","REG5_SERVO","FAN_FUSED","SERVO_FUSED","+3V3","GND","EF_RTN"]
SHEET_SPACING = 62
SHEET_COLUMNS = 2
SHEET_WIDTH = 155
SHEET_X_STEP = 180

def uid(value):
    return str(uuid.uuid5(NS,value))

def q(value):
    return json.dumps(str(value),ensure_ascii=True)

def write(path,value):
    path = Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(value,encoding="utf-8",newline="\n")

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def pin(number,name,net,kind="passive"):
    return {"number":str(number),"name":name,"net":net,"type":kind}

def add(ref,value,mpn,group,pins,footprint="",datasheet="",dnp=False,location="carrier",note=""):
    assert not any(item["ref"]==ref for item in COMPONENTS),ref
    item={"ref":ref,"value":value,"mpn":mpn,"group":group,"pins":pins,
          "footprint_source":footprint,"datasheet":datasheet,"dnp":dnp,"location":location,"note":note}
    COMPONENTS.append(item)
    return item

def resistor(ref,value,a,b,group,mpn=None,dnp=False,location="carrier"):
    order={"100k":"RC0603FR-07100KL","10k":"RC0603FR-0710KL","4.7k":"RC0603FR-074K7L",
           "3.9k":"RC0603FR-073K9L","1M":"RC0603FR-071ML","100":"RC0603FR-07100RL",
           "330":"RC0603FR-07330RL","33":"RC0603FR-0733RL","1k":"RC0603FR-071KL",
           "8.06k":"RC0603FR-078K06L","402k":"RC0603FR-07402KL","15k":"RC0603FR-0715KL","130k":"RC0603FR-07130KL"}
    part=mpn or order[value]
    footprint="Resistor_SMD:R_1206_3216Metric" if part=="RC1206FR-07330RL" else "Resistor_SMD:R_0603_1608Metric"
    return add(ref,value+" 1%","Yageo "+part,group,[pin(1,"1",a),pin(2,"2",b)],footprint,dnp=dnp,location=location)

def capacitor(ref,value,a,b,group,location="carrier"):
    ceramic={"100nF":"GRM188R71H104KA93D","10nF":"GRM188R71C103KA01D","1uF":"GRM188R71E105KA12D"}
    if value in ceramic:
        mpn="Murata "+ceramic[value];fp="Capacitor_SMD:C_0603_1608Metric"
    elif value=="100uF/25V":
        mpn="Panasonic EEU-FR1E101";fp="Capacitor_THT:CP_Radial_D6.3mm_P2.50mm"
    elif value=="470uF/10V":
        mpn="Panasonic EEU-FR1A471";fp="Capacitor_THT:CP_Radial_D8.0mm_P3.50mm"
    else:
        raise ValueError(value)
    return add(ref,value,mpn,group,[pin(1,"+" if "/" in value else "1",a),pin(2,"-" if "/" in value else "2",b)],fp,location=location)

def xh(ref,n,nets,group,note=""):
    return add(ref,f"XH {n}",f"JST B{n}B-XH-A(LF)(SN)",group,
               [pin(i+1,str(i+1),net) for i,net in enumerate(nets)],
               f"Connector_JST:JST_XH_B{n}B-XH-A_1x{n:02d}_P2.50mm_Vertical",
               "https://www.jst-mfg.com/product/pdf/eng/eXH.pdf",note=note)

def header(ref,n,nets,group,mpn,note=""):
    return add(ref,f"2.54mm {n}",mpn,group,[pin(i+1,str(i+1),net) for i,net in enumerate(nets)],
               f"Connector_PinHeader_2.54mm:PinHeader_1x{n:02d}_P2.54mm_Vertical",note=note)

def load_switch(ref,vin,vout,en,group):
    ct=ref+"_CT";qod=ref+"_QOD"
    return add(ref,"TPS22810DBVR","Texas Instruments TPS22810DBVR",group,
               [pin(1,"VIN",vin,"power_in"),pin(2,"GND","GND","power_in"),pin(3,"EN",en,"input"),
                pin(4,"CT",ct,"passive"),pin(5,"QOD",qod,"passive"),pin(6,"VOUT",vout,"power_out")],
               "Package_TO_SOT_SMD:SOT-23-6","https://www.ti.com/lit/ds/symlink/tps22810.pdf")

def quad_buffer(ref,group,supply,channels):
    pins=[pin(7,"GND","GND","power_in"),pin(14,"VCC",supply,"power_in")]
    for (oe,a,y), (input_net,output_net,enabled) in zip(((1,2,3),(4,5,6),(10,9,8),(13,12,11)),channels):
        pins += [pin(oe,"~{OE}","GND" if enabled else supply,"input"),
                 pin(a,"A",input_net,"input"),pin(y,"Y",output_net,"output")]
    return add(ref,"74AHCT125D,118","Nexperia 74AHCT125D,118",group,sorted(pins,key=lambda v:int(v["number"])),
               "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm","https://assets.nexperia.com/documents/data-sheet/74AHC_AHCT125.pdf")

def population():
    g="power"
    xh("J1",2,["PD_RAW","GND"],g,"HUSB238 PD output; physical breakout is remote")
    add("F1","2A","Littelfuse 0451002.MRL",g,[pin(1,"1","PD_RAW"),pin(2,"2","RAW_FUSED")],"Fuse:Fuse_2410_6125Metric")
    add("D1","SMBJ18A","Littelfuse SMBJ18A",g,[pin(1,"K","RAW_FUSED"),pin(2,"A","GND")],"Diode_SMD:D_SMB")
    capacitor("C1","100nF","RAW_FUSED","GND",g)
    add("EF1","TPS26600PWPR","Texas Instruments TPS26600PWPR",g,[
        pin(1,"IN","RAW_FUSED","power_in"),pin(2,"IN","RAW_FUSED"),pin(3,"UVLO","EF_UVLO","input"),pin(4,"NC",None,"no_connect"),
        pin(5,"OVP","EF_OVP","input"),pin(6,"MODE","EF_MODE"),pin(7,"SHDN","EF_UVLO","input"),pin(8,"RTN","EF_RTN","power_in"),
        pin(9,"GND","GND","power_in"),pin(10,"IMON",None,"output"),pin(11,"ILIM","EF_ILIM"),pin(12,"DVDT","EF_DVDT"),
        pin(13,"NC",None,"no_connect"),pin(14,"~{FLT}",None,"open_collector"),pin(15,"OUT","BUS_PROTECTED","power_out"),
        pin(16,"OUT","BUS_PROTECTED"),pin(17,"EP","EF_RTN","power_in")],
        "Package_SO:HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3.4x5mm_Mask2.66x2.46mm_ThermalVias",
        "https://www.ti.com/lit/ds/symlink/tps2660.pdf",note="EP17 and pin8 use isolated EF_RTN; never merge with GND")
    capacitor("C2","100uF/25V","BUS_PROTECTED","GND",g)
    for ref,value,a,b in [("R42","8.06k","EF_ILIM","EF_RTN"),("R43","402k","EF_MODE","EF_RTN"),
                          ("R44","100k","RAW_FUSED","EF_UVLO"),("R45","15k","EF_UVLO","EF_RTN"),
                          ("R46","130k","RAW_FUSED","EF_OVP"),("R47","10k","EF_OVP","EF_RTN")]:
        resistor(ref,value,a,b,g)
    capacitor("C29","100nF","EF_DVDT","EF_RTN",g)
    # The remote module's EN is not one of these connector nets. NC cavities are
    # physical pads with explicit no-connect flags, not secretly shorted pins.
    for ref,n,supply,pg,mpn in [("J17",6,"REG12V","PG_FAN","43045-0612"),
                               ("J18",4,"REG5_LOGIC",None,"43045-0412"),
                               ("J19",8,"REG5_SERVO","PG_SERVO","43045-0812")]:
        nets=["GND","BUS_PROTECTED",supply,pg]+[None]*(n-4)
        add(ref,mpn,"Molex "+mpn,g,[pin(i+1,str(i+1),net) for i,net in enumerate(nets)],
            f"Connector_Molex:Molex_Micro-Fit_3.0_{mpn}_2x{n//2:02d}_P3.00mm_Vertical",
            "https://www.molex.com/pdm_docs/sd/430450212_sd.pdf",
            note="Remote regulator; different shrouded cavity count. Module EN is NC. Mating/placement qualification pending")
    for index,supply in enumerate(("REG12V","REG5_LOGIC","REG5_SERVO"),3):
        capacitor(f"C{index}","1uF","BUS_PROTECTED","GND",g)
        capacitor(f"C{index+3}","100uF/25V",supply,"GND",g)
    add("D2","SS14-E3/61T","Vishay SS14-E3/61T",g,[pin(1,"K","PICO_VSYS"),pin(2,"A","REG5_LOGIC")],"Diode_SMD:D_SMA")

    g="fan_servo"
    for ref,value,source,dest,mpn in [("F2","0.5A","REG12V","FAN_FUSED","0451.500MRL"),
                                      ("F3","1A","REG5_SERVO","SERVO_FUSED","0451001.MRL")]:
        add(ref,value,"Littelfuse "+mpn,g,[pin(1,"1",source),pin(2,"2",dest)],"Fuse:Fuse_2410_6125Metric")
    load_switch("SW1","FAN_FUSED","FAN12_SWITCHED","EN_FAN",g)
    load_switch("SW2","SERVO_FUSED","SERVO5_SWITCHED","EN_SERVO",g)
    for sw,input_cap,ct_cap,res,en in [("SW1","C11","C14","R39","EN_FAN"),("SW2","C12","C15","R40","EN_SERVO")]:
        capacitor(input_cap,"1uF","FAN_FUSED" if sw=="SW1" else "SERVO_FUSED","GND",g)
        capacitor(ct_cap,"100nF",sw+"_CT","GND",g)
        resistor(res,"330",sw+"_QOD","FAN12_SWITCHED" if sw=="SW1" else "SERVO5_SWITCHED",g,"RC1206FR-07330RL")
    resistor("R10","100k","EN_FAN","GND",g);resistor("R11","100k","EN_SERVO","GND",g)
    add("Q1","2N7002,215","Nexperia 2N7002,215",g,[pin(1,"G","FAN_PWM_GATE","input"),pin(2,"S","GND"),pin(3,"D","FAN_PWM_OD","open_collector")],"Package_TO_SOT_SMD:SOT-23","https://www.nexperia.com/product/2N7002")
    resistor("R13","100","FAN_PWM_GPIO","FAN_PWM_GATE",g);resistor("R14","100k","FAN_PWM_GATE","GND",g)
    add("J3","FAN 4-pin","Molex 470531000",g,[pin(1,"GND","GND"),pin(2,"12V","FAN12_SWITCHED"),pin(3,"TACH","FAN_TACH"),pin(4,"PWM","FAN_PWM_OD")],"Connector:FanPinHeader_1x04_P2.54mm_Vertical")
    resistor("R4","4.7k","+3V3","FAN_TACH",g)
    add("BUF3","74AHCT1G125GW,125","Nexperia 74AHCT1G125GW,125",g,[pin(1,"~{OE}","GND","input"),pin(2,"A","SERVO_PWM_GPIO","input"),pin(3,"GND","GND","power_in"),pin(4,"Y","SERVO_BUF_OUT","output"),pin(5,"VCC","SERVO5_SWITCHED","power_in")],"Package_TO_SOT_SMD:SOT-353_SC-70-5","https://assets.nexperia.com/documents/data-sheet/74AHC_AHCT1G125.pdf")
    capacitor("C19","100nF","SERVO5_SWITCHED","GND",g)
    resistor("R23","100k","SERVO_PWM_GPIO","GND",g);resistor("R17","330","SERVO_BUF_OUT","SERVO_SIGNAL",g);resistor("R24","100k","SERVO_SIGNAL","GND",g)
    capacitor("C9","470uF/10V","SERVO5_SWITCHED","GND",g)
    header("J4",3,["GND","SERVO5_SWITCHED","SERVO_SIGNAL"],g,"Samtec TSW-103-07-G-S","Original servo plug, retain and label polarity")
    header("J5",1,["SERVO_FEEDBACK_RAW"],g,"Samtec TSW-101-07-G-S")
    resistor("R8","4.7k","+3V3","PG_SERVO",g);resistor("R9","4.7k","+3V3","PG_FAN",g)

    g="ambient"
    load_switch("SW3","REG5_LOGIC","AMBIENT5_SWITCHED","EN_AMBIENT",g)
    capacitor("C13","1uF","REG5_LOGIC","GND",g);capacitor("C16","100nF","SW3_CT","GND",g)
    resistor("R41","330","SW3_QOD","AMBIENT5_SWITCHED",g,"RC1206FR-07330RL")
    resistor("R12","100k","EN_AMBIENT","GND",g);capacitor("C10","470uF/10V","AMBIENT5_SWITCHED","GND",g)
    quad_buffer("BUF1",g,"AMBIENT5_SWITCHED",[("GND",None,False),("AMBIENT_DATA_GPIO","AMBIENT_BUF_OUT",True),("GND",None,False),("GND",None,False)])
    capacitor("C17","100nF","AMBIENT5_SWITCHED","GND",g)
    resistor("R19","100k","AMBIENT_DATA_GPIO","GND",g);resistor("R16","330","AMBIENT_BUF_OUT","AMBIENT_DATA",g)
    xh("J7",3,["GND","AMBIENT5_SWITCHED","AMBIENT_DATA"],g)

    g="inputs"
    xh("J2",3,["GND","I2C_SDA","I2C_SCL"],g,"HUSB238 I2C only; PD voltage must not enter sensor headers")
    xh("J8",4,["GND","ENC_A","ENC_B","ENC_PUSH"],g,"Exact encoder daughterboard J1 pin order")
    for ref in ("J9","J10","J11"):
        xh(ref,4,["GND","+3V3","I2C_SDA","I2C_SCL"],g)
    for ref,cap,net in (("R1","C26","ENC_A"),("R2","C27","ENC_B"),("R3","C28","ENC_PUSH")):
        resistor(ref,"10k","+3V3",net,g);capacitor(cap,"10nF",net,"GND",g)
    for ref,net in (("R6","I2C_SDA"),("R7","I2C_SCL")):
        resistor(ref,"4.7k","+3V3",net,g,dnp=True)
    capacitor("C22","100nF","+3V3","GND",g)
    capacitor("C33","100nF","+3V3","GND",g,location="pressure_daughterboard")
    xh("J12",2,["GND","GUARD_CONTACT_5V"],g,"Omron COM/NO; raw5V input goes to BUF4, never to GPIO")
    resistor("R5","3.9k","REG5_LOGIC","GUARD_CONTACT_5V",g)
    add("BUF4","SN74LVC1G17DBVR","Texas Instruments SN74LVC1G17DBVR",g,[pin(1,"NC",None,"no_connect"),pin(2,"A","GUARD_CONTACT_5V","input"),pin(3,"GND","GND","power_in"),pin(4,"Y","GUARD_LOGIC_3V3","output"),pin(5,"VCC","+3V3","power_in")],"Package_TO_SOT_SMD:SOT-23-5","https://www.ti.com/lit/ds/symlink/sn74lvc1g17.pdf")
    capacitor("C31","100nF","+3V3","GND",g);capacitor("C32","10nF","GUARD_CONTACT_5V","GND",g)
    resistor("R60","100k","+3V3","GUARD_LOGIC_3V3",g)
    header("J14",2,["GND","SERVICE_JUMPER"],g,"Samtec TSW-102-07-G-S","Removable SNT-100-BK-G service shunt")
    pico={1:"ENC_A",2:"ENC_B",3:"GND",4:"ENC_PUSH",5:"FAN_TACH",6:"I2C_SDA",7:"I2C_SCL",8:"GND",9:"FAN_PWM_GPIO",10:"TFT_RST_GPIO",11:"SERVO_PWM_GPIO",12:None,13:"GND",14:"TFT_DC_GPIO",15:"AMBIENT_DATA_GPIO",16:"EN_FAN",17:"EN_SERVO",18:"GND",19:"EN_AMBIENT",20:"GUARD_LOGIC_3V3",21:"TFT_BL_GPIO",22:"SERVICE_JUMPER",23:"GND",24:"TFT_SCK_GPIO",25:"TFT_MOSI_GPIO",26:"TFT_CS_GPIO",27:"PG_SERVO",28:"GND",29:"PG_FAN",30:None,31:"ADC_BUS",32:"ADC_SERVO_FEEDBACK",33:"GND",34:"ADC_LOGIC",35:None,36:"+3V3",37:None,38:"GND",39:"PICO_VSYS",40:None}
    for ref,offset in (("J15",0),("J16",20)):
        header(ref,20,[pico[i+offset] for i in range(1,21)],g,"Samtec TSW-120-07-G-S",
               "Remote Pico ribbon; physical key removes contact12 for J15 or contact10 for J16. NC35/37/40 preserved")

    g="adc"
    add("ISO1","TMUX1511PWR","Texas Instruments TMUX1511PWR",g,[
        pin(1,"SEL1","ADC_ENABLE","input"),pin(2,"S1","BUS_DIV"),pin(3,"D1","ADC_BUS"),pin(4,"SEL2","ADC_ENABLE","input"),
        pin(5,"S2","SERVO_DIV"),pin(6,"D2","ADC_SERVO_FEEDBACK"),pin(7,"GND","GND","power_in"),pin(8,"D3","ADC_LOGIC"),
        pin(9,"S3","LOGIC_DIV"),pin(10,"SEL3","ADC_ENABLE","input"),pin(11,"D4","GND"),pin(12,"S4","GND"),
        pin(13,"SEL4","GND","input"),pin(14,"VDD","+3V3","power_in")],"Package_SO:TSSOP-14_4.4x5mm_P0.65mm","https://www.ti.com/lit/ds/symlink/tmux1511.pdf")
    add("SUP1","TPS3808G33DBVR","Texas Instruments TPS3808G33DBVR",g,[pin(1,"~{RESET}","ADC_ENABLE","open_collector"),pin(2,"GND","GND","power_in"),pin(3,"~{MR}","+3V3","input"),pin(4,"CT",None),pin(5,"SENSE","+3V3","input"),pin(6,"VDD","+3V3","power_in")],"Package_TO_SOT_SMD:SOT-23-6","https://www.ti.com/lit/ds/symlink/tps3808.pdf")
    capacitor("C20","100nF","+3V3","GND",g);capacitor("C21","100nF","+3V3","GND",g)
    resistor("R37","10k","+3V3","ADC_ENABLE",g);resistor("R38","100k","ADC_ENABLE","GND",g)
    for refs,source,div,adc,lower,cap in [(("R28","R29","R30"),"BUS_PROTECTED","BUS_DIV","ADC_BUS","10k","C23"),(("R31","R32","R33"),"SERVO_FEEDBACK_RAW","SERVO_DIV","ADC_SERVO_FEEDBACK","100k","C24"),(("R34","R35","R36"),"REG5_LOGIC","LOGIC_DIV","ADC_LOGIC","100k","C25")]:
        resistor(refs[0],"100k",source,div,g);resistor(refs[1],lower,div,"GND",g);resistor(refs[2],"1M",adc,"GND",g)
        capacitor(cap,"100nF",div,"GND",g)

    g="screen"
    quad_buffer("BUF2",g,"REG5_LOGIC",[("TFT_CS_GPIO","TFT_CS_BUF",True),("TFT_RST_GPIO","TFT_RST_BUF",True),("TFT_BL_GPIO","TFT_BL_BUF",True),("GND",None,False)])
    capacitor("C18","100nF","REG5_LOGIC","GND",g)
    for ref,source,dest in (("R50","TFT_MOSI_GPIO","TFT_MOSI"),("R51","TFT_SCK_GPIO","TFT_SCK"),("R52","TFT_CS_BUF","TFT_CS"),("R53","TFT_DC_GPIO","TFT_DC"),("R54","TFT_RST_BUF","TFT_RST")):
        resistor(ref,"33",source,dest,g)
    resistor("R55","330","TFT_BL_BUF","TFT_BL",g)
    resistor("R56","1k","TFT_BL","GND",g,location="display_harness")
    resistor("R57","10k","+3V3","TFT_CS_GPIO",g);resistor("R58","10k","+3V3","TFT_RST_GPIO",g);resistor("R59","100k","TFT_BL_GPIO","GND",g)
    capacitor("C30","1uF","REG5_LOGIC","GND",g,location="display_harness")
    xh("J6",8,["REG5_LOGIC","GND","TFT_MOSI","TFT_SCK","TFT_CS","TFT_DC","TFT_RST","TFT_BL"],g)

    expected_refs={*(f"R{i}" for i in list(range(1,15))+[16,17,19,23,24]+list(range(28,48))+list(range(50,61))),
                   *(f"C{i}" for i in range(1,34)),"EF1","ISO1","SUP1","Q1","D1","D2","F1","F2","F3", "SW1","SW2","SW3","BUF1","BUF2","BUF3","BUF4",*(f"J{i}" for i in list(range(1,13))+list(range(14,20)))}
    assert {item["ref"] for item in COMPONENTS}==expected_refs
    assert len(COMPONENTS)==117
    assert {item["ref"] for item in COMPONENTS if item["dnp"]}=={"R6","R7"}
    assert {item["ref"] for item in COMPONENTS if item["location"]!="carrier"}=={"R56","C30","C33"}

def property_text(name,value,x,y,hidden=False,size=1.0):
    return f'(property {q(name)} {q(value)} (at {x} {y} 0) {"(hide yes)" if hidden else ""} (effects (font (size {size} {size}))))'

def footprint_libraries():
    LIB.mkdir(parents=True,exist_ok=True)
    for item in COMPONENTS:
        lib,name=item["footprint_source"].split(":")
        if name not in FP_SOURCES:
            source=RUNTIME/"share/kicad/footprints"/(lib+".pretty")/(name+".kicad_mod")
            if not source.exists():
                # Littelfuse0451 is a2410 chip fuse. Define its documented
                # recommended copper pattern separately, retaining this name.
                if name!="Fuse_2410_6125Metric":raise FileNotFoundError(source)
                data='(footprint "Fuse_2410_6125Metric" (version 20250108) (generator "pcbnew") (layer "F.Cu") (descr "Littelfuse0451/0453 datasheet recommended lands:1.96x3.15mm at+/-2.45mm;6.86mm outerspan and2.94mm gap (published2.95 rounded)") (attr smd) (property "Reference" "REF**" (at 0 -2.4 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15)))) (property "Value" "0451" (at 0 2.4 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15)))) (fp_rect (start -3.05 -1.345) (end 3.05 1.345) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab")) (fp_rect (start -3.68 -1.825) (end 3.68 1.825) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd")) (pad "1" smd rect (at -2.45 0) (size 1.96 3.15) (layers "F.Cu" "F.Paste" "F.Mask")) (pad "2" smd rect (at 2.45 0) (size 1.96 3.15) (layers "F.Cu" "F.Paste" "F.Mask")))\n'
                write(LIB/(name+".kicad_mod"),data)
                FP_SOURCES[name]={"source":"Littelfuse0451/0453 recommended pad dimensions,4-page fuse datasheet finalpage", "source_url":"https://www.littelfuse.com/assetdocs/fuse-451-and-453-datasheet?assetguid=533cd5cc-956c-4243-867f-6ab5a62f6ba1", "sha256":digest(LIB/(name+".kicad_mod")),"qualified":"Land dimensions checked; routing/clearance/assembly qualification pending"}
            else:
                write(LIB/source.name,source.read_text(encoding="utf-8"))
                FP_SOURCES[name]={"source":f"KiCad10.0.6 {item['footprint_source']}","sha256":digest(source),"qualified":"package/library mapping; final manufacturer land review required"}
        item["footprint"]="WindflowCarrier:"+name
    write(OUT/"fp-lib-table",'(fp_lib_table (version 7) (lib (name "WindflowCarrier") (type "KiCad") (uri "${KIPRJMOD}/WindflowCarrier.pretty") (options "") (descr "Frozen E3 carrier footprint candidates")))\n')

def symbol_definition(item):
    name="S_"+item["ref"]
    pins=item["pins"]
    nleft=(len(pins)+1)//2
    rows=max(nleft,len(pins)-nleft)
    half=max(2.54,rows*1.27+1.27)
    pin_geometry=[]
    for i,p in enumerate(pins):
        left=i<nleft;row=i if left else i-nleft
        y=round((rows-1)*1.27-row*2.54,6)
        x=-10.16 if left else 10.16;angle=0 if left else 180
        p["symbol_xy_mm"]=[x,y];p["side"]="left" if left else "right"
        pin_geometry.append(f'(pin {p["type"]} line (at {x} {y} {angle}) (length 2.54) (name {q(p["name"])} (effects (font (size 0.9 0.9)))) (number {q(p["number"])} (effects (font (size 0.9 0.9)))))')
    item["half_height_mm"]=half
    properties=property_text("Reference",item["ref"],0,half+1.27)+property_text("Value",item["value"],0,-half-1.27)
    properties+=property_text("Footprint",item["footprint"],0,0,True)+property_text("Datasheet",item["datasheet"],0,0,True)
    body=f'(rectangle (start -7.62 {half}) (end 7.62 {-half}) (stroke (width 0.254) (type default)) (fill (type background)))'
    return f'(symbol {q(name)} (pin_names (offset 0.5)) (exclude_from_sim no) (in_bom yes) (on_board yes) {properties} (symbol {q(name+"_0_1")} {body}) (symbol {q(name+"_1_1")} {" ".join(pin_geometry)}))'

GROUP_TITLES={"power":"PD input, eFuse and remote regulators", "fan_servo":"Fan/servo switches, PWM and feedback connectors", "ambient":"Downward ambient lighting supply and data", "inputs":"Encoder, I2C, grille safety and remote Pico", "adc":"ADC isolation and voltage/feedback measurement", "screen":"IPS display interfaces and external screen passives"}
NOTES={
    "power":["EF_RTN is an isolated return/thermal island; it must never be joined to system GND.","RegulatorEN pads remain NC at remote modules. J17/J18/J19 are connector candidates, not a fitted-board claim.","No bulk reservoir is on raw USB VBUS. F1 and eFuse precede C2 and the regulator bank."],
    "fan_servo":["FanPWM uses Q1 open-drain inversion; no12V pullup. EN pulldowns are mandatory.","BUF3 is powered only by switched servo supply. 330ohm QOD resistors are1206/0.25W.","Module PG is open-drain; pullups go only to3.3V. Fuse sizes do not replace timed servo jam cutoff."],
    "ambient":["BUF1 supply follows switched ambient rail. Its three unused channels are disabled and inputs grounded.","The retired main pixel bars/status lamp are absent. The 8-pixel ambient stick is the only LED chain."],
    "inputs":["BUF4 translates5V grille-contact node to3.3V GP15; keep rawguard net away from Pico.","R6/R7 are DNP until combined breakout pullups are measured. Sensor/temperature supplies are3.3V.","J15contact12 / J16contact10 are physically removed and cable keyed; Pico35/37/40 are NC.","J15positionn=Pico physicaln; J16positionn=Pico physicaln+20. Module orientation does not change numbering."],
    "adc":["Filter capacitors are before ISO1. ADC-side1M pulldowns remain after it; no stored capacitor on GPIO side.","SUP1 CT is NC for nominal20ms delay. /RESET enables ISO1 only after3.3V is healthy.","Bus nominal scale11.1; logic/servo network2.1. Servo uses measured raw feedback table."],
    "screen":["BUF2 is unswitched5V. CS/RST are buffered because module pullups go toVIN; GPIO must not see5V.","R56 and C30 are fitted at the display end and excluded from carrier PCB population.","GP6fan, GP8servo and GP16BL are different PWM slices. Keep combined Pico/display wire length under150mm."]}

def text_item(text,x,y,name,size=1.0):
    return f'(text {q(text)} (at {x} {y} 0) (effects (font (size {size} {size})) (justify left)) (uuid {q(uid(name))}))'

def sheet_header(sheet_uuid,title,defs):
    return f'(kicad_sch (version 20250114) (generator "eeschema") (uuid {q(sheet_uuid)}) (paper "A3") (title_block (title {q("Windflow "+SCHEMATIC_REVISION+" / "+title)}) (date {q(CAPTURE_DATE)}) (rev "C1 schematic capture")) (lib_symbols {defs})'

def schematics():
    definitions={item["ref"]:symbol_definition(item) for item in COMPONENTS}
    write(OUT/"WindflowCarrier.kicad_sym",'(kicad_symbol_lib (version 20250114) (generator "kicad_symbol_editor")\n'+"\n".join(definitions.values())+'\n)\n')
    write(OUT/"sym-lib-table",'(sym_lib_table (version 7) (lib (name "WindflowCarrier") (type "KiCad") (uri "${KIPRJMOD}/WindflowCarrier.kicad_sym") (options "") (descr "Explicit E3 pin mappings")))\n')
    rootitems=[]
    for group_index,(group,title) in enumerate(GROUP_TITLES.items()):
        sheet_id=uid("sheet-"+group)
        filename=f"{group}.kicad_sch"
        x=25+(group_index%SHEET_COLUMNS)*SHEET_X_STEP;y=45+(group_index//SHEET_COLUMNS)*SHEET_SPACING
        rootitems.append(f'(sheet (at {x} {y}) (size {SHEET_WIDTH} 40) (stroke (width 0.254) (type default)) (fill (color 0 0 0 0)) (uuid {q(sheet_id)}) {property_text("Sheetname",title,x,y-2.54)} {property_text("Sheetfile",filename,x,y+42.54)} (instances (project {q(NAME)} (path {q("/"+ROOT_UUID)} (page {q(group_index+2)})))))')
        items=[];selected=[item for item in COMPONENTS if item["group"]==group]
        assert len(selected)<=30,(group,len(selected))
        embedded=" ".join(definitions[item["ref"]].replace(f'(symbol "S_{item["ref"]}"',f'(symbol "WindflowCarrier:S_{item["ref"]}"',1) for item in selected)
        for index,item in enumerate(selected):
            # Compact contact-style blocks keep all named pin endpoints visible.
            # Nets are actual global labels, not merely free text descriptions.
            xx=round(43.18+(index%5)*76.2,6);yy=round(35.56+(index//5)*40.64,6)
            hh=item["half_height_mm"]
            props=property_text("Reference",item["ref"],xx,yy-hh-1.27)+property_text("Value",item["value"],xx,yy+hh+1.27,size=.9)
            props+=property_text("Footprint",item["footprint"],xx,yy,True)+property_text("Datasheet",item["datasheet"],xx,yy,True)
            props+=property_text("MPN",item["mpn"],xx,yy,True)+property_text("Assembly location",item["location"],xx,yy,True)
            symbol=f'(symbol (lib_id {q("WindflowCarrier:S_"+item["ref"])}) (at {xx} {yy} 0) (unit 1) (in_bom yes) (on_board {"yes" if item["location"]=="carrier" else "no"}) (dnp {"yes" if item["dnp"] else "no"}) (uuid {q(uid(item["ref"]))}) {props} '
            symbol+=" ".join(f'(pin {q(p["number"])} (uuid {q(uid(item["ref"]+"pin"+p["number"]))}))' for p in item["pins"])
            symbol+=f' (instances (project {q(NAME)} (path {q("/"+ROOT_UUID+"/"+sheet_id)} (reference {q(item["ref"])}) (unit 1)))))'
            items.append(symbol)
            for p in item["pins"]:
                px,py=p["symbol_xy_mm"];endx=round(xx+px,6);endy=round(yy-py,6)
                if p["net"] is None:
                    items.append(f'(no_connect (at {endx} {endy}) (uuid {q(uid(item["ref"]+p["number"]+"nc"))}))')
                else:
                    left=p["side"]=="left";labelx=round(endx+(-3.81 if left else 3.81),6)
                    items.append(f'(wire (pts (xy {endx} {endy}) (xy {labelx} {endy})) (stroke (width 0) (type default)) (uuid {q(uid(item["ref"]+p["number"]+"wire"))}))')
                    # Native KiCad label text extends to the right at zero
                    # degrees. Left labels therefore face 180 degrees so
                    # their text remains outside the component body.
                    items.append(f'(global_label {q(p["net"])} (shape bidirectional) (at {labelx} {endy} {180 if left else 0}) (effects (font (size .85 .85)) (justify {"right" if left else "left"})) (uuid {q(uid(item["ref"]+p["number"]+"label"))}) {property_text("Intersheetrefs","${INTERSHEET_REFS}",labelx,endy,True)})')
        for i,note in enumerate(NOTES[group]):items.append(text_item(note,15,265+i*4.5,group+"note"+str(i),1.0))
        write(OUT/filename,sheet_header(sheet_id,title,embedded)+"\n"+"\n".join(items)+"\n)\n")
    rootitems += [text_item("EDITABLE CIRCUIT CAPTURE C1 / not routed, fabricated or bench qualified",25,22,"root-title",1.5),
                  text_item("Every semiconductor pin, fitted passive and connector is explicit. NC pins have native no-connect flags.",25,32,"root-scope",1.2),
                  text_item(BOARD_SCOPE,25,280,"root-limit",1.0)]
    # ERC supply flags represent actual remote rails/returns at connection points.
    # They are not simulated sources or an assertion about startup power sequence.
    flag_nets=FLAG_NETS
    flags='(symbol "WindflowCarrier:SupplyFlag" (pin_names (offset 0)) (exclude_from_sim no) (in_bom no) (on_board no) '+property_text("Reference","#FLG",0,0,True)+property_text("Value","PWR_FLAG",0,0,True)+' (symbol "SupplyFlag_0_1" (polyline (pts (xy -1.27 0) (xy 0 1.27) (xy 1.27 0) (xy 0 -1.27) (xy -1.27 0)) (stroke (width .15) (type default)) (fill (type none)))) (symbol "SupplyFlag_1_1" (pin power_out line (at 0 -2.54 90) (length 1.27) (name "pwr" (effects (font (size .8 .8)))) (number "1" (effects (font (size .8 .8)))))))'
    for i,net in enumerate(flag_nets):
        x=round(30.48+i*40.64,6);y=254
        ref=f"#FLG{i+1:02d}"
        rootitems.append(f'(symbol (lib_id "WindflowCarrier:SupplyFlag") (at {x} {y} 0) (unit 1) (in_bom no) (on_board no) (dnp no) (uuid {q(uid(ref))}) {property_text("Reference",ref,x,y,True)} {property_text("Value","PWR_FLAG",x,y,True)} (pin "1" (uuid {q(uid(ref+"1"))})) (instances (project {q(NAME)} (path {q("/"+ROOT_UUID)} (reference {q(ref)}) (unit 1)))))')
        rootitems.append(f'(global_label {q(net)} (shape input) (at {x} {y+2.54} 0) (effects (font (size .85 .85)) (justify left)) (uuid {q(uid(ref+"label"))}) {property_text("Intersheetrefs","${INTERSHEET_REFS}",x,y+2.54,True)})')
    write(OUT/f"{NAME}.kicad_sch",sheet_header(ROOT_UUID,"sheet index and external-rail ERC origins",flags)+"\n"+"\n".join(rootitems)+f'\n(sheet_instances (path "/" (page "1"))))\n')
    write(OUT/"WindflowCarrier.kicad_sym",'(kicad_symbol_lib (version 20250114) (generator "kicad_symbol_editor")\n'+"\n".join(definitions.values())+'\n'+flags.replace('(symbol "WindflowCarrier:SupplyFlag"','(symbol "SupplyFlag"',1)+'\n)\n')

def call(*args,allow_failure=False):
    command=[str(CLI),*map(str,args)]
    result=subprocess.run(command,cwd=OUT,text=True,capture_output=True)
    COMMANDS.append({"arguments":list(map(str,args)),"exit_code":result.returncode,"stdout":result.stdout.strip(),"stderr":result.stderr.strip()})
    print(result.stdout.strip(),flush=True)
    write(OUT/"verification-commands.json",json.dumps(COMMANDS,indent=2)+"\n")
    if result.returncode and not allow_failure:raise RuntimeError(f"KiCad exit{result.returncode}: {result.stderr}")
    return result

def validate_netlist():
    xml=ET.parse(OUT/f"{NAME}.net.xml").getroot()
    actual={}
    net_nodes={}
    for net in xml.findall("nets/net"):
        name=net.attrib["name"];nodes=[]
        for node in net.findall("node"):
            key=(node.attrib["ref"],node.attrib["pin"])
            assert key not in actual,key
            actual[key]=name;nodes.append(key)
        net_nodes[name]=nodes
    assertion_count=0;nc=[]
    for item in COMPONENTS:
        for p in item["pins"]:
            key=(item["ref"],p["number"])
            assert key in actual,("Missing pin from native netlist",key)
            expected=p["net"]
            if expected is None:
                assert actual[key].startswith("unconnected-("),(key,actual[key])
                assert net_nodes[actual[key]]==[key],(key,net_nodes[actual[key]])
                nc.append({"ref":key[0],"pin":key[1],"name":p["name"]})
            else:
                assert actual[key]==expected,(key,actual[key],expected)
            assertion_count+=1
    # Independent safety invariants guard against accidental rail/name aliases.
    assert actual[("EF1","17")]==actual[("EF1","8")]=="EF_RTN"
    assert actual[("EF1","9")]=="GND" and "EF_RTN"!="GND"
    assert actual[("BUF4","2")]==actual[("J12","2")]=="GUARD_CONTACT_5V"
    assert actual[("BUF4","4")]==actual[("J15","20")]=="GUARD_LOGIC_3V3"
    assert actual[("BUF4","5")]==actual[("J16","16")]=="+3V3"
    assert actual[("BUF3","5")]==actual[("SW2","6")]=="SERVO5_SWITCHED"
    assert actual[("BUF1","14")]==actual[("SW3","6")]=="AMBIENT5_SWITCHED"
    assert actual[("BUF2","14")]=="REG5_LOGIC"
    assert actual[("ISO1","2")]==actual[("C23","1")]=="BUS_DIV"
    assert actual[("ISO1","3")]==actual[("J16","11")]=="ADC_BUS"
    assert actual[("D2","1")]==actual[("J16","19")]=="PICO_VSYS"
    assert actual[("J17","3")]=="REG12V" and actual[("J18","3")]=="REG5_LOGIC" and actual[("J19","3")]=="REG5_SERVO"
    write(OUT/"netlist-validation.json",json.dumps({"native_netlist_sha256":digest(OUT/f"{NAME}.net.xml"),"component_count":len(COMPONENTS),"pin_net_assertions":assertion_count,"explicit_nc_pins":nc,"nets":{name:sorted(nodes) for name,nodes in sorted(net_nodes.items())},"verified_invariants":["EF_RTN thermal/control return separate from GND","Guard5V isolated from GPIO through specificBUF4","Switched servo/ambient buffers","Unswitched display buffer","ADC filters before isolation","Pico VSYS diode direction","Three distinct regulator outputs","Pico NC/key positions"]},indent=2)+"\n")
    print(f"PASS native carrier netlist: {len(COMPONENTS)} components, {assertion_count} pin-net assertions",flush=True)

def main():
    if not CLI.exists():raise RuntimeError("Run tools/setup_kicad.ps1 first")
    OUT.mkdir(parents=True,exist_ok=True)
    population();footprint_libraries();schematics()
    write(OUT/f"{NAME}.kicad_pro",json.dumps({"meta":{"filename":f"{NAME}.kicad_pro","version":1}},indent=2)+"\n")
    write(OUT/"circuit-population.json",json.dumps({"scope":"Native circuit capture; no routed/fabrication carrier PCB","components":COMPONENTS,"footprint_sources":FP_SOURCES},indent=2)+"\n")
    sch=OUT/f"{NAME}.kicad_sch"
    call("sch","export","netlist","--format","kicadxml","-o",OUT/f"{NAME}.net.xml",sch)
    validate_netlist()
    call("sch","erc","--format","json","--severity-all","--exit-code-violations","-o",OUT/"erc.json",sch)
    call("sch","export","svg","--exclude-drawing-sheet","-o",OUT/"schematic-svg",sch)
    call("sch","export","pdf","--exclude-drawing-sheet","-o",OUT/f"{NAME}-schematic.pdf",sch)
    references={path:digest(ROOT/path) for path in ("hardware/wiring.md","hardware/BOM.md","hardware/circuit-review.md","hardware/carrier-interface-study.md")}
    write(OUT/"provenance.json",json.dumps({"generator":"tools/build_carrier_circuit.py","generator_sha256":digest(__file__),"kicad_version":"10.0.6","circuit_reference_sha256":references,"component_count":len(COMPONENTS),"carrier_fitted_component_count":sum(not c["dnp"] and c["location"]=="carrier" for c in COMPONENTS),"dnp":["R6","R7"],"external_screen_passives":["C30","R56"],"external_pressure_passives":["C33"],"release_scope":"Circuit capture only. No carrier PCB routes/fabrication/thermal or assembly release.","files":{str(p.relative_to(OUT)).replace("\\","/"):digest(p) for p in sorted(OUT.rglob("*")) if p.is_file() and p.name!="provenance.json" and p.suffix!=".kicad_prl"}},indent=2)+"\n")
    print("PASS native carrier schematic/netlist/ERC capture",flush=True)

if __name__=="__main__":main()
