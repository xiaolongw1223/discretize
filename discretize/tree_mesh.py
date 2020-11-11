#      ___          ___       ___          ___          ___          ___
#     /\  \        /\  \     /\  \        /\  \        /\  \        /\  \
#    /::\  \      /::\  \    \:\  \      /::\  \      /::\  \      /::\  \
#   /:/\:\  \    /:/\:\  \    \:\  \    /:/\:\  \    /:/\:\  \    /:/\:\  \
#  /:/  \:\  \  /:/  \:\  \   /::\  \  /::\~\:\  \  /::\~\:\  \  /::\~\:\  \
# /:/__/ \:\__\/:/__/ \:\__\ /:/\:\__\/:/\:\ \:\__\/:/\:\ \:\__\/:/\:\ \:\__\
# \:\  \ /:/  /\:\  \  \/__//:/  \/__/\/_|::\/:/  /\:\~\:\ \/__/\:\~\:\ \/__/
#  \:\  /:/  /  \:\  \     /:/  /        |:|::/  /  \:\ \:\__\   \:\ \:\__\
#   \:\/:/  /    \:\  \    \/__/         |:|\/__/    \:\ \/__/    \:\ \/__/
#    \::/  /      \:\__\                 |:|  |       \:\__\       \:\__\
#     \/__/        \/__/                  \|__|        \/__/        \/__/
#
#
#
#                      .----------------.----------------.
#                     /|               /|               /|
#                    / |              / |              / |
#                   /  |      6      /  |     7       /  |
#                  /   |            /   |            /   |
#                 .----------------.----+-----------.    |
#                /|    . ---------/|----.----------/|----.
#               / |   /|         / |   /|         / |   /|
#              /  |  / |  4     /  |  / |   5    /  |  / |
#             /   | /  |       /   | /  |       /   | /  |
#            . -------------- .----------------.    |/   |
#            |    . ---+------|----.----+------|----.    |
#            |   /|    .______|___/|____.______|___/|____.
#            |  / |   /    2  |  / |   /     3 |  / |   /
#            | /  |  /        | /  |  /        | /  |  /
#            . ---+---------- . ---+---------- .    | /
#            |    |/          |    |/          |    |/             z
#            |    . ----------|----.-----------|----.              ^   y
#            |   /      0     |   /       1    |   /               |  /
#            |  /             |  /             |  /                | /
#            | /              | /              | /                 o----> x
#            . -------------- . -------------- .
#
#
# Face Refinement:
#
#      2_______________3                    _______________
#      |               |                   |       |       |
#   ^  |               |                   |   2   |   3   |
#   |  |               |                   |       |       |
#   |  |       x       |        --->       |-------+-------|
#   t1 |               |                   |       |       |
#      |               |                   |   0   |   1   |
#      |_______________|                   |_______|_______|
#      0      t0-->    1
#
#
# Face and Edge naming conventions:
#
#                      fZp
#                       |
#                 6 ------eX3------ 7
#                /|     |         / |
#               /eZ2    .        / eZ3
#             eY2 |        fYp eY3  |
#             /   |            / fXp|
#            4 ------eX2----- 5     |
#            |fXm 2 -----eX1--|---- 3          z
#           eZ0  /            |  eY1           ^   y
#            | eY0   .  fYm  eZ1 /             |  /
#            | /     |        | /              | /
#            0 ------eX0------1                o----> x
#                    |
#                   fZm
#
#
#            fX                                  fY
#      2___________3                       2___________3
#      |     e1    |                       |     e1    |
#      |           |                       |           |
#   e0 |     x     | e2      z          e0 |     x     | e2      z
#      |           |         ^             |           |         ^
#      |___________|         |___> y       |___________|         |___> x
#      0    e3     1                       0    e3     1
#           fZ
#      2___________3
#      |     e1    |
#      |           |
#   e0 |     x     | e2      y
#      |           |         ^
#      |___________|         |___> x
#      0    e3     1

import properties

from discretize.base import BaseTensorMesh
from discretize.operators import InnerProducts, DiffOperators
from discretize.base.mesh_io import TreeMeshIO
from discretize.utils import as_array_n_by_dim
from discretize._extensions.tree_ext import _TreeMesh, TreeCell
import numpy as np
import scipy.sparse as sp
import warnings
from discretize.utils.code_utils import deprecate_property


