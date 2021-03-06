# -*- coding: utf-8 -*-
"""RP_final_G11_method_2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ghkozzLmDbYvueR3zWgmHA7C5gefH7fA
"""

from copy import copy
import numpy as np
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
from scipy.io import savemat
#define constants 

Ru = 8.3145
Mwco = 28e-3;
Mwco2 =44e-3;
Mwo2 = 32e-3;
Mwh2o = 18e-3;
Mwn2 = 28e-3;
V=67.4e-6; 
P = 1e5;

r =  0.03;
xh2o = r;
xo2 = (1-r)/(1+2+ (0.79/0.21))
xco = 2*xo2;
xn2 = 0.79*xo2/0.21;
Mwmix0 = (xo2*Mwo2 + xn2*Mwn2 + xco*Mwco + xh2o*Mwh2o)

yn2in = xn2*Mwn2/Mwmix0; yn2=yn2in;
yo2in = xo2*Mwo2/Mwmix0;
yh2o = xh2o*Mwh2o/Mwmix0;
yh2oin = yh2o;
ycoin = xco*Mwco/Mwmix0; 
yco2in=0;
inlet=np.array([ycoin,yo2in,yco2in]);

hf0co = -110541/Mwco #110541/Mwco;
hf0co2= -393546/Mwco2; #393546/Mwco2;
hf0h2o = -241845/Mwh2o; #241845/Mwh2o;
hf0o2 = 0;
hf0n2 = 0;
Cpo2 = 37.788/Mwo2;
Cph2o =  51.143/Mwh2o;
Cpco = 36.271/Mwco #1294;
Cpco2 = 60.433/Mwco2 ;
Cpn2 = 35.988/Mwn2;

def kr(T): 
    return (5e8)*np.exp( -1.674*10**5/(Ru*T))

def kf(T):
    return (2.24e12)*(1000**(-0.75))*np.exp( -1.674*10**5/(Ru*T))


def Mwmix(yh2o,yco,yco2,yo2,yn2):
    return 1/((yco/Mwco) + (yco2/Mwco2) + (yo2/Mwo2) + (yh2o/Mwh2o) + (yn2/Mwn2) )

def con(MWmix,y,MW,T):
    return (P*MWmix/(Ru*T))*y/MW
    
def wdco(yh2o,yco,yco2,yo2,T):
    MW=Mwmix(yh2o,yco,yco2,yo2,yn2);
    Cco2=con(MW,yco2,Mwco2,T);
    Cco=con(MW,yco,Mwco,T);
    Ch2o=con(MW,yh2o,Mwh2o,T);
    Co2=con(MW,yo2,Mwo2,T);
    dw=kr(T)*Cco2 - kf(T)*Cco*(Ch2o**0.5)*(Co2**0.25)
    #print(dw)
    return dw

def f1(yh2o,yco,yco2,yo2,T,mdot,ycoin):
    return mdot*(yco - ycoin) - wdco(yh2o,yco,yco2,yo2,T)*Mwco*V

def f2(yh2o,yco,yco2,yo2,T,mdot,yo2in):
    return mdot*(0 - yco2) - wdco(yh2o,yco,yco2,yo2,T)*Mwco2*V

def f3(yh2o,yco,yco2,yo2,yn2):
    return yco + yo2 + yco2 + yh2o + yn2 - 1 

Tin=298;
def f4(T,mdot,x):
    yco=x[0]; yo2=x[1]; yco2=x[2];
    return (yh2o*(hf0h2o + Cph2o*(T-298)) + yco*(hf0co + Cpco*(T-298)) + yco2*(hf0co2 + Cpco2*(T-298)) + yo2*(hf0o2 + Cpo2*(T-298)) + yn2*(hf0n2 + Cpn2*(T-298))  - yh2oin*(hf0h2o + Cph2o*(Tin-298)) - yo2in*(hf0o2 + Cpo2*(Tin-298)) - ycoin*(hf0co + Cpco*(Tin-298))- yn2in*(hf0n2 + Cpn2*(Tin-298)))


