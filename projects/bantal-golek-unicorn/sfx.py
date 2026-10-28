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
def shimmer():   # magic-wand glissando: fast rising music-box run + airy sparkle tail
    x=np.zeros(int(1.1*SR))
    for i,f in enumerate([1047,1319,1568,2093,2637,3136,4186]):
        s=ding(f,0.5)*(0.5+0.07*i); o=int(i*0.045*SR); x[o:o+len(s)]+=s[:len(x)-o]
    tt=t(1.1); air=np.diff(rng.standard_normal(len(tt)+1))*np.exp(-tt*5)*np.minimum(1,tt*40)*0.12
    return x+air
def twinkle():   # tiny two-note star twinkle for glitter stars
    x=np.zeros(int(0.5*SR)); a=ding(2637,0.35)*0.7; b=ding(3951,0.4)
    x[:len(a)]+=a; o=int(0.06*SR); x[o:o+len(b)]+=b[:len(x)-o]
    return x
save('shimmer',shimmer()); save('twinkle',twinkle())
def music(d=48.0, bpm=96):
    # gentle "unicorn" music bed (no licensed audio): pad + music-box arpeggio + soft bass + shaker,
    # chords C-G-Am-F, one bar each. The user can swap it for a trending sound in TikTok.
    beat=60/bpm; bar=4*beat; n=int(d*SR); x=np.zeros(n); tt_all=np.arange(n)/SR
    chords=[[261.63,329.63,392.00],[246.94,293.66,392.00],[220.00,261.63,329.63],[220.00,261.63,349.23]]
    roots=[130.81,98.00,110.00,87.31]
    nb=int(np.ceil(d/bar))
    for b in range(nb):
        c=chords[b%4]; r=roots[b%4]; o=int(b*bar*SR); L=min(int(bar*SR), n-o)
        if L<=0: break
        tt=np.arange(L)/SR
        env=np.minimum(1,tt/0.4)*np.minimum(1,(bar-tt)/0.3)
        pad=sum(np.sin(2*np.pi*f*tt)+0.5*np.sin(2*np.pi*f*1.003*tt)+0.25*np.sin(2*np.pi*f*2*tt) for f in c)
        x[o:o+L]+=pad*env*0.05
        for k in (0,2):                                   # bass on beats 1 and 3
            bo=o+int(k*beat*SR); bl=min(int(beat*1.8*SR), n-bo)
            if bl>0:
                bt=np.arange(bl)/SR; x[bo:bo+bl]+=np.sin(2*np.pi*r*bt)*np.exp(-bt*2.2)*np.minimum(1,bt*200)*0.22
        arp=[c[0]*2,c[1]*2,c[2]*2,c[1]*2,c[0]*4,c[2]*2,c[1]*2,c[2]*2]
        for k,f in enumerate(arp):                        # music-box 8ths
            ao=o+int(k*beat/2*SR); s=ding(f,0.7)*0.16
            al=min(len(s), n-ao)
            if al>0: x[ao:ao+al]+=s[:al]
        for k in range(8):                                # shaker on the off-8ths
            if k%2==1:
                so=o+int(k*beat/2*SR); sl=min(int(0.06*SR), n-so)
                if sl>0:
                    st=np.arange(sl)/SR; x[so:so+sl]+=np.diff(rng.standard_normal(sl+1))*np.exp(-st*70)*0.05
    fade=np.minimum(1,tt_all/1.0)*np.minimum(1,(d-tt_all)/1.5)
    return x*fade
save('music',music())
