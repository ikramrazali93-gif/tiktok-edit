import numpy as np, wave, sys, os
SR=48000; out=sys.argv[1]; rng=np.random.default_rng(7)
def save(name,x):
    x=x/ (np.max(np.abs(x))+1e-9)*0.9
    st=np.stack([x,x],1)
    w=wave.open(os.path.join(out,name+'.wav'),'w'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st*32767).astype(np.int16).tobytes()); w.close()
def t(d): return np.arange(int(d*SR))/SR
def lp(x,a):  # time-varying one-pole lowpass, a in (0,1]
    y=np.zeros_like(x); s=0.0
    a=np.broadcast_to(a,x.shape)
    for i in range(len(x)): s+=a[i]*(x[i]-s); y[i]=s
    return y
def hp(x,a): return x-lp(x,a)
def whoosh(d=0.55, up=True):
    tt=t(d); n=rng.standard_normal(len(tt))
    env=np.sin(np.pi*tt/d)**2
    cut=np.linspace(0.02,0.35,len(tt)) if up else np.linspace(0.35,0.02,len(tt))
    cut=0.02+0.33*np.sin(np.pi*tt/d)
    return hp(lp(n,cut),0.01)*env
def pop():
    tt=t(0.12); f=900*np.exp(-tt*25)+180
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*30)
def ding(f0=1568,d=1.0):
    tt=t(d); x=sum(a*np.sin(2*np.pi*f0*m*tt)*np.exp(-tt*k) for a,m,k in [(1,1,4),(.5,2.01,6),(.3,3.02,9),(.2,4.2,12)])
    return x*np.minimum(1,tt*400)
def sparkle():
    x=np.zeros(int(0.9*SR))
    for i,f in enumerate([2093,2637,3136,4186]):
        s=ding(f,0.6)*0.6; o=int(i*0.07*SR); x[o:o+len(s)]+=s[:len(x)-o]
    return x
def impact():
    tt=t(0.7); f=90*np.exp(-tt*6)+40
    b=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*5)
    n=lp(rng.standard_normal(len(tt)),0.08)*np.exp(-tt*18)*2
    return b+n
def riser(d=1.0):
    tt=t(d); f=200+1800*(tt/d)**2
    n=hp(lp(rng.standard_normal(len(tt)),0.05+0.4*tt/d),0.02)
    return (0.5*np.sin(2*np.pi*np.cumsum(f)/SR)*0.3+n)*(tt/d)**2
def zip_():
    d=0.55; x=np.zeros(int(d*SR)); tm=0.0; k=0
    while tm<d-0.01:
        c=hp(rng.standard_normal(int(0.004*SR)),0.3)*np.exp(-np.arange(int(0.004*SR))/60)
        o=int(tm*SR); x[o:o+len(c)]+=c[:len(x)-o]; tm+=0.03*np.exp(-k*0.06)+0.006; k+=1
    return x*np.linspace(0.6,1,len(x))
def click():
    tt=t(0.04); return hp(rng.standard_normal(len(tt)),0.4)*np.exp(-tt*200)+np.sin(2*np.pi*2500*tt)*np.exp(-tt*150)
def kaching():
    x=np.zeros(int(1.2*SR)); a=ding(2637,0.9); b=ding(3520,1.0)
    x[:len(a)]+=a; o=int(0.09*SR); x[o:o+len(b)]+=b[:len(x)-o]
    c=hp(rng.standard_normal(int(0.08*SR)),0.5)*np.exp(-np.arange(int(0.08*SR))/800)*0.5; x[:len(c)]+=c
    return x
def spray():
    d=0.7; tt=t(d); n=rng.standard_normal(len(tt))
    env=np.minimum(1,tt/0.015)*np.exp(-np.maximum(0,tt-0.35)*9)
    return hp(lp(n,0.6),0.25)*env
def bloop():
    tt=t(0.18); f=300+900*(tt/0.18)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.sin(np.pi*tt/0.18)
save('spray',spray()); save('bloop',bloop())
save('whoosh',whoosh()); save('swish',whoosh(0.3)); save('pop',pop()); save('ding',ding())
save('sparkle',sparkle()); save('impact',impact()); save('riser',riser()); save('zip',zip_())
save('click',click()); save('kaching',kaching())
def pluck(f0=660,d=0.45):
    # Karplus-Strong plucked string: soft "tik" for the speech-bubble labels (refresh v5)
    n=int(SR/f0); buf=rng.uniform(-1,1,n); out=np.zeros(int(d*SR))
    for i in range(len(out)):
        out[i]=buf[i%n]; buf[i%n]=0.5*(buf[i%n]+buf[(i+1)%n])*0.996
    return out*np.exp(-t(d)*6)
save('pluck',pluck()); save('pluck_hi',pluck(990,0.35))
def whip(d=0.2):
    # short airy whip for the ticket labels sliding in from the side (refresh v6)
    tt=t(d); n=rng.standard_normal(len(tt)); env=np.sin(np.pi*tt/d)**3
    return hp(lp(n,0.15+0.5*tt/d),0.05)*env
def boing(d=0.5):
    # springy "boing" (pitch wobble) for the banana iris-pop transition (refresh v6)
    tt=t(d); f=220+90*np.sin(2*np.pi*11*tt)*np.exp(-tt*5)+60*np.exp(-tt*8)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*5)*np.minimum(1,tt*300)
save('whip',whip()); save('boing',boing())
def thud(d=0.28):
    # soft cushion "thud" + tiny pitch drop for the seed-badge labels dropping in (refresh v7)
    tt=t(d); f=150*np.exp(-tt*6)+70
    body=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*16)
    puff=lp(rng.standard_normal(len(tt)),0.08)*np.exp(-tt*30)*0.6
    return (body+puff)*np.minimum(1,tt*400)
def shutter(n=5,gap=0.045):
    # quick run of soft clicks for the blinds transition (refresh v7)
    out=np.zeros(int((n*gap+0.08)*SR))
    for i in range(n):
        c=hp(rng.standard_normal(int(0.02*SR)),0.3)*np.exp(-t(0.02)*180)*(0.7+0.3*(i%2))
        s=int(i*gap*SR); out[s:s+len(c)]+=c
    return out
save('thud',thud()); save('shutter',shutter())
