from decimal import Decimal as D, ROUND_HALF_UP
q6=lambda x: x.quantize(D('0.000001'),rounding=ROUND_HALF_UP)
q0=lambda x: x.quantize(D('1'),rounding=ROUND_HALF_UP)
P=D(6000000)/D(200)
def k(qbn,qnk=600,qc=48,rr=D('0.02'),qe=12,h=D('0.03')):
    ql=q0(qbn*rr)
    return q6((qbn+qnk+qc+ql+qe)/((1-h)*qbn)), ql
k1,l1=k(D(12000)); k2,l2=k(D(1200))
print('TV01',k1,l1,q6(P*k1)); print('TV02',k2,l2,q6(P*k2))
tv03=q6(D(800)*k1); print('TV03',tv03)
tv04=q6(D(90000000)/D(300000)); print('TV04',tv04)
# IQC: 0.1 mL x2 levels x1/day x300 days =60 mL; vial 5 mL 1,200,000 -> 240,000/mL
iqc_year=D('0.1')*2*1*300*(D(1200000)/5); tv05=q6(iqc_year/20/12000); print('TV05',iqc_year,tv05)
tv06=q6(D(400000)*12/12000); print('TV06',tv06)
tv07=q6((D(14000000)+D(1000000))/10/12000); print('TV07',tv07)
tv08=q6(D(3600000000)/8/300000); print('TV08',tv08)
tv09=q6(D(180000000)/300000); print('TV09',tv09)
comp=D(6000000)*12/12+D(9000000)*12/24; tv10=q6(comp/300000); print('TV10',comp,tv10)
rate=q6(D(211200000)/(1760*60)); mins=D('1.5')+D(20)/40+D('0.3'); tv11=q6(mins*rate); print('TV11',rate,mins,tv11)
tv12=q6(D(6000)/4); print('TV12',tv12)
kwh=D('1.2')*10+D('0.3')*14; elec=kwh*365*2500; tv13=q6(elec/300000); print('TV13',kwh,elec,tv13)
ct=D(1500000000)+D(600000000)+D(1800000000)*12/36+D(30000000); pm=q6(ct/135000); print('TV14',ct,pm,q0(pm*10),q0(pm*20),q0(ct/9000))
print('TV15',D('0.6')*40000+D('0.4')*46000)
hc=q6(P*k1)
vt=tv12+hc+tv03+tv04+tv05+tv06
dt=tv09+tv10+tv07
parts={'NC':tv11,'VT':vt,'DN':tv13,'DT':dt,'KH':tv08,'QL':D(3000)}
tot=sum(parts.values()); print('TV16',parts,tot,q0(tot),{a:q0(b) for a,b in parts.items()}, sum(q0(b) for b in parts.values()))
# reconciliation example
calc=D(12000)*k1; act=D(14000); print('REC',q6(calc),q6((act-calc)/act*100))
