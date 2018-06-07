# -*- coding: utf-8 -*-
"""Fitting DF while also rescaling profiles to match literature DSol."""
# use this for matplotlib on the cluster
# import matplotlib
# matplotlib.use('Agg')
import numpy as np
import time
import inputOutput as io
import FPModel as fp
import functools as ft
import scipy.optimize as op
import scipy.special as sp
import plottingScripts as ps
import xlsxwriter as xl
import os
import sys
startTime = time.time()  # start measuring run time


def save_data(xx, cc_scaled_best, cc_scaled_means, ccRes, tt, errors, t_best,
              best_params, avg_params, std_params, D_mean, D_best, F_mean, F_best,
              D_std, F_std, c_bulk_mean, c_bulk_std, c_bulk_best, top_percent,
              savePath, x_tot=1780):
    """Make plots and save analyzed data."""
    # header for txt file in which concentration profiles will be saved
    header_cons = ''
    for i, t in enumerate(tt):
        header_cons += ('column%i: c-profile [micro_M] for t_%i = %i min\n'
                        % (i+2, i, int(t/60)))
    # saving numerical profiles
    np.savetxt(savePath+'concentrationRes.txt', ccRes, delimiter=',',
               header='Numerically computed concentration profiles\n'+header_cons)
    # saving averaged DF
    np.savetxt(savePath+'DF_avg.txt', np.c_[D_mean, D_std, F_mean-F_mean[0], F_std],
               delimiter=',',
               header=('Diffusivity and free energy profiles from analysis\n'
                       'cloumn1: average diffusivity [micro_m^2/s]\n'
                       'cloumn2: stdev of diffusivity [+/- micro_m^2/s]\n'
                       'cloumn3: average free energy [k_BT]\n'
                       'cloumn4: stdev of free energy [+/- k_BT]'))
    # saving best DF
    np.savetxt(savePath+'DF_best.txt', np.c_[D_best, F_best-F_best[0]],
               delimiter=',',
               header=('Diffusivity and free energy profiles with lowest '
                       'error from analysis\n'
                       'cloumn1: diffusivity [micro_m^2/s]\n'
                       'cloumn2: free energy [k_BT]'))

    # saving Error of top 1% of runs
    np.savetxt(savePath+'minError.txt', errors, delimiter=',',
               header=('Minimal error for top %.2f %% runs.' % (top_percent*100)))
    # saving fitted average bulk concentrations
    np.savetxt(savePath+'c_bulk_avg.txt', np.c_[c_bulk_mean, c_bulk_std],
               delimiter=',',
               header=('Fitted bulk concentration, averaged over all runs.\n'
                       'column1: average\n'
                       'column2: standart deviation\n'))
    np.savetxt(savePath+'c_bulk_best.txt', c_bulk_best, delimiter=',',
               header=('Fitted bulk concentration for best run.'))

    # reconstruct original x-vector
    length_bulk, dx = (x_tot - np.max(xx)), (xx[1] - xx[0])
    # for labeling the x-axis correctly
    xx_dummy = np.arange(ccRes[:, 0].size)
    xlabels = [[xx_dummy[0]]+[x for x in xx_dummy[6::5]],
               [-length_bulk]+[i*5*dx for i in range(xx_dummy[6::5].size)]]
    # plotting profiles
    t_newX_coords = int(t_best/dx + 6)
    ps.plotBlock(xx_dummy, cc_scaled_best, ccRes, tt, t_newX_coords, locs=[1, 3], save=True,
                 path=savePath, plt_profiles='all', end=None, xticks=xlabels)
    # plotting averaged D and F
    ps.plotDF(xx_dummy, D_mean, F_mean-F_mean[0], D_STD=D_std, F_STD=F_std, save=True,
              style='.--', path=savePath, xticks=xlabels)
    ps.plotDF(xx_dummy, D_best, F_best-F_best[0], save=True, style='.--', name='bestDF',
              path=savePath, xticks=xlabels)

    # saving data to excel spreadsheet
    workbook = xl.Workbook(savePath+'results.xlsx')
    worksheet = workbook.add_worksheet()
    bold = workbook.add_format({'bold': True})
    # writing headers
    worksheet.write('A1', 'D_sol_avg [µm^2/s]', bold)
    worksheet.write('C1', 'D_sol_best [µm^2/s]', bold)
    worksheet.write('A2', 'D_muc_avg [µm^2/s]', bold)
    worksheet.write('C2', 'D_muc_best [µm^2/s]', bold)
    worksheet.write('A3', 'F_muc_avg [kT]', bold)
    worksheet.write('C3', 'F_muc_best [kT]', bold)
    worksheet.write('A4', 't_avg [µm]', bold)
    worksheet.write('C4', 't_best [µm]', bold)
    worksheet.write('A5', 'd_avg [µm]', bold)
    worksheet.write('C5', 'd_best [µm]', bold)
    worksheet.write('A8', 'min Err. [+/- µM]', bold)

    # gather original parameters
    means = [avg_params[0], avg_params[1], (avg_params[3]-avg_params[2]),
             avg_params[4], avg_params[5]]
    stdevs = [std_params[0], std_params[1], (std_params[3]+std_params[2]),
              std_params[4], std_params[5]]
    bests = [best_params[0], best_params[1], (best_params[3]-std_params[2]),
             best_params[4], best_params[5]]

    # writing entries, storing original parameters for sigmoidal curves
    for i, data in enumerate(zip(means, stdevs)):
        worksheet.write('B%i' % (i+1), '%.2f +/- %.2f' % (data[0], data[1]))
    for i, best in enumerate(bests):
        worksheet.write('D%i' % (i+1), '%.2f' % best)
    worksheet.write('B8', '%.2f' % np.min(errors))  # write also error
    # adjusting cell widths
    worksheet.set_column(0, 15, len('D_sol_best [µm^2/s]'))
    workbook.close()


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


