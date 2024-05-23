"""
    types    = []
    priority = {}
    ia_time  = {}
    tasks    = {}

    types.append('A')
    types.append('B')
    priority ['A'] = 'A'  # lower value := higher priority
    priority ['B'] = 'B'
    ia_time  ['A'] = RV(SIM.env, 'ExpRt', 'hours', 123, 1.2)
    ia_time  ['B'] = RV(SIM.env, 'ExpRt', 'hours', 123, 2.2)

    tasks['A'] = [
        SNS(name='Get Lift',
            type='S',   
            rsgr='Lifts',
            ridx=0,
             dur=None),
        SNS(name='Oil Change',
            type='SDR',
            rsgr='Mechanics',
            ridx=1,
             dur={'SrMech' : RV(SIM.env, 'Tri', 'minutes', 123, 20, 30, 40),
                  'JrMech' : RV(SIM.env, 'Tri', 'minutes', 231, 25, 35, 50)}),
        SNS(name='Brake Svc',
            type='SDR',
            rsgr='Mechanics', 
            ridx=1,
             dur={'SrMech' : RV(SIM.env, 'Tri', 'minutes', 222, 20, 25, 30),
                  'JrMech' : RV(SIM.env, 'Tri', 'minutes', 333, 30, 35, 45)}),
        SNS(name='Rls Lift',
            type='R',
            rsgr='Lifts',
            ridx=0,
             dur=None),
        SNS(name='Test Drive',
            type='SDR', 
            ridx=1,
            rsgr='SrMechanics', 
             dur={'SrMech' : RV(SIM.env, 'Tri', 'minutes', 444, 25, 30, 35)}),
    ]

    tasks['B'] = [
        SNS(name='Get Lift',
            type='S',   
            rsgr='Lifts',
            ridx=0,
             dur=None),
        SNS(name='Oil Change',
            type='SDR',
            rsgr='Mechanics',
            ridx=1,
             dur={'SrMech' : RV(SIM.env, 'Tri', 'minutes', 733, 15, 20, 30),
                  'JrMech' : RV(SIM.env, 'Tri', 'minutes', 622, 20, 25, 35)}),
        SNS(name='Brake Svc',
            type='SDR',
            rsgr='Mechanics', 
            ridx=1,
             dur={'SrMech' : RV(SIM.env, 'Tri', 'minutes', 421, 25, 35, 40),
                  'JrMech' : RV(SIM.env, 'Tri', 'minutes', 534, 30, 40, 50)}),
        SNS(name='Rls Lift',
            type='R',
            rsgr='Lifts',
            ridx=0,
             dur=None),
        SNS(name='Test Drive',
            type='SDR', 
            rsgr='SrMechanics', 
            ridx=1,
             dur={'SrMech' : RV(SIM.env, 'Tri', 'minutes', 355, 15, 25, 30)}),
    ]
"""



def Extract_Value(O, D, fld, conv=None):
    if   conv is None:
        pass
    elif conv == "list":
        v = D[fld]
    elif conv == "int":
        v = int(D[fld])
    elif conv == "float":
        v = float(D[fld])
    elif conv == "str":
        v = str(D[fld])
    elif conv == "list:str":
        v = [str(x) for x in D[fld]]
    elif conv == "list:int":
        v = [int(x) for x in D[fld]]
    elif conv == "list:float":
        v = [float(x) for x in D[fld]]
    else:
        raise ValueError(f"Invalid operation={conv!r}")
    setattr(O, fld, v)


def Extract_Field(O, D, fld, op=None):
    setattr(O, fld, OBJ())
    for k,v in D[fld].items():
        if   op is None:
            pass
        elif op == "split":
            v = v.split()
        else:
            raise ValueError(f"Invalid operation={op!r}")
        setattr(getattr(O, fld), k, v)


def Traverse(V, pfx=""):
    if isinstance(V, (int, float, str, bool)):
        print(f"{pfx} = {V}")
    elif isinstance(V, dict):
        for k,v in V.items():
            Traverse(v, pfx + f"{k} : ")
    elif isinstance(V, list):
        for x in V:
            Traverse(x, pfx+" -")
    else:
        print(f"??? {V!r}")
        raise ValueError("Invalid")


