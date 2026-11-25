"""Read-only: configurational temperature of molecule-centre translation in stored frames, by species size.
usage: tconf.py PACKAGE OUT SKIP_PS NFRAMES CUTOFF EWTOL OUTJSON"""
import sys, json
from pathlib import Path
import numpy as np, h5py, openmm as mm
from openmm import unit
from ucmd_bridge.package import load
from ucmd_bridge.model import NonbondedSettings, build_system
KB=8.31446261815324e-3
pkg,out,skip,nfr,rc,tol=sys.argv[1],Path(sys.argv[2]),float(sys.argv[3]),int(sys.argv[4]),float(sys.argv[5]),float(sys.argv[6])
top=load(pkg)
system,_=build_system(top,NonbondedSettings.from_provider(dict(kind="force-field",cutoff_nm=rc,coulomb="pme",ewald_tolerance=tol,dispersion_correction=False)))
ctx=mm.Context(system,mm.VerletIntegrator(1e-3),mm.Platform.getPlatformByName("CPU"),{"Threads":"6"})
h=h5py.File(out/"trajectory.h5","r"); p=h["particles/all"]; mi=p["molecule_index"][:]; m=p["mass"][:]; m=m if m.ndim==1 else m[0]
assert np.allclose(m,top.masses_amu)
nm=mi.max()+1; M=np.bincount(mi,m); first=np.array([np.argmax(mi==k) for k in range(nm)]); size=np.bincount(mi)
t=p["position/time"][:]; idx=np.where(t>=skip)[0]; idx=idx[np.unique(np.linspace(0,len(idx)-1,nfr).astype(int))]
o=h["observables/temperature"]; Tt,Tv=o["time"][:],o["value"][:]
rng=np.random.default_rng(2); sm=lambda f:np.stack([np.bincount(mi,f[:,k],nm) for k in range(3)],1)
def force(x):
    ctx.setPositions(x); return ctx.getState(getForces=True).getForces(asNumpy=True).value_in_unit(unit.kilojoule_per_mole/unit.nanometer)
F2,LP,TT,HB=[],[],[],[]
for i in idx:
    L=np.asarray(p["box/edges/value"][i])[0,0]; x=p["position/value"][i].astype(float); x-=L*np.round((x-x[first[mi]])/L)
    ctx.setPeriodicBoxVectors([L,0,0],[0,L,0],[0,0,L]); f=force(x); F=sm(f); d=2e-4; s=rng.choice([-1.,1.],(nm,3))
    dF=-(sm(force(x+d*s[mi]))-sm(force(x-d*s[mi])))*s/(2*d)
    F2.append((F**2).sum(1)); LP.append(dF.sum(1)); TT.append(Tv[np.argmin(abs(Tt-t[i]))])
    HB.append((f**2/(4*m[:,None])).sum()*1e-6/((3*len(m)-3)*KB))   # half-step minus on-step T, dt = 1 fs
F2,LP=np.array(F2),np.array(LP)
def jk(mask,nb=8):
    b=np.array_split(np.arange(len(F2)),nb); g=lambda z:F2[z][:,mask].sum()/LP[z][:,mask].sum()/KB
    v=[g(np.concatenate([b[a] for a in range(nb) if a!=c])) for c in range(nb)]
    return g(np.arange(len(F2))),float(np.sqrt((nb-1)/nb*((np.array(v)-np.mean(v))**2).sum()))
res={"all":jk(np.ones(nm,bool))}
for z in sorted(set(size)): res[f"molecules of {z} atoms"]=jk(size==z)
res["T displayed"]=(float(np.mean(TT)),float(np.std(TT)/np.sqrt(len(TT))))
res["half-step minus on-step T (dt=1fs)"]=(float(np.mean(HB)),float(np.std(HB)/np.sqrt(len(HB))))
print(out,len(F2)); [print(f"  {k:40s}{v[0]:9.2f} +- {v[1]:.2f} K") for k,v in res.items()]
json.dump(res,open(sys.argv[7],"w"),indent=1)
