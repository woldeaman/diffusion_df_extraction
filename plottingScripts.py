import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib as mpl
# from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import numpy as np
import sys


# plotting format for plots of minimal error for each transition layer distance
def plotMinError(distance, Error, ESTD, save=False,
                 path=None):
    if path is None:
        if sys.platform == "darwin":  # folder for linux
            path = '/Users/AmanuelWK/Desktop/'
        elif sys.platform.startswith("linux"):  # folder for mac
            path = '/home/amanuelwk/Desktop/'

    plt.figure()
    plt.gca().set_xlim([0, np.max(distance)])
    plt.errorbar(distance, Error, yerr=[np.zeros(ESTD.size), ESTD])
    plt.xlabel('Transition Layer Thickness d [µm]')
    plt.ylabel('Minimal Error [$\pm$ µM]')
    if save:
        plt.savefig(path+'minError.pdf', bbox_inches='tight')
    else:
        plt.show()


# plotting format for D and F in the same figure
def plotDF(xx, D, F, D_STD=None, F_STD=None, save=False, style='.',
           scale='linear', name='avgDF', path=None, xticks=None):
    """
    Plots D and F profiles
    """
    if path is None:
        if sys.platform == "darwin":  # folder for linux
            path = '/Users/AmanuelWK/Desktop/'
        elif sys.platform.startswith("linux"):  # folder for mac
            path = '/home/amanuelwk/Desktop/'

    plt.figure()
    plt.gca().set_xlim(left=xx[0])
    plt.gca().set_xlim(right=xx[-1])
    # plotting F
    if F_STD is None:
        plt.plot(xx, F, style+'b')
    else:
        plt.errorbar(xx, F, yerr=F_STD, fmt=style+'b')
    plt.ylabel('Free Energy [k$_{B}$T]', color='b')
    plt.xlabel('z-distance [µm]')
    plt.tick_params('y', colors='b')
    # plotting D
    plt.twinx()
    if D_STD is None:
        plt.plot(xx, D, style+'r')
    else:
        plt.errorbar(xx, D, yerr=D_STD, fmt=style+'r')
    # Make the y-axis label, ticks and tick labels match the line
    plt.gca().set_xlim(left=xx[0])
    plt.gca().set_xlim(right=xx[-1])
    plt.ylabel('Diffusivity [µm$^2$/s]', color='r')
    plt.yscale(scale)
    plt.tick_params('y', colors='r')
    plt.xlabel('Distance [µm]')
    if xticks is not None:
        plt.xticks(xticks[0], xticks[1])
    if save:
        plt.savefig(path+'%s.pdf' % name, bbox_inches='tight')
    else:
        plt.show()


# for plotting concentration profiles
def plotCon(xx, cc, ccRes, tt, plt_profiles='all',
            locs=[1, 3], colorbar=False, styles=['--', '-'],
            save=False, path=None):
    """
    Plot analyzed concentration profiles.

    plt_profiles - submit number of profiles for which comparison should be plotted,
    'all' means  all profiles will be plot.
    'locs' - determines location for the two legends.
    'colorbar' - plots colorbar instead of legends.
    'styles' - defines styles for experimental and numerical profiles.
    """
    if path is None:
        if sys.platform == "darwin":  # folder for linux
            path = '/Users/AmanuelWK/Desktop/'
        elif sys.platform.startswith("linux"):  # folder for mac
            path = '/home/amanuelwk/Desktop/'

    M = cc[0, :].size  # number of profiles

    # setting number of profiles to plot
    if plt_profiles is 'all':
        plt_nbr = np.arange(M)  # go through all profiles
    else:
        skp = int(M/plt_profiles)
        plt_nbr = np.arange(0, M, skp)

    # plotting concentration profiles
    l1s = []  # for sperate legends
    l2s = []
    # mapping profiles to colormap
    lines = np.linspace(0, 1, M)
    colors = [cm.jet(x) for x in lines]
    # Set the colormap and norm
    cmap = cm.jet
    norm = mpl.colors.Normalize(vmin=tt[0]/60, vmax=tt[-1]/60)
    scalarMap = cm.ScalarMappable(norm=norm, cmap=cmap)
    scalarMap.set_array(tt/60)  # mapping colors to time in minutes

    fig = plt.figure()
    for j in plt_nbr:
        plt.gca().set_xlim(left=xx[0])
        plt.gca().set_xlim(right=xx[-1])
        l1, = plt.plot(xx, cc[:, j], '--', color=colors[j])
        l1s.append([l1])
        if j > 0:
            # plot t=0 profile only for experiment
            # because numerical profiles are computed from this one
            l2, = plt.plot(xx, ccRes[:, j], '-', color=colors[j])
            l2s.append([l2])
    # plotting two legends, for color and linestyle
    plt.legend([l1, l2], ["Experiment", "Numerical"], loc=locs[0])
    plt.xlabel('z-distance [µm]')
    plt.ylabel('Concentration [µM]')
    # place colorbar in inset in current axis
    fig.tight_layout()
    # TODO: think about position of colorbar
    # inset = inset_axes(plt.gca(), width="40%", height="3%", loc=locs[0])
    cb1 = plt.colorbar(scalarMap, cmap=cmap, norm=norm, orientation='vertical')
    cb1.set_label('Time [min]')

    if save:
        plt.savefig(path+'profiles.pdf', bbox_inches='tight')
    else:
        plt.show()


