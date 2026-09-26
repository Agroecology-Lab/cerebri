/*
 * Copyright (c) 2026 Agroecology Lab
 *
 * SPDX-License-Identifier: Apache-2.0
 *
 * Ported from the public-domain/MIT PNPOLY algorithm by
 * W. Randolph Franklin: https://wrf.ecse.rpi.edu/Research/Short_Notes/pnpoly.html
 */

#include <cerebri/core/geofence.h>

/**
 * @brief Test whether a point lies inside a polygon using planar coordinates.
 *
 * Uses the PNPOLY ray-crossing algorithm. Results for points exactly on a
 * polygon edge are unspecified.
 *
 * @param poly    Vertices in order; do not repeat the first vertex at the end.
 * @param n_verts Number of vertices; must be >= 3.
 * @param test    Point to test.
 *
 * @retval true  test is inside poly.
 * @retval false test is outside poly, n_verts < 3, or poly is NULL.
 */
bool geofence_point_in_polygon(const struct geofence_point *poly,
				size_t n_verts,
				struct geofence_point test)
{
	bool inside = false;

	if ((poly != NULL) && (n_verts >= 3U)) {
		size_t i;
		size_t j = n_verts - 1U;

		for (i = 0U; i < n_verts; i++) {
			const bool y_straddles = ((poly[i].y > test.y) != (poly[j].y > test.y));

			if (y_straddles) {
				const double x_intersect = (poly[j].x - poly[i].x) *
					(test.y - poly[i].y) / (poly[j].y - poly[i].y) +
					poly[i].x;

				if (test.x < x_intersect) {
					inside = !inside;
				}
			}
			j = i;
		}
	}

	return inside;
}