def average_data(result, xx, cc, top_percent=1):
    """Gather and average data from all optimization runs."""
    # number if top x% of the runs
    nbr = np.ceil(top_percent*len(result)).astype(int)

    # used to later compute normalized error
    n_profiles = len(cc)  # number of profiles
    bins = cc[1].size  # number of bins
    combis = n_profiles-1  # number of combinations for different c-profiles

    # loading error values, factor two, because of cost function definition
    error = [np.sqrt(2*res.cost / (bins*combis)) for res in result]
    indices = np.argsort(error)  # for sorting according to error
    error_sorted = [error[idx] for idx in indices[:nbr]]

    # gathering mean for all parameters
    averages = np.mean([result[idx].x for idx in indices[:nbr]], axis=0)
    stdevs = np.std([result[idx].x for idx in indices[:nbr]], axis=0)
    best_results = result[indices[0]].x

    # splitting up parameters to compute D, F profiles
    D_mean, F_mean, t_mean, d_mean = averages[:2], averages[2:4], averages[4], averages[5]
    D_std, F_std = stdevs[:2], stdevs[2:4]
    D_best, F_best, t_best, d_best = best_results[:2], best_results[2:4], best_results[4], best_results[5]

    # post processing D, F profiles
    D_mean_pre = np.array([fp.sigmoidalDF(D_mean, t_mean, d_mean, x) for x in xx])
    F_mean_pre = np.array([fp.sigmoidalDF(F_mean, t_mean, d_mean, x) for x in xx])
    D_best = np.array([fp.sigmoidalDF(D_best, t_best, d_best, x) for x in xx])
    F_best = np.array([fp.sigmoidalDF(F_best, t_best, d_best, x) for x in xx])
    segments = np.concatenate((np.zeros(6), np.arange(xx.size))).astype(int)
    D_mean, F_mean = fp.computeDF(D_mean_pre, F_mean_pre, shape=segments)
    D_best, F_best = fp.computeDF(D_best, F_best, shape=segments)

    # computing errors using error propagation for Dsol, Dmuc or Fsol, Fmuc
    # contributions of t, d neglected for now...
    DSTD_pre = np.array([np.sqrt(((0.5 - sp.erf((x-t_mean)/(np.sqrt(2)*d_mean))/2) *
                                  D_std[0])**2 + ((0.5 + sp.erf((x-t_mean)/(np.sqrt(2)*d_mean))/2) *
                                                  D_std[1])**2) for x in xx])
    FSTD_pre = np.array([np.sqrt(((0.5 - sp.erf((x-t_mean)/(np.sqrt(2)*d_mean))/2) *
                                  F_std[0])**2 + ((0.5 + sp.erf((x-t_mean)/(np.sqrt(2)*d_mean))/2) *
                                                  F_std[1])**2) for x in xx])
    # now keeping fixed stdev of D, F in first 6 bins
    DSTD, FSTD = fp.computeDF(DSTD_pre, FSTD_pre, shape=segments)

    return (best_results, averages, stdevs, F_best, D_best, t_best, d_best,
            F_mean, D_mean, t_mean, d_mean, FSTD, DSTD, error_sorted)