# for printing analytical solution and transition layer thicknesses
def plotConTrans(xx, cc, ccRes, c0, tt, TransIndex, layerD, save=False,
                 path=None):

    if path is None:
        if sys.platform == "darwin":  # folder for linux
            path = '/Users/AmanuelWK/Desktop/'
        elif sys.platform.startswith("linux"):  # folder for mac
            path = '/home/amanuelwk/Desktop/'

    plt.figure()
    deltaX = abs(xx[1] - xx[0])
    M = cc[0, :].size  # number of profiles

    # ccAna = np.load('cProfiles.npy')  # change here
    # xxAna = np.linspace(0, 590.82, num=100)  # for positively charged peptide
    # xxAna = np.linspace(0, 617.91, num=100)  # for negatively charged peptide
    # indexTime = np.array([10, 500, 1000, -1])  # index for which t = 5,10,15m
    # plt.plot(xxAna, ccAna[:, indexTime[1]], 'k-.', label='Analytical')
    # plotting shaded area in transition layer and textboxes
    # conditional positions, based on distance vector
    xLeft = xx[TransIndex]-layerD/2-deltaX*1.5
    xRight = xx[TransIndex]+layerD/2-deltaX*1.5
    yMax = np.max(np.concatenate((cc, ccRes), axis=1))
    # plotting shaded region
    plt.axvspan(xLeft, xRight, color='r', lw=None, alpha=0.25)
    plt.figtext(xx[TransIndex]/np.max(xx), 0.91, 'transition layer')
    plt.text(x=xLeft-30, y=yMax, s='$D_{sol}$', va='top')
    plt.text(x=xRight+10, y=yMax, s='$D_{muc}, F_{muc}$', va='top')

    # plotting concentration profiles
    l1s = []  # for sperate legends
    l2s = []

    colors = ['r', 'm', 'c', 'b', 'y', 'k', 'g']
    for j in range(M):
        plt.gca().set_xlim(left=-deltaX)
        plt.gca().set_xlim(right=xx[-1])
        plt.xlabel('Distance [µm]')
        plt.ylabel('Concentration [µM]')
        # printing analytical solution
        # plt.plot(xxAna, ccAna[:, indexTime[j]], 'k-.')
        l1, = plt.plot(xx, cc[:, j], '--', color=colors[j],
                       label='%.2f m Experiment' % float(tt[j]/60))
        # plot computed only for t > 0, otherwise not computed
        l1s.append([l1])
        # concatenated to include constanc c0 boundary condition
        l2, = plt.plot(np.concatenate((-deltaX*np.ones(1), xx)),
                       np.concatenate((c0*np.ones(1), ccRes[:, j])),
                       '-', color=colors[j],
                       label=str(int(tt[j]/60))+'m Numerical')
        l2s.append([l2])
    # plotting two legends, for color and linestyle
    legend1 = plt.legend([l1, l2], ["Experiment", "Numerical"], loc=1)
    plt.legend([l[0] for l in l1s], ["%.2f min" % (tt[i]/60) if tt[i] % 60 != 0
                                     else "%i min" % int(tt[i]/60)
                                     for i in range(tt.size)], loc=4)
    plt.gca().add_artist(legend1)

    if save:
        plt.savefig(path+'profiles.pdf', bbox_inches='tight')
    else:
        plt.show()


