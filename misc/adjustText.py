import io
import multiprocessing as mp
import sys
import warnings
from pathlib import Path
from timeit import default_timer as timer

import matplotlib
import numpy as np
import pandas as pd
import scipy.spatial.distance
from loguru import logger
from matplotlib import pyplot as plt
from matplotlib.patches import FancyArrowPatch
from matplotlib.path import get_path_collection_extents

try:
    from matplotlib.backend_bases import _get_renderer as matplot_get_renderer
except ImportError:
    matplot_get_renderer = None

WORKERS = 8


def adjust_text(texts, x=None, y=None, objects=None, avoid_self=True, force_text: tuple[float, float]=(0.1, 0.2), force_static: tuple[float, float]=(0.1, 0.2), force_pull: tuple[float, float]=(0.01, 0.01), force_explode: tuple[float, float]=(0.01, 0.02), expand: tuple[float, float]=(1.05, 1.1), explode_radius='auto', ensure_inside_axes=True, expand_axes=False, only_move={'text': 'xy', 'static': 'xy', 'explode': 'xy', 'pull': 'xy'}, ax=None, min_arrow_len=5, time_lim: float | None=None, iter_lim: int | None=None, *args, **kwargs):
    if not texts:
        return
    if ax is None:
        ax = plt.gca()
    try:
        ax.figure.draw_without_rendering()
    except AttributeError:
        logging.warn('Looks like you are using an old matplotlib version.\n               In some cases adjust_text might fail, if possible update\n               matplotlib to version >=3.5.0')
        ax.figure.canvas.draw()
    try:
        transform = texts[0].get_transform()
    except IndexError:
        logging.warn('Something wrong with the texts. Did you pass a list of matplotlib text objects?')
        return
    if time_lim is None and iter_lim is None:
        time_lim = 0.5
    elif time_lim is not None and iter_lim is not None:
        logging.warn('Both time_lim and iter_lim are set, faster will be used')
    start_time = timer()
    orig_xy = [text.get_unitless_position() for text in texts]
    orig_xy_disp_coord = transform.transform(orig_xy)
    coords = get_2d_coordinates(texts)
    if isinstance(only_move, str):
        only_move = {'text': only_move, 'static': only_move, 'explode': only_move, 'pull': only_move}
    if x is not None and y is not None:
        point_coords = transform.transform(np.vstack([x, y]).T)
    else:
        point_coords = np.empty((0, 2))
    if avoid_self:
        point_coords = np.vstack([point_coords, np.hstack([np.mean(coords[:, :2], axis=1)[:, np.newaxis], np.mean(coords[:, 2:], axis=1)[:, np.newaxis]])])
    if objects is None:
        obj_coords = np.empty((0, 4))
    else:
        obj_coords = get_2d_coordinates(objects)
    static_coords = np.vstack([point_coords[:, [0, 0, 1, 1]], obj_coords])
    if explode_radius == 'auto':
        explode_radius = max((coords[:, 1] - coords[:, 0]).max(), (coords[:, 3] - coords[:, 2]).max())
    if explode_radius > 0 and np.all(np.asarray(force_explode) > 0):
        explode_x, explode_y = explode(coords, static_coords, explode_radius)
        if 'x' not in only_move['explode']:
            explode_x = np.zeros_like(explode_x)
        if 'y' not in only_move['explode']:
            explode_y = np.zeros_like(explode_y)
        coords = apply_shifts(coords, -explode_x * force_explode[0], -explode_y * force_explode[1])
    error = np.Inf
    if expand_axes:
        expand_axes_to_fit(coords, ax, transform)
    if ensure_inside_axes:
        ax_bbox = ax.patch.get_extents()
        ax_bbox = (ax_bbox.xmin, ax_bbox.xmax, ax_bbox.ymin, ax_bbox.ymax)
    else:
        ax_bbox = False
    i = 0
    while error > 0:
        coords, error = iterate(coords, orig_xy_disp_coord, static_coords, force_text=force_text, force_static=force_static, force_pull=force_pull, expand=expand, bbox_to_contain=ax_bbox, only_move=only_move)
        i += 1
        if time_lim is not None and timer() - start_time > time_lim:
            break
        if iter_lim is not None and i == iter_lim:
            break
    xdists = np.min(np.abs(np.subtract(coords[:, :2], orig_xy_disp_coord[:, 0][:, np.newaxis])), axis=1)
    ydists = np.min(np.abs(np.subtract(coords[:, 2:], orig_xy_disp_coord[:, 1][:, np.newaxis])), axis=1)
    display_dists = np.max(np.vstack([xdists, ydists]), axis=0)
    connections = np.hstack([np.mean(coords[:, :2], axis=1)[:, np.newaxis], np.mean(coords[:, 2:], axis=1)[:, np.newaxis], orig_xy_disp_coord])
    transformed_connections = np.empty_like(connections)
    transformed_connections[:, :2] = transform.inverted().transform(connections[:, :2])
    transformed_connections[:, 2:] = transform.inverted().transform(connections[:, 2:])
    if 'arrowprops' in kwargs:
        ap = kwargs.pop('arrowprops')
    else:
        ap = {}
    for i, text in enumerate(texts):
        text_mid = transformed_connections[i, :2]
        target = transformed_connections[i, 2:]
        text.set_verticalalignment('center')
        text.set_horizontalalignment('center')
        text.set_position(text_mid)
        if ap and display_dists[i] >= min_arrow_len:
            arrowpatch = FancyArrowPatch(*args, posA=text_mid, posB=target, patchA=text, **kwargs, **ap)
            ax.add_patch(arrowpatch)


