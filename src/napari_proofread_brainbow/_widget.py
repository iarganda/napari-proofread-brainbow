"""Plugin main widgets

widgets
-------
widget_cvtRGB()
    Put channel dims to the last dims so that napari can understand it as RGB
widget_norm
    Normalize the selected image with 99 percentile
widget_contrast_limits_all
    Change contrast limit max of all images at once
widget_scale
    Change scales of z, y, x
widget_points
    Change size of points at once
"""
from itertools import tee

import numpy as np

from magicgui import magic_factory, magicgui
from magicgui.widgets import Container, PushButton
from napari import layers as L
from napari import types
from qtpy.QtWidgets import QMessageBox


_HELP_TEXT = (
    "1. Open an image (or drag-and-drop)                         \n"
    "2. Convert it to RGB                                        \n"
    "3. In 'layer list' on the left, right-click the image layer \n"
    "  and 'Split RGB'. This will split channels into layers.    \n"
    "  This is useful when you go 3D (Ctrl+Y).                   \n"
    "4. You can adjust 'contrast limits' either using 'Normalize'\n"
    "module or 'Contrast max'                                    \n"
    "5. When you are on 3D view mode (Ctrl+Y), z-scale is too    \n"
    "  short. Increasing it may help by 'ZYX scale' slider.      \n"
    "6. When you load a .csv file, it becomes a Points layer in  \n"
    "  napari. You can resize points using 'Points size' module. \n"
    "IMPORTANT. The order of layers matters. Make sure that      \n"
    "Points layers are placed above Image layers so that points  \n"
    "can appear properly."
)


def _show_help_dialog(parent=None):
    """Show plugin usage help in a compact popup dialog."""
    QMessageBox.information(parent, 'Proofread Brainbow Help', _HELP_TEXT)


@magic_factory(
    img_layer=dict(tooltip="Select raw Brainbow image"),
    call_button='convertRGB',
)
def widget_cvtRGB(
    viewer: 'napari.Viewer',
    img_layer: L.Image,
) -> types.LayerDataTuple:
    # print(len(viewer.layers))
    # print(f"you have selected {img_layer}")
    data = img_layer.data
    # print(data.shape, data.ndim, data.dtype)
    if data.ndim == 4:
        # assume (z, c=3, y, x) or (c=3, z, y, x)
        if data.shape[-1] == 3:
            return None
        elif data.shape[1] == 3:
            # (z, c=3, y, x)
            # data = img_layer.data.transpose(1, 0, 2, 3)
            viewer.layers.pop(viewer.layers.index(img_layer))
            kwargs = dict(
                name=img_layer.name + '_rgb'
            )
            return (data.transpose(0, 2, 3, 1), kwargs, 'image')
        elif data.shape[0] == 3:
            # (c=3, z, y, x)
            # data = img_layer.data.transpose(1, 0, 2, 3)
            viewer.layers.pop(viewer.layers.index(img_layer))
            kwargs = dict(
                name=img_layer.name + '_rgb'
            )
            return (data.transpose(1, 2, 3, 0), kwargs, 'image')
    else:
        return None


@magicgui(
    img_layer=dict(tooltip="Set maximum contrast limit to 99 percentile of the "
                   "given image"),
    call_button='normalize(img layer)(perc=99)',
)
def widget_norm(
    viewer: 'napari.Viewer',
    img_layer: L.Image,
):
    data = img_layer.data
    # print(data.shape)
    if data.shape[-1] == 3:
        # per channel
        _vmax = np.percentile(data, 99, axis=tuple(range(data.ndim - 1)))
        # print(f'_vmax: {_vmax}')
        vmax = max(_vmax)
        # print(f'vmax: {vmax}')
    else:
        vmax = np.percentile(data, 99)
        # print(f'vmax: {vmax}')
    contrast_limits = [img_layer.contrast_limits[0], vmax]
    # print(f'contrast_limits: {contrast_limits}')
    img_layer.contrast_limits = contrast_limits


@magicgui(
    contrast_limits_vmax=dict(
        label='vmax',
        widget_type='Slider',
        value=255,
        step=1,
        min=1,
        max=255,
        tooltip="Adjust all images' contrast_limits at once"
    ),
    auto_call=True,
)
def widget_contrast_limits_all(
    viewer: 'napari.Viewer',
    contrast_limits_vmax,
):
    for l in viewer.layers:
        if isinstance(l, L.Image):
            _min = l.contrast_limits[0]
            if contrast_limits_vmax > _min:
                l.contrast_limits = [l.contrast_limits[0], contrast_limits_vmax]


