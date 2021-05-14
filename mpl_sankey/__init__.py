import numpy as np
import pandas as pd

import matplotlib.patches as patches
from matplotlib import pyplot as plt
from matplotlib.path import Path

from matplotlib.collections import PatchCollection

__version__ = '0.1.0'

# Share of total width left empty (same in each phase):
GAPS = .1

# Location of bounds (if a phase is drawn from 0 to 1).
LEFT = .1
RIGHT = .9

def _draw_flow(start, end, width, left, right, color):
    """
    Draw a single flow, from "left" to "right", with y going from "start" to
    "end", width "width" and color "color".
    """
    space = right - left

    verts = np.zeros(shape=(9, 2), dtype='float')
    verts[:,1] = start
    verts[2:6,1] = end
    verts[4:,1] += width

    verts[:,0] = left
    verts[1:7,0] += space / 2
    verts[3:5,0] += space / 2

    codes = [Path.MOVETO,
             Path.CURVE4,
             Path.CURVE4,
             Path.CURVE4,
             Path.LINETO,
             Path.CURVE4,
             Path.CURVE4,
             Path.CURVE4,
             Path.CLOSEPOLY
             ]

    path = Path(verts, codes)

    patch = patches.PathPatch(path, facecolor=color, lw=0, alpha=.4)
    plt.gca().add_patch(patch)


def _node_text(start, size, node_sizes):
    if node_sizes is True:
        node_sizes = '{label} ({size})'
    # Allow for formatting specs:
    elif '{label' not in node_sizes:
        size = node_sizes.format(size)
        node_sizes = '{label} {size}'
    return node_sizes.format(label=start, size=size)

