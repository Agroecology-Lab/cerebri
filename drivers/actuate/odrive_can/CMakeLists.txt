# Copyright (c) 2026, Agroecology Lab
# SPDX-License-Identifier: Apache-2.0

zephyr_library_named(cerebri_actuate_odrive_can)

# we need to be able to include generated header files
zephyr_include_directories()

zephyr_library_sources(
  main.c
  )

add_dependencies(cerebri_actuate_odrive_can synapse_pb)