def Read_yaml():
    with open(fn, 'r') as yf:
        D = yaml.safe_load(yf.read())


    Extract_Field(SHOP, D['SHOP'], 'ResourceTypes',  'split')
    Extract_Field(SHOP, D['SHOP'], 'ResourceGroups', 'split')

    Extract_Value(JOB, D['JOB'], 'types',    'list:str')
    # Extract_Field(JOB, D['JOB'], 'priority', None)
    JOB.priority = D['JOB']['priority']
    JOB.ia_time = D['JOB']['ia_time']

    print(dirm(SHOP))
    print(dirm(SHOP.ResourceGroups))
    print(dirm(SHOP.ResourceTypes))
    print("JOB.        ", dirm(JOB))
    print("JOB.types   ", JOB.types)
    print("JOB.priority", JOB.priority)
    print("JOB.ia_time ", JOB.ia_time)
    print(dirm(SIM))
    print("SIM.        ", dirm(JOB))
    print("SIM.        ", SIM)

    """
    D['RUN']
    D['SHOP']
    D['JOB']
    D['JOB']['types']
    D['JOB']['priority']
    D['JOB']['ia_time']
    D['JOB']['tasks']
    D['JOB']['tasks']['A']
    """

    return D


"""
mean
std.deviation
minimum
median
90% percentile
95% percentile
maximum


SIM.Resource['L01'].all_monitors()
  (Length of requesters of L01)
  (Length of stay in requesters of L01)
  (Length of claimers of L01)
  (Length of stay in claimers of L01)
  (Capacity of L01)
  (Available quantity of L01)
  (Claimed quantity of L01)
  (Occupancy of L01)

ASW.SIM.Resource['L01'].occupancy.mean()
ASW.SIM.Resource['L01'].occupancy.std()
ASW.SIM.Resource['L01'].claimed_quantity.mean()
ASW.SIM.Resource['L01'].claimed_quantity.std()


occupancy
requesters
claimed_quantity

all_monitors
available_quantity
base_name
capacity
claimers
deregister
env
ispreemptive
monitor
name
print_histograms
print_info
print_statistics
register
release
reset_monitors
sequence_number
set_capacity
setup



Statistics of JM04 at       100.000                                  all    excl.zero         zero
-------------------------------------------- -------------- ------------ ------------ ------------
Length of requesters of JM04                 duration            100            0          100
Length of stay in requesters of JM04         entries              65           65            0
                                             mean                  0            0
                                             std.deviation         0            0

                                             minimum               0            0
                                             median                0            0
                                             90% percentile        0            0
                                             95% percentile        0            0
                                             maximum               0            0

Length of claimers of JM04                   duration            100           54.833       45.167
                                             mean                  0.548        1
                                             std.deviation         0.498        0

                                             minimum               0            1
                                             median                1            1
                                             90% percentile        1            1
                                             95% percentile        1            1
                                             maximum               1            1

Length of stay in claimers of JM04           entries              64           64            0
                                             mean                  0.849        0.849
                                             std.deviation         0.260        0.260

                                             minimum               0.690        0.690
                                             median                0.754        0.754
                                             90% percentile        1.482        1.482
                                             95% percentile        1.534        1.534
                                             maximum               1.620        1.620

Capacity of JM04                             duration            100          100            0
                                             mean                  1            1
                                             std.deviation         0            0

                                             minimum               1            1
                                             median                1            1
                                             90% percentile        1            1
                                             95% percentile        1            1
                                             maximum               1            1

Available quantity of JM04                   duration            100           45.167       54.833
                                             mean                  0.452        1
                                             std.deviation         0.498        0

                                             minimum               0            1
                                             median                0            1
                                             90% percentile        1            1
                                             95% percentile        1            1
                                             maximum               1            1

Claimed quantity of JM04                     duration            100           54.833       45.167
                                             mean                  0.548        1
                                             std.deviation         0.498        0

                                             minimum               0            1
                                             median                1            1
                                             90% percentile        1            1
                                             95% percentile        1            1
                                             maximum               1            1

Occupancy of JM04                            duration            100           54.833       45.167
                                             mean                  0.548        1
                                             std.deviation         0.498        0

                                             minimum               0            1
                                             median                1            1
                                             90% percentile        1            1
                                             95% percentile        1            1
                                             maximum               1            1

"""


"""
    print("\nFinished but still requesting:", 
            sum(1 for j in SIM.Arrivals 
                if (j.t_fin is not None) and (j.rsgr_req is not None)))

    for typ in JOB.types:
        print(f"{typ}:")
        for j in SIM.Arrivals:
            if (j.job_type == typ) and (j.t_fin is not None):
                print(f"   {j.name()} {j.t_fin - j.t_arr:6.2f}", end=" ")
                for T in j.task:
                    if "S" in T.job_type:
                        print(f"S:{T.t_s_acq - T.t_s_req:4.2f}", end=" ")
                for T in j.task:
                    if "D" in T.job_type:
                        print(f"D:{T.t_d_fin - T.t_d_sta:4.2f}", end=" ")
                print()
"""
