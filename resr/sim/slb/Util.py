import salabim as sim


class SNS:
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)


def Enum(name, n):
    return [f"{name}{i:02d}" for i in range(1,n+1)]


TU = {'years'   : sim.Uniform(1, 1, 'years')(),
      'weeks'   : sim.Uniform(1, 1, 'weeks')(),
      'days'    : sim.Uniform(1, 1, 'days')(),
      'hours'   : sim.Uniform(1, 1, 'hours')(),
      'minutes' : sim.Uniform(1, 1, 'minutes')(),
      'seconds' : sim.Uniform(1, 1, 'seconds')(),}
TU['yr' ] = TU['years'  ]
TU['wk' ] = TU['weeks'  ]
TU['day'] = TU['days'   ]
TU['hr' ] = TU['hours'  ]
TU['min'] = TU['minutes']
TU['sec'] = TU['seconds']



def RV(dist, time_unit, rs, *pars):
    if dist.lower() in ('exponential', 'exp'):
        return sim.Exponential(mean=pars[0], 
                               time_unit=time_unit, 
                               randomstream=sim.random.Random(rs))

    if dist.lower() in ('gamma', 'mm'):
        return sim.Gamma(shape=pars[0], 
                         scale=pars[1], 
                         time_unit=time_unit, 
                         randomstream=sim.random.Random(rs))
    
    if dist.lower() in ('uniform', 'uni'):
        return sim.Uniform(lowerbound=pars[0], 
                           upperbound=pars[1], 
                           time_unit=time_unit, 
                           randomstream=sim.random.Random(rs))
    
    if dist.lower() in ('normal', 'nor'):
        return sim.Normal(mean=pars[0], 
                          standard_deviation=pars[1], 
                          time_unit=time_unit, 
                          randomstream=sim.random.Random(rs))

    if dist.lower() in ('triangular', 'tri'):
        return sim.Triangular(low=pars[0], 
                              mode=pars[1], 
                              high=pars[2], 
                              time_unit=time_unit, 
                              randomstream=sim.random.Random(rs))

    if dist.lower() in ('sequence', 'seq'):
        def gen(L):
            for v in L:
                yield v * TU[time_unit]
        g = gen(pars[0])
        return g.__next__