def apply_shifts(coords, shifts_x, shifts_y):
    coords[:, :2] = np.subtract(coords[:, :2], shifts_x[:, np.newaxis])
    coords[:, 2:] = np.subtract(coords[:, 2:], shifts_y[:, np.newaxis])
    return coords


def arange_multi(starts, stops=None, lengths=None):
    if (stops is None) == (lengths is None):
        raise ValueError('Either stops or lengths must be provided!')
    if lengths is None:
        lengths = stops - starts
    if np.isscalar(starts):
        starts = np.full(len(stops), starts)
    cat_start = np.repeat(starts, lengths)
    cat_counter = np.arange(lengths.sum()) - np.repeat(lengths.cumsum() - lengths, lengths)
    cat_range = cat_start + cat_counter
    return cat_range


def expand_axes_to_fit(coords, ax, transform):
    max_x, max_y = np.max(transform.transform(coords[:, [1, 3]]), axis=0)
    min_x, min_y = np.min(transform.transform(coords[:, [1, 3]]), axis=0)
    if min_x < ax.get_xlim()[0]:
        ax.set_xlim(xmin=min_x)
    if min_y < ax.get_ylim()[0]:
        ax.set_ylim(ymin=min_y)
    if max_x < ax.get_xlim()[1]:
        ax.set_xlim(xmin=max_x)
    if max_y < ax.get_ylim()[1]:
        ax.set_ylim(ymin=max_y)


def expand_coords(coords, x_frac, y_frac):
    mid_x = np.mean(coords[:, :2], axis=1)
    mid_y = np.mean(coords[:, 2:], axis=1)
    x = np.subtract(coords[:, :2], mid_x[:, np.newaxis]) * x_frac + mid_x[:, np.newaxis]
    y = np.subtract(coords[:, 2:], mid_y[:, np.newaxis]) * y_frac + mid_y[:, np.newaxis]
    return np.hstack([x, y])


def explode(coords, static_coords, r=None):
    N = coords.shape[0]
    x = coords[:, [0, 1]].mean(axis=1)
    y = coords[:, [2, 3]].mean(axis=1)
    points = np.vstack([x, y]).T
    if static_coords.shape[0] > 0:
        static_x = np.mean(static_coords[:, [0, 1]], axis=1)
        static_y = np.mean(static_coords[:, [2, 3]], axis=1)
        static_centers = np.vstack([static_x, static_y]).T
        points = np.vstack([points, static_centers])
    tree = scipy.spatial.KDTree(points)
    pairs = tree.query_pairs(r, output_type='ndarray')
    pairs = pairs[pairs[:, 0] < N]
    pairs = pairs[pairs[:, 0] != pairs[:, 1]]
    diff = points[pairs[:, 0]] - points[pairs[:, 1]]
    xshifts = np.bincount(pairs[:, 0], diff[:, 0], minlength=N)
    yshifts = np.bincount(pairs[:, 0], diff[:, 1], minlength=N)
    return (xshifts, yshifts)


