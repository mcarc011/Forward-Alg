#%%
import numpy as np
import sympy
import time
from scipy.linalg import null_space
from itertools import combinations_with_replacement
from itertools import combinations
from itertools import product

def jandeterms(filestr):
    with open(filestr,'r') as f:
        text = f.read()
        f.close()
    monomials = text.split('\\')
    monomials = [line.split(':')[1] for line in monomials if ':' in line]
    monomials = [line.replace(' & ','|') for line in monomials]
    monomials = [line.replace('&','') for line in monomials]
    return monomials

def chiraldic(jelist):
    chirals = {}
    for mon in jelist:
        Jterm,Eterm = mon.split('|')[1],mon.split('|')[2]
        Jterm,Eterm,mon = Jterm.replace('|',''), Eterm.replace('|',''), mon.replace('|','')
        Jterm,Eterm = Jterm.split('-'), Eterm.split('-')
        tempterm = {}
        for field in mon.split(' '):
            if '_' in field:
                if field not in chirals:
                    chirals[field] = []
                if field not in tempterm:
                    tempterm[field] = {}
                jinfo = [str(Jterm.index(i)) for i in Jterm if field in i]
                einfo = [str(Eterm.index(i)) for i in Eterm if field in i]
                if len(jinfo)!=1:
                    jinfo = []
                if len(einfo)!=1:
                    einfo = []
                tempterm[field]['J'] = jinfo
                tempterm[field]['E'] = einfo

        for term1 in tempterm:
            rel = ['','']
            for term2 in tempterm:
                if term1!=term2:
                    types = ['J','E']
                    for i,t in enumerate(types):
                        if tempterm[term1][t] != [] and tempterm[term2][t] != []:
                            if tempterm[term1][t] == tempterm[term2][t]:
                                rel[i] += 'inv'+term2+'*'
                            else:
                                rel[i] += term2+'*'
            for r in rel:
                if r !='':
                    chirals[term1] += [r]
    for field in chirals:
        if chirals[field] ==[]:
            chirals[field] = [field]
    return chirals

def findkmatrix(xdict,nodenum,chiralweight):       

    def turn2array(ktempdict):
        'TURN THE STRING DATA INTO ARRAYS'
        for chiral in ktempdict:
            datum = ktempdict[chiral].split(',')
            kvec = np.zeros(nodenum+3)
            for d in datum:
                if d!='':
                    zero = np.zeros(nodenum+3)
                    if '-' in d:
                        zero[abs(int(d))] = -1
                    else:
                        zero[abs(int(d))] = 1
                    kvec += zero
            if abs(np.sum(kvec))>1:
                raise ValueError
            ktempdict[chiral] = kvec
        return ktempdict
    
    chiralkeys = [t[1] for t in chiralweight]   
    
    'SEARCH FOR A RELABELING'
    for relabels in combinations(range(len(xdict)),nodenum+3):
        K = {}
        relabels = [chiralkeys[i] for i in list(relabels)]
        #relabels = [i for i in xdict if 'P' in i or '{12}' in i]
        for chiral in chiralkeys:
            if chiral in relabels:
                K[chiral] = str(relabels.index(chiral))
            else:
                for expression in xdict[chiral]:
                    for r in relabels:
                        expression = expression.replace(r,str(relabels.index(r)))
                    expression = expression.replace('*',',')
                    expression = expression.replace('inv','-')
                    if chiral not in K:
                        K[chiral] = expression
                    if expression.count('_')<K[chiral].count('_'):
                        K[chiral] = expression
        Unlabeledp = [0]
        Unlabeled = [K[key].count('_') for key in K]
        while np.sum(Unlabeledp)<np.sum(Unlabeled):
            Unlabeled = [K[key].count('_') for key in K]
            for chiral in K:
                for item in K[chiral].split(','):
                    chiral2 = item.replace('-','')
                    if '_' in item and chiral2 in K:
                        if '_' not in K[chiral2]:
                            K[chiral] = K[chiral].replace(item+',',K[chiral2])
                            K[chiral] = K[chiral].replace(item,K[chiral2])
            Unlabeledp = [K[key].count('_') for key in K]
        if np.sum(Unlabeledp)==0:
            try:
                Knew = turn2array(K)
                return Knew
            except ValueError:
                pass


