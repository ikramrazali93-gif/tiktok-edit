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
def puff():
    # soft cushion squish: short low-passed noise thump with a gentle pitch-down body
    tt=t(0.32); n=rng.standard_normal(len(tt))
    body=np.sin(2*np.pi*np.cumsum(180-90*(tt/0.32))/SR)*np.exp(-tt*14)
    air=lp(n,0.12)*np.exp(-tt*11)*1.6
    return 0.8*body+air
save('puff',puff())
def plop():
    # avocado seed "plop": quick pitch-drop blip with a short wet body
    tt=t(0.16); f=520*np.exp(-tt*22)+140
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*24)*np.minimum(1,tt*900)
def rustle():
    # leaf rustle: three soft band-passed noise flicks
    x=np.zeros(int(0.5*SR))
    for o in (0.0,0.11,0.24):
        n=int(0.12*SR); c=hp(lp(rng.standard_normal(n),0.35),0.08)*np.sin(np.pi*np.arange(n)/n)**2
        i=int(o*SR); x[i:i+n]+=c[:len(x)-i]
    return x
save('plop',plop()); save('rustle',rustle())
def stamp():
    # rubber-stamp "thunk": short low body + papery click for the slanted badges
    tt=t(0.22); body=np.sin(2*np.pi*np.cumsum(220*np.exp(-tt*18)+70)/SR)*np.exp(-tt*22)
    clk=hp(rng.standard_normal(len(tt)),0.35)*np.exp(-tt*120)*0.7
    return body+clk
def duo():
    # two-note "duo" chime (low banana note, then high eggplant note)
    x=np.zeros(int(0.7*SR)); a=ding(1047,0.5)*0.8; b=ding(1568,0.55)
    x[:len(a)]+=a; o=int(0.09*SR); x[o:o+len(b)]+=b[:len(x)-o]
    return x
save('stamp',stamp()); save('duo',duo())
def jelly():
    # jelly "boing-wobble" for the chunky 3D labels: pitch wobbles down like a bouncing jelly
    tt=t(0.4); f=420+160*np.sin(2*np.pi*11*tt)*np.exp(-tt*7)-120*tt
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*9)*np.minimum(1,tt*300)
def note():
    # music-box pluck for the floating notes (tain-tain-tain)
    x=np.zeros(int(0.8*SR))
    for i,f in enumerate([1319,1568,2093]):
        s=ding(f,0.5)*(0.7 if i<2 else 0.9); o=int(i*0.08*SR); x[o:o+len(s)]+=s[:len(x)-o]
    return x
def slice_():
    # knife "slice" for the watermelon-wedge wipe: bright noise sweep with a short tail
    tt=t(0.28); n=rng.standard_normal(len(tt)); env=np.sin(np.pi*np.minimum(1,tt/0.28))**3
    return hp(lp(n,0.25+0.5*tt/0.28),0.2)*env
save('jelly',jelly()); save('note',note()); save('slice',slice_())
def knock():   # two quick wooden knocks: a signboard landing
    x = np.zeros(int(0.32 * SR))
    for o in (0.0, 0.11):
        tt = t(0.12); f = 420 * np.exp(-tt * 18) + 260
        k = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 45) + hp(rng.standard_normal(len(tt)), 0.3) * np.exp(-tt * 90) * 0.4
        i = int(o * SR); x[i:i + len(k)] += k * (1.0 if o == 0 else 0.7)
    return x
save('knock', knock())
def squish():  # soft frosting "splat": low wet thump with a short filtered-noise smear
    tt = t(0.3); f = 180 * np.exp(-tt * 12) + 90
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 16)
    smear = lp(rng.standard_normal(len(tt)), 0.08) * np.exp(-tt * 22) * 2.5
    return (body + smear) * np.minimum(1, tt * 400)
def sprinkles():  # a quick shower of tiny bright ticks, like sprinkles landing
    x = np.zeros(int(0.5 * SR))
    for i in range(14):
        o = int(rng.uniform(0, 0.38) * SR); tt = t(0.03)
        k = np.sin(2 * np.pi * rng.uniform(2600, 4200) * tt) * np.exp(-tt * 160)
        x[o:o + len(k)] += k * rng.uniform(0.4, 1.0)
    return x
save('squish', squish()); save('sprinkles', sprinkles())
def warp():  # sci-fi "pew" sweep: a falling sine with a phaser-ish shimmer, for labels landing from space
    tt=t(0.42); f=1800*np.exp(-tt*9)+220
    x=np.sin(2*np.pi*np.cumsum(f)/SR)+0.35*np.sin(2*np.pi*np.cumsum(f*1.5)/SR)
    return x*np.exp(-tt*7)*(1-np.exp(-tt*300))
def twinkle():  # little star chime: three high bell partials ringing up
    out=np.zeros(int(0.9*SR))
    for k,f0 in enumerate((2093,2637,3136)):
        tt=t(0.9-k*0.07); x=sum(a*np.sin(2*np.pi*f0*m*tt)*np.exp(-tt*q) for a,m,q in [(1,1,7),(.4,2.01,11)])
        o=int(k*0.07*SR); out[o:o+len(x)]+=x*0.7
    return out
def hum():  # soft spaceship hum swell for the blanket reveal
    tt=t(1.2); x=np.sin(2*np.pi*110*tt)+0.5*np.sin(2*np.pi*165*tt)+0.25*np.sin(2*np.pi*220.5*tt)
    return x*np.sin(np.pi*tt/1.2)**2
save('warp', warp()); save('twinkle', twinkle()); save('hum', hum())