def force_into_bbox(coords, bbox):
    xmin, xmax, ymin, ymax = bbox
    dx, dy = (np.zeros(coords.shape[0]), np.zeros(coords.shape[0]))
    if np.any((coords[:, 0] < xmin) & (coords[:, 1] > xmax)):
        logging.warn("Some labels are too long, can't fit inside the X axis")
    if np.any((coords[:, 2] < ymin) & (coords[:, 3] > ymax)):
        logging.warn("Some labels are too toll, can't fit inside the Y axis")
    dx[coords[:, 0] < xmin] = (xmin - coords[:, 0])[coords[:, 0] < xmin]
    dx[coords[:, 1] > xmax] = (xmax - coords[:, 1])[coords[:, 1] > xmax]
    dy[coords[:, 2] < ymin] = (ymin - coords[:, 2])[coords[:, 2] < ymin]
    dy[coords[:, 3] > ymax] = (ymax - coords[:, 3])[coords[:, 3] > ymax]
    return apply_shifts(coords, -dx, -dy)


def get_2d_coordinates(objs):
    try:
        ax = objs[0].axes
    except:
        ax = objs.axes
    bboxes = get_bboxes(objs, get_renderer(ax.get_figure()), (1.0, 1.0), ax)
    xs = [(ax.convert_xunits(bbox.xmin), ax.convert_yunits(bbox.xmax)) for bbox in bboxes]
    ys = [(ax.convert_xunits(bbox.ymin), ax.convert_yunits(bbox.ymax)) for bbox in bboxes]
    coords = np.hstack([np.array(xs), np.array(ys)])
    return coords


def get_bboxes(objs, r=None, expand=(1, 1), ax=None, transform=None):
    ax = ax or plt.gca()
    r = r or get_renderer(ax.get_figure())
    try:
        return [i.get_window_extent(r).expanded(*expand) for i in objs]
    except (AttributeError, TypeError):
        try:
            if all([isinstance(obj, matplotlib.transforms.BboxBase) for obj in objs]):
                return objs
            else:
                raise ValueError('Something is wrong')
        except TypeError:
            return get_bboxes_pathcollection(objs, ax)


def get_bboxes_pathcollection(sc, ax):
    transform = sc.get_transform()
    transOffset = sc.get_offset_transform()
    offsets = sc._offsets
    paths = sc.get_paths()
    transforms = sc.get_transforms()
    if not transform.is_affine:
        paths = [transform.transform_path_non_affine(p) for p in paths]
        transform = transform.get_affine()
    if not transOffset.is_affine:
        offsets = transOffset.transform_non_affine(offsets)
        transOffset = transOffset.get_affine()
    if isinstance(offsets, np.ma.MaskedArray):
        offsets = offsets.filled(np.nan)
    bboxes = []
    if len(paths) and len(offsets):
        if len(paths) < len(offsets):
            paths = [paths[0]] * len(offsets)
        if len(transforms) < len(offsets):
            transforms = [transforms[0]] * len(offsets)
        for p, o, t in zip(paths, offsets, transforms):
            result = get_path_collection_extents(transform.frozen(), [p], [t], [o], transOffset.frozen())
            bboxes.append(result)
    return bboxes


def get_renderer(fig):
    if hasattr(fig.canvas, 'get_renderer'):
        return fig.canvas.get_renderer()
    if hasattr(fig.canvas, 'renderer'):
        return fig.canvas.renderer
    if matplot_get_renderer:
        return matplot_get_renderer(fig)
    fig.canvas.print_figure(io.BytesIO())
    try:
        return fig._cachedRenderer
    except AttributeError:
        raise ValueError('Unable to determine renderer') from None


