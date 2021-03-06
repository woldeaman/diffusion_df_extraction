# functions and definitions for modeling of
# one dimensional concentration profiles by the smoluchowski equation
# in order to obtain diffusivity and free energy profiles
# -*- coding: utf-8 -*-
import numpy as np
import scipy.linalg as al
import scipy.special as sp
import numpy.linalg as la
import sys


def compute_c_bulk_stdev(cc_original, scalings_std, xx, x_tot=1780):
    """Compute standart deviation for fitted average c_bulk."""
    dx = xx[1] - xx[0]  # discretization width
    length_bulk = x_tot - np.max(xx)  # length of bulk phase
    # error from gauß error propagation
    c_bulk_std = [std*(dx*np.sum(c_og))/length_bulk
                  for std, c_og in zip(scalings_std, cc_original[1:])]
    return c_bulk_std


def compute_avg_c_bulk(cc_scaled, xx, dxx_width, x_tot=1780):
    """Compute corresponding average bulk concentration from fitted scalings."""
    dx = xx[1] - xx[0]  # discretization width
    length_bulk = x_tot - np.max(xx)  # length of bulk phase
    c_tot = np.sum(dxx_width*cc_scaled[0])  # total amount from c(t=0) profile

    # compute total amount of concentration for profiles
    c_amount = [dx * np.sum(c) for c in cc_scaled[1:]]
    c_bulk_avg = [(c_tot - c_am)/length_bulk for c_am in c_amount]

    return c_bulk_avg


def build_zero_profile(cc, bins_bulk=6):
    """Build profile at t=0 by extending measured concentration into bulk."""
    # assuming c = const. in bulk at t = 0
    c_const = cc[0, 0]  # extend first value through bulk
    c0 = cc[:, 0]
    c0 = np.concatenate((np.ones(bins_bulk)*c_const, c0))
    cc = [c0] + [cc[:, i] for i in range(1, cc[0, :].size)]  # now with c0

    return cc


def discretization_Block(xx, x_tot=1780):
    """Set up discretization for measured system in Block experiments."""
    # original discretization
    dx_og = xx[1] - xx[0]
    dim = xx.size  # number of measured bins

    # lenght of the different segments for computation
    x_2 = np.max(xx)  # length of segment 2, gel phase
    x_1 = x_tot - x_2  # length of segment 1, bulk phase

    # defining discretization, in bulk first 4 bins with dx1, next 2 bins with dx2
    dx2 = dx_og  # in gel
    dx1 = (x_1-2.5*dx2)/3.5  # in bulk

    # vectors for distance between bins dxx_dist and bin width dxx_width
    dxx_width = np.concatenate((np.ones(3)*dx1, np.ones(1)*(dx1+dx2)/2,
                                np.ones(2+dim)*dx2))  # used for concentration
    # dxx_dist contains distance to previous bin, at first bin same dx is taken
    dxx_dist = np.concatenate((np.ones(4)*dx1,  # used for WMatrix
                               np.ones(2+dim+1)*dx2))
    # dxx_dist has one element more than dxx_width because it's for WMatrix
    # computation dx at i+1 is necccessary --> needed for last bin too

    return dxx_dist, dxx_width


# definition of rate matrix
# with reflective BCs or one sided open BCs
# in case of open BCs df contains d and f for leftmost bin outside domain
# TODO: check this, why is it so different from roberts results?
def WMatrixGrima(d, f, deltaX=1, bc='reflective'):
    '''
    Calculates entries of rate matrix W with rank F.size
    definition in R. Grima, PRE, 2004
    '''
    if d.size != f.size:
        print('Something\'s wrong, not same lenght of F and D')
        sys.exit()
    else:
        n = d.size  # number of bins

    # transition rates only to nearest neighbours
    W = np.array([[(np.sqrt(d[i]*d[j])/(deltaX**2))*np.exp(-(f[i]-f[j]))
                   if (abs(j-i) == 1) else 0
                   for j in range(n)] for i in range(n)])
    # then add rates to leave on main diagonal from original matrix
    for i in range(n):
        W[i, i] = -np.sum([W[j, i] for j in range(n)])

    # boundary conditions differ only in the part of the matrix we use for
    # further analysis
    if bc == 'reflective':
        return W
    elif bc == 'open1side':
        # returning truncated matrix as well as W[1, 0]
        # which is used for further calculations
        return W[1:, 1:], W[1, 0]
    else:
        print('Error: Invalid boundary conditions!')
        sys.exit()


def stepDF(df, t, xx):
    '''
    Function computes step-function profile for D and F
    df = [df1, df2] - list containing diffusivity or free energy values
    t - location of jump
    xx - position at wich D or F profile is computed
    '''

    DF = []
    for x in xx:
        if x < t:
            DF.append(df[0])
        else:
            DF.append(df[1])

    return np.array(DF)


