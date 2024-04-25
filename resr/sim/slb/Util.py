import salabim as sim


class SNS:
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)


def Enum(name, n):
    return [f"{name}{i:02d}" for i in range(1,n+1)]


def TU(env):
    """ TODO: return dict of functions: SIM.env.hours(), SIM.env.days(), etc
    """
    D = {'year'   : 365*24*60*60,
         'week'   : 7*24*60*60,
         'day'    : 24*60*60,
         'hour'   : 60*60,
         'minute' : 60,
         'second' : 1,}
    D['yr' ] = D['year'  ]
    D['wk' ] = D['week'  ]
    D['day'] = D['day'   ]
    D['hr' ] = D['hour'  ]
    D['min'] = D['minute']
    D['sec'] = D['second']
    D['years'  ] = D['year'  ]
    D['weeks'  ] = D['week'  ]
    D['days'   ] = D['day'   ]
    D['hours'  ] = D['hour'  ]
    D['minutes'] = D['minute']
    D['seconds'] = D['second']
    return D




def RV(env, dist, time_unit, rs, *pars):
    if dist.lower() in ('exponential', 'exp'):
        return env.Exponential(mean=pars[0], 
                               time_unit=time_unit, 
                               randomstream=env.random.Random(rs))

    if dist.lower() in ('gamma', 'mm'):
        return env.Gamma(shape=pars[0], 
                         scale=pars[1], 
                         time_unit=time_unit, 
                         randomstream=env.random.Random(rs))
    
    if dist.lower() in ('uniform', 'uni'):
        return env.Uniform(lowerbound=pars[0], 
                           upperbound=pars[1], 
                           time_unit=time_unit, 
                           randomstream=env.random.Random(rs))
    
    if dist.lower() in ('normal', 'nor'):
        return env.Normal(mean=pars[0], 
                          standard_deviation=pars[1], 
                          time_unit=time_unit, 
                          randomstream=env.random.Random(rs))

    if dist.lower() in ('triangular', 'tri'):
        return env.Triangular(low=pars[0], 
                              mode=pars[1], 
                              high=pars[2], 
                              time_unit=time_unit, 
                              randomstream=env.random.Random(rs))

    if dist.lower() in ('sequence', 'seq'):
        def gen(L):
            for v in L:
                yield v / env.get_time_unit(time_unit, 1)
        g = gen(pars[0])
        return g.__next__