@magicgui(
    scale_z=dict(
        widget_type='FloatSlider',
        value=1.0,
        step=0.1,
        min=0.5,
        max=5.0,
    ),
    scale_y=dict(
        widget_type='FloatSlider',
        value=1.0,
        step=0.1,
        min=0.5,
        max=5.0,
    ),
    scale_x=dict(
        widget_type='FloatSlider',
        value=1.0,
        step=0.1,
        min=0.5,
        max=5.0,
    ),
    scale_z_default=dict(
        widget_type='PushButton',
        value=True,
        text='default_z'
    ),
    scale_y_default=dict(
        widget_type='PushButton',
        value=True,
        text='default_y'
    ),
    scale_x_default=dict(
        widget_type='PushButton',
        value=True,
        text='default_x'
    ),
    auto_call=True,
    call_button=False,
)
def widget_scale(
    viewer: 'napari.Viewer',
    scale_z,
    scale_y,
    scale_x,
    scale_z_default,
    scale_y_default,
    scale_x_default,
):
    scale_z = round(scale_z, 1)
    scale_y = round(scale_y, 1)
    scale_x = round(scale_x, 1)
    # print(scale_z, scale_y, scale_x)
    scale = scale_z, scale_y, scale_x
    for l in viewer.layers:
        if hasattr(l, 'scale'):
            # print(f"set scale of {l.name} to {scale}")
            l.scale = scale


@widget_scale.scale_z_default.changed.connect
def _scale_z_default(value):
    viewer = widget_scale.viewer.value
    # print(viewer, type(viewer))
    scale_z = 1.0
    scale_y = widget_scale.scale_y.value
    scale_x = widget_scale.scale_x.value
    scale = scale_z, scale_y, scale_x
    # update widget_scale_z
    widget_scale.scale_z.value = scale_z
    for l in viewer.layers:
        if hasattr(l, 'scale'):
            # print(f"set scale of {l.name} to {scale}")
            if isinstance(l, (L.Image, L.Points)):
                l.scale = scale


@widget_scale.scale_y_default.changed.connect
def _scale_y_default(value):
    viewer = widget_scale.viewer.value
    scale_z = widget_scale.scale_z.value
    scale_y = 1.0
    scale_x = widget_scale.scale_x.value
    scale = scale_z, scale_y, scale_x
    # update widget_scale_z
    widget_scale.scale_y.value = scale_y
    for l in viewer.layers:
        if hasattr(l, 'scale'):
            # print(f"set scale of {l.name} to {scale}")
            l.scale = scale


@widget_scale.scale_x_default.changed.connect
def _scale_x_default(value):
    viewer = widget_scale.viewer.value
    scale_z = widget_scale.scale_z.value
    scale_y = widget_scale.scale_y.value
    scale_x = 1.0
    scale = scale_z, scale_y, scale_x
    # update widget_scale_z
    widget_scale.scale_x.value = scale_x
    for l in viewer.layers:
        if hasattr(l, 'scale'):
            # print(f"set scale of {l.name} to {scale}")
            l.scale = scale


@magicgui(
    point_size=dict(
        tooltip="Change size of all points at once",
        widget_type="Slider",
        value=10,
        max=15
    ),
    auto_call=True,
    call_button=False,
)
def widget_points(
    point_layer: L.Points,
    point_size,
):
    # print(f"you have selected {point_layer}")
    # Seems to interact with scales and distance from camera
    point_layer.size = point_size


@magic_factory(
    xbins=dict(
        widget_type='Slider',
        value=5,
        step=1,
        min=2,
        max=10,
    ),
    ybins=dict(
        widget_type='Slider',
        value=5,
        step=1,
        min=2,
        max=10,
    ),
    # thickness = dict(
    #     widget_type='FloatSlider',
    #     value=1,
    #     step=0.1,
    #     min=1,
    #     max=10,
    # ),
    # auto_call=True
    call_button='make grid'
)
def widget_grid(
    img_layer: 'napari.layers.Image',
    xbins,
    ybins,
) -> types.LayerDataTuple:
    def pairwise(x):
        a, b = tee(x)
        next(b, None)
        return zip(a, b)

    shape = img_layer.data.shape
    width = shape[-2] if shape[-1] == 3 else shape[-1]
    height = shape[-3] if shape[-1] == 3 else shape[-2]
    bins_x = np.linspace(0, width, xbins+1, endpoint=True)
    bins_y = np.linspace(0, height, ybins+1, endpoint=True)
    data = []
    # vertical
    for x in bins_x:
        # coord [[y0, x0], [y1, x1]]
        data.append(np.array([[0, x], [height, x]]))
    # horizontal
    for y in bins_y:
        data.append(np.array([[y, 0], [y, width]]))
    # dummies for text
    # a pair of `features` and `text` argument can be used to put text on shape
    # object. but it does not support defining a translation for each obeject.
    XLABELS = 'ABCDEFGHIJ'
    yoffset = - height * 0.05
    xoffset = - width * 0.05
    for x0, x1 in pairwise(bins_x):
        data.append(np.array([[yoffset, x0], [yoffset, x1]]))
        ...
    for y0, y1 in pairwise(bins_y):
        data.append(np.array([[y0, xoffset], [y1, xoffset]]))
        ...

    text = {
        'string': '{number}',
        # 'anchor': ''
        # 'translation': [0, 0],
        'size': 16,
        'color': 'lime',
    }
    features = {
        'number': (
            ['' for _ in range(xbins + ybins + 2)] +  # empty for grid
            [XLABELS[i] for i in range(xbins)] +  # ABCD...
            list(range(ybins))  # 123..
        )
    }
    kwargs = dict(
        name=f'grid({img_layer.name})',
        shape_type='line',
        # edge_width=thickness,
        features=features,
        text=text,
    )
    return (data, kwargs, 'shapes')