def sankey(data, cmap=plt.get_cmap('jet_r'), flows_color=None,
           labels_color='black', titles_color='black', labels_size=20,
           titles_size=20, node_sizes=False, sort_flows_by_nodes=False):
    """
    Draw a sankey diagram.

    Parameters
    ----------

    data : pandas DataFrame, numpy 2-D array, or list of equal length lists
        The data to be represented. Each row describes a flow from the
        beginning to the end. The first column must be numeric and represents
        the (positive) width of the flow. Each other column describes the label
        of the flow at a given stage.
        At least two stages (start, end) are needed to produce a meaningful
        diagram, hence "data" needs to hold three or more columns.

    cmap : colormap, default: 'jet_r'
        Used to assign a color to each block (and to its outgoing flows, unless
        the "flows_color" argument is used).

    flows_color : color, default: None
        Draw all flows of a same color, rather than of the color of each flow's
        starting block.

    labels_color : color or None, default: 'black'
        Color to be used for labels, None to hide them.

    titles_color : color or None, default: 'black'
        Color to be used for titles, None to hide them.

    labels_size : int, default: 20
        Font size for node labels.

    titles_size : int, default: 20
        Font size for titles.

    node_sizes : Boolean or string, default: False
        Whether to show node sizes close to node labels.
        A format string with named placeholders can be passed to control the
        formatting, as in '{label}\n({size}\%)': if only a non-named
        placeholder is present, as in '- {}', the label is prepended separated
        by a space.
        Passing True is equivalent to passing '{label} ({size})' (or '({})').

    sort_flows_by_nodes : Boolean, default: False
        Whether flows from/to a given node should be sorted based on the
        position of the starting and ending nodes - the default is to sort them
        based on their position in the passed data.
    """

    data = pd.DataFrame(data)

    # One column is for the weights, the remaining n+1 limits define n phases:
    phases = data.shape[1] - 2


    all_labels = data.iloc[:, 1:].stack().unique()

    colors = dict(zip(all_labels,
                      cmap(np.arange(0, len(all_labels))/len(all_labels))))

    # Actual scale from flow/block width to drawn width:
    factor = (1 - GAPS) / data.iloc[:, 0].sum()

    # The first column always contains weights:
    var_weight = data.columns[0]
    for phase in range(phases):
        # ... while the columns containing variables shift at each phase:
        var_left = data.columns[phase+1]
        var_right = data.columns[phase+2]

        # Compute total weight for each label:
        l_sizes = data.groupby(var_left)[var_weight].sum()
        r_sizes = data.groupby(var_right)[var_weight].sum()

        # Drop empty cats (https://github.com/pandas-dev/pandas/issues/8559):
        l_sizes, r_sizes = (s.pipe(lambda x : x[x>0]) for s in (l_sizes, r_sizes))

        # Map weights to drawn sizes:
        l_shares = l_sizes * factor
        r_shares = r_sizes * factor

        # Distribute gap space among gaps:
        l_gaps = GAPS / max((len(l_shares) - 1), 1)
        r_gaps = GAPS / max((len(r_shares) - 1), 1)

        # Compute blocks positions, including gaps:
        l_starts = (l_shares + l_gaps).cumsum().shift().fillna(0)
        r_starts = (r_shares + r_gaps).cumsum().shift().fillna(0)

        for (pos, l, w, starts, shares) in (
                           ('right', phase+RIGHT, 1-RIGHT, r_starts, r_shares),
                           ('left', phase, LEFT, l_starts, l_shares)):
            if pos == 'right' and phase < phases - 1:
                # Center text for full width:
                text_x = l + w
            elif pos == 'left' and phase:
                # Do not draw text - it will be drawn by next phase:
                text_x = -1
            else:
                # Center text for half width (first or last extreme):
                text_x = l + 0.5*w

            for idx, start in enumerate(starts.index):
                # Draw blocks:
                bottom = starts.loc[start]
                p = patches.Rectangle((l, 1 - bottom - shares.loc[start]),
                                      w, shares.loc[start],
                                      fill=False, clip_on=False)
                pc = PatchCollection([p], facecolor=colors[start], alpha=.5)
                plt.gca().add_collection(pc)

                # Draw labels text:
                if text_x != -1 and labels_color is not None:
                    if node_sizes is not False:
                        if phase == 0 and pos == 'left':
                            size = l_sizes.iloc[idx]
                        else:
                            size = r_sizes.iloc[idx]
                        text = _node_text(start, size, node_sizes)
                    else:
                        text = f"{start}"

                    plt.gca().text(text_x,
                                   1 - bottom - 0.5 * shares.loc[start],
                                   text,
                                   horizontalalignment='center',
                                   verticalalignment='center',
                                   fontsize=labels_size, color=labels_color)

            # Draw titles:
            if text_x != -1 and titles_color is not None:
                plt.gca().text(text_x,
                               1,
                               var_left if pos == 'left' else var_right,
                               horizontalalignment='center',
                               verticalalignment='bottom',
                               fontsize=titles_size, color=titles_color)

        # Draw flows:
        flows_list = data[[var_weight,
                           var_left,
                           var_right]]
        if sort_flows_by_nodes:
            # Avoid (probably unjustified - we're working on entire columns)
            # SettingWithCopyWarning:
            flows_list = flows_list.copy()
            for a_var, starts in (var_left, l_starts), (var_right, r_starts):
                dtype = pd.CategoricalDtype(categories=starts.index,
                                            ordered=True)
                flows_list[a_var] = flows_list[a_var].astype(dtype)
            flows_list = flows_list.sort_values([var_left, var_right])

        for idx, (weight, start, end) in flows_list.iterrows():
            width = weight * factor
            l = l_starts.loc[start]
            r = r_starts.loc[end]
            _draw_flow(1 - l_starts.loc[start] - width,
                       1 - r_starts.loc[end] - width, width,
                       phase + LEFT, phase + RIGHT,
                       flows_color or colors[start])
            l_starts.loc[start] += width
            r_starts.loc[end] += width

    plt.xlim(0, phases)
    plt.axis('off')