def sigmoidalDF(df, t, d, x):
    '''
    Function computes sigmoidal D or F profile based on errorfunction.
    df = [df1, df2] - list containing diffusivity or free energy values
    t - location of interface between segment 1 and 2
    d - length of sigmoidal transition regime between segment 1 and 2
    x - position at wich D or F profile is computed
    '''
    DF = 0.5*((df[0]+df[1]) + (df[1]-df[0])*sp.erf((x-t)/(np.sqrt(2)*d)))
    return DF


def WMatrixVar(d, f, start, deltaXX, end=None, con=False):
    '''
    Rate matrix for variable discretization widths,
    d, f - diffusivity, free energy
    start, end - start and end transitions between discretizations
    if end is 'None' only two segments will be assumed
    deltaXX - discretization array (has deltaX for each bin)
    con - flag for c-conservation --> W-Matrix check
    '''

    # segment1 with new definition for variable binning in areas of const. D, F
    DiagUp1 = np.array([2*d[i]/(deltaXX[i+1]*(deltaXX[i+1]+deltaXX[i]))
                       for i in range(start)])
    DiagDown1 = np.array([2*d[i]/(deltaXX[i]*(deltaXX[i+1]+deltaXX[i]))
                          for i in range(start)])
    MainDiag1 = np.array([-2*d[i]/(deltaXX[i+1]*deltaXX[i])
                          for i in range(start)])
    MainDiag1[0] = -DiagDown1[1]
    # MainDiag1[0] = -2*d[1]/(deltaXX[1]*(deltaXX[2]+deltaXX[1]))

    if con:
        if np.any(np.array([d[i] != d[i+1] for i in range(start+1)])):
            print('Error: D is not kept constant in segment 1!\n D = ',
                  [d[i] for i in range(start+1)])
            sys.exit()
        if np.any(np.array([f[i] != f[i+1] for i in range(start+1)])):
            print('Error: F is not kept constant in segment 1!\n F = ',
                  [f[i] for i in range(start+1)])
            sys.exit()

    if end is None:
        stop = d.size
        d = np.append(d, d[-1])  # extending d and f for full WMatrix computation
        f = np.append(f, f[-1])
        # last entry of DiagUp2 and MainDiag2 is correctly computed
    else:
        stop = end

    # segment2 with standart definition for constant deltaX and variable D and F
    DiagUp2 = np.array([(d[i]+d[i+1])/(2*(deltaXX[i])**2) *
                        np.exp(-(f[i]-f[i+1])/2) for i in range(start, stop)])

    DiagDown2 = np.array([(d[i]+d[i-1])/(2*(deltaXX[i])**2) *
                          np.exp(-(f[i]-f[i-1])/2) for i in range(start, stop)])

    MainDiag2 = np.array([-(d[i-1]+d[i])/(2*(deltaXX[i])**2) *
                          np.exp(-(f[i-1]-f[i])/2) -
                          (d[i+1]+d[i])/(2*(deltaXX[i])**2) *
                          np.exp(-(f[i+1]-f[i])/2) for i in range(start, stop)])
    if end is None:
        # reflective BC now here
        MainDiag2[-1] = -DiagUp2[-2]

    if con:
        if np.any(np.array([deltaXX[i] != deltaXX[i+1]
                            for i in range(start, stop)])):
            print('Error: deltaX is not kept constant in segment 2!\n'
                  'deltaX = ',
                  [deltaXX[i] for i in range(start, stop)])
            sys.exit()

    if end is not None:
        # segment3 with new definition
        DiagUp3 = np.array([2*d[i]/(deltaXX[i+1]*(deltaXX[i+1]+deltaXX[i]))
                           for i in range(end, d.size)])
        DiagDown3 = np.array([2*d[i]/(deltaXX[i]*(deltaXX[i+1]+deltaXX[i]))
                              for i in range(end, d.size)])
        MainDiag3 = np.array([-2*d[i]/(deltaXX[i+1]*deltaXX[i])
                              for i in range(end, d.size)])
        MainDiag3[-1] = -DiagUp3[-2]
        # MainDiag3[-1] = -2*d[-1]/(deltaXX[-2]*(deltaXX[-2]+deltaXX[-3]))

        if con:
            if np.any(np.array([d[i-1] != d[i] for i in range(end-1, d.size)])):
                print('Error: D is not kept constant in segment 3!\n D = ',
                      [d[i] for i in range(end-1, d.size)])
                sys.exit()
            if np.any(np.array([f[i-1] != f[i] for i in range(end-1, d.size)])):
                print('Error: F is not kept constant in segment 3!\n F = ',
                      [f[i] for i in range(end-1, d.size)])
                sys.exit()

        DiagUp = np.concatenate((DiagUp1, DiagUp2, DiagUp3))
        DiagDown = np.concatenate((DiagDown1, DiagDown2, DiagDown3))
        MainDiag = np.concatenate((MainDiag1, MainDiag2, MainDiag3))

    else:
        DiagUp = np.concatenate((DiagUp1, DiagUp2))
        DiagDown = np.concatenate((DiagDown1, DiagDown2))
        MainDiag = np.concatenate((MainDiag1, MainDiag2))

    W = np.diag(MainDiag) + np.diag(DiagUp[:-1], 1) + np.diag(DiagDown[1:], -1)

    if con:
        if(np.sum(W, 0)[0] != 0 or np.sum(W, 0)[-1] != 0):
            print('Error: Wrong implementation of BCs!\n Row1, RowN:',
                  np.sum(W, 0)[0], np.sum(W, 0)[-1])
            sys.exit()

    return W