class MainWidget(Container):
    def __init__(
        self,
        layout='vertical',
        widgets=[
            widget_cvtRGB(),  # 0
            widget_norm,      # 1
            widget_contrast_limits_all,  # 2
            widget_scale,     # 3
            widget_points,    # 4
            widget_grid(),    # 5
        ]
    ):
        widgets[0].label = 'Convert to RGB'
        widgets[1].label = 'Normalize'
        widgets[2].label = 'Contrast max'
        widgets[3].label = 'ZYX scale'
        widgets[4].label = 'Points size'
        widgets[5].label = 'Grid'

        help_button = PushButton(text='Show help')
        help_button.label = 'Description'
        help_button.changed.connect(lambda _: _show_help_dialog(self.native))
        widgets.insert(0, help_button)
        super().__init__(layout=layout, widgets=widgets)


# @magic_factory(
#     img_layer=dict(tooltip="Select raw probability image"),
#     threshold=dict(widget_type='FloatSlider',
#                    min=0, max=1.0, step=0.01, value=0.5),
#     auto_call=True
# )
# def threshold_prob(
#     img_layer: L.Image,
#     threshold
# ) -> types.LabelsData:
#     return img_layer.data.copy() > threshold


class ThresholdPoints(L.Points):
    """Same as Points layer with additional data callbacks
    """

    _max_points_thumbnail = 1024

    def __init__(
        self,
        data=None,
        **kwargs
    ):
        super().__init__(
            data=data,
            **kwargs,
        )

    def add(self, coord):
        """Adds point at coordinate. (Override napari.Points.add)

        Parameters
        ----------
        coord : sequence of indices to add point at
        """
        super().add(coord)
        # -2 because the new point is already added.
        ind = max(self._id_offset, self.properties['id'][-2]) + 1
        self._id_offset = ind
        self.border_color[-1] = [0.0, 1.0, 0.0, 1.0]  # green
        # overriding properties
        self.properties['id'][-1] = ind
        self.properties['probability'][-1] = 1.0
        source_points = self.source_points
        source_points.add(coord)
        # match 'id' and 'probability'
        source_points.properties['id'][-1] = ind
        source_points.properties['probability'][-1] = 1.0

    def remove_selected(self):
        """Removes selected points if any. (Override napari.Points.remove_selected)
        """
        index = list(self.selected_data)
        index.sort()
        if len(index):
            source_points = self.source_points
            selected_ids = [self.properties['id'][i] for i in index]
            source_ids = source_points.properties['id'].tolist()
            source_index = [source_ids.index(i) for i in selected_ids]
            # remove
            super().remove_selected()
            source_points.selected_data = set(source_index)
            source_points.remove_selected()
            # end(ThresholdPoints)

    @property
    def _type_string(self):
        """If not set, it set to classname. It's used for save()"""
        return 'points'


@magic_factory(
    # point_layer=dict(tooltip="Select probability csv"),
    threshold=dict(widget_type='FloatSlider',
                   min=0, max=1.0, step=0.01, value=0.5),
    auto_call=True,
    call_button=True,
)
def threshold_prob(
    viewer: 'napari.Viewer',
    point_layer: L.Points,
    threshold
) -> L.Points:
    if 'probability' in point_layer.properties:
        prob = point_layer.properties['probability']
        m = prob > threshold
        # update Points
        name = 'threshold_prob'
        names = [layer.name for layer in viewer.layers]
        if name in names:
            points = viewer.layers[names.index(name)]
            ids = point_layer.properties['id']
            # update
            points.data = point_layer.data[m]
            points.properties = dict(id=ids[m],
                                     probability=prob[m])
        else:
            # new Points
            # Create 'threshold_prob' layer (custom ThresholdPoints).
            # ThresholdPoints is a subclass of napari.layers.Points.
            ids = np.arange(len(prob))
            m = prob > threshold
            points = ThresholdPoints(
                data=point_layer.data.copy()[m],
                name=name,
                border_color='red',
                # add properties
                properties=dict(id=ids[m],  # assign id
                                probability=prob[m]),  # copy probability
            )
            points.source_points = point_layer
            points._id_offset = ids[-1]
            # Add 'id' properties
            point_layer.features['id'] = ids
            return points