def get_shifts_extra(coords, extra_coords):
    N = coords.shape[0]
    xoverlaps = overlap_intervals(coords[:, 0], coords[:, 1], extra_coords[:, 0], extra_coords[:, 1])
    yoverlaps = overlap_intervals(coords[:, 2], coords[:, 3], extra_coords[:, 2], extra_coords[:, 3])
    overlaps = yoverlaps[(yoverlaps[:, None] == xoverlaps).all(-1).any(-1)]
    if len(overlaps) == 0:
        return (np.zeros(coords.shape[0]), np.zeros(coords.shape[0]))
    diff = coords[overlaps[:, 0]] - extra_coords[overlaps[:, 1]]
    xshifts = np.where(np.abs(diff[:, 0]) < np.abs(diff[:, 1]), diff[:, 0], diff[:, 1])
    yshifts = np.where(np.abs(diff[:, 2]) < np.abs(diff[:, 3]), diff[:, 2], diff[:, 3])
    xshifts = np.bincount(overlaps[:, 0], xshifts, minlength=N)
    yshifts = np.bincount(overlaps[:, 0], yshifts, minlength=N)
    return (xshifts, yshifts)


def get_shifts_texts(coords):
    N = coords.shape[0]
    xoverlaps = overlap_intervals(coords[:, 0], coords[:, 1], coords[:, 0], coords[:, 1])
    xoverlaps = xoverlaps[xoverlaps[:, 0] != xoverlaps[:, 1]]
    yoverlaps = overlap_intervals(coords[:, 2], coords[:, 3], coords[:, 2], coords[:, 3])
    yoverlaps = yoverlaps[yoverlaps[:, 0] != yoverlaps[:, 1]]
    overlaps = yoverlaps[(yoverlaps[:, None] == xoverlaps).all(-1).any(-1)]
    if len(overlaps) == 0:
        return (np.zeros(coords.shape[0]), np.zeros(coords.shape[0]))
    diff = coords[overlaps[:, 1]] - coords[overlaps[:, 0]]
    xshifts = np.where(np.abs(diff[:, 0]) < np.abs(diff[:, 1]), diff[:, 0], diff[:, 1])
    yshifts = np.where(np.abs(diff[:, 2]) < np.abs(diff[:, 3]), diff[:, 2], diff[:, 3])
    xshifts = np.bincount(overlaps[:, 0], xshifts, minlength=N)
    yshifts = np.bincount(overlaps[:, 0], yshifts, minlength=N)
    return (xshifts, yshifts)


def iterate(coords, orig_coords, static_coords=None, force_text: tuple[float, float]=(0.1, 0.2), force_static: tuple[float, float]=(0.05, 0.1), force_pull: tuple[float, float]=(0.05, 0.1), expand: tuple[float, float]=(1.05, 1.1), bbox_to_contain=False, only_move={'text': 'xy', 'static': 'xy', 'explode': 'xy', 'pull': 'xy'}):
    text_shifts_x, text_shifts_y = get_shifts_texts(expand_coords(coords, expand[0], expand[1]))
    if static_coords.shape[0] > 0:
        static_shifts_x, static_shifts_y = get_shifts_extra(expand_coords(coords, expand[0], expand[1]), static_coords)
    else:
        static_shifts_x, static_shifts_y = (np.zeros(1), np.zeros(1))
    error_x = np.abs(text_shifts_x) + np.abs(static_shifts_x)
    error_y = np.abs(text_shifts_y) + np.abs(static_shifts_y)
    error = np.sum(np.append(error_x, error_y))
    pull_x, pull_y = pull_back(coords, orig_coords)
    text_shifts_x *= force_text[0]
    text_shifts_y *= force_text[1]
    static_shifts_x *= force_static[0]
    static_shifts_y *= force_static[1]
    pull_x *= -force_pull[0]
    pull_y *= -force_pull[1]
    if only_move:
        if 'x' not in only_move['text']:
            text_shifts_x = np.zeros_like(text_shifts_x)
        elif 'x+' in only_move['text']:
            text_shifts_x[text_shifts_x > 0] = 0
        elif 'x-' in only_move['text']:
            text_shifts_x[text_shifts_x < 0] = 0
        if 'y' not in only_move['text']:
            text_shifts_y = np.zeros_like(text_shifts_y)
        elif 'y+' in only_move['text']:
            text_shifts_y[text_shifts_y > 0] = 0
        elif 'y-' in only_move['text']:
            text_shifts_y[text_shifts_y < 0] = 0
        if 'x' not in only_move['static']:
            static_shifts_x = np.zeros_like(static_shifts_x)
        elif 'x+' in only_move['static']:
            static_shifts_x[static_shifts_x > 0] = 0
        elif 'x-' in only_move['static']:
            static_shifts_x[static_shifts_x < 0] = 0
        if 'y' not in only_move['static']:
            static_shifts_y = np.zeros_like(static_shifts_y)
        elif 'y+' in only_move['static']:
            static_shifts_y[static_shifts_y > 0] = 0
        elif 'y-' in only_move['static']:
            static_shifts_y[static_shifts_y < 0] = 0
        if 'x' not in only_move['pull']:
            pull_x = np.zeros_like(pull_x)
        elif 'x+' in only_move['pull']:
            pull_x[pull_x > 0] = 0
        elif 'x-' in only_move['pull']:
            pull_x[pull_x < 0] = 0
        if 'y' not in only_move['pull']:
            pull_y = np.zeros_like(pull_y)
        elif 'y+' in only_move['pull']:
            pull_y[pull_y > 0] = 0
        elif 'y-' in only_move['pull']:
            pull_y[pull_y < 0] = 0
    shifts_x = text_shifts_x + static_shifts_x + pull_x
    shifts_y = text_shifts_y + static_shifts_y + pull_y
    coords = apply_shifts(coords, shifts_x, shifts_y)
    if bbox_to_contain:
        coords = force_into_bbox(coords, bbox_to_contain)
    return (coords, error)