def computeDF(d, f, shape, mode='segments', transiBin=None, dx=None):
    '''
    Function generates D and F array for different segments, each with constant
    d and f and an additional option for linear transition between segments.
    Shape array with information about segments needs to be given.
    '''
    dim = int(shape.size)

    if mode == 'segments':
        # generating D and F from shape array
        D = np.array([d[shape[i]] for i in range(dim)])
        F = np.array([f[shape[i]] for i in range(dim)])

    elif (mode == 'transition') and (transiBin is None or dx is None):
        print('Error: Transition distance and location must be given'
              'for df computation!')
        sys.exit()
    elif mode == 'transition':
        dist = round(dx)
        # computing left and right half of transition bin
        if dist % 2 == 0:
            x = int(dist/2)
            y = int(dist/2)
        else:
            x = np.floor(dist/2).astype(int)
            y = np.ceil(dist/2).astype(int)

        # calculating d and f before transition
        DPre = np.array([d[shape[i]] for i in range(transiBin-x)])
        FPre = np.array([f[shape[i]] for i in range(transiBin-x)])

        # calculating d and f at transition
        DTrans = np.linspace(d[shape[transiBin-x]],
                             d[shape[transiBin+y]], dist)
        FTrans = np.linspace(f[shape[transiBin-x]],
                             f[shape[transiBin+y]], dist)

        # calculating d and f after transition
        DPost = np.array([d[shape[i]] for i in range(transiBin+y, dim)])
        FPost = np.array([f[shape[i]] for i in range(transiBin+y, dim)])

        D = np.concatenate((DPre, DTrans, DPost))
        F = np.concatenate((FPre, FTrans, FPost))
    else:
        print('Error: Unkown mode for df computation.')
        sys.exit()

    return D, F


# definition of rate matrix
# with reflective BCs or one sided open BCs
# in case of open BCs df contains d and f for leftmost bin outside domain
def WMatrix(d, f, deltaX=1, bc='reflective'):
    '''
    Calculates entries of rate matrix W with rank F.size
    definition in R. Schulz, PNAS, 2016.
    Column sum has to be zero per definition --> concentration is conserved!
    '''

    FUp = f - np.roll(f, -1)  # F contributions off-diagonal
    FDown = f - np.roll(f, 1)

    DUp = d + np.roll(d, -1)  # D contributions off-diagonal
    DDown = d + np.roll(d, 1)

    # computing off-diagonals (dimensionless)
    DiagUp = DUp/(2*(deltaX)**2) * np.exp(-FUp/2)
    DiagDown = DDown/(2*(deltaX)**2) * np.exp(-FDown/2)

    DiagUp[-1] = 0  # reflective bc's
    DiagDown[0] = 0

    # main diagonal is negative sum of off-diagonals
    DiagMain = -(np.roll(DiagUp, 1) + np.roll(DiagDown, -1))

    # constructing W Matrix from diagonal entries
    W = np.diag(DiagMain) + np.diag(DiagUp[:-1], 1) + np.diag(DiagDown[1:], -1)

    # boundary conditions differ only in the part of the matrix we use for
    # further analysis
    if bc == 'reflective':
        return W
    elif bc == 'open1side':
        # returning truncated matrix as well as W[1, 0]
        # which is used for further calculations
        return W[1:, 1:], W[1, 0]
    else:
        print('Error: Invalid boundary conditions!')
        sys.exit()


# calulating concentration profile at time t from previous times
# with given W matrix
def calcC(cc, t, W=None, T=None, bc='reflective', W10=None, c0=None, Qb=None,
          Q=None, b=None):
    '''
    Calculates concentration profiles at time t from W or T matrix with
    reflective or open boundaries, based on concentration profile cc.
    Due to computing exp(W*dt) as T^dt, only integers are allowed for 't'.
    '''

    # calculate only variables that are not given
    if T is None:
        if W is None:
            print('Error: Either W or T Matrix must be given for computation!')
            sys.exit()
        else:
            T = al.expm(W)  # exponential of W
    dim = T[0, :].size

    if bc == 'open1side':
        if Qb is None:
            if Q is None:
                if W is None:
                    print('Error: Either W or Q Matrix must be given for'
                          ' computation!')
                    sys.exit()
                Q = la.inv(W)  # inverse of W
            if b is None:
                if (W10 is None) or (c0 is None):
                    print('Error: W10 and c0 must be specified for'
                          'open boundaries!')
                    sys.exit()
                b = np.append(c0*W10, np.zeros(dim-1))
            Qb = np.dot(Q, b)

    if bc == 'reflective':
        return np.dot(la.matrix_power(T, t), cc)
    elif bc == 'open1side':
        return np.dot(la.matrix_power(T, t), cc) + np.dot(
            la.matrix_power(T, t) - np.eye(dim), Qb)