class TreeMesh(_TreeMesh, BaseTensorMesh, InnerProducts, TreeMeshIO):
    """
    TreeMesh is a class for adaptive QuadTree (2D) and OcTree (3D) meshes.
    """

    _meshType = "TREE"
    _aliases = {
        **BaseTensorMesh._aliases,
        **DiffOperators._aliases,
        **{
            "ntN": "n_total_nodes",
            "ntEx": "n_total_edges_x",
            "ntEy": "n_total_edges_y",
            "ntEz": "n_total_edges_z",
            "ntE": "n_total_edges",
            "ntFx": "n_total_faces_x",
            "ntFy": "n_total_faces_y",
            "ntFz": "n_total_faces_z",
            "ntF": "n_total_faces",
            "nhN": "n_hanging_nodes",
            "nhEx": "n_hanging_edges_x",
            "nhEy": "n_hanging_edges_y",
            "nhEz": "n_hanging_edges_z",
            "nhE": "n_hanging_edges",
            "nhFx": "n_hanging_faces_x",
            "nhFy": "n_hanging_faces_y",
            "nhFz": "n_hanging_faces_z",
            "nhF": "n_hanging_faces",
            "gridhN": "grid_hanging_nodes",
            "gridhFx": "grid_hanging_faces_x",
            "gridhFy": "grid_hanging_faces_y",
            "gridhFz": "grid_hanging_faces_z",
            "gridhEx": "grid_hanging_edges_x",
            "gridhEy": "grid_hanging_edges_y",
            "gridhEz": "grid_hanging_edges_z",
        },
    }

    # inheriting stuff from BaseTensorMesh that isn't defined in _QuadTree
    def __init__(self, h=None, x0=None, **kwargs):
        if "h" in kwargs.keys():
            h = kwargs.pop("h")
        if "x0" in kwargs.keys():
            x0 = kwargs.pop("x0")
        # print(h, x0)
        BaseTensorMesh.__init__(
            self, h, x0
        )  # TODO:, **kwargs) # pass the kwargs for copy/paste

        nx = len(self.h[0])
        ny = len(self.h[1])
        nz = len(self.h[2]) if self.dim == 3 else 2

        def is_pow2(num):
            return ((num & (num - 1)) == 0) and num != 0

        if not (is_pow2(nx) and is_pow2(ny) and is_pow2(nz)):
            raise ValueError("length of cell width vectors must be a power of 2")
        # Now can initialize cpp tree parent
        _TreeMesh.__init__(self, self.h, self.x0)

        if "cell_levels" in kwargs.keys() and "cell_indexes" in kwargs.keys():
            inds = kwargs.pop("cell_indexes")
            levels = kwargs.pop("cell_levels")
            self.__setstate__((inds, levels))

    def __repr__(self):
        """Plain text representation."""
        mesh_name = "{0!s}TreeMesh".format(("Oc" if self.dim == 3 else "Quad"))

        top = "\n" + mesh_name + ": {0:2.2f}% filled\n\n".format(self.fill * 100)

        # Number of cells per level
        level_count = self._count_cells_per_index()
        non_zero_levels = np.nonzero(level_count)[0]
        cell_display = ["Level : Number of cells"]
        cell_display.append("-----------------------")
        for level in non_zero_levels:
            cell_display.append("{:^5} : {:^15}".format(level, level_count[level]))
        cell_display.append("-----------------------")
        cell_display.append("Total : {:^15}".format(self.nC))

        extent_display = ["            Mesh Extent       "]
        extent_display.append("        min     ,     max     ")
        extent_display.append("   ---------------------------")
        dim_label = {0: "x", 1: "y", 2: "z"}
        for dim in range(self.dim):
            n_vector = getattr(self, "nodes_" + dim_label[dim])
            extent_display.append(
                "{}: {:^13},{:^13}".format(dim_label[dim], n_vector[0], n_vector[-1])
            )

        for i, line in enumerate(extent_display):
            if i == len(cell_display):
                cell_display.append(" " * (len(cell_display[0]) - 3 - len(line)))
            cell_display[i] += 3 * " " + line

        h_display = ["     Cell Widths    "]
        h_display.append("    min   ,   max   ")
        h_display.append("-" * (len(h_display[0])))
        h_gridded = self.h_gridded
        mins = np.min(h_gridded, axis=0)
        maxs = np.max(h_gridded, axis=0)
        for dim in range(self.dim):
            h_display.append("{:^10}, {:^10}".format(mins[dim], maxs[dim]))

        for i, line in enumerate(h_display):
            if i == len(cell_display):
                cell_display.append(" " * len(cell_display[0]))
            cell_display[i] += 3 * " " + line

        return top + "\n".join(cell_display)

    def _repr_html_(self):
        """html representation"""
        mesh_name = "{0!s}TreeMesh".format(("Oc" if self.dim == 3 else "Quad"))
        level_count = self._count_cells_per_index()
        non_zero_levels = np.nonzero(level_count)[0]
        dim_label = {0: "x", 1: "y", 2: "z"}
        h_gridded = self.h_gridded
        mins = np.min(h_gridded, axis=0)
        maxs = np.max(h_gridded, axis=0)

        style = " style='padding: 5px 20px 5px 20px;'"
        # Cell level table:
        cel_tbl = "<table>\n"
        cel_tbl += "<tr>\n"
        cel_tbl += "<th" + style + ">Level</th>\n"
        cel_tbl += "<th" + style + ">Number of cells</th>\n"
        cel_tbl += "</tr>\n"
        for level in non_zero_levels:
            cel_tbl += "<tr>\n"
            cel_tbl += "<td" + style + ">{}</td>\n".format(level)
            cel_tbl += "<td" + style + ">{}</td>\n".format(level_count[level])
            cel_tbl += "</tr>\n"
        cel_tbl += "<tr>\n"
        cel_tbl += (
            "<td style='font-weight: bold; padding: 5px 20px 5px 20px;'> Total </td>\n"
        )
        cel_tbl += "<td" + style + "> {} </td>\n".format(self.nC)
        cel_tbl += "</tr>\n"
        cel_tbl += "</table>\n"

        det_tbl = "<table>\n"
        det_tbl += "<tr>\n"
        det_tbl += "<th></th>\n"
        det_tbl += "<th" + style + " colspan='2'>Mesh extent</th>\n"
        det_tbl += "<th" + style + " colspan='2'>Cell widths</th>\n"
        det_tbl += "</tr>\n"

        det_tbl += "<tr>\n"
        det_tbl += "<th></th>\n"
        det_tbl += "<th" + style + ">min</th>\n"
        det_tbl += "<th" + style + ">max</th>\n"
        det_tbl += "<th" + style + ">min</th>\n"
        det_tbl += "<th" + style + ">max</th>\n"
        det_tbl += "</tr>\n"
        for dim in range(self.dim):
            n_vector = getattr(self, "nodes_" + dim_label[dim])
            det_tbl += "<tr>\n"
            det_tbl += "<td" + style + ">{}</td>\n".format(dim_label[dim])
            det_tbl += "<td" + style + ">{}</td>\n".format(n_vector[0])
            det_tbl += "<td" + style + ">{}</td>\n".format(n_vector[-1])
            det_tbl += "<td" + style + ">{}</td>\n".format(mins[dim])
            det_tbl += "<td" + style + ">{}</td>\n".format(maxs[dim])
            det_tbl += "</tr>\n"
        det_tbl += "</table>\n"

        full_tbl = "<table>\n"
        full_tbl += "<tr>\n"
        full_tbl += "<td style='font-weight: bold; font-size: 1.2em; text-align: center;'>{}</td>\n".format(
            mesh_name
        )
        full_tbl += "<td style='font-size: 1.2em; text-align: center;' colspan='2'>{0:2.2f}% filled</td>\n".format(
            100 * self.fill
        )
        full_tbl += "</tr>\n"
        full_tbl += "<tr>\n"

        full_tbl += "<td>\n"
        full_tbl += cel_tbl
        full_tbl += "</td>\n"

        full_tbl += "<td>\n"
        full_tbl += det_tbl
        full_tbl += "</td>\n"

        full_tbl += "</tr>\n"
        full_tbl += "</table>\n"

        return full_tbl

    @properties.validator("x0")
    def _x0_validator(self, change):
        self._set_x0(change["value"])

    @property
    def vntF(self):
        """Total number of hanging and non-hanging faces in a [nx,ny,nz] form"""
        return [self.ntFx, self.ntFy] + ([] if self.dim == 2 else [self.ntFz])

    @property
    def vntE(self):
        """Total number of hanging and non-hanging edges in a [nx,ny,nz] form"""
        return [self.ntEx, self.ntEy] + ([] if self.dim == 2 else [self.ntEz])

    @property
    def cell_gradient_stencil(self):
        if getattr(self, "_cellGradStencil", None) is None:

            self._cellGradStencil = sp.vstack(
                [self._cellGradxStencil, self._cellGradyStencil]
            )
            if self.dim == 3:
                self._cellGradStencil = sp.vstack(
                    [self._cellGradStencil, self._cellGradzStencil]
                )

        return self._cellGradStencil

    @property
    def cell_gradient(self):
        """
        Cell centered Gradient operator built off of the faceDiv operator.
        Grad =  - (Mf)^{-1} * Div * diag (volume)
        """
        if getattr(self, "_cellGrad", None) is None:

            i_s = self.face_boundary_indices

            ix = np.ones(self.nFx)
            ix[i_s[0]] = 0.0
            ix[i_s[1]] = 0.0
            Pafx = sp.diags(ix)

            iy = np.ones(self.nFy)
            iy[i_s[2]] = 0.0
            iy[i_s[3]] = 0.0
            Pafy = sp.diags(iy)

            MfI = self.get_face_inner_product(invMat=True)

            if self.dim == 2:
                Pi = sp.block_diag([Pafx, Pafy])

            elif self.dim == 3:
                iz = np.ones(self.nFz)
                iz[i_s[4]] = 0.0
                iz[i_s[5]] = 0.0
                Pafz = sp.diags(iz)
                Pi = sp.block_diag([Pafx, Pafy, Pafz])

            self._cellGrad = (
                -Pi * MfI * self.face_divergence.T * sp.diags(self.cell_volumes)
            )

        return self._cellGrad

    @property
    def cell_gradient_x(self):
        """
        Cell centered Gradient operator in x-direction (Gradx)
        Grad = sp.vstack((Gradx, Grady, Gradz))
        """
        if getattr(self, "_cellGradx", None) is None:

            nFx = self.nFx
            i_s = self.face_boundary_indices

            ix = np.ones(self.nFx)
            ix[i_s[0]] = 0.0
            ix[i_s[1]] = 0.0
            Pafx = sp.diags(ix)

            MfI = self.get_face_inner_product(invMat=True)
            MfIx = sp.diags(MfI.diagonal()[:nFx])

            self._cellGradx = (
                -Pafx * MfIx * self.face_x_divergence.T * sp.diags(self.cell_volumes)
            )

        return self._cellGradx

    @property
    def cell_gradient_y(self):
        """
        Cell centered Gradient operator in y-direction (Grady)
        Grad = sp.vstack((Gradx, Grady, Gradz))
        """
        if getattr(self, "_cellGrady", None) is None:

            nFx = self.nFx
            nFy = self.nFy
            i_s = self.face_boundary_indices

            iy = np.ones(self.nFy)
            iy[i_s[2]] = 0.0
            iy[i_s[3]] = 0.0
            Pafy = sp.diags(iy)

            MfI = self.get_face_inner_product(invMat=True)
            MfIy = sp.diags(MfI.diagonal()[nFx : nFx + nFy])

            self._cellGrady = (
                -Pafy * MfIy * self.face_y_divergence.T * sp.diags(self.cell_volumes)
            )

        return self._cellGrady

    @property
    def cell_gradient_z(self):
        """
        Cell centered Gradient operator in z-direction (Gradz)
        Grad = sp.vstack((Gradx, Grady, Gradz))
        """
        if self.dim == 2:
            raise TypeError("z derivative not defined in 2D")
        if getattr(self, "_cellGradz", None) is None:

            nFx = self.nFx
            nFy = self.nFy
            i_s = self.face_boundary_indices

            iz = np.ones(self.nFz)
            iz[i_s[4]] = 0.0
            iz[i_s[5]] = 0.0
            Pafz = sp.diags(iz)

            MfI = self.get_face_inner_product(invMat=True)
            MfIz = sp.diags(MfI.diagonal()[nFx + nFy :])

            self._cellGradz = (
                -Pafz * MfIz * self.face_z_divergence.T * sp.diags(self.cell_volumes)
            )

        return self._cellGradz

    @property
    def face_x_divergence(self):
        if getattr(self, "_faceDivx", None) is None:
            self._faceDivx = self.face_divergence[:, : self.nFx]
        return self._faceDivx

    @property
    def face_y_divergence(self):
        if getattr(self, "_faceDivy", None) is None:
            self._faceDivy = self.face_divergence[:, self.nFx : self.nFx + self.nFy]
        return self._faceDivy

    @property
    def face_z_divergence(self):
        if getattr(self, "_faceDivz", None) is None:
            self._faceDivz = self.face_divergence[:, self.nFx + self.nFy :]
        return self._faceDivz

    def point2index(self, locs):
        """Finds cells that contain the given points.
        Returns an array of index values of the cells that contain the given
        points

        Parameters
        ----------
        locs: array_like of shape (N, dim)
            points to search for the location of

        Returns
        -------
        numpy.array of integers of length(N)
            Cell indices that contain the points
        """
        locs = as_array_n_by_dim(locs, self.dim)
        inds = self._get_containing_cell_indexes(locs)
        return inds

    def cell_levels_by_index(self, indices):
        """Fast function to return a list of levels for the given cell indices

        Parameters
        ----------
        index: array_like of length (N)
            Cell indexes to query

        Returns
        -------
        numpy.array of length (N)
            Levels for the cells.
        """

        return self._cell_levels_by_indexes(indices)

    def get_interpolation_matrix(
        self, locs, loc_type="CC", zeros_outside=False, **kwargs
    ):
        """Produces interpolation matrix

        Parameters
        ----------
        loc : numpy.ndarray
            Location of points to interpolate to

        loc_type: str
            What to interpolate

            loc_type can be::

                'Ex'    -> x-component of field defined on edges
                'Ey'    -> y-component of field defined on edges
                'Ez'    -> z-component of field defined on edges
                'Fx'    -> x-component of field defined on faces
                'Fy'    -> y-component of field defined on faces
                'Fz'    -> z-component of field defined on faces
                'N'     -> scalar field defined on nodes
                'CC'    -> scalar field defined on cell centers

        Returns
        -------
        scipy.sparse.csr_matrix
            M, the interpolation matrix

        """
        if "locType" in kwargs:
            warnings.warn(
                "The locType keyword argument has been deprecated, please use loc_type. "
                "This will be removed in discretize 1.0.0",
                FutureWarning,
            )
            loc_type = kwargs["locType"]
        if "zerosOutside" in kwargs:
            warnings.warn(
                "The zerosOutside keyword argument has been deprecated, please use loc_type. "
                "This will be removed in discretize 1.0.0",
                FutureWarning,
            )
            zeros_outside = kwargs["zerosOutside"]
        locs = as_array_n_by_dim(locs, self.dim)
        if loc_type not in ["N", "CC", "Ex", "Ey", "Ez", "Fx", "Fy", "Fz"]:
            raise Exception("loc_type must be one of N, CC, Ex, Ey, Ez, Fx, Fy, or Fz")

        if self.dim == 2 and loc_type in ["Ez", "Fz"]:
            raise Exception("Unable to interpolate from Z edges/face in 2D")

        locs = np.require(np.atleast_2d(locs), dtype=np.float64, requirements="C")

        if loc_type == "N":
            Av = self._getNodeIntMat(locs, zeros_outside)
        elif loc_type in ["Ex", "Ey", "Ez"]:
            Av = self._getEdgeIntMat(locs, zeros_outside, loc_type[1])
        elif loc_type in ["Fx", "Fy", "Fz"]:
            Av = self._getFaceIntMat(locs, zeros_outside, loc_type[1])
        elif loc_type in ["CC"]:
            Av = self._getCellIntMat(locs, zeros_outside)
        return Av

    @property
    def permute_cells(self):
        """Permutation matrix re-ordering of cells sorted by x, then y, then z"""
        # TODO: cache these?
        P = np.lexsort(self.gridCC.T)  # sort by x, then y, then z
        return sp.identity(self.nC).tocsr()[P]

    @property
    def permute_faces(self):
        """Permutation matrix re-ordering of faces sorted by x, then y, then z"""
        # TODO: cache these?
        Px = np.lexsort(self.gridFx.T)
        Py = np.lexsort(self.gridFy.T) + self.nFx
        if self.dim == 2:
            P = np.r_[Px, Py]
        else:
            Pz = np.lexsort(self.gridFz.T) + (self.nFx + self.nFy)
            P = np.r_[Px, Py, Pz]
        return sp.identity(self.nF).tocsr()[P]

    @property
    def permute_edges(self):
        """Permutation matrix re-ordering of edges sorted by x, then y, then z"""
        # TODO: cache these?
        Px = np.lexsort(self.gridEx.T)
        Py = np.lexsort(self.gridEy.T) + self.nEx
        if self.dim == 2:
            P = np.r_[Px, Py]
        if self.dim == 3:
            Pz = np.lexsort(self.gridEz.T) + (self.nEx + self.nEy)
            P = np.r_[Px, Py, Pz]
        return sp.identity(self.nE).tocsr()[P]

    def serialize(self):
        serial = BaseTensorMesh.serialize(self)
        inds, levels = self.__getstate__()
        serial["cell_indexes"] = inds.tolist()
        serial["cell_levels"] = levels.tolist()
        return serial

    @classmethod
    def deserialize(cls, serial):
        mesh = cls(**serial)
        return mesh

    def __reduce__(self):
        return TreeMesh, (self.h, self.x0), self.__getstate__()

    cellGrad = deprecate_property("cell_gradient", "cellGrad", removal_version="1.0.0")
    cellGradx = deprecate_property(
        "cell_gradient_x", "cellGradx", removal_version="1.0.0"
    )
    cellGrady = deprecate_property(
        "cell_gradient_y", "cellGrady", removal_version="1.0.0"
    )
    cellGradz = deprecate_property(
        "cell_gradient_z", "cellGradz", removal_version="1.0.0"
    )
    cellGradStencil = deprecate_property(
        "cell_gradient_stencil", "cellGradStencil", removal_version="1.0.0"
    )
    nodalGrad = deprecate_property(
        "nodal_gradient", "nodalGrad", removal_version="1.0.0"
    )
    nodalLaplacian = deprecate_property(
        "nodal_laplacian", "nodalLaplacian", removal_version="1.0.0"
    )
    faceDiv = deprecate_property("face_divergence", "faceDiv", removal_version="1.0.0")
    faceDivx = deprecate_property(
        "face_x_divergence", "faceDivx", removal_version="1.0.0"
    )
    faceDivy = deprecate_property(
        "face_y_divergence", "faceDivy", removal_version="1.0.0"
    )
    faceDivz = deprecate_property(
        "face_z_divergence", "faceDivz", removal_version="1.0.0"
    )
    edgeCurl = deprecate_property("edge_curl", "edgeCurl", removal_version="1.0.0")
    maxLevel = deprecate_property("max_used_level", "maxLevel", removal_version="1.0.0")
    vol = deprecate_property("cell_volumes", "vol", removal_version="1.0.0")
    areaFx = deprecate_property("face_x_areas", "areaFx", removal_version="1.0.0")
    areaFy = deprecate_property("face_y_areas", "areaFy", removal_version="1.0.0")
    areaFz = deprecate_property("face_z_areas", "areaFz", removal_version="1.0.0")
    area = deprecate_property("face_areas", "area", removal_version="1.0.0")
    edgeEx = deprecate_property("edge_x_lengths", "edgeEx", removal_version="1.0.0")
    edgeEy = deprecate_property("edge_y_lengths", "edgeEy", removal_version="1.0.0")
    edgeEz = deprecate_property("edge_z_lengths", "edgeEz", removal_version="1.0.0")
    edge = deprecate_property("edge_lengths", "edge", removal_version="1.0.0")
    permuteCC = deprecate_property(
        "permute_cells", "permuteCC", removal_version="1.0.0"
    )
    permuteF = deprecate_property("permute_faces", "permuteF", removal_version="1.0.0")
    permuteE = deprecate_property("permute_edges", "permuteE", removal_version="1.0.0")
    faceBoundaryInd = deprecate_property(
        "face_boundary_indices", "faceBoundaryInd", removal_version="1.0.0"
    )
    cellBoundaryInd = deprecate_property(
        "cell_boundary_indices", "cellBoundaryInd", removal_version="1.0.0"
    )
