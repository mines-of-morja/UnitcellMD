"""Read-only: pressure and temperature of stored frames (flexible water), no dynamics.
For each frame, from positions only:
  T_conf,trans  <|F_I|^2>/<-div_I F_I>   (molecule centres, Hutchinson probe)
  T_conf,rot    <|tau_I|^2>/<-L.tau_I>
  T_int,half    -<sum (r_i-R_I).F_i>/(6 N_mol k)   discrete virial theorem: half-step internal KE
  P_mol by component, P_atomic with the on-step kinetic energy from thermo.tsv
usage: pdecomp.py PACKAGE RUN_OUT SKIP_PS NFRAMES CUTOFF EWTOL TSET
"""
import sys, json
from pathlib import Path
import numpy as np, h5py, openmm as mm
from openmm import unit
from ucmd_bridge.package import load
from ucmd_bridge.model import NonbondedSettings, build_system

KB=8.31446261815324e-3; BAR=16.6053906660
pkg,out,skip,nfr,rc,tol,Tset=sys.argv[1],Path(sys.argv[2]),float(sys.argv[3]),int(sys.argv[4]),float(sys.argv[5]),float(sys.argv[6]),float(sys.argv[7])
top=load(pkg)
s=NonbondedSettings.from_provider(dict(kind="force-field",cutoff_nm=rc,coulomb="pme",ewald_tolerance=tol,dispersion_correction=False))
system,info=build_system(top,s)
for f in system.getForces():
    f.setForceGroup(1 if isinstance(f,mm.NonbondedForce) else 2 if isinstance(f,mm.CustomNonbondedForce) else 0)
ctx=mm.Context(system,mm.VerletIntegrator(1e-3),mm.Platform.getPlatformByName("CPU"),{"Threads":"4"})
m=np.array(top.masses_amu,float); N=len(m); nm=N//3
assert np.allclose(m.reshape(nm,3),m[:3])
mi=np.repeat(np.arange(nm),3); M=m[:3].sum(); w=(m[:3]/M)[None,:,None]
O=np.argmax(m[:3]); sg=float(top.sigma_nm[O]); ep=float(top.epsilon_kjmol[O])
assert all(top.epsilon_kjmol[i]==0 for i in range(N) if i%3!=O)
h=h5py.File(out/"trajectory.h5","r"); p=h["particles/all"]; t=p["position/time"][:]
idx=np.where(t>=skip)[0]; idx=idx[np.unique(np.linspace(0,len(idx)-1,min(nfr,len(idx))).astype(int))]
box=p["box/edges"]
thermo=np.genfromtxt(out/"thermo.tsv",comments="#",usecols=(1,3,6,7,8)) if (out/"thermo.tsv").stat().st_size<5e7 else None
if thermo is None:
    o=h["observables"]; kt=o["kinetic_energy/time"][:]; kv=o["kinetic_energy/value"][:]; Pt=o["pressure/value"][:]
else:
    kt,kv,Pt=thermo[:,0],thermo[:,1],thermo[:,3]
rng=np.random.default_rng(1)
def setL(L): ctx.setPeriodicBoxVectors([L,0,0],[0,L,0],[0,0,L])
def force(x,g=-1):
    ctx.setPositions(x); return ctx.getState(getForces=True,groups=g).getForces(asNumpy=True).value_in_unit(unit.kilojoule_per_mole/unit.nanometer)
def energy(x,g):
    ctx.setPositions(x); return ctx.getState(getEnergy=True,groups=g).getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
def rot(v,r):
    th=np.linalg.norm(v,axis=-1,keepdims=True); k=v/th; c,sn=np.cos(th)[:,None],np.sin(th)[:,None]; k=k[:,None,:]
    return r*c+np.cross(np.broadcast_to(k,r.shape),r)*sn+k*(k*r).sum(-1,keepdims=True)*(1-c)
