#-----------------------------------------------------------------------------
# Copyright (c) 2025, PyInstaller Development Team.
#
# Distributed under the terms of the GNU General Public License (version 2
# or later) with exception for distributing the bootloader.
#
# The full license is in the file COPYING.txt, distributed with this software.
#
# SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
#-----------------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all PyQt6.QtCharts submodules
hiddenimports = collect_submodules('PyQt6.QtCharts')

# Collect any data files that might be needed
datas = collect_data_files('PyQt6.QtCharts')

# Ensure specific chart components are included
hiddenimports += [
    'PyQt6.QtCharts.QChart',
    'PyQt6.QtCharts.QChartView', 
    'PyQt6.QtCharts.QBarSet',
    'PyQt6.QtCharts.QBarSeries',
    'PyQt6.QtCharts.QBarCategoryAxis',
    'PyQt6.QtCharts.QValueAxis',
    'PyQt6.QtCharts.QPieSeries',
    'PyQt6.QtCharts.QPieSlice',
    'PyQt6.QtCharts.QLineSeries',
    'PyQt6.QtCharts.QScatterSeries',
    'PyQt6.QtCharts.QAreaSeries',
    'PyQt6.QtCharts.QSplineSeries'
]