def findtmatrix(kmatrix, nodenum,timer=False):
    tlist = []
    tlist2 = []
    for t in product(range(3),repeat=nodenum+3):
        store = True
        for k in kmatrix:
            if np.dot(t,k)<0:
                store = False
                break
        if store and t not in tlist and 2 not in t:
            tlist += [list(t)]
        if store and t not in tlist2 and 2 in t:
            tlist2 += [list(t)]
    tlist = [np.array(i) for i in tlist]
    tlist2 = [np.array(i) for i in tlist2]
    tvectors = tlist.copy()

    def treducefunc(tindv,ttest):
        start = time.time()
        tindvsig = [int(str(tj)[1:-1].replace(' ',''),3) for tj in tindv]
        for n,ti in enumerate(ttest):
            if n&20==0 and timer:
                print(round(100*(n/len(ttest)),2))
                print(int((time.time()-start)/60))

            #normv = np.linalg.norm(ti)
            tisig = int(str(ti)[1:-1].replace(' ',''),3)

            testvec = []
            testsig = []
            for i, tj in enumerate(tindv):
                if all(ti-tj) >= 0:
                    testvec += [tj]
                    testsig += [tindvsig[i]]

            save = True
            lengthi = 0

            while lengthi<np.sum(ti) or lengthi < len(testvec):
                lengthi += 1
                for addedarr in combinations(range(len(testvec)),lengthi):
                    sigtotal = np.sum([testsig[a] for a in addedarr])
                    if sigtotal == tisig:
                        save = False
                        break
                if not save:
                    break
            if save:
                tindv += [ti]
                tindvsig += [tisig]
        return tindv

    _, inds = sympy.Matrix(tlist).T.rref() 
    tprime = [tlist[i] for i in inds]
    tsort= [(round(np.linalg.norm(tp),2),ti) for ti,tp in enumerate(tprime)]
    tsort.sort()
    tprime = [tprime[tp[1]] for tp in tsort]
    tres = []
    for tind,t in enumerate(tlist):
        if tind not in inds:
            tres += [t]
    tlist = treducefunc(tprime,tres)

    tsig = set()
    testsig = [int(str(ti)[1:-1].replace(' ',''),4) for ti in tlist]
    tsig2 = [int(str(ti)[1:-1].replace(' ',''),4) for ti in tlist2]
    for li in range(2*len(tlist)):
        for addedarr in combinations_with_replacement(range(len(tlist)),li):
            tsig.add(np.sum([testsig[a] for a in addedarr]))
    for t1 in tsig2:
        if t1 not in testsig:
            pass

    return np.matrix([t0 for t0 in tlist if np.sum(t0)>0]),tvectors
    #return [tmatrix[i] for i in inds]

def dmatrix(xkeys,nodenum):
    D = []
    for chiral in xkeys:
        t0 = np.zeros(nodenum)
        ind = chiral[chiral.find('{')+1:chiral.find('}')]
        if '.' in ind:
            ind = ind.split('.')
            ind1,ind2 = int(ind[0]),int(ind[1])
        else:
            ind1,ind2 = int(ind[0]),int(ind[1])
        t0[ind1-1],t0[ind2-1] = 1,-1
        D += [t0]
    return np.transpose(D)[1:]
    

def Xweight(filestr,Xkeys):
    with open(filestr,'r') as f:
        text = f.read()
        f.close()
    xweights = []
    for key in Xkeys:
        xweights+=[(len(text.split(key))-1,key)]
    xweights.sort()
    return xweights

# def null_space(matrix):