def function(x,dm,T):
  n=len(x); f=np.zeros(n)
  yco=x[0]; yo2=x[1]; yco2=x[2];
  f[0]=f1(yh2o,yco,yco2,yo2,T,dm,ycoin);
  f[1]=f2(yh2o,yco,yco2,yo2,T,dm,yo2in);
  f[2]=f3(yh2o,yco,yco2,yo2,yn2);
  return f

def Newton_NL(func,x0,dm,T):
    n=len(x0); 
    x=copy(x0); k=0;
    dfdx=np.zeros([n,n]);
    while True:
        #print(x)
        k=k+1;
        f=func(x,dm,T);
        for i in range(n):
            for j in range(n):
                dfdx[i,j]=pde(func,x,dm,i,j,T)
        delta=np.linalg.solve(dfdx,-f)/5;
        x=x+delta; ch=delta/(x);
        if np.all(abs(x) >= 1e-7):
            if np.all(abs(ch)<=1e-7):
                #print("m1 :","\nsol=",x,"\nfun",f,"\n ch=",ch,"\n delta",delta)
                break;
        else:
            if np.all(abs(delta)<=1e-7):
                #print("m2 :","\nsol=",x,"\nfun",f,"\n ch=",ch,"\n delta",delta)
                break;        
    return x

def pde(func,x,dm,i,j,T):
    if abs(x[j])>1:
        ep=abs(x[j])*1e-5;
    else:
        ep=1e-5
    x1=copy(x); x1[j]=x1[j]+ep;
    F1=func(x1,dm,T);
    F=func(x,dm,T);
    dfdx=(F1[i]-F[i])/ep;
    return(dfdx)

#yco=x[0]; yo2=x[1]; yco2=x[2];
def Feval(dm,init):
    Temps=init[0];
    y0=init[1];
    while True:
        y=Newton_NL(function,y0,dm,Temps);
        Temps=Newton_NL(f4,Temps,dm,y);
        if abs(f4(Temps,dm,y))<=1e-7:
            break
    return [Temps,y]

dm=np.linspace(1e-6,0.5,50);

#yco=x[0]; yo2=x[1]; yco2=x[2];
X=[]; Tr=[]; Yco=[]; Yo2=[]; Yco2=[]; T=[]; mdot=[]; #final values

init=[np.array([2100.0]),np.array([3e-2,2e-2,4.3e-1],dtype=float)];
for i in range(len(dm)):
    sol=Feval(dm[i],init)
    init=sol;
    if all(abs(sol[1]-inlet)<1e-6): 
        break
    else:
        T.append(sol[0]);
        mdot.append(dm[i]);
        Yco.append(sol[1][0]);  
        Yo2.append(sol[1][1]);  
        Yco2.append(sol[1][2]); 
        
T=np.asarray(T);
Yco=np.asarray(Yco);
Yo2=np.asarray(Yo2);
Yco2=np.asarray(Yco2);

RP={"pre_h2o":r,"mdot":mdot,"T":T,"Yco":Yco,"Yo2":Yo2,"Yco2":Yco2}
savemat("RP"+str(r)+".mat", RP)

     
plt.figure(1)
plt.plot(mdot,Yco,"-o")
plt.ylabel(" Yco")
plt.xlabel("mass flow rate (kg/s)")
plt.grid()

plt.figure(2)
plt.plot(mdot,Yo2,"-o")
plt.ylabel(" Yo2")
plt.xlabel("mass flow rate (kg/s)")
plt.grid()

plt.figure(3)
plt.plot(mdot,Yco2,"-o")
plt.ylabel(" Yco2")
plt.xlabel("mass flow rate (kg/s)")
plt.grid()
    
plt.figure(4)
plt.plot(mdot,T,"-o")
plt.ylabel("Temperature (K)")
plt.xlabel("mass flow rate (kg/s)")
plt.grid()

plt.show()