rows=[]
for i in idx:
    e=box["value"]; e=np.asarray(e[min(i,len(e)-1)] if e.ndim==3 else e[:]); L=e[0,0]; V=L**3
    x=p["position/value"][i].astype(float).reshape(nm,3,3)
    x=x-L*np.round((x-x[:,O:O+1])/L)
    R=(w*x).sum(1); r=x-R[:,None]
    setL(L); full=x.reshape(-1,3)
    F=force(full).reshape(nm,3,3); FI=F.sum(1); tau=np.cross(r,F).sum(1)
    d=2e-4; sv=rng.choice([-1.,1.],(nm,3))
    fp=force((x+d*sv[:,None]).reshape(-1,3)).reshape(nm,3,3).sum(1); fm=force((x-d*sv[:,None]).reshape(-1,3)).reshape(nm,3,3).sum(1)
    lap=-((fp-fm)*sv).sum()/(2*d)
    dr=2e-3; sr=rng.choice([-1.,1.],(nm,3))
    def tq(sgn):
        rr=rot(sgn*dr*sr,r); f=force((R[:,None]+rr).reshape(-1,3)).reshape(nm,3,3); return np.cross(rr,f).sum(1)
    lapr=-((tq(1)-tq(-1))*sr).sum()/(2*dr)
    # molecular virial: Coulomb from the energy under scaling of centres, LJ from O-O pairs
    q=1e-3
    def ec(sc): setL(L*sc); return energy((R[:,None]*sc+r).reshape(-1,3),1<<1)
    WC=-(ec(1+q)-ec(1-q))/(2*q); setL(L)
    ox=x[:,O]; a,b=np.triu_indices(nm,1); D=ox[a]-ox[b]; n=np.round(D/L); D-=L*n; r2=(D**2).sum(1); k=r2<rc*rc
    D,r2=D[k],r2[k]; s6=(sg*sg/r2)**3; ff=(24*ep*(2*s6*s6-s6)/r2)[:,None]*D
    DR=(R[a]-R[b]-L*n)[k]; WL=(DR*ff).sum(); WLat=(D*ff).sum()
    Wrel=(r*F).sum()
    Wt=16*np.pi*nm*nm/V*ep*sg**3*((2/3)*(sg/rc)**9-(sg/rc)**3)   # 3V*P_tail
    j=np.argmin(abs(kt-t[i])); assert abs(kt[j]-t[i])<1e-3,(kt[j],t[i])
    rows.append((t[i],V,(FI**2).sum(),lap,(tau**2).sum(),lapr,Wrel,WC,WL,Wt,2*kv[j],Pt[j] if np.isfinite(Pt[j]) else np.nan))
a=np.array(rows); t_,V,F2,lap,T2,lapr,Wrel,WC,WL,Wt,twoK,Plog=a.T
nb=8; bl=np.array_split(np.arange(len(a)),nb)
def jk(fn):
    full=fn(slice(None)); v=[fn(np.concatenate([bl[z] for z in range(nb) if z!=y])) for y in range(nb)]
    return full,np.sqrt((nb-1)/nb*((np.array(v)-np.mean(v))**2).sum())
res={}
def rep(name,fn,u=""):
    v,e=jk(fn); res[name]=(v,e); print(f"{name:58s} {v:10.2f} +- {e:6.2f} {u}")
ndof=3*N-3
print("run",out,"frames",len(a),"t",t_[0],t_[-1],"V",V.mean(),"rho",nm*M*1.66053906660e-3/V.mean())
rep("T displayed (on-step, all dof)",lambda z:twoK[z].mean()/(ndof*KB),"K")
rep("T configurational, translation of molecules",lambda z:F2[z].mean()/lap[z].mean()/KB,"K")
rep("T configurational, rotation of molecules",lambda z:T2[z].mean()/lapr[z].mean()/KB,"K")
rep("T internal motion, half-step (virial theorem)",lambda z:-Wrel[z].mean()/(6*nm*KB),"K")
Ts=res["T configurational, translation of molecules"][0]
bar=lambda W,z:(W[z]/(3*V[z])).mean()*BAR
rep("P ideal, molecule centres at T set",lambda z:(nm-1)*KB*Tset*(1/V[z]).mean()*BAR,"bar")
rep("P Coulomb (molecular)",lambda z:bar(WC,z),"bar")
rep("P LJ within cutoff (molecular)",lambda z:bar(WL,z),"bar")
rep("P LJ tail",lambda z:bar(Wt,z),"bar")
rep("P molecular, sum (kinetic at T set)",lambda z:(nm-1)*KB*Tset*(1/V[z]).mean()*BAR+bar(WC+WL+Wt,z),"bar")
rep("P molecular, sum (kinetic at T conf trans)",lambda z:(nm-1)*KB*Ts*(1/V[z]).mean()*BAR+bar(WC+WL+Wt,z),"bar")
rep("P atomic, on-step KE (thermo) + atomic virial",lambda z:bar(twoK+WC+WL+Wt+Wrel,z),"bar")
rep("P atomic - P molecular(T set), internal motion",lambda z:bar(twoK-3*(nm-1)*KB*Tset+Wrel,z),"bar")
rep("P logged by the run, same frames",lambda z:np.nanmean(Plog[z]),"bar")
Pat=(twoK+WC+WL+Wt+Wrel)/(3*V)*BAR; Pm=(3*(nm-1)*KB*Tset+WC+WL+Wt)/(3*V)*BAR
print("frame-by-frame logged - P_atomic: mean %.2f std %.2f | logged - P_mol: mean %.2f std %.2f"%(np.nanmean(Plog-Pat),np.nanstd(Plog-Pat),np.nanmean(Plog-Pm),np.nanstd(Plog-Pm)))
json.dump({k:[float(v[0]),float(v[1])] for k,v in res.items()},open(sys.argv[8],"w"),indent=1)