def cross_checking(W, cc, tt, dxx_width, dxx_dist):
    """Check numerical model for conservation of concentration."""
    # Column sum does not vanish anymore for variable binning, but equal
    # positive and negative terms appear at binning transition --> total sum vanishes
    if abs(np.sum((np.sum(W, 0)))) > 0.01:
        print("WMatrix total sum does not vanish!\nMax is:",
              np.max(np.sum(W, 0)), '\nFor each column:\n', np.sum(W, 0))
        sys.exit()

    # testing conservation of concentration
    con = np.sum(cc[0]*dxx_width)
    # compute profiles from c0 and do the same conservation check
    ccComp = [fp.calcC(cc[0], t=t, W=W) for t in tt]

    if np.any(np.array([abs(np.sum(c*dxx_width)-con)
                        for c in ccComp]) > 0.01*con):
        print('Error: Computed concentration '
              'is not conserved in profiles: \n',
              np.nonzero(np.array([abs(np.sum(c*dxx_width)-con)
                                   for c in ccComp]) > 0.01*con))
        print([np.sum(c*dxx_width) for c in ccComp], '\n')
        print('concentration:\n', con)
        print('WMatrix Size:\n', W.shape)
        print('WMatrix Row Sum:\n', np.sum(W, 0))
        print('WMatrix 2Sum:\n', np.sum(np.sum(W, 0)))
        sys.exit()


def initialize_optimization(runs, params, n_profiles, xx, DMax=1000, FMax=20):
    """Set up bounds and start values for non-linear fit."""
    # gather discretization
    dx = xx[1] - xx[0]

    # set D, F bounds
    bnds_d_up = np.ones(params)*DMax
    bnds_f_up = np.ones(params)*FMax
    bnds_d_low = np.zeros(params)
    bnds_f_low = np.ones(params)*(-FMax)
    # bounds for interface position and layer thickness zero and max x position
    bnds_td_up = np.ones(2)*np.max(xx)
    bnds_td_low = np.zeros(2)
    # bounds for scaling factors for each profile
    bnds_scale_up = np.ones(n_profiles)*100  # setting this beetwen 0-100
    bnds_scale_low = np.zeros(n_profiles)
    # setting start values
    f_init = np.zeros(params)
    d_init = (np.random.rand(runs, params)*DMax)  # randomly choose D
    td_init = np.array([50, dx*3])  # order is [t, d], set t initially to 50 µm
    scale_init = np.ones(n_profiles)  # initially no scaling
    # storing everything together
    bnds = (np.concatenate((bnds_d_low, bnds_f_low, bnds_td_low, bnds_scale_low)),
            np.concatenate((bnds_d_up, bnds_f_up, bnds_td_up, bnds_scale_up)))
    inits = [np.concatenate((d, f_init, td_init, scale_init)) for d in d_init]

    return bnds, inits


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


def analysis(result, xx, cc, tt, dxx_dist, dxx_width, per=1):
    """Analyze results from optimization runs."""
    # create new folder to save results in
    savePath = os.path.join(os.getcwd(), 'results/')
    if not os.path.exists(savePath):
        os.makedirs(savePath)

    # gather data from results objects
    (best_results, averages, stdevs, F_best, D_best, t_best, d_best,
     F_mean, D_mean, t_mean, d_mean, F_std, D_std, error) = average_data(result, xx, cc, per)
    # fitted values for re-scaling concentration profiles
    scalings_mean, scalings_std, scalings_best = averages[6:], stdevs[6:], best_results[6:]

    # computing rate matrix from best results
    W = fp.WMatrixVar(D_best, F_best, start=4, end=None, deltaXX=dxx_dist, con=True)
    # computing concentration profiles
    ccRes = np.array([fp.calcC(cc[0], t, W=W) for t in tt]).T

    # compute re-scaled concentration profiles
    cc_best, cc_mean = [cc[0]], [cc[0]]
    for c_b, c_m, c_og in zip(scalings_best, scalings_mean, cc[1:]):
        cc_best.append(c_og*c_b)
        cc_mean.append(c_og*c_m)
    # compute fitted average bulk concentration
    c_bulk_best = compute_avg_c_bulk(cc_best, xx, dxx_width)
    c_bulk_mean = compute_avg_c_bulk(cc_mean, xx, dxx_width)
    # error from gauß error propagation
    c_bulk_std = compute_c_bulk_stdev(cc, scalings_std, xx)

    save_data(xx, cc_best, cc_mean, ccRes, tt, error, t_best,
              best_results, averages, stdevs, D_mean, D_best, F_mean, F_best,
              D_std, F_std, c_bulk_mean, c_bulk_std, c_bulk_best, per, savePath)


