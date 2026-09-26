/*
 * Copyright (c) 2026 Agroecology Lab
 *
 * SPDX-License-Identifier: Apache-2.0
 *
 * Point-in-polygon geofence check.
 *
 * Algorithm: PNPOLY, W. Randolph Franklin (MIT-licensed original):
 * https://wrf.ecse.rpi.edu/Research/Short_Notes/pnpoly.html
 * See also chrberger/geofence (MIT) for a C++ header-only wrapper of the
 * same algorithm: https://github.com/chrberger/geofence
 *
 * LIMITATION: this is a planar test, not geodesic. Coordinates are
 * treated as flat Cartesian (x, y). For small-area fences (a field, a
 * site boundary) lat/lon degrees are an adequate approximation; do not
 * use this directly for fences spanning large areas, crossing the
 * +/-180 degree meridian, or near the poles without first projecting
 * to a local tangent plane. Behaviour for a test point exactly on a
 * polygon edge is unspecified (documented PNPOLY property) -- do not
 * rely on edge-exact results for the safety boundary itself; apply a
 * margin.
 */
#ifndef CEREBRI_CORE_GEOFENCE_H_
#define CEREBRI_CORE_GEOFENCE_H_

#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

struct geofence_point {
	double x;
	double y;
};

/**
 * @brief Test whether a point lies inside a polygon.
 *
 * @param poly    Vertices in order; do not repeat the first vertex at
 *                the end.
 * @param n_verts Number of vertices; must be >= 3.
 * @param test    Point to test.
 *
 * @retval true  test is inside poly.
 * @retval false test is outside poly, n_verts < 3, or poly is NULL.
 */
bool geofence_point_in_polygon(const struct geofence_point *poly,
				size_t n_verts,
				struct geofence_point test);

#ifdef __cplusplus
}
#endif

#endif /* CEREBRI_CORE_GEOFENCE_H_ */
