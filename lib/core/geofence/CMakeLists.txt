# Copyright (c) 2026 Agroecology Lab
# SPDX-License-Identifier: Apache-2.0

zephyr_library_named(cerebri_core_geofence)

zephyr_library_sources(
  src/geofence.c
  )

add_dependencies(app cerebri_core_geofence)