# for printing c-profiles
def plotConSkin(xx, cc, ccRes, tt, locs=[0, 2], save=False, path=None,
                deltaXX=None, start=6, end=-3, xticks=None, name='profiles',
                ylabel='Concentration [µM]'):

    M = len(cc)  # number of profiles
    N = ccRes[0, :].size  # number of bins
    if deltaXX is None:
        deltaXX = np.ones(N+1)
    if path is None:
        if sys.platform == "darwin":  # folder for linux
            path = '/Users/AmanuelWK/Desktop/'
        elif sys.platform.startswith("linux"):  # folder for mac
            path = '/home/amanuelwk/Desktop/'

    # plotting concentration profiles
    l1s = []  # for sperate legends
    l2s = []
    lines = np.linspace(0, 1, M)
    colors = [cm.jet(x) for x in lines]
    # Set the colormap and norm
    cmap = cm.jet
    norm = mpl.colors.Normalize(vmin=tt[0]/60, vmax=tt[-1]/60)
    scalarMap = cm.ScalarMappable(norm=norm, cmap=cmap)
    scalarMap.set_array(tt/60)  # mapping colors to time in minutes

    fig = plt.figure()
    for j in range(M):
        if j == 0:
            l1, = plt.plot(xx, cc[j], '--', color=colors[j])
        else:
            l1, = plt.plot(xx[start:end], cc[j], '--', color=colors[j])

        # plot computed only for t > 0, otherwise not computed
        l1s.append([l1])
        if j > 0:
            # concatenated to include constanc c0 boundary condition
            l2, = plt.plot(xx, ccRes[:, j], '-', color=colors[j])
            l2s.append([l2])
    # plotting two legends, for color and linestyle
    plt.legend([l1, l2], ["Experiment", "Numerical"], loc=locs[0],
               frameon=False)
    plt.gca().set_xlim(left=xx[0])
    plt.gca().set_xlim(right=xx[-1])
    plt.xlabel('z-distance [µm]')
    plt.ylabel(ylabel)

    if xticks is not None:
        plt.xticks(xticks[0], xticks[1])

    # place colorbar in inset in current axis
    fig.tight_layout()
    # TODO: think about position of colorbar
    # inset = inset_axes(plt.gca(), width="40%", height="3%", loc=locs[0])
    cb1 = plt.colorbar(scalarMap, cmap=cmap, norm=norm, orientation='vertical')
    cb1.set_label('Time [min]')

    if save:
        plt.savefig(path+'%s.pdf' % name, bbox_inches='tight')
    else:
        plt.show()


# for printing c-profiles
def plotBlock(xx, cc, ccRes, tt, t_sig=None, locs=[0, 2], save=False, path=None,
              plt_profiles='all', deltaXX=None, start=6, end=-3, xticks=None,
              name='profiles', ylabel='Concentration [µM]'):

    M = len(cc)  # number of profiles
    N = ccRes[0, :].size  # number of bins
    if deltaXX is None:
        deltaXX = np.ones(N+1)
    if path is None:
        if sys.platform == "darwin":  # folder for linux
            path = '/Users/AmanuelWK/Desktop/'
        elif sys.platform.startswith("linux"):  # folder for mac
            path = '/home/amanuelwk/Desktop/'

    # setting number of profiles to plot
    if plt_profiles is 'all' or M < plt_profiles:
        plt_nbr = np.arange(M)  # go through all profiles
    else:
        skp = int(M/plt_profiles)
        plt_nbr = np.arange(0, M, skp)

    # plotting concentration profiles
    l1s = []  # for sperate legends
    l2s = []
    lines = np.linspace(0, 1, M)
    colors = [cm.jet(x) for x in lines]
    # Set the colormap and norm
    cmap = cm.jet
    norm = mpl.colors.Normalize(vmin=tt[0]/60, vmax=tt[-1]/60)
    scalarMap = cm.ScalarMappable(norm=norm, cmap=cmap)
    scalarMap.set_array(tt/60)  # mapping colors to time in minutes

    fig = plt.figure()
    for j in plt_nbr:
        if j == 0:
            l1, = plt.plot(xx, cc[j], '--', color=colors[j])
        else:
            l1, = plt.plot(xx[start:end], cc[j], '--', color=colors[j])

        # plot computed only for t > 0, otherwise not computed
        l1s.append([l1])
        if j > 0:
            # concatenated to include constanc c0 boundary condition
            l2, = plt.plot(xx, ccRes[:, j], '-', color=colors[j])
            l2s.append([l2])
    # add line indicating fitted transition
    if t_sig is not None:
        plt.axvline(t_sig, c='k', ls=':')
    # plotting two legends, for color and linestyle
    plt.legend([l1, l2], ["Experiment", "Numerical"], loc=locs[0],
               frameon=False)
    plt.gca().set_xlim(left=xx[0])
    plt.gca().set_xlim(right=xx[-1])
    plt.xlabel('z-distance [µm]')
    plt.ylabel(ylabel)

    if xticks is not None:
        plt.xticks(xticks[0], xticks[1])

    # place colorbar in inset in current axis
    fig.tight_layout()
    # TODO: think about position of colorbar
    # inset = inset_axes(plt.gca(), width="40%", height="3%", loc=locs[0])
    cb1 = plt.colorbar(scalarMap, cmap=cmap, norm=norm, orientation='vertical')
    cb1.set_label('Time [min]')

    if save:
        plt.savefig(path+'%s.pdf' % name, bbox_inches='tight')
    else:
        plt.show()