def resFun(parameters, xx, cc, tt, dxx_dist, dxx_width, check=False):
    """Compute residuals for non-linear optimization."""
    # separate fit parameters accordingly
    d = parameters[:2]
    f = parameters[2:4]
    t_sig, d_sig = parameters[4], parameters[5]
    scalings = parameters[6:]

    # compute sigmoidal D, F profiles
    D = np.array([fp.sigmoidalDF(d, t_sig, d_sig, x) for x in xx])
    F = np.array([fp.sigmoidalDF(f, t_sig, d_sig, x) for x in xx])
    # now keeping fixed D, F in first 6 bins throughout bulk
    segments = np.concatenate((np.zeros(6), np.arange(D.size))).astype(int)
    D, F = fp.computeDF(D, F, shape=segments)
    # computing WMatrix, start smaller than 6, because D, F is const. only there
    W = fp.WMatrixVar(D, F, start=4, end=None, deltaXX=dxx_dist, con=True)

    if check:  # checking for conservation of concentration
        cross_checking(W, cc, tt, dxx_width, dxx_dist)

    # compute numerical profiles
    cc_theo = [fp.calcC(cc[0], t=t, W=W) for t in tt]
    # re-scale concentration profiles with fit parameters
    cc_norm = [c*norm for c, norm in zip(cc[1:], scalings)]

    # compute residual vector and reshape into one long vector
    RR = np.array([c_exp - c_num[6:] for c_exp, c_num in zip(cc_norm, cc_theo)]).T
    RRn = RR.reshape(RR.size)  # residual vector contains all deviations

    return RRn


def optimization(init, bnds, xx, cc, tt, dxx_dist, dxx_width, verbosity=0):
    """Run one iteration of the non-linear optimization."""
    # reduce residual function to one argument in order to work with algorithm
    optimize = ft.partial(resFun, xx=xx, cc=cc, tt=tt, dxx_dist=dxx_dist,
                          dxx_width=dxx_width)

    # running freely with standart termination conditions
    result = op.least_squares(optimize, init, bounds=bnds, verbose=verbosity)

    return result


def main():
    """Set up optimization and run it."""
    # reading input and setting up analysis
    verbosity, runs, ana, xx, cc, tt = io.startUp_slim()
    n_profiles = cc[0, :].size-1  # number of profiles without c(t=0)

    dxx_dist, dxx_width = discretization_Block(xx)  # get variable discretization
    cc = build_zero_profile(cc)  # build t=0 profile
    # set up optimization
    params = 2  # only fit here Dsol, Fsol and Dmuc, Fmuc
    bnds, inits = initialize_optimization(runs, params, n_profiles, xx)

    if ana:  # make only analysis
        print('\nDoing analysis only.')
        res = np.load('result.npy')
        print('Overall %i runs have been performed.' % res.size)
        analysis(np.array(res), xx, cc, tt, dxx_dist, dxx_width, per=1)
        print('\nPlots have been made and data was extraced and saved.')
        sys.exit()

    results = []  # saving optimization results
    for i, init in enumerate(inits):  # looping through all different start values
        print('\nNow at run %i out of %i...\n' % (i+1, len(inits)))
        try:
            results.append(optimization(init, bnds, xx, cc, tt, dxx_dist,
                                        dxx_width, verbosity))
            np.save('result.npy', np.array(results))
        except KeyboardInterrupt:
            print('\n\nScript has been terminated.\nData will now be analyzed...')
            break

    analysis(np.array(results), xx, cc, tt, dxx_dist, dxx_width, per=1)

    return runs  # returns number of runs in order to compute average time per run


if __name__ == "__main__":
    runs = main()
    print("\nFinished optimization!"
          "\nTotal execution time was %.2f minutes"
          "\nAverage time per run was %.2f minutes"
          % (((time.time() - startTime)/60),
             (time.time() - startTime)/(60*runs)))