def kmodel(name):
    if name =='1':
        #SPPxC
        K = [
            [1,1,0,0,0,0,0,0,0,0],
            [0,1,1,0,0,0,0,0,0,0],
            [0,0,0,1,0,0,-1,0,0,0],
            [0,0,0,0,1,0,1,0,0,0],
            [0,0,0,0,0,1,1,0,0,0],
            [0,0,0,0,0,0,0,1,1,1]
            ]
        K = np.transpose(K)

    if name =='2':
        #C4/z3
        K = [
            [1,0,0,0,0,-1,0,-1,-1,0,0,-1],
            [0,1,1,0,0,1,0,1,1,0,0,1],
            [0,-1,0,1,0,0,0,-1,0,0,-1,-1],
            [0,1,0,0,1,1,0,1,0,0,1,1],
            [0,0,0,0,0,0,1,1,1,0,0,0],
            [0,0,0,0,0,0,0,0,0,1,1,1],
            ]
        K = np.transpose(K)

    if name =='3':
        #c4/z2
        K = [
            [1,0,0,-1,0,-1,0,-1],
            [0,1,0,1,0,1,0,1],
            [0,0,1,1,0,0,0,0],
            [0,0,0,0,1,1,0,0],
            [0,0,0,0,0,0,1,1],
            ]
        K = np.transpose(K)
    return K

# def matrixnorm(fmatrix):
#     fmatrix = np.transpose([np.array([round(q,2) for q in fm]) for fm in fmatrix])
#     fmnorm = np.amin([abs(fmatrix.flatten()[i]) for i in np.nonzero(fmatrix.flatten())])
#     fmatrix = np.transpose(fmatrix/fmnorm)
#     return fmatrix

#models = [(8,'model9.txt')]
#models = [(10,'model15.txt')]

#models = [(6,'model3.txt')]
#models = [(4,'c4z4.txt')]
#models = [(2,'c4z2.txt')]
#models = [(2,'cxC.txt')]
#models = [(3,'sppxc.txt')]
models = [(4,'q111.txt')]

import re
def convert_to_latex_subscript(s):
    # Use regex to find a letter followed by numbers with a decimal and replace it with LaTeX subscript
    result = re.sub(r'([A-Z])(\d+\.\d+)\.', r'\1_{\2} ', s)
    return result.strip()

M = 17
with open('QuiverData\\model'+str(M)+'.txt','r') as f:
    data = f.read()
    data = data.replace('array','np.array')
    data = eval(data)
    data = data[-1][2]
    f.close()   
models = [(12,'QuiverData\\model'+str(M)+'.txt','r')]
jeterms=[]
sgndict = {'++':'+','--':'+','+-':'-','-+':'-'}
for fermi in data:
    terms = data[fermi]
    terms = [t.replace(',',' ') for t in terms]
    terms = [' '.join([convert_to_latex_subscript(t) for t in ti.split(',')]) for ti in terms]
    sgn1,sgn2 = terms[0][0] + terms[1][0], terms[2][0]+terms[3][0]
    if sgn1 in sgndict:
        sgn1 = sgndict[sgn1]
    if sgn2 in sgndict:
        sgn2 = sgndict[sgn2]
    terms = [t[1:] for t in terms]
    jeterms += ['|' + terms[0] + sgn1 + terms[1] + '|' + terms[2] + sgn2 + terms[2] + '|']

    

for m in models:
    #jeterms = jandeterms(m[1])
    xdict = chiraldic(jeterms)
    k = findkmatrix(xdict,m[0],Xweight(m[1],xdict.keys()))
    skey2 = k.keys()
    Km = [k[n] for n in skey2]

    T,tvec = findtmatrix(Km,m[0])
    P = sympy.Matrix(Km*np.transpose(T))

    # Dt = sympy.Matrix(dmatrix(list(skey2),m[0]))
    # Qd = P.gauss_jordan_solve(Dt.T)
    # Qdeval = Qd[0]
    # for var in Qd[1]:
    #     Qdeval = Qdeval.subs(var,0)
    # Qd = Qdeval.T

    # Et = P.nullspace()
    # Et = sympy.Matrix([list(e.T) for e in Et])

    # Qt = Qd.row_insert(0,Et)

    # G = Qt.nullspace()
    # G = sympy.Matrix([list(g.T) for g in G])


#%%