def overlap_intervals(starts1, ends1, starts2, ends2, closed=False, sort=False):
    for vec in [starts1, ends1, starts2, ends2]:
        if isinstance(vec, pd.Series):
            warnings.warn('One of the inputs is provided as pandas.Series and its index will be ignored.', SyntaxWarning)
    starts1 = np.asarray(starts1)
    ends1 = np.asarray(ends1)
    starts2 = np.asarray(starts2)
    ends2 = np.asarray(ends2)
    n1 = len(starts1)
    n2 = len(starts2)
    ids1 = np.arange(0, n1)
    ids2 = np.arange(0, n2)
    order1 = np.lexsort([ends1, starts1])
    order2 = np.lexsort([ends2, starts2])
    starts1, ends1, ids1 = (starts1[order1], ends1[order1], ids1[order1])
    starts2, ends2, ids2 = (starts2[order2], ends2[order2], ids2[order2])
    match_2in1_starts = np.searchsorted(starts2, starts1, 'left')
    match_2in1_ends = np.searchsorted(starts2, ends1, 'right' if closed else 'left')
    match_1in2_starts = np.searchsorted(starts1, starts2, 'right')
    match_1in2_ends = np.searchsorted(starts1, ends2, 'right' if closed else 'left')
    match_2in1_mask = match_2in1_ends > match_2in1_starts
    match_1in2_mask = match_1in2_ends > match_1in2_starts
    match_2in1_starts, match_2in1_ends = (match_2in1_starts[match_2in1_mask], match_2in1_ends[match_2in1_mask])
    match_1in2_starts, match_1in2_ends = (match_1in2_starts[match_1in2_mask], match_1in2_ends[match_1in2_mask])
    overlap_ids = np.block([[np.repeat(ids1[match_2in1_mask], match_2in1_ends - match_2in1_starts)[:, None], ids2[arange_multi(match_2in1_starts, match_2in1_ends)][:, None]], [ids1[arange_multi(match_1in2_starts, match_1in2_ends)][:, None], np.repeat(ids2[match_1in2_mask], match_1in2_ends - match_1in2_starts)[:, None]]])
    if sort:
        overlap_ids = overlap_ids[np.lexsort([overlap_ids[:, 1], overlap_ids[:, 0]])]
    return overlap_ids


def pull_back(coords, targets):
    dx = np.min(np.subtract(targets[:, 0][:, np.newaxis], coords[:, :2]), axis=1)
    dy = np.min(np.subtract(targets[:, 1][:, np.newaxis], coords[:, 2:]), axis=1)
    return (dx, dy)
